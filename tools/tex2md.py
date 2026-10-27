#!/usr/bin/env python3
"""Convert the LaTeX thesis into one Markdown file per chapter (markdown/).

Usage:  python3 tools/tex2md.py

The LaTeX sources are cp1252-encoded and use packages pandoc cannot parse
(toptesi, signalflowdiagram, gnuplot-lua-tikz, subfig).  This script
flattens master.tex into a single pandoc-friendly LaTeX document, replaces
the TikZ diagrams with PNG crops of the final PDF (figures/), runs pandoc
with tools/number.lua (chapter-based numbering of figures, tables and
equations, as in the PDF) and splits the result into chapters.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "markdown"
TOOLS = ROOT / "tools"

# Chapters in the order master.tex includes them.
PARTS = ["preliminari", "riassunto", "cap1", "cap2", "cap3", "cap4", "cap5",
         "cap6", "ldpcdec", "conclusioni", "Basic"]

# Figures drawn with TikZ/gnuplot, keyed by their \label.  The PNGs are
# cropped from TESI_FINALE.pdf (pages 52, 53, 56, 88, 97, 98, 101).
TIKZ_FIGURES = {
    "fig:Q8PSK": "qpsk-8psk-constellations",
    "dd": "apsk-constellations",
    "f:ShBou": "shannon-bound",
    "fig:PolyDiv": "lfsr-polynomial-division",
    "fig:COMBout": "comb-network-output",
    "fig:COMBin": "comb-network-input",
    "fig:HWarch": "hw-architecture",
}

# Macros from master.tex and the toptesi class, in a form pandoc expands.
PREAMBLE = r"""
\newcommand{\vet}[1]{\mathbf{#1}}
\newcommand{\ped}[1]{_{\mathrm{#1}}}
\newcommand{\ap}[1]{^{\mathrm{#1}}}
\newcommand{\unit}[1]{\,\mathrm{#1}}
\newcommand{\virgola}{,}
\newcommand{\decimalcomma}{{,}}
\newcommand{\im}{\mathrm{j}}
\newcommand{\figref}[1]{Figure~\ref{#1}}
\newcommand{\tbref}[1]{Table~\ref{#1}}
\newcommand{\secref}[1]{Section~\ref{#1}}
\newcommand{\bch}[2]{$\mathrm{BCH(#1,#2)}$}
\newtheorem{Theorem}{Theorem}
\newtheorem{Def}{Definition}
"""


def read_tex(name):
    path = ROOT / (name if name.endswith(".tex") else name + ".tex")
    text = path.read_bytes().decode("cp1252").replace("\r\n", "\n")
    # Drop comments, keeping escaped \%.
    return re.sub(r"(?<!\\)%.*", "", text)


def find_group(text, start):
    """Return the index just past the {...} group opening at text[start]."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError("unbalanced braces")


def unwrap_subfloats(text):
    r"""\subfloat[caption]{body} -> body (pandoc drops subfloats entirely)."""
    out = []
    pos = 0
    for m in re.finditer(r"\\subfloat(\[[^\]]*\])?\s*\{", text):
        if m.start() < pos:
            continue
        end = find_group(text, m.end() - 1)
        out.append(text[pos:m.start()])
        out.append(text[m.end():end - 1])
        pos = end
    out.append(text[pos:])
    return "".join(out)


def replace_tikz_figures(text):
    def figure(m):
        body = m.group(0)
        label = re.search(r"\\label\{([^}]*)\}", body)
        if not label or label.group(1) not in TIKZ_FIGURES:
            return body
        caption = re.search(r"\\caption\{", body)
        start = caption.start()
        end = find_group(body, caption.end() - 1)
        png = TIKZ_FIGURES[label.group(1)]
        return ("\\begin{figure}\n\\includegraphics{figures/%s.png}\n%s\\label{%s}\n\\end{figure}"
                % (png, body[start:end], label.group(1)))
    return re.sub(r"\\begin\{figure\}.*?\\end\{figure\}", figure, text, flags=re.S)


def resolve_images(text):
    def image(m):
        name = m.group(2)
        if name.startswith("figures/"):
            return "\\includegraphics{%s}" % name
        for ext in (".jpg", ".png"):
            if (ROOT / (name + ext)).exists():
                return "\\includegraphics{%s%s}" % (name, ext)
        sys.exit("no raster image for \\includegraphics{%s}" % name)
    return re.sub(r"\\includegraphics(\[[^\]]*\])?\{([^}]*)\}", image, text)


def preprocess(text):
    # Inline \input files (figure bodies are replaced afterwards).
    text = re.sub(r"\\input\{([^}]*)\}", lambda m: read_tex(m.group(1)), text)
    text = replace_tikz_figures(text)
    text = unwrap_subfloats(text)
    text = resolve_images(text)
    text = re.sub(r"\\lstinputlisting(\[[^\]]*\])?\{([^}]*)\}",
                  lambda m: "\\begin{lstlisting}[language=C]\n%s\n\\end{lstlisting}"
                  % (ROOT / m.group(2)).read_bytes().decode("cp1252").replace("\r\n", "\n").rstrip(),
                  text)
    # A \label right after \end{equation} or \end{align} belongs inside it.
    text = re.sub(r"(\\end\{(?:equation|align)\})\s*(\\label\{[^}]*\})", r"\2\1", text)
    # align nested in equation: LaTeX gives it a single number.
    text = re.sub(r"\\begin\{equation\}\s*\\begin\{align\}(.*?)\\end\{align\}\s*\\end\{equation\}",
                  r"\\begin{equation}\\begin{aligned}\1\\end{aligned}\\end{equation}", text, flags=re.S)
    # number.lua recognises subequations by a \label in front of the align.
    count = iter(range(1, 1000))
    text = re.sub(r"\\begin\{subequations\}(?!\s*\\label)",
                  lambda m: "\\begin{subequations}\\label{subequations-%d}" % next(count), text)
    # pandoc takes "\centering 2\%" in a table cell as \centering{2}, losing the 2.
    text = re.sub(r"\\centering\b\s*", "", text)
    # toptesi front-matter commands.
    text = text.replace("\\sommario", "\\chapter*{Sommario}")
    text = text.replace("\\ringraziamenti", "\\chapter*{Ringraziamenti}")
    text = re.sub(r"\\(english|italiano|clearpage|indici)\b", "", text)
    return text


def main():
    if not shutil.which("pandoc"):
        sys.exit("pandoc not found")
    body = []
    for part in PARTS:
        if part == "Basic":
            # pandoc ignores \appendix; number.lua looks for this marker.
            body.append("\n\nAPPENDIXMARKER\n\n")
        body.append(preprocess(read_tex(part)))
    tex = ("\\documentclass{book}\n\\usepackage{amsmath}\n" + PREAMBLE +
           "\\begin{document}\n" + "\n".join(body) +
           "\n\\nocite{*}\n\\end{document}\n")

    build = ROOT / "tools" / "build"
    build.mkdir(exist_ok=True)
    (build / "thesis.tex").write_text(tex, encoding="utf-8")

    md = subprocess.run(
        ["pandoc", str(build / "thesis.tex"), "-f", "latex", "-t", "gfm",
         "--wrap=none", "--citeproc", "--bibliography", str(ROOT / "thesis.bib"),
         "--lua-filter", str(TOOLS / "number.lua")],
        check=True, stdout=subprocess.PIPE, text=True, cwd=ROOT).stdout
    (build / "thesis.md").write_text(md, encoding="utf-8")
    split_chapters(md)


def slug(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:60].rstrip("-")


def split_chapters(md):
    # number.lua puts an HTML comment before each chapter heading:
    # <!-- chapter: <number> -->
    pieces = re.split(r"^<!-- chapter: (.*?) -->\n+", md, flags=re.M)
    chapters = []
    for index, (number, text) in enumerate(zip(pieces[1::2], pieces[2::2])):
        title = re.sub(r"<[^>]*>", "", re.match(r"# (.*)", text).group(1))
        if number:
            title = title[len(number):].strip()
        name = "%02d-%s.md" % (index, slug(title))
        chapters.append({"file": name, "number": number, "title": title, "text": text})
    if pieces[0].strip():
        sys.exit("unexpected text before the first chapter")

    # Where each anchor lives, to turn #id links into file.md#id links.
    where = {}
    for ch in chapters:
        for anchor in re.findall(r'id="([^"]+)"', ch["text"]):
            where[anchor] = ch["file"]
        for anchor in re.findall(r'<a name="([^"]+)"', ch["text"]):
            where[anchor] = ch["file"]

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for i, ch in enumerate(chapters):
        def link(m):
            target = where.get(m.group(2))
            if target is None or target == ch["file"]:
                return m.group(0)
            return "%s%s#%s" % (m.group(1), target, m.group(2))
        text = re.sub(r'(href="|\]\()#([^")]+)', link, ch["text"])
        # Images live in the repository root, one level up.
        text = re.sub(r'(<img src="|!\[[^\]]*\]\()(?!https?:)', r"\1../", text)
        nav = []
        if i > 0:
            nav.append("[← %s](%s)" % (chapters[i - 1]["title"], chapters[i - 1]["file"]))
        nav.append("[Contents](README.md)")
        if i + 1 < len(chapters):
            nav.append("[%s →](%s)" % (chapters[i + 1]["title"], chapters[i + 1]["file"]))
        nav = " · ".join(nav)
        (OUT / ch["file"]).write_text(text.rstrip() + "\n\n---\n\n" + nav + "\n", encoding="utf-8")

    toc = ["# BCH-LDPC Concatenated Coding and High Order Modulations for Satellite Transmitters", "",
           "Master's Thesis — Eriprando Pacces, Politecnico di Torino, July 2008.", "",
           "*Generated from the LaTeX sources by `tools/tex2md.py`; do not edit by hand. "
           "The reference text is [`TESI_FINALE.pdf`](../TESI_FINALE.pdf).*", ""]
    for ch in chapters:
        prefix = ch["number"] + ". " if ch["number"] else ""
        toc.append("- [%s%s](%s)" % (prefix, ch["title"], ch["file"]))
    (OUT / "README.md").write_text("\n".join(toc) + "\n", encoding="utf-8")
    (OUT / "chapters.json").write_text(json.dumps(
        [{k: ch[k] for k in ("file", "number", "title")} for ch in chapters], indent=2) + "\n")
    print("wrote %d chapters to %s" % (len(chapters), OUT.relative_to(ROOT)))


if __name__ == "__main__":
    main()
