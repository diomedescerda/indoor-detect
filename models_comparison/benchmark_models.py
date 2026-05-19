import time
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import json

from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval

# ============================================
# COCO CATEGORY IDS
# ============================================

COCO_IDS = {
    1: "person",
    62: "chair",
    63: "couch",
    65: "bed",
    67: "dining table",
    70: "toilet",
    72: "tv",
    73: "laptop",
    81: "sink",
    82: "refrigerator"
}

# ============================================
# YOLO CLASS INDEX -> COCO CATEGORY ID
# ============================================

YOLO_TO_COCO = {
    0: 1,    # person
    56: 62,  # chair
    57: 63,  # couch
    59: 65,  # bed
    60: 67,  # dining table
    61: 70,  # toilet
    62: 72,  # tv
    63: 73,  # laptop
    71: 81,  # sink
    72: 82   # refrigerator
}

# ============================================
# PATHS
# ============================================

IMAGE_DIR = "test_images/data/"
ANNOTATIONS = "test_images/labels.json"

# Build filtered annotations with only kept images
kept_ids = {int(p.stem) for p in Path(IMAGE_DIR).glob("*.jpg")}

with open(ANNOTATIONS) as f:
    full_data = json.load(f)

filtered_data = {
    "info": full_data.get("info", {}),
    "licenses": full_data.get("licenses", []),
    "categories": full_data["categories"],
    "images": [img for img in full_data["images"] if img["id"] in kept_ids],
    "annotations": [ann for ann in full_data["annotations"] if ann["image_id"] in kept_ids]
}

FILTERED_ANNOTATIONS = "/tmp/filtered_labels.json"
with open(FILTERED_ANNOTATIONS, "w") as f:
    json.dump(filtered_data, f)

# ============================================
# LETTERBOX
# ============================================

def letterbox_image(image, size=640):

    img_w, img_h = image.size

    scale = min(size / img_w, size / img_h)

    new_w = int(img_w * scale)
    new_h = int(img_h * scale)

    resized = image.resize((new_w, new_h))

    canvas = Image.new("RGB", (size, size), (114, 114, 114))

    pad_x = (size - new_w) // 2
    pad_y = (size - new_h) // 2

    canvas.paste(resized, (pad_x, pad_y))

    return canvas, scale, pad_x, pad_y

# ============================================
# YOLOv8 TFLite
# ============================================

def run_yolo_tflite(model_path, image_dir, input_size=640, conf_threshold=0.25, iou_threshold=0.5):

    import tensorflow as tf

    interpreter = tf.lite.Interpreter(model_path=model_path)

    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_dtype = input_details[0]['dtype']

    print( f"{model_path} | " f"input: {input_details[0]['shape']} | " f"dtype: {input_dtype}")

    results_list = []
    latencies = []

    yolo_target = set(YOLO_TO_COCO.keys())

    image_paths = sorted(Path(image_dir).glob("*.jpg"))

    for img_path in image_paths:

        img_pil = Image.open(img_path).convert("RGB")

        img_w, img_h = img_pil.size

        # ============================================
        # LETTERBOX PREPROCESSING
        # ============================================

        img_resized, scale, pad_x, pad_y = letterbox_image(img_pil, input_size)

        input_data = np.array(img_resized)

        if input_dtype in [np.float32, np.float16]:
            input_data = input_data.astype(input_dtype) / 255.0
        else:
            input_data = input_data.astype(input_dtype)

        input_data = np.expand_dims(input_data, axis=0)

        interpreter.set_tensor(input_details[0]['index'], input_data)

        start = time.time()
        interpreter.invoke()
        latency = (time.time() - start) * 1000
        latencies.append(latency)

        # ============================================
        # OUTPUT
        # shape: [84, 8400]
        # ============================================

        output = interpreter.get_tensor(output_details[0]['index'])[0]
        output = output.T

        boxes_xywh = output[:, :4]
        class_scores = output[:, 4:]

        class_ids = np.argmax(class_scores, axis=1)

        confidences = np.max(class_scores, axis=1)

        filtered_boxes = []
        filtered_scores = []
        filtered_classes = []

        for i in range(len(confidences)):

            confidence = confidences[i]

            if confidence < conf_threshold:
                continue

            yolo_cls = int(class_ids[i])

            if yolo_cls not in yolo_target:
                continue

            xc, yc, w, h = boxes_xywh[i]

            # ============================================
            # NORMALIZED -> INPUT SIZE
            # ============================================

            xc *= input_size
            yc *= input_size
            w *= input_size
            h *= input_size

            # ============================================
            # XYWH -> XYXY
            # ============================================

            x1 = xc - w / 2
            y1 = yc - h / 2

            # ============================================
            # REMOVE LETTERBOX PADDING
            # ============================================

            x1 -= pad_x
            y1 -= pad_y

            # ============================================
            # SCALE BACK TO ORIGINAL IMAGE
            # ============================================

            x = x1 / scale
            y = y1 / scale

            pw = w / scale
            ph = h / scale

            # clip boxes

            x = max(0, x)
            y = max(0, y)

            pw = min(pw, img_w - x)
            ph = min(ph, img_h - y)

            filtered_boxes.append([float(x), float(y), float(pw), float(ph) ])
            filtered_scores.append(float(confidence))
            filtered_classes.append(yolo_cls)

        # ============================================
        # NMS
        # ============================================

        indices = cv2.dnn.NMSBoxes(filtered_boxes, filtered_scores, conf_threshold, iou_threshold)

        if len(indices) == 0:
            continue

        for idx in indices.flatten():

            x, y, pw, ph = filtered_boxes[idx]

            coco_cls = YOLO_TO_COCO[ filtered_classes[idx] ]

            results_list.append({
                "image_id": int(img_path.stem),
                "category_id": coco_cls,
                "bbox": [ float(x), float(y), float(pw), float(ph) ],
                "score": float(filtered_scores[idx])
            })

    return results_list, latencies

# ============================================
# SSD / EFFICIENTDET
# ============================================

def run_tflite(model_path, image_dir, conf_threshold=0.3):

    import tensorflow as tf

    interpreter = tf.lite.Interpreter(model_path=model_path)

    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_shape = input_details[0]['shape']

    input_dtype = input_details[0]['dtype']

    height = int(input_shape[1])
    width = int(input_shape[2])

    print(f"{model_path} | " f"input: {input_shape} | " f"dtype: {input_dtype}")

    results_list = []
    latencies = []

    image_paths = sorted(
        Path(image_dir).glob("*.jpg")
    )

    for img_path in image_paths:

        img_pil = Image.open(img_path).convert("RGB")

        img_w, img_h = img_pil.size

        img_resized = img_pil.resize((width, height))

        input_data = np.array(img_resized, dtype=input_dtype)

        input_data = np.expand_dims(input_data, axis=0)

        interpreter.set_tensor(input_details[0]['index'], input_data)

        start = time.time()
        interpreter.invoke()
        latency = (time.time() - start) * 1000
        latencies.append(latency)

        boxes = interpreter.get_tensor(output_details[0]['index'])[0]

        classes = interpreter.get_tensor(output_details[1]['index'])[0]

        scores = interpreter.get_tensor(output_details[2]['index'])[0]

        for i, score in enumerate(scores):

            if score < conf_threshold:
                continue

            coco_cls = int(classes[i]) + 1

            if coco_cls not in COCO_IDS:
                continue

            ymin, xmin, ymax, xmax = boxes[i]

            x = float(xmin) * img_w
            y = float(ymin) * img_h

            w = float(xmax - xmin) * img_w
            h = float(ymax - ymin) * img_h

            results_list.append({
                "image_id": int(img_path.stem),
                "category_id": coco_cls,
                "bbox": [ x, y, w, h ],
                "score": float(score)
            })

    return results_list, latencies

# ============================================
# COCO EVALUATION
# ============================================

def compute_map(results_list, annotation_file, model_name):

    coco_gt = COCO(annotation_file)

    if len(results_list) == 0:

        print(f"WARNING: {model_name} " f"produced 0 detections")

        return 0.0, 0.0

    print(f"{model_name}: " f"{len(results_list)} detections")

    coco_dt = coco_gt.loadRes(results_list)

    coco_eval = COCOeval(coco_gt, coco_dt, "bbox")

    coco_eval.params.catIds = list(COCO_IDS.keys())

    coco_eval.evaluate()
    coco_eval.accumulate()
    coco_eval.summarize()

    return (coco_eval.stats[0], coco_eval.stats[1])

# ============================================
# PRINT RESULTS
# ============================================

def print_results(name, latencies, map5095, map50):

    fps = 1000 / np.mean(latencies)

    print(f"\n{'='*40}")
    print(f"  {name}")
    print(f"{'='*40}")
    print(f"  MAP50:        {map50:.3f}")
    print(f"  MAP50-95:     {map5095:.3f}")
    print(f"  FPS:          {fps:.2f}")
    print(f"  Latencia avg: " f"{np.mean(latencies):.1f} ms")
    print(f"  Latencia min: " f"{np.min(latencies):.1f} ms")
    print(f"  Latencia max: " f"{np.max(latencies):.1f} ms")

# ============================================
# RUN EVALUATION
# ============================================
print("=== Evaluando YOLOv8s Float32 TFLite ===")
yolov8_f32_results, yolov8_f32_lat = run_yolo_tflite("models/yolov8s_float32.tflite", IMAGE_DIR)
print("\n=== Evaluando YOLOv8s Float16 TFLite ===")
yolov8_f16_results, yolov8_f16_lat = run_yolo_tflite("models/yolov8s_float16.tflite", IMAGE_DIR)
print("\n=== Evaluando YOLO11n Float32 TFLite ===")
yolo11_f32_results, yolo11_f32_lat = run_yolo_tflite("models/yolo11n_float32.tflite", IMAGE_DIR)
print("\n=== Evaluando YOLO11n Float16 TFLite ===")
yolo11_f16_results, yolo11_f16_lat = run_yolo_tflite("models/yolo11n_float16.tflite", IMAGE_DIR)
print("\n=== Evaluando SSD MobileNetV1 ===")
ssd_results, ssd_lat = run_tflite("models/ssd_mobilenet_v1.tflite", IMAGE_DIR)
print("\n=== Evaluando EfficientDet-Lite2 ===")
eff_results, eff_lat = run_tflite("models/efficientdet-lite2-detection-metadata.tflite", IMAGE_DIR)

# ============================================
# CALCULAR MAP
# ============================================

print("\n=== Calculando MAP ===")

map5095_v8_f32, map50_v8_f32 = compute_map(yolov8_f32_results, FILTERED_ANNOTATIONS, "YOLOv8s Float32")
map5095_v8_f16, map50_v8_f16 = compute_map(yolov8_f16_results, FILTERED_ANNOTATIONS, "YOLOv8s Float16")
map5095_11_f32, map50_11_f32 = compute_map(yolo11_f32_results, FILTERED_ANNOTATIONS, "YOLO11n Float32")
map5095_11_f16, map50_11_f16 = compute_map(yolo11_f16_results, FILTERED_ANNOTATIONS, "YOLO11n Float16")
map5095_s, map50_s = compute_map(ssd_results, FILTERED_ANNOTATIONS, "SSD MobileNetV1")
map5095_e, map50_e = compute_map(eff_results, FILTERED_ANNOTATIONS, "EfficientDet-Lite2")

# ============================================
# PRINT RESULTS
# ============================================

print_results("YOLOv8s Float32", yolov8_f32_lat, map5095_v8_f32, map50_v8_f32)
print_results("YOLOv8s Float16", yolov8_f16_lat, map5095_v8_f16, map50_v8_f16)
print_results("YOLO11n Float32", yolo11_f32_lat, map5095_11_f32, map50_11_f32)
print_results("YOLO11n Float16", yolo11_f16_lat, map5095_11_f16, map50_11_f16)
print_results("SSD MobileNetV1", ssd_lat, map5095_s, map50_s)
print_results("EfficientDet-Lite2", eff_lat, map5095_e, map50_e)
