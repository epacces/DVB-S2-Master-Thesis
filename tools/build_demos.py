#!/usr/bin/env python3
"""Export the marimo notebooks in demos/ to WebAssembly pages under _site/demos/.

Usage:  python tools/build_demos.py      (after tools/build_site.py)

Needs marimo, uv and build (pip install marimo uv build).  Each notebook goes
to _site/demos/<name>/index.html together with the dvbs2 wheel, which the
notebook installs with micropip when it runs in the browser.  The BER explorer
also gets the simulation results from sim/results/.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "_site" / "demos"


def main():
    SITE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, "-m", "build", "--wheel", "--outdir", tmp, str(ROOT / "sim")], check=True,
                       stdout=subprocess.DEVNULL)
        wheel = next(pathlib.Path(tmp).glob("dvbs2-*.whl"))
        notebooks = sorted(ROOT.glob("demos/[0-9][0-9]_*.py"))
        for nb in notebooks:
            out = SITE / nb.stem
            if out.exists():
                shutil.rmtree(out)
            subprocess.run([sys.executable, "-m", "marimo", "export", "html-wasm", str(nb), "-o", str(out),
                            "--mode", "run", "-f"], check=True)
            (out / "CLAUDE.md").unlink(missing_ok=True)
            shutil.copy2(wheel, out / wheel.name)
        results = sorted((ROOT / "sim" / "results").glob("*.json"))
        dest = SITE / "08_ber_explorer" / "results"
        if dest.parent.exists():
            dest.mkdir(exist_ok=True)
            for path in results:
                shutil.copy2(path, dest / path.name)
            (dest / "index.json").write_text(json.dumps([p.name for p in results]))
    for build in (ROOT / "sim" / "build", *ROOT.glob("sim/src/*.egg-info")):
        shutil.rmtree(build, ignore_errors=True)
    print("wrote %d notebooks to %s (%d result files)" % (len(notebooks), SITE.relative_to(ROOT), len(results)))


if __name__ == "__main__":
    main()
