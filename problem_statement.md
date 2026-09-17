# Coding the causes of death the searchers wrote down

## The original statement

John Graunt, *Natural and Political Observations ... upon the Bills of
Mortality* (London, 1662). Graunt built the first quantitative analysis of
death records and immediately hit the problem that the causes were
recorded by untrained parish "searchers" in lay, inconsistent terms. He
asks (quoted from Hull's public-domain edition, *The Economic Writings of
Sir William Petty*, vol. 2, 1899, pp. 347-349):

> "to make these Corrections upon the, perhaps, ignorant and careless
> Searchers Reports, I considered first of what Authority they were of
> themselves, that is, whether any credit at all were to be given to
> their Distinguishments"

and settles for lay categories a non-expert can tell apart:

> "the generality of the World are able pretty well to distinguish the
> Gout, Stone, Dropsie, Falling sickness, Palsie, Agues, Pleuresie,
> Rickets, one from another."

Source scan (public domain): Internet Archive,
https://archive.org/details/economicwritings02pett (Graunt's 1662
Observations, reprinted). Graunt d. 1674; the source is public domain.
See DATA-LICENSES.md.

## The bound and the capability

Labor. Historical death registers hold millions of causes written in
archaic, vernacular, misspelled, and compound terms ("dropsy", "teething",
"quinsy", "decline", "mortification", "water on the brain"). To use them
you must map each string to a coherent disease category -- by hand, term
by term, a task demographers still grind through. The candidate
capability is **medical/lexical knowledge that generalizes to unseen
archaic strings**: assign a category even to a term not in any coding
dictionary. That is where a hand-built lookup fails and an LLM might not.

## Still open

Consistent coding of historic causes of death is active and unsolved:
Alter & Carmichael note there is "no key" to translating archaic causes;
the ICD10h scheme (2024) and LLM-coding papers (2024) exist precisely
because it is not solved, especially for rare and cross-period terms.

## Data

ICD10h "Historic cause of death coding scheme -- English language historic
strings" (Reid, Garrett, Hiltunen Maltesdotter, Univ. Cambridge, 2024),
**CC-BY 4.0**. 3,306 historic English cause-of-death strings, each with an
ICD10h code. We derive the broad ICD-10 **chapter** (~20 classes:
Infectious, Neoplasm, Circulatory, Respiratory, Digestive, Ill-defined,
Injury, ...) from each code as the label. See DATA-LICENSES.md.

## Task, split, baselines, kill criterion (fixed before any model run)

Task: classify a historic cause-of-death string into one of the ~20 ICD
chapters.

Split (deterministic, seed 0): 300 strings held out as TEST; the other
3,006 form the DICTIONARY used by the lookup baseline. (De-duplicated by
string first.)

Baselines (run first, measured):
- B_majority = always predict the most common chapter. **acc 0.153.**
- B_fuzzy = nearest DICTIONARY string by char-3gram cosine -> its chapter
  (a coding dictionary with fuzzy lookup). **acc 0.707.**

Instruments (given the string + the list of chapters; no dictionary):
- M_local = qwen2.5:14b (local).
- M_comm = claude-sonnet-5 (commercial, via the authenticated CLI).

**Primary metric: accuracy on the 300 held-out strings.** 95% CI by
bootstrap (seed 0).

**Kill criterion (fixed now):** the commercial instrument must beat the
best baseline (B_fuzzy, 0.707) by >= +0.05 accuracy (i.e. reach >= 0.757).
Otherwise a fuzzy coding dictionary is as good, and the verdict is
KILLED-AT-4. Secondary (not part of the kill test): accuracy on the HARD
subset -- the 33 TEST strings whose best dictionary similarity is < 0.5
(novel terms), where the dictionary is weak and generalization matters;
and commercial vs local. Small n (33) -- reported as suggestive only.

No threshold moves after seeing the model numbers.

## Memorization probe 

The ICD10h dataset is public (CC-BY, 2024); a frontier model may have seen
it. Chapter-level correctness for clear diseases (cholera -> Infectious)
is legitimate medical knowledge, not dataset recall. The threat is recall
of the authors' idiosyncratic **extended codes** (e.g. A00.900). Probe:
ask the commercial model for the exact ICD10h code of 30 test strings;
score exact-code match. Interpretation fixed now: if exact-code match is
non-trivial (> 0.15), flag that the model has likely seen this specific
scheme and read the chapter accuracy with that caveat; a low number means
the chapter accuracy rests on general medical knowledge, which is the
instrument working as intended.
