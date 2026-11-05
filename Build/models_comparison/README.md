# Comparación histórica de modelos

**Código fuente de la aplicación Android:** [diomedescerda/AssistiveVision](https://github.com/diomedescerda/AssistiveVision). Este repositorio conserva la documentación, los datos y los análisis experimentales del proyecto.

Esta carpeta conserva el código y los resultados de la selección inicial de DNN que se describe en el capítulo 2 del [informe final](../../Documents/Informe_Final_AssistiveVision.docx).

| Archivo | Contenido |
|---|---|
| [results/desktop.md](results/desktop.md) | Resultados de evaluación de los modelos en escritorio |
| [results/android.md](results/android.md) | Tiempos y memoria en Redmi Note 13, con las condiciones indicadas en el propio archivo |
| [benchmark_models.py](benchmark_models.py) | Evaluador histórico COCO para modelos TFLite |
| [benchmark_models_android.sh](benchmark_models_android.sh) | Script histórico de medición Android |

El manuscrito describe seis configuraciones de modelos y una evaluación inicial de 80 imágenes con 257 anotaciones. El conjunto posterior de **198 fotografías y 889 instancias**, empleado para comparar montajes y lentes, está en [Build/Testing](../Testing/LEEME.md).

Los seis binarios ya no están en el árbol actual, pero se recuperaron exactamente
del commit `30b777f7d368f5a3b2b89676965961f626bfd6ba` conservado en Git. La
[guía de recuperación y reproducción](../../docs/HISTORICO.md) utiliza hashes
SHA-256, versiones fijadas y carpetas nuevas, sin descargar modelos distintos.
`test_images/` sí contiene las 80 imágenes y 257 anotaciones; también se conserva
el conjunto panorámico. El runtime original no se congeló: la repetición utiliza
LiteRT 2.3.0 explícitamente y compara los valores publicados antes de afirmar equivalencia.

El benchmark de Redmi y la ejecución posterior con perfil Pixel 8 en emulador corresponden a entornos distintos; sus tiempos deben interpretarse por separado.

[Volver al inicio](../../README.md) · [Guía de lectura](../../Documents/GUIA_DE_LECTURA.md)

Para ejecución directa, el evaluador histórico tiene `benchmark_config.json` en modo `panoramic`, escribe resultados en rutas fijas y requiere sus seis modelos. El script Android requiere un binario `android_benchmark` y modelos ya preparados en el dispositivo. No ejecutarlos suponiendo que descargan o preparan esas entradas automáticamente. El nuevo ejecutor recupera esos modelos y prepara las entradas; el binario de medición Android/Redmi no se conserva y sus latencias no se presentan como reproducidas.
