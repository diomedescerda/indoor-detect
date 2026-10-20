# AssistiveVision — documentación y evaluación experimental

Repositorio de la pasantía de investigación sobre un prototipo Android que detecta objetos en interiores y produce descripciones de voz para personas con discapacidad visual.

**Para comenzar:** [guía de lectura del proyecto](Documents/GUIA_DE_LECTURA.md). El documento principal es el [informe final de trabajo de grado](Documents/Informe_Final_Trabajo_de_Grado_AssistiveVision.docx).

## Dónde está cada parte

| Contenido | Ubicación | Uso |
|---|---|---|
| Informe final actualizado | [Documents/Informe_Final_Trabajo_de_Grado_AssistiveVision.docx](Documents/Informe_Final_Trabajo_de_Grado_AssistiveVision.docx) | Manuscrito principal para lectura y correcciones |
| Guía de lectura y resultados | [Documents/GUIA_DE_LECTURA.md](Documents/GUIA_DE_LECTURA.md) | Recorrido recomendado por las evidencias |
| Mapa de archivos y reproducción | [Documents/MAPA_DEL_REPOSITORIO.md](Documents/MAPA_DEL_REPOSITORIO.md) | Localizar datos, gráficos, código y antecedentes |
| Propuesta de pasantía | [Propuesta original](Documents/Propuesta%20Pasantia%20de%20Investigación%20-%20Diomedes%20Cerda.pdf) | Objetivos y tres fases previstas |
| Guía institucional y original del informe | [Documents/Templates/](Documents/Templates/) | Reglas de presentación y base conservada |
| Estudio de posición y lente | [Build/Testing/LEEME.md](Build/Testing/LEEME.md) | 198 fotografías, anotaciones y ejecución Android archivada |
| Oclusión | [Build/Testing/occlusion/README.md](Build/Testing/occlusion/README.md) | Protocolo, revisión parcial del autor y resultados |
| Selección inicial de modelos | [Build/models_comparison/README.md](Build/models_comparison/README.md) | Comparación histórica; distinta del estudio de posición/lente |
| Documentación del manuscrito | [Documents/README.md](Documents/README.md) | Edición, regeneración y verificaciones |

## Aplicación Android

El código completo de la app se mantiene en un repositorio separado: [diomedescerda/AssistiveVision](https://github.com/diomedescerda/AssistiveVision). Este repositorio conserva el modelo, la prueba Android y copias de los módulos utilizados en el experimento en [Build/Testing/provenance/](Build/Testing/provenance/). La ejecución archivada corresponde al commit de la app `85c852ddcb543bce1bd69ad0db307f895d597881`.

## Lectura rápida de los resultados

La evaluación principal contiene 198 fotografías de iPhone 12 Pro Max, distribuidas en 33 grupos de seis configuraciones: cabeza, pecho y Gorillapod, cada uno con lente nominal 1x y 0,5x. La referencia COCO contiene 889 instancias de diez clases. Las imágenes se procesaron con los módulos de producción de la app en un **emulador con perfil Pixel 8**.

Gorillapod 0,5x recuperó más objetos correctos (82); pecho 1x obtuvo el mayor F1 (61,9%). Son criterios distintos y la elección de Gorillapod 0,5x es provisional. Las diferencias, intervalos y límites se desarrollan en el informe y en la guía de lectura. Los tiempos del emulador no representan mediciones de un Pixel 8 físico ni el tiempo hasta terminar el anuncio de voz.

## Obtener y revisar el material

```sh
git clone git@github.com:diomedescerda/indoor-detect.git
cd indoor-detect
```

Para una copia existente, ejecutar `git pull` después de guardar los cambios propios. No se necesita Android Studio ni Python para leer el informe, los CSV y los gráficos ya generados. El DOCX puede abrirse directamente en Word o LibreOffice Writer.

Para reproducir los análisis, seguir [las instrucciones del estudio](Build/Testing/LEEME.md#reproducir-con-predicciones-guardadas). Antes de ejecutar constructores o inferencia, leer sus advertencias sobre archivos de salida: algunos comandos sobrescriben resultados o el manuscrito. La versión de referencia se conserva en Git.

Los borradores de anotación, notas personales y fragmentos se conservan por trazabilidad; la guía identifica cuáles son los archivos principales. No deben sustituir al informe ni a `Build/Testing/labels.json`.
