# Informe final de AssistiveVision

[Inicio del repositorio](../README.md) · [Guía de lectura del proyecto](GUIA_DE_LECTURA.md) · [Mapa de archivos y reproducción](MAPA_DEL_REPOSITORIO.md)

El manuscrito de trabajo es **Informe_Final_Trabajo_de_Grado_AssistiveVision.docx**. Integra la comparación histórica de modelos, la implementación actual y la evaluación de 198 fotografías (889 anotaciones, 33 grupos y seis configuraciones). Se actualizó el 16 de octubre de 2026 para vincular las tres fases de la propuesta con sus evidencias y límites.

`Templates/Informe_Final_Base_2026-09-25.docx` conserva el original sin modificaciones. El manuscrito mantiene su geometría de página, doce secciones, escudo, estilos y estructura institucional. Se repararon portada, encabezados, índices y tablas. `Fragments/` contiene el capítulo experimental independiente; el manuscrito completo es la versión final para presentación.

## Continuar desde otro equipo

Hacer `git pull` y abrir el manuscrito en Word o LibreOffice. Guardar y confirmar los cambios en ese archivo. Los datos, anotaciones, predicciones y análisis están en `Build/Testing/`; `Review/2026-10-14_revision.md` documenta las correcciones y comprobaciones de esta revisión.

Se completaron autor, supervisores, grupo TecnOS, línea temática de investigación y agradecimientos. La versión para presentación no incluye una hoja de aceptación sin diligenciar ni afirma aprobación institucional. Los supervisores se identifican por sus nombres y cargos documentados, sin añadir grados académicos no acreditados. Las discrepancias EXIF y el alcance exploratorio de la profundidad se describen como limitaciones del estudio; las latencias del emulador no representan un Pixel 8 físico.

## Regeneración técnica

La regeneración sobrescribe el manuscrito a partir del original conservado; **no incorpora ediciones manuales posteriores**. Confirmar primero esas ediciones en Git y actualizar el constructor si se desea mantenerlas en futuras regeneraciones.

Desde la raíz del repositorio, con Python, python-docx, Pillow y lxml:

```sh
python Build/Testing/scripts/build_chapter4.py
python Documents/scripts/analyze_proposal_evidence.py
python Documents/scripts/update_informe.py
```

El gráfico en español de precisión, recall y F1 está en `Figures/seleccion_metricas.png` y se desarrolla en la sección 4.5. El mapa de conteos `Figures/seleccion_escenas.png` se conserva como material de análisis, pero se retiró del informe para evitar redundancia con la Tabla 4.5. Para regenerarlas desde los CSV archivados, instalar NumPy y Matplotlib y ejecutar `python Documents/scripts/build_selection_figures.py` antes del constructor del informe. Los gráficos originales del benchmark se conservan en `Build/Testing/benchmark/results/android/`.

El segundo comando usa las tablas archivadas y el capítulo generado. Requiere Liberation Sans en `/usr/share/fonts/liberation/LiberationSans-Regular.ttf` para los diagramas. Renderizar después el DOCX a PDF con un motor de documentos y verificar todas sus páginas. Con pypdfium2 instalado:

```sh
python Documents/scripts/refresh_informe_pages.py /ruta/al/informe_renderizado.pdf
```

Esto completa los números de página de contenido, figuras y tablas sin volver a guardar el DOCX a través del renderizador. Renderizar una vez más y comprobar índices y paginación. Los campos PAGEREF del cuerpo pueden actualizarse en Word; las seis entradas preliminares usan números romanos estáticos por compatibilidad con LibreOffice y requieren revisión si cambia la extensión de los preliminares. `scripts/informe_page_map.json` registra la correspondencia verificada.

Los scripts de análisis, sus resultados y la corrección estadística se versionan junto con el informe. El manifiesto original de `Build/Testing/` sigue protegiendo 570 archivos del paquete base. `Review/revision_sha256.json` registra por separado los archivos de esta revisión.

## Correspondencia con la propuesta y la guía institucional

Las secciones 3.13 y 4.7–4.8 explicitan requerimientos, distribución de tiempos y brillo digital. La matriz de actividades se conserva únicamente como nota personal en `Review/seguimiento_personal_propuesta.md`, fuera del informe. `Review/proposal_evidence/` conserva los datos derivados y sus fuentes; el análisis no repite inferencia ni modifica anotaciones. El brillo digital no equivale a lux; las etiquetas de oclusión proceden de inspección visual separada, no del brillo. Audio comprensible, latencia completa y ergonomía requieren evaluación adicional. `scripts/align_proposal.py` incorpora estos contenidos al constructor.

`Templates/Guia_Institucional_Informe_Final.docx` conserva la guía entregada el 16 de octubre. `Review/proposal_alignment_validation.json` registra sus reglas verificables y los datos que faltan para el cierre. Se mantiene la estructura institucional de doce secciones, cinco capítulos, introducción general, conclusiones, anexos y bibliografía. Las tablas se mantienen completas para evitar continuaciones sin identificar.

## Análisis de oclusión del 16 de octubre de 2026

La sección 4.8.1 incorpora un análisis observacional provisional con 889 etiquetas suplementarias producidas por inspección visual con GPT-6 Astra High, sin mostrar predicciones. No modifica la anotación COCO original. `Build/Testing/occlusion/` conserva protocolo, lotes, incidencias GT, métricas y visor de revisión del autor. El autor revisó 215 etiquetas; las otras 674 conservan la clasificación inicial por su decisión. El informe explicita esta revisión parcial, sin atribuir doble revisión independiente. `author_review.json` conserva la descarga importada y se utiliza automáticamente al recalcular. Antes del constructor, ejecutar `python Build/Testing/benchmark/analyze_occlusion.py` en el entorno del benchmark. `scripts/add_occlusion.py` incorpora sus resultados.

## Orientación del Gorillapod y estilo de referencias

La revisión del 20 de octubre de 2026 describe en las secciones 3.2 y 4.1 que el Gorillapod permite orientar libremente el celular y que en las pruebas se apuntó hacia los objetos. La sección 4.6 y las conclusiones vinculan los resultados con esta estrategia de encuadre; no se atribuye la diferencia exclusivamente al soporte.

La presentación sigue la plantilla institucional. Las citas numéricas y la bibliografía emplean estilo IEEE; la guía institucional permite elegir la norma bibliográfica de la disciplina y no exige APA. Esta identificación no sustituye la revisión individual de todas las referencias.

La bibliografía contiene 49 entradas; las citas del cuerpo enlazan con sus referencias y los DOI, URL e identificadores arXiv disponibles son clicables. `scripts/link_references.py` añade estos enlaces sin alterar el texto y se ejecuta al final del constructor. Son hipervínculos de Word, no campos de Zotero ni una biblioteca sincronizada; para gestión automática debe vincularse una biblioteca bibliográfica.

## Revisión de atribución del 20 de octubre de 2026

Se revisaron el texto completo, las tablas, las figuras y las referencias para distinguir fuentes externas, métodos conocidos y decisiones del proyecto. Se corrigieron citas de YOLOv8/YOLO11 y Third Eye, un DOI incorrecto de More et al., la referencia de la Benchmark Tool y varias explicaciones sin respaldo causal. Se añadieron fuentes de métricas, estadística, EXIF y software; las 49 entradas se numeran por primera cita y mantienen enlaces internos y externos.

`scripts/audit_citations.py` aplica las correcciones registradas en `citation_revision.json` antes de enlazar la bibliografía. `citation_number_map.json` permite relacionar los identificadores originales con la numeración nueva. La reproducción se comprobó desde el DOCX anterior. `Review/citation_audit.json` conserva el alcance, verificaciones y asuntos pendientes. Esta revisión no equivale a un certificado de ausencia de plagio ni a un informe de Turnitin o iThenticate. El autor confirmó que las imágenes externas del conjunto inicial se obtuvieron de Roboflow. La exportación del 5 de junio de 2026 conserva 80 imágenes, 257 anotaciones COCO y una declaración de licencia CC BY 4.0. El informe registra esta procedencia y remite al material archivado en `Build/models_comparison/test_images/`, sin atribuir dominio público ni inventar autores, nombre o versión del dataset. La trazabilidad se cierra con la evidencia conservada, sin requerir recuperar un enlace. `scripts/update_dataset_provenance.py` mantiene esta aclaración al reconstruir el documento.

## Versión final para presentación

Cierre editorial del 20 de octubre de 2026: 68 páginas, 49 referencias y sin marcadores pendientes. Se revisaron texto, tablas, encabezados, índices y campos; se actualizaron números romanos preliminares tras retirar la hoja de aceptación. `scripts/finalize_submission.py` mantiene el cierre al reconstruir el documento. `Review/submission_validation.json` conserva la verificación. Las limitaciones y el trabajo futuro forman parte del informe científico final.

## Enfoque del resumen y del sistema

El resumen, el abstract y las conclusiones presentan el desarrollo integrado desde la captura hasta la descripción auditiva. Se distinguen detecciones del modelo, selección para anuncios y métricas del sistema completo. Ambos resúmenes tienen menos de200 palabras. `scripts/update_system_overview.py` conserva la revisión editorial y `Review/system_overview_validation.json` documenta su comprobación.
