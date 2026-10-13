"""Paired comparisons pooled by lens and mount, retaining scene groups."""
import argparse,csv,json
from pathlib import Path
import numpy as np
from evaluate import bootstrap,write_csv

def main():
 p=argparse.ArgumentParser();p.add_argument('results',type=Path);a=p.parse_args()
 rows=list(csv.DictReader((a.results/'per_image.csv').open()))
 for r in rows:
  for key in ('capture_group','tp','fp','fn','gt','predictions'):r[key]=int(r[key])
 groups=sorted({r['capture_group'] for r in rows});draws=np.random.default_rng(20261013).integers(0,len(groups),(10000,len(groups)))
 output=[]
 for mode in ('detector','app_output'):
  def pool(field,value):
   selected=[r for r in rows if r['mode']==mode and r[field]==value]
   return [{k:sum(r[k] for r in selected if r['capture_group']==g) for k in ('tp','fp','fn','gt','predictions')} for g in groups]
  for field,left,right in [('lens','1x','0.5x'),('mount','head_harness','chest_harness'),('mount','head_harness','gorillapod'),('mount','chest_harness','gorillapod')]:
   output.append(dict(mode=mode,factor=field,condition_a=left,condition_b=right,**bootstrap(pool(field,left),pool(field,right),draws)))
 write_csv(a.results/'paired_effects.csv',output)
 print(json.dumps(output,indent=2))
if __name__=='__main__':main()
