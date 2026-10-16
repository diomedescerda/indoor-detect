# Análisis observacional de oclusión

Se reutilizan las 198 fotografías, las 889 instancias de la anotación COCO revisada y las predicciones archivadas. No se vuelve a ejecutar el detector ni se modifica `Build/Testing/labels.json`.

## Protocolo de etiquetado

La unidad es una instancia anotada, identificada por `annotation_id`. Se inspeccionan la fotografía y la caja GT, sin mostrar predicciones ni aciertos del detector. Las etiquetas cualitativas describen obstrucción por otro objeto; no se estiman porcentajes de superficie oculta.

- `none`: no se identifica una obstrucción externa del objeto.
- `partial`: otro objeto oculta parte del objetivo, pero quedan rasgos identificativos sustanciales.
- `heavy`: la obstrucción externa oculta la mayor parte de la extensión identificativa esperada; debe existir evidencia visual clara.
- `uncertain`: no se distingue de forma fiable oclusión, perspectiva, geometría o contexto. No se fuerza una categoría.

El corte por borde (`truncation`) se registra por separado. Un objeto pequeño, lejano o visto de perfil no se considera ocluido sólo por esas condiciones. La autooclusión por geometría tampoco se cuenta como obstrucción externa. Se conservan un motivo breve y confianza alta/media/baja.

Las etiquetas iniciales se producen mediante inspección visual con GPT-6 Astra, razonamiento High. Son provisionales hasta revisión humana. Dos lotes de trabajo no equivalen a dos revisores independientes: cada instancia recibe una primera etiqueta. La revisión por el mismo modelo no constituye acuerdo interobservador humano.

## Evaluación

Se aplica el emparejamiento de clase y caja del benchmark (IoU mínimo 0,50, confianza 0,30), conservando los modos detector y lista de hasta dos objetos. La métrica principal es recall: TP / GT; FN = GT − TP. No se asigna nivel de oclusión a falsos positivos sin una instancia de referencia.

Los intervalos percentiles del 95 % se estiman con 10 000 remuestreos de los 33 grupos completos de captura (semilla 20261013). Se describen también resultados por clase, configuración, truncamiento y tamaño aparente (área de caja / área de imagen: pequeño < 0,01; mediano 0,01–<0,10; grande ≥ 0,10). Las celdas escasas requieren cautela. La incertidumbre de las etiquetas no queda incluida automáticamente en los intervalos bootstrap.

El análisis se limita a los objetos ya anotados. No incluye objetos completamente ocultos o ausentes de la anotación y no vuelve a auditar su exhaustividad. La asociación entre oclusión y detección no aísla una causa: clase, tamaño, escena y posición pueden variar simultáneamente. No se atribuyen diferencias exclusivamente a oclusión.

## Revisión del autor

Antes de usar conclusiones definitivas, revisar los casos inciertos, de baja confianza y fuertemente ocluidos, además de una muestra aleatoria de los demás casos. Registrar qué casos se revisaron y cuáles cambiaron. Para medir acuerdo, un segundo revisor debe etiquetar de forma independiente antes de ver las etiquetas iniciales.

## Reproducción

Con el entorno Python del benchmark (NumPy y pycocotools):

```sh
python Build/Testing/benchmark/analyze_occlusion.py
python Build/Testing/occlusion/build_review.py
```

Abrir `Build/Testing/occlusion/review.html` en el navegador. Utiliza las fotografías locales de `../data/`; no sube imágenes a un servicio. La descarga guarda todas las etiquetas y marca cuáles revisó el autor. Los cambios no se escriben directamente al archivo fuente: descargar antes de cerrar la página. Para continuar, cargar el JSON descargado con «Restaurar JSON».

Después de revisar y descargar, recalcular con `python Build/Testing/benchmark/analyze_occlusion.py --labels /ruta/occlusion_author_review.json`. Regenerar el visor y el informe después del análisis. Los JSON `gt_review_issues_batch_*.json` registran posibles problemas de clase, duplicados e identidad que requieren revisión separada; el visor de oclusión no modifica las cajas ni categorías GT.

Con cero aciertos en una celda, el intervalo percentil bootstrap puede ser [0,0]; esto refleja la muestra remuestreada y no demuestra una probabilidad poblacional nula.

### Guardado durante la revisión

«Guardar y marcar revisión del autor» conserva la etiqueta en la sesión actual y muestra confirmación junto al botón; permanece en el mismo objeto. «Guardar y siguiente» guarda y avanza. La marca ✓ identifica las instancias revisadas. El contador aumenta sólo la primera vez que se revisa una instancia, no al actualizarla. Para conservar el trabajo al cerrar o recargar, usar «Descargar etiquetas revisadas» y luego «Restaurar JSON» al continuar.

### Revisión del autor importada (2026-10-16)

`author_review.json` conserva la descarga original: 215 de 889 instancias marcadas como revisadas, con cambios en 14 registros. Las otras 674 mantienen las etiquetas iniciales por decisión del autor; no se presentan como revisadas individualmente. El analizador utiliza este archivo automáticamente cuando existe, salvo que se indique otro mediante `--labels`. Se regeneraron métricas, visor e informe sin repetir inferencia ni alterar GT.
