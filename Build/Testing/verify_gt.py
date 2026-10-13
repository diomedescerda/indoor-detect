"""Validate COCO object-detection annotations and write a review report."""
import argparse
import json
import math
from collections import Counter
from pathlib import Path
from pycocotools.coco import COCO
from PIL import Image

EXPECTED={1:'person',62:'chair',63:'couch',65:'bed',67:'dining table',70:'toilet',72:'tv',73:'laptop',81:'sink',82:'refrigerator'}

def verify(path, data):
    raw=json.loads(path.read_text())
    assert {c['id']:c['name'] for c in raw['categories']}==EXPECTED,'Category IDs/names differ'
    images={i['id']:i for i in raw['images']}
    assert len(images)==len(raw['images'])==198,'Expected 198 unique images'
    assert len({i['file_name'] for i in images.values()})==198,'Duplicate file names'
    assert all(i.get('annotation_status')!='pending' for i in images.values()),'Pending annotations'
    ids=set();counts=Counter();per_image=Counter()
    for a in raw['annotations']:
        assert a['id'] not in ids,'Duplicate annotation ID'
        ids.add(a['id']);im=images[a['image_id']]
        assert a['category_id'] in EXPECTED
        x,y,w,h=a['bbox']
        assert all(math.isfinite(v) for v in (x,y,w,h))
        assert x>=0 and y>=0 and w>0 and h>0
        assert x+w<=im['width']+0.001 and y+h<=im['height']+0.001
        assert abs(a['area']-w*h)<0.01 and a['iscrowd']==0
        counts[a['category_id']]+=1;per_image[a['image_id']]+=1
    for im in images.values():
        with Image.open(data/im['file_name']) as image:
            assert image.size==(im['width'],im['height'])
    coco=COCO(str(path))
    assert len(coco.getImgIds())==198
    report={'file':path.name,'images':198,'annotations':len(ids),'histogram':{name:counts[k] for k,name in EXPECTED.items()},'zero_annotation_images':[im['file_name'] for im in images.values() if not per_image[im['id']]],'review_status':raw.get('info',{}).get('review_status','unspecified'),'warning':'Structural validation does not establish annotation accuracy or human review.'}
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('coco',type=Path);p.add_argument('--data',type=Path,default=Path(__file__).resolve().parent/'data');a=p.parse_args()
    report=verify(a.coco,a.data)
    a.coco.with_suffix('.validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
