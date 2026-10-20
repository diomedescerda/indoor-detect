# Guía de lectura para la profesora

Esta guía permite revisar el proyecto sin ejecutar código. Actualizada el 20 de octubre de 2026. El [informe final](Informe_Final_Trabajo_de_Grado_AssistiveVision.docx) es el manuscrito principal; este documento facilita localizar su evidencia.

## Recorrido recomendado

1. Leer la [propuesta de pasantía](Propuesta%20Pasantia%20de%20Investigación%20-%20Diomedes%20Cerda.pdf) para conocer objetivos y fases.
2. Abrir el [informe final](Informe_Final_Trabajo_de_Grado_AssistiveVision.docx): el capítulo 2 presenta la selección de modelos; el 3, la arquitectura y los módulos; el 4, la evaluación; el 5, conclusiones y recomendaciones.
3. Consultar las tablas y gráficos enlazados abajo para contrastar los resultados con sus archivos fuente.
4. Para revisar el formato, usar la [guía institucional](Templates/Guia_Institucional_Informe_Final.docx). Para modificar el manuscrito, seguir [Documents/README.md](README.md).

## Qué se hizo y dónde se puede revisar

| Trabajo | Evidencia principal | Qué permite comprobar |
|---|---|---|
| Selección inicial de DNN | [Resultados de escritorio](../Build/models_comparison/results/desktop.md), [benchmark Redmi Note 13](../Build/models_comparison/results/android.md), capítulo 2 | Comparación histórica de modelos y coste de ejecución |
| Desarrollo e integración Android | Capítulo 3, [repositorio de la app](https://github.com/diomedescerda/AssistiveVision), [código archivado](../Build/Testing/provenance/app_source/) | Captura, preprocesamiento, detección, coordenadas y composición de salida |
| Referencia para evaluar detecciones | [198 fotografías](../Build/Testing/data/), [GT COCO](../Build/Testing/labels.json), [exportación corregida](../Build/Testing/annotation_history/roboflow_reviewed.coco.json) | Cajas y clases de referencia corregidas por el autor |
| Montajes y lentes | [Métricas por configuración](../Build/Testing/benchmark/results/android/summary.csv), [comparaciones por grupo](../Build/Testing/benchmark/results/android/scenes/report.txt) | Cobertura, aciertos, errores y diferencias pareadas |
| Distancia aproximada | [Análisis de profundidad](../Build/Testing/benchmark/results/android/depth/report.txt), [bandas](../Build/Testing/benchmark/results/android/depth/depth_bands.csv) | Recall por bandas estimadas mediante geometría y EXIF |
| Tiempos e iluminación | Secciones 4.7–4.8, [evidencia derivada](Review/proposal_evidence/summary.json) | Distribución de tiempos archivados y brillo digital de las imágenes |
| Oclusión | Sección 4.8.1, [protocolo](../Build/Testing/occlusion/README.md), [tabla de resultados](../Build/Testing/occlusion/results/severity.csv) | Recall según obstrucción visible del objeto |
| Trazabilidad | [Metadatos Android](../Build/Testing/provenance/android_run_metadata.json), [registro de revisión](Review/2026-10-14_revision.md) | Versiones, procedencia y cambios del manuscrito |

## Cómo interpretar la comparación de configuración

Cada grupo de captura contiene seis fotos sucesivas: cabeza 1x, cabeza 0,5x, pecho 1x, pecho 0,5x, Gorillapod 1x y Gorillapod 0,5x. [capture_groups.csv](../Build/Testing/capture_groups.csv) vincula cada imagen con su configuración. Los 33 grupos no equivalen necesariamente a 33 habitaciones independientes.

Gorillapod 0,5x obtuvo 82 detecciones correctas sobre 174 instancias visibles; pecho 1x obtuvo 65 sobre 124. El primero favorece el conteo recuperado; el segundo tiene mayor F1 (61,9% frente a 57,1%). Frente a pecho 0,5x, la ventaja media de conteo de Gorillapod 0,5x tiene un intervalo que incluye cero. Por ello el informe propone una configuración provisional, sin establecer un ganador universal.

«Visibles» cuenta instancias anotadas dentro de cada fotografía; un mismo objeto puede aparecer en varias fotos. «Correctas» exige clase coincidente y solapamiento de caja IoU ≥ 0,50, con confianza ≥ 0,30. La lista de «hasta dos objetos» aproxima la selección que se entrega al módulo de voz; no mide comprensión ni calidad del audio.

## Gráficos y ejemplos

- [Comparación por configuración: precisión, recall y F1](Figures/seleccion_metricas.png).
- [Distribución de objetos correctos por montaje](../Build/Testing/benchmark/results/android/scenario1/boxplot_mount.png).
- [Distribución por montaje y lente](../Build/Testing/benchmark/results/android/scenario1/boxplot_configuration.png).
- [Recall por distancia estimada](../Build/Testing/benchmark/results/android/depth/depth_recall.png).
- [33 láminas con las seis vistas de cada grupo](../Build/Testing/benchmark/results/android/scenes/sheets/).
- [Ejemplos con predicciones superpuestas](../Build/Testing/benchmark/results/android/overlays/).

El mapa denso de conteos por escena se conserva como análisis auxiliar, pero se retiró del informe por redundancia. El manuscrito incluye una selección de figuras integrada con su texto.

## Alcance que acompaña los resultados

La comparación histórica de modelos en Redmi y la reproducción del conjunto de 198 fotos en emulador son experimentos distintos. La distancia es una estimación, no una medida física; el brillo digital no es iluminancia en lux. La oclusión se etiquetó visualmente con asistencia de IA: el autor revisó 215 de 889 instancias y decidió conservar las otras 674; no hubo doble revisión humana independiente. Se registran aparte posibles incidencias de cajas y clases GT, sin modificar automáticamente la referencia.

Estas precisiones delimitan la evidencia disponible al interpretar los resultados. Las notas de reunión y de seguimiento son materiales de trabajo, separados del manuscrito entregable.

## Cómo aportar observaciones

Se puede comentar directamente el DOCX en Word o LibreOffice, indicando sección, tabla o figura. Para evitar versiones paralelas, conservar el nombre del manuscrito principal y registrar sus cambios en Git. Si se comparte una copia comentada, añadir un sufijo de revisión y mantener identificada la versión de origen. No ejecutar el constructor del informe sobre ediciones manuales sin incorporarlas antes: reconstruye el documento desde una base anterior.
