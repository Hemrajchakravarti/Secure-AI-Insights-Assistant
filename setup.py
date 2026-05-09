# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
setup.py  -  Run this ONCE before starting the app.

  python setup.py

Steps:
  1. Checks your Python version (needs 3.10+)
  2. Deletes any stale .venv, creates a fresh one using the CURRENT Python
  3. Installs all Python packages
  4. Generates mock CSV files + SQLite database
  5. Generates PDF text content + ingests into ChromaDB
  6. Installs frontend npm dependencies
"""

import os, sys, subprocess, shutil

# Force UTF-8 on Windows (prevents cp1252 UnicodeEncodeError)
os.environ["PYTHONUTF8"] = "1"

# ── 0. Python version gate ─────────────────────────────────────────────────
MIN = (3, 10)
cur = sys.version_info[:2]
if cur < MIN:
    print(f"""
============================================================
  [ERROR] Python {cur[0]}.{cur[1]} detected  -  need 3.10+
============================================================

  Running from: {sys.executable}

  Fix (Anaconda users):
    conda create -n insights python=3.11
    conda activate insights
    python setup.py
""")
    sys.exit(1)

print(f"  Python {cur[0]}.{cur[1]} OK  ({sys.executable})")

IS_WIN = os.name == "nt"
ROOT   = os.path.dirname(os.path.abspath(__file__))
BACK   = os.path.join(ROOT, "backend")
FRONT  = os.path.join(ROOT, "frontend")
VENV   = os.path.join(BACK, ".venv")
PY     = sys.executable   # the verified 3.10+ Python


def venv_py():
    """Path to the venv's python executable."""
    if IS_WIN:
        return os.path.join(VENV, "Scripts", "python.exe")
    return os.path.join(VENV, "bin", "python")


def run(cmd, cwd=None):
    print(f"\n  $ {' '.join(str(c) for c in cmd)}")
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        print(f"\n[ERROR] Command failed (exit {r.returncode}).")
        sys.exit(r.returncode)


def step(n, title):
    print(f"\n{'='*60}\n  {n}  {title}\n{'='*60}")


# ── 1. Virtual environment ─────────────────────────────────────────────────
step("1/5", "Creating Python virtual environment")

# Always check the venv Python version.
# If it exists but is the wrong version, delete and recreate.
if os.path.exists(VENV):
    vpy = venv_py()
    if os.path.exists(vpy):
        r = subprocess.run(
            [vpy, "-c",
             "import sys; v=sys.version_info[:2]; exit(0 if v>=(3,10) else 1)"],
            capture_output=True
        )
        if r.returncode != 0:
            print(f"  Stale .venv is Python <3.10  -  deleting it...")
            shutil.rmtree(VENV)
        else:
            # Check it was made from the SAME python as we're running now
            r2 = subprocess.run(
                [vpy, "-c", "import sys; print(sys.executable)"],
                capture_output=True, text=True
            )
            venv_base = os.path.normcase(os.path.dirname(r2.stdout.strip()))
            cur_base  = os.path.normcase(os.path.dirname(PY))
            if venv_base != cur_base:
                print(f"  .venv was built from a different Python  -  deleting it...")
                print(f"    venv Python: {r2.stdout.strip()}")
                print(f"    current:     {PY}")
                shutil.rmtree(VENV)
            else:
                print("  .venv is current and compatible  -  skipping creation.")
    else:
        print("  Incomplete .venv found  -  deleting it...")
        shutil.rmtree(VENV)

if not os.path.exists(VENV):
    run([PY, "-m", "venv", VENV])
    print("  Virtual environment created.")

VP = venv_py()
if not os.path.exists(VP):
    print(f"[ERROR] venv python not found: {VP}")
    sys.exit(1)

# ── 2. Install packages ────────────────────────────────────────────────────
step("2/5", "Installing Python packages (2-4 min on first run)")
run([VP, "-m", "pip", "install", "--upgrade", "pip",
     "--quiet", "--no-warn-script-location"])
run([VP, "-m", "pip", "install", "-r",
     os.path.join(BACK, "requirements.txt")])

# ── 3. CSV + SQLite ────────────────────────────────────────────────────────
step("3/5", "Generating mock CSV data + SQLite database")
run([VP, os.path.join(BACK, "scripts", "generate_mock_data.py")])

# ── 4. PDFs + ChromaDB ────────────────────────────────────────────────────
step("4/5", "Generating PDF texts + ingesting into ChromaDB")
print("  Note: downloads ~90 MB sentence-transformer model on first run.")
run([VP, os.path.join(BACK, "scripts", "generate_pdfs.py")])

# ── 5. npm install ────────────────────────────────────────────────────────
step("5/5", "Installing frontend npm packages")
npm = shutil.which("npm")
if npm is None:
    print("  [WARN] npm not found  -  skipping.")
    print("  Install Node.js 18+ from https://nodejs.org")
    print("  Then: cd frontend && npm install")
else:
    if IS_WIN:
        r = subprocess.run("npm install", cwd=FRONT, shell=True)
        if r.returncode != 0:
            sys.exit(r.returncode)
    else:
        run([npm, "install"], cwd=FRONT)

step("DONE", "Setup complete!")
print("""
Next steps:
  1. Add your API key:
       copy .env.example .env    (Windows)
       cp .env.example .env      (Mac/Linux)
     Then open .env and set ANTHROPIC_API_KEY=sk-ant-...

  2. Start:
       Windows:    start.bat
       Mac/Linux:  ./start.sh

  Frontend  ->  http://localhost:5173
  Backend   ->  http://localhost:8000
  Docs      ->  http://localhost:8000/docs
""")
