"""Classify each held-out historic cause-of-death string into an ICD chapter.
Usage: python score.py [local|comm]. Cached / resume-safe."""
import json
import os
import sys
import time

from common import generate, generate_cli
from common_coding import (CHAPTERS, accuracy, bootstrap_acc_ci, macro_f1,
                           parse_chapter)

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
DERIVED = os.path.join(ROOT, "data/derived")
OUT = os.path.join(ROOT, "outputs")

SYSTEM = "You are a medical coder assigning historical (17th-20th century) causes of death to broad modern disease categories. Reply with exactly one category name from the given list and nothing else."
USER = '''Historic cause of death: "{s}"

Assign it to ONE of these categories:
{cats}

Answer with exactly one category name.'''


def main(method):
    os.makedirs(OUT, exist_ok=True)
    test = json.load(open(os.path.join(DERIVED, "test.json")))
    raw_path = os.path.join(OUT, f"raw_{method}.jsonl")
    done = {}
    if os.path.exists(raw_path):
        for l in open(raw_path):
            r = json.loads(l)
            done[r["i"]] = r
    f = open(raw_path, "a")
    todo = [(i, t) for i, t in enumerate(test) if i not in done]
    print(f"{method}: {len(test)} items, {len(done)} cached, {len(todo)} to do")
    t0 = time.time()
    cats = ", ".join(CHAPTERS)
    for k, (i, t) in enumerate(todo):
        prompt = USER.format(s=t["string"], cats=cats)
        if method == "local":
            out = generate(SYSTEM + "\n\n" + prompt, num_predict=12)
        else:
            out = generate_cli(prompt, system=SYSTEM, model="claude-sonnet-5")
        f.write(json.dumps({"i": i, "raw": out.strip()[:40],
                            "pred": parse_chapter(out)}, ensure_ascii=False) + "\n")
        f.flush()
        if (k + 1) % 25 == 0:
            print(f"  [{k+1}/{len(todo)}] {time.time()-t0:.0f}s", flush=True)
    f.close()

    pr = {r["i"]: r["pred"] for r in (json.loads(l) for l in open(raw_path))}
    unparsed = sum(1 for i in range(len(test)) if pr.get(i) is None)
    gold = [t["chapter"] for t in test]
    pred = [pr.get(i) or "Ill-defined" for i in range(len(test))]  # unparsed -> Ill-defined
    acc = accuracy(gold, pred)
    lo, hi = bootstrap_acc_ci(gold, pred)
    f1 = macro_f1(gold, pred)
    name = {"local": "M_local_qwen14b", "comm": "M_comm_sonnet5"}[method]
    json.dump({"method": name, "acc": acc, "ci95": [lo, hi], "macro_f1": f1,
               "unparsed": unparsed, "pred": pred},
              open(os.path.join(OUT, f"pred_{name}.json"), "w"))
    print(f"{name}: acc={acc:.4f} [{lo:.4f},{hi:.4f}] macroF1={f1:.4f} unparsed={unparsed}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "local")
