# Referencias del informe

[Informe final](../Informe_Final_AssistiveVision.docx) · [Inicio](../../README.md)

La colección [AssistiveVision — Trabajo de grado](https://www.zotero.org/diomedescerda/collections/X2VAUMZ3)
contiene 49 referencias. Esta carpeta conserva las exportaciones finales:

- [Bibliografia_APA_Zotero.html](Bibliografia_APA_Zotero.html): bibliografía generada por Zotero, APA, español.
- [biblioteca_sincronizada.csl.json](biblioteca_sincronizada.csl.json): exportación de los registros reales de la colección.
- [referencias_assistivevision.csl.json](referencias_assistivevision.csl.json) y [referencias_assistivevision.ris](referencias_assistivevision.ris): copias de intercambio de las mismas referencias.

Las referencias ya están añadidas a la cuenta. No volver a importar ambos
archivos en la biblioteca existente. Los comprobantes de importación, copias de
metadatos anteriores y herramientas auxiliares están en
`development/editorial/revision/Zotero/` y `development/editorial/scripts/`.
Las credenciales no forman parte del repositorio. La revisión de formato del
6 de noviembre incorpora **91 campos de cita de Zotero** y un campo de
bibliografía en el Word. Contienen los identificadores de los 49 registros de
la colección y una copia de sus datos para que el documento sea portátil.
La bibliografía visible se obtiene de Zotero con el estilo `apa` y la
configuración regional `es-ES`.

La colección se consultó mediante la API autenticada el 6 de noviembre. Se
completaron los cinco autores del artículo de Meenakshi a partir de
[la publicación original](https://www.techscience.com/cmc/v73n2/48359), conservando
su clave de Zotero. Se descargaron nuevamente las cuatro exportaciones de esta
carpeta y se normalizó el uso de mayúsculas de siete títulos para APA, conservando
los nombres propios. El RIS utiliza saltos de línea LF para su seguimiento en Git.
El [comprobante de actualización](../../development/editorial/revision/Zotero/actualizacion_formato_2026-11-06.json)
registra el cambio y los hashes; no contiene credenciales.

Para actualizar citas en Word, abrir el documento con Zotero y su complemento
instalados, sincronizar la misma cuenta y usar **Zotero → Refresh**. Mantener el
estilo APA y el idioma español en las preferencias del documento. No usar
**Unlink Citations** en la copia editable: elimina la vinculación.
El complemento de escritorio no se ejecutó en esta sesión Linux; se comprobaron
los campos, los datos incrustados y la exportación de la API. Para cambiar entre
Word y LibreOffice, seguir [el procedimiento de Zotero](https://www.zotero.org/support/kb/moving_documents_between_word_processors).

Para consultar la bibliografía sin Zotero, abrir el HTML. Para llevarla a una
biblioteca nueva, importar una sola copia de intercambio (por ejemplo, el RIS);
conservar los otros archivos como exportaciones del mismo conjunto.
