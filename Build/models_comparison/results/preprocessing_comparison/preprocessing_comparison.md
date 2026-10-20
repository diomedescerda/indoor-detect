# Panoramic Preprocessing Comparison — YOLOv8s Float16

Comparing inference-time preprocessing to improve object detection on equirectangular panoramas.
Baseline = whole equirectangular image, letterboxed to 640x640 (the current project pipeline).

| Method | mAP50 | mAP50-95 | Precision | Recall | F1 |
|--------|-------|----------|-----------|--------|-----|
| **Baseline (no preprocessing)** | **0.499** | **0.369** | **0.734** | **0.453** | **0.561** |
| Lens distortion correction (Browń-Conrady) | 0.462 | 0.325 | 0.677 | 0.424 | 0.521 |
| Vignetting correction | 0.479 | 0.359 | 0.738 | 0.451 | 0.560 |
| CLAHE contrast normalization | 0.478 | 0.355 | 0.738 | 0.442 | 0.553 |
| Distortion + vignetting | 0.465 | 0.324 | 0.683 | 0.426 | 0.524 |
| Full pipeline (dist+vign+contrast) | ~0.28–0.46 | – | – | – | – |
| Perspective strips (4x90°, GT transformed) | 0.013 | 0.006 | 0.044 | 0.032 | 0.037 |

## Conclusions

**Off-the-shelf inference-time preprocessing does NOT fix the panoramic problem.**

1. **Geometric/radiometric corrections hurt or are neutral.** Lens distortion correction,
   vignetting correction, and CLAHE all *reduce* mAP50 (0.462–0.479 vs 0.499). Two reasons:
   - The default Brown–Conrady / vignetting parameters do not match the actual camera/lens that
     captured these panoramas, so we add distortion instead of removing it.
   - Any pixel-level change shifts the input statistics away from the distribution the detector
     was trained on (perspective COCO images).

2. **Perspective-strip extraction (projection change) collapses mAP.** The model *does* emit
   detections on perspective strips, but transforming the ground-truth boxes into each strip's
   coordinate space produces a poor match (mAP50 0.013). Strip-edge distortion plus projecting only
   the 4 box corners onto the sphere yields inconsistent GT, and the off-the-shelf detector is not
   robust to the heavy stretching at strip borders.

3. **Root cause is train-time, not test-time.** The whole-image baseline already beats every
   fix because the detector was *trained* on perspective images. This matches the project's own
   earlier finding: "the bottleneck is the representation, not the quantization."

## What would actually improve it (training-time)

- **Equirectangular-aware fine-tuning** — fine-tune YOLO on synths distortion (horizontal
  scale by cos(latitude)) so it learns the projection.
- **Cubemap / perspective-crop training & inference** — train on cube faces, then at test time
  detect per face/strip and warp detections back to equirectangular (the correct version of the
  strip idea, with a detector trained on *those* views).
- **Larger input resolution / no downsizing** to the 640x640 letterbox, since small objects at
  the poles are the biggest recall loss.
