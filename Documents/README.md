# Informe final de AssistiveVision

El manuscrito de trabajo es **Informe_Final_Trabajo_de_Grado_AssistiveVision.docx**. Integra la comparación histórica de modelos, la implementación actual y la evaluación de 198 fotografías (889 anotaciones, 33 grupos y seis configuraciones). Se actualizó el 16 de octubre de 2026 para vincular las tres fases de la propuesta con sus evidencias y límites.

`Templates/Informe_Final_Base_2026-09-25.docx` conserva el original sin modificaciones. El manuscrito mantiene su geometría de página, doce secciones, escudo, estilos y estructura institucional. Se repararon portada, encabezados, índices y tablas. `Fragments/` contiene el capítulo experimental independiente; el manuscrito completo es la versión principal para seguir escribiendo.

## Continuar desde otro equipo

Hacer `git pull` y abrir el manuscrito en Word o LibreOffice. Guardar y confirmar los cambios en ese archivo. Los datos, anotaciones, predicciones y análisis están en `Build/Testing/`; `Review/2026-10-14_revision.md` documenta las correcciones y comprobaciones de esta revisión.

Se incorporaron los nombres del autor y de los supervisores, y el grupo TecnOS, desde la propuesta. Permanecen pendientes los títulos académicos de los supervisores, la línea de investigación y los agradecimientos opcionales. No se inventaron esos datos. Revisar además las discrepancias EXIF antes de cerrar la selección de lente. El resultado de profundidad es exploratorio y las latencias del emulador no representan un Pixel 8 físico.

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
