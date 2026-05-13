import subprocess
import sys
from pathlib import Path

def run(args):
    print(f"\nRunning: {' '.join(args)}", flush=True)
    base_dir = Path(__file__).resolve().parent
    r = subprocess.run([sys.executable, *args], check=False, cwd=base_dir)
    if r.returncode != 0:
        raise SystemExit(r.returncode)

def main():
    run(["test_pertanyaan_dokumen.py", *sys.argv[1:]])

if __name__ == "__main__":
    main()
