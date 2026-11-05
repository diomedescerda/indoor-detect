#!/usr/bin/env python3
"""Regenerate the archived analyses in isolation and check every generated CSV."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / 'Build/Testing'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_csv(actual, expected):
    """Compare full tables, including text, empty cells, row order and floats."""
    with actual.open(newline='') as a, expected.open(newline='') as e:
        left, right = list(csv.reader(a)), list(csv.reader(e))
    if len(left) != len(right):
        raise ValueError(f'{actual.name}: row count differs ({len(left)} != {len(right)})')
    for row, (a, e) in enumerate(zip(left, right), 1):
        if len(a) != len(e):
            raise ValueError(f'{actual.name}: column count differs at row {row}')
        for column, (x, y) in enumerate(zip(a, e), 1):
            if x == y:
                continue
            try:
                same = math.isclose(float(x), float(y), rel_tol=1e-10, abs_tol=1e-12)
            except ValueError:
                same = False
            if not same:
                raise ValueError(f'{actual.name}: row {row}, column {column}: {x!r} != {y!r}')
    return dict(rows=max(0, len(left)-1), sha256=sha256(actual),
                archived_sha256=sha256(expected))


def run(command, log, env):
    print('+ ' + ' '.join(map(str, command)), flush=True)
    result = subprocess.run(list(map(str, command)), cwd=REPO, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log.write(result.stdout)
    log.flush()
    if result.returncode:
        print(result.stdout, file=sys.stderr)
        raise RuntimeError(f'Command failed ({result.returncode}); see reproduction.log')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=REPO/'development/runs/saved-results')
    parser.add_argument('--overlays', action='store_true', help='Also render 198 prediction overlays')
    args = parser.parse_args()
    output = args.output.resolve()
    # Refuse overwrites, including all archived input/output directories.
    if output == REPO or DATA == output or DATA in output.parents:
        parser.error('Choose an output outside Build/Testing and outside the repository root itself.')
    if output.exists():
        parser.error('Output already exists. Choose a new --output directory; archived results are never overwritten.')
    for package in ('numpy', 'pillow', 'pycocotools', 'matplotlib'):
        try:
            importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            parser.error(f'Missing {package}. Install requirements-analysis.lock.txt with this Python interpreter.')
    output.mkdir(parents=True)
    report = dict(status='running',python=sys.version, csv_tables={}, json_files={},
                  packages={p:importlib.metadata.version(p) for p in ('numpy','pillow','pycocotools','matplotlib')},
                  inputs={str(p.relative_to(REPO)):sha256(p) for p in (
                      DATA/'labels.json',DATA/'benchmark/results/android.json',
                      DATA/'benchmark/models/efficientdet-lite2-detection-metadata.tflite',
                      DATA/'occlusion/author_review.json',DATA/'occlusion/labels_batch_1.json',
                      DATA/'occlusion/labels_batch_2.json', REPO/'requirements-analysis.lock.txt')},
                  numerical_tolerance=dict(relative=1e-10,absolute=1e-12))
    try:
        with (output/'reproduction.log').open('w') as log, tempfile.TemporaryDirectory(prefix='assistivevision-') as temp:
            work=Path(temp)/'Testing'
            (work/'benchmark/results').mkdir(parents=True)
            (work/'occlusion').mkdir()
            # The original scripts derive paths from __file__. Copying them into a
            # temporary workspace preserves that behavior without changing the archive.
            for script in (DATA/'benchmark').glob('*.py'):
                shutil.copy2(script,work/'benchmark'/script.name)
            for source in (DATA/'data',DATA/'labels.json'):
                destination=work/source.name
                try:
                    destination.symlink_to(source, target_is_directory=source.is_dir())
                except OSError:  # Windows without symlink privileges
                    if source.is_dir():shutil.copytree(source,destination)
                    else:shutil.copy2(source,destination)
            shutil.copy2(DATA/'benchmark/results/android.json',work/'benchmark/results/android.json')
            for source in (DATA/'occlusion').glob('*.json'):
                shutil.copy2(source,work/'occlusion'/source.name)
            env=dict(os.environ,MPLBACKEND='Agg',MPLCONFIGDIR=str(Path(temp)/'matplotlib'))
            commands=[
                [sys.executable,REPO/'scripts/verify_archive.py'],
                [sys.executable,REPO/'scripts/validate_ground_truth.py',DATA/'labels.json'],
                [sys.executable,'-m','unittest','discover','-s',DATA/'benchmark','-p','test_*.py'],
                [sys.executable,work/'benchmark/evaluate.py',work/'benchmark/results/android.json'],
                [sys.executable,work/'benchmark/analyze_effects.py',work/'benchmark/results/android'],
                [sys.executable,work/'benchmark/analyze_scenes.py'],
                [sys.executable,work/'benchmark/plot_scenario1.py'],
                [sys.executable,work/'benchmark/analyze_depth.py',work/'benchmark/results/android.json'],
                [sys.executable,work/'benchmark/analyze_occlusion.py'],
                [sys.executable,REPO/'scripts/analyze_brightness.py','--output',output/'brightness'],
            ]
            if args.overlays:
                commands.append([sys.executable,work/'benchmark/render_predictions.py',work/'benchmark/results/android.json'])
            for command in commands:
                run(command,log,env)
            shutil.copytree(work/'benchmark/results/android',output/'android')
            shutil.copytree(work/'occlusion/results',output/'occlusion')
            for generated,reference in ((output/'android',DATA/'benchmark/results/android'),
                                        (output/'occlusion',DATA/'occlusion/results')):
                actual_tables={p.relative_to(generated) for p in generated.rglob('*.csv')}
                expected_tables={p.relative_to(reference) for p in reference.rglob('*.csv')}
                if actual_tables != expected_tables:
                    raise ValueError(f'CSV table inventory differs: {actual_tables ^ expected_tables}')
                for relative in sorted(actual_tables):
                    report['csv_tables'][str((generated/relative).relative_to(output))]=compare_csv(generated/relative,reference/relative)
            report['csv_tables']['brightness/brightness_per_image.csv']=compare_csv(
                output/'brightness/brightness_per_image.csv',REPO/'Build/Testing/benchmark/results/brightness/brightness_per_image.csv')
            for name in ('summary.json','image_sha256.json'):
                actual=output/'brightness'/name
                reference=REPO/'Build/Testing/benchmark/results/brightness'/name
                if json.loads(actual.read_text())!=json.loads(reference.read_text()):
                    raise ValueError(f'Brightness evidence JSON differs: {name}')
                report['json_files']['brightness/'+name]=dict(sha256=sha256(actual),archived_sha256=sha256(reference))
            # Verify the archive again, after all regeneration steps.
            run([sys.executable,REPO/'scripts/verify_archive.py'],log,env)
            report['status']='passed'
    except Exception as exc:
        report['status']='failed';report['error']=str(exc)
        raise
    finally:
        (output/'reproduction_report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f"PASS: {len(report['csv_tables'])} full CSV tables match the archive. Outputs: {output}")


if __name__ == '__main__':
    main()
