"""Render COCO draft overlays and contact sheets, preserving capture sequence."""
import json
from collections import defaultdict
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent

def main():
 c=json.loads((ROOT/'preannotations.coco.json').read_text());cats={x['id']:x['name'] for x in c['categories']};by=defaultdict(list)
 for a in c['annotations']:by[a['image_id']].append(a)
 for group in range(33):
  sheet=Image.new('RGB',(1152,1060),'#eeeeee');d=ImageDraw.Draw(sheet)
  for k,im in enumerate(c['images'][group*6:group*6+6]):
   preview=Image.open(ROOT/'data'/im['file_name']).resize((384,512));draw=ImageDraw.Draw(preview)
   for a in by[im['id']]:
    x,y,w,h=a['bbox'];box=(x/4,y/4,(x+w)/4,(y+h)/4)
    draw.rectangle(box,outline='red',width=2);draw.text(box[:2],cats[a['category_id']],fill='red')
   preview.save(ROOT/'review'/('annotated_'+im['file_name']))
   x=k%3*384;y=k//3*530;sheet.paste(preview,(x,y+18))
   d.text((x+3,y+3),f"{im['id']} {im['file_name']} boxes:{len(by[im['id']])}",fill='black')
  sheet.save(ROOT/'review'/f'annotated_group_{group+1:02}.jpg')
 print('Rendered 198 overlays and 33 contact sheets')
if __name__=='__main__':main()
