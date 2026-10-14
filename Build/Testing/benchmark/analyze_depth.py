"""Estimate camera-object distances from GEOMETRY/EXIF and analyse detection recall by depth band.

Distances are ESTIMATES from the pinhole model d = f_px * H_ref / h_px, not measurements:
- f_px comes from the EXIF FocalLengthIn35mmFilm of each photo (1x ~ 25 mm, 0.5x ~ 14 mm).
- H_ref is a fixed reference vertical extent per COCO class; class height uncertainty is
  proportional (~±30%), and partially occluded objects overestimate distance.
Results are therefore reported as exploratory distance bands, not precise distances.
"""
import argparse, csv, json, math
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
from PIL import Image
from evaluate import CONFIGS, ROOT, match, write_csv

OUT = ROOT / 'benchmark/results/android/depth'
# Reference vertical extent (m) of a typically framed instance; approximations by design.
REF_HEIGHT_M = {
    'person': 1.70, 'chair': 0.90, 'couch': 0.85, 'bed': 0.60,
    'dining table': 0.76, 'toilet': 0.78, 'tv': 0.60, 'laptop': 0.25,
    'sink': 0.80, 'refrigerator': 1.75,
}
BANDS = [(0.5, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 4.0), (4.0, 6.0), (6.0, None)]
DIAG_35MM = math.sqrt(36.0 ** 2 + 24.0 ** 2)  # full-frame diagonal in mm
NAMES = [m.replace('_harness', '').capitalize() + ' ' + l for m, l in CONFIGS]


def focal_px(width, height, focal_35mm):
    return focal_35mm * math.sqrt(width ** 2 + height ** 2) / DIAG_35MM if focal_35mm else None


def band_of(distance):
    for j, (lo, hi) in enumerate(BANDS):
        if distance >= lo and (hi is None or distance < hi):
            return j
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('run', type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    gt = json.loads((ROOT / 'labels.json').read_text())
    run = json.loads(a.run.read_text())
    meta = run['metadata']
    images = {i['id']: i for i in gt['images']}
    frames = {f['image_id']: f for f in run['frames']}
    categories = {c['id']: c['name'] for c in gt['categories']}
    if meta['gt_sha256'] != __import__('hashlib').sha256((ROOT / 'labels.json').read_bytes()).hexdigest():
        raise ValueError('Ground truth hash mismatch')
    gts = defaultdict(list)
    for ann in gt['annotations']:
        gts[ann['image_id']].append(ann)

    # EXIF focal lengths (mm, 35 mm equivalent) per photo.
    focal_by_image = {}
    mismatches = []
    for image_id, im in images.items():
        exif = Image.open(ROOT / 'data' / im['file_name']).getexif().get_ifd(34665)
        f35 = exif.get(41989)  # FocalLengthIn35mmFilm
        focal_by_image[image_id] = f35
        expected = 25 if im['lens'] == '1x' else 14
        if f35 != expected:
            mismatches.append(dict(file_name=im['file_name'], manifest_lens=im['lens'], exif_f35=f35))
    if mismatches:
        write_csv(OUT / 'exif_lens_mismatches.csv', mismatches)
    else:
        (OUT / 'exif_lens_mismatches.csv').write_text('file_name,manifest_lens,exif_f35\n')

    # Per-instance rows with estimated distance and match status.
    instances = []  # gt instances
    pred_rows = []
    for mode, threshold, cap in [('detector', meta['confidence'], 15), ('app_output', meta['confidence'], meta['max_objects'])]:
        for image_id, im in images.items():
            f_px = focal_px(im['width'], im['height'], focal_by_image[image_id])
            if f_px is None:
                continue
            preds = sorted([q for q in frames[image_id]['predictions'] if q['score'] >= threshold], key=lambda q: -q['score'])[:cap]
            matches, fp, fn = match(gts[image_id], preds)
            matched_gt = {id(g) for _, g, _ in matches}
            for g in gts[image_id] if gts[image_id] else []:
                d = f_px * REF_HEIGHT_M[categories[g['category_id']]] / g['bbox'][3]
                instances.append(dict(mode=mode, image_id=image_id, capture_group=im['capture_group'], mount=im['mount'], lens=im['lens'],
                                      category=categories[g['category_id']], distance_m=d if d > 0 else None,
                                      band=band_of(d) if d > 0 else None, tp=int(id(g) in matched_gt)))
            for q in fp:
                # Distance estimate for unmatched predictions uses the same pinhole model per class.
                d = f_px * REF_HEIGHT_M[categories[q['category_id']]] / q['bbox'][3]
                j = band_of(d)
                if j is None or d <= 0:
                    continue
                pred_rows.append(dict(mode=mode, capture_group=im['capture_group'], mount=im['mount'], lens=im['lens'],
                                      category=categories[q['category_id']], distance_m=d, band=j))
    write_csv(OUT / 'instance_distances.csv', instances)
    write_csv(OUT / 'false_prediction_distances.csv', pred_rows)

    draws = np.random.default_rng(20261013).integers(0, 33, (10000, 33))
    groups = sorted({im['capture_group'] for im in images.values()})

    def aggregate(mode, mount, lens, band):
        sel = [r for r in instances if r['mode'] == mode and r['band'] == band
               and (mount is None or r['mount'] == mount) and (lens is None or r['lens'] == lens)]
        n, tp = len(sel), sum(r['tp'] for r in sel)
        per_group = [dict(tp=sum(r['tp'] for r in sel if r['capture_group'] == g), gt=sum(r['capture_group'] == g for r in sel)) for g in groups]
        recs = []
        for draw in draws:
            draw_tp = sum(per_group[i]['tp'] for i in draw)
            draw_gt = sum(per_group[i]['gt'] for i in draw)
            if draw_gt:
                recs.append(draw_tp / draw_gt)
        composition = Counter(r['category'] for r in sel)
        top3 = ', '.join(f'{c} {n_share/len(sel):.0%}' for c, n_share in composition.most_common(3)) if sel else ''
        return dict(mode=mode, mount=mount or 'all', lens=lens or 'all', band=band,
                    band_label=band_label(band), gt=n, tp=tp, recall=tp / n if n else None,
                    recall_group_mean=float(np.mean(recs)) if recs and n else None,
                    recall_ci95_low=float(np.percentile(recs, 2.5)) if recs and n else None,
                    recall_ci95_high=float(np.percentile(recs, 97.5)) if recs and n else None,
                    classes=len(composition), composition_top3=top3,
                    mean_est_distance_m=float(np.mean([r['distance_m'] for r in sel])) if n else None)

    def band_label(b):
        lo, hi = BANDS[b]
        return f'{lo:.1f}-{hi:.1f}' if hi is not None else f'{lo:.1f}+'

    rows = []
    for mode in ('detector', 'app_output'):
        for band in range(len(BANDS)):
            rows.append(aggregate(mode, None, None, band))
            for m, l in CONFIGS:
                rows.append(aggregate(mode, m, l, band))
    rows = [r for r in rows if r['gt'] > 0]
    write_csv(OUT / 'depth_bands.csv', rows)

    # Pooled positives per band for the suggested-range summary.
    pooled = [r for r in rows if r['mode'] == 'detector' and r['mount'] == 'all']
    positives = [r for r in pooled if r['gt'] >= 30]
    last_full = max((r['band'] for r in positives if (r['recall'] or 0) >= 0.5), default=None)
    report = ['Detection depth analysis (estimated distances)', '',
        'Pinhole distance estimate: d = f_px * H_ref / h_px.',
        f'f_px from EXIF FocalLengthIn35mmFilm; diagonal-normalised over {DIAG_35MM:.1f} mm.',
        f'Reference heights (m): ' + ', '.join(f'{k} {v:.2f}' for k, v in REF_HEIGHT_M.items()),
        f'Bands: ' + ', '.join(f'{band_label(b)} m' for b in range(len(BANDS))),
        f'Manifest/EXIF lens mismatches: {len(mismatches)} of {len(images)} photos (see exif_lens_mismatches.csv).', '',
        'Detector mode, confidence 0.30, IoU >= 0.50, class match. Bands with < 30 annotated',
        'instances and bands without complete coverage are excluded from the suggested range.', '',
        'Pooled all configurations, by band (pooled uses every instance; group mean and CI are',
        'balanced over the 33 capture groups, so they can move off the pooled value):',
        'band | gt | tp | recall | group-mean recall | 95% CI | top classes']
    for r in pooled:
        report.append(f"{r['band_label']} | {r['gt']} | {r['tp']} | {r['recall']:.1%} | {r['recall_group_mean']:.1%} | [{r['recall_ci95_low']:.1%}, {r['recall_ci95_high']:.1%}] | {r['composition_top3']}")
    report += ['', 'Suggested usable range bands (recall >= 0.5, >= 30 instances, pooled):',
               *([f'  {band_label(last_full)} m and closer'] if last_full is not None else ['  none reaches recall 0.5']), '',
               'All configurations, detector mode:',
               'band | ' + ' | '.join(NAMES)]
    by_band = defaultdict(dict)
    for r in rows:
        if r['mode'] == 'detector' and r['mount'] != 'all':
            by_band[r['band']][f"{r['mount'].replace('_harness', '').capitalize()} {r['lens']}"] = r
    for b in sorted(by_band):
        cells = []
        for name in NAMES:
            r = by_band[b].get(name)
            cells.append('—' if r is None else f'{r["gt"]}/{r["tp"]} ({r["recall"]:.0%})' if r['recall'] is not None else '—')
        report.append(f'{band_label(b)} | ' + ' | '.join(cells))
    report += ['', 'gt/tp per cell shows annotated instances and matches; cells below ~15 instances are unstable.',
               '', 'Limits:',
               '- Distances are single-camera estimates; class reference height uncertainty is proportional (~±30%).',
               '- Recall is not monotone in distance: class mix changes with distance (e.g., bathroom items close,',
               '  chairs and tables far), so each band pools different classes and depth is partly confounded with class.',
               '- Occluded or truncated objects lose visible box height, which overestimates their distance.',
               '- iPhone optics; results do not transfer to other cameras without re-estimating focal length.',
               '- If the estimated range is used as an operating guideline, validate it on new scenes at measured distances.']
    (OUT / 'report.txt').write_text('\n'.join(report) + '\n')
    plot([r for r in rows if r['mode'] == 'detector' and r['mount'] == 'all'], band_label)
    print(OUT)


def plot(pooled, label_fn):
    import os
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'benchmark/.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    xs = [(BANDS[b][0] + (BANDS[b][1] if BANDS[b][1] is not None else BANDS[b][0] + 2)) / 2 for b in range(len(BANDS))]
    xs[0] = 0.75
    pooled = [r for r in pooled if r['recall_group_mean'] is not None]
    fig, ax = plt.subplots(figsize=(7, 4.5), layout='constrained')
    means = [r['recall_group_mean'] for r in pooled]
    yerr = [[max(0, r['recall_group_mean'] - r['recall_ci95_low']) for r in pooled],
            [max(0, r['recall_ci95_high'] - r['recall_group_mean']) for r in pooled]]
    ax.errorbar([xs[r['band']] for r in pooled], means, yerr=yerr,
                marker='o', color='#2575b8', capsize=3, label='Recall agrupado (IC 95% bootstrap)')
    ax.set_xticks(xs, [label_fn(r['band']) for r in pooled])
    ax.set_xlabel('Distancia estimada (m)')
    ax.set_ylabel('Recall (IoU ≥ 0,50, conf 0,30)')
    ax.set_ylim(0, 1)
    ax.grid(alpha=.2)
    ax.legend()
    fig.savefig(OUT / 'depth_recall.png', dpi=180)
    fig.savefig(OUT / 'depth_recall.pdf')
    plt.close(fig)


if __name__ == '__main__':
    main()
