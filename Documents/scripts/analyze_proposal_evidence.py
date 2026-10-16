"""Describe archived timing and digital image brightness; does not rerun inference.

Brightness is Pillow's 8-bit RGB-to-L conversion, averaged over native pixels.
Groups are sample-relative tertiles, not measured lighting conditions or lux.
Quantiles use linear interpolation with index (n-1)*p.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageStat

REPO = Path(__file__).resolve().parents[2]
TEST = REPO / 'Build/Testing'
RESULTS = TEST / 'benchmark/results/android'
OUT = REPO / 'Documents/Review/proposal_evidence'

def quantile(values, p):
    a = sorted(values)
    index = (len(a)-1)*p
    low = math.floor(index)
    return a[low] + (a[min(low+1, len(a)-1)]-a[low])*(index-low)

def describe(values):
    return {name: quantile(values, p) for name, p in [('min',0),('p25',.25),('median',.5),('p75',.75),('p95',.95),('max',1)]}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    run = json.loads((RESULTS.parent/'android.json').read_text())
    gt = json.loads((TEST/'labels.json').read_text())
    images = {i['id']: i for i in gt['images']}
    rows = [r for r in csv.DictReader((RESULTS/'per_image.csv').open()) if r['mode']=='detector']
    by_id = {int(r['image_id']):r for r in rows}
    assert len(run['frames'])==len(images)==len(by_id)==198
    assert {f['image_id'] for f in run['frames']}==set(images)==set(by_id)
    timings = {key:describe([f[key] for f in run['frames']]) for key in ['preprocess_ms','inference_ms']}
    timings['replay_total_ms'] = describe([f['preprocess_ms']+f['inference_ms'] for f in run['frames']])
    brightness = {}
    image_hashes = {}
    for iid, im in images.items():
        path = TEST/'data'/im['file_name']
        with Image.open(path) as src:
            assert src.size==(im['width'],im['height'])
            brightness[iid] = ImageStat.Stat(src.convert('RGB').convert('L')).mean[0]
        image_hashes[im['file_name']]=hashlib.sha256(path.read_bytes()).hexdigest()
    cut1, cut2 = [quantile(list(brightness.values()),p) for p in [1/3,2/3]]
    groups = ['Menor brillo','Brillo intermedio','Mayor brillo']
    records=[]
    for iid, im in images.items():
        value=brightness[iid]; band=groups[0 if value<=cut1 else 1 if value<=cut2 else 2]
        r=by_id[iid]
        records.append(dict(image_id=iid,file_name=im['file_name'],capture_group=im['capture_group'],mount=im['mount'],lens=im['lens'],mean_luma_8bit=value,brightness_group=band,**{k:int(r[k]) for k in ['gt','tp','fp','fn']}))
    categories={c['id']:c['name'] for c in gt['categories']}
    summary=[]
    for band in groups:
        selected=[r for r in records if r['brightness_group']==band];ids={r['image_id'] for r in selected}
        counts={k:sum(r[k] for r in selected) for k in ['gt','tp','fp','fn']}
        classes={n:sum(a['category_id']==cid and a['image_id'] in ids for a in gt['annotations']) for cid,n in categories.items()}
        configs={f"{m} {l}":sum(r['mount']==m and r['lens']==l for r in selected) for m,l in sorted({(r['mount'],r['lens']) for r in records})}
        summary.append(dict(group=band,n=len(selected),luma_min=min(r['mean_luma_8bit'] for r in selected),luma_max=max(r['mean_luma_8bit'] for r in selected),**counts,precision=counts['tp']/(counts['tp']+counts['fp']),recall=counts['tp']/counts['gt'],class_counts=classes,configuration_counts=configs))
    assert sum(s['gt'] for s in summary)==889 and sum(s['tp'] for s in summary)==425
    with (OUT/'brightness_per_image.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    evidence=dict(n_images=198,quantile_method='linear interpolation at (n-1)*p',timing_scope=run['metadata']['timing_scope'],timing_warmup_runs=3,timing_ms=timings,brightness_method='Pillow RGB to L at original resolution; arithmetic mean over pixels; 8-bit digital luma, not physical luminance',tertile_cutpoints=[cut1,cut2],brightness_groups=summary,limitations=['Post hoc sample-relative grouping; no lux measurements or controlled exposure','Class composition, framing, lens and scene content confound brightness associations','No occlusion fraction or labels in COCO GT; cannot infer hidden-object fraction from bbox area','Timing excludes camera acquisition, UI, localization, speech generation and playback; emulator only'],source_sha256={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [RESULTS.parent/'android.json',TEST/'labels.json',RESULTS/'per_image.csv']})
    (OUT/'summary.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
    (OUT/'image_sha256.json').write_text(json.dumps(image_hashes,indent=2)+'\n')
    print(json.dumps(dict(timing_ms=timings,brightness_groups=[{k:v for k,v in s.items() if k not in ['class_counts','configuration_counts']} for s in summary]),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
