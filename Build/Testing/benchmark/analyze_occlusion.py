"""Explore recall by visually assigned occlusion on the existing COCO instances.

Labels are supplemental AI judgments, never changes to labels.json. All annotations
must be labeled once. Output remains provisional until an independent human review.
Matching reuses evaluate.match (class-aware, greedy score order, IoU >= .50).
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from evaluate import CONFIGS, ROOT, match

SEVERITIES = ('none', 'partial', 'heavy')
LEVELS = (*SEVERITIES, 'uncertain')
CONFIDENCES = ('high', 'medium', 'low')
SEED = 20261013
DRAWS = 10000
DEFAULT_LABELS = ROOT / 'occlusion'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_labels(paths, annotations):
    """Reject incomplete, duplicate, unknown or malformed labels; no imputation."""
    expected = {ann['id']: ann for ann in annotations}
    if len(expected) != len(annotations):
        raise ValueError('Duplicate annotation IDs in ground truth')
    labels = {}
    for path in paths:
        data = json.loads(Path(path).read_text())
        records = data.get('annotations', data.get('records')) if isinstance(data, dict) else data
        if not isinstance(records, list):
            raise ValueError(f'{path}: expected a JSON array or object with annotations array')
        for record in records:
            if not isinstance(record, dict):
                raise ValueError(f'{path}: label must be an object')
            annotation_id = record.get('annotation_id')
            if type(annotation_id) is not int or annotation_id not in expected:
                raise ValueError(f'{path}: unknown annotation_id {annotation_id!r}')
            if annotation_id in labels:
                raise ValueError(f'Duplicate label for annotation {annotation_id}')
            if type(record.get('image_id')) is not int or record['image_id'] != expected[annotation_id]['image_id']:
                raise ValueError(f'Annotation {annotation_id}: image_id mismatch')
            if record.get('occlusion') not in LEVELS:
                raise ValueError(f'Annotation {annotation_id}: invalid occlusion')
            if type(record.get('truncation')) is not bool:
                raise ValueError(f'Annotation {annotation_id}: truncation must be boolean')
            if record.get('confidence') not in CONFIDENCES:
                raise ValueError(f'Annotation {annotation_id}: invalid confidence')
            if not isinstance(record.get('reason'), str) or not record['reason'].strip():
                raise ValueError(f'Annotation {annotation_id}: nonempty reason required')
            if 'human_reviewed' in record and type(record['human_reviewed']) is not bool:
                raise ValueError(f'Annotation {annotation_id}: human_reviewed must be boolean')
            # Preserve author review markers and initial AI labels in reviewed exports.
            labels[annotation_id] = dict(record)
    missing = sorted(set(expected) - set(labels))
    if missing:
        raise ValueError(f'Missing {len(missing)} occlusion labels; first IDs: {missing[:20]}')
    return labels


def verify_batch_sources(documents, gt_hash, photo_hashes):
    """Verify any source hashes supplied by inspectors against frozen inputs."""
    for path, document in documents.items():
        if not isinstance(document, dict):
            continue
        sources = document.get('source_hashes', {})
        if sources.get('labels.json', document.get('source_labels_sha256', gt_hash)) != gt_hash:
            raise ValueError(f'{path}: inspector ground truth hash mismatch')
        for file_name, digest in sources.get('images', document.get('source_images_sha256', {})).items():
            if file_name not in photo_hashes or photo_hashes[file_name] != digest:
                raise ValueError(f'{path}: inspector photo hash mismatch for {file_name}')


def area_stratum(fraction):
    """Prespecified bbox area / full image area; not COCO pixel-area bins."""
    if not math.isfinite(fraction) or fraction < 0:
        raise ValueError('Invalid bbox area fraction')
    return 'small' if fraction < .01 else 'medium' if fraction < .10 else 'large'


def validate_sources(gt, run, gt_path):
    if run['metadata']['gt_sha256'] != sha256(gt_path):
        raise ValueError('Ground truth hash mismatch with prediction run')
    images = {image['id']: image for image in gt['images']}
    frames = {frame['image_id']: frame for frame in run['frames']}
    if len(images) != len(gt['images']) or len(frames) != len(run['frames']) or set(frames) != set(images):
        raise ValueError('Duplicate or incomplete image/frame IDs')
    if len(images) != 198 or len(gt['annotations']) != 889:
        raise ValueError('Expected the frozen 198-image / 889-instance dataset')
    groups = sorted({image['capture_group'] for image in images.values()})
    if len(groups) != 33 or any(sum(image['capture_group'] == group and
        (image['mount'], image['lens']) == config for image in images.values()) != 1
        for group in groups for config in CONFIGS):
        raise ValueError('Expected 33 complete six-configuration capture groups')
    categories = {category['id']: category['name'] for category in gt['categories']}
    for image_id, image in images.items():
        if frames[image_id]['file_name'] != image['file_name']:
            raise ValueError(f'Image {image_id}: filename mismatch')
        if image['width'] <= 0 or image['height'] <= 0:
            raise ValueError('Invalid image dimensions')
        for pred in frames[image_id]['predictions']:
            if pred['image_id'] != image_id or pred['category_id'] not in categories:
                raise ValueError('Invalid prediction image/category')
            if not 0 <= pred['score'] <= 1 or len(pred['bbox']) != 4 or not all(math.isfinite(v) for v in pred['bbox']) or min(pred['bbox'][2:]) < 0:
                raise ValueError('Invalid prediction score/bbox')
    for ann in gt['annotations']:
        if ann['image_id'] not in images or ann['category_id'] not in categories:
            raise ValueError('Invalid annotation image/category')
        if len(ann['bbox']) != 4 or not all(math.isfinite(v) for v in ann['bbox']) or min(ann['bbox'][2:]) < 0 or ann.get('iscrowd', 0):
            raise ValueError('Invalid or unsupported crowd annotation')
    meta = run['metadata']
    if meta['confidence'] != .30 or meta['max_objects'] != 2 or meta.get('detector_cap', 15) != 15:
        raise ValueError('Expected confidence .30, detector cap 15, app cap 2')
    return images, frames, categories, groups


def build_instances(gt, run, labels):
    images = {image['id']: image for image in gt['images']}
    frames = {frame['image_id']: frame for frame in run['frames']}
    categories = {category['id']: category['name'] for category in gt['categories']}
    annotations = defaultdict(list)
    for ann in gt['annotations']:
        annotations[ann['image_id']].append(ann)
    instances, matching_totals = [], []
    for mode, cap in (('detector', 15), ('app_output', 2)):
        for image_id, image in images.items():
            preds = sorted((pred for pred in frames[image_id]['predictions'] if pred['score'] >= .30), key=lambda pred: -pred['score'])[:cap]
            matched, fp, fn = match(annotations[image_id], preds)
            matched_ids = {ann['id'] for _, ann, _ in matched}
            matching_totals.append(dict(mode=mode, image_id=image_id, capture_group=image['capture_group'],
                                        gt=len(annotations[image_id]), tp=len(matched), fn=len(fn), fp=len(fp)))
            for ann in annotations[image_id]:
                fraction = ann['bbox'][2] * ann['bbox'][3] / (image['width'] * image['height'])
                label = labels[ann['id']]
                tp = int(ann['id'] in matched_ids)
                instances.append(dict(mode=mode, annotation_id=ann['id'], image_id=image_id,
                    file_name=image['file_name'], capture_group=image['capture_group'], mount=image['mount'], lens=image['lens'],
                    category_id=ann['category_id'], category=categories[ann['category_id']],
                    bbox_x=ann['bbox'][0], bbox_y=ann['bbox'][1], bbox_width=ann['bbox'][2], bbox_height=ann['bbox'][3],
                    bbox_area_fraction=fraction, area_stratum=area_stratum(fraction),
                    occlusion=label['occlusion'], truncation=label['truncation'], confidence=label['confidence'],
                    reason=label['reason'], human_reviewed=label.get('human_reviewed', False),
                    human_reviewed_at=label.get('human_reviewed_at', ''), tp=tp, fn=1-tp))
    return instances, matching_totals


def summarize(rows, groups, draws):
    """Pooled instance recall with whole capture-group percentile bootstrap."""
    counts = {group: [0, 0] for group in groups}
    for row in rows:
        counts[row['capture_group']][0] += row['tp']
        counts[row['capture_group']][1] += 1
    grouped = np.array([counts[group] for group in groups], dtype=np.int64)
    sample = grouped[draws].sum(axis=1)
    valid = sample[:, 1] > 0
    recalls = sample[valid, 0] / sample[valid, 1]
    gt, tp = len(rows), sum(row['tp'] for row in rows)
    return dict(gt=gt, tp=tp, fn=gt-tp, recall=tp/gt if gt else None,
        recall_ci95_low=float(np.percentile(recalls, 2.5)) if len(recalls) else None,
        recall_ci95_high=float(np.percentile(recalls, 97.5)) if len(recalls) else None,
        bootstrap_valid_draws=int(valid.sum()), capture_groups_with_gt=sum(value[1] > 0 for value in counts.values()),
        uncertain_gt=sum(row['occlusion'] == 'uncertain' for row in rows),
        low_confidence_gt=sum(row['confidence'] == 'low' for row in rows),
        sparse_stratum=gt < 15)


def make_summaries(instances, groups, draws):
    results = {name: [] for name in ('severity', 'uncertainty', 'by_class', 'by_area', 'truncation', 'by_configuration', 'label_confidence', 'sensitivity', 'by_class_area')}
    categories = sorted({row['category'] for row in instances})
    for mode in ('detector', 'app_output'):
        pool = [row for row in instances if row['mode'] == mode]
        known = [row for row in pool if row['occlusion'] in SEVERITIES]
        def add(table, rows, **keys):
            results[table].append(dict(mode=mode, **keys, **summarize(rows, groups, draws)))
        for level in SEVERITIES:
            severity = [row for row in known if row['occlusion'] == level]
            add('severity', severity, occlusion=level)
            for sensitivity, selected in (
                ('nontruncated', [row for row in severity if not row['truncation']]),
                ('high_confidence', [row for row in severity if row['confidence'] == 'high']),
                ('high_confidence_nontruncated', [row for row in severity if row['confidence'] == 'high' and not row['truncation']])):
                add('sensitivity', selected, occlusion=level, sensitivity=sensitivity)
            for category in categories:
                class_rows = [row for row in severity if row['category'] == category]
                add('by_class', class_rows, occlusion=level, category=category)
                for size in ('small', 'medium', 'large'):
                    add('by_class_area', [row for row in class_rows if row['area_stratum'] == size],
                        occlusion=level, category=category, area_stratum=size)
            for size in ('small', 'medium', 'large'):
                add('by_area', [row for row in severity if row['area_stratum'] == size], occlusion=level, area_stratum=size)
            for mount, lens in CONFIGS:
                add('by_configuration', [row for row in severity if row['mount'] == mount and row['lens'] == lens], occlusion=level, mount=mount, lens=lens)
        add('uncertainty', [row for row in pool if row['occlusion'] == 'uncertain'], occlusion='uncertain')
        for truncated in (False, True):
            # Overall and severity-specific truncation rows keep the two concepts separate.
            for level in ('all_annotated', *LEVELS):
                add('truncation', [row for row in pool if row['truncation'] == truncated and
                    (level == 'all_annotated' or row['occlusion'] == level)], occlusion=level, truncation=truncated)
        for confidence in CONFIDENCES:
            add('label_confidence', [row for row in pool if row['confidence'] == confidence], confidence=confidence)
    return results


def review_rows(instances):
    rows = []
    for row in instances:
        if row['mode'] != 'detector':
            continue
        reviewed = row.get('human_reviewed', False)
        flags = [] if reviewed else ['human_review_pending']
        if row['occlusion'] == 'uncertain': flags.append('uncertain_occlusion')
        if row['confidence'] != 'high': flags.append(f"{row['confidence']}_confidence")
        if row['occlusion'] == 'heavy': flags.append('heavy_occlusion')
        if row['truncation']: flags.append('frame_truncation')
        rows.append({**{key: value for key, value in row.items() if key not in ('mode', 'tp', 'fn')},
                     'human_review_status': 'author_reviewed' if reviewed else 'pending',
                     'independent_review_status': 'pending',
                     'review_priority': 'high' if any(flag != 'human_review_pending' for flag in flags) else 'normal',
                     'review_flags': ';'.join(flags)})
    return rows


def write_csv(path, rows):
    if not rows:
        raise ValueError(f'Cannot write empty table {path}')
    with Path(path).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path, nargs='?', default=ROOT/'benchmark/results/android.json')
    parser.add_argument('--ground-truth', type=Path, default=ROOT/'labels.json')
    parser.add_argument('--labels-dir', type=Path, default=DEFAULT_LABELS)
    parser.add_argument('--labels', type=Path, help='Complete author-reviewed JSON export; original batch hashes are retained')
    parser.add_argument('--output', type=Path, default=DEFAULT_LABELS/'results')
    args = parser.parse_args()
    if args.labels is None and (args.labels_dir/'author_review.json').is_file():
        args.labels = args.labels_dir/'author_review.json'
    label_paths = sorted(args.labels_dir.glob('labels_batch_*.json'))
    if not label_paths and args.labels is None:
        raise ValueError(f'No labels_batch_*.json files in {args.labels_dir}')
    gt = json.loads(args.ground_truth.read_text())
    run = json.loads(args.run.read_text())
    images, frames, categories, groups = validate_sources(gt, run, args.ground_truth)
    active_paths = [args.labels] if args.labels is not None else label_paths
    labels = read_labels(active_paths, gt['annotations'])
    instances, matching_totals = build_instances(gt, run, labels)
    draws = np.random.default_rng(SEED).integers(0, len(groups), size=(DRAWS, len(groups)))
    tables = make_summaries(instances, groups, draws)
    reviews = review_rows(instances)
    paths = [args.ground_truth, args.run, Path(__file__), Path(__file__).with_name('evaluate.py'), *label_paths, *active_paths]
    source_hashes = {str(path.resolve()): sha256(path) for path in paths}
    photo_hashes = {image['file_name']: sha256(ROOT/'data'/image['file_name']) for image in images.values()}
    batch_documents = {str(path.resolve()): json.loads(path.read_text()) for path in label_paths}
    verify_batch_sources(batch_documents, sha256(args.ground_truth), photo_hashes)
    batch_metadata = {path: {key: value for key, value in document.items()
                            if key in ('schema_version', 'reviewer_model', 'reasoning_effort', 'status', 'image_review', 'empty_image_review', 'method')}
                      for path, document in batch_documents.items() if isinstance(document, dict)}
    reviewed_count = sum(label.get('human_reviewed', False) for label in labels.values())
    status = ('ai_labels_author_reviewed_independent_review_pending' if reviewed_count == len(labels)
              else 'provisional_ai_labels_partial_author_review_pending' if reviewed_count
              else 'provisional_ai_labels_human_review_pending')
    input_document = json.loads(args.labels.read_text()) if args.labels is not None else {}
    inherited_sources = input_document.get('metadata', {}).get('source_hashes', {}) if isinstance(input_document, dict) else {}
    metadata = dict(status=status, human_review_status='author_review_complete' if reviewed_count == len(labels) else 'author_review_partial' if reviewed_count else 'pending',
        independent_human_review_status='pending', author_reviewed_count=reviewed_count,
        initial_ai_batch_sources={str(path.resolve()): sha256(path) for path in label_paths},
        initial_ai_batch_metadata=batch_metadata,
        inherited_source_hashes=inherited_sources,
        label_origin='AI visual inspection of existing photographs, with author review markers when present', labels_complete=True,
        sensitivity_analyses=['nontruncated', 'high_confidence', 'high_confidence_nontruncated'],
        images=len(images), annotations=len(labels), capture_groups=len(groups), new_captures=0,
        modes={'detector': {'confidence': .30, 'cap': 15}, 'app_output': {'confidence': .30, 'cap': 2}},
        matcher='evaluate.match', match_iou=.50, match_class_required=True,
        severity_levels=list(SEVERITIES), uncertainty_excluded_from_main_severity=True,
        area_strata={'small': '[0, 0.01)', 'medium': '[0.01, 0.10)', 'large': '[0.10, infinity)'},
        area_definition='COCO bbox width * height / full image width * height',
        bootstrap={'unit': 'whole capture_group, all six configurations retained', 'draws': DRAWS, 'seed': SEED,
                   'interval': 'percentile 95%', 'zero_denominator_draws': 'excluded and counted'},
        false_positives='No occlusion assigned: predictions have no GT visibility label',
        source_hashes=source_hashes, photo_sha256=photo_hashes, prediction_metadata=run['metadata'],
        label_counts=dict(Counter(label['occlusion'] for label in labels.values())),
        review_priority_counts=dict(Counter(row['review_priority'] for row in reviews)),
        limitations=[
            'Labels began as AI judgments; author review markers are preserved, and independent human validation remains pending.',
            'Occlusion describes obstruction by another object; frame truncation is recorded separately.',
            'Severity is a qualitative visible-instance judgment, not a measured hidden-area percentage.',
            'Class and apparent box size can confound severity associations; stratified tables are descriptive.',
            'Boxes use the existing annotation extent; area is not full hidden-object area.',
            'Bootstrap intervals cover capture-group variability only, not labeling/model uncertainty.',
            'Capture groups follow provisional filename ordering and may share rooms; intervals may be optimistic.',
            'Recall describes existing annotated GT instances; fully hidden, unannotated and out-of-frame targets are excluded.',
            'No cross-image instance identity is available; associations do not establish a causal occlusion effect.',
            'Android predictions replay iPhone photos on an emulator; this does not test live camera or speech performance.'
        ])
    # Only write after complete labels and source integrity checks succeed.
    args.output.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        write_csv(args.output/f'{name}.csv', rows)
    write_csv(args.output/'per_instance.csv', instances)
    write_csv(args.output/'matching_per_image.csv', matching_totals)
    write_csv(args.output/'human_review.csv', reviews)
    (args.output/'labels.json').write_text(json.dumps({'status': metadata['status'], 'metadata': metadata, 'annotations': [labels[key] for key in sorted(labels)]}, indent=2, allow_nan=False)+'\n')
    (args.output/'metrics.json').write_text(json.dumps({'metadata': metadata, **tables}, indent=2, allow_nan=False)+'\n')
    print(args.output)


if __name__ == '__main__':
    main()
