"""Baselines, run first.
B_majority : always predict the most common chapter in the dictionary.
B_fuzzy    : nearest dictionary string by char-3gram cosine -> its chapter.
Also computes, per test item, the best dictionary similarity (used later to
define the HARD/novel subset)."""
import collections
import json
import os

from common import char_ngram_cosine
from common_coding import accuracy, bootstrap_acc_ci, macro_f1

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
DERIVED = os.path.join(ROOT, "data/derived")
OUT = os.path.join(ROOT, "outputs")


def main():
    os.makedirs(OUT, exist_ok=True)
    test = json.load(open(os.path.join(DERIVED, "test.json")))
    dictn = json.load(open(os.path.join(DERIVED, "dictionary.json")))
    gold = [t["chapter"] for t in test]

    majority = collections.Counter(d["chapter"] for d in dictn).most_common(1)[0][0]
    pred_maj = [majority] * len(test)

    # precompute dictionary ngram sets
    from common import char_ngrams
    dng = [(char_ngrams(d["string"], 3), d["chapter"]) for d in dictn]
    pred_fuzzy = []
    best_sim = []
    for t in test:
        q = char_ngrams(t["string"], 3)
        best = (-1.0, None)
        for ng, ch in dng:
            if not q or not ng:
                sim = 0.0
            else:
                sim = len(q & ng) / (len(q) ** 0.5 * len(ng) ** 0.5)
            if sim > best[0]:
                best = (sim, ch)
        pred_fuzzy.append(best[1])
        best_sim.append(best[0])

    for name, pred in [("B_majority", pred_maj), ("B_fuzzy", pred_fuzzy)]:
        acc = accuracy(gold, pred)
        lo, hi = bootstrap_acc_ci(gold, pred)
        f1 = macro_f1(gold, pred)
        json.dump({"method": name, "acc": acc, "ci95": [lo, hi], "macro_f1": f1,
                   "pred": pred}, open(os.path.join(OUT, f"pred_{name}.json"), "w"))
        print(f"{name:12} acc={acc:.4f} [{lo:.4f},{hi:.4f}] macroF1={f1:.4f}")
    json.dump(best_sim, open(os.path.join(OUT, "test_dictsim.json"), "w"))
    hard = sum(1 for s in best_sim if s < 0.5)
    print(f"HARD (novel: best dict char-3gram sim < 0.5): {hard}/{len(test)}")


if __name__ == "__main__":
    main()
