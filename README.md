# cause-of-death-coding

Historical Cause-of-Death Coding

This project explores how modern language models handle noisy, archaic
medical text from historical mortality records. The task is to classify
cause-of-death phrases written in inconsistent, vernacular language into
broad disease categories, using a held-out evaluation set and a strong
fuzzy dictionary baseline for comparison.

Historical death records are full of lexical drift, misspellings, and
short-form phrases that do not map cleanly to modern clinical vocabulary.
The problem is not just coding accuracy, but robustness when the surface
form is unfamiliar and no exact dictionary entry exists.

The work focuses on a practical question in applied AI: when does semantic
reasoning help, and when do simpler retrieval-based methods still outperform
it? The results show that fuzzy matching remains highly effective on
familiar historical terms, while model-based reasoning provides a clear
advantage on rarer or more novel cases where direct lookup fails.

This project combines historical text analysis, benchmark design, and
careful model evaluation, and it is a useful example of applied NLP where
simple baselines remain surprisingly competitive.

## Why this matters

Historical mortality data are often written by untrained observers in
vernacular language, which makes them difficult to standardize and compare
across time. Reliable coding of these strings matters for research in
population health, historical epidemiology, and the reconstruction of
patterns that are otherwise lost in non-standard wording.

This project treats that challenge as an applied classification task with
real evaluation pressure: not just whether a model can guess a chapter,
but whether it helps in the cases where dictionary-based methods break.

## What I built

- A historical cause-of-death classification benchmark built on ICD-10
  chapter labels.
- A deterministic held-out evaluation split for fair comparison.
- A fuzzy dictionary baseline that performs nearest-neighbour matching from
  historical strings to known entries.
- A model-based approach evaluated against the same benchmark, including a
  harder subset of novel historical terms.

## Key result

The core finding is nuanced rather than sensational: fuzzy lookup remains
extremely strong on familiar historical strings, while the model-based
approach adds meaningful value on the harder novel-term cases where direct
lookup is weak. That is the practical insight this project is designed to
surface.

## Task

Classify a historical English cause-of-death string into one of roughly 20
ICD-10 chapters. The dataset is the ICD10h historical coding scheme
(CC-BY), and the evaluation compares a majority baseline, a fuzzy
char-3gram dictionary lookup, and a modern language-model approach.

The project emphasizes not only overall accuracy, but also how performance
changes on the harder subset of novel historical terms, where direct lookup
is weak and generalization becomes more important.

## Repository layout

- Problem definition and task framing: `PROBLEM.md`
- Data provenance and licensing: `DATA-LICENSES.md`
- Evaluation results and verdict: `RESULTS.md`
- Source code: `src/`
- Model outputs and cached probes: `outputs/`

## Run it

```
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
# data: ICD10h historic strings (CC-BY) from
#   https://www.repository.cam.ac.uk/items/5e006e8c-a78a-4693-b851-aabbdc08755f
#   -> data/raw/icd10h_strings.txt
ollama pull qwen2.5:14b

cd src
python prepare.py
python baseline.py                    # majority + fuzzy (run first)
python score.py local && python score.py comm
python probe.py
python report.py
```

This project is designed to be a clear, evidence-based benchmark rather than
an AI demo: the goal is to understand where retrieval methods remain strong,
and where model-based reasoning adds real value.
