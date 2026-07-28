#!/bin/bash

BENCHMARK=/data/local/tmp/android_benchmark
MODELS_DIR=/data/local/tmp
THREADS=4
RUNS=50

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_FILE="$SCRIPT_DIR/results/android.md"

mkdir -p "$SCRIPT_DIR/results"

cat > "$RESULTS_FILE" <<EOF
* The Android benchmarks were executed on a Redmi Note 13 equipped with a Qualcomm Snapdragon 685 Octa-core Max 2.80GHz, Adreno 610 GPU, 8 GB RAM, and Android 15.

Threads: $THREADS | Runs: $RUNS
EOF

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
            --enable_memory_profiling=true \
            --use_gpu=true 2>&1)
    else
        result=$(adb shell $BENCHMARK \
            --graph=$MODELS_DIR/$model \
            --num_threads=$THREADS \
            --num_runs=$RUNS \
            --enable_memory_profiling=true 2>&1)
    fi

    echo "$result" > "/tmp/gpu_debug_${model}.log"

    inference_line=$(echo "$result" | grep "Inference timings")
    count_line=$(echo "$result" | grep "count=$RUNS")
    memory_line=$(echo "$result" | grep "Memory footprint delta")

    init=$(echo "$inference_line" | grep -oP 'Init: \K[0-9]+')
    avg=$(echo "$inference_line" | grep -oP 'Inference \(avg\): \K[0-9]+')
    median=$(echo "$count_line" | grep -oP 'median=\K[0-9]+')
    min=$(echo "$count_line" | grep -oP 'min=\K[0-9]+')
    max=$(echo "$count_line" | grep -oP 'max=\K[0-9]+')
    ram=$(echo "$memory_line" | grep -oP 'overall=\K[0-9.]+')

    init=${init:-0}
    avg=${avg:-0}
    median=${median:-0}
    min=${min:-0}
    max=${max:-0}
    ram=${ram:-0}

    python3 - <<PYEOF >> "$RESULTS_FILE"
avg=$avg
median=$median
min=$min
max=$max
init=$init
ram=$ram
fps = 1000/(avg/1000) if avg > 0 else 0
print("")
print("========================================")
print("  $name")
print("========================================")
print(f"  Init time:       {init/1000:.1f} ms")
print(f"  RAM usage:       {ram:.1f} MB")
print(f"  Latencia avg:    {avg/1000:.1f} ms")
print(f"  Latencia median: {median/1000:.1f} ms")
print(f"  Latencia min:    {min/1000:.1f} ms")
print(f"  Latencia max:    {max/1000:.1f} ms")
print(f"  FPS (avg):       {fps:.2f}")
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
echo "Resultados guardados en $RESULTS_FILE"
