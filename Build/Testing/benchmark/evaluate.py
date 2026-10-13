"""Compare six capture configurations with COCO AP and paired scene analysis."""
import argparse, contextlib, csv, hashlib, io, itertools, json, math, os
from collections import defaultdict
from pathlib import Path
import numpy as np
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval

ROOT=Path(__file__).resolve().parent.parent
CONFIGS=[(m,l) for m in ('head_harness','chest_harness','gorillapod') for l in ('1x','0.5x')]

def iou(a,b):
    ax,ay,aw,ah=a;bx,by,bw,bh=b
    inter=max(0,min(ax+aw,bx+bw)-max(ax,bx))*max(0,min(ay+ah,by+bh)-max(ay,by))
    union=aw*ah+bw*bh-inter
    return inter/union if union else 0.

def match(gt,preds):
    used=set();matches=[];unmatched=[]
    for p in sorted(preds,key=lambda x:-x['score']):
        candidates=[(iou(p['bbox'],g['bbox']),j) for j,g in enumerate(gt) if j not in used and p['category_id']==g['category_id']]
        overlap,j=max(candidates,default=(-1,-1))
        if overlap>=.5:used.add(j);matches.append((p,gt[j],overlap))
        else:unmatched.append(p)
    return matches,unmatched,[g for j,g in enumerate(gt) if j not in used]

def scores(tp,fp,fn):
    return dict(precision=tp/(tp+fp) if tp+fp else None,recall=tp/(tp+fn) if tp+fn else None,f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None)

def metric_sum(rows):
    sums={key:int(sum(r[key] for r in rows)) for key in ('tp','fp','fn','gt','predictions')}
    return {**sums,**scores(sums['tp'],sums['fp'],sums['fn'])}

def ap(coco,preds,ids):
    if not any(len(coco.imgToAnns.get(i,[])) for i in ids):return {'AP':None,'AP50':None,'AP75':None}
    if not preds:return {'AP':0.,'AP50':0.,'AP75':0.}
    with contextlib.redirect_stdout(io.StringIO()):
        result=coco.loadRes(preds);ev=COCOeval(coco,result,'bbox');ev.params.imgIds=ids
        ev.params.catIds=sorted(coco.getCatIds());ev.evaluate();ev.accumulate();ev.summarize()
    return {k:float(ev.stats[j]) if ev.stats[j]>=0 else None for j,k in enumerate(('AP','AP50','AP75'))}

def write_csv(path,rows):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def bootstrap(rows_a,rows_b,draws):
    # Matched six-photo groups are resampled together; individual photos are not independent trials.
    a=np.array([[r['tp'],r['fp'],r['fn']] for r in rows_a]);b=np.array([[r['tp'],r['fp'],r['fn']] for r in rows_b])
    aa=a[draws].sum(axis=1);bb=b[draws].sum(axis=1)
    def f1(x):
        den=2*x[:,0]+x[:,1]+x[:,2]
        return np.divide(2*x[:,0],den,out=np.full(len(x),np.nan),where=den>0)
    delta=f1(aa)-f1(bb);valid=delta[np.isfinite(delta)]
    basea=metric_sum(rows_a)['f1'];baseb=metric_sum(rows_b)['f1']
    return dict(delta_f1=basea-baseb if basea is not None and baseb is not None else None,ci95_low=float(np.percentile(valid,2.5)) if len(valid) else None,ci95_high=float(np.percentile(valid,97.5)) if len(valid) else None)

def main():
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--output',type=Path)
    a=p.parse_args();out=a.output or a.run.parent/a.run.stem;out.mkdir(parents=True,exist_ok=True)
    gt=json.loads((ROOT/'labels.json').read_text());run=json.loads(a.run.read_text());meta=run['metadata']
    if meta['gt_sha256']!=hashlib.sha256((ROOT/'labels.json').read_bytes()).hexdigest():raise ValueError('Ground truth hash mismatch')
    images={i['id']:i for i in gt['images']};frames={f['image_id']:f for f in run['frames']}
    if len(frames)!=len(run['frames']) or set(frames)!=set(images):raise ValueError('Incomplete or duplicate frame results')
    assert len(images)==198
    for im in images.values():
        assert (im['mount'],im['lens']) in CONFIGS
        assert frames[im['id']]['file_name']==im['file_name']
    scene_ids=sorted({i['capture_group'] for i in images.values()})
    assert len(scene_ids)==33
    assert all(sum(i['capture_group']==s and (i['mount'],i['lens'])==c for i in images.values())==1 for s in scene_ids for c in CONFIGS)
    categories={c['id']:c['name'] for c in gt['categories']};gts=defaultdict(list)
    for ann in gt['annotations']:gts[ann['image_id']].append(ann)
    with contextlib.redirect_stdout(io.StringIO()):coco=COCO(str(ROOT/'labels.json'))
    for image_id,f in frames.items():
        for pred in f['predictions']:
            assert pred['image_id']==image_id and pred['category_id'] in categories
            assert 0<=pred['score']<=1 and all(math.isfinite(x) for x in pred['bbox'])
            assert pred['bbox'][2]>=0 and pred['bbox'][3]>=0
    summaries=[];image_rows=[];class_rows=[];pairs=[]
    draws=np.random.default_rng(20261013).integers(0,len(scene_ids),size=(10000,len(scene_ids)))
    for mode,threshold,cap in [('detector',meta['confidence'],15),('app_output',meta['confidence'],meta['max_objects'])]:
        mode_rows=[];preds_by={};class_counts=defaultdict(lambda:[0,0,0])
        for image_id,im in images.items():
            preds=sorted([p for p in frames[image_id]['predictions'] if p['score']>=threshold],key=lambda p:-p['score'])[:cap]
            preds_by[image_id]=preds;matches,fp,fn=match(gts[image_id],preds)
            for p,g,_ in matches:class_counts[(im['mount'],im['lens'],g['category_id'])][0]+=1
            for p in fp:class_counts[(im['mount'],im['lens'],p['category_id'])][1]+=1
            for g in fn:class_counts[(im['mount'],im['lens'],g['category_id'])][2]+=1
            row=dict(mode=mode,image_id=image_id,file_name=im['file_name'],capture_group=im['capture_group'],mount=im['mount'],lens=im['lens'],gt=len(gts[image_id]),predictions=len(preds),tp=len(matches),fp=len(fp),fn=len(fn),inference_ms=frames[image_id]['inference_ms'],**scores(len(matches),len(fp),len(fn)))
            mode_rows.append(row);image_rows.append(row)
        selections=[('configuration',m,l,[r for r in mode_rows if r['mount']==m and r['lens']==l]) for m,l in CONFIGS]
        selections += [('lens','all',l,[r for r in mode_rows if r['lens']==l]) for l in ('1x','0.5x')]
        selections += [('mount',m,'all',[r for r in mode_rows if r['mount']==m]) for m in ('head_harness','chest_harness','gorillapod')]
        selections += [('overall','all','all',mode_rows)]
        for kind,m,l,rows in selections:
            ids=[r['image_id'] for r in rows];ids_set=set(ids)
            # AP uses low-floor predictions with detector cap; fixed-threshold P/R/F1 use operating settings.
            low=[p for id in ids for p in sorted(frames[id]['predictions'],key=lambda p:-p['score'])[:cap]]
            summary=dict(mode=mode,aggregation=kind,mount=m,lens=l,images=len(rows),**metric_sum(rows),**ap(coco,low,ids),mean_gt_per_image=sum(r['gt'] for r in rows)/len(rows),mean_tp_per_image=sum(r['tp'] for r in rows)/len(rows),positive_images=sum(r['gt']>0 for r in rows),positive_images_with_tp=sum(r['gt']>0 and r['tp']>0 for r in rows),empty_images=sum(r['gt']==0 for r in rows),empty_images_with_fp=sum(r['gt']==0 and r['fp']>0 for r in rows),inference_median_ms=float(np.median([r['inference_ms'] for r in rows])),inference_p95_ms=float(np.percentile([r['inference_ms'] for r in rows],95)))
            summaries.append(summary)
        for (m,l,cat),(tp,fp,fn) in sorted(class_counts.items()):class_rows.append(dict(mode=mode,mount=m,lens=l,category=categories[cat],tp=tp,fp=fp,fn=fn,**scores(tp,fp,fn)))
        grouped={c:sorted([r for r in mode_rows if (r['mount'],r['lens'])==c],key=lambda r:r['capture_group']) for c in CONFIGS}
        for ca,cb in itertools.combinations(CONFIGS,2):
            pairs.append(dict(mode=mode,configuration_a='/'.join(ca),configuration_b='/'.join(cb),**bootstrap(grouped[ca],grouped[cb],draws)))
    write_csv(out/'summary.csv',summaries);write_csv(out/'per_image.csv',image_rows);write_csv(out/'per_class.csv',class_rows);write_csv(out/'paired_comparisons.csv',pairs)
    result=dict(metadata=meta,summary=summaries,paired_comparisons=pairs)
    (out/'metrics.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    make_report(out,result)
    print(out)

def make_report(out,result):
    os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'benchmark/.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    meta=result['metadata'];rows=[r for r in result['summary'] if r['aggregation']=='configuration']
    def fmt(v):return 'n/a' if v is None else f'{v:.3f}'
    lines=['AssistiveVision capture configuration comparison',f"Run source: {meta['source']}",f"Confidence: {meta['confidence']}; app object limit: {meta['max_objects']}",'', 'Each configuration contains the same 33 acquisition groups. Metrics describe visible annotated instances in the iPhone photos.','COCO AP/AP50/AP75 use score floor 0.001 and the stated output cap; P/R/F1 use the configured confidence and IoU >= 0.50.','The app_output row models the selected-object list; speech quality and camera capture are not tested.','', 'mode | mount | lens | GT | TP | FP | FN | precision | recall | F1 | AP50 | AP',]
    for r in rows:lines.append(' | '.join([r['mode'],r['mount'],r['lens']]+[str(r[k]) for k in ('gt','tp','fp','fn')]+[fmt(r[k]) for k in ('precision','recall','f1','AP50','AP')]))
    lines += ['', 'Interpretation limits:', '- A wider view can contain more targets. GT per image and TP per image accompany recall so a narrow view is not rewarded for hiding difficult targets.', '- No cross-image object identity or task relevance was annotated; the study cannot count real-world targets outside the frame.', '- The 33 groups are paired acquisitions, not necessarily independent rooms/homes. Paired bootstrap intervals resample groups and may be optimistic when groups share environments.', '- Pairwise intervals are exploratory, unadjusted for multiple comparisons. Choosing a winner on this test set makes it a configuration-selection set; validate the choice on new scenes.', '- iPhone 0.5x/1x results may not transfer to the Android phone’s optics, camera resolution or framing.', '- Desktop proxy uses a different runtime and image decoder/resizer from Android. Android replay and phone timing are required before a final app recommendation.', '- Confirm the six-photo sequence labels against capture notes before relying on the comparison.']
    if meta['source']=='android_app_modules':
        lines=[line for line in lines if not line.startswith('- Desktop proxy uses')]
    if meta.get('device_kind')=='emulator':
        lines += ['- This Android run used a Pixel 8 AVD on the host CPU, not physical Pixel 8 hardware. Its latency is emulator-only.']
    best=max((r for r in rows if r['mode']=='detector'),key=lambda r:r['f1'] or 0)
    lines += ['', f"Highest observed detector F1: {best['mount']} {best['lens']} ({best['f1']:.3f}).", 'This is an exploratory leader, not a statistically established winner. See paired_comparisons.csv.']
    (out/'report.txt').write_text('\n'.join(lines)+'\n')
    fig,axes=plt.subplots(1,3,figsize=(15,5),layout='constrained')
    labels=[m.replace('_harness','').replace('_',' ')+' '+l for m,l in CONFIGS]
    for mode,color,offset in [('detector','#2575b8',-.18),('app_output','#df8232',.18)]:
        rr=[next(r for r in rows if r['mode']==mode and (r['mount'],r['lens'])==c) for c in CONFIGS]
        for ax,key in zip(axes,('precision','recall','f1')):
            ax.bar(np.arange(6)+offset,[r[key] or 0 for r in rr],width=.36,label=mode,color=color)
            ax.set_xticks(np.arange(6),labels,rotation=35,ha='right');ax.set_ylim(0,1);ax.set_title(key.capitalize());ax.grid(axis='y',alpha=.2)
    axes[0].legend();fig.suptitle(f"{meta['source']} — confidence {meta['confidence']}, IoU ≥ 0.50")
    fig.savefig(out/'comparison.png',dpi=180);fig.savefig(out/'comparison.pdf');plt.close(fig)

if __name__=='__main__':main()
