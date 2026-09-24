Adaptation
- Preprocessing: Letterbox resize to 448x448, RGB tensor in uint8 format matching EfficientDet-Lite2 input spec
- Output parsing: Boxes [ymin, xmin, ymax, xmax] → RectF, 0-indexed class IDs +1 for COCO mapping, confidence filtering at 0.30
- Target classes: Filtered to 10 relevant COCO classes (person, chair, couch, bed, table, toilet, tv, computer, sink, refrigerator)

Integration
- TFLite runtime: Added as dependency (org.tensorflow:tensorflow-lite:2.16.1)
- Model loading: From assets via MappedByteBuffer, interpreter created once at startup
- Pipeline: CaptureModule (9 FPS) → PreprocessingModule → DetectionModule → LocalizationModule
- State exposure: MainViewModel exposes `StateFlow<List<Detection>>` to the Activity
- Output tensor handling: Dynamically queries model output shape (25 max detections) instead of hardcoding
- Performance: Frame rate capped at 9 FPS to match model throughput (~8.55 FPS benchmark)