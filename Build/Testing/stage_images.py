"""Stage photos without modifying originals; preserve six-capture sequence metadata."""
import csv
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent
CLASSES = {1:'person',62:'chair',63:'couch',65:'bed',67:'dining table',70:'toilet',72:'tv',73:'laptop',81:'sink',82:'refrigerator'}
CYCLE = [('head_harness','1x'),('head_harness','0.5x'),('chest_harness','1x'),('chest_harness','0.5x'),('gorillapod','1x'),('gorillapod','0.5x')]

def main():
    files = sorted((ROOT/'iCloud Photos').glob('*.JPEG'), key=lambda p:int(p.stem.split('_')[-1]))
    if len(files) != 198:
        raise ValueError(f'Expected 198 images, found {len(files)}')
    data = ROOT/'data'
    data.mkdir(exist_ok=True)
    images, rows = [], []
    for index, source in enumerate(files):
        destination = data/(source.stem+'.jpeg')
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if destination.exists():
            if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
                raise ValueError(f'Conflicting staged file: {destination}')
        else:
            shutil.copy2(source,destination)
        with Image.open(source) as image:
            image.verify()
        with Image.open(source) as image:
            width,height = image.size
            if image.getexif().get(274,1) != 1:
                raise ValueError(f'Unexpected EXIF orientation: {source.name}')
        mount,lens = CYCLE[index % 6]
        metadata = dict(sequence_index=index+1,capture_group=index//6+1,capture_position=index%6+1,mount=mount,lens=lens,grouping_status='provisional_filename_order')
        images.append(dict(id=index+1,file_name=destination.name,width=width,height=height,**metadata))
        rows.append(dict(original_name=source.name,file_name=destination.name,sha256=digest,**metadata))
    coco = dict(info=dict(description='AssistiveVision image manifest; no ground truth yet',capture_order_assumption='Ascending IMG number, repeating six captures starting at head harness 1x'),licenses=[],images=images,annotations=[],categories=[dict(id=k,name=v,supercategory='object') for k,v in CLASSES.items()])
    (ROOT/'images.coco.json').write_text(json.dumps(coco,indent=2)+'\n')
    with (ROOT/'capture_groups.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    print(f'Staged {len(images)} images in {len(images)//6} provisional capture groups; hashes and orientation verified.')

if __name__ == '__main__':
    main()
