"""Build/install the app benchmark, stage photos, run Android replay, collect results."""
import argparse, hashlib, json, os, shutil, subprocess, tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
PACKAGE='com.unimagdalena.assistivevision'

def main():
    p=argparse.ArgumentParser();p.add_argument('--app',type=Path,required=True,help='Path to the AssistiveVision Android checkout')
    p.add_argument('--sdk',type=Path);p.add_argument('--serial');p.add_argument('--confidence',type=float);p.add_argument('--max-objects',type=int);p.add_argument('--skip-build',action='store_true',help='Use APKs already built from this checkout')
    a=p.parse_args();sdk=a.sdk or Path(os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT') or Path.home()/'Android/Sdk')
    adb=sdk/'platform-tools/adb'
    if not adb.exists():raise SystemExit(f'Android SDK platform-tools missing at {sdk}. Finish Android Studio SDK setup or pass --sdk PATH.')
    env=os.environ.copy();env['ANDROID_HOME']=str(sdk);env['ANDROID_SDK_ROOT']=str(sdk)
    env.setdefault('GRADLE_USER_HOME',str(Path.home()/'.gradle'))
    jbr=Path('/opt/android-studio/jbr')
    if jbr.exists():env['JAVA_HOME']=str(jbr)
    base=[str(adb)] + (['-s',a.serial] if a.serial else [])
    devices=subprocess.check_output([str(adb),'devices'],text=True)
    attached=[line.split()[0] for line in devices.splitlines()[1:] if line.strip().endswith('\tdevice')]
    if a.serial and a.serial not in attached:raise SystemExit('Requested phone is not connected/authorized. Check the USB-debugging prompt.')
    if not a.serial and len(attached)!=1:raise SystemExit('Connect exactly one authorized Android device, or pass --serial.\n'+devices)
    def call(cmd,**kw):subprocess.run(cmd,check=True,**kw)
    test=a.app/'app/src/androidTest/java/com/unimagdalena/assistivevision/DatasetBenchmarkTest.kt'
    if not test.exists():raise SystemExit('DatasetBenchmarkTest.kt has not been installed into this checkout.')
    if not a.skip_build:
        call([str(a.app/'gradlew'),'--max-workers=2',':app:assembleDebug',':app:assembleDebugAndroidTest'],cwd=a.app,env=env)
    (ROOT/'benchmark/results').mkdir(parents=True,exist_ok=True)
    # Do not uninstall on signature mismatch: that would erase the existing app's settings/data.
    call(base+['install','-r',str(a.app/'app/build/outputs/apk/debug/app-debug.apk')])
    call(base+['install','-r',str(a.app/'app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk')])
    archive=ROOT/'benchmark/dataset.tar'
    with tarfile.open(archive,'w') as tf:
        tf.add(ROOT/'labels.json',arcname='labels.json')
        for path in sorted((ROOT/'data').glob('*.jpeg')):tf.add(path,arcname='data/'+path.name)
    call(base+['shell','run-as',PACKAGE,'mkdir','-p','files/benchmark'])
    with archive.open('rb') as src:call(base+['exec-in','run-as',PACKAGE,'tar','-xf','-','-C','files/benchmark'],stdin=src)
    # Ensure a failed test cannot accidentally return a stale successful result.
    call(base+['shell','run-as',PACKAGE,'rm','-f','files/benchmark/android.json'])
    cmd=base+['shell','am','instrument','-w','-r','-e','class',PACKAGE+'.DatasetBenchmarkTest']
    if a.confidence is not None:cmd+=['-e','confidence',str(a.confidence)]
    if a.max_objects is not None:cmd+=['-e','maxObjects',str(a.max_objects)]
    cmd += [PACKAGE+'.test/androidx.test.runner.AndroidJUnitRunner']
    result=subprocess.run(cmd,check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (ROOT/'benchmark/results/android-instrumentation.log').write_text(result.stdout)
    print(result.stdout)
    if 'FAILURES!!!' in result.stdout or 'INSTRUMENTATION_FAILED' in result.stdout or 'OK (1 test)' not in result.stdout:
        raise SystemExit('Android test did not confirm success. See android-instrumentation.log.')
    raw=subprocess.check_output(base+['exec-out','run-as',PACKAGE,'cat','files/benchmark/android.json'])
    run=json.loads(raw);assert len(run['frames'])==198
    model=a.app/'app/src/main/assets/efficientdet-lite2-detection-metadata.tflite'
    assert run['metadata']['model_sha256']==hashlib.sha256(model.read_bytes()).hexdigest()
    run['metadata']['app_commit']=subprocess.check_output(['git','-C',str(a.app),'rev-parse','HEAD'],text=True).strip()
    run['metadata']['build']='debug instrumentation; production inference modules'
    run['metadata']['device_kind']='emulator' if subprocess.check_output(base+['shell','getprop','ro.kernel.qemu'],text=True).strip()=='1' else 'physical'
    run['metadata']['android_fingerprint']=subprocess.check_output(base+['shell','getprop','ro.build.fingerprint'],text=True).strip()
    run['metadata']['abi']=subprocess.check_output(base+['shell','getprop','ro.product.cpu.abi'],text=True).strip()
    if run['metadata']['device_kind']=='emulator':
        run['metadata']['avd']=subprocess.check_output(base+['emu','avd','name'],text=True).splitlines()[0]
    source_root=a.app/'app/src/main/java/com/unimagdalena/assistivevision'
    run['metadata']['source_hashes']={str(f.relative_to(a.app)):hashlib.sha256(f.read_bytes()).hexdigest() for f in source_root.rglob('*.kt') if f.name in ['PreprocessingModule.kt','DetectionModule.kt','LetterboxMapper.kt','MainViewModel.kt','SettingsManager.kt']}
    output=ROOT/'benchmark/results/android.json';output.write_text(json.dumps(run,indent=2)+'\n');print(output)
    call([str(ROOT/'benchmark/.venv/bin/python'),str(ROOT/'benchmark/evaluate.py'),str(output)])

if __name__=='__main__':main()
