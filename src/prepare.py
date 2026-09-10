"""Load ICD10h historic strings, derive ICD chapter, split into dictionary
(for the fuzzy baseline) and held-out test. Deterministic."""
import csv
import json
import os
import random

from common_coding import chapter

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "data/raw/icd10h_strings.txt")
DERIVED = os.path.join(ROOT, "data/derived")
N_TEST = 300


def main():
    os.makedirs(DERIVED, exist_ok=True)
    rows = list(csv.DictReader(open(RAW, encoding="latin-1"), delimiter="\t"))
    items = []
    for r in rows:
        s = r["HISTORICSTRING"].replace(".", " ").strip()
        ch = chapter(r["ICD10H"])
        if s and ch:
            items.append({"string": s, "code": r["ICD10H"].strip(), "chapter": ch})
    # dedup by string
    seen = set()
    uniq = []
    for it in items:
        if it["string"].lower() in seen:
            continue
        seen.add(it["string"].lower())
        uniq.append(it)
    rng = random.Random(0)
    rng.shuffle(uniq)
    test = uniq[:N_TEST]
    dictionary = uniq[N_TEST:]
    json.dump(test, open(os.path.join(DERIVED, "test.json"), "w"), ensure_ascii=False, indent=0)
    json.dump(dictionary, open(os.path.join(DERIVED, "dictionary.json"), "w"), ensure_ascii=False)
    print(f"usable: {len(uniq)}  test: {len(test)}  dictionary: {len(dictionary)}")
    import collections
    print("test chapter distribution:", dict(collections.Counter(t["chapter"] for t in test).most_common()))


if __name__ == "__main__":
    main()
