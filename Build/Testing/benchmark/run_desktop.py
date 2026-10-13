"""Desktop proxy of AssistiveVision's image pipeline; Android replay is authoritative."""
import argparse, hashlib, importlib.metadata, json, platform, subprocess, time
from pathlib import Path
import numpy as np
from PIL import Image
from ai_edge_litert.interpreter import Interpreter

ROOT=Path(__file__).resolve().parent.parent
CLASSES={1,62,63,65,67,70,72,73,81,82}

def prepare(path):
    with Image.open(path) as source:
        im=source.convert('RGB');w,h=im.size
        scale=min(448/w,448/h);dw,dh=int(w*scale),int(h*scale)
        dx,dy=(448-dw)//2,(448-dh)//2
        canvas=Image.new('RGB',(448,448),(114,114,114))
        canvas.paste(im.resize((dw,dh),Image.Resampling.BILINEAR),(dx,dy))
    return np.asarray(canvas,dtype=np.uint8)[None],(w,h,dw,dh,dx,dy)

def main():
    p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True)
    p.add_argument('--output',type=Path,default=ROOT/'benchmark/results/desktop.json')
    p.add_argument('--confidence',type=float,default=.30);p.add_argument('--max-objects',type=int,default=2)
    a=p.parse_args();gt=json.loads((ROOT/'labels.json').read_text())
    interpreter=Interpreter(model_path=str(a.model),num_threads=1);interpreter.allocate_tensors()
    ins=interpreter.get_input_details();outs=interpreter.get_output_details()
    assert len(ins)==1 and tuple(ins[0]['shape'])==(1,448,448,3) and ins[0]['dtype']==np.uint8
    assert tuple(outs[0]['shape'])[0]==1 and tuple(outs[0]['shape'])[-1]==4
    sample,_=prepare(ROOT/'data'/gt['images'][0]['file_name'])
    for _ in range(3):interpreter.set_tensor(ins[0]['index'],sample);interpreter.invoke()
    frames=[]
    for n,im in enumerate(gt['images'],1):
        t0=time.perf_counter();tensor,geometry=prepare(ROOT/'data'/im['file_name']);t1=time.perf_counter()
        interpreter.set_tensor(ins[0]['index'],tensor);t2=time.perf_counter();interpreter.invoke();t3=time.perf_counter()
        boxes,classes,scores,count=[interpreter.get_tensor(o['index']) for o in outs]
        w,h,dw,dh,dx,dy=geometry;predictions=[]
        candidates=[i for i in range(min(int(count[0]),boxes.shape[1])) if int(classes[0,i])+1 in CLASSES and scores[0,i]>=.001]
        candidates=sorted(candidates,key=lambda i:-float(scores[0,i]))[:15]
        for i in candidates:
            y1,x1,y2,x2=boxes[0,i]
            x1,x2=np.clip((np.array([x1,x2])*448-dx)*w/dw,0,w)
            y1,y2=np.clip((np.array([y1,y2])*448-dy)*h/dh,0,h)
            predictions.append(dict(image_id=im['id'],category_id=int(classes[0,i])+1,score=float(scores[0,i]),bbox=[float(x1),float(y1),float(x2-x1),float(y2-y1)]))
        frames.append(dict(image_id=im['id'],file_name=im['file_name'],predictions=predictions,preprocess_ms=(t1-t0)*1000,inference_ms=(t3-t2)*1000))
        if n%12==0 or n==198:print(f'{n}/198',flush=True)
    run=dict(metadata=dict(source='desktop_proxy',model_sha256=hashlib.sha256(a.model.read_bytes()).hexdigest(),gt_sha256=hashlib.sha256((ROOT/'labels.json').read_bytes()).hexdigest(),runtime=importlib.metadata.version('ai-edge-litert'),platform=platform.platform(),confidence=a.confidence,max_objects=a.max_objects,detector_cap=15,score_floor=.001,threads=1,warmup=3,preprocessing='Pillow bilinear RGB, gray114 letterbox. Same geometry as app; JPEG decoding and resize pixels may differ from Android.',timing_scope='desktop CPU inference only; not Android latency'),frames=frames)
    app_root=a.model.resolve().parents[4]
    if a.model.parent.name=='assets' and (app_root/'.git').exists():
        run['metadata']['app_commit']=subprocess.check_output(['git','-C',str(app_root),'rev-parse','HEAD'],text=True).strip()
        source_root=app_root/'app/src/main/java/com/unimagdalena/assistivevision'
        run['metadata']['source_hashes']={str(f.relative_to(app_root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in source_root.rglob('*.kt') if f.name in ['PreprocessingModule.kt','DetectionModule.kt','LetterboxMapper.kt','MainViewModel.kt','SettingsManager.kt']}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(run,indent=2)+'\n')
    print(a.output)
if __name__=='__main__':main()
