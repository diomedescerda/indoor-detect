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
| Gráficos y ejemplos | Se generan 33 láminas de escenas y diez superposiciones de ejemplo, además de figuras de métricas; cantidad confirmada en la revisión del 9 de noviembre |
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

## Recorrido de los README del 5 de noviembre de 2026

Se revisaron **16 README/LEEME**: doce vigentes y cuatro archivos históricos o de
procedencia. Los 30 documentos de navegación actuales tienen 248 enlaces locales
y 28 URL externas comprobadas, sin archivos, anclas ni respuestas HTTP fallidas.
El README congelado del paquete base conserva sus bytes y sus rutas históricas;
una nueva guía de archivo conduce al procedimiento actual.

En copias independientes obtenidas desde `main`, con entornos Python nuevos, se
repitieron las 27 tablas/dos JSON, las doce evaluaciones históricas y la inferencia
opcional de escritorio. La repetición histórica conservó las siete/nueve diferencias
ya documentadas. Las 198 predicciones Android volvieron a coincidir exactamente.
Se verificaron la descarga pública completa del APK, su instalación y captura en
emulador, persistencia de ajustes, 34 pruebas JVM y cinco de voz/fotogramas en modo
avión. El visor de oclusión superó guardado, exportación, recarga y restauración
con un registro de prueba que no se incorporó a las anotaciones científicas.

La reconstrucción editorial en otro entorno conservó 22 tablas, once secciones y
49 referencias. Sus **73 páginas renderizadas coinciden píxel a píxel** con el Word
actual; se corrigió el constructor para conservar el subrayado de los enlaces de
descarga. El Word final no se sustituyó durante estas pruebas.

Se reprodujo una incidencia del APK `v1.0.0`: el primer permiso de cámara puede dejar
Capturar deshabilitado aunque exista vista previa. Forzar detención y abrir una vez resolvió
el caso sin borrar datos; las guías incluyen esa recuperación. Esta revisión mejora
las instrucciones y no modifica el código de producción de la app.

Las pruebas se hicieron en Linux x86_64 y un emulador x86_64/API 37.2 con páginas de
16 KB. Se reutilizaron objetos Git y descargas SDK/Gradle/Maven; los clones quedaron
independientes, sin `.venv`, builds ni `local.properties` heredados. Windows/macOS,
la instalación desde un navegador de teléfono, cámaras físicas, mandos Bluetooth
y claridad con oyentes requieren sus propias comprobaciones. No se creó otra
versión pública solo para probar el procedimiento de publicación.

El [registro completo](../development/validation/readme-e2e-20261105.json) separa
éxitos, recuperaciones, archivos históricos y límites de la comprobación.

## Verificación de recorridos del 9 de noviembre de 2026

Se inventariaron **17 README/LEEME** de ambos repositorios: trece vigentes y cuatro
archivos históricos o de procedencia. Pasaron **292 enlaces locales y 33 URL
externas**. Los recorridos ejecutados usaron copias independientes de `main`,
entornos Python 3.12 nuevos y salidas nuevas; se reutilizaron descargas de
dependencias, SDK y objetos Git para un clon disociado sin dependencias del
repositorio original.

| Recorrido | Resultado observado |
|---|---|
| Análisis principal con `--overlays` | 570 sumas conservadas antes y después, 22 pruebas numéricas y tres del ejecutor correctas; 27 CSV/dos JSON coincidentes |
| Imágenes de diagnóstico | Diez superposiciones de ejemplo y 33 láminas que reúnen las 198 fotos; se corrigió la cantidad de superposiciones anunciada en la guía |
| Comparación histórica | Seis modelos recuperados y doce evaluaciones completas; siete/nueve diferencias, como en la ejecución anterior; salida 1 esperada y explicada en HISTORICO.md |
| Inferencia opcional de escritorio | 198 fotos procesadas y métricas calculadas en una salida separada |
| APK desde `AssistiveVision/main` | Compilación limpia, 34 pruebas JVM, lint con cero errores y 30 advertencias, 362 activos y APK verificados |
| APK público `v1.0.0` | Descarga sin autenticación, SHA-256, instalación, permisos, capturas y voz local en español/inglés comprobados |
| Ajustes y controles | Persisten los cinco ajustes tras cierre completo; funcionan vista previa oculta, pantalla completa y tecla de cámara simulada |
| Instrumentación de voz/fotogramas | Cinco pruebas correctas en modo avión |
| Inferencia Android histórica | 198/198 arrays idénticos y resumen sin tiempos coincidente; fuentes y modelo iguales a la referencia |
| Paneles del informe | Regeneración desde sus fuentes verificadas; ambos PNG coinciden byte por byte |
| Visor opcional de oclusión | Generación correcta de la página con 889 registros; guardado/exportación/restauración conservan el código ya comprobado el 5 de noviembre |

La prueba positiva con la escena virtual del emulador usó confianza **0,10** y
velocidad de voz **2,0**. En esa escena la puntuación del televisor quedó por
debajo del valor inicial 0,30; el recorrido sin detecciones también se comprobó.
La tecla de cámara se inyectó con `adb`; no se emparejó un mando físico.

El [informe final](../Documents/Informe_Final_AssistiveVision.docx) conserva las
82 páginas revisadas visualmente, sus 91 campos de cita, 49 referencias Zotero y
las fotografías de colocación en la Figura 4.2. El README conduce a este Word como informe final.

El autor informa que la app funciona en su Redmi Note 13. Esta ronda no contó
con un teléfono conectado: ejecutó Linux x86_64 y emuladores API 37.2 x86_64 con
páginas de 16 KB. Windows/macOS, la instalación desde el navegador de un teléfono,
el complemento de Zotero en Word y la comprensión del audio con participantes
requieren sus propias comprobaciones; no se presentan como pruebas realizadas aquí.

El [registro completo](../development/validation/readme-e2e-20261109.json) y sus
[comprobantes](../development/validation/readme-e2e-20261109/) conservan comandos,
resultados, metadatos y límites. Las nuevas mediciones no sustituyen las del estudio.
