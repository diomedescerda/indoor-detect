# AssistiveVision: datos, resultados y documentación

Material de investigación de un prototipo Android que reconoce diez clases de
objetos y anuncia sus posiciones en español o inglés. Este repositorio contiene
las fotografías, anotaciones, experimentos e informe; el código completo de la
aplicación está en [AssistiveVision](https://github.com/diomedescerda/AssistiveVision),
cuya rama principal es **`main`**.

## Comenzar según lo que necesitas

| Quiero… | Abrir |
|---|---|
| Instalar la app o conseguir un APK | **[Descargar APK](https://github.com/diomedescerda/AssistiveVision/releases/latest/download/AssistiveVision-1.0-debug.apk)** · [Instalación y uso](https://github.com/diomedescerda/AssistiveVision/blob/main/docs/USO.md) |
| Compilar la app desde cero | [Código y compilación reproducible](https://github.com/diomedescerda/AssistiveVision/blob/main/docs/REPRODUCING.md) |
| Reproducir las tablas y figuras | [Guía de reproducción](docs/REPRODUCIR.md) y comandos de abajo |
| Entender los datos y resultados | [Datos, métricas y alcance](docs/DATOS_Y_RESULTADOS.md) |
| Leer el informe revisado | [Word revisado](Documents/Informe_Final_AssistiveVision.docx) |
| Revisar qué se comprobó | [Registro de validación](docs/VALIDACION.md) |
| Localizar antecedentes y archivos | [Guía de lectura](Documents/GUIA_DE_LECTURA.md) · [Mapa del repositorio](Documents/MAPA_DEL_REPOSITORIO.md) |

## Reproducir resultados sin Android

Se necesita **Python 3.12**, Git e internet para instalar las dependencias.
No se necesitan Android Studio, GPU, Zotero ni una cuenta de Roboflow.
Las imágenes, anotaciones, modelo y predicciones ya están incluidos en Git.
Si `python3.12` no existe o se usa una terminal AppImage, seguir
[la preparación del entorno](docs/REPRODUCIR.md#antes-de-empezar) antes de ejecutar los comandos.

```sh
git clone https://github.com/diomedescerda/indoor-detect.git
cd indoor-detect
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-analysis.lock.txt
.venv/bin/python scripts/reproduce.py --overlays
```

En Windows usar `.venv\Scripts\python.exe` en los dos últimos comandos.
La [guía completa](docs/REPRODUCIR.md) incluye PowerShell, resultados esperados y
una nueva ejecución de inferencia Android.

El comando comprueba las 570 sumas originales mediante un mapa de reubicación, valida la anotación,
ejecuta 22 pruebas y regenera las métricas, comparaciones, figuras y ejemplos.
Compara **27 tablas CSV completas y dos JSON** con la referencia. Incluye
montajes/lentes, grupos de captura, oclusión, distancia estimada y brillo digital.

Todo se escribe en `development/runs/saved-results/`, junto con
`reproduction_report.json` y `reproduction.log`. Si esa carpeta existe, el
comando pide elegir otra con `--output`; conserva intactos los datos, resultados
y manuscritos archivados. El [workflow de GitHub Actions](.github/workflows/reproduce.yml)
ejecuta la misma comprobación y adjunta los resultados a cada ejecución.

## Qué resultados se pueden comprobar

El estudio principal contiene **198 fotografías**, **889 instancias anotadas** y
**33 grupos** con seis configuraciones: cabeza, pecho y palo de selfie con trípode, cada uno con
lente nominal 1x y 0,5x. Se tomaron con iPhone 12 Pro Max y se procesaron con
los módulos Android de producción en un emulador con perfil Pixel 8.

Palo de selfie 0,5x obtuvo más detecciones correctas (**82**); pecho 1x tuvo mayor
F1 (**61,9 %**). Son criterios distintos y la selección de configuración es
exploratoria. No son 33 habitaciones independientes ni una prueba de claridad
del audio. La [guía de datos](docs/DATOS_Y_RESULTADOS.md) explica las condiciones.

También puede repetirse la inferencia: el [ejecutor Android](scripts/run_android_benchmark.py)
construye la app, prepara el conjunto y guarda una ejecución nueva. En la
validación del 5 de noviembre de 2026 se reprodujeron exactamente las predicciones
de las 198 imágenes. Las latencias cambiaron; los tiempos de emulador no son
mediciones de rendimiento de un teléfono físico.

La [comparación histórica de seis modelos](docs/HISTORICO.md) es otro
experimento. Sus binarios originales se recuperaron del historial Git mediante
SHA-256. Un ejecutor separado permite repetir la evaluación de escritorio normal
y panorámica con el runtime declarado y comparar sus tablas; no reproduce las
latencias históricas del Redmi.

## Separación del material intermedio

Los borradores de anotación, previews, notas, revisiones, herramientas editoriales
y logs están reunidos en `development/`. Las nuevas ejecuciones van a
`development/runs/`, ignorado por Git. La anotación final, los modelos y las
tablas científicas permanecen en `Build/`; el Word final está directamente en
`Documents/`. [La guía del directorio](development/README.md) explica qué contiene
cada grupo y cómo se mantienen verificables las rutas originales.

## Mapa breve

| Ruta | Contenido |
|---|---|
| [`Build/Testing/data/`](Build/Testing/data) | 198 JPEG originales |
| [`Build/Testing/labels.json`](Build/Testing/labels.json) | Anotación final COCO; los borradores no la sustituyen |
| [`Build/Testing/capture_groups.csv`](Build/Testing/capture_groups.csv) | Archivo, grupo, montaje, lente y SHA-256 |
| [`Build/Testing/benchmark/results/android.json`](Build/Testing/benchmark/results/android.json) | Predicciones y tiempos de referencia |
| [`Build/Testing/benchmark/results/android/`](Build/Testing/benchmark/results/android) | Tablas, gráficos y ejemplos |
| [`Build/Testing/provenance/`](Build/Testing/provenance) | Commit, hashes y copias de los módulos evaluados |
| [`Build/Testing/occlusion/`](Build/Testing/occlusion) | Etiquetas adicionales y revisión parcial del autor |
| [`Documents/`](Documents/README.md) | Informe final, bibliografía, figuras, propuesta y presentaciones |
| [`scripts/`](scripts) | Ejecución reproducible sin sobrescribir el archivo experimental |

[Cómo contribuir](CONTRIBUTING.md). Para una copia existente, guardar los cambios
propios antes de actualizar Git. Los constructores históricos del manuscrito y
algunos scripts antiguos conservados en `development/` sí sobrescriben sus salidas: para reproducir, utilizar
los nuevos comandos de esta página.

La [correspondencia de nombres de montajes](docs/NOMBRES_DE_MONTAJES.md) aclara las claves
históricas del archivo y su equivalencia con el palo de selfie con trípode.
