# AssistiveVision capture configuration benchmark

This directory preserves the 198-photo study and its completed Android benchmark for paper writing and reproduction on another computer. The benchmark date is **13 October 2026**. Start with [the Word report](AssistiveVision_Benchmark_Report.docx).

**Current interpretation:** Gorillapod + 0.5x is the provisional choice when the objective is the number of correctly detected objects across scenes. Chest harness + 1x leads F1. These are different objectives; the count objective was emphasized after the initial F1 analysis and is exploratory.

The data contain 33 successive six-photo groups, with 889 reviewed objects in ten COCO classes. Every group follows head 1x, head 0.5x, chest 1x, chest 0.5x, gorillapod 1x, gorillapod 0.5x. Groups use ascending original IMG numbers. They are acquisition groups, not necessarily independent rooms or environments.

## Results to use in the paper

| Setup | Objects in frame | Correct detections | False detections | Detector F1 | Correct after top two limit |
|---|---:|---:|---:|---:|---:|
| Head 1x | 129 | 56 | 20 | 54.6% | 31 |
| Head 0.5x | 164 | 70 | 36 | 51.9% | 37 |
| Chest 1x | 124 | 65 | 21 | 61.9% | 37 |
| Chest 0.5x | 153 | 77 | 32 | 58.8% | 44 |
| Gorillapod 1x | 145 | 75 | 29 | 60.2% | 40 |
| Gorillapod 0.5x | 174 | 82 | 31 | 57.1% | 49 |

At confidence 0.30 and IoU 0.50, Gorillapod 0.5x has 17 more correct detections than chest 1x, with 16 scene wins, 10 ties and 7 losses. The paired difference is 0.515 correct objects per scene, exploratory 95% bootstrap interval [0.121, 0.939]. Against chest 0.5x the difference is only 0.152 [−0.182, 0.515]. A universal winner is not established.

- [Scene analysis report](benchmark/results/android/scenes/report.txt): all 33 scenes, definitions, paired count comparisons and counterexamples.
- [Scene count chart](benchmark/results/android/scenes/scene_counts.png) and [all six-view scene sheets](benchmark/results/android/scenes/sheets/).
- [Configuration metrics](benchmark/results/android/summary.csv): P/R/F1, COCO AP, counts and emulator timing.
- [Per-image metrics](benchmark/results/android/per_image.csv), [per-class metrics](benchmark/results/android/per_class.csv), [paired F1 comparisons](benchmark/results/android/paired_comparisons.csv) and [paired count differences](benchmark/results/android/scenes/paired_count_differences.csv).
- [Raw Android predictions](benchmark/results/android.json): complete 198-frame output and provenance. **Primary run for reporting.**
- [Desktop proxy](benchmark/results/desktop/): a secondary comparison with a different runtime and JPEG resizing. Do not mix its rows or timing with Android results.

## Dataset and annotation history

- `data/`: all 198 original-resolution JPEGs, with lowercase extensions; bytes match the source photographs.
- `labels.json`: **reviewed ground truth**, 198 images, 889 boxes, 16 empty images. This is the evaluation input.
- `capture_groups.csv`: filenames, sequence, mount, lens and original image SHA-256 hashes.
- `images.coco.json`: image manifest without object annotations.
- `annotation_history/roboflow_reviewed.coco.json`: original corrected Roboflow export. Category names were mapped to true COCO IDs. Thirteen boxes exceeded image edges by export rounding and were clipped within a 0.05-pixel tolerance.
- `preannotations.coco.json`, `chat_boxes.json`, `review/`, `review_checklist.csv`: **historical unreviewed draft material**. Do not use these as final ground truth. The checklist records the initial state and does not supersede the later corrected export.
- `annotation_history/initial_draft_notes.txt`: historical procedure and caveats. Its statements that review, labels and benchmarking are pending describe that earlier stage only.

The initial draft was created through the Codex chat and then corrected by the user in Roboflow. GPT-6.1 Sol was requested for the draft; the saved files do not independently prove the exact serving model. EfficientDet was not used to create the initial boxes. This is human-corrected model-assisted ground truth, with no independent second-reviewer audit.

Class IDs: person 1, chair 62, couch 63, bed 65, dining table 67, toilet 70, tv 72, laptop 73, sink 81, refrigerator 82. COCO boxes are pixel `[x, y, width, height]`. All images are 1536 by 2048, with no EXIF rotation required.

## Reproduce the analysis on another computer

Clone or pull this repository, then work from `Build/Testing`. Python 3.12 was used for the benchmark. Saved predictions allow all evaluation and figures to be regenerated without Android Studio or inference.

```bash
cd Build/Testing
python3.12 -m venv .venv
.venv/bin/python -m pip install -r benchmark/requirements.lock.txt
.venv/bin/python verify_package.py
.venv/bin/python verify_gt.py labels.json
.venv/bin/python -m unittest discover -s benchmark -p 'test_*.py'
.venv/bin/python benchmark/evaluate.py benchmark/results/android.json
.venv/bin/python benchmark/analyze_effects.py benchmark/results/android
.venv/bin/python benchmark/analyze_scenes.py
.venv/bin/python benchmark/render_predictions.py benchmark/results/android.json
```

The frozen dependencies record the working environment; wheel availability can vary by OS and architecture. To evaluate saved results only, the essential libraries are NumPy, Pillow, pycocotools and Matplotlib. LiteRT is needed only for desktop inference. On Windows, use `.venv\Scripts\python.exe`.

Optional desktop inference with the archived exact model:

```bash
.venv/bin/python benchmark/run_desktop.py --model benchmark/models/efficientdet-lite2-detection-metadata.tflite --output benchmark/results/desktop-rerun.json
```

For a new Android run, clone `git@github.com:diomedescerda/AssistiveVision.git` separately and check out commit `85c852ddcb543bce1bd69ad0db307f895d597881`. Copy `benchmark/android/DatasetBenchmarkTest.kt` into `app/src/androidTest/java/com/unimagdalena/assistivevision/` in that checkout. Install the SDK required by the app, start an emulator or authorize a phone, and run:

```bash
.venv/bin/python benchmark/run_android.py --app /path/to/AssistiveVision --sdk /path/to/Android/Sdk --serial emulator-5554 --confidence 0.30 --max-objects 2
```

The runner builds and installs debug APKs and stages the photos. It overwrites `benchmark/results/android.json` and generated Android metrics, so preserve the archived run before rerunning. `--skip-build` is only for APKs already built from the current checkout. The runner does not uninstall the app on a signature conflict.

## Method and reporting limits

The Android test invokes production `PreprocessingModule`, `DetectionModule` and `LetterboxMapper`, using EfficientDet-Lite2 at 448 by 448. It retains low-floor detections at 0.001, capped at 15. Operating P/R/F1 and counts use confidence 0.30, class agreement and greedy one-to-one matching at IoU >= 0.50. COCO AP uses the saved low-score predictions. The `app_output` analysis applies the default top-two cap to the score-ordered detections; it models the selected-object list and does not test speech behavior.

Pixel_8 is an **Android emulator profile** (Android 17, API 37, x86_64, 16 KB pages). JPEGs came from the iPhone. The completed run's detection-method median is 246.3 ms, p95 307.5 ms, and JPEG decode/preprocessing median is 104.0 ms. These are debug emulator measurements, not physical Pixel 8 performance or end-to-end latency.

Count differences describe annotated photo instances, not unique objects tracked across views. Objects outside a frame are not detector false negatives. Successive capture also allows people and poses to change. Chairs comprise 438/889 annotations, so pooled counts and F1 are class-imbalanced. Bootstrap intervals use 10,000 paired capture-group resamples, seed 20261013, without multiplicity correction; shared rooms may make them optimistic. Selecting a configuration on these data requires validation on new scenes and the actual target phone.

## Integrity and provenance

`provenance/android_run_metadata.json` preserves the app commit, runtime/device information, model and GT hashes, and hashes of the production Kotlin files. `provenance/app_source/` contains those source snapshots. `benchmark/android/` contains the exact executed instrumentation test. `benchmark/models/` contains the app's model asset. The model came from the AssistiveVision checkout; its upstream origin and license should be documented before publication.

`SHA256SUMS.json` and `verify_package.py` check the committed package. After intentionally regenerating a file, its checksum can change; retain the original commit as the benchmark record. Drafts and final results are both preserved, but duplicate ZIPs, the virtual environments, APKs, caches and interrupted checkpoints are excluded. The interrupted run was not used in the reported metrics.

The Word report can be rebuilt with `python scripts/build_report.py` after installing `python-docx`. The report builder reads the saved metric files rather than retyping table values. Original QA renders are local intermediates and are not part of the repository.
