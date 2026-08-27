def plot_rx_monthly(archivo_excel: str, salida_figura: str, salida_excel: str,
                    mes_seleccionado: int = None, agrupar_anual: bool = False,
                    salida_interpolado: str = None):
    """
    Grafica y calcula tendencia para índices RX1day/RX5day a partir de un archivo
    Excel con columnas: year, month, index.

    Parámetros
    ----------
    archivo_excel : str
        Ruta al archivo .xlsx con 3 columnas (year, month, index).
    salida_figura : str
        Ruta donde guardar la figura.
    salida_excel : str
        Ruta donde guardar los estadísticos.
    mes_seleccionado : int, opcional (default=None)
        Número del mes (1=Enero, ..., 12=Diciembre) a graficar.
        Si se especifica, se filtra la serie para ese mes.
    agrupar_anual : bool, opcional (default=False)
        Si es True, se agrupa por año tomando el máximo (RX1day/RX5day anual).
        Solo se usa si `mes_seleccionado` es None.
    salida_interpolado : str, opcional (default=None)
        Ruta donde guardar el archivo Excel con los datos interpolados.
        Si no se proporciona, se genera automáticamente añadiendo "_interpolated"
        al nombre del archivo de entrada.
    """
    # 1. Leer el archivo
    df_original = pd.read_excel(archivo_excel)
    # Guardar nombres de columnas originales
    col_year = df_original.columns[0]
    col_month = df_original.columns[1]
    col_index = df_original.columns[2]

    # Renombrar para estandarizar el manejo interno
    df = df_original.rename(columns={col_year: 'year', col_month: 'month', col_index: 'index'})

    # ---- NUEVO: Forzar conversión a numérico y detectar NaN ----
    # Convertir columna 'index' a numérico, forzando errores a NaN
    df['index'] = pd.to_numeric(df['index'], errors='coerce')

    n_nan_original = df['index'].isna().sum()
    if n_nan_original > 0:
        print(f"ℹ Se encontraron {n_nan_original} valores faltantes en la columna '{col_index}'.")
        print("   Se interpolarán linealmente sobre toda la serie mensual.")
        
        # Crear índice temporal fraccionario (año + (mes-1)/12)
        df['time'] = df['year'] + (df['month'] - 1) / 12.0
        df_sorted = df.sort_values('time')
        serie = df_sorted['index']
        
        # Interpolación lineal (con relleno en bordes)
        serie_interp = serie.interpolate(method='linear', limit_direction='both')
        # Si aún quedan NaN (por ejemplo, toda la serie es NaN), rellenar con la media
        if serie_interp.isna().any():
            print("⚠  Aún quedan NaN después de interpolar. Se rellenarán con la media de los valores no NaN.")
            serie_interp = serie_interp.fillna(serie_interp.mean())
        
        # Reemplazar en el DataFrame ordenado
        df_sorted['index'] = serie_interp
        # Restaurar el orden original (por year, month)
        df = df_sorted.sort_values(['year', 'month']).reset_index(drop=True)
        
        # Eliminar columna temporal
        df = df.drop(columns=['time'])
        
        # Guardar archivo interpolado con los nombres de columna originales
        if salida_interpolado is None:
            import os
            base, ext = os.path.splitext(archivo_excel)
            salida_interpolado = f"{base}_interpolated{ext}"
        # Restaurar nombres originales para guardar
        df_out = df.rename(columns={'year': col_year, 'month': col_month, 'index': col_index})
        df_out.to_excel(salida_interpolado, index=False)
        print(f"✅ Archivo con datos interpolados guardado: {salida_interpolado}")
    else:
        print("✅ No se encontraron valores faltantes. No se genera archivo interpolado.")

    # A partir de aquí, trabajar con el DataFrame ya interpolado (df)
    # 2. Preparar serie temporal según el modo elegido
    if mes_seleccionado is not None:
        # --- Modo: mes específico ---
        if not (1 <= mes_seleccionado <= 12):
            raise ValueError("mes_seleccionado debe estar entre 1 y 12.")
        df_filtrado = df[df['month'] == mes_seleccionado].copy()
        if df_filtrado.empty:
            raise ValueError(f"No hay datos para el mes {mes_seleccionado}.")
        time_array = df_filtrado['year'].values
        data_array = df_filtrado['index'].values
        xlabel = 'Año'
        mes_nombre = calendar.month_abbr[mes_seleccionado]
        titulo_extra = f' - Mes: {mes_nombre}'
        modo_texto = f'para {mes_nombre}'
        mes_guardado = mes_seleccionado
    elif agrupar_anual:
        # --- Modo: máximo anual ---
        df_anual = df.groupby('year', as_index=False)['index'].max()
        time_array = df_anual['year'].values
        data_array = df_anual['index'].values
        xlabel = 'Año'
        titulo_extra = ' (máximo anual)'
        modo_texto = 'anual'
        mes_guardado = 'Anual'
    else:
        # --- Modo: serie mensual completa (por defecto) ---
        time_array = df['year'].values + (df['month'].values - 1) / 12.0
        data_array = df['index'].values
        xlabel = 'Año (serie mensual)'
        titulo_extra = ' (mensual)'
        modo_texto = 'mensual completa'
        mes_guardado = 'Todos'

    # 3. Calcular estadísticos (con los datos ya interpolados)
    tau, p_value, trend, z_stat = mann_kendall_test(data_array)
    slope, intercept, slope_ci_lower, slope_ci_upper = theil_sen_estimator_with_ci(
        time_array, data_array
    )
    trend_line, trend_line_lower, trend_line_upper = calculate_confidence_bands(
        time_array, data_array, slope, intercept, slope_ci_lower, slope_ci_upper
    )

    # 4. Guardar estadísticos en Excel
    resultados = pd.DataFrame([{
        'Variable': col_index,
        'Mes': mes_guardado,
        'Modo': modo_texto,
        'Kendall_tau': tau,
        'p_value': p_value,
        'Tendencia': trend,
        'Z-statistic': z_stat,
        'Sen_slope': slope,
        'IC_inferior': slope_ci_lower,
        'IC_superior': slope_ci_upper,
        'Intercept': intercept
    }])
    resultados.to_excel(salida_excel, index=False)
    print(f"✅ Archivo de estadísticas exportado: {salida_excel}")

    # 5. Graficar
    fig, ax = plt.subplots(figsize=(20, 12))
    ax.plot(time_array, data_array, 'o-', color='black', alpha=0.7,
            markersize=4, linewidth=1, label='Datos')
    ax.plot(time_array, trend_line, '-', color='red', linewidth=2,
            label='Tendencia Theil-Sen')
    ax.fill_between(time_array, trend_line_lower, trend_line_upper,
                    color='red', alpha=0.2, label='IC 95%')
    ax.set_xlabel(xlabel)
    # Unidades (intentar obtener del nombre de la variable)
    unidades_dict = {
        'RX1day': 'mm',
        'RX5day': 'mm',
        'R10mm': 'días',
        'R20mm': 'días',
        'CDD': 'días',
        'CWD': 'días',
        'PRCPTOT': 'mm',
        'SDII': 'mm/day',
        'R95P': 'mm',
        'R99P': 'mm'
    }
    # Buscar el nombre de la variable en el diccionario (puede ser parte del nombre)
    unidades = ''
    for key, unit in unidades_dict.items():
        if key in col_index:
            unidades = unit
            break
    ylabel = f'{col_index} ({unidades})' if unidades else col_index
    ax.set_ylabel(ylabel)
    ymin = np.nanmin(data_array) - 1
    ymax = np.nanmax(data_array) + 1
    ax.set_ylim(ymin, ymax)

    significance = "**" if p_value < 0.01 else "*" if p_value < 0.05 else ""
    title = f'{col_index}{titulo_extra}\n'
    title += f'Tendencia: {trend}{significance}\n'
    title += f'Pendiente: {slope:.4f} {unidades}/año\n'
    title += f'IC 95%: [{slope_ci_lower:.4f}, {slope_ci_upper:.4f}]\n'
    title += f'τ = {tau:.3f}, p = {p_value:.3f}'
    ax.set_title(title, fontsize=12)
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(salida_figura, dpi=150, bbox_inches='tight')
    print(f"✅ Figura guardada en: {salida_figura}")
    plt.show()
    plt.close(fig)

    return resultados, df
