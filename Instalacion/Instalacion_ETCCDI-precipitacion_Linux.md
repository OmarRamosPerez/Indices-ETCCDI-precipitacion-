## Pasos para la instalación en Linux 

## 1) Instala Anaconda 

La forma más fácil de instalar ETCCDI_precipitacion es hacerlo dentro de un nuevo entorno de Anaconda. \
Si aún no tienes conda, consulta cómo instalarlo aquí [Anaconda Linux](https://www.anaconda.com/docs/getting-started/anaconda/install/linux-install).

## 2) Clona el repositorio

En anaconda prompt
```
git clone https://github.com/OmarRamosPerez/Indices-ETCCDI-precipitacion-.git
```

## 2-1) Ir al directorio Indices-ETCCDI-precipitacion
```
cd Indices-ETCCDI-precipitacion-
```
## 3) Crear el entorno
Utiliza conda para crear el nuevo entorno e instalar las dependencias
```
conda env create -f environment.yml
```
Esto creará automáticamente el entorno llamado ETCCDI_precipitacion con todas las dependencias. \
⏳ Puede tardar varios minutos.

## 4) Activa el entorno
Sin salir del Anaconda prompt
```
conda activate ETCCDI_precipitacion
```
## 5) Instala el paquete
```
pip install -e .
```
## 6) Replicación de Ejemplos
Sin salir del Anaconda prompt, instalar el entorno como kernel para que aparezca disponible en Jupyter.
```
python -m ipykernel install --user --name ETCCDI_precipitacion --display-name "ETCCDI_precipitacion"
```
