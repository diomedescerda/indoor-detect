"""Compare paired capture groups by visible and correctly detected object counts."""
import csv
import json
import os
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from evaluate import CONFIGS, ROOT, match, write_csv

OUT = ROOT / 'benchmark/results/android/scenes'
NAMES = [m.replace('_harness', '').capitalize() + ' ' + l for m, l in CONFIGS]


def main():
    OUT.mkdir(exist_ok=True)
    rows = list(csv.DictReader((OUT.parent / 'per_image.csv').open()))
    for r in rows:
        for k in ('capture_group', 'image_id', 'gt', 'tp', 'fp', 'fn', 'predictions'):
            r[k] = int(r[k])
    lookup = {(r['mode'], r['capture_group'], r['mount'], r['lens']): r for r in rows}
    assert len(lookup) == 396
    draws = np.random.default_rng(20261013).integers(0, 33, (10000, 33))
    comparisons = []
    for mode in ('detector', 'app_output'):
        for mount, lens in CONFIGS[:-1]:
            a = [lookup[mode, s, 'gorillapod', '0.5x'] for s in range(1, 34)]
            b = [lookup[mode, s, mount, lens] for s in range(1, 34)]
            for metric in ('gt', 'tp', 'fp', 'fn'):
                d = np.array([x[metric] - y[metric] for x, y in zip(a, b)])
                low, high = np.percentile(d[draws].mean(axis=1), [2.5, 97.5])
                comparisons.append(dict(mode=mode, metric=metric,
                    configuration_a='gorillapod/0.5x', configuration_b=f'{mount}/{lens}',
                    total_difference=int(d.sum()), mean_difference=float(d.mean()),
                    ci95_low=float(low), ci95_high=float(high),
                    scenes_a_greater=int((d > 0).sum()), scenes_tied=int((d == 0).sum()),
                    scenes_a_lower=int((d < 0).sum())))
    write_csv(OUT / 'paired_count_differences.csv', comparisons)
    write_csv(OUT / 'scene_counts.csv', rows)
    summary = []
    for mode in ('detector', 'app_output'):
        for c, name in zip(CONFIGS, NAMES):
            rr = [lookup[mode, s, *c] for s in range(1, 34)]
            best = [max(lookup[mode, s, *cc]['tp'] for cc in CONFIGS) for s in range(1, 34)]
            summary.append(dict(mode=mode, configuration=name,
                **{k:sum(r[k] for r in rr) for k in ('gt','tp','fp','fn')},
                mean_tp_per_scene=sum(r['tp'] for r in rr)/33,
                scenes_with_correct_detection=sum(r['tp']>0 for r in rr),
                scenes_at_best_nonzero_count=sum(r['tp']==v and v>0 for r,v in zip(rr,best)),
                scenes_without_annotated_objects=sum(r['gt']==0 for r in rr)))
    write_csv(OUT / 'count_summary.csv', summary)
    report(lookup, comparisons, summary)
    plots(lookup)
    sheets(lookup)
    print(OUT)


def report(lookup, comparisons, summary):
    lines = ['Paired scene comparison: object coverage and detection counts', '',
        '198 reviewed photos, arranged into 33 consecutive six-photo capture groups.',
        'Same Android predictions: confidence 0.30, class match and IoU >= 0.50.',
        'No inference rerun or annotation changes; the analysis objective is now object count.', '',
        'VISIBLE = reviewed objects inside this photo (GT). CORRECT = matched detections (TP).',
        'MISSED = annotated objects in the photo without a match (FN). FALSE = unmatched predictions (FP).',
        'An object outside the frame is not a detector false negative. Comparing VISIBLE counts',
        'describes observed coverage, but without cross-photo instance identities cannot tell exactly',
        'which unique objects each setup adds or leaves out. Counts cover only the ten target classes.', '',
        'Totals across 33 scenes per configuration:',
        'mode | configuration | visible | correct | false | missed | correct/scene | scenes with correct | best count (ties included)']
    for r in summary:
        lines.append(f"{r['mode']} | {r['configuration']} | {r['gt']} | {r['tp']} | {r['fp']} | {r['fn']} | {r['mean_tp_per_scene']:.2f} | {r['scenes_with_correct_detection']}/33 | {r['scenes_at_best_nonzero_count']}/33")
    lines += ['', 'Gorillapod 0.5x versus each alternative: correct-object counts',
        'mode | alternative | more/tied/fewer scenes | total difference | mean difference and paired 95% interval']
    for r in comparisons:
        if r['metric'] == 'tp':
            lines.append(f"{r['mode']} | {r['configuration_b']} | {r['scenes_a_greater']}/{r['scenes_tied']}/{r['scenes_a_lower']} | {r['total_difference']:+d} | {r['mean_difference']:+.3f} [{r['ci95_low']:+.3f}, {r['ci95_high']:+.3f}]")
    lines += ['', 'Every scene, detector output. Each cell = visible/correct/false/missed.',
        'scene | ' + ' | '.join(NAMES)]
    for s in range(1, 34):
        lines.append(f'{s:02d} | ' + ' | '.join('/'.join(str(lookup['detector',s,*c][k]) for k in ('gt','tp','fp','fn')) for c in CONFIGS))
    lines += ['', 'Interpretation:',
        'Gorillapod 0.5x leads total correct counts in both detector and two-object output modes.',
        'It also leads total annotated objects in frame. This supports it as the candidate when',
        'the objective is object coverage, while chest 1x leads the earlier F1 objective.',
        'Raw prediction counts are not treated as a benefit: they include false detections.',
        'A scene with many chairs weighs heavily in totals. Means, scene win/tie/loss counts,',
        'per-class counts and paired intervals should be considered together.',
        'The two-object output cap limits count differences by design; speech usefulness is untested.',
        'Confidence intervals use 10,000 paired group resamples, seed 20261013. All comparisons',
        'are exploratory and unadjusted for multiple comparisons. Capture groups may share rooms.',
        'These are iPhone images replayed through the Android app on a Pixel 8 emulator.',
        'Photos were successive, not simultaneous: moving people and changed poses can also',
        'change object counts. Count differences cannot be attributed entirely to mount or lens.',
        'The six-photo order uses the sequence supplied by the user; filenames appear on each sheet.',
        'Visual sheets show matched GT in green, missed GT in amber, false predictions in red.',
        'Green boxes use reviewed GT geometry for easier comparison, not predicted geometry.',
        'Chest 1x has more correct detections than gorillapod 0.5x in scenes: ' +
        ', '.join(f'{s:02d}' for s in range(1,34) if lookup['detector',s,'chest_harness','1x']['tp'] > lookup['detector',s,'gorillapod','0.5x']['tp']) + '.',
        '', 'Selected scenes inspected visually:',
        'Scene 10, living/dining room: chest 1x has 7 annotated objects and zero correct',
        'detections; chest 0.5x has 8 and zero; gorillapod 0.5x has 8 and four.',
        'The chest failure here involves recognizing visible objects, not just framing.',
        'Scene 12, living/dining room: gorillapod 0.5x detects 9/10, chest 0.5x 7/10,',
        'and chest 1x 6/8. The wider gorillapod view combines coverage and detection gains.',
        'Scene 28, outdoor seating: gorillapod 0.5x contains 36 annotated objects versus',
        'chest 1x 23, but detects only 10 versus 9. Wider coverage does not guarantee',
        'the detector can recover the extra small/distant objects. People also move.',
        'Scene 30, salon: chest 0.5x detects 7/10 with one false detection; gorillapod',
        '0.5x detects 4/13 with six false detections. Chest is preferable in this scene.',
        'Scene 03: gorillapod 1x detects 7/9; gorillapod 0.5x 4/12. This is another',
        'case where broader coverage does not yield more correct detections.',
        '', 'Practical conclusion:',
        'For the stated goal of finding more objects across scenes, choose gorillapod 0.5x',
        'as the provisional configuration to validate next. Its count advantage over chest',
        '1x is supported by the exploratory paired interval; its smaller advantage over',
        'chest 0.5x and gorillapod 1x remains uncertain. F1 still favors chest 1x.',
        'A stronger coverage benchmark would assign shared object IDs across the six photos',
        'and mark which objects are visible, occluded, or outside each frame. This would',
        'measure recovery of the same scene objects and separate framing from detector errors.']
    (OUT / 'report.txt').write_text('\n'.join(lines)+'\n')


def plots(lookup):
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT/'benchmark/.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(14, 13), layout='constrained')
    for ax, metric, title, cmap in zip(axes, ('gt','tp','fp'),
            ('Objects in the photo (GT)', 'Correct detections (TP)', 'False detections (FP)'),
            ('Blues','Greens','Reds')):
        values = np.array([[lookup['detector', s, *c][metric] for c in CONFIGS] for s in range(1,34)])
        ax.imshow(values, cmap=cmap, vmin=0, aspect='auto')
        for y in range(33):
            for x in range(6):
                ax.text(x,y,str(values[y,x]),ha='center',va='center',fontsize=9,
                    color='white' if values[y,x] > values.max()*.58 else '#17202a')
        ax.set_xticks(range(6),NAMES,rotation=45,ha='right')
        ax.set_yticks(range(33),range(1,34));ax.set_ylabel('Capture group / scene');ax.set_title(title)
    fig.suptitle('Same 33 scenes, six configurations - detector at confidence 0.30\nCell numbers are object counts; each panel has its own color scale')
    fig.savefig(OUT/'scene_counts.png',dpi=170);fig.savefig(OUT/'scene_counts.pdf');plt.close(fig)


def sheets(lookup):
    gt=json.loads((ROOT/'labels.json').read_text())
    run=json.loads((OUT.parent.parent/'android.json').read_text())
    frames={f['image_id']:f for f in run['frames']}
    annotations=defaultdict(list)
    for ann in gt['annotations']:annotations[ann['image_id']].append(ann)
    from matplotlib.font_manager import findfont
    font=ImageFont.truetype(findfont('DejaVu Sans'),14)
    sheets_dir=OUT/'sheets';sheets_dir.mkdir(exist_ok=True)
    for s in range(1,34):
        sheet=Image.new('RGB',(1152,1180),'#ffffff');d=ImageDraw.Draw(sheet)
        d.text((8,8),f'Scene {s:02d} | Green: correct GT; amber: missed GT; red: false prediction',font=font,fill='#17202a')
        for n,c in enumerate(CONFIGS):
            row=lookup['detector',s,*c];truth=annotations[row['image_id']]
            preds=[p for p in frames[row['image_id']]['predictions'] if p['score']>=run['metadata']['confidence']]
            matched,fp,fn=match(truth,preds)
            with Image.open(ROOT/'data'/row['file_name']) as im:tile=im.resize((384,512))
            td=ImageDraw.Draw(tile)
            for objects,color in (([p[1] for p in matched],'#27ed62'),(fn,'#ffbb00'),(fp,'#ff354d')):
                for obj in objects:
                    x,y,w,h=obj['bbox'];td.rectangle((x/4,y/4,(x+w)/4,(y+h)/4),outline=color,width=2)
            left=(n%3)*384;top=36+(n//3)*568
            d.text((left+6,top),NAMES[n]+' | '+row['file_name'],font=font,fill='#17202a')
            d.text((left+6,top+19),f"Visible {row['gt']} | Correct {row['tp']} | Missed {row['fn']} | False {row['fp']}",font=font,fill='#17202a')
            sheet.paste(tile,(left,top+42))
        sheet.save(sheets_dir/f'scene-{s:02d}.jpg',quality=90)


if __name__=='__main__':
    main()
