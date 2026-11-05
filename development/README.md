# Material intermedio de desarrollo

[Descargar APK](https://github.com/diomedescerda/AssistiveVision/releases/latest/download/AssistiveVision-1.0-debug.apk) · [Volver al proyecto](../README.md) · [Informe final](../Documents/Informe_Final_AssistiveVision.docx)

Esta carpeta reúne borradores, revisión editorial, diagnósticos y ejecuciones de
trabajo. Se excluyen del recorrido principal de la entrega. La referencia científica
sigue en `Build/Testing/labels.json`, sus fotografías y los resultados archivados;
la aplicación se compila desde el repositorio AssistiveVision.

| Carpeta | Contenido | Uso |
|---|---|---|
| `annotation_drafts/` | Preanotaciones, previews, checklist, hojas de inspección y visor de oclusión | Historia de preparación; no GT final |
| `editorial/scripts/` | Constructores Word y herramientas bibliográficas | Mantenimiento editorial opcional |
| `editorial/review/` | Archivo comentado de la tutora y revisiones anteriores | Fuentes y antecedentes de edición |
| `editorial/revision/` | Comparación de cambios, navegación y verificaciones editoriales | Auditoría de la revisión actual |
| `editorial/templates/`, `editorial/fragments/`, `editorial/previous_reports/` | Plantillas, capítulos sueltos y manuscritos antiguos | No sustituir el informe final con estas copias |
| `editorial/benchmark_builders/` | Constructores antiguos del reporte experimental | El original `build_report.py` se conserva congelado; `build_report_adapted.py` usa las rutas nuevas |
| `dataset_exports/` | Exportación panorámica original y árbol de imágenes de preparación | El conjunto utilizado por el análisis sigue en `Build/models_comparison/panoramic/data/` |
| `notes/`, `planning/` | Reuniones y planificación personal | Material de trabajo |
| `presentations/` | Generadores auxiliares de diapositivas | Escriben en `runs/presentations/` |
| `validation/` | Logs y comprobantes de verificaciones locales | Evidencia técnica auxiliar, sin sustituir resultados científicos |
| `runs/`, `scratch/` | Ejecuciones regeneradas y pruebas locales | Ignorados por Git |
| `reference_library/` | Biblioteca local y ZIP de literatura del autor, si están presentes | Ignorados por Git; no necesarios para reproducir |

## Integridad tras la reorganización

`relocations.json` registra ruta anterior, destino, tamaño y SHA-256 antes del
traslado. Los archivos del paquete base mantienen sus bytes originales; el
verificador busca cada uno en su destino documentado:

```sh
python3 scripts/verify_archive.py
```

El comando se ejecuta desde la raíz y verifica las 570 sumas del manifiesto
histórico, incluidas las de 281 archivos reubicados. No se cambiaron los hashes
para aceptar archivos distintos. Los originales congelados de `verify_gt.py`,
`verify_package.py` y README se conservan en `annotation_drafts/Testing/`.
Los pequeños ejecutores de compatibilidad que quedan en `Build/Testing/`
redirigen a los verificadores activos, sin generar informes junto a GT.

## Herramientas editoriales

La guía de reconstrucción está en [editorial/revision/README.md](editorial/revision/README.md).
El constructor actual utiliza el Word comentado conservado y escribe el informe
en `Documents/Informe_Final_AssistiveVision.docx`; sus comprobantes se quedan aquí.
Los constructores antiguos pueden reemplazar sus salidas y no forman parte del
flujo necesario para reproducir los experimentos.

Para abrir el visor opcional de oclusión, usar
`development/annotation_drafts/occlusion/review.html`. Lee las fotografías finales
de `Build/Testing/data/`; descargar el JSON revisado antes de cerrar. No modifica
automáticamente la anotación principal.
