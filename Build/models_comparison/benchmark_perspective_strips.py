"""
Focused benchmark for the perspective-strip approach on equirectangular panoramas.

Converts each equirectangular image into N overlapping perspective views (strips),
runs detection on each, maps detections back, and compares against the baseline
whole-image approach using COCO metrics.
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

IMAGE_DIR = "panoramic/data/"
RAW_ANNOTATIONS = "panoramic/labels.json"
PREPROCESSED_DIR = "preprocessed_data/"

COCO_IDS = {
    1: "person", 62: "chair", 63: "couch", 65: "bed", 67: "dining table",
    70: "toilet", 72: "tv", 73: "laptop", 81: "sink", 82: "refrigerator",
}
ROBOFLOW_TO_COCO = {1: 65, 2: 62, 3: 63, 4: 67, 5: 73, 6: 1, 7: 82, 8: 81, 9: 70, 10: 72}
YOLO_TO_COCO = {0: 1, 56: 62, 57: 63, 59: 65, 60: 67, 61: 70, 62: 72, 63: 73, 71: 81, 72: 82}


def setup_annotations():
    """Baseline COCO annotations keyed to original images."""
    with open(RAW_ANNOTATIONS) as f:
        raw = json.load(f)
    files = sorted(list(Path(IMAGE_DIR).glob("*.jpg")) + list(Path(IMAGE_DIR).glob("*.jpeg")))
    fid = {p.name: i for i, p in enumerate(files)}
    images = []
    for img in raw["images"]:
        if img["file_name"] in fid:
            ni = dict(img); ni["id"] = fid[img["file_name"]]; images.append(ni)
    anns = []
    for a in raw["annotations"]:
        oi = next((i for i in raw["images"] if i["id"] == a["image_id"]), None)
        if oi is None or oi["file_name"] not in fid:
            continue
        na = dict(a); na["image_id"] = fid[oi["file_name"]]
        na["category_id"] = ROBOFLOW_TO_COCO.get(a["category_id"], a["category_id"])
        anns.append(na)
    cats = [{"id": c, "name": n, "supercategory": "indoor"} for c, n in COCO_IDS.items()]
    path = "preprocessed_data/_baseline_labels.json"
    with open(path, "w") as f:
        json.dump({"images": images, "annotations": anns, "categories": cats}, f)
    return fid, path


def build_strip_annotations(num_strips, fov):
    """Build COCO annotations where each strip is its own image, boxes transformed."""
    with open(RAW_ANNOTATIONS) as f:
        raw = json.load(f)
    files = sorted(list(Path(IMAGE_DIR).glob("*.jpg")) + list(Path(IMAGE_DIR).glob("*.jpeg")))
    pp = PanoramicPreprocessor()
    sw = 360 / num_strips
    images, anns, iid, aid = [], [], 0, 0

    for p in files:
        img = cv2.imread(str(p))
        if img is None:
            continue
        h, w = img.shape[:2]
        orig = next((i for i in raw["images"] if i["file_name"] == p.name), None)
        if orig is None:
            continue
        oanns = [a for a in raw["annotations"] if a["image_id"] == orig["id"]]
        for si in range(num_strips):
            yaw = -180 + (si + 0.5) * sw
            name = f"strips_{num_strips}_{int(fov)}_{si}_{p.name}"
            images.append({"id": iid, "file_name": name, "width": 640, "height": 640})
            for a in oanns:
                nb = pp.transform_bbox_equirect_to_perspective(a["bbox"], w, h, fov, yaw, 0, 640, 640)
                if nb:
                    anns.append({"id": aid, "image_id": iid,
                                 "category_id": ROBOFLOW_TO_COCO.get(a["category_id"], a["category_id"]),
                                 "bbox": nb, "area": nb[2]*nb[3], "iscrowd": 0})
                    aid += 1
            iid += 1

    cats = [{"id": c, "name": n, "supercategory": "indoor"} for c, n in COCO_IDS.items()]
    path = f"preprocessed_data/_strips_{num_strips}_{int(fov)}_labels.json"
    with open(path, "w") as f:
        json.dump({"images": images, "annotations": anns, "categories": cats}, f)
    fid = {im["file_name"]: im["id"] for im in images}
    return fid, path


def make_strips(num_strips, fov):
    """Generate perspective strip images into disk."""
    out_dir = os.path.join(PREPROCESSED_DIR, f"strips_{num_strips}_{int(fov)}")
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(list(Path(IMAGE_DIR).glob("*.jpg")) + list(Path(IMAGE_DIR).glob("*.jpeg")))
    pp = PanoramicPreprocessor()
    sw = 360 / num_strips
    for p in files:
        img = cv2.imread(str(p))
        if img is None:
            continue
        h, w = img.shape[:2]
        pp.width, pp.height = w, h
        for si in range(num_strips):
            yaw = -180 + (si + 0.5) * sw
            strip = pp.equirectangular_to_perspective(img, fov=fov, yaw=yaw, pitch=0, output_size=(640, 640))
            cv2.imwrite(os.path.join(out_dir, f"strips_{num_strips}_{int(fov)}_{si}_{p.name}"), strip)
    return out_dir


def letterbox(img, size=640):
    scale = min(size/img.width, size/img.height)
    nw, nh = int(img.width*scale), int(img.height*scale)
    img = img.resize((nw, nh))
    canvas = Image.new("RGB", (size, size), (114, 114, 114))
    canvas.paste(img, ((size-nw)//2, (size-nh)//2))
    return canvas, scale, (size-nw)//2, (size-nh)//2


def run_yolo(model_path, image_dir, fid):
    interpreter = TFLiteInterpreter(model_path=model_path)
    interpreter.allocate_tensors()
    inp = interpreter.get_input_details()[0]
    out_d = interpreter.get_output_details()[0]
    dtype = inp['dtype']
    results = []
    target = set(YOLO_TO_COCO.keys())
    files = sorted(list(Path(image_dir).glob("*.jpg")) + list(Path(image_dir).glob("*.jpeg")))
    for p in files:
        if p.name not in fid:
            continue
        pil = Image.open(p).convert("RGB")
        iw, ih = pil.size
        resized, scale, padx, pady = letterbox(pil)
        data = np.array(resized)
        data = (data.astype(dtype)/255.0) if dtype in (np.float32, np.float16) else data.astype(dtype)
        interpreter.set_tensor(inp['index'], data[None, ...])
        interpreter.invoke()
        out = interpreter.get_tensor(out_d['index'])[0].T
        boxes, scores_all = out[:, :4], out[:, 4:]
        cls = np.argmax(scores_all, 1)
        conf = np.max(scores_all, 1)
        fb, fs, fc = [], [], []
        for i in range(len(conf)):
            if conf[i] < 0.25 or int(cls[i]) not in target:
                continue
            xc, yc, w, h = boxes[i]*640
            x1, y1 = xc-w/2-padx, yc-h/2-pady
            x, y = x1/scale, y1/scale
            pw, ph = w/scale, h/scale
            x, y = max(0, x), max(0, y)
            pw, ph = min(pw, iw-x), min(ph, ih-y)
            fb.append([x, y, pw, ph]); fs.append(conf[i]); fc.append(int(cls[i]))
        idx = cv2.dnn.NMSBoxes(fb, fs, 0.25, 0.5)
        if len(idx) == 0:
            continue
        for j in idx.flatten():
            results.append({"image_id": fid[p.name], "category_id": YOLO_TO_COCO[fc[j]],
                            "bbox": [float(v) for v in fb[j]], "score": float(fs[j])})
    return results


def evaluate(results, ann_file, name):
    gt = COCO(ann_file)
    if not results:
        print(f"  {name}: 0 detections")
        return 0.0, 0.0, 0.0, 0.0, 0.0
    dt = gt.loadRes(results)
    ev = COCOeval(gt, dt, "bbox")
    ev.params.catIds = list(COCO_IDS.keys())
    ev.evaluate(); ev.accumulate(); ev.summarize()
    map50, map5095 = ev.stats[1], ev.stats[0]

    with open(ann_file) as f:
        gd = json.load(f)
    from collections import defaultdict
    g_by_img = defaultdict(list)
    for a in gd["annotations"]:
        g_by_img[a["image_id"]].append(a)
    d_by_img = defaultdict(list)
    for d in results:
        d_by_img[d["image_id"]].append(d)
    tp = fp = fn = 0
    for iid in set(g_by_img) | set(d_by_img):
        gts = g_by_img.get(iid, [])
        dets = sorted(d_by_img.get(iid, []), key=lambda d: -d["score"])
        matched = set()
        for det in dets:
            best, bidx = 0.0, -1
            for i, gt_ in enumerate(gts):
                if i in matched or gt_["category_id"] != det["category_id"]:
                    continue
                b1, b2 = det["bbox"], gt_["bbox"]
                x1, y1 = max(b1[0], b2[0]), max(b1[1], b2[1])
                x2, y2 = min(b1[0]+b1[2], b2[0]+b2[2]), min(b1[1]+b1[3], b2[1]+b2[3])
                inter = max(0, x2-x1)*max(0, y2-y1)
                union = b1[2]*b1[3]+b2[2]*b2[3]-inter
                iou = inter/union if union > 0 else 0
                if iou > best:
                    best, bidx = iou, i
            if best >= 0.5:
                tp += 1; matched.add(bidx)
            else:
                fp += 1
        fn += len(gts) - len(matched)
    prec = tp/(tp+fp) if tp+fp > 0 else 0
    rec = tp/(tp+fn) if tp+fn > 0 else 0
    f1 = 2*prec*rec/(prec+rec) if prec+rec > 0 else 0
    return map50, map5095, prec, rec, f1


def main():
    model = "models/yolov8s_float16.tflite"
    print("=" * 60)
    print("PERSPECTIVE-STRIP BENCHMARK (vs whole-image baseline)")
    print("=" * 60)

    # Baseline
    b_fid, b_ann = setup_annotations()
    print("\n[Baseline: whole equirectangular image]")
    base_res = run_yolo(model, IMAGE_DIR, b_fid)
    b_m50, b_m95, b_p, b_r, b_f1 = evaluate(base_res, b_ann, "Baseline")
    print(f"  Baseline: mAP50={b_m50:.3f} mAP50-95={b_m95:.3f} P={b_p:.3f} R={b_r:.3f} F1={b_f1:.3f}")

    configs = [(4, 90), (6, 90), (8, 90), (4, 120), (3, 120)]
    rows = [("Baseline", b_m50, b_m95, b_p, b_r, b_f1)]

    for num_strips, fov in configs:
        print(f"\n[{num_strips} strips, {fov}° FOV]")
        make_strips(num_strips, fov)
        fid, ann = build_strip_annotations(num_strips, fov)
        res = run_yolo(model, os.path.join(PREPROCESSED_DIR, f"strips_{num_strips}_{fov}"), fid)
        m50, m95, p, r, f1 = evaluate(res, ann, f"{num_strips} strips {fov}")
        rows.append((f"{num_strips} strips {fov}°", m50, m95, p, r, f1))
        print(f"  {num_strips} strips {fov}°: mAP50={m50:.3f} mAP50-95={m95:.3f} P={p:.3f} R={r:.3f} F1={f1:.3f}")

    print("\n" + "=" * 60)
    print("SUMMARY TABLE")
    print("=" * 60)
    print(f"{'Method':<22}{'mAP50':>8}{'mAP50-95':>10}{'P':>7}{'R':>7}{'F1':>7}")
    for name, m50, m95, p, r, f1 in rows:
        print(f"{name:<22}{m50:>8.3f}{m95:>10.3f}{p:>7.3f}{r:>7.3f}{f1:>7.3f}")


if __name__ == "__main__":
    main()
