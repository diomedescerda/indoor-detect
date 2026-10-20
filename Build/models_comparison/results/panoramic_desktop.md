* These benchmarks were executed on panoramic images (equirectangular projection) on a system running Arch Linux with an Intel Core i5-12450H processor, Intel UHD integrated graphics, and 8 GB RAM. Inference was performed using TensorFlow Lite under CPU-only execution.

========================================
  YOLOv8s Float32
========================================
  MAP50:        0.499
  MAP50-95:     0.369
  Precision:    0.732
  Recall:       0.453
  F1 Score:     0.560

========================================
  YOLOv8s Float16
========================================
  MAP50:        0.499
  MAP50-95:     0.369
  Precision:    0.734
  Recall:       0.453
  F1 Score:     0.561

========================================
  YOLO11n Float32
========================================
  MAP50:        0.402
  MAP50-95:     0.279
  Precision:    0.729
  Recall:       0.315
  F1 Score:     0.440

========================================
  YOLO11n Float16
========================================
  MAP50:        0.402
  MAP50-95:     0.281
  Precision:    0.733
  Recall:       0.315
  F1 Score:     0.440

========================================
  SSD MobileNetV1
========================================
  MAP50:        0.100
  MAP50-95:     0.053
  Precision:    0.162
  Recall:       0.115
  F1 Score:     0.135

========================================
  EfficientDet-Lite2
========================================
  MAP50:        0.269
  MAP50-95:     0.165
  Precision:    0.610
  Recall:       0.220
  F1 Score:     0.323

