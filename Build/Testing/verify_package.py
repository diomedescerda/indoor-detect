"""Compatibility entry point for the relocation-aware archive verifier."""
from pathlib import Path
import runpy

if __name__=='__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[2]/'scripts/verify_archive.py'),run_name='__main__')
