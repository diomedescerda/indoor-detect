---
title: AssistiveVision — notas para reunión con la profesora
date: 2026-10-14
tags:
  - assistivevision
  - trabajo-de-grado
  - reunion
  - benchmarking
estado: preparacion
---

# AssistiveVision — qué hice y cómo explicarlo

> [!summary] Mi explicación en un minuto
> Preparé y corregí un conjunto de 198 fotografías para comparar tres montajes y dos lentes. Evalué las imágenes con los módulos reales de detección de la aplicación Android, ejecutados en un emulador Pixel 8. Además de precisión y F1, comparé cuántos objetos correctos recupera cada configuración dentro de la misma escena. Gorillapod 0,5x obtuvo más detecciones correctas y pecho 1x obtuvo la mayor F1. Revisé la estadística, corregí un error en los p-valores e incorporé los resultados al informe completo, respetando la plantilla de la universidad. Conservé datos, scripts y documentos en Git para poder reproducir y continuar el trabajo.

## 1. Qué quería resolver

**Pregunta:** ¿qué combinación de montaje y lente permite que la aplicación comunique más objetos correctos?

Mi observación inicial era que algunas tomas con arnés de pecho dejaban fuera muchos objetos. Por eso no bastaba con mirar una puntuación de exactitud: también había que medir **cobertura del encuadre y cantidad de objetos recuperados**.

Mi preferencia por Gorillapod 0,5x motivó la comparación, pero la conclusión se apoya en las métricas y se presenta como provisional.

## 2. Cómo organicé las fotografías

- **198 fotos**, organizadas en **33 grupos de seis capturas sucesivas**.
- Cada grupo sigue este orden: cabeza 1x → cabeza 0,5x → pecho 1x → pecho 0,5x → Gorillapod 1x → Gorillapod 0,5x.
- Hay **33 fotos por configuración** y 66 por montaje al agrupar los lentes.
- Las fotos se tomaron con un iPhone; el emulador se utilizó para ejecutar Android.

> [!info] Por qué comparé por escena
> Dentro de cada grupo comparé las seis configuraciones sobre un contexto parecido. Así puedo preguntar: «En este grupo, ¿cuál recuperó más objetos?». Las capturas fueron sucesivas: no son simultáneas ni garantizan idéntica posición, iluminación u oclusión.

## 3. Qué hice con las anotaciones

Partí de un borrador asistido por modelo y corregí las cajas en Roboflow. El resultado final contiene **889 instancias anotadas**, en diez clases: persona, silla, sofá, cama, mesa de comedor, inodoro, televisor, portátil, lavamanos y nevera.

Exporté las anotaciones a **COCO JSON** y normalicé las categorías por nombre a sus identificadores COCO. Se conservaron **16 fotos sin objetos objetivo anotados** para evaluar también las predicciones falsas en esas imágenes. Se ajustaron trece cajas que sobrepasaban ligeramente el borde por redondeo.

**GT o verdad de campo** significa las anotaciones de referencia contra las que se comparan las predicciones. No es una garantía de anotación perfecta: hubo una revisión humana, sin auditoría de un segundo revisor independiente.

## 4. Cómo evalué la aplicación

Reproduje las 198 imágenes mediante una prueba de instrumentación que invoca el **preprocesamiento, detector y transformación de coordenadas de producción**.

- Modelo: **EfficientDet-Lite2**, entrada de 448 × 448 píxeles.
- Entorno: **emulador Pixel 8**, Android 17 / API 37, x86_64.
- Para conteos, precisión, recall y F1: confianza **0,30** y coincidencia de clase con **IoU ≥ 0,50**.
- Para AP: predicciones retenidas desde 0,001, con un máximo de 15 por imagen.
- También evalué la selección de **hasta dos objetos**, que aproxima la lista que la app entrega al módulo de voz.

> [!important] Dos resultados diferentes
> **Detector:** cuenta todas las detecciones que pasan el umbral, hasta el límite de 15. **Lista de salida:** conserva como máximo dos objetos por imagen. No debo decir que la app anunció los 82 objetos: 82 es el conteo correcto del detector en Gorillapod 0,5x; la lista de hasta dos conserva 49 selecciones correctas. Este experimento no evaluó la comprensión del audio.

## 5. Resultados que debo recordar

Cada fila reúne 33 fotografías. «Visibles» es el número de instancias anotadas dentro del encuadre; «correctos» son los objetos emparejados con la referencia.

| Configuración | Visibles | Correctos | Falsas predicciones | F1 | Correctos en lista de hasta dos |
|---|---:|---:|---:|---:|---:|
| Cabeza 1x | 129 | 56 | 20 | 54,6 % | 31 |
| Cabeza 0,5x | 164 | 70 | 36 | 51,9 % | 37 |
| Pecho 1x | 124 | 65 | 21 | **61,9 %** | 37 |
| Pecho 0,5x | 153 | 77 | 32 | 58,8 % | 44 |
| Gorillapod 1x | 145 | 75 | 29 | 60,2 % | 40 |
| Gorillapod 0,5x | **174** | **82** | 31 | 57,1 % | **49** |

### Cómo interpreto esto

- **Gorillapod 0,5x:** más cobertura y más objetos correctos; recupera al menos uno en **29 de 33 escenas**.
- **Pecho 1x:** mejor equilibrio entre precisión y recall según F1.
- Ver más objetos también aumenta la cantidad de objetos que pueden quedar sin detectar. Un recall menor puede convivir con un conteo correcto mayor.
- Los conteos son **instancias por fotografía**, no objetos físicos únicos: una silla fotografiada seis veces puede generar seis anotaciones.

### Comparación directa por escena

Gorillapod 0,5x frente a pecho 1x:

- Detectó más objetos correctos en **16 grupos**, empató en 10 y detectó menos en 7.
- Acumuló **17 detecciones correctas adicionales**.
- Diferencia media: **+0,515 por escena**; intervalo bootstrap del 95 % **[0,121; 0,939]**.

Frente a pecho 0,5x, la diferencia fue de cinco detecciones en total y el intervalo del detector incluyó cero: **no quedó establecida una ventaja con ese análisis**.

> [!quote] Conclusión que puedo defender
> «Gorillapod 0,5x es mi candidato provisional si priorizo cantidad de objetos correctos y cobertura. Pecho 1x es la alternativa con mayor F1. Todavía no puedo afirmar que una configuración sea la mejor en todos los escenarios».

## 6. Qué corregí en la estadística

Durante la revisión se encontró un error en la función que calculaba los p-valores de la prueba t. Se corrigió, se regeneraron **once contrastes** y se verificaron con pruebas e integración numérica independiente.

El cambio importante fue la comparación **pecho frente a Gorillapod al agrupar los dos lentes**: el p-valor pasó de aproximadamente 0,0365 a **0,1130**. Por tanto, esa comparación agrupada **no alcanza el umbral de 0,05**. Los conteos de objetos, anotaciones y predicciones permanecieron iguales.

No confundir esa comparación agrupada con **Gorillapod 0,5x frente a pecho 1x**, cuyo p-valor es aproximadamente **0,0194**. Son contrastes distintos.

**La estadística es exploratoria:** se hicieron varias comparaciones sin ajuste y se eligió la configuración sobre estas mismas escenas. Hace falta confirmación en un conjunto nuevo.

## 7. Qué hice con la profundidad

Exploré la relación entre recall y distancia **estimada** usando tamaño de las cajas, focal EXIF y una altura de referencia por clase. Se observó menor recall en las bandas lejanas, pero las distancias no se midieron físicamente.

La auditoría encontró **seis discrepancias entre el lente nominal y el grupo focal EXIF**, más una variación menor de 25 a 26 mm. Las etiquetas de configuración se conservaron para mantener la trazabilidad. Debo revisar esas capturas antes de cerrar la conclusión sobre lentes.

> [!warning] Lo que no debo afirmar
> No se demostró que la aplicación funcione de forma fiable hasta 4 m. La app no estima profundidad y este análisis no justifica filtrar objetos por distancia. Tampoco se midieron navegación, reducción de colisiones o beneficio con usuarios finales.

## 8. Qué actualicé en el informe

Actualicé resumen y abstract, metodología, descripción de implementación, resultados experimentales, conclusiones y anexos. Incorporé tablas, tres diagramas de implementación y tres figuras de resultados. Reparé portada, encabezados, índices y tablas conservando la estructura y geometría de la plantilla universitaria. Guardé una copia exacta del documento anterior.

También cotejé la descripción con el código actual: captura manual, localización en seis zonas y síntesis de voz local con sherpa-onnx. La actualización documental no debe presentarse como si todas esas funciones se hubieran implementado durante esta revisión.

**Comprobaciones:** 34 pruebas JVM de la app y ocho pruebas Python aprobadas; 570 archivos del paquete original verificados por SHA-256; revisión visual del informe renderizado.

Conservé separado el estudio inicial de selección de modelos (**80 imágenes y 257 anotaciones**) del estudio de montajes y lentes (**198 imágenes y 889 anotaciones**).

## 9. Preguntas para la profesora

- [ ] ¿Priorizamos cobertura y objetos correctos, F1, o una combinación de ambos para elegir la configuración?
- [ ] ¿Mantenemos los 33 grupos completos? Una nota previa mencionaba 30; el conjunto disponible tiene 33.
- [ ] ¿Aceptamos la profundidad estimada como análisis exploratorio o necesitamos un protocolo con distancias medidas?
- [ ] ¿Qué validación mínima falta: escenas nuevas, teléfono físico, segundo revisor o pruebas de audio con usuarios?
- [ ] ¿Conviene ajustar las comparaciones múltiples o definir un único contraste principal para la siguiente evaluación?
- [ ] Confirmar director, codirector si aplica, línea y grupo de investigación.

## 10. Dónde está todo

- [Informe completo](../Informe_Final_Trabajo_de_Grado_AssistiveVision.docx)
- [Registro de revisión y correcciones](../Review/2026-10-14_revision.md)
- [Guía para continuar el informe](../README.md)
- [Paquete de datos y benchmark](../../Build/Testing/README.md)
- [Resultados por escena](../../Build/Testing/benchmark/results/android/scenes/count_summary.csv)
- [Contrastes corregidos](../../Build/Testing/benchmark/results/android/scenario1/paired_t_tests.csv)
- Repositorio: [indoor-detect](https://github.com/diomedescerda/indoor-detect). Revisión del informe: `2bcac6e`.

Los enlaces relativos funcionan si la nota se abre dentro de la estructura del repositorio. Si la copio sola a otro vault, debo volver a enlazar los archivos de apoyo.

## Mini glosario para responder preguntas

| Término | Cómo explicarlo |
|---|---|
| TP | Una predicción de la clase correcta que coincide suficientemente con la caja anotada. |
| FP | Una predicción que no logra un emparejamiento válido. |
| FN | Una instancia anotada visible que no fue recuperada. |
| Precisión | De lo que predije, qué proporción fue correcta. |
| Recall | De lo que estaba anotado y visible, qué proporción recuperé. |
| F1 | Media armónica de precisión y recall; no mide cuántos objetos entraron al encuadre. |
| IoU | Área de intersección de dos cajas dividida entre su área de unión. |
| AP | Resumen de la curva precisión–recall al variar el umbral de puntuación. |
| Comparación pareada | Comparar configuraciones dentro del mismo grupo de captura. |
| Bootstrap por grupos | Remuestrear grupos completos para estimar variabilidad conservando el emparejamiento. |
| p = 0,113 | El contraste no alcanza 0,05; no demuestra que los montajes sean equivalentes. |

> [!tip] Frase para cerrar la reunión
> «Ya tengo una evaluación reproducible y una selección provisional por objetivo. Quiero acordar qué validación falta y qué criterio vamos a utilizar para cerrar la elección de montaje y lente».
