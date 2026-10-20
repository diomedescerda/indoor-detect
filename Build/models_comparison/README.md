# Comparación histórica de modelos

Esta carpeta conserva el código y los resultados de la selección inicial de DNN que se describe en el capítulo 2 del [informe final](../../Documents/Informe_Final_Trabajo_de_Grado_AssistiveVision.docx).

| Archivo | Contenido |
|---|---|
| [results/desktop.md](results/desktop.md) | Resultados de evaluación de los modelos en escritorio |
| [results/android.md](results/android.md) | Tiempos y memoria en Redmi Note 13, con las condiciones indicadas en el propio archivo |
| [benchmark_models.py](benchmark_models.py) | Evaluador histórico COCO para modelos TFLite |
| [benchmark_models_android.sh](benchmark_models_android.sh) | Script histórico de medición Android |

El manuscrito describe seis configuraciones de modelos y una evaluación inicial de 80 imágenes con 257 anotaciones. El conjunto posterior de **198 fotografías y 889 instancias**, empleado para comparar montajes y lentes, está en [Build/Testing](../Testing/LEEME.md).

Los archivos de esta carpeta son un registro histórico. Los modelos y el conjunto `test_images/` esperados por el evaluador histórico no están incluidos aquí, por lo que no es un paquete autónomo de reproducción. Para ejecutar el estudio archivado de la aplicación, seguir [las instrucciones actuales](../Testing/LEEME.md#reproducir-con-predicciones-guardadas), que incluyen el modelo exacto y las predicciones guardadas.

El benchmark de Redmi y la ejecución posterior con perfil Pixel 8 en emulador corresponden a entornos distintos; sus tiempos deben interpretarse por separado.

[Volver al inicio](../../README.md) · [Guía de lectura](../../Documents/GUIA_DE_LECTURA.md)
