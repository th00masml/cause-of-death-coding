# Results

Run date: 2026-08-09. Instruments: `qwen2.5:14b` (local) and
`claude-sonnet-5` (commercial, via the authenticated Claude CLI, no API
key). Numbers recompute from cached outputs in `outputs/`.

## Verdict: KILLED-AT-4 (on the preregistered primary)

On the full held-out test, a fuzzy lookup dictionary beats both models.
But the picture is split, and the split is the finding.

## The numbers

300 held-out historic cause-of-death strings, classified into ~20 ICD
chapters. HARD = the 33 strings whose nearest dictionary neighbour has
char-3gram similarity < 0.5 (novel terms).

| method | acc (all) | acc (HARD, n=33) | macro-F1 |
|---|---|---|---|
| B_majority | 0.153 | 0.091 | 0.015 |
| **B_fuzzy** (dictionary lookup) | **0.707** | 0.364 | 0.635 |
| M_local qwen2.5:14b | 0.560 | 0.576 | 0.568 |
| **M_comm claude-sonnet-5** | 0.667 | **0.758** | **0.709** |

Primary (full-test accuracy):
- best baseline B_fuzzy = 0.707; commercial = 0.667 (CI [0.610, 0.720]).
- gain = **−0.040** (needed +0.05). **KILLED-AT-4.**

```
cd src
python prepare.py && python baseline.py
python score.py local && python score.py comm
python probe.py && python report.py
```

## The split, and why it matters

- On the **full** test, most strings are near-duplicates of dictionary
  entries ("asiatic cholera" ~ "cholera"), so a fuzzy lookup nails them
  (0.707) and micro-accuracy rewards that. The LLM does not beat it.
- On the **novel** strings (HARD, no close dictionary neighbour) the
  dictionary collapses to **0.364** while the commercial model holds at
  **0.758** — a +0.39 gap. This is the labor-bound, still-open case:
  coding archaic terms no dictionary has seen. The instrument clearly
  helps there. (n=33; suggestive, not decisive — and it was *not* the
  preregistered primary, so it does not overturn the verdict.)
- By **macro-F1** (which weights rare chapters equally) the commercial
  model beats the dictionary (0.709 vs 0.635): the dictionary wins on
  frequent near-duplicate strings but is worse across the rarer classes.

So the honest headline: for coding historic causes of death, a fuzzy
dictionary is hard to beat on the bulk of strings that resemble known
ones; a frontier model earns its keep only on novel/rare terms and on
class-balanced coverage. The local 14B is worse than the dictionary
everywhere except the novel tail.

## Commercial vs local

The commercial model beats the local 14B on every cut (0.667 vs 0.560
overall; 0.758 vs 0.576 on novel strings; 0.709 vs 0.568 macro-F1). Here,
unlike the other two commercial runs, the frontier model is clearly
better than the local one — medical knowledge is exactly the axis where
model scale helps.

## Memorization: zero

Commercial model asked for the exact ICD10h code of 30 test strings:

    exact-code match = 0.000   base-3-char match = 0.000

The model does not reproduce ICD10h's idiosyncratic codes at all. Its
chapter accuracy is general medical knowledge, not recall of this
dataset. Clean.

## Limits

- Chapter-level (20 classes), not full ICD10h codes.
- HARD subset n=33 — the most interesting result has the least data;
  a larger novel-string test is the obvious next step.
- CLI scores single-sample (no temperature control); cached.
