import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import json

from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval

try:
    import tensorflow as tf
    TFLiteInterpreter = tf.lite.Interpreter
except ImportError:
    from tflite_runtime.interpreter import Interpreter as TFLiteInterpreter

# Paths
IMAGE_DIR = "test_images/data/"
RAW_ANNOTATIONS = "test_images/labels.json"

# Update COCO_IDS to only what you annotated
COCO_IDS = {
    1:  "person",
    62: "chair",
    63: "couch",
    65: "bed",
    67: "dining table",
    70: "toilet",
    72: "tv",
    73: "laptop",
    81: "sink",
    82: "refrigerator",
}

# remap roboflow ids to coco ids
ROBOFLOW_TO_COCO = {
    1: 65,  # bed
    2: 62,  # chair
    3:  63,  # couch
    4: 67,  # dining table
    5: 73,  # laptop
    6:  1,   # person
    7: 82,  # refrigerator
    9: 81,  # sink
    9: 70,  # toilet
    10: 72,  # tv
}


# update YOLO_TO_COCO to only include annotated classes
YOLO_TO_COCO = {
    0:  1,   # person
    56: 62,  # chair
    57: 63,  # couch
    59: 65,  # bed
    60: 67,  # dining table
    61: 70,  # toilet
    62: 72,  # tv
    63: 73,  # laptop
    71: 81,  # sink
    72: 82,  # refrigerator
}

with open(RAW_ANNOTATIONS) as f:
    raw_data = json.load(f)

# Build filename -> sequential int ID map
image_files = sorted(
        list(Path(IMAGE_DIR).glob("*.jpg")) + 
        list(Path(IMAGE_DIR).glob("*.jpeg"))
    )
filename_to_id = {p.name: i for i, p in enumerate(image_files)}

# Remap annotations
fixed_images = []
for img in raw_data["images"]:
    fname = img["file_name"]
    if fname in filename_to_id:
        new_img = dict(img)
        new_img["id"] = filename_to_id[fname]
        fixed_images.append(new_img)

fixed_annotations = []
for ann in raw_data["annotations"]:
    # Find original image filename
    orig_img = next((i for i in raw_data["images"] if i["id"] == ann["image_id"]), None)
    if orig_img is None:
        continue
    fname = orig_img["file_name"]
    if fname not in filename_to_id:
        continue
    new_ann = dict(ann)
    new_ann["image_id"] = filename_to_id[fname]
    new_ann["category_id"] = ROBOFLOW_TO_COCO.get(ann["category_id"], ann["category_id"])
    fixed_annotations.append(new_ann)

fixed_categories = [
    {"id": coco_id, "name": name, "supercategory": "indoor"}
    for coco_id, name in COCO_IDS.items()
]

FILTERED_ANNOTATIONS = "/tmp/filtered_labels.json"
with open(FILTERED_ANNOTATIONS, "w") as f:
    json.dump({
        "info": raw_data.get("info", {}),
        "licenses": raw_data.get("licenses", []),
        "categories": fixed_categories,
        "images": fixed_images,
        "annotations": fixed_annotations
    }, f)

print(f"Annotations ready: {len(fixed_images)} images, {len(fixed_annotations)} annotations")

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

def run_yolo_tflite(model_path, image_dir, input_size=640, conf_threshold=0.25, iou_threshold=0.5):

    interpreter = TFLiteInterpreter(model_path=model_path)

    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_dtype = input_details[0]['dtype']

    print( f"{model_path} | " f"input: {input_details[0]['shape']} | " f"dtype: {input_dtype}")

    results_list = []

    yolo_target = set(YOLO_TO_COCO.keys())

    image_paths = sorted(
        list(Path(IMAGE_DIR).glob("*.jpg")) + 
        list(Path(IMAGE_DIR).glob("*.jpeg"))
    )

    for img_path in image_paths:

        img_pil = Image.open(img_path).convert("RGB")

        img_w, img_h = img_pil.size

        # letterbox preprocessing

        img_resized, scale, pad_x, pad_y = letterbox_image(img_pil, input_size)

        input_data = np.array(img_resized)

        if input_dtype in [np.float32, np.float16]:
            input_data = input_data.astype(input_dtype) / 255.0
        else:
            input_data = input_data.astype(input_dtype)

        input_data = np.expand_dims(input_data, axis=0)

        interpreter.set_tensor(input_details[0]['index'], input_data)

        interpreter.invoke()

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
                "image_id": filename_to_id[img_path.name],
                "category_id": coco_cls,
                "bbox": [ float(x), float(y), float(pw), float(ph) ],
                "score": float(filtered_scores[idx])
            })

    return results_list

# ============================================
# SSD / EFFICIENTDET
# ============================================

def run_tflite(model_path, image_dir, conf_threshold=0.3):

    interpreter = TFLiteInterpreter(model_path=model_path)

    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_shape = input_details[0]['shape']

    input_dtype = input_details[0]['dtype']

    height = int(input_shape[1])
    width = int(input_shape[2])

    print(f"{model_path} | " f"input: {input_shape} | " f"dtype: {input_dtype}")

    results_list = []

    image_paths = sorted(
        list(Path(IMAGE_DIR).glob("*.jpg")) + 
        list(Path(IMAGE_DIR).glob("*.jpeg"))
    )

    for img_path in image_paths:

        img_pil = Image.open(img_path).convert("RGB")

        img_w, img_h = img_pil.size

        img_resized = img_pil.resize((width, height))

        input_data = np.array(img_resized, dtype=input_dtype)

        input_data = np.expand_dims(input_data, axis=0)

        interpreter.set_tensor(input_details[0]['index'], input_data)

        interpreter.invoke()

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
                "image_id": filename_to_id[img_path.name],
                "category_id": coco_cls,
                "bbox": [ x, y, w, h ],
                "score": float(score)
            })

    return results_list

# ============================================
# VISUALIZATION
# ============================================

import os

def save_visualizations(results_list, image_dir, model_name, output_dir="visualizations"):
    # group results by image_id
    from collections import defaultdict
    detections_by_image = defaultdict(list)
    for det in results_list:
        detections_by_image[det["image_id"]].append(det)
    
    model_dir = os.path.join(output_dir, model_name.replace(" ", "_"))
    os.makedirs(model_dir, exist_ok=True)

    # color per class
    colors = {
        1:  (200, 200, 200),  # person - light gray
        62: (0, 255, 0),      # chair - green
        63: (0, 200, 100),    # couch - teal
        65: (255, 0, 0),      # bed - red
        67: (0, 0, 255),      # dining table - blue
        70: (255, 128, 0),    # toilet - orange
        72: (128, 0, 255),    # tv - purple
        73: (255, 255, 0),    # laptop - yellow
        81: (0, 255, 255),    # sink - cyan
        82: (255, 0, 255),    # refrigerator - magenta
    }

    image_paths = sorted(
        list(Path(IMAGE_DIR).glob("*.jpg")) + 
        list(Path(IMAGE_DIR).glob("*.jpeg"))
    )

    for img_path in image_paths:
        img_id = filename_to_id[img_path.name]
        img_cv = cv2.imread(str(img_path))

        dets = detections_by_image.get(img_id, [])

        for det in dets:
            x, y, w, h = [int(v) for v in det["bbox"]]
            cat_id = det["category_id"]
            score = det["score"]
            label = COCO_IDS.get(cat_id, str(cat_id))
            color = colors.get(cat_id, (255, 255, 255))

            # draw box
            cv2.rectangle(img_cv, (x, y), (x + w, y + h), color, 2)

            # draw label
            text = f"{label} {score:.2f}"
            cv2.putText(img_cv, text, (x, y - 8),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        out_path = os.path.join(model_dir, img_path.name)
        cv2.imwrite(out_path, img_cv)

    print(f"Saved visualizations for {model_name} -> {model_dir}/")


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
    # Per-class AP at IoU 0.50
    print(f"\nPer-class AP50 for {model_name}:")
    for i, cat_id in enumerate(coco_eval.params.catIds):
        ap = coco_eval.eval['precision'][0, :, i, 0, 2]  # IoU=0.50, all areas, maxDets=100
        ap = ap[ap > -1]
        if len(ap) > 0:
            print(f"  {COCO_IDS[cat_id]:<20} {np.mean(ap):.3f}")
        else:
            print(f"  {COCO_IDS[cat_id]:<20} N/A")

    return (coco_eval.stats[0], coco_eval.stats[1])

# ============================================
# PRECISION / RECALL / F1
# ============================================

def compute_iou(box1, box2):
    # boxes in [x, y, w, h] format
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[0] + box1[2], box2[0] + box2[2])
    y2 = min(box1[1] + box1[3], box2[1] + box2[3])

    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = box1[2] * box1[3]
    area2 = box2[2] * box2[3]
    union = area1 + area2 - inter

    return inter / union if union > 0 else 0.0

def compute_precision_recall_f1(results_list, annotation_file, iou_threshold=0.5):

    from collections import defaultdict

    with open(annotation_file) as f:
        gt_data = json.load(f)

    # group ground truth and detections by image
    gt_by_image = defaultdict(list)
    for ann in gt_data["annotations"]:
        gt_by_image[ann["image_id"]].append(ann)

    det_by_image = defaultdict(list)
    for det in results_list:
        det_by_image[det["image_id"]].append(det)

    tp = fp = fn = 0

    image_ids = set(gt_by_image.keys()) | set(det_by_image.keys())

    for img_id in image_ids:
        gts = gt_by_image.get(img_id, [])
        dets = sorted(det_by_image.get(img_id, []), key=lambda d: -d["score"])
        matched = set()

        for det in dets:
            best_iou = 0.0
            best_idx = -1
            for i, gt in enumerate(gts):
                if i in matched:
                    continue
                if gt["category_id"] != det["category_id"]:
                    continue
                iou = compute_iou(det["bbox"], gt["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_idx = i
            if best_iou >= iou_threshold:
                tp += 1
                matched.add(best_idx)
            else:
                fp += 1

        fn += len(gts) - len(matched)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return precision, recall, f1

# ============================================
# FORMAT RESULTS
# ============================================

def format_results(name, map5095, map50, precision, recall, f1):

    lines = [
        f"{'='*40}",
        f"  {name}",
        f"{'='*40}",
        f"  MAP50:        {map50:.3f}",
        f"  MAP50-95:     {map5095:.3f}",
        f"  Precision:    {precision:.3f}",
        f"  Recall:       {recall:.3f}",
        f"  F1 Score:     {f1:.3f}",
    ]

    return "\n".join(lines)

# ============================================
# RUN EVALUATION
# ============================================
print("=== Evaluando YOLOv8s Float32 TFLite ===")
yolov8_f32_results = run_yolo_tflite("models/yolov8s_float32.tflite", IMAGE_DIR)
print("\n=== Evaluando YOLOv8s Float16 TFLite ===")
yolov8_f16_results = run_yolo_tflite("models/yolov8s_float16.tflite", IMAGE_DIR)
print("\n=== Evaluando YOLO11n Float32 TFLite ===")
yolo11_f32_results = run_yolo_tflite("models/yolo11n_float32.tflite", IMAGE_DIR)
print("\n=== Evaluando YOLO11n Float16 TFLite ===")
yolo11_f16_results = run_yolo_tflite("models/yolo11n_float16.tflite", IMAGE_DIR)
print("\n=== Evaluando SSD MobileNetV1 ===")
ssd_results = run_tflite("models/ssd_mobilenet_v1.tflite", IMAGE_DIR)
print("\n=== Evaluando EfficientDet-Lite2 ===")
eff_results = run_tflite("models/efficientdet-lite2-detection-metadata.tflite", IMAGE_DIR)

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
# VISUALIZATION
# ============================================

print("=== Exporting visualizations ===")

save_visualizations(yolov8_f32_results, IMAGE_DIR, "YOLOv8s_Float32")
save_visualizations(yolov8_f16_results, IMAGE_DIR, "YOLOv8s_Float16")
save_visualizations(yolo11_f32_results, IMAGE_DIR, "YOLO11n_Float32")
save_visualizations(yolo11_f16_results, IMAGE_DIR, "YOLO11n_Float16")
save_visualizations(ssd_results,        IMAGE_DIR, "SSD_MobileNetV1")
save_visualizations(eff_results,        IMAGE_DIR, "EfficientDet_Lite2")

# ============================================
# WRITE RESULTS TO FILE
# ============================================

RESULTS_FILE = "results/desktop.md"

models = [
    ("YOLOv8s Float32",    yolov8_f32_results, map5095_v8_f32,  map50_v8_f32),
    ("YOLOv8s Float16",    yolov8_f16_results, map5095_v8_f16,  map50_v8_f16),
    ("YOLO11n Float32",    yolo11_f32_results, map5095_11_f32,  map50_11_f32),
    ("YOLO11n Float16",    yolo11_f16_results, map5095_11_f16,  map50_11_f16),
    ("SSD MobileNetV1",    ssd_results,        map5095_s,       map50_s),
    ("EfficientDet-Lite2", eff_results,        map5095_e,       map50_e),
]

header = ("* The desktop benchmarks were executed on a system running Arch Linux "
          "with an Intel Core i5-12450H processor, Intel UHD integrated graphics, "
          "and 8 GB RAM. Inference was performed using TensorFlow Lite under "
          "CPU-only execution.\n")

os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)

with open(RESULTS_FILE, "w") as f:
    f.write(header + "\n")
    for name, results, map5095, map50 in models:
        precision, recall, f1 = compute_precision_recall_f1(results, FILTERED_ANNOTATIONS)
        f.write(format_results(name, map5095, map50,
                               precision, recall, f1) + "\n\n")
        print(f"Results written for {name}")

print(f"\nResults saved to {RESULTS_FILE}")
