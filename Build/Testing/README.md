# Reviewed capture study

[Repository home](../../README.md) · [Español](LEEME.md) · [Reproduce results](../../docs/REPRODUCIR.md) · [Download APK](https://github.com/diomedescerda/AssistiveVision/releases/latest/download/AssistiveVision-1.0-debug.apk)

This directory contains the final 198-photo / 889-instance dataset and the
scientific analysis. It retains the reviewed GT, capture groups, original
photographs, detector model, raw Android predictions, final result tables,
analysis code and required numerical tests.

From the repository root, with the [documented Python environment](../../docs/REPRODUCIR.md#antes-de-empezar):

```sh
python scripts/verify_archive.py
python scripts/reproduce.py --overlays
```

New outputs go to `development/runs/saved-results/` and never replace the archived
results. Annotation drafts, preview images, old report builders and work notes
are grouped in [development/](../../development/README.md). They are not final GT.
The original checksum-protected README and helpers remain there as frozen records;
the relocation-aware verifier still checks their original hashes.

Final report: [Documents/Informe_Final_AssistiveVision.docx](../../Documents/Informe_Final_AssistiveVision.docx).
