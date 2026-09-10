"""Coding-specific helpers: ICD chapter derivation, class list, metrics."""

CHAPTERS = [
    "Infectious", "Neoplasm", "Blood", "Endocrine/metabolic", "Mental",
    "Nervous", "Eye", "Ear", "Circulatory", "Respiratory", "Digestive",
    "Skin", "Musculoskeletal", "Genitourinary", "Pregnancy", "Perinatal",
    "Congenital", "Ill-defined", "Injury", "ExternalCause", "Factors", "Special",
]


def chapter(code):
    c = (code or "").strip().upper()
    if not c or not c[0].isalpha():
        return None
    L = c[0]
    try:
        num = int(c[1:3])
    except Exception:
        num = 0
    table = [("A", 0, 99, "Infectious"), ("B", 0, 99, "Infectious"),
             ("C", 0, 99, "Neoplasm"), ("D", 0, 48, "Neoplasm"),
             ("D", 50, 89, "Blood"), ("E", 0, 99, "Endocrine/metabolic"),
             ("F", 0, 99, "Mental"), ("G", 0, 99, "Nervous"),
             ("H", 0, 59, "Eye"), ("H", 60, 95, "Ear"),
             ("I", 0, 99, "Circulatory"), ("J", 0, 99, "Respiratory"),
             ("K", 0, 99, "Digestive"), ("L", 0, 99, "Skin"),
             ("M", 0, 99, "Musculoskeletal"), ("N", 0, 99, "Genitourinary"),
             ("O", 0, 99, "Pregnancy"), ("P", 0, 99, "Perinatal"),
             ("Q", 0, 99, "Congenital"), ("R", 0, 99, "Ill-defined"),
             ("S", 0, 99, "Injury"), ("T", 0, 99, "Injury"),
             ("V", 0, 99, "ExternalCause"), ("W", 0, 99, "ExternalCause"),
             ("X", 0, 99, "ExternalCause"), ("Y", 0, 99, "ExternalCause"),
             ("Z", 0, 99, "Factors"), ("U", 0, 99, "Special")]
    for LL, lo, hi, name in table:
        if L == LL and lo <= num <= hi:
            return name
    return None


def parse_chapter(text):
    """Map free model output to one of CHAPTERS (case-insensitive substring)."""
    t = (text or "").strip().lower()
    # exact-ish first
    for c in CHAPTERS:
        if c.lower() == t:
            return c
    for c in CHAPTERS:
        if c.lower() in t:
            return c
    # some aliases
    alias = {"infection": "Infectious", "cancer": "Neoplasm", "tumor": "Neoplasm",
             "heart": "Circulatory", "cardiovascular": "Circulatory",
             "lung": "Respiratory", "metabolic": "Endocrine/metabolic",
             "endocrine": "Endocrine/metabolic", "psych": "Mental",
             "neuro": "Nervous", "kidney": "Genitourinary", "urinary": "Genitourinary",
             "childbirth": "Pregnancy", "newborn": "Perinatal",
             "ill defined": "Ill-defined", "unknown": "Ill-defined",
             "external": "ExternalCause", "injury": "Injury", "poison": "Injury"}
    for k, v in alias.items():
        if k in t:
            return v
    return None


def accuracy(gold, pred):
    ok = sum(1 for g, p in zip(gold, pred) if g == p)
    return ok / len(gold) if gold else 0.0


def macro_f1(gold, pred):
    labels = set(gold)
    f1s = []
    for L in labels:
        tp = sum(1 for g, p in zip(gold, pred) if g == L and p == L)
        fp = sum(1 for g, p in zip(gold, pred) if g != L and p == L)
        fn = sum(1 for g, p in zip(gold, pred) if g == L and p != L)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return sum(f1s) / len(f1s) if f1s else 0.0


def bootstrap_acc_ci(gold, pred, n_boot=1000, seed=0):
    import numpy as np
    rng = np.random.default_rng(seed)
    g = np.array(gold)
    p = np.array(pred)
    n = len(g)
    accs = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        accs.append((g[idx] == p[idx]).mean())
    return float(np.percentile(accs, 2.5)), float(np.percentile(accs, 97.5))
