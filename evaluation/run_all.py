import subprocess
import sys
from pathlib import Path

def run(cmd):
    print(f"\n▶ Running: {cmd}")
    base_dir = Path(__file__).resolve().parent
    r = subprocess.run([sys.executable, cmd], check=False, cwd=base_dir)
    if r.returncode != 0:
        raise SystemExit(r.returncode)

def main():
    run("generate_candidates_from_api.py")
    run("eval_rouge.py")
    run("eval_bertscore.py")

if __name__ == "__main__":
    main()
