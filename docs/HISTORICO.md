# Recuperar y repetir la comparación histórica de modelos

[Inicio](../README.md) · [Estudio de 198 fotos](REPRODUCIR.md)

Los modelos no estaban en el árbol actual, pero sus seis binarios originales
siguen en el commit `30b777f7d368f5a3b2b89676965961f626bfd6ba` del historial Git.
La recuperación no descarga versiones nuevas ni vuelve a exportar redes.
[historical-models.json](historical-models.json) registra ruta histórica, blob,
tamaño y SHA-256 de cada archivo. El EfficientDet recuperado coincide también
con el modelo de la aplicación y del estudio posterior.

## Recuperar solo los modelos

Desde la raíz, con Git y Python:

```sh
python3 scripts/recover_historical_models.py
```

Los seis modelos se escriben en `development/runs/historical-models/`, suman unos
95 MB y se verifican antes de aceptar los archivos. Si existe uno distinto,
el comando se detiene sin reemplazarlo. No requiere TensorFlow ni GPU.

Un clon normal conserva el historial. Si se hizo un clon superficial y falta
el commit, ejecutar `git fetch --unshallow` y repetir. El workflow manual
histórico usa `fetch-depth: 0` para obtenerlo.

## Repetir la inferencia de escritorio

Preparar el entorno Python 3.12 de la [guía principal](REPRODUCIR.md), luego:

```sh
.venv/bin/python -m pip install -r requirements-historical.lock.txt
.venv/bin/python scripts/reproduce_historical.py
```

Se ejecutan las seis redes en los conjuntos normal (80 imágenes/257 anotaciones)
y panorámico. Para uno solo, usar `--mode normal` o `--mode panoramic`.
La salida `development/runs/historical/` debe ser nueva; elegir otra con `--output`
para repetir. Incluye modelos recuperados, datos de trabajo, logs, predicciones,
visualizaciones, tablas Markdown y `historical_report.json`.

Se utiliza el código actual del evaluador histórico sin cambiar sus métricas,
preprocesamiento o pesos. Un import de compatibilidad permite ejecutarlo con
**LiteRT 2.3.0** en lugar del TensorFlow/tflite_runtime original no congelado.
Se registran todas las versiones, plataforma y hashes de entradas; los encabezados
de las tablas nuevas identifican la repetición y no atribuyen su ejecución al
equipo antiguo. Los resultados originales permanecen intactos.

## Resultado comprobado y diferencias

La repetición local del **5 de noviembre de 2026** terminó las doce evaluaciones
(seis por conjunto). Coincidieron 44 de los 60 valores publicados a tres decimales.
Se observaron **siete diferencias** en la tabla normal y **nueve** en la panorámica,
conservadas individualmente en [el comprobante](../development/validation/historical-replay.json).
No se atribuye una causa definitiva: el entorno original no estaba congelado.

Por diseño, el comando termina con código distinto de cero si hay diferencias
con la tabla histórica, después de guardar el informe y las predicciones.
Ese resultado es esperable con el entorno comprobado y hace visible la discrepancia;
no indica que el ejecutor haya detenido la inferencia a mitad de camino. Revisar
los campos `archived_metrics_match`, `differences` y `metrics` de cada conjunto.
El workflow histórico manual conserva esos comprobantes incluso si falla la comparación.

La reproducción exacta de **27 CSV/dos JSON y las 198 predicciones Android** del
estudio principal es independiente de estas diferencias. No se sustituyen valores
del informe histórico por los nuevos ni se presenta esta repetición como igualdad
de todos sus números. Para una nueva selección se pueden citar las predicciones
y runtime de esta repetición, identificándola como otra ejecución.

## Qué no está incluido en esta repetición

El script histórico Android esperaba un ejecutable `android_benchmark` y los
modelos preparados en `/data/local/tmp` del Redmi Note 13. Ese binario/configuración
completa de compilación no se conserva. Sus tiempos y memoria son evidencia histórica,
no una medición que este ejecutor reproduzca en otro equipo. Los scripts auxiliares
de transformaciones panorámicas se conservan, pero no forman parte de la comprobación
de doce evaluaciones descrita aquí.
