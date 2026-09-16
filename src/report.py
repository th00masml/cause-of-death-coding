"""Aggregate baselines + models; overall and on HARD/non-HARD splits;
apply the preregistered kill criterion; and emit illustrative examples."""
import json
import os

from common_coding import accuracy

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
DERIVED = os.path.join(ROOT, "data/derived")
OUT = os.path.join(ROOT, "outputs")
MARGIN = 0.05


def load(n):
    p = os.path.join(OUT, f"pred_{n}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def acc_on_idx(gold, pred, idx):
    if not idx:
        return float("nan")
    return accuracy([gold[i] for i in idx], [pred[i] for i in idx])


def char_ngrams(s, n=3):
    s = "".join(c for c in (s or "").lower() if "a" <= c <= "z")
    if len(s) < n:
        return {s} if s else set()
    return {s[i : i + n] for i in range(len(s) - n + 1)}


def nearest_neighbor(query, dictionary):
    q = char_ngrams(query, 3)
    best = (-1.0, None)
    for d in dictionary:
        ng = d["_ng"]
        if not q or not ng:
            sim = 0.0
        else:
            sim = len(q & ng) / (len(q) ** 0.5 * len(ng) ** 0.5)
        if sim > best[0]:
            best = (sim, d)
    sim, item = best
    return {
        "string": item["string"],
        "chapter": item["chapter"],
        "sim": sim,
    }


def pair_breakdown(gold, pred_a, pred_b, idx):
    return {
        "both_correct": sum(gold[i] == pred_a[i] == pred_b[i] for i in idx),
        "a_only": sum(gold[i] == pred_a[i] and gold[i] != pred_b[i] for i in idx),
        "b_only": sum(gold[i] != pred_a[i] and gold[i] == pred_b[i] for i in idx),
        "neither": sum(gold[i] != pred_a[i] and gold[i] != pred_b[i] for i in idx),
    }


def collect_examples(test, dictionary, sim, gold, pred_a, pred_b, idx, matcher, limit=6):
    out = []
    for i in idx:
        if not matcher(i):
            continue
        nn = nearest_neighbor(test[i]["string"], dictionary)
        out.append({
            "i": i,
            "string": test[i]["string"],
            "gold": gold[i],
            "dict_sim": sim[i],
            "nearest_dict_string": nn["string"],
            "nearest_dict_chapter": nn["chapter"],
            "pred_a": pred_a[i],
            "pred_b": pred_b[i],
        })
        if len(out) >= limit:
            break
    return out


def main():
    test = json.load(open(os.path.join(DERIVED, "test.json")))
    dictionary = json.load(open(os.path.join(DERIVED, "dictionary.json")))
    for d in dictionary:
        d["_ng"] = char_ngrams(d["string"], 3)
    gold = [t["chapter"] for t in test]
    sim = json.load(open(os.path.join(OUT, "test_dictsim.json")))
    hard_idx = [i for i, s in enumerate(sim) if s < 0.5]
    nonhard_idx = [i for i, s in enumerate(sim) if s >= 0.5]

    methods = ["B_majority", "B_fuzzy", "M_local_qwen14b", "M_comm_sonnet5"]
    res = {m: load(m) for m in methods}
    print(f"{'method':18} {'acc(all)':>9} {'acc(hard)':>10} {'acc(nonhard)':>13} {'macroF1':>8}")
    accs = {}
    for m in methods:
        r = res[m]
        if not r:
            continue
        pred = r["pred"]
        a = accuracy(gold, pred)
        ah = acc_on_idx(gold, pred, hard_idx)
        anh = acc_on_idx(gold, pred, nonhard_idx)
        accs[m] = {
            "all": a,
            "hard": ah,
            "nonhard": anh,
            "macro_f1": r.get("macro_f1", 0),
        }
        print(f"{m:18} {a:9.4f} {ah:10.4f} {anh:13.4f} {r.get('macro_f1',0):8.4f}")

    print(f"\nHARD subset (novel strings, dict sim<0.5): n={len(hard_idx)}")
    if "M_comm_sonnet5" in accs:
        base = max(accs.get("B_majority", {"all": 0})["all"], accs.get("B_fuzzy", {"all": 0})["all"])
        comm = accs["M_comm_sonnet5"]["all"]
        gain = comm - base
        cm = res["M_comm_sonnet5"]
        lo, hi = cm["ci95"]
        passed = gain >= MARGIN
        verdict = "BUILT" if passed else "KILLED-AT-4-not-beaten"
        print(f"\n--- PRIMARY (full test) ---")
        print(f"best baseline acc = {base:.4f}  commercial acc = {comm:.4f}  gain = {gain:+.4f} (need +{MARGIN})")
        print(f"commercial 95% CI [{lo:.4f},{hi:.4f}]")
        print(f"VERDICT: {verdict}")
        if hard_idx and "B_fuzzy" in accs:
            print(f"\n(secondary) HARD subset: B_fuzzy {accs['B_fuzzy']['hard']:.4f} "
                  f"vs commercial {accs['M_comm_sonnet5']['hard']:.4f} "
                  f"vs local {accs.get('M_local_qwen14b', {'hard': 0})['hard']:.4f}")

        pairwise = {}
        if "B_fuzzy" in res:
            pairwise["hard"] = pair_breakdown(gold, res["B_fuzzy"]["pred"], res["M_comm_sonnet5"]["pred"], hard_idx)
            pairwise["nonhard"] = pair_breakdown(gold, res["B_fuzzy"]["pred"], res["M_comm_sonnet5"]["pred"], nonhard_idx)

        examples = {}
        if "B_fuzzy" in res:
            bf = res["B_fuzzy"]["pred"]
            cm_pred = res["M_comm_sonnet5"]["pred"]
            examples["hard_comm_beats_fuzzy"] = collect_examples(
                test, dictionary, sim, gold, bf, cm_pred, hard_idx,
                lambda i: bf[i] != gold[i] and cm_pred[i] == gold[i],
            )
            examples["hard_comm_errors"] = collect_examples(
                test, dictionary, sim, gold, bf, cm_pred, hard_idx,
                lambda i: cm_pred[i] != gold[i],
            )
            examples["nonhard_fuzzy_beats_comm"] = collect_examples(
                test, dictionary, sim, gold, bf, cm_pred, nonhard_idx,
                lambda i: bf[i] == gold[i] and cm_pred[i] != gold[i],
            )

        summary = {
            "verdict": verdict,
            "primary": {
                "metric": "accuracy_full_test",
                "best_baseline": base,
                "commercial": comm,
                "gain_over_baseline": gain,
                "target_margin": MARGIN,
                "commercial_ci95": [lo, hi],
            },
            "subsets": {
                "all": {"n": len(test)},
                "hard": {"n": len(hard_idx), "criterion": "best dictionary char-3gram similarity < 0.5"},
                "nonhard": {"n": len(nonhard_idx)},
            },
            "metrics": accs,
            "pairwise_fuzzy_vs_comm": pairwise,
            "examples": examples,
        }
        json.dump(summary, open(os.path.join(OUT, "summary.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
