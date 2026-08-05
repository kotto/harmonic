# -*- coding: utf-8 -*-
"""Axe 6 — COMPOSANT APPRIS : prédire le rôle sémantique de chaque nombre.

Vérité terrain : les chaînes officielles taggées (Q-operands). Pour chaque
nombre de chaque énoncé, son rôle = l'op de l'étape où il est lié
(ADD→add, SUB→sub, MUL→mul, DIV→div, CONST→init) ; non lié → noise.

Features (extractibles de la question SEULE, 0 vérité) : contexte local
±2 mots, magnitude, position, phrase, marqueurs (per/each/than/times/of).

Classifieur : softmax multiclasse (numpy pur, 0 dépendance), 5-fold par
PROBLÈME (jamais vu en entraînement). Le critère de décision :
  - précision des SLOTS (non-noise) significativement haute → voie viable ;
  - ≈ chance/trivial → la représentation apprise n'apporte rien.
"""
import math
import re
import sys
import time
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

import numpy as np

from benchmark_gsm8k import load_gsm8k
from wave_gsm8k import GSM8KChainMemory

problems = load_gsm8k()
N = len(problems)
print('total :', N)
t0 = time.time()

mem = GSM8KChainMemory()
mem.load()

# ═══════════ 1. Vérité terrain : rôle officiel de chaque nombre ══════════════
ROLE_OF = {'ADD': 'add', 'SUB': 'sub', 'MUL': 'mul', 'DIV': 'div',
           'CONST': 'init'}
data = []           # (question, texte normalisé, positions des nombres, rôles)
for pat in mem.patterns:
    q = pat['question']
    qn = re.sub(r'(\d),(\d{3})(?:\.\d+)?', r'\1\2', pat['question'].lower())
    pos = [(m.start(), m.end(), float(m.group(1).replace(',', '')))
           for m in re.finditer(r'(\d+(?:\.\d+)?)\s*%?', qn)]
    roles = ['noise'] * len(pos)
    for st in pat['chain'].steps:
        for slot in ('a', 'b'):
            o = getattr(st, slot)
            if o is not None and o[0] == 'Q' and o[1] < len(roles):
                roles[o[1]] = ROLE_OF.get(st.op, 'noise')
    data.append((q, qn, pos, roles))

n_nums = sum(len(p) for _q, _qn, p, _r in data)
n_slots = sum(1 for _q, _qn, p, r in data for x in r if x != 'noise')
print('nombres : %d | slots liés (non-noise) : %d (%.1f%%)'
      % (n_nums, n_slots, 100.0 * n_slots / max(1, n_nums)))
print('distribution des rôles :', dict(Counter(
    x for _q, _qn, p, r in data for x in r)))

# ═══════════ 2. Features sémantiques par nombre ══════════════════════════════
_VERBES = re.compile(r'\b(has|have|had|buys?|bought|sells?|sold|gives?|gave|'
                     r'eats?|ate|spends?|spent|costs?|cost|pays?|paid|earns?|'
                     r'earned|makes?|made|takes?|took|gets?|got|receives?|'
                     r'finds?|found|plants?|planted|runs?|ran|walks?|walked|'
                     r'works?|worked|wants?|wanted|uses?|used|spends?|'
                     r'weighs?|weighed|contains?|contained)\b')
_MARKERS = ['per', 'each', 'than', 'times', 'of', 'as', 'dozen', 'dollars',
            'dollar', 'cent', 'percent', '%', 'left', 'remain', 'total',
            'combined', 'altogether', 'more', 'less', 'fewer', 'every',
            'after', 'before', 'for', 'at', 'costs', 'cost', 'sold', 'bought']

def feats(q, qn, occ, n_tot):
    """Vecteur de features pour l'occurrence (start, end, valeur)."""
    s, e, v = occ
    ctx_l = qn[max(0, s - 60):s]
    ctx_r = qn[e:e + 60]
    words = re.findall(r'[a-z]+', ctx_l[-12:])[-2:] + \
            re.findall(r'[a-z]+', ctx_r[:12])[:2]
    f = {}
    for w in words:
        f['w:' + w] = f.get('w:' + w, 0) + 1
    for mk in _MARKERS:
        if mk in ctx_l[-20:] or mk in ctx_r[:20]:
            f['mk:' + mk] = 1
    if _VERBES.search(ctx_l[-30:]):
        f['verb_l'] = 1
    if _VERBES.search(ctx_r[:30]):
        f['verb_r'] = 1
    f['log10'] = math.log10(v + 1.0) / 6.0
    f['pos_rel'] = s / max(1, len(qn))
    f['n_nums'] = min(n_tot, 8) / 8.0
    return f

samples = []        # (features dict, label, idx_problème)
for pi, (q, qn, pos, roles) in enumerate(data):
    for k, (occ, r) in enumerate(zip(pos, roles)):
        samples.append((feats(q, qn, occ, len(pos)), r, pi))
print('échantillons :', len(samples))

# Vocabulaire des features (fréquence ≥ 3)
vocab = Counter()
for fdict, _r, _pi in samples:
    for key in fdict:
        vocab[key] += 1
vocab = {k for k, c in vocab.items() if c >= 3}
v2i = {k: i for i, k in enumerate(sorted(vocab))}
print('features :', len(v2i))
LABELS = ['add', 'sub', 'mul', 'div', 'init', 'noise']
l2i = {l: i for i, l in enumerate(LABELS)}

X = np.zeros((len(samples), len(v2i)), dtype=np.float64)
y = np.zeros(len(samples), dtype=int)
pid = np.zeros(len(samples), dtype=int)
for n, (fdict, r, pi) in enumerate(samples):
    for key, val in fdict.items():
        j = v2i.get(key)
        if j is not None:
            X[n, j] += val
    y[n] = l2i[r]
    pid[n] = pi

# ═══════════ 3. Softmax multiclasse, 5-fold par PROBLÈME ═════════════════════
rng = np.random.RandomState(0)
folds = []
order = rng.permutation(N)
k = 5
for i in range(k):
    folds.append(set(order[i::k]))

def softmax_train(Xtr, ytr, lr=0.3, epochs=60, lam=1e-4):
    n, d = Xtr.shape
    W = np.zeros((len(LABELS), d))
    for _ in range(epochs):
        scores = Xtr @ W.T
        exp = np.exp(scores - scores.max(axis=1, keepdims=True))
        p = exp / exp.sum(axis=1, keepdims=True)
        g = (p - np.eye(len(LABELS))[ytr]).T @ Xtr / n
        W -= lr * (g + lam * W)
    return W

slot_tp = slot_tot = 0
conf = np.zeros((len(LABELS), len(LABELS)))
acc_total = acc_slot = tot_total = tot_slot = 0
for fi, test_ids in enumerate(folds):
    te = np.isin(pid, list(test_ids))
    tr = ~te
    W = softmax_train(X[tr], y[tr])
    pred = X[te] @ W.T
    pred = pred.argmax(axis=1)
    yt = y[te]
    acc_total += (pred == yt).sum()
    tot_total += len(yt)
    for a, b in zip(pred, yt):
        conf[a, b] += 1
        if b != l2i['noise']:
            tot_slot += 1
            if a == b:
                acc_slot += 1
    print('  fold %d : acc totale %.1f%% | acc slots %.1f%%'
          % (fi + 1, 100.0 * (pred == yt).mean(),
             100.0 * np.mean(pred[yt != l2i['noise']] ==
                             yt[yt != l2i['noise']]) if (yt != l2i['noise']).any() else 0))

print()
print('ACC totale (5-fold, par problème) : %.1f%%' % (100.0 * acc_total / tot_total))
print('ACC SLOTS (non-noise, jamais vus)  : %.1f%% (%d/%d)'
      % (100.0 * acc_slot / max(1, tot_slot), acc_slot, tot_slot))
print()
print('Matrice de confusion (prédit en lignes, vérité en colonnes) :')
print('        ' + ' '.join('%-6s' % l for l in LABELS))
for i, l in enumerate(LABELS):
    row = ' '.join('%5d ' % conf[i, j] for j in range(len(LABELS)))
    print('%-7s %s' % (l, row))
print('durée totale : %.0f s' % (time.time() - t0))
