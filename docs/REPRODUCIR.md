# Reproducir AssistiveVision y sus resultados

[Inicio](../README.md) · [Datos y métricas](DATOS_Y_RESULTADOS.md) · [Validación](VALIDACION.md)

Hay dos comprobaciones distintas: recalcular las tablas desde las predicciones
archivadas y ejecutar de nuevo la inferencia en Android. La primera verifica
el análisis sin teléfono ni SDK; la segunda comprueba los módulos del prototipo
sobre las mismas fotografías. La compilación de la app se documenta en su repositorio.

## 1. Recalcular todo sin Android

Requisitos: Git, **Python 3.12**, espacio para el clon y los resultados e internet
para instalar dependencias. Se verificó en Linux x86_64. Las instrucciones de
Windows usan el mismo código; esa plataforma no se ejecutó en la validación local.

### Linux y macOS

```sh
git clone https://github.com/diomedescerda/indoor-detect.git
cd indoor-detect
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-analysis.lock.txt
.venv/bin/python scripts/reproduce.py --overlays
```

### Windows PowerShell

```powershell
git clone https://github.com/diomedescerda/indoor-detect.git
cd indoor-detect
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-analysis.lock.txt
.venv\Scripts\python.exe scripts/reproduce.py --overlays
```

Los JPEG, COCO GT, modelo y predicciones están incluidos en Git. No hay submódulos
ni archivos Git LFS que descargar aparte. `requirements-analysis.lock.txt` fija
las dependencias del análisis. El archivo histórico
`Build/Testing/benchmark/requirements.lock.txt` incluye también LiteRT para
inferencia de escritorio y se conserva como registro del entorno original.

El ejecutor:

1. Verifica las **570 sumas SHA-256** archivadas y la estructura de las 198
   imágenes/889 anotaciones. Esto no demuestra calidad semántica de GT.
2. Ejecuta las **22 pruebas** de emparejamiento, estadística y oclusión.
3. Copia los scripts a un espacio temporal para respetar sus rutas históricas
   sin modificar el archivo experimental. Si no hay permisos para enlaces
   simbólicos, copia temporalmente las imágenes.
4. Regenera métricas COCO, precisión/recall/F1, comparaciones bootstrap, escenas,
   montajes, distancia estimada, oclusión y brillo digital. `--overlays` añade
   las 198 superposiciones; las 33 láminas de escenas se generan siempre.
5. Compara **27 tablas CSV completas**, incluyendo encabezados, textos, orden y
   valores. La tolerancia flotante es relativa `1e-10` o absoluta `1e-12`.
   También compara los dos JSON del análisis de brillo.
6. Vuelve a comprobar las 570 sumas originales. El estado final es `passed`
   únicamente si terminan correctamente todos los pasos y comparaciones.

### Archivos que obtendrás

```text
development/runs/saved-results/
├── reproduction_report.json   # estado, versiones, hashes y comparaciones
├── reproduction.log           # salida completa de verificaciones y análisis
├── android/
│   ├── summary.csv, per_image.csv, per_class.csv, metrics.json
│   ├── paired_comparisons.csv, paired_effects.csv
│   ├── scenes/                # conteos, intervalos y 33 láminas
│   ├── scenario1/             # distribuciones por montaje/configuración
│   ├── depth/                 # estimaciones geométricas y discrepancias EXIF
│   └── overlays/              # 198 imágenes si se usa --overlays
├── occlusion/                 # recall, revisión humana y estratos
└── brightness/                # brillo por imagen y tiempos guardados
```

Final esperado: `PASS: 27 full CSV tables match the archive.` Las figuras pueden
variar en metadatos PDF, fuentes o renderizado entre plataformas; se comprueban
las tablas que las sustentan, no igualdad binaria de PNG/PDF. Los tiempos de este
flujo son los guardados, no mediciones nuevas.

Para repetir sin reemplazar resultados:

```sh
.venv/bin/python scripts/reproduce.py --output development/runs/segunda-ejecucion --overlays
```

Si falla, revisar `reproduction.log` y el estado `failed` del JSON. No se reemplaza
la referencia por la salida fallida. Ante un hash diferente, comprobar el commit
y los archivos modificados; no regenerar el manifiesto para ocultar el cambio.
Pasar entre comillas las rutas que contengan espacios.

## 2. Obtener un APK o compilar la app

La app se mantiene en [diomedescerda/AssistiveVision](https://github.com/diomedescerda/AssistiveVision).
Su [guía de compilación](https://github.com/diomedescerda/AssistiveVision/blob/main/docs/REPRODUCING.md)
detalla JDK 21, SDK 37.1 e instalación. Ejecutar `python3 scripts/build_apk.py`
en ese repositorio genera un APK debug con pruebas, lint, manifiesto de compilación
y SHA-256. Incluye detector y voces; no necesita claves privadas ni descargas
adicionales de modelos. El primer build sí necesita internet para Gradle/Maven.

El workflow de la app entrega el paquete como artefacto de GitHub Actions después
de un build correcto. No guardar APKs de más de 100 MB en Git. Las claves debug
de distintas máquinas producen firmas diferentes: reproducir el código/modelos
no implica APKs firmados idénticos byte por byte.

## 3. Repetir la inferencia en Android

Preparar SDK/JDK y arrancar un emulador x86_64 o autorizar un teléfono arm64.
El ejecutor no crea el dispositivo. Android Studio Device Manager permite crear
un emulador. La referencia usa el perfil Pixel 8, API 37, x86_64 y páginas de 16 KB;
su fingerprint está en [los metadatos originales](../Build/Testing/provenance/android_run_metadata.json).

Crear un clon separado de la app evita modificar una copia con trabajo propio:

```sh
# Desde la carpeta que contendrá ambos repositorios:
git clone https://github.com/diomedescerda/AssistiveVision.git AssistiveVision-reference
git -C AssistiveVision-reference checkout 85c852ddcb543bce1bd69ad0db307f895d597881
cd indoor-detect
export JAVA_HOME=/path/to/jdk-21
export ANDROID_HOME="$HOME/Android/Sdk"
"$ANDROID_HOME/platform-tools/adb" devices
.venv/bin/python scripts/run_android_benchmark.py --app ../AssistiveVision-reference --sdk "$ANDROID_HOME" --serial emulator-5554
```

Sustituir rutas y serial por los reales. En Windows usar `.venv\Scripts\python.exe`,
variables PowerShell y el SDK local. El ejecutor copia la instrumentación exacta
si falta; si ya existe un test distinto, se detiene para conservarlo.

Comprueba el modelo y cinco módulos de producción, construye e instala los APKs,
prepara las fotos, ejecuta la instrumentación y valida las 198 identidades de
imagen y hashes GT/modelo antes de calcular métricas. Usa el mismo intérprete
Python que lo inicia, sin depender del antiguo `benchmark/.venv`. Ante conflictos
de firma o dispositivos no autorizados se detiene sin desinstalar la app.

La salida nueva está en `development/runs/android-<fecha UTC>/`: `android.json`,
`android-instrumentation.log`, `comparison_to_archive.json` y `metrics/`. Se puede elegir una carpeta nueva
con `--output development/runs/mi-android`. Cambiar módulos/modelo exige pasar
`--allow-different-source` y queda registrado como una ejecución distinta.

### Valores de referencia

Confianza 0,30, IoU mínimo 0,50, hasta 15 detecciones del detector y hasta dos
objetos en el análisis de selección para voz:

| Configuración | TP | FP | FN | F1 |
|---|---:|---:|---:|---:|
| Cabeza 1x | 56 | 20 | 73 | 0,5463414634 |
| Cabeza 0,5x | 70 | 36 | 94 | 0,5185185185 |
| Pecho 1x | 65 | 21 | 59 | 0,6190476190 |
| Pecho 0,5x | 77 | 32 | 76 | 0,5877862595 |
| Gorillapod 1x | 75 | 29 | 70 | 0,6024096386 |
| Gorillapod 0,5x | 82 | 31 | 92 | 0,5714285714 |

La ejecución local del 5 de noviembre de 2026 reprodujo los mismos arrays de
predicciones para las 198 fotos. En otro dispositivo/runtime pueden cambiar
detalles flotantes o detecciones cercanas al umbral; informar las diferencias.
La latencia no debe igualarse a la referencia: depende del equipo. No mezclar
las nuevas mediciones con las guardadas ni atribuir tiempos de emulador a un Pixel 8 físico.

## 4. Inferencia de escritorio opcional

Este runtime usa otro decodificador/redimensionado y no sustituye a Android:

```sh
.venv/bin/python -m pip install -r Build/Testing/benchmark/requirements.lock.txt
.venv/bin/python Build/Testing/benchmark/run_desktop.py --model Build/Testing/benchmark/models/efficientdet-lite2-detection-metadata.tflite --output development/runs/desktop-new.json
.venv/bin/python Build/Testing/benchmark/evaluate.py development/runs/desktop-new.json --output development/runs/desktop-new-metrics
```

Elegir nombres nuevos: el ejecutor histórico de escritorio sí puede sobrescribir
su `--output`. La instalación mínima del análisis evita este runtime opcional.

## 5. Otros materiales

La [comparación histórica de modelos](HISTORICO.md) tiene un ejecutor separado.
Recupera los seis binarios exactos del historial Git y compara las tablas de
escritorio con un runtime fijado y declarado. No requiere descargar nuevos modelos;
no pretende recuperar las mediciones de latencia de un teléfono Redmi diferente.

Los constructores Word de `development/editorial/scripts/` son herramientas editoriales,
no requisitos para verificar resultados. El informe revisado incluye cambios
manuales: no ejecutar un constructor anterior sobre esa copia. La
[guía documental](../Documents/README.md) explica las versiones.

El README y los verificadores originales del paquete se conservan en `development/annotation_drafts/Testing/`; el mapa de reubicación mantiene verificables sus hashes. El README actual de `Build/Testing/` y `LEEME.md` remiten a los ejecutores vigentes.

Si al crear el entorno Python dentro de una aplicación AppImage el intérprete se identifica como la propia AppImage o falla `ensurepip`, abrir una terminal externa. En Linux también se puede quitar esa variable solo para el comando: `env -u APPIMAGE python3.12 -m venv .venv`. No es necesario modificar Python ni el entorno global.
