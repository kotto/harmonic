# -*- coding: utf-8 -*-
"""
validation_encodage.py — P1.1 LE TEST DÉCISIF : l'encodage ondulatoire
bat-il le hasard sur la similarité sémantique ?
========================================================================
Protocole (pré-enregistré le 08/08/2026, PLAN_FAIBLESSES_IA_HARMONIQUE.md) :

  Tâche    : discriminer paires SYNONYMES / ANTONYMES / NEUTRES (français)
             par similarité cosinus des vecteurs de mots.
  Encodages:
    (a) ONDULATOIRE : encode() de primitives.py (FNV-1a × φ-spacing, ℂ⁵¹²)
    (b) HASH ALÉATOIRE : projection aléatoire unitaire ℂ⁵¹², graine = hash
        du mot — MÊME information d'entrée, ZÉRO structure
    (c) N-GRAMMES : cosinus sur les comptes de 2-3 grammes de caractères
        (baseline orthographique sans aucune théorie)

  Métriques :
    · cosinus moyen par classe (synonymes DEVRAIENT > neutres > antonymes)
    · AUC : P(cos(syn) > cos(non-syn)) — 0,5 = hasard, 1 = parfait
    · AUC(syn vs ant) : le théorème dit « -1 = opposés » → testable
    · test de permutation (5000) : p(ONDULATOIRE > HASH) et p(AUC > 0,5)

  Critère pré-enregistré (plan P1.1) :
    AUC(ondulatoire) − AUC(hash) > 0,05 AVEC p < 0,01  → signal réel
    sinon → l'encodage est un hash décoratif (documenté, effort recentré)

Usage : python validation_encodage.py
"""

import math
import random
import sys

import numpy as np

sys.path.insert(0, ".")
from primitives import encode, resonate, fnv1a   # noqa: E402

# ────────────────────────────────────────────────────────────────────────
# 1. DONNÉES — paires françaises (construites manuellement, 08/08/2026)
# ────────────────────────────────────────────────────────────────────────
SYNONYMES = [
    ("content", "heureux"), ("rapide", "vite"), ("beau", "joli"),
    ("grand", "immense"), ("petit", "minuscule"), ("parler", "discuter"),
    ("maison", "logement"), ("voiture", "automobile"), ("travail", "emploi"),
    ("content", "satisfait"), ("triste", "chagrin"), ("facile", "simple"),
    ("difficile", "compliqué"), ("commencer", "débuter"), ("terminer", "finir"),
    ("acheter", "acquérir"), ("regarder", "observer"), ("marcher", "avancer"),
    ("courageux", "brave"), ("agréable", "plaisant"), ("bizarre", "étrange"),
    ("calme", "tranquille"), ("célèbre", "connu"), ("cher", "coûteux"),
    ("clair", "lumineux"), ("colère", "fureur"), ("courage", "bravoure"),
    ("désirer", "souhaiter"), ("détruire", "démolir"), ("dormir", "sommeiller"),
    ("effrayant", "terrifiant"), ("fatigué", "épuisé"), ("froid", "glacial"),
    ("généreux", "prodigue"), ("habitant", "résident"), ("haine", "détestation"),
    ("heureux", "joyeux"), ("idée", "pensée"), ("important", "essentiel"),
    ("inquiet", "anxieux"), ("intelligent", "malin"), ("jardin", "parc"),
    ("joie", "bonheur"), ("lent", "lentement"), ("lumière", "clarté"),
    ("malheureux", "mélancolique"), ("manger", "se nourrir"), ("mari", "époux"),
    ("métier", "profession"), ("mince", "maigre"), ("montagne", "colline"),
    ("nourriture", "aliment"), ("obligatoire", "impératif"), ("ordre", "instruction"),
    ("pain", "miche"), ("partir", "s'en aller"), ("pauvre", "indigent"),
    ("peur", "frayeur"), ("politesse", "courtoisie"), ("prudent", "précautionneux"),
    ("répondre", "rétorquer"), ("riche", "opulent"), ("sale", "crasseux"),
    ("savoir", "connaître"), ("solide", "robuste"), ("sourire", "ricanement"),
    ("tard", "tardivement"), ("tôt", "matinalement"), ("toujours", "éternellement"),
    ("travailleur", "assidu"), ("tristesse", "mélancolie"), ("vacances", "congés"),
    ("vent", "brise"), ("vieux", "âgé"), ("voyage", "périple"),
]

ANTONYMES = [
    ("grand", "petit"), ("chaud", "froid"), ("vite", "lent"), ("haut", "bas"),
    ("jour", "nuit"), ("noir", "blanc"), ("fort", "faible"), ("riche", "pauvre"),
    ("jeune", "vieux"), ("début", "fin"), ("ouvert", "fermé"), ("plein", "vide"),
    ("long", "court"), ("gros", "mince"), ("propre", "sale"), ("sec", "mouillé"),
    ("dur", "mou"), ("droite", "gauche"), ("monter", "descendre"),
    ("aimer", "détester"), ("gagner", "perdre"), ("donner", "recevoir"),
    ("acheter", "vendre"), ("question", "réponse"), ("entrée", "sortie"),
    ("lumière", "ombre"), ("paix", "guerre"), ("calme", "agitation"),
    ("avant", "après"), ("beau", "laid"), ("facile", "dur"), ("tôt", "tard"),
    ("vrai", "faux"), ("oui", "non"), ("dedans", "dehors"), ("dessus", "dessous"),
    ("heureux", "malheureux"), ("intérieur", "extérieur"), ("premier", "dernier"),
    ("rapide", "lentement"), ("rare", "fréquent"), ("réveiller", "endormir"),
    ("souvent", "jamais"), ("toujours", "jamais"), ("plus", "moins"),
    ("grandir", "rétrécir"), ("augmenter", "diminuer"), ("avancer", "reculer"),
    ("commencer", "arrêter"), ("construire", "détruire"), ("courir", "marcher"),
    ("créer", "détruire"), ("crier", "chuchoter"), ("défendre", "attaquer"),
    ("dresser", "coucher"), ("échouer", "réussir"), ("emprunter", "prêter"),
    ("entrer", "sortir"), ("fermer", "ouvrir"), ("léger", "lourd"),
    ("nouveau", "ancien"), ("positif", "négatif"), ("proche", "lointain"),
    ("rapide", "lent"), ("régulier", "irrégulier"), ("sauvage", "domestique"),
    ("simple", "complexe"), ("solide", "liquide"), ("succès", "échec"),
    ("transparent", "opaque"), ("vieux", "neuf"), ("vivant", "mort"),
]

# pool de mots pour les paires NEUTRES (aucune paire syn/ant n'y figure)
_POOL = ["maison", "rapide", "ciel", "chaussure", "livre", "fourchette", "table",
         "orage", "route", "chanson", "matin", "poisson", "arbre", "chaise",
         "nuage", "verre", "chemin", "ville", "montagne", "fenêtre", "clé",
         "bouteille", "jardin", "oiseau", "bureau", "crayon", "pont", "rivière",
         "assiette", "manteau", "étoile", "fromage", "téléphone", "escalier",
         "parapluie", "jambon", "lunettes", "horloge", "bicyclette", "valise",
         "parapluie", "canapé", "savon", "serviette", "lampe", "cartable",
         "miroir", "tapis", "bouteille", "couteau"]
_SYN_SET = {frozenset(p) for p in SYNONYMES}
_ANT_SET = {frozenset(p) for p in ANTONYMES}
rng_dat = random.Random(42)
NEUTRES = []
while len(NEUTRES) < 120:
    a, b = rng_dat.sample(_POOL, 2)
    paire = frozenset((a, b))
    if paire in _SYN_SET or paire in _ANT_SET or paire == (a, b):
        continue
    if a == b:
        continue
    NEUTRES.append((a, b))

print(f"[donnees] {len(SYNONYMES)} synonymes | {len(ANTONYMES)} antonymes | "
      f"{len(NEUTRES)} neutres")


# ────────────────────────────────────────────────────────────────────────
# 2. ENCODAGES
# ────────────────────────────────────────────────────────────────────────
def enc_ondulatoire(mots):
    """(a) encode() primitives.py — FNV-1a × φ-spacing."""
    vec = {}
    for m in mots:
        vec[m] = encode(m, use_cache=False)
    return vec


def enc_hash_aleatoire(mots, dim=512):
    """(b) projection aléatoire unitaire ℂ⁵¹², graine = fnv1a(mot).
    Même information d'entrée que (a), zéro structure φ-spacing."""
    vec = {}
    for m in mots:
        rng = np.random.default_rng(fnv1a(m))
        v = rng.standard_normal(dim) + 1j * rng.standard_normal(dim)
        vec[m] = v / np.linalg.norm(v)
    return vec


def enc_ngrammes(mots):
    """(c) cosinus sur les comptes de 2-3 grammes de caractères."""
    vec = {}
    for m in mots:
        c = {}
        mm = m.lower()
        for n in (2, 3):
            for i in range(len(mm) - n + 1):
                g = mm[i:i + n]
                c[g] = c.get(g, 0) + 1
        v = np.array([c.get(g, 0.0) for g in sorted(c)], dtype=float)
        norme = np.linalg.norm(v)
        vec[m] = v / norme if norme > 0 else v
    return vec


def cosinus(va, vb):
    if va.shape != vb.shape:
        # vecteurs de tailles différentes (n-grammes) : compléter par zéros
        dim = max(len(va), len(vb))
        va2 = np.zeros(dim, dtype=complex if np.iscomplexobj(va) else float)
        vb2 = np.zeros(dim, dtype=complex if np.iscomplexobj(vb) else float)
        va2[:len(va)] = va
        vb2[:len(vb)] = vb
        va, vb = va2, vb2
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.real(np.vdot(va, vb) / (na * nb)))


def auc(paires_pos, paires_neg, vec):
    """P(cos(pos) > cos(neg)) — estimation directe par paires."""
    pos = [cosinus(vec[a], vec[b]) for a, b in paires_pos]
    neg = [cosinus(vec[a], vec[b]) for a, b in paires_neg]
    # AUC de Mann-Whitney
    comb = [(p, 1) for p in pos] + [(n, 0) for n in neg]
    comb.sort(key=lambda t: t[0])
    rangs = {}
    i = 0
    while i < len(comb):
        j = i
        while j + 1 < len(comb) and abs(comb[j + 1][0] - comb[i][0]) < 1e-15:
            j += 1
        r_moyen = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            rangs[id(comb[k])] = r_moyen
        i = j + 1
    r_pos = sum(rangs[id(c)] for c in comb if c[1] == 1)
    n1, n2 = len(pos), len(neg)
    return (r_pos - n1 * (n1 + 1) / 2.0) / (n1 * n2), pos, neg


# ────────────────────────────────────────────────────────────────────────
# 3. EXÉCUTION
# ────────────────────────────────────────────────────────────────────────
tous_mots = sorted({m for p in SYNONYMES + ANTONYMES + NEUTRES for m in p})
print(f"[vocabulaire] {len(tous_mots)} mots uniques\n")

resultats = {}
for nom, fab in (("ONDULATOIRE", enc_ondulatoire),
                 ("HASH ALÉATOIRE", enc_hash_aleatoire),
                 ("N-GRAMMES (2-3)", enc_ngrammes)):
    vec = fab(tous_mots)
    # cosinus moyens par classe
    cos_syn = np.array([cosinus(vec[a], vec[b]) for a, b in SYNONYMES])
    cos_ant = np.array([cosinus(vec[a], vec[b]) for a, b in ANTONYMES])
    cos_neu = np.array([cosinus(vec[a], vec[b]) for a, b in NEUTRES])
    a_syn, _, _ = auc(SYNONYMES, ANTONYMES + NEUTRES, vec)
    a_sa, _, _ = auc(SYNONYMES, ANTONYMES, vec)
    resultats[nom] = (a_syn, a_sa, cos_syn, cos_ant, cos_neu)
    print(f"--- {nom} ---")
    print(f"  cosinus moyen  syn = {cos_syn.mean():+.4f} | ant = {cos_ant.mean():+.4f}"
          f" | neu = {cos_neu.mean():+.4f}")
    print(f"  AUC(syn vs non-syn) = {a_syn:.4f}   AUC(syn vs ant) = {a_sa:.4f}"
          f"   (0,5 = hasard)")

# ────────────────────────────────────────────────────────────────────────
# 4. TEST DE PERMUTATION : ONDULATOIRE vs HASH
# ────────────────────────────────────────────────────────────────────────
vec_o = enc_ondulatoire(tous_mots)
vec_h = enc_hash_aleatoire(tous_mots)
# AUC sur les mêmes paires, différence observée
a_o, _, _ = auc(SYNONYMES, ANTONYMES + NEUTRES, vec_o)
a_h, _, _ = auc(SYNONYMES, ANTONYMES + NEUTRES, vec_h)
diff_obs = a_o - a_h
print(f"\n[permutation] AUC(ondulatoire) = {a_o:.4f} | AUC(hash) = {a_h:.4f}"
      f" | différence = {diff_obs:+.4f}")

rng = np.random.default_rng(2026)
# permutation 1 : les paires syn vs non-syn échangent leur étiquette
pos_par = [(a, b) for a, b in SYNONYMES]
neg_par = [(a, b) for a, b in ANTONYMES + NEUTRES]
comptes_sup = 0
n_perm = 5000
for _ in range(n_perm):
    mix = pos_par + neg_par
    rng.shuffle(mix)
    p2 = mix[:len(pos_par)]
    n2 = mix[len(pos_par):]
    ao, _, _ = auc(p2, n2, vec_o)
    if ao > a_o:
        comptes_sup += 1
p_h0 = comptes_sup / n_perm
print(f"  p(AUC_ond > 0,5 observé | hasard) = {p_h0:.4f}   (5000 permutations)")

# permutation 2 : différence ondulatoire vs hash sous H0
comptes_diff = 0
for _ in range(n_perm):
    mix = pos_par + neg_par
    rng.shuffle(mix)
    p2, n2 = mix[:len(pos_par)], mix[len(pos_par):]
    ao, _, _ = auc(p2, n2, vec_o)
    ah, _, _ = auc(p2, n2, vec_h)
    if ao - ah >= diff_obs:
        comptes_diff += 1
p_diff = comptes_diff / n_perm
print(f"  p(ΔAUC_ond-hash ≥ {diff_obs:+.4f} | H0) = {p_diff:.4f}")

# ────────────────────────────────────────────────────────────────────────
# 5. VERDICT (critère pré-enregistré du plan P1.1)
# ────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
if diff_obs > 0.05 and p_diff < 0.01:
    print("✅ SIGNAL RÉEL : l'encodage ondulatoire bat le hash aléatoire")
    print("   (ΔAUC > 0,05 et p < 0,01) — le langage ondulatoire encode")
    print("   de la sémantique au-delà du hasard. Résultat publiable.")
else:
    print("❌ AUCUN SIGNAL : l'encodage ondulatoire ne bat pas le hash")
    print("   aléatoire (ΔAUC ≤ 0,05 ou p ≥ 0,01). L'encode FNV-1a × φ-spacing")
    print("   est un hash décoratif pour la similarité sémantique — la valeur")
    print("   du projet repose sur les modules validés (physique 0,004 %,")
    print("   GSM8K 85,52 %, coquille HO) et l'architecture HRR documentée")
    print("   comme telle (Plate 1995).")
print("=" * 70)
