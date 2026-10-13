"""Convert chat visual annotations (384x512 display coordinates) to COCO."""
import json,sys,math
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent

def save(batch):
 p=ROOT/'chat_boxes.json'
 boxes=json.loads(p.read_text()) if p.exists() else {}
 boxes.update(batch);p.write_text(json.dumps(boxes,indent=2)+'\n')
 manifest=json.loads((ROOT/'images.coco.json').read_text());manifest['annotations']=[]
 manifest['info'].update(annotation_source='Codex chat visual annotation, requested GPT-6.1 Sol; no detector used',review_status='MODEL_ASSISTED_DRAFT_REQUIRES_USER_REVIEW',coordinate_method='Visual boxes on 384x512 previews, scaled to original pixels')
 cats={c['id']:c['name'] for c in manifest['categories']}
 for im in manifest['images']:
  im['annotation_status']='draft' if str(im['id']) in boxes else 'pending'
  if str(im['id']) not in boxes:continue
  preview=Image.open(ROOT/'data'/im['file_name']).resize((384,512));d=ImageDraw.Draw(preview)
  for cat,x1,y1,x2,y2 in boxes[str(im['id'])]:
   assert cat in cats and all(math.isfinite(v) for v in [x1,y1,x2,y2])
   assert 0<=x1<x2<=384 and 0<=y1<y2<=512,(im['id'],cat,x1,y1,x2,y2)
   box=[x1*4,y1*4,(x2-x1)*4,(y2-y1)*4]
   manifest['annotations'].append(dict(id=len(manifest['annotations'])+1,image_id=im['id'],category_id=cat,bbox=box,area=box[2]*box[3],iscrowd=0,segmentation=[]))
   d.rectangle((x1,y1,x2,y2),outline='red',width=2);d.text((x1,y1),cats[cat],fill='red')
  preview.save(ROOT/'review'/('annotated_'+im['file_name']))
 (ROOT/'preannotations.coco.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(f'{len(boxes)}/198 images annotated; {len(manifest["annotations"])} boxes')
if __name__=='__main__':save(json.loads(sys.stdin.read()))
