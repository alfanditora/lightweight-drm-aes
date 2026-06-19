# IEEE-Format

Reusable IEEE conference paper template for technical reports, research drafts,
class assignments, and project documentation. The paper source is in `paper/`.

- IEEEtran conference layout
- XeLaTeX with Times New Roman fallback handling
- modular `paper/sections/*.tex` files
- BibTeX references in `paper/references.bib`
- compact footer and section styling
- local `paper/IEEEtran.cls` for reproducible compilation

## Requirements

Install a LaTeX distribution that provides `xelatex` and `bibtex`.

Recommended options:

- Windows: MiKTeX or TeX Live
- Linux: TeX Live
- macOS: MacTeX

This template uses `fontspec`, so compile with `xelatex`, not `pdflatex`.

## Compile Locally

From the repository root:

```powershell
cd paper
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

The generated PDF will be:

```text
paper/main.pdf
```

## Compile with latexmk

If `latexmk` is installed:

```powershell
cd paper
latexmk -xelatex main.tex
```

Clean temporary files while keeping the PDF:

```powershell
latexmk -c main.tex
```

Remove temporary files and the PDF:

```powershell
latexmk -C main.tex
```

## Editing Guide

- Change title, author, abstract, keywords, packages, and section order in `paper/main.tex`.
- Replace body content in `paper/sections/*.tex`.
- Add references to `paper/references.bib`, then cite them with `\cite{key}`.
- Put figures in `images/` and reference them from paper files as `../images/name.png`.
- Keep generated files such as `.aux`, `.log`, `.bbl`, and `.pdf` out of git.

## Troubleshooting

- If `fontspec` fails, you are probably using `pdflatex`; use `xelatex`.
- If references show as `?`, run `bibtex main` and then run `xelatex main.tex` twice.
- If `IEEEtran.cls` is missing, compile from the `paper/` directory or restore `paper/IEEEtran.cls`.
- If a figure cannot be found, remember paths are relative to `paper/main.tex`.
