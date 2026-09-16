# Preprint source

`main.tex` + `refs.bib` + `figs/`. Build: `pdflatex main && bibtex main && pdflatex main && pdflatex main`.
Figures and the appendix table rows are produced by `../src/analysis_paper.py`
(run it from `src/`); the rows in `hard_table.tex` are pasted into `main.tex`.
Numbers in the text come from `../outputs/summary.json` (primary) and
`../outputs/paper_stats.json` (exploratory).
