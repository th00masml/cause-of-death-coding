"""Dataset-recall probe (commercial model): ask for the exact ICD10h fine
code (the authors' idiosyncratic extended codes, e.g. A00.900). If the model
reproduces these for obscure strings, it has seen THIS dataset (not just
general medical knowledge). Chapter-level knowledge is legitimate; specific
extended codes are dataset-specific. Cached."""
import json
import os
import re

from common import generate_cli

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
DERIVED = os.path.join(ROOT, "data/derived")
OUT = os.path.join(ROOT, "outputs")
RES = os.path.join(OUT, "probe_results.jsonl")
N = 30

PROMPT = '''In the ICD10h historic cause-of-death coding scheme, every historic term has a specific code (for example "asiatic cholera" is coded A00.900). Give the exact ICD10h code for this term. Reply with only the code.

Term: "{s}"'''


def main():
    test = json.load(open(os.path.join(DERIVED, "test.json")))[:N]
    done = {}
    if os.path.exists(RES):
        for l in open(RES):
            r = json.loads(l)
            done[r["string"]] = r
    f = open(RES, "a")
    for t in test:
        if t["string"] in done:
            continue
        out = generate_cli(PROMPT.format(s=t["string"]), model="claude-sonnet-5")
        m = re.search(r"[A-Z]\d\d(\.\d+)?", out.strip().upper())
        guess = m.group(0) if m else out.strip()[:12]
        answered = bool(m)  # a code-shaped answer; empty/refusal is NOT a miss
        rec = {"string": t["string"], "gold": t["code"], "guess": guess,
               "answered": answered,
               "exact": answered and guess == t["code"].upper(),
               "base3_match": answered and guess[:3] == t["code"].upper()[:3]}
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
    f.close()
    rows = [json.loads(l) for l in open(RES)]
    # Backward compatibility with the 2026-08-09 run, which had no "answered" field.
    for r in rows:
        r.setdefault("answered", bool(re.fullmatch(r"[A-Z]\d\d(\.\d+)?", (r["guess"] or "").upper())))
    n = len(rows)
    n_ans = sum(r["answered"] for r in rows)
    exact = sum(r["exact"] for r in rows) / n
    base3 = sum(r["base3_match"] for r in rows) / n
    if n_ans == 0:
        verdict = "INCONCLUSIVE: no item received a code-shaped answer; cannot distinguish ignorance from refusal or a CLI artefact"
    elif exact > 0.15:
        verdict = "FLAG: non-trivial exact-code recall; model has likely seen ICD10h"
    else:
        verdict = "LOW: chapter accuracy rests on general medical knowledge"
    print(f"probe n={n}  answered={n_ans}  exact-code match={exact:.3f}  base-3char match={base3:.3f}")
    print(verdict)
    json.dump({"n": n, "answered": n_ans, "exact_code": exact, "base3": base3,
               "exact_code_among_answered": (sum(r["exact"] for r in rows) / n_ans) if n_ans else None,
               "verdict": verdict},
              open(os.path.join(OUT, "probe_summary.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
