"""Aggregate baselines + models; overall and on the HARD (novel-string)
subset; apply the preregistered kill criterion."""
import json
import os

from common_coding import accuracy, bootstrap_acc_ci

HERE = os.path.dirname(__file__)
ROOT = os.path.dirname(HERE)
DERIVED = os.path.join(ROOT, "data/derived")
OUT = os.path.join(ROOT, "outputs")
MARGIN = 0.05


def load(n):
    p = os.path.join(OUT, f"pred_{n}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def main():
    test = json.load(open(os.path.join(DERIVED, "test.json")))
    gold = [t["chapter"] for t in test]
    sim = json.load(open(os.path.join(OUT, "test_dictsim.json")))
    hard_idx = [i for i, s in enumerate(sim) if s < 0.5]

    methods = ["B_majority", "B_fuzzy", "M_local_qwen14b", "M_comm_sonnet5"]
    res = {m: load(m) for m in methods}
    print(f"{'method':18} {'acc(all)':>9} {'acc(hard)':>10} {'macroF1':>8}")
    accs = {}
    for m in methods:
        r = res[m]
        if not r:
            continue
        pred = r["pred"]
        a = accuracy(gold, pred)
        ah = accuracy([gold[i] for i in hard_idx], [pred[i] for i in hard_idx]) if hard_idx else float("nan")
        accs[m] = (a, ah)
        print(f"{m:18} {a:9.4f} {ah:10.4f} {r.get('macro_f1',0):8.4f}")

    print(f"\nHARD subset (novel strings, dict sim<0.5): n={len(hard_idx)}")
    if "M_comm_sonnet5" in accs:
        base = max(accs.get("B_majority", (0,))[0], accs.get("B_fuzzy", (0,))[0])
        comm = accs["M_comm_sonnet5"][0]
        gain = comm - base
        # CI for commercial on full test
        cm = res["M_comm_sonnet5"]
        lo, hi = cm["ci95"]
        passed = gain >= MARGIN
        verdict = "BUILT" if passed else "KILLED-AT-4-not-beaten"
        print(f"\n--- PRIMARY (full test) ---")
        print(f"best baseline acc = {base:.4f}  commercial acc = {comm:.4f}  gain = {gain:+.4f} (need +{MARGIN})")
        print(f"commercial 95% CI [{lo:.4f},{hi:.4f}]")
        print(f"VERDICT: {verdict}")
        if hard_idx and "B_fuzzy" in accs:
            print(f"\n(secondary) HARD subset: B_fuzzy {accs['B_fuzzy'][1]:.4f} "
                  f"vs commercial {accs['M_comm_sonnet5'][1]:.4f} "
                  f"vs local {accs.get('M_local_qwen14b',(0,0))[1]:.4f}")
        json.dump({"verdict": verdict, "acc": {m: accs[m] for m in accs},
                   "gain_over_baseline": gain, "n_hard": len(hard_idx)},
                  open(os.path.join(OUT, "summary.json"), "w"), indent=2)


if __name__ == "__main__":
    main()
