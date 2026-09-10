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
        rec = {"string": t["string"], "gold": t["code"], "guess": guess,
               "exact": guess == t["code"].upper(),
               "base3_match": guess[:3] == t["code"].upper()[:3]}
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
    f.close()
    rows = [json.loads(l) for l in open(RES)]
    exact = sum(r["exact"] for r in rows) / len(rows)
    base3 = sum(r["base3_match"] for r in rows) / len(rows)
    print(f"probe n={len(rows)}  exact-code match={exact:.3f}  base-3char match={base3:.3f}")
    json.dump({"n": len(rows), "exact_code": exact, "base3": base3},
              open(os.path.join(OUT, "probe_summary.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
