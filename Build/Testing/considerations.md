# Considerations for continuing the Chapter 4 work

Read this before regenerating or editing the chapter on another machine. It collects the
review items, assumptions and open decisions recorded when the chapter
(`Documents/Fragments/Capitulo 4 - Diseño experimental.docx`) was produced on 14 Oct 2026.

## How to rebuild everything

```bash
cd Build/Testing
python3.12 -m venv .venv
.venv/bin/python -m pip install -r benchmark/requirements.lock.txt
.venv/bin/python -m pip install python-docx
.venv/bin/python verify_package.py          # 570 files must match archived SHA-256
.venv/bin/python benchmark/analyze_depth.py benchmark/results/android.json
.venv/bin/python benchmark/plot_scenario1.py
.venv/bin/python scripts/build_chapter4.py  # writes Documents/Fragments/Capitulo 4
```

`scripts/build_chapter4.py` reads every number from the CSVs in
`benchmark/results/android/` — nothing is retyped, so rerunning with the same package
reproduces the chapter exactly. The desktop-proxy results in `benchmark/results/desktop/`
are NOT used by the chapter.

## Chapter additions created this session

- `benchmark/analyze_depth.py` → `benchmark/results/android/depth/` (Escenario 3):
  estimated camera-object distances, depth-band recall, `depth_recall.png`.
- `benchmark/plot_scenario1.py` → `benchmark/results/android/scenario1/` (Escenario 1 +
  config t tests): `boxplot_mount.png`, `boxplot_configuration.png`,
  `paired_t_tests.csv`, `mount_stats.csv`, `report.txt`.
- `scripts/build_chapter4.py` → the chapter docx.
- A hand-written Student-t p-value lives in `plot_scenario1.py`
  (`_betacf`/`student_t_pvalue`, validated against t-table critical values: df 10/32/33).
  If scipy becomes available, cross-check it once against `scipy.stats.t.sf`.

## Depth model (Escenario 3) — decisions and caveats

- No new photos were taken. Distances come from the pinhole model
  `d = f_px * H_ref / h_px` using EXIF `FocalLengthIn35mmFilm` per photo
  (1x ≈ 25 mm, 0.5x ≈ 14 mm) and fixed reference heights per class.
- In 7 of 198 photos the EXIF focal disagrees with the manifest lens
  (`depth/exif_lens_mismatches.csv`); the EXIF value wins.
- Reference heights (m): person 1.70, refrigerator 1.75, chair 0.90, couch 0.85,
  toilet 0.78, dining table 0.76, sink 0.80, tv 0.60, bed 0.60, laptop 0.25.
  Uncertainty is proportional (~±30%), so results are bands only.
- Recall is not monotone with distance because class mix changes with distance
  (beds/laptops close, chairs far): depth is partially confounded with class.
  Suggested range (~4 m, recall ≥ 50 % with ≥ 30 instances) is stated in the chapter as
  an operational guideline, NOT a sensor characterization. If adopted as a product rule,
  validate with measured distances in a large classroom.
- Bootstrap CIs per band resample the 33 capture groups (10k draws, seed 20261013);
  band 0.5–1 m has few groups, so its CI is wide.

## Review items agreed for the thesis

- Photo count vs. advisor note: the study has **33 photos per configuration**, the
  meeting note said 30. The chapter reports 33; if the advisor insists on 30, subset
  groups 1–30 and rerun the two analysis scripts (they key on capture groups, so a
  filtered `capture_group` list would need a small change).
- Comparison basis: Gorillapod 0.5x is the count objective (max objects announced);
  chest harness 1x is the F1 objective. The chapter presents both; a universal winner
  is deliberately NOT claimed (chest 0.5x difference CI includes zero).
- The app top-two list analysis models the speech output only in count terms; audio
  clarity is not measured (belongs to the audio-descriptor module).
- Validity limits copied into section 4.6 come from `README.md` of this folder; keep
  both documents in sync if the evaluation changes.
- The GT was single-human-reviewed (model-assisted draft corrected by the author);
  no second-reviewer audit. List as internal-validity threat (done in 4.6).
- Emulator latency is debug-profile only (median 246.3 ms detection, 104.0 ms
  decode+preprocess). Do not quote as physical Pixel 8 performance.

## Git / provenance discipline

- The chapter builder and the two analysis scripts are committed; outputs under
  `benchmark/results/android/depth/` and `scenario1/` are committed too so the docx
  can be regenerated without running the analyses.
- `SHA256SUMS.json` predates the depth/ scenario1/ outputs (they are new files, not
  replacements); it still verifies the archived 570 files with `verify_package.py`.
  Regenerate the checksum manifest only if the archived run files ever change.
- Do not mix desktop proxy rows into any Android table.
- `Build/models_comparison/` has unrelated uncommitted work (venv, models, panorama
  dataset). It is excluded from the Chapter 4 commits on purpose.
