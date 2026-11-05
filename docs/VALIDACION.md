# Registro de reproducción y comprobaciones

[Inicio](../README.md) · [Repetir los pasos](REPRODUCIR.md) · [Datos](DATOS_Y_RESULTADOS.md)

Fecha: **5 de noviembre de 2026**. Equipo anfitrión: Linux x86_64. Se comprobaron
copias independientes de los fuentes, sin las carpetas de build de la app ni
`local.properties`, y un entorno Python 3.12 nuevo con solo las dependencias
de `requirements-analysis.lock.txt`. Se reutilizaron descargas de SDK y cachés
de dependencias del equipo; no se reutilizaron APKs ni salidas de análisis como
sustituto del trabajo de compilación/cálculo.

| Comprobación | Resultado |
|---|---|
| Paquete base antes y después | **570 archivos** coinciden con sus sumas archivadas |
| GT | 198 imágenes, 889 instancias, diez clases, 16 imágenes sin anotaciones |
| Pruebas numéricas archivadas | **22 correctas** |
| Pruebas del nuevo verificador | **3 correctas**: cambios de conteo, filas/texto, tolerancia y protección de salidas |
| Regeneración completa | **27 tablas CSV** coinciden, incluyendo estructura, textos y valores |
| Evidencia de brillo | **Dos JSON** coinciden con la referencia |
| Gráficos y ejemplos | Se generaron 33 láminas de escenas y 198 superposiciones, además de figuras de métricas |
| Inferencia Android nueva | Instrumentación correcta; **198 arrays de predicciones idénticos** al archivo original |
| Resumen Android nuevo | Mismos valores excluyendo las columnas de tiempo |
| Modelos históricos | Seis binarios exactos recuperados de Git; doce evaluaciones terminadas, con 16 discrepancias de 60 valores publicados |
| App desde fuentes limpios | APK construido; 34 tests JVM correctos, lint con 0 errores y 28 advertencias |
| Voz/frame store | Cinco pruebas de instrumentación correctas en emulador con modo avión |

## Comprobantes conservados

- [saved-results.json](../development/validation/saved-results.json): dependencias, hashes de
  entrada y comparación de cada tabla/JSON. Las tolerancias CSV son relativas
  `1e-10` y absolutas `1e-12`; los JSON de brillo se compararon como datos completos.
- [android-comparison.json](../development/validation/android-comparison.json): comparación de
  arrays y resumen frente a la referencia.
- [android-instrumentation.log](../development/validation/android-instrumentation.log): salida de la instrumentación de 198 fotos.
- [android-replay-20261105.json](../development/validation/android-replay-20261105.json): predicciones,
  tiempos y metadatos de la nueva ejecución, separados de `Build/Testing`.
- [historical-replay.json](../development/validation/historical-replay.json): modelos recuperados, versiones, hashes, métricas y las 16 diferencias históricas.
- [Validación de la app](https://github.com/diomedescerda/AssistiveVision/blob/main/docs/VALIDATION.md):
  compilación, checksum de activos, firma y pruebas del APK.

La copia temporal de los fuentes tuvo un commit local de verificación; ese hash
en los nuevos metadatos no identifica una revisión publicada en GitHub. La base
real de la app es `85c852ddcb543bce1bd69ad0db307f895d597881` y los cinco hashes
de módulos/modelo coinciden con la ejecución archivada. Los cambios de esta
revisión son documentación y herramientas de reproducción/paquetización.

## Reorganización del material intermedio

La comprobación posterior al traslado está en [reorganization.json](../development/validation/reorganization.json) y [sus comparaciones completas](../development/validation/reorganization-results.json). Se repitió el análisis con salida nueva: coinciden las 27 tablas y los dos JSON, pasan las 22 pruebas numéricas y las tres del ejecutor, y se mantienen las 570 sumas. También se verificaron los enlaces locales y las rutas de reubicación. En la app pasan los 362 activos y los comandos Gradle de pruebas unitarias y compilación; sus tareas quedaron actualizadas. No se repitió la instrumentación en este traslado de documentos.

## Límites de esta comprobación

Las salidas temporales fueron nuevas. Tras la reorganización, las 570 sumas originales siguen verificándose mediante `scripts/verify_archive.py`; 281 archivos conservan sus bytes en la nueva ubicación documentada en `development/relocations.json`. El README y los verificadores históricos están separados de los actuales.
Las figuras se regeneraron, pero no se exige igualdad binaria de PNG/PDF entre
plataformas. En los JSON de oclusión pueden variar rutas temporales de procedencia;
se comparan todas sus tablas CSV numéricas.

Los tiempos del nuevo emulador cambiaron y no se sustituyeron por los originales.
La prueba Android excluye captura, interfaz y audio; las cinco pruebas de voz/frame
store son comprobaciones funcionales aparte, sin participantes ni puntuaciones
de claridad. Windows/macOS, otros teléfonos y otras versiones Android no fueron
ejecutados en esta validación local.

La comprobación inicial de los workflows fue local. El build Android remoto
[del commit d78ffa7](https://github.com/diomedescerda/AssistiveVision/actions/runs/42096695975) terminó correctamente; su APK se distribuye en
[Releases](https://github.com/diomedescerda/AssistiveVision/releases/latest). Los artefactos temporales de CI se conservan como evidencia técnica. Los seis modelos históricos se recuperaron de Git con sus hashes exactos; su
repetición de escritorio y comparación se describen en [HISTORICO.md](HISTORICO.md).
No se reproducen las latencias originales de Redmi ni se atribuyen al nuevo equipo.
