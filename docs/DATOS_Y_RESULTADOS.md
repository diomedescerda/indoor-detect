# Datos, métricas y alcance

[Inicio](../README.md) · [Reproducir](REPRODUCIR.md)

## Entradas del análisis

| Entrada | Identidad / función |
|---|---|
| `Build/Testing/data/` | 198 JPEG de iPhone 12 Pro Max, 1536 × 2048 píxeles |
| `Build/Testing/labels.json` | COCO GT revisada: 889 cajas, diez clases y 16 imágenes sin anotaciones |
| `Build/Testing/capture_groups.csv` | Orden, archivo, montaje, lente y hash de captura |
| `Build/Testing/benchmark/results/android.json` | 198 frames, predicciones de piso bajo y tiempos de referencia |
| `Build/Testing/benchmark/models/efficientdet-lite2-detection-metadata.tflite` | Binario exacto EfficientDet-Lite2, entrada 448 × 448 |
| `Build/Testing/provenance/android_run_metadata.json` | Commit, modelo, GT, fingerprint y hashes de cinco módulos Kotlin |
| `Build/Testing/occlusion/author_review.json` | Etiquetas de oclusión: 215/889 instancias marcadas como revisadas por el autor |

`annotation_history/roboflow_reviewed.coco.json` conserva la exportación corregida
antes de normalizar clases. Los archivos `preannotations.coco.json`, `chat_boxes.json`, `review/` y el checklist inicial están en `development/annotation_drafts/Testing/`: son borradores, no GT final. Las clases COCO
son persona 1, silla 62, sofá 63, cama 65, mesa 67, inodoro 70, TV 72,
portátil 73, lavamanos 81 y refrigerador 82.

## Notación

- Cajas COCO: píxeles `[x, y, ancho, alto]`, origen en la esquina superior izquierda.
- **GT**: instancia anotada dentro de la foto; **TP**: detección correctamente
  emparejada; **FP**: predicción sin pareja; **FN**: instancia GT sin detección.
- **IoU**: intersección de dos cajas dividida por su unión. Se requiere clase
  coincidente e IoU ≥ 0,50; el emparejamiento es uno a uno y por confianza.
- Precisión = TP/(TP+FP); recall = TP/(TP+FN); F1 = 2TP/(2TP+FP+FN).
  Un denominador nulo queda sin valor, no se convierte en éxito perfecto.
- `detector`: confianza ≥ 0,30, hasta 15 predicciones. `app_output`: lista
  de hasta dos objetos seleccionados por confianza para el anuncio.
- AP COCO usa predicciones de piso 0,001 y su propio barrido de umbrales;
  no equivale a F1 con confianza fija de 0,30.

## Configuraciones y alcance estadístico

Hay 33 grupos sucesivos de seis fotos: cabeza 1x, cabeza 0,5x, pecho 1x,
pecho 0,5x, palo de selfie 1x y palo de selfie 0,5x. Son grupos de adquisición,
no 33 habitaciones independientes. «1x» y «0,5x» son etiquetas nominales;
el análisis EXIF registra discrepancias y variantes de focal por separado.

Palo de selfie permitió apuntar hacia los objetos; no fue una posición fija con
idéntico campo visual. Las capturas sucesivas también permiten cambios en
personas y poses. Cada vista tiene sus instancias GT: sumar cajas entre vistas
no cuenta objetos únicos del mundo. Los objetos fuera del encuadre no son FN.

Palo de selfie 0,5x lidera el conteo TP y pecho 1x lidera F1. La ventaja media de
conteo del primero frente a pecho 1x es 0,515 objetos/grupo, intervalo bootstrap
exploratorio del 95 % [0,121; 0,939]. Frente a pecho 0,5x el intervalo incluye cero.
Se usan 10 000 remuestreos de grupos completos, semilla 20261013, sin corrección
por comparaciones múltiples. Compartir recintos puede hacer los intervalos
optimistas; las 438 sillas de 889 instancias influyen en las métricas agrupadas.

## Qué demuestra cada análisis

| Análisis | Lo que permite comprobar | Límite |
|---|---|---|
| Montaje/lente | Conteos y detección en fotos anotadas | No aísla una causa ni valida un montaje universal |
| Distancia | Bandas geométricas estimadas con EXIF y alturas de referencia | No son metros físicos medidos ni un alcance validado |
| Brillo | Asociación con brillo digital medio relativo | No son lux ni iluminación controlada |
| Oclusión | Recall por etiqueta cualitativa de objetos anotados | Asistencia de IA, revisión humana parcial, sin doble revisión independiente |
| Tiempo Android | Reproducción JPEG, preprocesamiento y detector | Excluye captura, UI, localización y audio |
| Pruebas de voz de la app | Activos presentes e inicialización/completitud de síntesis española | No comprueban claridad perceptual ni resultados con participantes |

El modelo se suministra para inferencia; estos repositorios no entrenan un
detector nuevo ni reconstruyen sus datos originales de entrenamiento. La app
y las fotos de evaluación son entregables distintos. La procedencia y términos
de los componentes están en
[THIRD_PARTY.md](https://github.com/diomedescerda/AssistiveVision/blob/main/docs/THIRD_PARTY.md).

La [correspondencia de nombres de montajes](NOMBRES_DE_MONTAJES.md) aclara las claves
históricas del archivo y su equivalencia con el palo de selfie con trípode.
