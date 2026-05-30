# Indices-ETCCDI-precipitacion
Paquete en Python para calcular y graficar índices climáticos de precipitación ETCCDI para datos en malla (NetCDF) y in situ (TXT)

<br><br>

# Versión:
1.0
<br><br>



# Tutorial


Aquí encontrarás la definición de los índices y ejemplos de cuadernos de Jupyter. [Enlace](ejemplos/descripcion.txt)


<br><br>



# Instalación paso a paso
<br><br>

- [Windows](Instalacion/Instalacion_ETCCDI-precipitacion_Windows.md) 
- [Linux](Instalacion/Instalacion_ETCCDI-precipitacion_Linux.md)
- [MacOS](Instalacion/Instalacion_ETCCDI-precipitacion_MacOS.md)

<!--
##3.1 Instalación en Linux (Ubuntu / Debian)

Paso 1: Instalar CDO y dependencias del sistema

```
sudo apt update
```

```
sudo apt install cdo python3-pip python3-venv git -y
```

Paso 2: Clonar el repositorio corregido
```
git clone https://github.com/OmarRamosPerez/Indices-ETCCDI-precipitacion-.git
```
```
cd Indices-ETCCDI-precipitacion-
```

Paso 3: Crear entorno virtual (recomendado)
```
python3 -m venv venv_etccdi
```
```
source venv_etccdi/bin/activate
```


Paso 4: Instalar el paquete en modo editable (para desarrollo, los cambios al código se reflejan al instante):
```
pip install -e .
```

Paso 5: Verificar instalación
```
python3 -c "from ETCCDI_precipitacion.Procesamiento import ETCCDI_precip_procesamiento; print('OK')"
```
-->

# Verificación de instalación
<br><br>

En una nueva anaconda prompt o terminal, activar el entorno "ETCCDI_precipitacion"
```
conda activate ETCCDI_precipitacion
```  
Enseguida escribir las siguientes líneas
```
python -c "
from ETCCDI_precipitacion import ETCCDI_precip_malla, ETCCDI_precip_in_situ
from ETCCDI_precipitacion import ETCCDI_precip_plot_in_situ, ETCCDI_precip_plot_malla
print('✅ Paquete instalado correctamente')
"
```
<br><br>
Resultado esperado

![Felicitaciones paquete "ETCCDI_precipitacion"]() 


# Asistencia

Si tienes alguna pregunta, no dudes en escribir a:

omar.ramos@unison.mx


Puedes escribirme en español o inglés. 
