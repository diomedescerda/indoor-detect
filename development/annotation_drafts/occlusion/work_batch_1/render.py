import json,os
from PIL import Image,ImageDraw,ImageFont
base='/home/kenma/personal/coding/indoor-detect/Build/Testing'
d=json.load(open(base+'/labels.json')); ims=sorted(d['images'],key=lambda x:x['file_name'])[:99]
font=ImageFont.load_default(size=19)
for k in range(0,99,3):
 sh=Image.new('RGB',(2160,1000),'#eeeeee'); dr=ImageDraw.Draw(sh)
 for j,im in enumerate(ims[k:k+3]):
  pic=Image.open(base+'/data/'+im['file_name']).convert('RGB'); pic.thumbnail((720,960)); sx=pic.width/im['width']; sy=pic.height/im['height']; off=j*720
  sh.paste(pic,(off,40)); dr.text((off+8,8),f"{k+j+1}: image {im['id']} {im['file_name']}",font=font,fill='black')
  for a in d['annotations']:
   if a['image_id']!=im['id']:continue
   x,y,w,h=a['bbox']; box=[off+x*sx,40+y*sy,off+(x+w)*sx,40+(y+h)*sy]
   dr.rectangle(box,outline='#00ffff',width=2)
   text=str(a['id']); bb=dr.textbbox((box[0]+2,box[1]+2),text,font=font); dr.rectangle(bb,fill='black'); dr.text((box[0]+2,box[1]+2),text,font=font,fill='#ffff00')
 sh.save(base+f'/occlusion/work_batch_1/sheet_{k+1:03}.jpg',quality=95)
json.dump([{'index':i+1,**im,'annotations':[a for a in d['annotations'] if a['image_id']==im['id']]} for i,im in enumerate(ims)],open(base+'/occlusion/work_batch_1/manifest.json','w'),indent=2)
print('Rendered 33 sheets; annotations:',sum(a['image_id'] in {im['id'] for im in ims} for a in d['annotations']))
