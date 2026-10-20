"""
Benchmark script to compare panoramic preprocessing methods.

Tests different preprocessing approaches on equirectangular panoramic images
and evaluates their impact on object detection performance.

Two categories of methods:
1. Coordinate-preserving: Keep equirectangular coordinates (annotations valid)
2. Coordinate-transforming: Extract perspective views (need annotation transform)
"""

import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import json
import os
import sys

from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval

try:
    import tensorflow as tf
    TFLiteInterpreter = tf.lite.Interpreter
except ImportError:
    from tflite_runtime.interpreter import Interpreter as TFLiteInterpreter

from panoramic_preprocessing import PanoramicPreprocessor

# ============================================
# CONFIGURATION
# ============================================

IMAGE_DIR = "panoramic/data/"
RAW_ANNOTATIONS = "panoramic/labels.json"
RESULTS_DIR = "results/preprocessing_comparison/"
PREPROCESSED_DIR = "preprocessed_data/"

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

ROBOFLOW_TO_COCO = {
    1: 65, 2: 62, 3: 63, 4: 67, 5: 73,
    6: 1, 7: 82, 8: 81, 9: 70, 10: 72,
}

YOLO_TO_COCO = {
    0: 1, 56: 62, 57: 63, 59: 65, 60: 67,
    61: 70, 62: 72, 63: 73, 71: 81, 72: 82,
}


# ============================================
# SETUP ANNOTATIONS
# ============================================

def setup_annotations():
    """Prepare COCO-format annotations for evaluation."""
    with open(RAW_ANNOTATIONS) as f:
        raw_data = json.load(f)

    image_files = sorted(
        list(Path(IMAGE_DIR).glob("*.jpg")) +
        list(Path(IMAGE_DIR).glob("*.jpeg"))
    )
    filename_to_id = {p.name: i for i, p in enumerate(image_files)}

    fixed_images = []
    for img in raw_data["images"]:
        fname = img["file_name"]
        if fname in filename_to_id:
            new_img = dict(img)
            new_img["id"] = filename_to_id[fname]
            fixed_images.append(new_img)

    fixed_annotations = []
    for ann in raw_data["annotations"]:
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

    filtered_file = "/tmp/filtered_labels_preprocessing.json"
    with open(filtered_file, "w") as f:
        json.dump({
            "info": raw_data.get("info", {}),
            "licenses": raw_data.get("licenses", []),
            "categories": fixed_categories,
            "images": fixed_images,
            "annotations": fixed_annotations
        }, f)

    return filename_to_id, filtered_file


def setup_perspective_annotations(method_key, num_strips=4, fov=90.0):
    """
    Create COCO-format annotations for perspective-transformed images.

    Each original image produces num_strips perspective views.
    Annotations are transformed to match each perspective view.
    """
    with open(RAW_ANNOTATIONS) as f:
        raw_data = json.load(f)

    image_files = sorted(
        list(Path(IMAGE_DIR).glob("*.jpg")) +
        list(Path(IMAGE_DIR).glob("*.jpeg"))
    )

    preprocessor = PanoramicPreprocessor()

    new_images = []
    new_annotations = []
    image_id_counter = 0
    ann_id_counter = 0

    strip_width_deg = 360 / num_strips

    for img_path in image_files:
        img = cv2.imread(str(img_path))
        if img is None:
            continue

        h, w = img.shape[:2]

        # Find annotations for this image
        orig_img_data = next(
            (i for i in raw_data["images"] if i["file_name"] == img_path.name),
            None
        )
        if orig_img_data is None:
            continue

        orig_anns = [
            a for a in raw_data["annotations"] if a["image_id"] == orig_img_data["id"]
        ]

        # Create perspective strips
        for strip_idx in range(num_strips):
            yaw = -180 + (strip_idx + 0.5) * strip_width_deg

            # The preprocessed image file name
            strip_name = f"{method_key}_{strip_idx}_{img_path.name}"

            # Transform annotations to this strip's perspective
            transformed_anns = []
            for ann in orig_anns:
                bbox = ann["bbox"]  # [x, y, w, h]
                new_bbox = preprocessor.transform_bbox_equirect_to_perspective(
                    bbox, w, h, fov, yaw, 0, 640, 640
                )
                if new_bbox is not None:
                    coco_cat = ROBOFLOW_TO_COCO.get(ann["category_id"], ann["category_id"])
                    transformed_anns.append({
                        "id": ann_id_counter,
                        "image_id": image_id_counter,
                        "category_id": coco_cat,
                        "bbox": new_bbox,
                        "area": new_bbox[2] * new_bbox[3],
                        "iscrowd": 0,
                    })
                    ann_id_counter += 1

            new_images.append({
                "id": image_id_counter,
                "file_name": strip_name,
                "width": 640,
                "height": 640,
            })
            new_annotations.extend(transformed_anns)
            image_id_counter += 1

    fixed_categories = [
        {"id": coco_id, "name": name, "supercategory": "indoor"}
        for coco_id, name in COCO_IDS.items()
    ]

    filtered_file = f"/tmp/filtered_labels_{method_key}.json"
    with open(filtered_file, "w") as f:
        json.dump({
            "info": {},
            "licenses": [],
            "categories": fixed_categories,
            "images": new_images,
            "annotations": new_annotations
        }, f)

    # Build filename_to_id mapping
    filename_to_id = {img["file_name"]: img["id"] for img in new_images}

    return filename_to_id, filtered_file


# ============================================
# PREPROCESS IMAGES
# ============================================

def preprocess_images(method: str, output_dir: str, **kwargs):
    """Preprocess all panoramic images using the specified method."""
    os.makedirs(output_dir, exist_ok=True)

    image_paths = sorted(
        list(Path(IMAGE_DIR).glob("*.jpg")) +
        list(Path(IMAGE_DIR).glob("*.jpeg"))
    )

    preprocessor = PanoramicPreprocessor()

    for img_path in image_paths:
        image = cv2.imread(str(img_path))
        if image is None:
            continue

        preprocessor.width = image.shape[1]
        preprocessor.height = image.shape[0]

        processed = preprocessor.preprocess_pipeline(image, method, **kwargs)

        output_path = os.path.join(output_dir, img_path.name)
        cv2.imwrite(output_path, processed)

    print(f"  Preprocessed {len(image_paths)} images -> {output_dir}")


def preprocess_images_perspective_strips(output_dir: str, num_strips: int = 4, fov: float = 90.0,
                                          method_key: str = "strips"):
    """Create perspective strips from all panoramic images."""
    os.makedirs(output_dir, exist_ok=True)

    image_paths = sorted(
        list(Path(IMAGE_DIR).glob("*.jpg")) +
        list(Path(IMAGE_DIR).glob("*.jpeg"))
    )

    preprocessor = PanoramicPreprocessor()
    strip_width_deg = 360 / num_strips

    for img_path in image_paths:
        image = cv2.imread(str(img_path))
        if image is None:
            continue

        h, w = image.shape[:2]
        preprocessor.width = w
        preprocessor.height = h

        for strip_idx in range(num_strips):
            yaw = -180 + (strip_idx + 0.5) * strip_width_deg
            strip = preprocessor.equirectangular_to_perspective(
                image, fov=fov, yaw=yaw, pitch=0, output_size=(640, 640)
            )

            # Use method_key in filename to match annotation setup
            strip_name = f"{method_key}_{strip_idx}_{img_path.name}"
            output_path = os.path.join(output_dir, strip_name)
            cv2.imwrite(output_path, strip)

    print(f"  Created {len(image_paths) * num_strips} perspective strips -> {output_dir}")


# ============================================
# YOLO TFLITE RUNNER
# ============================================

def letterbox_image(image, size=640):
    """Letterbox image for YOLO input."""
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


def run_yolo_tflite(model_path, image_dir, filename_to_id, input_size=640,
                    conf_threshold=0.25, iou_threshold=0.5):
    """Run YOLO TFLite inference on images."""
    interpreter = TFLiteInterpreter(model_path=model_path)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    input_dtype = input_details[0]['dtype']

    print(f"  {model_path.split('/')[-1]} | input: {input_details[0]['shape']} | dtype: {input_dtype}")

    results_list = []
    yolo_target = set(YOLO_TO_COCO.keys())

    image_paths = sorted(
        list(Path(image_dir).glob("*.jpg")) +
        list(Path(image_dir).glob("*.jpeg"))
    )

    for img_path in image_paths:
        if img_path.name not in filename_to_id:
            continue

        img_pil = Image.open(img_path).convert("RGB")
        img_w, img_h = img_pil.size

        img_resized, scale, pad_x, pad_y = letterbox_image(img_pil, input_size)

        input_data = np.array(img_resized)
        if input_dtype in [np.float32, np.float16]:
            input_data = input_data.astype(input_dtype) / 255.0
        else:
            input_data = input_data.astype(input_dtype)

        input_data = np.expand_dims(input_data, axis=0)
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()

        output = interpreter.get_tensor(output_details[0]['index'])[0].T
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
            xc *= input_size
            yc *= input_size
            w *= input_size
            h *= input_size

            x1 = xc - w / 2
            y1 = yc - h / 2
            x1 -= pad_x
            y1 -= pad_y

            x = x1 / scale
            y = y1 / scale
            pw = w / scale
            ph = h / scale

            x = max(0, x)
            y = max(0, y)
            pw = min(pw, img_w - x)
            ph = min(ph, img_h - y)

            filtered_boxes.append([float(x), float(y), float(pw), float(ph)])
            filtered_scores.append(float(confidence))
            filtered_classes.append(yolo_cls)

        indices = cv2.dnn.NMSBoxes(filtered_boxes, filtered_scores, conf_threshold, iou_threshold)

        if len(indices) == 0:
            continue

        for idx in indices.flatten():
            x, y, pw, ph = filtered_boxes[idx]
            coco_cls = YOLO_TO_COCO[filtered_classes[idx]]

            results_list.append({
                "image_id": filename_to_id[img_path.name],
                "category_id": coco_cls,
                "bbox": [float(x), float(y), float(pw), float(ph)],
                "score": float(filtered_scores[idx])
            })

    return results_list


# ============================================
# EVALUATION
# ============================================

def compute_map(results_list, annotation_file, model_name):
    """Compute COCO mAP metrics."""
    coco_gt = COCO(annotation_file)

    if len(results_list) == 0:
        print(f"  WARNING: {model_name} produced 0 detections")
        return 0.0, 0.0

    coco_dt = coco_gt.loadRes(results_list)
    coco_eval = COCOeval(coco_gt, coco_dt, "bbox")
    coco_eval.params.catIds = list(COCO_IDS.keys())
    coco_eval.evaluate()
    coco_eval.accumulate()
    coco_eval.summarize()

    return coco_eval.stats[0], coco_eval.stats[1]


def compute_precision_recall_f1(results_list, annotation_file, iou_threshold=0.5):
    """Compute precision, recall, and F1 score."""
    from collections import defaultdict

    with open(annotation_file) as f:
        gt_data = json.load(f)

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


def compute_iou(box1, box2):
    """Compute IoU between two boxes in [x, y, w, h] format."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[0] + box1[2], box2[0] + box2[2])
    y2 = min(box1[1] + box1[3], box2[1] + box2[3])

    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area1 = box1[2] * box1[3]
    area2 = box2[2] * box2[3]
    union = area1 + area2 - inter

    return inter / union if union > 0 else 0.0


# ============================================
# MAIN BENCHMARK
# ============================================

def run_benchmark():
    """Run preprocessing benchmark comparing different methods."""

    print("=" * 60)
    print("PANORAMIC PREPROCESSING BENCHMARK")
    print("=" * 60)

    # Setup base annotations
    filename_to_id, annotation_file = setup_annotations()

    # Models to test (using Float16 for speed)
    models = [
        ("YOLOv8s Float16", "models/yolov8s_float16.tflite"),
    ]

    # ============================================
    # PART 1: Coordinate-preserving methods
    # (annotations stay valid)
    # ============================================
    print("\n" + "=" * 60)
    print("PART 1: Coordinate-Preserving Methods")
    print("=" * 60)

    coord_preserving_methods = [
        ("none", "No Preprocessing (Baseline)", {}, IMAGE_DIR),
        ("distortion", "Lens Distortion Correction", {}, None),
        ("vignetting", "Vignetting Correction", {"strength": 0.5}, None),
        ("contrast", "CLAHE Contrast Normalization", {}, None),
        ("distortion_vignetting", "Distortion + Vignetting", {}, None),
        ("full", "Full Pipeline (Distortion+Vignetting+Contrast)", {}, None),
    ]

    all_results = {}

    for model_name, model_path in models:
        print(f"\n--- {model_name} ---")
        model_results = {}

        for method_key, method_name, kwargs, fixed_dir in coord_preserving_methods:
            print(f"\n  [{method_name}]")

            if fixed_dir is not None:
                image_dir = fixed_dir
            else:
                output_dir = os.path.join(PREPROCESSED_DIR, method_key)
                preprocess_images(method_key, output_dir, **kwargs)
                image_dir = output_dir

            results = run_yolo_tflite(model_path, image_dir, filename_to_id)
            map5095, map50 = compute_map(results, annotation_file, f"{model_name} - {method_name}")
            precision, recall, f1 = compute_precision_recall_f1(results, annotation_file)

            model_results[method_name] = {
                "map5095": map5095, "map50": map50,
                "precision": precision, "recall": recall, "f1": f1,
                "num_detections": len(results),
            }
            print(f"    mAP50: {map50:.3f} | P: {precision:.3f} | R: {recall:.3f} | F1: {f1:.3f}")

        all_results[model_name] = model_results

    # ============================================
    # PART 2: Perspective strip detection
    # (with annotation transformation)
    # ============================================
    print("\n" + "=" * 60)
    print("PART 2: Perspective Strip Detection")
    print("=" * 60)

    strip_configs = [
        (4, 90.0, "4 strips, 90° FOV"),
        (6, 90.0, "6 strips, 90° FOV"),
        (8, 90.0, "8 strips, 90° FOV"),
        (4, 120.0, "4 strips, 120° FOV"),
    ]

    for model_name, model_path in models:
        if model_name not in all_results:
            all_results[model_name] = {}

        for num_strips, fov, desc in strip_configs:
            method_key = f"strips_{num_strips}_{int(fov)}"
            print(f"\n  [{desc}]")

            # Create perspective strips
            strips_dir = os.path.join(PREPROCESSED_DIR, method_key)
            preprocess_images_perspective_strips(strips_dir, num_strips, fov, method_key)

            # Setup transformed annotations
            strip_filename_to_id, strip_annotation_file = setup_perspective_annotations(
                method_key, num_strips, fov
            )

            # Run inference
            results = run_yolo_tflite(model_path, strips_dir, strip_filename_to_id)
            map5095, map50 = compute_map(results, strip_annotation_file,
                                         f"{model_name} - {desc}")
            precision, recall, f1 = compute_precision_recall_f1(results, strip_annotation_file)

            # Normalize by number of strips (each original image produces num_strips views)
            normalized_results = {
                "map5095": map5095, "map50": map50,
                "precision": precision, "recall": recall, "f1": f1,
                "num_detections": len(results),
                "num_strips": num_strips,
            }
            all_results[model_name][f"Perspective {desc}"] = normalized_results
            print(f"    mAP50: {map50:.3f} | P: {precision:.3f} | R: {recall:.3f} | F1: {f1:.3f}")

    # ============================================
    # SAVE RESULTS
    # ============================================
    os.makedirs(RESULTS_DIR, exist_ok=True)

    report_path = os.path.join(RESULTS_DIR, "preprocessing_comparison.md")
    with open(report_path, "w") as f:
        f.write("# Panoramic Preprocessing Comparison\n\n")
        f.write("Comparing preprocessing methods for equirectangular panoramic object detection.\n\n")

        for model_name, model_results in all_results.items():
            f.write(f"## {model_name}\n\n")
            f.write("| Method | mAP50 | mAP50-95 | Precision | Recall | F1 |\n")
            f.write("|--------|-------|----------|-----------|--------|----|\n")

            for method_name, metrics in model_results.items():
                f.write(f"| {method_name} | {metrics['map50']:.3f} | {metrics['map5095']:.3f} | "
                       f"{metrics['precision']:.3f} | {metrics['recall']:.3f} | {metrics['f1']:.3f} |\n")
            f.write("\n")

    json_path = os.path.join(RESULTS_DIR, "preprocessing_comparison.json")
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for model_name, model_results in all_results.items():
        print(f"\n{model_name}:")
        baseline = model_results.get("No Preprocessing (Baseline)", {})
        baseline_map50 = baseline.get("map50", 0)

        best_method = max(model_results.items(), key=lambda x: x[1]["map50"])
        best_map50 = best_method[1]["map50"]
        improvement = best_map50 - baseline_map50

        print(f"  Baseline mAP50:       {baseline_map50:.3f}")
        print(f"  Best method:         {best_method[0]}")
        print(f"  Best mAP50:          {best_map50:.3f}")
        print(f"  Improvement:         {improvement:+.3f} ({improvement/baseline_map50*100:+.1f}%)" if baseline_map50 > 0 else "")

    print(f"\nResults saved to {report_path}")


if __name__ == "__main__":
    run_benchmark()
