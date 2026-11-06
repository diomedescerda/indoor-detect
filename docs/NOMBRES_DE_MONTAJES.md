# Nombres de los montajes de captura

El autor confirmó el 6 de noviembre de 2026 que el tercer soporte era un **palo de
selfie extensible con patas plegables de trípode**, de diseño similar al L01
mostrado en la imagen de referencia. En el informe se abrevia como **palo de
selfie**. La marca, el modelo exacto, la extensión y el uso de las patas o del
mando durante cada captura no quedaron registrados y no se deducen de la imagen.

| Nombre del soporte | Etiqueta en el informe | Identificadores del archivo original |
|---|---|---|
| Arnés de cabeza | Cabeza | `head_harness`, `Head` |
| Arnés de pecho | Pecho | `chest_harness`, `Chest` |
| Palo de selfie con trípode | Palo de selfie | `gorillapod`, `Gorillapod`, `GorillaPod` |

Las claves de la tercera fila son denominaciones históricas incorrectas del
mismo soporte, no otro montaje ni una configuración adicional. Los seis casos
siguen siendo cabeza, pecho y palo de selfie, cada uno con lente nominal 1x y
0,5x. Las 198 fotos, las 889 anotaciones, los 33 grupos y todos los valores
numéricos se conservan.

Los CSV, JSON, scripts y figuras originales de `Build/Testing/` forman un archivo
verificable mediante SHA-256. Se conservan con sus nombres originales para que
`scripts/verify_archive.py` y la comparación exacta de 27 CSV y dos JSON sigan
siendo válidos. Sus rótulos históricos deben leerse con la correspondencia de
esta tabla. Lo mismo se aplica a las copias históricas de manuscritos y revisiones
editoriales, incluido el Word comentado de la tutora.

La documentación actual y el informe corregido usan los nombres de la segunda
columna. `scripts/build_report_figures.py` lee las claves originales y produce
los gráficos de publicación con rótulos corregidos en `Documents/Figures/`;
no sustituye los resultados archivados. La fuente comercial y los hashes de las
imágenes están en [el registro de figuras](../Documents/Figures/fuentes_fotograficas.json).
La imagen L01 es una referencia de diseño confirmada por el autor, no una foto
de su unidad ni evidencia de su colocación experimental.
