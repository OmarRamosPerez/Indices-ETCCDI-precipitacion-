import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import calendar
import pandas as pd

import geopandas as gpd

import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter

import warnings
warnings.simplefilter(action = "ignore", category = RuntimeWarning)
warnings.simplefilter(action = "ignore", category = FutureWarning)


######################
###################
# Estadísticos in situ
#######################
#######################


def mann_kendall_test(data):
        """
        Perform the Mann-Kendall trend test
    
        Parameters:
            data: array-like, time series data
    
        Returns:
            tau: Kendall's tau statistic
            p_value: two-tailed p-value
            trend: string describing the trend ('increasing', 'decreasing', 'no trend')
            z_stat: standardized test statistic
            """
        n = len(data)
    
    # Calculate S statistic
        S = 0
        for i in range(n-1):
            for j in range(i+1, n):
                S += np.sign(data[j] - data[i])
    
    # Calculate variance
        var_S = n * (n - 1) * (2 * n + 5) / 18
    
    # Calculate standardized test statistic
        if S > 0:
            Z = (S - 1) / np.sqrt(var_S)
        elif S < 0:
            Z = (S + 1) / np.sqrt(var_S)
        else:
            Z = 0
    
    # Calculate p-value (two-tailed)
        p_value = 2 * (1 - stats.norm.cdf(abs(Z)))
    
    # Calculate Kendall's tau
        tau = S / (n * (n - 1) / 2)
    
    # Determine trend
        alpha = 0.05
        if p_value < alpha:
            if tau > 0:
                trend = 'increasing'
            else:
                trend = 'decreasing'
        else:
            trend = 'no trend'
    
        return tau, p_value, trend, Z

def theil_sen_estimator_with_ci(x, y, confidence_level=0.95):
        """
    Calculate the Theil-Sen slope estimator with confidence intervals
    
    Parameters:
    x: array-like, independent variable (time)
    y: array-like, dependent variable (data)
    confidence_level: float, confidence level for intervals (default 0.95)
    
    Returns:
    slope: Theil-Sen slope estimate
    intercept: intercept of the trend line
    slope_ci_lower: lower bound of slope confidence interval
    slope_ci_upper: upper bound of slope confidence interval
    """
        n = len(x)
        slopes = []
    
    # Calculate all pairwise slopes
        for i in range(n-1):
            for j in range(i+1, n):
                if x[j] != x[i]:  # Avoid division by zero
                    slope = (y[j] - y[i]) / (x[j] - x[i])
                    slopes.append(slope)
    
        slopes = np.array(slopes)
    
    # Theil-Sen slope is the median of all slopes
        slope = np.median(slopes)
    
    # Calculate confidence interval for slope
        alpha = 1 - confidence_level
        z_alpha_2 = stats.norm.ppf(1 - alpha/2)
    
    # Number of slope estimates
        n_slopes = len(slopes)
    
    # Calculate confidence interval bounds using the sorted slopes
        slopes_sorted = np.sort(slopes)
    
    # Standard error approximation for confidence interval
        c_gamma = z_alpha_2 * np.sqrt(n * (n-1) * (2*n + 5) / 18)
    
    # Calculate indices for confidence interval
        m1 = int(np.floor((n_slopes - c_gamma) / 2))
        m2 = int(np.ceil((n_slopes + c_gamma) / 2))
    
    # Ensure indices are within bounds
        m1 = max(0, m1)
        m2 = min(n_slopes - 1, m2)
    
        slope_ci_lower = slopes_sorted[m1] if m1 < len(slopes_sorted) else slopes_sorted[0]
        slope_ci_upper = slopes_sorted[m2] if m2 < len(slopes_sorted) else slopes_sorted[-1]
    
    # Calculate intercept
        intercept = np.median(y) - slope * np.median(x)
    
        return slope, intercept, slope_ci_lower, slope_ci_upper

def calculate_confidence_bands(x, y, slope, intercept, slope_ci_lower, slope_ci_upper):
        """
    Calculate confidence bands for the trend line
    """
        x_median = np.median(x)
        y_median = np.median(y)
    
    # Calculate trend lines
        trend_line = slope * x + intercept
        trend_line_lower = slope_ci_lower * (x - x_median) + y_median
        trend_line_upper = slope_ci_upper * (x - x_median) + y_median
    
        return trend_line, trend_line_lower, trend_line_upper


# Función para calcular promedio excluyendo ceros
def calculate_mean_no_zeros(data_array):
        """
    Calcula el promedio de un array excluyendo los valores cero
    
    Parameters:
    data_array: array 2D con datos de precipitación
    
    Returns:
    mean_value: promedio excluyendo ceros, o NaN si todos son ceros
    """
    # Aplanar el array y remover ceros
        flat_data = data_array.flatten()
        non_zero_data = flat_data[flat_data > 0]
    
        if len(non_zero_data) > 0:
            return np.mean(non_zero_data)
        else:
            return np.nan  # Retorna NaN si todos los valores son cero




################################################################################
################################################################################
class ETCCDI_precip_plot_in_situ:
    
    ######################
    ## Graficar FIGURA 
    #######
    
    def plot(archivo_excel: str, salida_figura: str, salida_excel:str):
    
# Load the Excel file (first sheet by default)
        df = pd.read_excel(archivo_excel)

        # Obtener nombre de la variable desde el encabezado de la segunda columna
        nombre_variable = df.columns[1]
        # Diccionario opcional con unidades comunes (ampliar según necesidad)
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
        unidades = unidades_dict.get(nombre_variable, '')
        ylabel = f'{nombre_variable} ({unidades})' if unidades else nombre_variable

        data_in = df.iloc[:, 1]

        time_array = df.iloc[:, 0]
    # Calculate global y-limits
        all_data = np.array(data_in)
        diff_min_ar = np.floor(min([data.min() for data in all_data])) - 1
        diff_max_ar = np.ceil(max([data.max() for data in all_data])) + 1
    
    
        data_array = all_data
    
#     # Create plots
        fig, axes = plt.subplots(1, 1, figsize=(20, 12))
    
#     # Colors for datasets
        colors = 'black'
    
#     # Store results for summary table
        results = []
    
# for dataset_idx, (dataset_name, data_arrays) in enumerate(zip(datasets, [livneh_data, mexhi_data])):
#         for month_idx, (month, data) in enumerate(zip(months, data_arrays)):
        ax = axes
    
            # Perform Mann-Kendall test
        tau, p_value, trend, z_stat = mann_kendall_test(all_data)

            # Calculate Theil-Sen estimator with confidence intervals
        slope, intercept, slope_ci_lower, slope_ci_upper = theil_sen_estimator_with_ci(time_array, data_array)
            
            # Calculate confidence bands
        trend_line, trend_line_lower, trend_line_upper = calculate_confidence_bands(
                time_array, data_array, slope, intercept, slope_ci_lower, slope_ci_upper)


            # Store results
        results.append({
#                'Dataset': dataset_name,
#                'Mes': month,
                'Kendall_tau': tau,
                'p_value': p_value,
                'Tendencia': trend,
                'Z-statistic': z_stat,
                'Sen_slope': slope,
                'IC_inferior': slope_ci_lower,
                'IC_superior': slope_ci_upper,
                'Intercept': intercept
            })
            
            # Plot original data
        ax.plot(time_array, data_array, 'o-', color=colors, 
                   alpha=0.7, markersize=4, linewidth=1, label='Data')
            
            # Plot Theil-Sen trend line
        ax.plot(time_array, trend_line, '-', color='red', linewidth=2, 
                   label='Theil-Sen trend')
            
            # Plot 95% confidence band
        ax.fill_between(time_array, trend_line_lower, trend_line_upper, 
                           color='red', alpha=0.2, label='95% CI')
            
            # Set plot properties
        ax.set_xlabel('Year')
        ax.set_ylabel(ylabel)
        ax.set_ylim(diff_min_ar, diff_max_ar)
        ax.set_xticks(np.arange(1951, 2014, 10))
        ax.set_xticklabels(np.arange(1951, 2014, 10).astype(int))
            
            # Title with trend information
        significance = "**" if p_value < 0.01 else "*" if p_value < 0.05 else ""
        title = f'{nombre_variable}\n'  #f'{dataset_name} - {month}\n'
        title += f'Trend: {trend}{significance}\n'
        title += f'Slope: {slope:.4f} mm/year\n'
        title += f'95% CI: [{slope_ci_lower:.4f}, {slope_ci_upper:.4f}]\n'
        title += f'τ = {tau:.3f}, p = {p_value:.3f}'
        ax.set_title(title, fontsize=9)
            
            # Add legend only to first subplot
  #  if dataset_idx == 0 and month_idx == 0:
        ax.legend(loc='upper left', fontsize=8)
            
            # Add grid
        ax.grid(True, alpha=0.3)

    
        plt.tight_layout()
        plt.savefig(salida_figura, dpi=150, bbox_inches='tight')
        print("********************")
        print(f"✅Figura guardada correctamente: {salida_figura}")
        print("********************")

            
            
        print("********************")
        print(f"✅ Archivo de estadísticas exportado: {salida_excel} ")
        print("********************")

            
        plt.show()


        # Convertir diccionario a DataFrame de Pandas
        df = pd.DataFrame(results)

# Exportar a Excel
        df.to_excel(salida_excel, index=False)
        

        return results, df




    def plot_rx_monthly(archivo_excel:str, salida_figura:str, salida_excel:str,
                    agrupar_anual=False, mes_seleccionado=None):
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
    agrupar_anual : bool, opcional (default=False)
        Si es True, se agrupa por año tomando el máximo (RX1day/RX5day anual).
        Solo se usa si `mes_seleccionado` es None.
    mes_seleccionado : int, opcional (default=None)
        Número del mes (1=Enero, ..., 12=Diciembre) a graficar.
        Si se especifica, se filtra la serie para ese mes y se grafica la tendencia
        interanual. Anula el efecto de `agrupar_anual`.
    """
    # 1. Leer el archivo
        df = pd.read_excel(archivo_excel)
    
    # Guardar el nombre original de la variable (tercera columna)
        nombre_variable = df.columns[2]
    
    # Renombrar para estandarizar el manejo interno
        df.columns = ['year', 'month', 'index']
    
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

    # 3. Calcular estadísticos
        tau, p_value, trend, z_stat = mann_kendall_test(data_array)
        slope, intercept, slope_ci_lower, slope_ci_upper = theil_sen_estimator_with_ci(
            time_array, data_array
            )
        trend_line, trend_line_lower, trend_line_upper = calculate_confidence_bands(
            time_array, data_array, slope, intercept, slope_ci_lower, slope_ci_upper
            )

    # 4. Guardar estadísticos en Excel
        resultados = pd.DataFrame([{
        'Variable': nombre_variable,
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
        
 
    # 5. Graficar
        fig, ax = plt.subplots(figsize=(20, 12))

    # Datos originales
        ax.plot(time_array, data_array, 'o-', color='black', alpha=0.7,
            markersize=4, linewidth=1, label='Datos')

    # Recta de tendencia
        ax.plot(time_array, trend_line, '-', color='red', linewidth=2,
            label='Tendencia Theil-Sen')

    # Banda de confianza al 95%
        ax.fill_between(time_array, trend_line_lower, trend_line_upper,
                    color='red', alpha=0.2, label='IC 95%')

    # Configuración del gráfico
        ax.set_xlabel(xlabel)
    
    # Unidades
        unidades_dict = {
        'RX1day': 'mm',
        'RX5day': 'mm',
        'R10mm': 'días',
        'R20mm': 'días',
        # ... puedes ampliar
        }
        unidades = unidades_dict.get(nombre_variable, '')
        ylabel = f'{nombre_variable} ({unidades})' if unidades else nombre_variable
        ax.set_ylabel(ylabel)

    # Límites Y
        ymin = np.floor(data_array.min()) - 1
        ymax = np.ceil(data_array.max()) + 1
        ax.set_ylim(ymin, ymax)

    # Título con información de la tendencia
        significance = "**" if p_value < 0.01 else "*" if p_value < 0.05 else ""
        title = f'{nombre_variable}{titulo_extra}\n'
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
        
        
        print("********************")
        print(f"✅ Archivo de estadísticas exportado: {salida_excel} ")
        print("********************")

        
        plt.show()
        plt.close(fig)


        # Convertir diccionario a DataFrame de Pandas
        df = pd.DataFrame(resultados)

# Exportar a Excel
        df.to_excel(salida_excel, index=False)
        

        return resultados, df


###############################################################################################
###############################
###############################
#   Datos Grid NetCDF 

import netCDF4 as nc

from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")


# ── pymannkendall opcional ───────────────────────────────────
try:
    import pymannkendall as mk
    USE_PYMANNKENDALL = True
#    print("✔  pymannkendall disponible.")
except ImportError:
    USE_PYMANNKENDALL = False
#    print("⚠  pymannkendall no encontrado. Usando implementación propia (scipy).")


# ════════════════════════════════════════════════════════════
#  1. FUNCIONES DE TENDENCIA
# ════════════════════════════════════════════════════════════

def mann_kendall_test_malla(x):
    """Mann-Kendall + Theil-Sen implementación propia."""
    x = np.asarray(x, dtype=float)
    n = len(x)

    s = 0
    for k in range(n - 1):
        for j in range(k + 1, n):
            s += np.sign(x[j] - x[k])

    var_s = n * (n - 1) * (2 * n + 5) / 18

    if s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0.0

    p_valor = 2 * (1 - stats.norm.cdf(abs(z)))
    tau = s / (0.5 * n * (n - 1))

    slopes = [(x[j] - x[k]) / (j - k)
              for k in range(n - 1)
              for j in range(k + 1, n)]
    pendiente = float(np.median(slopes)) if slopes else 0.0
    t = np.arange(n)
    intercepto = float(np.median(x - pendiente * t))

    return tau, p_valor, pendiente, intercepto


def calcular_tendencia_punto(serie):
    """Calcula todas las métricas para una serie temporal 1-D."""
    serie = np.asarray(serie, dtype=float)
    mask = ~np.isnan(serie)
    n_validos = int(mask.sum())

    resultado = dict(tau=np.nan, p_valor=np.nan,
                     pendiente=np.nan, intercepto=np.nan,
                     significativo=False, tendencia=0)

    if n_validos < 4:
        return resultado

    x = serie[mask]

    if USE_PYMANNKENDALL:
        res = mk.original_test(x)
        tau        = float(res.Tau)
        p_valor    = float(res.p)
        pendiente  = float(res.slope)
        intercepto = float(res.intercept)
    else:
        tau, p_value, trend_str, z_stat = mann_kendall_test(x)
        t = np.arange(len(x))
        pendiente, intercepto, _, _ = theil_sen_estimator_with_ci(t, x)

        # ✅ Conversión aquí dentro, con el nombre correcto
        pendiente  = float(pendiente) if not np.isnan(pendiente) else 0.0
        tau        = float(tau)
        p_valor    = float(p_value)   # ← p_value → p_valor
        intercepto = float(intercepto)

        
    resultado.update(
        tau=tau,
        p_valor=p_valor,
        pendiente=pendiente,
        intercepto=float(intercepto),
        significativo=bool(p_valor < 0.05),
        tendencia=int(np.sign(pendiente)) if pendiente != 0 else 0
    )
    return resultado


# ════════════════════════════════════════════════════════════
#  2. LECTURA DEL NETCDF
# ════════════════════════════════════════════════════════════

def leer_netcdf(ruta_archivo, nombre_variable=None):
    """
    Lee el NetCDF y devuelve los datos (con escalado), lat, lon,
    nombre de variable, long_name y units.
    Selecciona automáticamente la variable principal si no se especifica.
    """
    ds = nc.Dataset(ruta_archivo, 'r')

    # Detectar coordenadas
    coord_lat = next((v for v in ds.variables if v.lower() in ('lat', 'latitude', 'rlat', 'y')), None)
    coord_lon = next((v for v in ds.variables if v.lower() in ('lon', 'longitude', 'rlon', 'x')), None)

    if coord_lat is None or coord_lon is None:
        raise ValueError("No se encontraron coordenadas lat/lon en el archivo.")

    lats = np.array(ds.variables[coord_lat][:], dtype=float)
    lons = np.array(ds.variables[coord_lon][:], dtype=float)

    # Si el usuario no especifica la variable, la seleccionamos automáticamente
    if nombre_variable is None:
        # Variables a excluir (dimensiones, coordenadas, metadatos)
        excluir = {
            'time', 'tiempo', 'time_bnds', 'time_bounds',
            'lon', 'lat', 'latitude', 'longitude', 'rlon', 'rlat', 'x', 'y',
            'spatial_ref', 'crs', 'crs_wkt', 'grid_mapping',
            'number_of_5day_heavy_precipitation_periods_per_time_period'  # ¡añadimos esta!
        }
        # También excluimos cualquier variable que sea de tipo string o no tenga dimensiones espaciales
        candidatas = []
        for v in ds.variables:
            if v in excluir or v in ds.dimensions:
                continue
            # Verificar que la variable tenga al menos dos dimensiones (lat, lon)
            dims = ds.variables[v].dimensions
            if coord_lat in dims and coord_lon in dims:
                candidatas.append(v)
        if not candidatas:
            raise ValueError("No se encontró ninguna variable con coordenadas lat/lon.")
        # Elegir la variable con más dimensiones (priorizar 3D sobre 2D)
        candidatas.sort(key=lambda v: len(ds.variables[v].dimensions), reverse=True)
        nombre_variable = candidatas[0]
        print(f"ℹ  Variable seleccionada automáticamente: '{nombre_variable}'")

    var = ds.variables[nombre_variable]
    long_name = getattr(var, 'long_name', nombre_variable)
    units = getattr(var, 'units', '')

    # Lectura + escalado
    raw = var[:]
    if hasattr(var, 'scale_factor') or hasattr(var, 'add_offset'):
        scale = float(getattr(var, 'scale_factor', 1.0))
        offset = float(getattr(var, 'add_offset', 0.0))
        datos = np.asarray(raw, dtype=float) * scale + offset
    else:
        datos = np.asarray(raw, dtype=float)

    # FillValue
    fill_value = getattr(var, '_FillValue', None) or getattr(var, 'missing_value', None)
    if fill_value is not None:
        datos[np.isclose(datos, float(fill_value), rtol=1e-5, atol=1e8)] = np.nan

    ds.close()
    return datos, lats, lons, nombre_variable, long_name, units



# ════════════════════════════════════════════════════════════
#  3. CÁLCULO EN TODA LA GRILLA
# ════════════════════════════════════════════════════════════

def calcular_tendencias_grilla(datos):
    
    if datos.ndim != 3:
        raise ValueError(f"Se esperaban 3 dimensiones (tiempo, lat, lon), pero se obtuvieron {datos.ndim}.")
    ntime, nlat, nlon = datos.shape
    if ntime < 4:
        raise ValueError(f"Solo hay {ntime} pasos de tiempo. Se necesitan al menos 4 para calcular tendencia.")
    
    _, nlat, nlon = datos.shape
    tau_map       = np.full((nlat, nlon), np.nan)
    pval_map      = np.full((nlat, nlon), np.nan)
    pend_map      = np.full((nlat, nlon), np.nan)
    sig_map       = np.zeros((nlat, nlon), dtype=bool)
    tend_map      = np.zeros((nlat, nlon), dtype=int)

#    print(f"\n📊 Procesando {nlat}×{nlon} = {nlat*nlon} puntos de malla...")
    with tqdm(total=nlat * nlon, ncols=70, unit='pts') as pbar:
        for i in range(nlat):
            for j in range(nlon):
                res = calcular_tendencia_punto(datos[:, i, j])
                tau_map[i, j]  = res['tau']
                pval_map[i, j] = res['p_valor']
                pend_map[i, j] = res['pendiente']
                sig_map[i, j]  = res['significativo']
                tend_map[i, j] = res['tendencia']
                pbar.update(1)

    return tau_map, pval_map, pend_map, sig_map, tend_map


# ════════════════════════════════════════════════════════════
#  4. HELPERS DE FIGURA
# ════════════════════════════════════════════════════════════
 
def _base_ax(fig, lats, lons, shapefile_ruta):
    """Crea un eje cartopy con fondo, costas y grilla estándar."""
    proj   = ccrs.PlateCarree()
    extent = [lons.min() - 1, lons.max() + 1,
              lats.min() - 1, lats.max() + 1]
    ax = fig.add_subplot(1, 1, 1, projection=proj)
    ax.set_extent(extent, crs=proj)
    ax.set_facecolor('white')
    ax.add_feature(cfeature.OCEAN, facecolor='None',    edgecolor='black', zorder=0)
    ax.add_feature(cfeature.LAND,  facecolor='None',    edgecolor='black', zorder=0)
    ax.add_feature(cfeature.BORDERS,   linewidth=0.4, edgecolor='black', zorder=3)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.6, edgecolor='black', zorder=3)
    ax.add_feature(cfeature.STATES, linewidth=0.6, edgecolor='black', zorder=3)

    # 8.1 Agregar

        # Load the shapefile
    gdf = gpd.read_file(shapefile_ruta)

    gdf.plot(ax=ax, transform=ccrs.PlateCarree(), edgecolor='gold', facecolor='none', linewidth=1)


    gl = ax.gridlines(crs=proj, draw_labels=True,
                      linewidth=0.3, color='gray', alpha=0.6, linestyle='--')
    gl.top_labels   = False
    gl.right_labels = False
    gl.xlabel_style = dict(color='black', size=8)
    gl.ylabel_style = dict(color='black', size=8)
    gl.xformatter   = LongitudeFormatter()
    gl.yformatter   = LatitudeFormatter()
    return ax, proj

 
#    cb_label = f'Pendiente Theil-Sen de {long_name} ({units})' if units else f'Pendiente Theil-Sen de {long_name}'
        

def _pcolormesh_cb(fig, ax, proj, lons, lats, data2d, cmap,
                   vmin, vmax, cb_label):
    """Pinta pcolormesh + colorbar horizontal centrada en 0."""
    if vmin is None and vmax is None:
        # Límite simétrico: el 0 queda exactamente en el centro del colormap
        abs_max = max(abs(np.nanpercentile(data2d, 2)),
                      abs(np.nanpercentile(data2d, 98)))
        vn, vx = -abs_max, abs_max
    else:
        vn = vmin if vmin is not None else np.nanpercentile(data2d, 2)
        vx = vmax if vmax is not None else np.nanpercentile(data2d, 98)

    im = ax.pcolormesh(lons, lats, data2d,
                       cmap=cmap, vmin=vn, vmax=vx,
                       transform=proj, zorder=1,
                       shading='auto', alpha=0.9)
    cb = plt.colorbar(im, ax=ax, orientation='horizontal',
                      pad=0.05, fraction=0.046, aspect=35)
    cb.set_label(cb_label, color='black', fontsize=9)
    cb.ax.tick_params(labelcolor='black', labelsize=8, colors='black')
    cb.outline.set_edgecolor('black')
                           
 
def _guardar(fig, archivo):
    """Título, guardado y cierre."""
#    fig.suptitle( color='#e8f4f8',
#                 fontsize=12, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(archivo, dpi=150,
                bbox_inches='tight', facecolor=fig.get_facecolor())
    
    print("************************")
    print(f"✅ Figura guardada correctamente: {archivo}")
    print("************************")

    plt.show()
    
    plt.close(fig)


# ════════════════════════════════════════════════════════════
#  5. GUARDAR RESULTADOS EN NETCDF
# ════════════════════════════════════════════════════════════
 
def guardar_resultados(lats, lons, tau_map, pval_map, pend_map,
                       sig_map, tend_map, nombre_var,
                       archivo_salida):
    ds = nc.Dataset(archivo_salida, 'w', format='NETCDF4')
    ds.createDimension('lat', len(lats))
    ds.createDimension('lon', len(lons))
 
    vl = ds.createVariable('lat', 'f4', ('lat',)); vl.units = 'degrees_north'; vl[:] = lats
    vn = ds.createVariable('lon', 'f4', ('lon',)); vn.units = 'degrees_east';  vn[:] = lons
 
    def add(name, data, long_name, units='1'):
        v = ds.createVariable(name, 'f4', ('lat', 'lon'), fill_value=np.nan)
        v.long_name = long_name; v.units = units; v[:] = data
 
    add('kendall_tau',    tau_map,              f'Kendall Tau — {nombre_var}')
    add('p_value',        pval_map,             f'p-valor Mann-Kendall — {nombre_var}')
    add('theilsen_slope', pend_map,             f'Pendiente Theil-Sen — {nombre_var}', 'unidad/paso')
    add('significant',    sig_map.astype(float), 'Significativo 95% (1=sí, 0=no)')
    add('trend_sign',     tend_map.astype(float),'Signo (+1 pos, -1 neg)')
 
    ds.description = f'Tendencias de {nombre_var}. Mann-Kendall, Theil-Sen, Kendall Tau.'
    ds.close()
                               
    print("************************")
    print(f"✅  NetCDF de estadísticos guardado: {archivo_salida}")
    print("************************")



#################################################################################
###############################################################################
##########   GRAFICAR FIGURAS GRID (NETCDF)

class ETCCDI_precip_plot_malla:
    



    def Plot_netcdf_1_tiempo(Archivo_NETCDF: str, Salida_FIGURA: str,
                         color_scale: str,
                         shapefile_ruta=None,
                         center_cmap=False,
                         levels=None,
                         set_global=False,
                         ax=None):
        """
    Grafica el primer paso de tiempo de una variable en un archivo NetCDF.
    Usa leer_netcdf para obtener datos y coordenadas de forma robusta.
    """
    # 1. Leer el archivo con la función auxiliar (global)
        datos, lats, lons, nombre_var, long_name, units = leer_netcdf(Archivo_NETCDF)

    # 2. Seleccionar el primer tiempo si es 3D
        if datos.ndim == 3:
            data_array = datos[0, :, :]   # (lat, lon)
        elif datos.ndim == 2:
            data_array = datos
        else:
            raise ValueError(f"Los datos tienen {datos.ndim} dimensiones, se esperaban 2 o 3.")

    # 3. Asegurar que sean arrays numpy y con las formas correctas
        lons = np.asarray(lons)
        lats = np.asarray(lats)
        data_array = np.asarray(data_array)

    # Verificar consistencia
        if lons.ndim != 1 or lats.ndim != 1:
            raise ValueError("Las coordenadas deben ser 1D")
        if data_array.shape != (len(lats), len(lons)):
            raise ValueError(f"Forma de datos {data_array.shape} no coincide con (lat,lon) ({len(lats)},{len(lons)})")

    # 4. Crear malla 2D para pcolormesh (más seguro y compatible con Cartopy)
        lon2d, lat2d = np.meshgrid(lons, lats)

    # 5. Configurar figura y ejes
        projection = ccrs.PlateCarree()
        if ax is None:
            fig = plt.figure(figsize=(20, 12))
            ax = plt.axes(projection=projection)
        else:
            fig = ax.get_figure()

    # 6. Definir límites del colormap (usando percentiles)
        valid = data_array[~np.isnan(data_array)]
        if len(valid) == 0:
            vmin, vmax = 0, 1
        else:
            vmin = float(np.percentile(valid, 1))
            vmax = float(np.percentile(valid, 99.5))

    # 7. Graficar con pcolormesh (usando malla 2D)
        cmap = plt.get_cmap(color_scale)
        im = ax.pcolormesh(lon2d, lat2d, data_array,
                       cmap=cmap, vmin=vmin, vmax=vmax,
                       transform=ccrs.PlateCarree(), shading='auto')

    # 8. Agregar elementos geográficos
        ax.add_feature(cfeature.BORDERS, edgecolor='black', linewidth=0.4)
        ax.add_feature(cfeature.COASTLINE, edgecolor='black', linewidth=0.5)
        ax.add_feature(cfeature.STATES, edgecolor='black', linewidth=0.4)


    # 8.1 Agregar

        # Load the shapefile
        gdf = gpd.read_file(shapefile_ruta)

        gdf.plot(ax=ax, transform=ccrs.PlateCarree(), edgecolor='gold', facecolor='none', linewidth=1)


    # 9. Extensión del mapa
        ax.set_extent([lons.min()-1, lons.max()+1, lats.min()-1, lats.max()+1],
                  crs=ccrs.PlateCarree())

    # 10. Etiquetas de ejes y grid
        dx = 5
        xticks = np.arange(np.floor(lons.min()), np.ceil(lons.max()) + 1, dx)
        yticks = np.arange(np.floor(lats.min()), np.ceil(lats.max()) + 1, dx)
        ax.set_xticks(xticks, crs=ccrs.PlateCarree())
        ax.set_yticks(yticks, crs=ccrs.PlateCarree())
        ax.xaxis.set_major_formatter(LongitudeFormatter())
        ax.yaxis.set_major_formatter(LatitudeFormatter())

    # 11. Colorbar
        cb_label = f"{long_name} [{units}]" if units else long_name
        plt.colorbar(im, ax=ax, orientation='vertical', pad=0.03,
                 fraction=0.035, aspect=30, label=cb_label)

    # 12. Líneas de grid (opcional)
        ax.gridlines(xlocs=xticks, ylocs=yticks, alpha=0.6, color='gray',
                 draw_labels=False, linewidth=0.25, linestyle='--')

    # 13. Guardar y mostrar
        plt.tight_layout()
        plt.savefig(Salida_FIGURA, dpi=200, bbox_inches='tight', facecolor='white')
        print(f"✅ Figura guardada correctamente: {Salida_FIGURA}")
        plt.show()
        plt.close(fig)

        return fig, ax, im


 # ════════════════════════════════════════════════════════════
#  4D. FIGURA 4 — Mapa de tendencias + significancia
# ════════════════════════════════════════════════════════════
 
    def plot_netcdf_n_tiempos(Archivo_NC: str, Salida_FIG: str, Salida_NC: str, color_scale: str, shapefile_ruta=None):
#        print(f"\n📂 Leyendo: {ARCHIVO_NC}")
        VARIABLE = None
        
        datos, lats, lons, nombre_var, long_name, units = leer_netcdf(Archivo_NC, VARIABLE)
        
        # Calcular tendencias
        tau_map, pval_map, pend_map, sig_map, tend_map = calcular_tendencias_grilla(datos)

        fig = plt.figure(figsize=(12, 8))
        fig.patch.set_facecolor('white') ##0d1117
        ax, proj = _base_ax(fig, lats, lons, shapefile_ruta)
 
        cmap = plt.get_cmap(color_scale)

        cb_label = f'Pendiente Theil-Sen de {long_name} ({units})' if units else f'Pendiente Theil-Sen de {long_name}'

        # Fondo con pendiente
        _pcolormesh_cb(fig, ax, proj, lons, lats, pend_map,
                       cmap, None, None, cb_label )

        lon2d, lat2d = np.meshgrid(lons, lats)
 
        # Puntos significativos
        for tend_val, color_s, marker_s, label_s in [
                ( 1, 'None', '^', 'Tendencia ↑ (p < 0.05)'),
                (-1, 'None', 'v', 'Tendencia ↓ (p < 0.05)')]:
            mask = (tend_map == tend_val) & sig_map
            if mask.sum() == 0:
                continue
            ax.scatter(lon2d[mask], lat2d[mask],
                       marker=marker_s, c=color_s, s=20, alpha=0.9,
                       linewidths=1.0, edgecolors='black',
                       transform=proj, zorder=5, label=label_s)

        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(handles=handles, labels=labels, loc='lower left', 
                      fontsize=9, facecolor='white', edgecolor='black')

        n_sig = int(sig_map.sum())
        n_tot = int(np.sum(~np.isnan(tau_map)))
        pct_sig = 100 * n_sig / n_tot if n_tot > 0 else 0

 #       ax.set_title(f'{long_name}\nTendencias significativas: {n_sig}/{n_tot} ({pct_sig:.1f}%) | α=0.05',
 #                    color='black', fontsize=12, fontweight='bold', pad=10)
        
        _guardar(fig, Salida_FIG)
 
 
        guardar_resultados(lats, lons, tau_map, pval_map, pend_map,
                   sig_map, tend_map, nombre_var,
                   archivo_salida=Salida_NC)


# #     # Print summary table
# # print("\n" + "="*120)
# # print("MANN-KENDALL TEST AND THEIL-SEN ESTIMATOR WITH 95% CONFIDENCE INTERVALS")
# # print("="*120)
# # print(f"{'Dataset':<8} {'Month':<10} {'Tau':<8} {'P-value':<10} {'Trend':<12} {'Slope':<10} "
# #           f"{'CI Lower':<10} {'CI Upper':<10} {'Sig':<4}")
# # print("-"*120)
    
# # for result in results:
# #         significance = "**" if result['P-value'] < 0.01 else "*" if result['P-value'] < 0.05 else ""
# #         print(f"{result['Dataset']:<8} {result['Month']:<10} "
# #               f"{result['Tau']:<8.3f} {result['P-value']:<10.3f} "
# #               f"{result['Trend']:<12} {result['Slope (mm/year)']:<10.4f} "
# #               f"{result['Slope CI Lower']:<10.4f} {result['Slope CI Upper']:<10.4f} "
# #               f"{significance:<4}")
