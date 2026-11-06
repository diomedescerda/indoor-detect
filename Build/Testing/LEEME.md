# Estudio de montaje y lente de AssistiveVision

**Código fuente de la aplicación Android:** [diomedescerda/AssistiveVision](https://github.com/diomedescerda/AssistiveVision). Este repositorio conserva la documentación, los datos y los análisis experimentales del proyecto.

**[Descargar APK](https://github.com/diomedescerda/AssistiveVision/releases/latest/download/AssistiveVision-1.0-debug.apk)** · [Inicio del repositorio](../../README.md) · [Guía de lectura del proyecto](../../Documents/GUIA_DE_LECTURA.md) · [Mapa de archivos](../../Documents/MAPA_DEL_REPOSITORIO.md)

Esta carpeta conserva las 198 fotografías, las anotaciones, la ejecución Android del 13 de octubre de 2026 y los análisis posteriores. El documento principal para continuar la escritura es el [informe revisado](../../Documents/Informe_Final_AssistiveVision.docx). El reporte previo del benchmark se conserva como material auxiliar en `development/annotation_drafts/Testing/`.

## Diseño del conjunto

Hay 33 grupos de captura sucesiva. Cada grupo contiene, en este orden:

1. Arnés de cabeza, lente nominal 1x.
2. Arnés de cabeza, lente nominal 0,5x.
3. Arnés de pecho, lente nominal 1x.
4. Arnés de pecho, lente nominal 0,5x.
5. Palo de selfie, lente nominal 1x.
6. Palo de selfie, lente nominal 0,5x.

[capture_groups.csv](capture_groups.csv) relaciona fotografías, orden, configuración y hashes. Los grupos siguen el orden ascendente de los números IMG originales. No equivalen necesariamente a habitaciones o entornos independientes. Las fotos se tomaron con un iPhone 12 Pro Max y se procesaron después en Android. El palo de selfie permite orientar libremente el celular; en estas capturas se apuntó hacia los objetos de interés. No se midieron altura ni inclinación. La comparación incluye esa estrategia de encuadre y no aísla el efecto del soporte.

## Datos y anotaciones

| Archivo o carpeta | Función |
|---|---|
| [data/](data) | 198 fotografías JPEG de 1536 × 2048, con extensión en minúsculas y bytes originales |
| [labels.json](labels.json) | Referencia COCO utilizada en la evaluación: 889 cajas en 198 imágenes; 16 imágenes sin anotaciones |
| [images.coco.json](../../development/annotation_drafts/Testing/images.coco.json) | Manifiesto de imágenes sin anotaciones de objetos |
| [annotation_history/roboflow_reviewed.coco.json](annotation_history/roboflow_reviewed.coco.json) | Exportación corregida por el autor en Roboflow |
| [annotation_history/](annotation_history) | Antecedentes del proceso de anotación |
| [occlusion/](occlusion/README.md) | Etiquetas suplementarias de oclusión, revisión parcial y resultados |

El borrador inicial de cajas se produjo en el chat y el autor lo corrigió en Roboflow. Se solicitó GPT-6.1 Sol para el borrador, pero los archivos guardados no prueban de forma independiente el modelo que lo sirvió. No se utilizó EfficientDet para producir las cajas iniciales. No hubo una segunda auditoría humana independiente.

Los nombres de categorías del exportado se mapearon a los identificadores COCO verdaderos. Trece cajas excedían los bordes por redondeo de exportación y se recortaron dentro de una tolerancia de 0,05 píxeles. Las cajas usan `[x, y, ancho, alto]` en píxeles.

| Clase COCO | ID |
|---|---:|
| person | 1 |
| chair | 62 |
| couch | 63 |
| bed | 65 |
| dining table | 67 |
| toilet | 70 |
| tv | 72 |
| laptop | 73 |
| sink | 81 |
| refrigerator | 82 |

Los borradores `preannotations.coco.json`, `chat_boxes.json`, `review/` y `review_checklist.csv` están agrupados en `development/annotation_drafts/Testing/`. No sustituyen a `labels.json`. Las observaciones posteriores sobre posibles problemas de cajas y clases se conservan en `development/annotation_drafts/occlusion/gt_review_issues_batch_*.json`, sin modificar automáticamente la referencia.

## Resultados principales

Con confianza 0,30 y coincidencia de clase e IoU ≥ 0,50:

| Configuración | Instancias visibles | Detecciones correctas | Detecciones falsas | F1 | Correctas tras el límite de dos |
|---|---:|---:|---:|---:|---:|
| Cabeza 1x | 129 | 56 | 20 | 54,6% | 31 |
| Cabeza 0,5x | 164 | 70 | 36 | 51,9% | 37 |
| Pecho 1x | 124 | 65 | 21 | 61,9% | 37 |
| Pecho 0,5x | 153 | 77 | 32 | 58,8% | 44 |
| Palo de selfie 1x | 145 | 75 | 29 | 60,2% | 40 |
| Palo de selfie 0,5x | 174 | 82 | 31 | 57,1% | 49 |

Palo de selfie 0,5x es la elección provisional cuando se prioriza recuperar más objetos correctos. Pecho 1x lidera F1. El énfasis en conteos se adoptó después del análisis inicial de F1 y es exploratorio.

Frente a pecho 1x, palo de selfie 0,5x suma 17 aciertos: gana en 16 grupos, empata en 10 y pierde en 7. La diferencia media es 0,515 objetos por grupo, con IC bootstrap exploratorio del 95% [0,121; 0,939]. Frente a pecho 0,5x, la diferencia es 0,152 [−0,182; 0,515]. No se establece un ganador universal.

## Dónde consultar tablas y figuras

| Contenido | Ubicación |
|---|---|
| Predicciones principales y procedencia | [benchmark/results/android.json](benchmark/results/android.json) |
| Métricas por configuración | [summary.csv](benchmark/results/android/summary.csv) |
| Métricas por foto y por clase | [per_image.csv](benchmark/results/android/per_image.csv), [per_class.csv](benchmark/results/android/per_class.csv) |
| Comparaciones de F1 | [paired_comparisons.csv](benchmark/results/android/paired_comparisons.csv) |
| Conteos pareados y ejemplos por grupo | [scenes/](benchmark/results/android/scenes) |
| Pruebas t por montaje y diagramas de distribución | [scenario1/](benchmark/results/android/scenario1) |
| Distancia aproximada, bandas y discrepancias EXIF | [depth/](benchmark/results/android/depth) |
| Predicciones superpuestas en fotografías | [overlays/](benchmark/results/android/overlays) |
| Oclusión y análisis de sensibilidad | [occlusion/results/](occlusion/results) |
| Resultados del proxy de escritorio | [benchmark/results/desktop/](benchmark/results/desktop) |

## Método y alcance

La prueba Android invoca los módulos de producción `PreprocessingModule`, `DetectionModule` y `LetterboxMapper`, con EfficientDet-Lite2 a 448 × 448. Se guardan detecciones desde confianza 0,001, con un máximo de 15. Las métricas operativas de precisión, recall, F1 y conteos aplican confianza 0,30 y emparejamiento uno a uno de clase y caja a IoU ≥ 0,50. COCO AP utiliza las predicciones guardadas de baja confianza.

El modo `app_output` conserva hasta dos detecciones ordenadas por puntuación. Aproxima la selección de objetos que llega al módulo de voz; no evalúa el habla ni su comprensión.

`Pixel_8` es un perfil de emulador Android 17, API 37, x86_64, con páginas de 16 KB. La mediana del método de detección fue 246,3 ms y P95 307,5 ms; la preparación tuvo mediana de 104,0 ms. Son mediciones en emulador con compilación de depuración, no de un Pixel 8 físico ni de latencia completa hasta el audio.

Los conteos corresponden a instancias por foto, no a objetos únicos entre vistas. Un objeto fuera del encuadre no es un falso negativo del detector. Hay 438 sillas de 889 instancias, por lo que los resultados agrupados tienen desequilibrio de clases. Los intervalos usan 10 000 remuestreos pareados de grupos, semilla 20261013, sin corrección por comparaciones múltiples. Compartir habitaciones puede reducir la independencia. La elección requiere validación en escenas nuevas y en el teléfono físico de destino.

La distancia usa un modelo geométrico aproximado con EXIF y alturas de referencia; no es una medición física. El brillo digital no equivale a lux. La oclusión tiene etiquetas visuales asistidas por IA, con 215 instancias revisadas por el autor y 674 conservadas de la clasificación inicial. El [protocolo específico](occlusion/README.md) explica incertidumbre, truncamiento y límites.

## Reproducir con predicciones guardadas

La [guía de reproducción actual](../../docs/REPRODUCIR.md) reúne todos los pasos.
Desde la **raíz del repositorio**, con Python 3.12. Si falta ese intérprete o se usa una terminal AppImage, seguir [la preparación del entorno](../../docs/REPRODUCIR.md#antes-de-empezar):

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-analysis.lock.txt
.venv/bin/python scripts/reproduce.py --overlays
```

Se verifican las 570 sumas, GT y 22 pruebas; se regeneran los análisis y se
comparan 27 CSV y dos JSON con la referencia. Los resultados nuevos van a
`development/runs/saved-results/` sin sobrescribir este directorio. En Windows usar
`.venv\Scripts\python.exe`. Para repetir, elegir otra carpeta con `--output`.
No se necesita LiteRT ni Android para este procedimiento.

## Ejecutar de nuevo la inferencia

Seguir [la ejecución Android documentada](../../docs/REPRODUCIR.md#3-repetir-la-inferencia-en-android):
compilar el clon de AssistiveVision de referencia, iniciar un emulador o
conectar un teléfono autorizado y ejecutar desde la raíz:

```sh
.venv/bin/python scripts/run_android_benchmark.py --app ../AssistiveVision-reference --sdk /ruta/Android/Sdk --serial emulator-5554
```

El nuevo ejecutor prepara la instrumentación, construye e instala los APKs,
valida las 198 imágenes y guarda predicciones/métricas en una carpeta nueva.
`benchmark/run_android.py` se conserva como fuente histórica con su hash original;
usa rutas y salidas antiguas y no es el comando recomendado.

La [inferencia de escritorio opcional](../../docs/REPRODUCIR.md#4-inferencia-de-escritorio-opcional)
usa otro runtime/decodificador y debe mantenerse separada de Android.

## Integridad y documentación histórica

[provenance/android_run_metadata.json](provenance/android_run_metadata.json) conserva el commit Android, entorno y hashes de modelo, GT y módulos. [provenance/app_source/](provenance/app_source) conserva esos módulos; [benchmark/models/](benchmark/models) contiene el modelo usado. La procedencia y las condiciones de los componentes se documentan en [la guía de terceros de la app](https://github.com/diomedescerda/AssistiveVision/blob/main/docs/THIRD_PARTY.md).

El [verificador activo](../../scripts/verify_archive.py) comprueba las 570 sumas originales mediante [el mapa de reubicación](../../development/relocations.json); 281 archivos están archivados en `development/`. Las comprobaciones nuevas escriben en `development/runs/`, sin reemplazar los originales.

El [README original en inglés](../../development/annotation_drafts/Testing/README.md) se mantiene como parte del paquete base verificable. Esta guía en español permite consultarlo sin alterar ese registro histórico.

La [correspondencia de nombres de montajes](../../docs/NOMBRES_DE_MONTAJES.md) aclara las claves
históricas del archivo y su equivalencia con el palo de selfie con trípode.
