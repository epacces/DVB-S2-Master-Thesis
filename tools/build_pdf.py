#!/usr/bin/env python3
"""Rebuild TESI_FINALE.pdf from the LaTeX sources with Tectonic.

Usage:  python3 tools/build_pdf.py          (writes tools/build/pdf/master.pdf)
        python3 tools/build_pdf.py --install (also copies it to TESI_FINALE.pdf)

Tectonic (brew install tectonic) is a XeTeX-based engine that downloads the
packages it needs.  The sources were written in 2008 for latex + an older
toptesi class, so they are built from a patched copy in tools/build/pdf:
cp1252 is converted to UTF-8 and the incompatibilities are worked around
below.  The sources themselves are not modified.
"""
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / "tools" / "build" / "pdf"

COPY = ["*.tex", "*.sty", "*.bib", "*.c", "*.jpg", "*.pdf"]


def utf8(path):
    return path.read_bytes().decode("cp1252").replace("\r\n", "\n")


def patch_master(text):
    # toptesi now handles languages itself (polyglossia under XeTeX).  Keep the
    # 2008 front-matter headings: Sommario, Acknowledgements, Contents.
    text = re.sub(r"\\usepackage\[(?:italian|english|T1)\]\{(?:babel|fontenc)\}\n", "", text)
    text = text.replace("\\begin{document}\n",
                        "\\ExtendCaptions{italian}{Sommario}{Acknowledgements}\n"
                        "\\gappto\\captionsitalian{\\renewcommand*{\\contentsname}{Contents}}\n"
                        "\\begin{document}\n", 1)
    # \DeclareMathSymbol on the "letters" family has no font under XeTeX.
    text = text.replace(r'\DeclareMathSymbol{\virgola}{\mathpunct}{letters}{"3B}',
                        r"\providecommand{\virgola}{\mathpunct{,}}")
    text = text.replace(r'\DeclareMathSymbol{\decimalcomma}{\mathord}{letters}{"3B}',
                        r"\providecommand{\decimalcomma}{\mathord{,}}")
    # The title-page fields now go inside the frontespizio environment.
    text = text.replace("\\frontespizio\n",
                        "\\begin{frontespizio}\n\\input{frontmatter}\n\\end{frontespizio}\n", 1)
    # Tectonic only runs BibTeX when \bibdata is in master.aux, not in an \include's aux.
    text = text.replace("\\include{bibliografy}", "\\clearpage\n\\input{bibliografy}")
    return text


def patch_chapter(text):
    # align nested in equation: old amsmath silently recovered with aligned.
    return re.sub(r"\\begin\{equation\}(\s*)\\begin\{align\}(.*?)\\end\{align\}(\s*)\\end\{equation\}",
                  r"\\begin{equation}\1\\begin{aligned}\2\\end{aligned}\3\\end{equation}", text, flags=re.S)


def main():
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    for pattern in COPY:
        for src in ROOT.glob(pattern):
            if src.suffix == ".tex":
                text = utf8(src)
                text = patch_master(text) if src.name == "master.tex" else patch_chapter(text)
                (BUILD / src.name).write_text(text, encoding="utf-8")
            else:
                shutil.copy2(src, BUILD / src.name)
    shutil.copytree(ROOT / "schemi", BUILD / "schemi")
    shutil.copytree(ROOT / "figures", BUILD / "figures")
    # tikz looks for tikzlibrary<name>.code.tex.
    for lib in ROOT.glob("pgflibrarytikz*.code.tex"):
        (BUILD / lib.name.replace("pgflibrarytikz", "tikzlibrary")).write_text(utf8(lib), encoding="utf-8")
    (BUILD / "frontmatter.tex").write_text(utf8(ROOT / "toptesi.cfg").replace("\\endinput", ""), encoding="utf-8")

    subprocess.run(["tectonic", "-X", "compile", "--keep-logs", "master.tex"], cwd=BUILD, check=True)
    print("wrote", (BUILD / "master.pdf").relative_to(ROOT))
    if "--install" in sys.argv:
        shutil.copy2(BUILD / "master.pdf", ROOT / "TESI_FINALE.pdf")
        print("copied to TESI_FINALE.pdf")


if __name__ == "__main__":
    main()
