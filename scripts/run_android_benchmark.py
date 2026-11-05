#!/usr/bin/env python3
"""Replay all 198 photos through production Android modules into a new directory."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

REPO=Path(__file__).resolve().parents[1]
DATA=REPO/'Build/Testing'
PACKAGE='com.unimagdalena.assistivevision'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--app',type=Path,required=True)
    p.add_argument('--sdk',type=Path,help='Android SDK directory; defaults to ANDROID_HOME or ~/Android/Sdk')
    p.add_argument('--serial',required=True,help='Authorized adb device serial, e.g. emulator-5554')
    p.add_argument('--output',type=Path,default=REPO/'development/runs'/('android-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')))
    p.add_argument('--allow-different-source',action='store_true',help='Allow an exploratory run with changed production modules/model')
    a=p.parse_args();a.app=a.app.resolve();a.output=a.output.resolve()
    sdk=(a.sdk or Path(os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT') or Path.home()/'Android/Sdk')).resolve()
    adb=sdk/'platform-tools'/('adb.exe' if os.name=='nt' else 'adb')
    if not adb.is_file():p.error(f'Install Android SDK Platform-Tools or pass --sdk; adb missing at {adb}')
    if a.output.exists():p.error('Output exists; select a new directory. Existing results are never overwritten.')
    if a.output==REPO or a.output==DATA or DATA in a.output.parents:p.error('Output must be outside Build/Testing.')
    if not (a.app/'settings.gradle.kts').is_file():p.error('--app must point to the AssistiveVision project root.')
    archived=json.loads((DATA/'provenance/android_run_metadata.json').read_text())
    source_hashes={name:sha256(a.app/name) for name in archived['source_hashes']}
    model=a.app/'app/src/main/assets/efficientdet-lite2-detection-metadata.tflite'
    same_source=source_hashes==archived['source_hashes'] and sha256(model)==archived['model_sha256']
    if not same_source and not a.allow_different_source:p.error('Production source/model differ from the archived run. Use the documented app commit, or explicitly allow an exploratory run.')
    subprocess.run([sys.executable,str(REPO/'scripts/verify_archive.py')],check=True)
    base=[str(adb),'-s',a.serial]
    devices=subprocess.check_output([str(adb),'devices'],text=True)
    if a.serial not in [line.split()[0] for line in devices.splitlines() if line.endswith('\tdevice')]:
        p.error('Device is absent or unauthorized. Check adb devices and accept USB debugging on the device.')
    test=a.app/'app/src/androidTest/java/com/unimagdalena/assistivevision/DatasetBenchmarkTest.kt'
    exact_test=DATA/'benchmark/android/DatasetBenchmarkTest.kt'
    if test.exists() and test.read_bytes()!=exact_test.read_bytes():p.error('Existing DatasetBenchmarkTest.kt differs; preserve it and use a separate app checkout.')
    if not test.exists():test.parent.mkdir(parents=True,exist_ok=True);test.write_bytes(exact_test.read_bytes())
    a.output.mkdir(parents=True)
    env=dict(os.environ,ANDROID_HOME=str(sdk),ANDROID_SDK_ROOT=str(sdk))
    def call(cmd,**kwargs):
        print('+ '+' '.join(map(str,cmd)),flush=True)
        return subprocess.run(list(map(str,cmd)),check=True,**kwargs)
    wrapper=a.app/('gradlew.bat' if os.name=='nt' else 'gradlew')
    call([wrapper,'--no-daemon','--max-workers=2',':app:assembleDebug',':app:assembleDebugAndroidTest'],cwd=a.app,env=env)
    for apk in (a.app/'app/build/outputs/apk/debug/app-debug.apk',a.app/'app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'):
        call(base+['install','-r','-t',str(apk)])
    # Only the benchmark workspace inside the app is changed. Never uninstall on
    # signing conflicts, as uninstalling would erase user settings and app data.
    with tempfile.TemporaryDirectory(prefix='assistivevision-android-') as temp:
        archive=Path(temp)/'dataset.tar'
        with tarfile.open(archive,'w') as tf:
            tf.add(DATA/'labels.json',arcname='labels.json')
            for path in sorted((DATA/'data').glob('*.jpeg')):tf.add(path,arcname='data/'+path.name)
        call(base+['shell','run-as',PACKAGE,'mkdir','-p','files/benchmark'])
        with archive.open('rb') as stream:
            call(base+['exec-in','run-as',PACKAGE,'tar','-xf','-','-C','files/benchmark'],stdin=stream)
    call(base+['shell','run-as',PACKAGE,'rm','-f','files/benchmark/android.json'])
    cmd=base+['shell','am','instrument','-w','-r','-e','class',PACKAGE+'.DatasetBenchmarkTest','-e','confidence','0.30','-e','maxObjects','2',PACKAGE+'.test/androidx.test.runner.AndroidJUnitRunner']
    result=subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (a.output/'android-instrumentation.log').write_text(result.stdout)
    print(result.stdout)
    if 'OK (1 test)' not in result.stdout or any(x in result.stdout for x in ('FAILURES!!!','INSTRUMENTATION_FAILED')):
        raise SystemExit('Instrumentation did not pass. See the log in the new output directory.')
    run=json.loads(subprocess.check_output(base+['exec-out','run-as',PACKAGE,'cat','files/benchmark/android.json']))
    gt=json.loads((DATA/'labels.json').read_text())
    frames=run['frames'];expected={im['id']:im['file_name'] for im in gt['images']}
    if len(frames)!=198 or {f['image_id']:f['file_name'] for f in frames}!=expected:
        raise SystemExit('Incomplete, duplicate or mismatched frame results.')
    if run['metadata']['model_sha256']!=sha256(model) or run['metadata']['gt_sha256']!=sha256(DATA/'labels.json'):
        raise SystemExit('Android input hashes do not match this checkout.')
    def device_property(name):return subprocess.check_output(base+['shell','getprop',name],text=True).strip()
    meta=run['metadata'];meta.update(
        app_commit=subprocess.check_output(['git','-C',str(a.app),'rev-parse','HEAD'],text=True).strip(),
        build='debug instrumentation; production inference modules',source_hashes=source_hashes,
        android_fingerprint=device_property('ro.build.fingerprint'),abi=device_property('ro.product.cpu.abi'),
        device_kind='emulator' if device_property('ro.kernel.qemu')=='1' else 'physical',
        production_source_matches_archive=same_source,
        instrumentation_sha256=sha256(test))
    if meta['device_kind']=='emulator':meta['avd']=subprocess.check_output(base+['emu','avd','name'],text=True).splitlines()[0]
    output=a.output/'android.json';output.write_text(json.dumps(run,indent=2)+'\n')
    call([sys.executable,DATA/'benchmark/evaluate.py',output,'--output',a.output/'metrics'],env=env)
    original=json.loads((DATA/'benchmark/results/android.json').read_text())
    reference_frames={f['image_id']:f for f in original['frames']}
    identical=sum(f['predictions']==reference_frames[f['image_id']]['predictions'] for f in frames)
    def summary_without_timing(path):
        with path.open(newline='') as stream:
            return [{k:v for k,v in row.items() if k not in ('inference_median_ms','inference_p95_ms')}
                    for row in csv.DictReader(stream)]
    comparison=dict(frames=198,frames_with_identical_prediction_arrays=identical,
        all_predictions_exactly_equal=identical==198,
        summary_equal_excluding_timing=summary_without_timing(a.output/'metrics/summary.csv')==summary_without_timing(DATA/'benchmark/results/android/summary.csv'),
        production_source_matches_archive=same_source,
        timing_comparison='New measurements; equality with archived emulator timings is not required.',
        reference_app_commit=archived['app_commit'],new_app_commit=meta['app_commit'])
    (a.output/'comparison_to_archive.json').write_text(json.dumps(comparison,indent=2)+'\n')
    print(f'Prediction arrays identical to reference: {identical}/198')
    print(f'Completed 198 frames. New predictions and metrics: {a.output}')


if __name__=='__main__':main()
