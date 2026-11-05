#!/usr/bin/env python3
"""Verify the original 570-file benchmark after documented path relocations."""
import hashlib
import json
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
DATA=REPO/'Build/Testing'


def resolve_original(name,relocations):
    original='Build/Testing/'+name
    record=relocations.get(original)
    destination=record['destination'] if record else original
    path=(REPO/destination).resolve()
    if not path.is_relative_to(REPO):
        raise ValueError('Archive path escapes the repository: '+destination)
    return path


def verify():
    manifest=json.loads((DATA/'SHA256SUMS.json').read_text())
    relocations=json.loads((REPO/'development/relocations.json').read_text())['files']
    failures=[];moved=0
    for name,expected in manifest.items():
        path=resolve_original(name,relocations)
        if path!=DATA/name:moved+=1
        if not path.is_file():failures.append('Missing: '+str(path.relative_to(REPO)))
        elif hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            failures.append('Changed: '+str(path.relative_to(REPO)))
    if failures:raise SystemExit('\n'.join(failures))
    print(f'OK: {len(manifest)} original files match archived SHA-256 checksums ({moved} relocated).')
    return len(manifest),moved


if __name__=='__main__':verify()
