"""Compatibility entry point; validation reports are written only with --output."""
from pathlib import Path
import runpy

if __name__=='__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[2]/'scripts/validate_ground_truth.py'),run_name='__main__')
