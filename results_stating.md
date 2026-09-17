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

Split view:

| subset | n | B_fuzzy | M_local qwen2.5:14b | M_comm claude-sonnet-5 |
|---|---:|---:|---:|---:|
| all | 300 | **0.707** | 0.560 | 0.667 |
| HARD (novel) | 33 | 0.364 | 0.576 | **0.758** |
| non-HARD | 267 | **0.749** | 0.558 | 0.655 |

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

Another way to see the split: on HARD, the commercial model gets **14**
strings right that the fuzzy dictionary misses, while the dictionary
rescues only **1** HARD string that the commercial model misses. On the
267 non-HARD strings the direction flips: the dictionary gets **62**
right that the commercial model misses, while the commercial model adds
only **37** non-HARD rescues. So the benchmark is not saying "LLM bad"
or "dictionary bad"; it is locating exactly where each instrument helps.

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

## Error analysis

The missed cases are interpretable and fit a small set of recurring
failure modes.

- **Archaic or lexicalized historical terms.** The commercial model helps
  when the string is a real but rare historical medical term and the
  nearest dictionary neighbour is lexically misleading: `quinsy`
  (Respiratory), `prurigo` (Skin), `entozoa` (Infectious), `synovitis`
  (Musculoskeletal).
- **Explicit event / external-cause phrasing.** The commercial model also
  helps when the string describes a cause as an event rather than as a
  disease name: `beaten with iron bar`, `house fire`, `self-inflicted`.
- **Very vague or symptom-only phrases.** The commercial model tends to
  over-medicalize broad symptom descriptions that ICD10h keeps under
  `Ill-defined`: `loss of blood`, `shortness of breath`, `gripes`.
- **Boundary cases between infection, skin, and genitourinary coding.**
  Some historical labels sit awkwardly between organ-system and disease
  family interpretations, e.g. `noma pudendi` (gold: Genitourinary;
  commercial: Infectious; fuzzy: Skin).

The dictionary's strongest region is the opposite regime: strings that
are close to previously seen terms, where lexical overlap almost solves
the task by itself. That is why it remains best on the non-HARD bulk.

## Example cases

Illustrative HARD cases where the commercial model succeeds and the fuzzy
dictionary fails:

| string | gold | nearest dictionary neighbour | fuzzy | commercial |
|---|---|---|---|---|
| `quinsy` | Respiratory | `insanity` | Mental | **Respiratory** |
| `glands in the lungs` | Respiratory | `glands inflammation` | Ill-defined | **Respiratory** |
| `synovitis` | Musculoskeletal | `otitis` | Ear | **Musculoskeletal** |
| `congenital chest mischief` | Congenital | `syphilis congenital` | Infectious | **Congenital** |
| `died of grief` | Mental | `died at sea` | ExternalCause | **Mental** |
| `self-inflicted` | ExternalCause | `influenza` | Respiratory | **ExternalCause** |

Illustrative non-HARD cases where the dictionary is right and the
commercial model is wrong:

| string | gold | fuzzy | commercial |
|---|---|---|---|
| `cerebral congestion` | Nervous | **Nervous** | Circulatory |
| `syncope supposed` | Ill-defined | **Ill-defined** | Circulatory |
| `meningitis tubercular` | Infectious | **Infectious** | Nervous |
| `uterus rupture` | Genitourinary | **Genitourinary** | Pregnancy |
| `fracture skull supposed` | ExternalCause | **ExternalCause** | Injury |
| `amputation arm` | ExternalCause | **ExternalCause** | Injury |

These examples are not cherry-picked for drama; they are representative
of the broader split. The commercial model is strongest when lexical
nearest-neighbour lookup breaks on genuinely novel wording. The fuzzy
dictionary is strongest when the correct historical coding convention is
already implicit in nearby entries.

## Primary vs exploratory claims

The preregistered **primary endpoint** is full-test accuracy on the 300
held-out strings. On that endpoint, the commercial model does **not**
beat the best baseline by the required +0.05 margin, so the registered
verdict stays **KILLED-AT-4**.

## Important implication

The HARD result is therefore **secondary / exploratory**. It is the most
interesting scientific signal in the run, but it does not overturn the
primary verdict. The right reading is narrower: on novel historical
terms, a frontier model appears useful; on the full benchmark as
currently constructed, a fuzzy coding dictionary remains harder to beat.

## Limits

- Chapter-level (20 classes), not full ICD10h codes.
- Single dataset (ICD10h English historic strings); external validity to
  other archives, periods, or languages is untested.
- HARD subset n=33 — the most interesting result has the least data, so
  the novel-term advantage should be treated as suggestive rather than
  definitive until replicated on a larger tail set.
- The evaluation is only chapter-level (not full ICD10h coding), so the
  benchmark tests broad categorization rather than exact historical code
  assignment.
- CLI scores single-sample (no temperature control); cached.
- 
