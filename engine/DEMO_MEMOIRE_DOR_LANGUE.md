# 🧠 DEMO_MEMOIRE_DOR_LANGUE — Niveau langue : la frontière mesurée entre mémoire statistique et récupération de contenu

**Date** : 09/08/2026 — **Auteur** : ZCode, avec Univers-Holistique
**Statut** : RÉSULTAT PUBLIÉ (négatif au niveau langue) — le protocole a invalidé la tâche, deux fois, avec critères pré-enregistrés
**Référence** : `THEORIE_HARMONIQUE_REFONDEE.md` — T1, T2 · leçon X3 (spectre appris)
**Script** : `memoire_dor_langue.py` — **Rapport** : `data/benchmarks/memoire_dor_langue_report.json`

---

> *Le protocole pré-enregistré a fait exactement son travail : il a invalidé le benchmark avant qu'il ne produise un faux verdict. Ce qui reste est une frontière mesurée — la plus utile pour la théorie.*

---

## 1. Ce qui était testé

L'extension « niveau langue » du Cerveau à Mémoire d'Or : embeddings **appris** (leçon X3) + mémoire **dérivée** (T1 : α=1/φ, T2 : λ=φ, zéro paramètre) sur une tâche de langue à longue dépendance, contre les mêmes baselines que le niveau série (EWMA ajusté, ABC ajusté, uniforme).

## 2. L'historique de conception (publié intégralement)

### v1 — « le pont » à remplisseurs aléatoires → INVALIDE (C3 ❌)
Séquence [clé] + [G remplisseurs aléatoires] + [sonde] → prédire la clé.
**Résultat : toutes les mémoires ≈ 25 % (le hasard)** — le critère C3 (tâche apprenable) a invalidé. Diagnostic : avec des remplisseurs purement aléatoires, la récence est du bruit pur — ce qui handicape *toute* mémoire à décroissance, y compris les baselines ajustées. Tâche non représentative de la langue.

### v2 — « la langue du pont » (prochain token + récupération) → INVALIDE (C3 ❌)
Remplisseurs avec structure locale (chaîne de Markov — la récence devient utile) + sonde de récupération, pondération de la sonde déclarée, lecteur à couche cachée, 1200 étapes.
**Résultat : encore ~25 % (le hasard) pour TOUTES les mémoires** — y compris EWMA et uniforme. C3 a invalidé à nouveau. Diagnostic mesuré :

| Observation | Mesure |
|---|---|
| La perte de langue ne décroît presque pas | 2,4846 → 2,4517 (hasard = 2,4849) sur 100 étapes |
| Le poids de la clé dans le contexte, à l'écart G | w_G/Σw ≈ 2-4 % (noyau doré), 2,4 % (uniforme) |
| La récupération | ~hasard pour toutes les mémoires, à tous les écarts |

**La cause profonde** : la clé, noyée dans le contexte pondéré à ~2-4 %, est inextractible par un lecteur entraîné par descente de gradient — quel que soit le noyau. Ce n'est pas une défaillance de la mémoire dorée : c'est une **limite de la classe d'architecture** « somme pondérée à noyau fixe + lecteur ».

## 3. La frontière mesurée — le résultat qui compte

> **Une mémoire à noyau fixe est un FILTRE STATISTIQUE, pas une MÉMOIRE ADRESSABLE PAR CONTENU.**
>
> - Le noyau doré (T1/T2) pondère le passé par décroissance : c'est une *statistique* — la bonne question est « quel poids donner au passé selon son âge ? » — validée au niveau série.
> - La récupération (« où se trouvait la clé ? ») est un *adressage par contenu* : il faut chercher dans le passé, pas le pondérer — c'est précisément ce que l'attention (mécanisme par contenu) a été inventée pour faire.
> - **La théorie ne prétend rien de plus que T1/T2** : la décroissance de la mémoire. Cette frontière est donc cohérente avec la refondation — et elle la précise : le noyau doré est un filtre statistique, pas un mécanisme d'adressage.

**Ce que la frontière interdit** : prétendre que la mémoire dorée « retrouve » des informations passées. **Ce qu'elle permet** : tout ce qui relève de la pondération statistique du passé (prédiction, lissage, mémoire de travail probabiliste) — le domaine validé au niveau série.

## 4. Ce qui reste validé (niveau série — `cerveau_memoire_dor.py`)

| Critère | Résultat |
|---|---|
| C1 · dorée vs meilleure baseline ajustée, H∈[0,65, 0,75] | ✅ marge 2,82 % (seuil 5 %) — zéro paramètre |
| C2 · benchmark non biaisé (bruit blanc) | ✅ gain 0,58 % vs optimum · pénalité dorée 4,88 % |
| C3 · refus calibré | ✅ 100 % sur bruit blanc, 0 % faux refus |
| Régime doré H = 0,691 | ✅ bat les baselines simples, marge 1,5 % vs oracle de Wiener appris |

## 5. La suite recommandée — v3 (statistique longue portée, pas récupération)

La version qui reste à écrire, cohérente avec la frontière : **la langue à influence longue** — prochain token dont la distribution dépend du token à distance L (structure statistique longue portée, pas adressage) :

```
x_t dépend de x_{t−1} (local, Markov) ET de x_{t−L} (longue portée, L ∈ {5,20,40})
→ perte pure de modélisation de langue (pas de sonde)
→ la mémoire doit PONDÉRER x_{t−L} : la queue τ^{−1/φ} du noyau doré
  (loi de puissance) vs l'oubli exponentiel de l'EWMA
→ critères : C1 dorée dans 5 % de la meilleure ajustée à L ≥ 20 ·
  C2 dorée ≥ EWMA à L ≥ 20 · C3 tâche apprenable (perte < hasard)
```

C'est l'analogue discret exact de la démonstration série validée — le domaine où T1/T2 ont leur mot à dire.

## 6. Reproductibilité

```bash
# Le niveau langue (v1 et v2 — les deux invalidations publiées)
python memoire_dor_langue.py
# → data/benchmarks/memoire_dor_langue_report.json (verdict ❌ — benchmark invalide)

# Le niveau série (VALIDÉ — la démonstration qui tient)
python cerveau_memoire_dor.py
# → data/benchmarks/memoire_dor_report.json (verdict ✅ — les 3 critères)
```

---

*Démonstration langue — FIN — deux invalidations publiées, une frontière mesurée, une suite tracée : la mémoire dorée est un filtre statistique validé, pas un adressage de contenu — et la théorie ne prétend rien d'autre.*
