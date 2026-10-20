# Mapa del repositorio y continuidad del trabajo

[Inicio](../README.md) · [Guía de lectura](GUIA_DE_LECTURA.md) · [Edición del informe](README.md)

## Estructura

```text
indoor-detect/
├── README.md                         Entrada principal
├── Build/
│   ├── models_comparison/            Comparación histórica de modelos
│   └── Testing/                      Estudio de 198 fotografías
│       ├── data/                     Fotografías originales
│       ├── labels.json               Referencia COCO para evaluar
│       ├── capture_groups.csv        Orden, montaje, lente y hashes
│       ├── annotation_history/       Exportación corregida y antecedentes
│       ├── benchmark/
│       │   ├── android/              Prueba de instrumentación ejecutada
│       │   ├── models/               Modelo usado por la app en el estudio
│       │   ├── results/android.json  Predicciones principales archivadas
│       │   └── results/android/      Métricas y análisis derivados
│       ├── occlusion/                Etiquetas adicionales, visor y análisis
│       ├── provenance/               Metadatos y módulos Android archivados
│       └── scripts/                  Constructores de reportes
└── Documents/
    ├── Informe_Final_Trabajo_de_Grado_AssistiveVision.docx
    ├── Templates/                    Base conservada y guía institucional
    ├── Figures/                      Figuras preparadas para el manuscrito
    ├── Fragments/                    Capítulos independientes auxiliares
    ├── scripts/                      Construcción y análisis del informe
    ├── Review/                       Auditoría, hashes y evidencia derivada
    ├── Notes/                        Notas de reunión
    └── Obsidian/                     Apuntes de trabajo anteriores
```

El código completo Android está en [AssistiveVision](https://github.com/diomedescerda/AssistiveVision), fuera de este árbol. Los directorios se conservan para mantener funcionando rutas de scripts y registros de procedencia.

## Qué archivo tiene prioridad

| Necesidad | Archivo principal | Material auxiliar o histórico |
|---|---|---|
| Continuar el informe | [Informe final](Informe_Final_Trabajo_de_Grado_AssistiveVision.docx) | `Templates/` conserva la base; `Fragments/` no sustituye al manuscrito completo |
| Consultar el estudio de captura | [README del estudio](../Build/Testing/LEEME.md) | `AssistiveVision_Benchmark_Report.docx` es el reporte específico del benchmark, anterior al manuscrito integrado |
| Evaluar detecciones | [labels.json](../Build/Testing/labels.json) | `preannotations.coco.json`, `chat_boxes.json` y `review/` son borradores históricos |
| Consultar la ejecución principal | [android.json](../Build/Testing/benchmark/results/android.json) | `results/desktop/` corresponde a un proxy con otro entorno |
| Consultar oclusión actual | [results/labels.json](../Build/Testing/occlusion/results/labels.json) y [metrics.json](../Build/Testing/occlusion/results/metrics.json) | `author_review.json` preserva la descarga del autor; `labels_batch_*.json` son etiquetas iniciales |
| Consultar antecedentes y notas de trabajo | [Notes/](Notes/) y [Obsidian/](Obsidian/) | Material histórico auxiliar; no reemplaza la metodología ni los resultados del informe |

## Datos, resultados y código por análisis

Todas las rutas siguientes parten de `Build/Testing/`.

| Análisis | Código | Resultados archivados |
|---|---|---|
| Evaluación general COCO y P/R/F1 | `benchmark/evaluate.py` | `benchmark/results/android/{metrics.json,summary.csv,per_image.csv,per_class.csv}` |
| Comparaciones pareadas de configuración | `benchmark/analyze_effects.py` | `benchmark/results/android/{paired_comparisons.csv,paired_effects.csv,interpretation.txt}` |
| Conteos por grupo y comparación con Gorillapod 0,5x | `benchmark/analyze_scenes.py` | `benchmark/results/android/scenes/` |
| Montajes agrupando lentes y pruebas t | `benchmark/plot_scenario1.py` | `benchmark/results/android/scenario1/` |
| Distancia aproximada mediante EXIF | `benchmark/analyze_depth.py` | `benchmark/results/android/depth/`, incluidas discrepancias EXIF/lente |
| Oclusión, estratos y sensibilidad | `benchmark/analyze_occlusion.py` | `occlusion/results/` |
| Ejemplos visuales de detección | `benchmark/render_predictions.py` | `benchmark/results/android/overlays/` |
| Nueva ejecución Android | `benchmark/run_android.py` y `benchmark/android/DatasetBenchmarkTest.kt` | Sobrescribe `benchmark/results/android.json`; preservar antes el archivo archivado |

El análisis de brillo y tiempos del manuscrito se genera con [analyze_proposal_evidence.py](scripts/analyze_proposal_evidence.py) y se conserva en [Review/proposal_evidence/](Review/proposal_evidence/). La construcción del manuscrito se explica en [Documents/README.md](README.md).

## Revisar sin instalar herramientas

Descargar o clonar el repositorio y abrir los DOCX, PNG y CSV. GitHub permite leer los Markdown y explorar las carpetas. No se necesita repetir inferencia para comprobar tablas o revisar imágenes. Para clonar por HTTPS:

```sh
git clone https://github.com/diomedescerda/indoor-detect.git
cd indoor-detect
```

Si el repositorio requiere acceso, la cuenta utilizada para consultarlo debe tener permisos. El clon incluye aproximadamente 209 MB en `Build/Testing/`, principalmente fotografías y resultados; no depende de rutas del equipo del autor para consultar esos archivos.

## Recalcular o continuar desde otro equipo

1. Seguir el entorno y los comandos de [Build/Testing/LEEME.md](../Build/Testing/LEEME.md#reproducir-con-predicciones-guardadas).
2. Empezar por predicciones guardadas; Android Studio solo es necesario para una nueva ejecución de la aplicación.
3. Para oclusión, ejecutar desde la raíz `python Build/Testing/benchmark/analyze_occlusion.py` y luego `python Build/Testing/occlusion/build_review.py`. Se usa automáticamente la revisión del autor archivada. El visor requiere descargar el JSON para conservar nuevas correcciones.
4. Para reconstruir el informe, seguir [Documents/README.md](README.md), incluyendo la actualización de páginas y revisión visual. El constructor sobrescribe el DOCX; incorporar antes cualquier edición manual a los scripts.
5. Revisar `git diff` antes de confirmar y publicar cambios. No mezclar un nuevo experimento con los resultados archivados sin identificarlo.

## Integridad y procedencia

[Build/Testing/SHA256SUMS.json](../Build/Testing/SHA256SUMS.json) y [verify_package.py](../Build/Testing/verify_package.py) protegen el paquete base. [Review/revision_sha256.json](Review/revision_sha256.json) registra archivos de revisiones posteriores. Un hash distinto tras una edición intencional identifica una nueva versión; no significa que la ejecución histórica deba reescribirse. Los commits conservan ambas versiones.

[Review/occlusion_validation.json](Review/occlusion_validation.json) documenta la revisión parcial de oclusión; [Review/template_validation.json](Review/template_validation.json) y [Review/proposal_alignment_validation.json](Review/proposal_alignment_validation.json) registran las comprobaciones del informe. [Review/seguimiento_personal_propuesta.md](Review/seguimiento_personal_propuesta.md) es una nota administrativa personal y no forma parte del manuscrito.

Las copias locales no rastreadas por Git no se transfieren al clonar. En particular, la carpeta y el ZIP locales `Documents/Literatura` no forman parte de la entrega versionada; la bibliografía utilizada se consulta en el informe. Los entornos Python, APK y renders temporales tampoco son necesarios para leer los resultados.
