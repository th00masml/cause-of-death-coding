"""Recompute every number and figure in the preprint from the cached outputs.
Run from the repository's src/ directory:  python analysis_paper.py
Writes figures to ../paper/figs/ and the HARD table to ../paper/hard_table.tex.
Needs numpy and matplotlib only. Exploratory analyses; the preregistered
primary endpoint is produced by report.py."""
import collections
import json
import os
from math import comb

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "outputs")
PAPER = os.path.join(ROOT, "paper")
FIGS = os.path.join(PAPER, "figs")
os.makedirs(FIGS, exist_ok=True)

METHODS = ["B_majority", "B_fuzzy", "M_local_qwen14b", "M_comm_sonnet5"]
NAMES = {"B_fuzzy": "Fuzzy dictionary", "M_local_qwen14b": "Qwen2.5-14B (local)",
         "M_comm_sonnet5": "Claude Sonnet 5"}
COLS = {"B_fuzzy": "#555555", "M_local_qwen14b": "#e08a2e", "M_comm_sonnet5": "#2a6fb0"}

test = json.load(open(os.path.join(ROOT, "data/derived/test.json")))
sim = np.array(json.load(open(os.path.join(OUT, "test_dictsim.json"))))
g = np.array([t["chapter"] for t in test])
P = {m: np.array(json.load(open(os.path.join(OUT, f"pred_{m}.json")))["pred"]) for m in METHODS}
ALL = np.arange(len(g))
HARD = np.where(sim < 0.5)[0]
NONHARD = np.where(sim >= 0.5)[0]
rng = np.random.default_rng(0)
STATS = {"note": "Exploratory analyses for the preprint; recomputed from cached outputs. Primary endpoint is in summary.json."}


def acc(p, idx=ALL):
    return float((p[idx] == g[idx]).mean())


def boot_acc(p, idx, n=2000):
    r = np.random.default_rng(0)
    return np.percentile([(p[s] == g[s]).mean() for s in (r.choice(idx, len(idx)) for _ in range(n))], [2.5, 97.5])


def per_class_f1(p, idx=ALL):
    out = {}
    for L in set(g[idx]):
        gg, pp = g[idx], p[idx]
        tp = ((gg == L) & (pp == L)).sum(); fp = ((gg != L) & (pp == L)).sum(); fn = ((gg == L) & (pp != L)).sum()
        pr = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        out[L] = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    return out


def macro_f1(p, idx=ALL):
    return float(np.mean(list(per_class_f1(p, idx).values())))


def mcnemar_exact(a, b, idx):
    a_only = int(((a[idx] == g[idx]) & (b[idx] != g[idx])).sum())
    b_only = int(((b[idx] == g[idx]) & (a[idx] != g[idx])).sum())
    n, k = a_only + b_only, min(a_only, b_only)
    p = min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)
    return a_only, b_only, p


print("== accuracy with bootstrap CI ==")
STATS["accuracy"] = {}
for m in METHODS:
    STATS["accuracy"][m] = {k: [acc(P[m], idx), *boot_acc(P[m], idx).round(3).tolist()]
                            for k, idx in [("all", ALL), ("hard", HARD), ("nonhard", NONHARD)]}
    print(f"{m:16} all {acc(P[m]):.3f} {boot_acc(P[m], ALL).round(3)}  hard {acc(P[m], HARD):.3f} "
          f"{boot_acc(P[m], HARD).round(3)}  nonhard {acc(P[m], NONHARD):.3f} {boot_acc(P[m], NONHARD).round(3)}")

print("== macro-F1 with bootstrap CI ==")
STATS["macro_f1"] = {}
for m in METHODS:
    vals = [macro_f1(P[m], rng.choice(ALL, len(ALL))) for _ in range(1000)]
    STATS["macro_f1"][m] = [macro_f1(P[m]), *np.percentile(vals, [2.5, 97.5]).round(3).tolist()]
    print(f"{m:16} {macro_f1(P[m]):.3f} {np.percentile(vals, [2.5, 97.5]).round(3)}")

print("== paired comparison: Sonnet-5 minus Fuzzy ==")
a, b = P["B_fuzzy"], P["M_comm_sonnet5"]
for name, idx in [("all", ALL), ("hard", HARD), ("nonhard", NONHARD)]:
    d = [(b[s] == g[s]).mean() - (a[s] == g[s]).mean() for s in (rng.choice(idx, len(idx)) for _ in range(5000))]
    a_only, b_only, pv = mcnemar_exact(a, b, idx)
    STATS.setdefault("sonnet5_minus_fuzzy", {})[name] = {
        "diff": acc(b, idx) - acc(a, idx), "ci95": np.percentile(d, [2.5, 97.5]).round(3).tolist(),
        "fuzzy_only_correct": a_only, "sonnet5_only_correct": b_only, "mcnemar_exact_p": pv}
    print(f"{name:8} diff {acc(b, idx) - acc(a, idx):+.3f} CI {np.percentile(d, [2.5, 97.5]).round(3)} "
          f"fuzzy-only {a_only} sonnet-only {b_only} McNemar p={pv:.4f}")
d = [macro_f1(b, s) - macro_f1(a, s) for s in (rng.choice(ALL, len(ALL)) for _ in range(2000))]
print(f"macro-F1 diff {macro_f1(b) - macro_f1(a):+.3f} CI {np.percentile(d, [2.5, 97.5]).round(3)}")
STATS["sonnet5_minus_fuzzy"]["macro_f1"] = {"diff": macro_f1(b) - macro_f1(a), "ci95": np.percentile(d, [2.5, 97.5]).round(3).tolist()}

print("== accuracy by similarity bin ==")
BINS = [(0, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 1.01)]
STATS["accuracy_by_similarity_bin"] = []
for lo, hi in BINS:
    idx = np.where((sim >= lo) & (sim < hi))[0]
    print(f"[{lo:.1f},{hi:.1f}) n={len(idx):3d} " + " ".join(f"{m}={acc(P[m], idx):.3f}" for m in NAMES))
    STATS["accuracy_by_similarity_bin"].append({"lo": lo, "hi": min(hi, 1.0), "n": int(len(idx)), **{m: acc(P[m], idx) for m in NAMES}})

print("== Injury merged into ExternalCause (post hoc) ==")
STATS["injury_merged_into_externalcause_posthoc"] = {}
for m in NAMES:
    pm = np.where(P[m] == "Injury", "ExternalCause", P[m])
    print(f"{m:16} injury preds {(P[m] == 'Injury').sum():2d}  acc {acc(P[m]):.3f} -> {acc(pm):.3f}")
    STATS["injury_merged_into_externalcause_posthoc"][m] = {
        "injury_predictions": int((P[m] == "Injury").sum()), "acc_all": acc(P[m]), "acc_all_merged": acc(pm),
        "acc_hard_merged": acc(pm, HARD), "acc_nonhard_merged": acc(pm, NONHARD)}

print("== confusions ==")
for m in ["B_fuzzy", "M_comm_sonnet5"]:
    cf = collections.Counter((str(g[i]), str(P[m][i])) for i in ALL if P[m][i] != g[i])
    print(m, cf.most_common(7))
    STATS.setdefault("top_confusions_gold_to_pred", {})[m] = [[a_, b_, n_] for (a_, b_), n_ in cf.most_common(10)]
STATS["per_chapter_f1"] = {m: {str(k): v for k, v in per_class_f1(P[m]).items()} for m in NAMES}

print("== routed hybrid ==")
taus = np.linspace(0, 1.0, 101)
for m in ["M_comm_sonnet5", "M_local_qwen14b"]:
    curve = [acc(np.where(sim >= t, P["B_fuzzy"], P[m])) for t in taus]
    h05 = np.where(sim >= 0.5, P["B_fuzzy"], P[m])
    print(f"{m}: tau=0.5 acc {acc(h05):.3f} macroF1 {macro_f1(h05):.3f}; best tau {taus[int(np.argmax(curve))]:.2f} acc {max(curve):.3f}")
    STATS.setdefault("routed_hybrid", {})[m] = {
        "rule": "dictionary chapter if best similarity >= tau, else model chapter",
        "tau_0.5_preregistered_cut": {"acc": acc(h05), "macro_f1": macro_f1(h05)},
        "best_tau_posthoc_upper_bound": {"tau": float(taus[int(np.argmax(curve))]), "acc": float(max(curve))},
        "curve": [[float(t), float(c)] for t, c in zip(taus, curve)]}
oracle = ((P["B_fuzzy"] == g) | (P["M_comm_sonnet5"] == g)).mean()
print(f"oracle union {oracle:.3f}")
STATS["oracle_union_fuzzy_sonnet5"] = float(oracle)
json.dump(STATS, open(os.path.join(OUT, "paper_stats.json"), "w"), indent=1, default=float)
print("wrote outputs/paper_stats.json")

# ---- figures ----
plt.rcParams.update({"font.size": 9, "font.family": "serif", "axes.spines.top": False, "axes.spines.right": False})

fig, ax = plt.subplots(figsize=(5.2, 2.9))
w = 0.26
for k, m in enumerate(NAMES):
    accs = [acc(P[m], np.where((sim >= lo) & (sim < hi))[0]) for lo, hi in BINS]
    ax.bar(np.arange(len(BINS)) + (k - 1) * w, accs, w, label=NAMES[m], color=COLS[m])
ax.set_xticks(range(len(BINS)))
ax.set_xticklabels([f"[{lo:.1f},{min(hi, 1.0):.1f}{')' if hi < 1 else ']'}\nn={((sim >= lo) & (sim < hi)).sum()}" for lo, hi in BINS])
ax.set_xlabel("Best char-3gram cosine similarity to any dictionary string"); ax.set_ylabel("Chapter accuracy"); ax.set_ylim(0, 1)
ax.axvline(1.5, color="k", ls=":", lw=0.8); ax.text(1.55, 0.97, "HARD | non-HARD", va="top", fontsize=7)
ax.legend(frameon=False, fontsize=7, loc="lower right")
fig.tight_layout(); fig.savefig(os.path.join(FIGS, "acc_by_similarity.pdf"))

fig, ax = plt.subplots(figsize=(5.2, 3.1))
for m, lab in [("M_comm_sonnet5", "dictionary if sim \u2265 \u03c4, else Claude Sonnet 5"),
               ("M_local_qwen14b", "dictionary if sim \u2265 \u03c4, else Qwen2.5-14B")]:
    ax.plot(taus, [acc(np.where(sim >= t, P["B_fuzzy"], P[m])) for t in taus], color=COLS[m], label=lab)
ax.axhline(acc(P["B_fuzzy"]), color="#555555", ls="--", lw=0.9, label=f"Fuzzy dictionary alone ({acc(P['B_fuzzy']):.3f})")
ax.axhline(acc(P["M_comm_sonnet5"]), color="#2a6fb0", ls=":", lw=0.9, label=f"Claude Sonnet 5 alone ({acc(P['M_comm_sonnet5']):.3f})")
ax.axhline(0.757, color="red", ls="-.", lw=0.8, label="Preregistered target (0.757)")
ax.axvline(0.5, color="k", ls=":", lw=0.8); ax.text(0.49, 0.81, "\u03c4 = 0.5 (preregistered HARD cut)", fontsize=6.5, ha="right", va="top")
ax.set_xlabel("Routing threshold \u03c4 on best dictionary similarity"); ax.set_ylabel("Accuracy (n=300)"); ax.set_ylim(0.5, 0.82)
ax.legend(frameon=False, fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=2)
fig.tight_layout(); fig.savefig(os.path.join(FIGS, "hybrid_routing.pdf"), bbox_inches="tight")

cnt = collections.Counter(g); chs = [c for c, _ in cnt.most_common()]
M = np.array([[per_class_f1(P[m])[c] for c in chs] for m in NAMES])
fig, ax = plt.subplots(figsize=(5.4, 1.9))
ax.imshow(M, cmap="Blues", vmin=0, vmax=1, aspect="auto")
ax.set_yticks(range(3)); ax.set_yticklabels([NAMES[m] for m in NAMES], fontsize=7)
ax.set_xticks(range(len(chs))); ax.set_xticklabels([f"{c}\n({cnt[c]})" for c in chs], rotation=60, ha="right", fontsize=6)
for i in range(3):
    for j in range(len(chs)):
        ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=5.5, color="white" if M[i, j] > 0.6 else "black")
ax.spines[:].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(FIGS, "per_chapter_f1.pdf"))

# ---- HARD table for the appendix ----
def esc(s):
    return s.replace("&", "\\&").replace("_", "\\_")

rows = []
for i in HARD:
    gold = g[i]
    cell = lambda p: f"\\textbf{{{esc(p)}}}" if p == gold else esc(p)
    rows.append(f"{esc(test[i]['string'])} & {esc(gold)} & {cell(P['B_fuzzy'][i])} & {cell(P['M_comm_sonnet5'][i])} \\\\")
open(os.path.join(PAPER, "hard_table.tex"), "w").write("\n".join(rows) + "\n")
print("figures and hard_table.tex written to", PAPER)
