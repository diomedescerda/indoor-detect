# Informe y materiales finales

[Inicio](../README.md) · [Reproducir resultados](../docs/REPRODUCIR.md) · [Mapa](MAPA_DEL_REPOSITORIO.md)

El manuscrito principal es [Informe_Final_AssistiveVision.docx](Informe_Final_AssistiveVision.docx).
Contiene cinco capítulos, conclusiones vinculadas a los objetivos, un único anexo
de repositorios/reproducción y 49 referencias. La presentación conserva el formato
institucional e incorpora las figuras de interfaz, escenas y los tres soportes.

La [copia más reciente en revisión](Informe_Final_AssistiveVision_Revision_Formato_Zotero.docx)
conserva el ajuste de cohesión e incorpora capturas reales de la interfaz y seis
fotografías del conjunto experimental. La Figura 4.2 incorpora las imágenes
comerciales de los arneses de cabeza y pecho y del palo de selfie con trípode
identificado por el autor. La terminología de texto, tablas y gráficos está corregida. Los
[orígenes y la regeneración de las imágenes](Figures/README.md) están documentados.
La revisión vigente aplica la guía institucional de márgenes, encabezados,
numeración, capítulos en página impar y espaciado. Incluye 91 campos de cita de
Zotero vinculados a los 49 registros de la colección y una bibliografía APA
generada por Zotero. [Cómo mantener las referencias](Referencias/README.md).

| Contenido | Ubicación |
|---|---|
| Informe final editable | [Informe_Final_AssistiveVision.docx](Informe_Final_AssistiveVision.docx) |
| Figuras del informe | [Figures/](Figures/) |
| Referencias exportadas de Zotero | [Referencias/](Referencias/) |
| Presentaciones finales | [Slides/](Slides/) |
| Propuesta de pasantía | [Propuesta original](Propuesta%20Pasantia%20de%20Investigación%20-%20Diomedes%20Cerda.pdf) |
| Recorrido por los resultados | [GUIA_DE_LECTURA.md](GUIA_DE_LECTURA.md) |

Los datos y resultados científicos permanecen en `Build/Testing/`; el análisis de
brillo está en `Build/Testing/benchmark/results/brightness/`. Los comandos activos
están en `scripts/`. Para consultar el informe y reproducir sus resultados no se
necesitan los constructores editoriales.

Los borradores, documentos comentados, manuscritos anteriores, plantillas,
notas, diagnósticos y herramientas de edición se agrupan en
[development/](../development/README.md). La
[comparación de cambios](../development/editorial/revision/Cambios_tutor_AssistiveVision.html)
y la [guía de reconstrucción](../development/editorial/revision/README.md) se
conservan allí para trazabilidad y no constituyen entregables científicos separados.
No reconstruir el Word sobre ediciones manuales sin incorporarlas primero al constructor.

Los registros auxiliares y los borradores trasladados conservan su identidad en
`development/relocations.json`. Las nuevas pruebas se guardan en
`development/runs/`, ignorado por Git. El archivo de la biblioteca local de literatura
es opcional, tampoco está versionado ni es necesario para repetir los experimentos.

Para probar la app, usar **[Descargar APK](https://github.com/diomedescerda/AssistiveVision/releases/latest/download/AssistiveVision-1.0-debug.apk)**.
[Las versiones publicadas](https://github.com/diomedescerda/AssistiveVision/releases/latest) incluyen el manifiesto de fuentes y los comprobantes. El código actual se mantiene en `AssistiveVision/main`.
