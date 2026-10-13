"""Verify all archived files against the package checksum manifest."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main():
    manifest = json.loads((ROOT / 'SHA256SUMS.json').read_text())
    failures = []
    for name, expected in manifest.items():
        path = ROOT / name
        if not path.is_file():
            failures.append(f'Missing: {name}')
        elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            failures.append(f'Changed: {name}')
    if failures:
        raise SystemExit('\n'.join(failures))
    print(f'OK: {len(manifest)} files match the archived SHA-256 checksums.')

if __name__ == '__main__':
    main()
