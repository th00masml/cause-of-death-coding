"""Shared helpers: Ollama call, lexical baselines, AUC, bootstrap."""
import json
import re
import urllib.request

import numpy as np

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:14b"

_TOK = re.compile(r"[a-zA-Z]+")


def tokens(s):
    return _TOK.findall((s or "").lower())


def token_set(s):
    return set(tokens(s))


def token_jaccard(a, b):
    A, B = token_set(a), token_set(b)
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def char_ngrams(s, n=3):
    s = re.sub(r"[^a-z]", "", (s or "").lower())
    if len(s) < n:
        return {s} if s else set()
    return {s[i : i + n] for i in range(len(s) - n + 1)}


def char_ngram_cosine(a, b, n=3):
    A, B = char_ngrams(a, n), char_ngrams(b, n)
    if not A or not B:
        return 0.0
    inter = len(A & B)
    return inter / (len(A) ** 0.5 * len(B) ** 0.5)


def generate(prompt, seed=7, num_predict=12, temperature=0.0, timeout=120):
    body = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "seed": seed,
                    "num_predict": num_predict, "top_p": 1.0},
    }
    req = urllib.request.Request(
        OLLAMA_URL, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)["response"]


def parse_score(s):
    m = re.search(r"(0?\.\d+|1(?:\.0+)?|0|1)", s.strip())
    if not m:
        return None
    try:
        return max(0.0, min(1.0, float(m.group(1))))
    except ValueError:
        return None


def roc_auc(labels, scores):
    labels = np.asarray(labels)
    scores = np.asarray(scores, dtype=np.float64)
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=np.float64)
    s = scores[order]
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    n_pos = int(labels.sum())
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    u = ranks[labels == 1].sum() - n_pos * (n_pos + 1) / 2.0
    return float(u / (n_pos * n_neg))


def bootstrap_auc_ci(labels, scores, n_boot=1000, seed=0):
    rng = np.random.default_rng(seed)
    labels = np.asarray(labels)
    scores = np.asarray(scores)
    n = len(labels)
    out = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        lb = labels[idx]
        if lb.sum() in (0, len(lb)):
            continue
        out.append(roc_auc(lb, scores[idx]))
    out = np.array(out)
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


def paired_delta_ci(labels, scores_a, scores_b, n_boot=2000, seed=0):
    """CI for AUC(b) - AUC(a) on the same items."""
    rng = np.random.default_rng(seed)
    labels = np.asarray(labels)
    sa, sb = np.asarray(scores_a), np.asarray(scores_b)
    obs = roc_auc(labels, sb) - roc_auc(labels, sa)
    n = len(labels)
    d = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        lb = labels[idx]
        if lb.sum() in (0, len(lb)):
            continue
        d.append(roc_auc(lb, sb[idx]) - roc_auc(lb, sa[idx]))
    d = np.array(d)
    return obs, float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5)), float((d <= 0).mean())


# ---- commercial instrument via authenticated `claude` CLI (no API key) ----
import subprocess


def generate_cli(prompt, system=None, model="claude-sonnet-5", timeout=90):
    """Call the authenticated Claude CLI in print mode. Non-deterministic
    (no temperature control); we run once and cache the raw output."""
    cmd = ["claude", "-p", "--model", model, "--allowedTools", ""]
    if system:
        cmd += ["--append-system-prompt", system]
    cmd += [prompt]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return (r.stdout or "").strip()
