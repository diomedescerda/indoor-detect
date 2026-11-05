#!/usr/bin/env python3
"""Recover the six exact model binaries retained in this repository's Git history."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

REPO=Path(__file__).resolve().parents[1]


def recover(output):
    manifest=json.loads((REPO/'docs/historical-models.json').read_text())
    # Never fetch silently or overwrite a file supplied by the user.
    available=subprocess.run(['git','cat-file','-e',manifest['commit']+'^{commit}'],cwd=REPO,capture_output=True)
    if available.returncode:
        raise SystemExit('The historical commit is absent (possibly a shallow clone). Fetch the full repository history with git fetch --unshallow, then retry.')
    output=output.resolve();output.mkdir(parents=True,exist_ok=True)
    for name,record in manifest['models'].items():
        target=output/name
        if target.exists():
            data=target.read_bytes()
        else:
            data=subprocess.check_output(['git','show',manifest['commit']+':'+record['git_path']],cwd=REPO)
        if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256']:
            raise SystemExit(f'Historical model checksum mismatch: {name}; no existing file was replaced.')
        if not target.exists():target.write_bytes(data)
    print(f'OK: six exact historical models available at {output}')
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=REPO/'development/runs/historical-models')
    recover(parser.parse_args().output)
