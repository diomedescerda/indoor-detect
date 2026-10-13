"""Render selected app detections beside reviewed GT for coordinate QA."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw
from evaluate import ROOT,match

def main():
 p=argparse.ArgumentParser();p.add_argument('run',type=Path);a=p.parse_args()
 run=json.loads(a.run.read_text());gt=json.loads((ROOT/'labels.json').read_text());cats={c['id']:c['name'] for c in gt['categories']}
 frames={f['image_id']:f for f in run['frames']};out=a.run.parent/a.run.stem/'overlays';out.mkdir(parents=True,exist_ok=True)
 for im in gt['images']:
  if im['id'] not in frames or im['id'] not in (1,4,21,37,57,133,157,163,193,198):continue
  preds=[x for x in frames[im['id']]['predictions'] if x['score']>=run['metadata']['confidence']]
  truth=[x for x in gt['annotations'] if x['image_id']==im['id']]
  matched,fp,fn=match(truth,preds)
  canvas=Image.new('RGB',(1536,1060),'white');d=ImageDraw.Draw(canvas)
  for panel,objects in enumerate((truth,preds)):
   with Image.open(ROOT/'data'/im['file_name']) as image:preview=image.resize((768,1024))
   draw=ImageDraw.Draw(preview)
   for obj in objects:
    x,y,w,h=obj['bbox'];color='#10ff35' if panel==0 or any(obj is pair[0] for pair in matched) else '#ff3030'
    draw.rectangle((x/2,y/2,(x+w)/2,(y+h)/2),outline=color,width=3)
    label=cats[obj['category_id']]+(f" {obj['score']:.2f}" if panel else '')
    draw.text((x/2,max(0,y/2-12)),label,fill=color,stroke_width=1,stroke_fill='black')
   canvas.paste(preview,(panel*768,36));d.text((panel*768+8,8),f"{im['file_name']} - "+('Reviewed GT' if panel==0 else f"Android detector: {len(matched)} TP, {len(fp)} FP, {len(fn)} FN"),fill='black')
  canvas.save(out/im['file_name'])
 print(out)
if __name__=='__main__':main()
