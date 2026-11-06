# Figuras de AssistiveVision

`interfaz_app.png` reúne dos capturas reales de la aplicación en español:
captura manual y configuración. Se obtuvieron del APK público en un emulador
Android. La habitación virtual del emulador ilustra la interfaz; no forma parte
del conjunto experimental. Las capturas completas están en `sources/ui/`.

`escenas_ejemplo.png` reúne seis fotografías originales de
`Build/Testing/data/`: dormitorio, sala/comedor, cocina, baño, espacio de trabajo
y terraza. Cada panel identifica su grupo y archivo. Son ejemplos visuales,
no un recuento de recintos físicos distintos.

Ambas figuras usan fondo blanco, letras de panel y rótulos negros en Liberation
Sans. Las imágenes se conservan completas, sin recortes, retoques ni detecciones
superpuestas. El registro [fuentes_fotograficas.json](fuentes_fotograficas.json)
identifica archivos, grupos, configuración de la aplicación y hashes SHA-256.

## Regenerar los paneles

Con el entorno editorial descrito en la
[guía de reconstrucción](../../development/editorial/revision/README.md), desde
la raíz del repositorio:

```sh
.venv-editorial/bin/python development/editorial/scripts/build_report_photos.py
```

En Linux instalar Liberation Sans si no está disponible. En otros sistemas, o
para indicar su ubicación explícita, añadir
`--font /ruta/a/LiberationSans-Regular.ttf`. En Windows usar
`.venv-editorial\Scripts\python.exe`. El constructor comprueba los hashes de
las fotografías y capturas antes de componer las dos figuras.

## Soportes

Los paneles (a) y (b) de la Figura 4.2 muestran el **Soporte de cabeza + accesorio para celular** y el
**Arnés Pecho Innovo+ para GoPro y celulares**, identificados mediante las dos
capturas de las publicaciones facilitadas por el autor. Los originales están
en `sources/harnesses/`; el registro de fuentes conserva título, enlace,
identificador, hash y rectángulo de recorte en píxeles.

El constructor Word inserta ambas capturas completas y aplica un recorte nativo
de Word para mostrar solo la fotografía comercial, sin precios ni controles de
la tienda. No retoca ni reconstruye el producto. Los paneles (a) y (b) usan fondo
blanco y rótulos negros. El pie enlaza las publicaciones y aclara que son
ilustraciones comerciales, no fotografías del montaje experimental. El teléfono
y la cámara que aparecen en las publicaciones también son ilustrativos.
El panel (c) muestra un **palo de selfie extensible con trípode, de diseño L01**,
identificado por el autor entre las opciones visuales. El original comercial
está en `sources/mounts/palo_selfie_L01_referencia.jpg`; el constructor conserva
sus bytes y aplica un recorte nativo de Word que muestra el soporte abierto.
El pie enlaza eMAG y lo presenta como referencia de diseño, sin atribuir una
marca exacta ni afirmar cómo se usaron las patas o el mando en el experimento.

Los gráficos `montajes_cajas.png`, `configuraciones_cajas.png`,
`seleccion_metricas.png` y `seleccion_escenas.png` se regeneran con
`scripts/build_report_figures.py` desde los mismos resultados guardados. Sus
rótulos usan «Palo de selfie». Para regenerarlos, usar el entorno de análisis de
`requirements-analysis.lock.txt`, descrito en `docs/REPRODUCIR.md`. La [correspondencia de nombres](../../docs/NOMBRES_DE_MONTAJES.md)
explica las claves conservadas en el archivo original.

La reproducción de esta figura se realiza al ejecutar
`development/editorial/scripts/revise_tutor_feedback.py`, según la guía
editorial; no necesita acceder a las páginas comerciales.
