# Results

Run date: 2026-08-09. Supplementary analyses and probe correction: 2026-09-16. Instruments: `qwen2.5:14b` (local) and
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

## Memorization probe: inconclusive (corrected 2026-09-16)

The commercial model was asked for the exact ICD10h code of 30 test
strings. The cached `outputs/probe_results.jsonl` shows an **empty
response for all 30 items**; the CLI returned nothing. An earlier version
of this file read that as "exact-code match = 0.000, clean". That reading
was wrong: a zero over zero answers does not distinguish a model that does
not know the codes from one that declined to guess, or from an interface
artefact. `probe.py` now records an `answered` flag and reports the probe
as INCONCLUSIVE when no item gets a code-shaped answer.

    n=30  answered=0  exact-code match=0.000  (undefined among answered)

The memorization question is therefore open. Two things reduce, without
settling, the concern: the model's errors are systematic ICD10h convention
errors of the kind a model that had memorized the codes would not make
(see "Convention errors" below), and it does best on the strings least
like anything in the published file. Rerunning the probe with a prompt
that elicits an actual code, or via the API, is the obvious next step.

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

## Supplementary analyses (exploratory, 2026-09-16)

All numbers below are recomputed from the cached outputs by
`src/analysis_paper.py`, which writes them to `outputs/paper_stats.json`
and draws the figures in `paper/figs/`. None of this was preregistered.

**Paired statistics, commercial minus fuzzy** (paired bootstrap, 5,000
resamples, seed 0; exact McNemar on discordant pairs):

| subset | n | diff | 95% CI | fuzzy-only right | comm-only right | McNemar p |
|---|---:|---:|---|---:|---:|---:|
| all | 300 | −0.040 | [−0.110, +0.030] | 63 | 51 | 0.30 |
| HARD | 33 | **+0.394** | [+0.212, +0.576] | 1 | 14 | 0.001 |
| non-HARD | 267 | −0.094 | [−0.169, −0.022] | 62 | 37 | 0.015 |

Macro-F1 difference +0.074, CI [−0.017, +0.156]. On the full set the two
instruments are a statistical tie; the primary verdict stands on the
preregistered margin, not on a significant deficit.

**Accuracy by best dictionary similarity.** The dictionary is close to a
linear function of similarity; the models are flat.

| similarity bin | n | B_fuzzy | M_local | M_comm |
|---|---:|---:|---:|---:|
| [0.0, 0.4) | 16 | 0.188 | 0.562 | **0.875** |
| [0.4, 0.5) | 17 | 0.529 | 0.588 | **0.647** |
| [0.5, 0.6) | 36 | 0.611 | 0.472 | **0.639** |
| [0.6, 0.7) | 71 | 0.606 | 0.549 | **0.662** |
| [0.7, 0.8) | 87 | **0.782** | 0.552 | 0.632 |
| [0.8, 1.0] | 73 | **0.918** | 0.616 | 0.685 |

The crossover is around similarity 0.6–0.7, above the preregistered 0.5
cut. The HARD result is not an artefact of where the cut was placed.

**Label asymmetry (added 2026-09-18 after external review).** Two of the 22
chapter names offered to the models have zero support in the dictionary:
Special (never chosen) and Injury. ICD10h files nature-of-injury in a
separate `ICD10hInjury` column, so no string is ever primary-coded S–T. The
fuzzy baseline returns a dictionary entry's chapter and therefore *cannot*
emit Injury; the models can and did (Sonnet 15, Qwen 31, all gold
ExternalCause). "The label list was fixed before the data" does not repair a
handicap that only one side can incur. Both scorings are now reported:

| | fuzzy | Sonnet prereg | Sonnet folded | Qwen prereg | Qwen folded |
|---|---:|---:|---:|---:|---:|
| correct / 300 | 212 | 200 | 214 | 168 | 197 |
| acc all | 0.707 | 0.667 | **0.713** [0.660, 0.763] | 0.560 | 0.657 |
| vs fuzzy, all: diff, McNemar | | −0.040, 63 vs 51, p=0.30 | +0.007, 52 vs 54, p=0.92 | | −0.050, p=0.17 |
| vs fuzzy, non-HARD | | −0.094, p=0.015 | −0.041, p=0.29 | | −0.105, p=0.004 |
| vs fuzzy, HARD | | +0.394, p=0.001 | +0.394, p=0.001 | | +0.394, p=0.002 |
| macro-F1 | 0.635 | 0.709 | 0.722 | 0.568 | 0.613 |

What moves: the full-set ordering (dictionary 12 strings ahead) was
entirely the 15-string Injury artefact; folded, it is a tie. The non-HARD
advantage of the dictionary stops being significant. What does not move:
the kill verdict (0.713 < 0.757), the HARD tail, the τ=0.5 hybrid (0.750
either way; Sonnet never answered Injury on a HARD string).

**Convention errors, not medical errors.** Three confusion cells hold 34
of the commercial model's 100 preregistered errors:

- `ExternalCause → Injury` (14). ICD10h's primary column codes a traumatic
  death by its external cause (V–Y); the nature of injury (S–T) lives in a
  separate `ICD10hInjury` column of the strings file. **The Injury chapter
  never occurs in the dictionary or the test set.** The label list was
  fixed from the ICD-10 chapter structure before inspecting the data, so
  Injury stayed in the prompt as a distractor. The local model picked it
  31 times (its ExternalCause F1 is 0.05 for this reason alone).
- `Ill-defined → organ system` (Digestive 9, Circulatory 5, ...).
  ICD10h keeps symptom strings (`jaundice`, `loss of blood`, `gripes`)
  under R; the model medicalizes them. It predicted Ill-defined 8 times
  against 31 gold and 45 fuzzy predictions.
- `Infectious → Digestive` (11). `gastro enteritis acute`,
  `entero-colitis`, `tuberculosis bowels` are A09/A18, Chapter I.

The Injury cell is the asymmetry above; the folded rows in the table
already remove it. The other two cells are prompt-fixable conventions.

**Routed hybrid.** Answer from the dictionary when best similarity ≥ τ,
else from the model. At the preregistered τ = 0.5 (no tuning): **0.750**
acc, 0.689 macro-F1 with the commercial model; 0.730 with the local one.
Best post hoc τ = 0.65 gives 0.780 (chosen on the test set; an upper
bound). Oracle union of dictionary and commercial model: 0.877.

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
- The memorization probe produced no answers; dataset exposure is untested.
