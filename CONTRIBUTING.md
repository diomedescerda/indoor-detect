# Contribuir y conservar la evidencia

Usar la [guía de reproducción](docs/REPRODUCIR.md) antes de cambiar análisis.
`python scripts/reproduce.py` escribe en una carpeta nueva sin reemplazar el archivo experimental.

Para un experimento nuevo, conservar datos, GT, commit de app, hashes del modelo
y módulos, dispositivo/runtime, configuración, predicciones crudas y comandos.
Separar los tiempos de cada equipo. Cambiar umbral, GT, modelo o código constituye
otra ejecución, no una corrección silenciosa del original. No actualizar hashes
para ocultar diferencias inesperadas.

Para cambios de análisis, comprobar que la reproducción completa sigue pasando
y añadir comprobaciones relevantes del comportamiento numérico modificado.
Para la app, seguir su repositorio. CI genera artefactos; no guardar entornos,
cachés, APKs ni resultados temporales en Git.

Para el informe, conservar el original y usar el [mapa documental](Documents/README.md).
Los constructores anteriores pueden sustituir ediciones manuales. Describir qué
objetivo, tabla o figura cambió y qué fuente de datos respalda el cambio.

Mantener los materiales de preparación, revisión y diagnóstico en `development/`.
Las nuevas ejecuciones deben ir a `development/runs/`, ignorado por Git.
Si se traslada un archivo protegido por el manifiesto original, documentar su
destino en `development/relocations.json` y comprobar las 570 sumas; no sustituir
la suma antigua por la de un contenido distinto. El Word final se mantiene en
`Documents/Informe_Final_AssistiveVision.docx`.
