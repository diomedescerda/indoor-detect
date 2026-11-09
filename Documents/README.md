# Informe y materiales finales

[Inicio](../README.md) · [Reproducir resultados](../docs/REPRODUCIR.md) · [Mapa](MAPA_DEL_REPOSITORIO.md)

El informe final principal es **[Informe Final Pasantía de Investigación - Diomedes Cerda.pdf](Informe%20Final%20Pasant%C3%ADa%20de%20Investigaci%C3%B3n%20-%20Diomedes%20Cerda.pdf)** (junto con el manuscrito editable [Informe_Final_AssistiveVision.docx](Informe_Final_AssistiveVision.docx)).
Contiene cinco capítulos, conclusiones vinculadas a los objetivos, un único anexo
de repositorios/reproducción y 49 referencias. La presentación conserva el formato
institucional e incorpora las figuras de interfaz, escenas y tipos de soporte.
La Figura 3.2 presenta los soportes en «Posicionamiento del dispositivo»; la Figura 4.2
muestra las fotografías de su colocación para la captura.

El informe final aplica las últimas observaciones de la directora: interpretación de tablas,
accesibilidad, ejemplo de audio y conclusiones. Conserva las capturas de la interfaz,
las seis fotografías del conjunto y todos los valores numéricos de las tablas.
Los modelos de soporte se muestran en la Figura 3.2, con sus fuentes enlazadas.
La Figura 4.2 incorpora las fotografías del autor con la colocación en cabeza,
pecho y palo de selfie. Las figuras de regiones, secuencia e interfaz pasan a 3.3, 3.4 y
3.5, con sus menciones e índice actualizados.
El [registro de cambios](CAMBIOS_REVISION_FINAL.md) permite revisar el alcance.
La terminología de texto, tablas y gráficos está corregida. Los
[orígenes y la regeneración de las imágenes](Figures/README.md) están documentados.
La revisión vigente aplica la guía institucional de márgenes, encabezados,
numeración, capítulos en página impar y espaciado. Incluye 91 campos de cita de
Zotero vinculados a los 49 registros de la colección y una bibliografía APA
generada por Zotero. La consulta autenticada del 9 de noviembre confirmó que los
49 registros y el HTML APA coinciden con las exportaciones conservadas.
[Cómo mantener las referencias](Referencias/README.md).

| Contenido | Ubicación |
|---|---|
| Informe final (PDF) | [Informe Final Pasantía de Investigación - Diomedes Cerda.pdf](Informe%20Final%20Pasant%C3%ADa%20de%20Investigaci%C3%B3n%20-%20Diomedes%20Cerda.pdf) |
| Informe final editable (Word) | [Informe_Final_AssistiveVision.docx](Informe_Final_AssistiveVision.docx) |
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
