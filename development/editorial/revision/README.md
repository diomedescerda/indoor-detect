# Informe revisado de AssistiveVision

Esta revisión aplica los comentarios de la tutora contenidos en el archivo Word recibido el 5 de noviembre de 2026 y las indicaciones adicionales del autor. El manuscrito histórico y los resultados experimentales permanecen conservados.

- [Informe revisado](../../../Documents/Informe_Final_AssistiveVision.docx).
- [Comparación de cambios](Cambios_tutor_AssistiveVision.html), con texto anterior, texto revisado y respuesta a cada comentario.
- [Validación editorial](validacion_revision.json), [referencias APA](referencias_apa.json) y [comentarios originales](comentarios_tutora.json).

La revisión recupera el título de la propuesta, integra antecedentes y fundamentos, explica las siglas al introducirlas, traslada metodología y candidatos al capítulo 2, amplía el protocolo del capítulo 4 y presenta las conclusiones en relación con los objetivos. Conserva un único anexo de repositorios y reproducción. La bibliografía y las citas siguen el sistema APA de autor y fecha; el diseño de página conserva la plantilla institucional.

## Actualización de repositorios y reproducción

El Word incorpora los ejecutores verificados y las instrucciones para compilar,
instalar y obtener el APK de depuración. El anexo único distingue la reproducción
exacta del estudio principal (27 CSV, dos JSON y predicciones de 198 imágenes),
las pruebas funcionales completadas y las 16 diferencias de la repetición
histórica tras recuperar los seis modelos desde Git. Las tablas originales no
se sustituyen por nuevos valores; las latencias de cada ejecución permanecen
separadas. Se actualizaron también los pasajes relacionados de los capítulos 2,
3 y 4 y las conclusiones. El build remoto de main d78ffa7 terminó correctamente;
el APK se publica como descarga individual en GitHub Releases.

## Campos del autor e imágenes

En la sección 4.1.1 hay un campo explícito para identificar el número de recintos, su correspondencia con los grupos y el criterio y condiciones de captura. Las tipologías y ejemplos que lo acompañan se derivan de las fotografías y de las anotaciones, sin confundir 33 grupos con 33 habitaciones.

Hay tres marcadores de imágenes: pantallas de interfaz en la Figura 3.4, espacios en la Figura 4.1 y soportes o arneses en la Figura 4.2. Reemplazar el texto del marcador por las imágenes del autor y conservar el pie. Al insertar imágenes cambiará la paginación; actualizar los índices y volver a comprobar el documento.

La sección 4.9 y las conclusiones explican el alcance real del audio: se verificaron composición textual, configuración y ejecución funcional de la síntesis española en modo avión; no existe una evaluación perceptual con oyentes en la evidencia archivada. El protocolo descrito allí es una propuesta de continuación, no un ensayo realizado. No se inventaron participantes, puntuaciones de claridad ni condiciones físicas de adquisición.

## Contenido de los repositorios

[indoor-detect](https://github.com/diomedescerda/indoor-detect) contiene el informe, datos y análisis. [AssistiveVision](https://github.com/diomedescerda/AssistiveVision) contiene la aplicación Android.

El mapa completo está en [MAPA_DEL_REPOSITORIO.md](../../../Documents/MAPA_DEL_REPOSITORIO.md). Para el estudio posterior, `Build/Testing/labels.json` es la referencia final de 889 instancias en 198 fotografías; `capture_groups.csv` relaciona los 33 grupos y sus configuraciones; `benchmark/results/android.json` conserva predicciones y tiempos. El modelo está en `benchmark/models/` y la procedencia en `provenance/`. Los borradores no sustituyen la referencia final.

La comparación inicial está en `Build/models_comparison/results/`. Se conservan
las 80 imágenes/257 anotaciones y los seis binarios son recuperables del historial
Git con sus hashes exactos. La [guía histórica](../../../docs/HISTORICO.md) explica
la recuperación y repetición de escritorio con runtime declarado; las latencias
originales de Redmi corresponden a otro entorno. El estudio posterior de 198
fotografías incluye modelo, GT y predicciones para recalcular todas sus métricas.

## Recalcular las métricas archivadas

Usar la [guía de reproducción verificada](../../../docs/REPRODUCIR.md). Desde la raíz:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-analysis.lock.txt
.venv/bin/python scripts/reproduce.py --overlays
```

Regenera las métricas, brillo y tiempos guardados, oclusión, distancia y figuras
en `development/runs/saved-results/`; comprueba 27 CSV y dos JSON sin sobrescribir
el manuscrito ni el paquete original. En Windows usar `.venv\Scripts\python.exe`.

## Compilar y repetir Android

La [guía de la aplicación](https://github.com/diomedescerda/AssistiveVision/blob/main/docs/REPRODUCING.md)
explica SDK/JDK, build, APK y uso. La [guía experimental](../../../docs/REPRODUCIR.md#3-repetir-la-inferencia-en-android)
prepara un clon de referencia y una nueva ejecución Android, con salidas separadas
y sin depender de `benchmark/.venv`. El registro está en [VALIDACION.md](../../../docs/VALIDACION.md).

## Uso básico del prototipo

[Descargar el APK](https://github.com/diomedescerda/AssistiveVision/releases/latest/download/AssistiveVision-1.0-debug.apk), abrir el archivo e instalarlo. Abrir AssistiveVision y conceder permiso de cámara. Colocar el teléfono con la cámara trasera despejada y el soporte estable. En Configuración seleccionar idioma, velocidad, confianza, máximo de objetos y vista previa. Pulsar **Capturar fotograma**, escuchar la descripción y esperar a que se libere la vista antes de la siguiente captura. Las regiones describen la imagen según la orientación de la cámara. El sistema no mide distancias ni identifica una ruta libre.

## Reconstruir esta revisión

Los constructores históricos de `development/editorial/scripts/update_informe.py` generan la versión anterior. No ejecutarlos sobre esta revisión para incorporar cambios: volverían a introducir su estructura y bibliografía numérica.

Con Python y `python-docx`, `lxml` y Pillow disponibles, desde la raíz:

```sh
python development/editorial/scripts/revise_tutor_feedback.py development/editorial/review/2026-11-05_original_comentado.docx
```

El constructor valida que la entrada sea el archivo anotado de 542 párrafos y conserva sus partes de medios y tablas. Escribe el Word final en `Documents/Informe_Final_AssistiveVision.docx` y genera los comprobantes de esta carpeta a partir del contenido editorial de `development/editorial/scripts/tutor_revision_content.py` y del anexo actualizado en `development/editorial/scripts/reproduction_revision_content.py`. Para conservar una edición manual futura, trasladarla también a ese contenido antes de reconstruir. El archivo original recibido se conserva sin alterar en `development/editorial/review/2026-11-05_original_comentado.docx`.

La paginación se verifica después de renderizar el Word. `development/editorial/scripts/refresh_tutor_pages.py` permite materializar los números de los índices a partir del PDF de comprobación, sin guardar el documento mediante LibreOffice:

```sh
python development/editorial/scripts/refresh_tutor_pages.py /ruta/al/render_verificado.pdf
```

Volver a renderizar después de actualizar índices. Las páginas PNG y el PDF de comprobación son archivos de revisión interna; el documento editable es el Word enlazado arriba.
