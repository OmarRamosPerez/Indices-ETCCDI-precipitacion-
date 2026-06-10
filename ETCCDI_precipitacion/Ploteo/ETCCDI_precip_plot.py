import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


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


import pandas as pd


################################################################################
################################################################################
class ETCCDI_precip_plot_in_situ:
    
    ######################
    ## Graficar FIGURA 
    #######
    
    def plot(archivo_excel: str, salida_figura: str, salida_excel:str):
    
# Load the Excel file (first sheet by default)
        df = pd.read_excel(archivo_excel)

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
        ax.set_ylabel('RX5day (mm)')
        ax.set_ylim(diff_min_ar, diff_max_ar)
        ax.set_xticks(np.arange(1951, 2014, 10))
        ax.set_xticklabels(np.arange(1951, 2014, 10).astype(int))
            
            # Title with trend information
        significance = "**" if p_value < 0.01 else "*" if p_value < 0.05 else ""
        title = '' #f'{dataset_name} - {month}\n'
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
    """Lee el NetCDF aplicando escalado correctamente."""
    ds = nc.Dataset(ruta_archivo, 'r')
#    print(f"\n   Variables encontradas: {list(ds.variables.keys())}")

    coord_lat = next((v for v in ds.variables if v.lower() in ('lat', 'latitude', 'rlat', 'y')), None)
    coord_lon = next((v for v in ds.variables if v.lower() in ('lon', 'longitude', 'rlon', 'x')), None)

    lats = np.array(ds.variables[coord_lat][:], dtype=float)
    lons = np.array(ds.variables[coord_lon][:], dtype=float)

    if nombre_variable is None:
        excluir = {'time', 'tiempo', 'time_bnds', 'lon', 'lat', 'latitude', 'longitude', 'time_bounds'}
        candidatas = [v for v in ds.variables if v not in excluir and v not in ds.dimensions]
        nombre_variable = candidatas[0]
 #       print(f"ℹ  Variable seleccionada automáticamente: '{nombre_variable}'")

    var = ds.variables[nombre_variable]
    long_name = getattr(var, 'long_name', nombre_variable)
    units     = getattr(var, 'units', '')

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

 #   if datos.ndim == 3:
 #       print(f"   Array 3D con {datos.shape[0]} pasos de tiempo.")

    ds.close()
    return datos, lats, lons, nombre_variable, long_name, units



# ════════════════════════════════════════════════════════════
#  3. CÁLCULO EN TODA LA GRILLA
# ════════════════════════════════════════════════════════════

def calcular_tendencias_grilla(datos):
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
 
def _base_ax(fig, lats, lons):
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

    gl = ax.gridlines(crs=proj, draw_labels=True,
                      linewidth=0.3, color='gray', alpha=0.6, linestyle='--')
    gl.top_labels   = False
    gl.right_labels = False
    gl.xlabel_style = dict(color='black', size=8)
    gl.ylabel_style = dict(color='black', size=8)
    gl.xformatter   = LongitudeFormatter()
    gl.yformatter   = LatitudeFormatter()
    return ax, proj
 
 
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
                             center_cmap=False,
                             levels=None,
                             set_global=False,
                             ax=None):
        """ 
        Versión FINAL con netCDF4 - valores correctos.
        """

        import netCDF4 as nc
        import numpy as np

#        print(f"\n📂 Leyendo con netCDF4: {Archivo_NETCDF}")
        ds = nc.Dataset(Archivo_NETCDF, 'r')

        # Detectar variable principal
        var_names = [v for v in ds.variables if v not in ds.dimensions and v.lower() not in ['time', 'tiempo']]
        nombre_var = var_names[0] if var_names else list(ds.variables.keys())[0]
#        print(f"ℹ  Variable: '{nombre_var}'")

        var = ds.variables[nombre_var]
        long_name = getattr(var, 'long_name', nombre_var)
        units = getattr(var, 'units', '')

        # === Lectura y escalado correcto ===
        data_raw = var[:]

        if hasattr(var, 'scale_factor') or hasattr(var, 'add_offset'):
            scale_factor = getattr(var, 'scale_factor', 1.0)
            add_offset   = getattr(var, 'add_offset', 0.0)
            data_array = np.asarray(data_raw, dtype=float) * scale_factor + add_offset
     #       print(f"   Aplicado: scale_factor={scale_factor}, add_offset={add_offset}")
        else:
            data_array = np.asarray(data_raw, dtype=float)

        # Limpieza de fill values
        fill_value = getattr(var, '_FillValue', None) or getattr(var, 'missing_value', None)
        if fill_value is not None:
            data_array[np.isclose(data_array, fill_value, rtol=1e-5, atol=1e8)] = np.nan

        data_array[np.isinf(data_array) | (np.abs(data_array) > 1e10)] = np.nan

        # Primer tiempo si es 3D
        if data_array.ndim == 3:
            data_array = data_array[0, :, :]
  #          print("   Usando primer paso de tiempo")

   #     print(f"   Min/Max: {np.nanmin(data_array):.2f} / {np.nanmax(data_array):.2f}")

        # Extraer coordenadas ANTES de cerrar
        lons = ds.variables['lon'][:]
        lats = ds.variables['lat'][:]

        ds.close()

        # ── Escala de color ─────────────────────
        valid = data_array[~np.isnan(data_array)]
        vmin = float(np.percentile(valid, 1)) if len(valid) > 0 else 0
        vmax = float(np.percentile(valid, 99.5))

 #       if any(x in nombre_var.lower() for x in ['r10', 'r20', 'count', 'days']):
 #           vmin = max(0.0, vmin)
 #           vmax = min(250.0, vmax)

 #       print(f"   vmin/vmax final: {vmin:.2f} / {vmax:.2f}")

        # ── FIGURA ─────────────────────────────────────────────────────
        projection = ccrs.PlateCarree()
        if ax is None:
            fig = plt.figure(figsize=(20, 12))
            ax = plt.axes(projection=projection)
        else:
            fig = ax.get_figure()

        cmap = plt.get_cmap(color_scale)

        img = ax.pcolormesh(lons, lats, data_array,
                            cmap=cmap, vmin=vmin, vmax=vmax,
                            transform=ccrs.PlateCarree(), shading='auto')

        # Mapa
        ax.add_feature(cfeature.BORDERS, edgecolor='black', linewidth=0.4)
        ax.add_feature(cfeature.COASTLINE, edgecolor='black', linewidth=0.5)
        ax.add_feature(cfeature.STATES, edgecolor='black', linewidth=0.4)

        ax.set_extent([lons.min(), lons.max(), lats.min(), lats.max()], crs=ccrs.PlateCarree())

        # Grid y etiquetas
        dx = 5
        xticks = np.arange(np.floor(lons.min()), np.ceil(lons.max()) + 1, dx)
        yticks = np.arange(np.floor(lats.min()), np.ceil(lats.max()) + 1, dx)

        ax.set_xticks(xticks, crs=ccrs.PlateCarree())
        ax.set_yticks(yticks, crs=ccrs.PlateCarree())
        ax.xaxis.set_major_formatter(LongitudeFormatter())
        ax.yaxis.set_major_formatter(LatitudeFormatter())

        # Colorbar
        cb_label = f"{long_name} [{units}]" if units else long_name
        plt.colorbar(img, ax=ax, orientation='vertical', pad=0.03, fraction=0.035, 
                    aspect=30, label=cb_label)

 #       ax.set_title(long_name, color='black', fontsize=14, pad=20, loc='left', fontweight='bold')

# Sets grid characteristics
        ax.gridlines(xlocs=xticks, ylocs=yticks, alpha=0.6, color='gray',
             draw_labels=False, linewidth=0.25, linestyle='--')

        plt.tight_layout()
        plt.savefig(Salida_FIGURA, dpi=200, bbox_inches='tight', facecolor='white')

        print("************************")
        print(f"✅ Figura guardada correctamente: {Salida_FIGURA}")
        print("************************")

        plt.show()
        plt.close(fig)

        return fig, ax, img





 # ════════════════════════════════════════════════════════════
#  4D. FIGURA 4 — Mapa de tendencias + significancia
# ════════════════════════════════════════════════════════════
 
    def plot_netcdf_n_tiempos(Archivo_NC: str, Salida_FIG: str, Salida_NC: str, color_scale: str):
#        print(f"\n📂 Leyendo: {ARCHIVO_NC}")
        VARIABLE = None
        
        datos, lats, lons, nombre_var, long_name, units = leer_netcdf(Archivo_NC, VARIABLE)
        
        # Calcular tendencias
        tau_map, pval_map, pend_map, sig_map, tend_map = calcular_tendencias_grilla(datos)

        fig = plt.figure(figsize=(12, 8))
        fig.patch.set_facecolor('white') ##0d1117
        ax, proj = _base_ax(fig, lats, lons)
 
        cmap = plt.get_cmap(color_scale)

        # Fondo con pendiente
        _pcolormesh_cb(fig, ax, proj, lons, lats, pend_map,
                       cmap, None, None, 'Pendiente Theil-Sen')

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
