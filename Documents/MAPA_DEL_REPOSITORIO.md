# Mapa de los componentes principales

[Inicio](../README.md) · [Informe](Informe_Final_AssistiveVision.docx) · [Reproducción](../docs/REPRODUCIR.md)

```text
indoor-detect/
├── Build/
│   ├── Testing/              # fotos, GT, modelo, análisis y resultados finales
│   └── models_comparison/    # conjuntos y código de la comparación histórica
├── Documents/                # Word, figuras, bibliografía y presentaciones finales
├── docs/                     # guías de datos, reproducción y validación
├── scripts/                  # comandos activos de reproducción y verificación
├── development/              # todo el material intermedio y auxiliar
│   ├── annotation_drafts/
│   ├── editorial/
│   ├── notes/ y planning/
│   ├── presentations/
│   ├── validation/
│   └── runs/                 # nuevas pruebas, ignoradas por Git
└── .github/workflows/        # automatización de las verificaciones
```

## Qué archivo utilizar

| Necesidad | Referencia |
|---|---|
| Manuscrito | [Documents/Informe_Final_AssistiveVision.docx](Informe_Final_AssistiveVision.docx) |
| Fotografías originales | [Build/Testing/data/](../Build/Testing/data/) |
| Anotación final | [Build/Testing/labels.json](../Build/Testing/labels.json) |
| Grupos, montajes y lentes | [capture_groups.csv](../Build/Testing/capture_groups.csv) |
| Predicciones y tiempos originales | [android.json](../Build/Testing/benchmark/results/android.json) |
| Tablas y gráficos | [benchmark/results/android/](../Build/Testing/benchmark/results/android/) |
| Brillo y tiempos derivados | [benchmark/results/brightness/](../Build/Testing/benchmark/results/brightness/) |
| Modelo y procedencia | [benchmark/models/](../Build/Testing/benchmark/models/) y [provenance/](../Build/Testing/provenance/) |
| Oclusión | [occlusion/README.md](../Build/Testing/occlusion/README.md), etiquetas y resultados en esa carpeta |
| Repetir análisis | [scripts/reproduce.py](../scripts/reproduce.py) |
| Nueva inferencia Android | [scripts/run_android_benchmark.py](../scripts/run_android_benchmark.py) |
| Comprobar el paquete original tras los traslados | [scripts/verify_archive.py](../scripts/verify_archive.py) |
| Generar análisis de brillo | [scripts/analyze_brightness.py](../scripts/analyze_brightness.py) |
| Recuperar modelos históricos | [docs/HISTORICO.md](../docs/HISTORICO.md) |
| Consultar borradores y revisiones | [development/README.md](../development/README.md) |

La aplicación es un proyecto separado:
[diomedescerda/AssistiveVision](https://github.com/diomedescerda/AssistiveVision).
Su directorio `app/` conserva código, activos y tests; `development/` contiene
los logs y herramientas auxiliares. `dist/` contiene los paquetes APK locales.

## Integridad y límites

La reorganización cambia rutas, no las cajas GT, fotografías, modelo ni cifras
publicadas. El manifiesto original de 570 sumas se conserva sin reescribir;
`development/relocations.json` permite encontrar los 281 archivos reubicados.
Los resultados temporales se generan fuera de las referencias científicas.
La comparación histórica conserva sus discrepancias de reproducción, descritas
por separado en la guía correspondiente. Los registros de validación están
agrupados en `development/validation/`; su resumen legible permanece en `docs/`.

La rama principal del repositorio Android AssistiveVision es **`main`**. Las guías de compilación y descarga de APK deben consultarse en esa rama; el replay experimental usa el commit histórico explícito de su guía.
