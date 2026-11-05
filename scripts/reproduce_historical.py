#!/usr/bin/env python3
"""Replay the original six-model evaluation without overwriting its archived tables."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from recover_historical_models import REPO,recover


def parse_metrics(text):
    rows={};lines=text.splitlines()
    for index,line in enumerate(lines):
        if line=='='*40 and index+2<len(lines) and lines[index+2]=='='*40:
            name=lines[index+1].strip();row={}
            for value in lines[index+3:index+8]:
                key,number=value.strip().rsplit(':',1);row[key]=float(number)
            rows[name]=row
    if len(rows)!=6:raise ValueError('Expected six model metric blocks')
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['normal','panoramic','both'],default='both')
    p.add_argument('--output',type=Path,default=REPO/'development/runs/historical')
    a=p.parse_args();a.output=a.output.resolve()
    archive=REPO/'Build/Testing'
    if a.output==REPO or a.output==archive or archive in a.output.parents:p.error('Choose an output outside Build/Testing.')
    if a.output.exists():p.error('Output exists; choose a new directory.')
    versions={name:importlib.metadata.version(name) for name in ('numpy','pillow','pycocotools','opencv-python-headless','ai-edge-litert')}
    a.output.mkdir(parents=True)
    models=recover(a.output/'models')
    report=dict(runtime='LiteRT interpreter through compatibility import; original historical runtime was not frozen',packages=versions,platform=platform.platform(),models=models,modes={})
    source=REPO/'Build/models_comparison'
    worker=Path(__file__).with_name('reproduce_historical_worker.py')
    for mode in (['normal','panoramic'] if a.mode=='both' else [a.mode]):
        work=a.output/mode;work.mkdir()
        shutil.copytree(a.output/'models',work/'models')
        dataset='test_images' if mode=='normal' else 'panoramic'
        (work/dataset).mkdir();shutil.copy2(source/dataset/'labels.json',work/dataset/'labels.json')
        shutil.copytree(source/dataset/'data',work/dataset/'data')
        shutil.copy2(source/'benchmark_models.py',work/'benchmark_models.py')
        (work/'benchmark_config.json').write_text(json.dumps(dict(mode=mode)))
        result_file='desktop.md' if mode=='normal' else 'panoramic_desktop.md'
        print('Replaying six models:',mode,flush=True)
        with (work/'inference.log').open('w') as log:
            subprocess.run([sys.executable,str(worker),str(work)],cwd=work,stdout=log,stderr=subprocess.STDOUT,check=True)
        generated=work/'results'/result_file
        text=generated.read_text();actual=parse_metrics(text);expected=parse_metrics((source/'results'/result_file).read_text())
        differences=[dict(model=name,metric=key,archived=expected[name][key],new=number)
                     for name,row in actual.items() for key,number in row.items() if expected[name][key]!=number]
        # Remove the historical machine description from the new result.
        generated.write_text('New replay: '+versions['ai-edge-litert']+' LiteRT, '+platform.platform()+'. Original model binaries and evaluation code; runtime updated.\n\n'+text[text.index('='*40):])
        inputs={str(file.relative_to(work)):hashlib.sha256(file.read_bytes()).hexdigest()
                for file in [work/'benchmark_models.py',work/dataset/'labels.json',*sorted((work/dataset/'data').iterdir())] if file.is_file()}
        report['modes'][mode]=dict(archived_metrics_match=not differences,differences=differences,metrics=actual,input_sha256=inputs)
        (a.output/'historical_report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(mode+': '+('all 30 displayed metrics match' if not differences else str(len(differences))+' displayed metrics differ'),flush=True)
    if any(not mode['archived_metrics_match'] for mode in report['modes'].values()):
        raise SystemExit('Replay completed with differences from historical metrics; see historical_report.json. The archive was not changed.')


if __name__=='__main__':main()
