import json,hashlib,runpy,collections
from pathlib import Path
p=Path('/home/kenma/personal/coding/indoor-detect/Build/Testing');w=p/'occlusion/work_batch_1'
m=json.loads((w/'manifest.json').read_text());D=runpy.run_path(str(w/'decisions.py'))['D']; wanted={a['id'] for i in m for a in i['annotations']};assert set(D)==wanted
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
records=[]
for im in m:
 for a in im['annotations']:records.append({'annotation_id':a['id'],'image_id':im['id'],**D[a['id']]})
out={'schema_version':1,'reviewer_model':'gpt-6-astra','reasoning_effort':'high','status':'provisional_ai_labels_human_review_pending','source_hashes':{'labels.json':sha(p/'labels.json'),'images':{im['file_name']:sha(p/'data'/im['file_name']) for im in m}},'image_review':[im['id'] for im in m],'annotations':records}
f=p/'occlusion/labels_batch_1.json';f.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print('Saved',str(f));print('images',len(m),'annotations',len(records),'empty_images',[im['id'] for im in m if not im['annotations']]);print('occlusion',dict(collections.Counter(x['occlusion'] for x in records)));print('confidence',dict(collections.Counter(x['confidence'] for x in records)));print('truncation',sum(x['truncation'] for x in records));print('source_labels_sha256',out['source_hashes']['labels.json'])
