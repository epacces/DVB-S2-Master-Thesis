#!/usr/bin/env python3
"""Build the GitHub Pages site (_site/) from the Markdown chapters.

Usage:  python3 tools/build_site.py

Each markdown/NN-*.md becomes NN-*.html with a chapter sidebar; math is
rendered by MathJax.  Images and the PDF are copied next to the pages.
"""
import html
import json
import pathlib
import re
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
MD = ROOT / "markdown"
SITE = ROOT / "_site"
TOOLS = ROOT / "tools" / "site"


def sidebar(chapters, current):
    items = []
    for ch in chapters:
        label = html.escape(("%s&nbsp; " % ch["number"] if ch["number"] else "") + ch["title"]).replace("&amp;nbsp;", "&nbsp;")
        cls = ' class="current"' if ch["file"] == current else ""
        items.append('<li%s><a href="%s">%s</a></li>' % (cls, ch["file"][:-3] + ".html", label))
    return "<ol>%s</ol>" % "".join(items)


def pandoc(src, dest, title, extra):
    args = ["pandoc", str(src), "-f", "gfm", "-t", "html5", "--standalone", "--mathjax",
            "--template", str(TOOLS / "template.html"),
            "--lua-filter", str(TOOLS / "links.lua"),
            "--metadata", "pagetitle=" + title, "-o", str(dest)]
    for key, value in extra.items():
        args += ["--variable", "%s=%s" % (key, value)]
    subprocess.run(args, check=True)


def main():
    chapters = json.loads((MD / "chapters.json").read_text())
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()

    # Previous/next links come from the footer tex2md.py writes in each chapter.
    for ch in chapters:
        pandoc(MD / ch["file"], SITE / (ch["file"][:-3] + ".html"), ch["title"],
               {"sidebar": sidebar(chapters, ch["file"])})
    pandoc(MD / "README.md", SITE / "index.html", "BCH-LDPC Concatenated Coding",
           {"sidebar": sidebar(chapters, None)})
    # Landing page of the interactive demos (the notebooks are exported by tools/build_demos.py).
    pandoc(ROOT / "demos" / "index.md", SITE / "demos.html", "Interactive demos",
           {"sidebar": sidebar(chapters, None)})

    # Everything the chapters link to with ../ (images, the PDF).
    used = set()
    for ch in list(chapters) + [{"file": "README.md"}]:
        used.update(re.findall(r"\]\(\.\./([^)#]+)\)", (MD / ch["file"]).read_text()))
    for rel in sorted(used):
        (SITE / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, SITE / rel)
    for name in ("style.css", "site.js"):
        shutil.copy2(TOOLS / name, SITE / name)
    (SITE / ".nojekyll").touch()
    print("wrote %s (%d pages, %d files)" % (SITE.relative_to(ROOT), len(chapters) + 2, len(used)))


if __name__ == "__main__":
    main()
