# Data licenses

## 1. Source article (public domain)

John Graunt, *Natural and Political Observations ... upon the Bills of
Mortality* (1662). Public domain (author d. 1674). Quoted from the
public-domain reprint in C.H. Hull (ed.), *The Economic Writings of Sir
William Petty*, vol. 2 (Cambridge University Press, 1899):
https://archive.org/details/economicwritings02pett . Used only for the
quoted problem statement.

## 2. Dataset (CC-BY 4.0)

A. Reid, E. Garrett, M. Hiltunen Maltesdotter, "Historic cause of death
coding and classification scheme for individual-level causes of death --
English language historic strings" (University of Cambridge, 2024).
**CC-BY 4.0**. DOI: 10.17863/CAM.109962.2
- File used: ICD10H_HISTORICSTRINGSENGLISH_2024.2.txt (3,306 strings).
- https://www.repository.cam.ac.uk/items/5e006e8c-a78a-4693-b851-aabbdc08755f
- The ICD chapter labels used here are derived from the ICD10h codes.
  Attribution: Reid et al., ICD10h (CC-BY 4.0). Derived files here are
  shared under CC-BY 4.0.

## 3. Models

- Local model via Ollama.
- Commercial model via an authenticated CLI session, with no API key required.
  Single-sample outputs are cached under `outputs/`.

## Not committed

`data/raw/` (the ICD10h file) is gitignored; CC-BY and re-downloadable.
