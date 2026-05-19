#!/bin/bash

BENCHMARK=/data/local/tmp/android_benchmark
MODELS_DIR=/data/local/tmp
THREADS=4
RUNS=50

run_benchmark() {
    local name=$1
    local model=$2
    local gpu=$3

    echo "Corriendo: $name..."

    if [ "$gpu" = "true" ]; then
        result=$(adb shell $BENCHMARK \
            --graph=$MODELS_DIR/$model \
            --num_threads=$THREADS \
            --num_runs=$RUNS \
            --use_gpu=true 2>&1)
    else
        result=$(adb shell $BENCHMARK \
            --graph=$MODELS_DIR/$model \
            --num_threads=$THREADS \
            --num_runs=$RUNS 2>&1)
    fi

    inference_line=$(echo "$result" | grep "Inference timings")
    count_line=$(echo "$result" | grep "count=$RUNS")

    avg=$(echo "$inference_line" | grep -oP 'Inference \(avg\): \K[0-9]+')
    median=$(echo "$count_line" | grep -oP 'median=\K[0-9]+')
    min=$(echo "$count_line" | grep -oP 'min=\K[0-9]+')
    max=$(echo "$count_line" | grep -oP 'max=\K[0-9]+')

    python3 - <<PYEOF
avg=$avg
median=$median
min=$min
max=$max
print("")
print("========================================")
print("  $name")
print("========================================")
print(f"  Latencia avg:    {avg/1000:.1f} ms")
print(f"  Latencia median: {median/1000:.1f} ms")
print(f"  Latencia min:    {min/1000:.1f} ms")
print(f"  Latencia max:    {max/1000:.1f} ms")
print(f"  FPS (avg):       {1000/(avg/1000):.2f}")
PYEOF
}

echo "=== BENCHMARKS EN ANDROID ==="
echo "Threads: $THREADS | Runs: $RUNS"

# ============================================
# YOLOv8s
# ============================================

run_benchmark "YOLOv8s Float32 - CPU" \
    "yolov8s_float32.tflite" false

run_benchmark "YOLOv8s Float32 - GPU" \
    "yolov8s_float32.tflite" true

run_benchmark "YOLOv8s Float16 - CPU" \
    "yolov8s_float16.tflite" false

run_benchmark "YOLOv8s Float16 - GPU" \
    "yolov8s_float16.tflite" true

# ============================================
# YOLO11n
# ============================================

run_benchmark "YOLO11n Float32 - CPU" \
    "yolo11n_float32.tflite" false

run_benchmark "YOLO11n Float32 - GPU" \
    "yolo11n_float32.tflite" true

run_benchmark "YOLO11n Float16 - CPU" \
    "yolo11n_float16.tflite" false

run_benchmark "YOLO11n Float16 - GPU" \
    "yolo11n_float16.tflite" true

# ============================================
# SSD
# ============================================

run_benchmark "SSD MobileNetV1 - CPU" \
    "ssd_mobilenet_v1.tflite" false

# ============================================
# EfficientDet
# ============================================

run_benchmark "EfficientDet-Lite2 - CPU" \
    "efficientdet-lite2-detection-metadata.tflite" false

run_benchmark "EfficientDet-Lite2 - GPU" \
    "efficientdet-lite2-detection-metadata.tflite" true

echo ""
echo "=== COMPLETADO ==="
