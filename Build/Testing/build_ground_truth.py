"""Convert a fully reviewed COCO export to this dataset's canonical IDs."""
import argparse
import json
from pathlib import Path
from verify_gt import EXPECTED,verify

ROOT=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('export',type=Path);p.add_argument('--reviewed-all',action='store_true',help='Confirm you personally reviewed all 198 images, including empty ones')
    p.add_argument('--output',type=Path,default=ROOT/'labels.json');a=p.parse_args()
    if not a.reviewed_all:p.error('Complete manual review first, then pass --reviewed-all.')
    source=json.loads(a.export.read_text());manifest=json.loads((ROOT/'images.coco.json').read_text())
    names={name:k for k,name in EXPECTED.items()};category_map={}
    used_categories={x['category_id'] for x in source['annotations']}
    for c in source['categories']:
        if c['name'] in names:category_map[c['id']]=names[c['name']]
        elif c['id']==0 and c['id'] not in used_categories and c.get('supercategory')=='none':continue
        elif c['name']!='indoor-detection':raise ValueError(f'Unexpected category: {c["name"]}')
    canonical={Path(i['file_name']).stem:i for i in manifest['images']};image_map={};seen=set()
    for i in source['images']:
        # Roboflow may append .rf.<hash> and convert the extension.
        prefix=Path(i['file_name']).name.split('.rf.')[0]
        stem=Path(prefix).stem
        if stem not in canonical:
            aliases={key+suffix:key for key in canonical for suffix in ('_jpeg','_jpg','_JPEG','_JPG')}
            stem=aliases.get(prefix,stem)
        if stem not in canonical:
            # Prefer exact original stem for ordinary COCO files.
            stem=Path(i['file_name']).stem
        if stem not in canonical:raise ValueError(f'Unmatched image: {i["file_name"]}')
        target=canonical[stem]
        if target['id'] in seen:raise ValueError('Duplicate source image')
        if (i['width'],i['height'])!=(target['width'],target['height']):raise ValueError('Image was resized; export original-resolution annotations')
        seen.add(target['id']);image_map[i['id']]=target['id']
    if len(seen)!=198:raise ValueError(f'Export must include all 198 images, found {len(seen)}')
    anns=[];rounding_fixes=0
    targets={i['id']:i for i in manifest['images']}
    for x in source['annotations']:
        if x['category_id'] not in category_map:raise ValueError('Annotation uses placeholder or unknown category')
        box=x['bbox'];target=targets[image_map[x['image_id']]]
        bx,by,bw,bh=box
        if bx<0 or by<0 or bx+bw>target['width'] or by+bh>target['height']:
            if min(bx,by)<-0.05 or bx+bw>target['width']+0.05 or by+bh>target['height']+0.05:
                raise ValueError(f'Box exceeds rounding tolerance: {x["id"]}')
            right=min(target['width'],bx+bw);bottom=min(target['height'],by+bh)
            bx=max(0,bx);by=max(0,by);box=[bx,by,right-bx,bottom-by];rounding_fixes+=1
        anns.append(dict(id=len(anns)+1,image_id=image_map[x['image_id']],category_id=category_map[x['category_id']],bbox=box,area=box[2]*box[3],iscrowd=0,segmentation=[]))
    manifest['annotations']=anns;manifest['info']['review_status']='USER_CONFIRMED_ALL_198_REVIEWED'
    manifest['info']['export_rounding_boxes_clipped']=rounding_fixes
    for i in manifest['images']:i['annotation_status']='reviewed'
    tmp=a.output.with_suffix('.pending.json');tmp.write_text(json.dumps(manifest,indent=2)+'\n')
    report=verify(tmp,ROOT/'data');tmp.replace(a.output)
    print(f'Wrote {a.output}: {len(anns)} annotations; {len(report["zero_annotation_images"])} empty images')

if __name__=='__main__':main()
