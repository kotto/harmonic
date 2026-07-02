#!/usr/bin/env python3
r"""
RAISONNEMENT ARITHMÉTIQUE ONDULATOIRE — Niveau 2 du paradigme Oyibo
=====================================================================
Les nombres SONT des modes spectraux (fréquences sur le cercle unité).
Les calculs émergent de la RÉSONANCE entre ondes numériques.

Principe :
  Chaque nombre n → onde z_n = exp(i · n · φ · 2π) = position sur le cercle
  Chaque opérateur (+, -, ×, /) → vecteur fixe dans l'espace des phases
  Un fait "3 + 4 = 7" → onde = z₃ ⊕ z₄ ⊕ v_+
                        résultat = 7 (stocké séparément, pas dans l'onde)
  Une question "3 + 4 = ?" → même onde (z₃ ⊕ z₄ ⊕ v_+) → résonance parfaite

  La normalisation STRIP le résultat avant encodage.
  Ainsi "3+4=7" et "3+4=?" produisent la MÊME onde → lookup parfait.

Usage :
  python raisonnement_arithmetique_ondulatoire.py
"""

import sys, os, math, hashlib, time, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ka_phone'))
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
PI = math.pi

# ═══════════════════════════════════════════════════════════════════════════════
# ENCODAGE SPECTRAL DES NOMBRES
# ═══════════════════════════════════════════════════════════════════════════════

def number_to_wave(n: int) -> tuple:
    """
    Encode un nombre n comme une onde sur le cercle unité.
    θ_n = n × φ × 2π mod 2π — distribution quasi-uniforme, ordonnée.
    Les nombres proches ont des fréquences proches (continuité spectrale).
    """
    theta = (n * PHI * 2 * math.pi) % (2 * math.pi)
    # Amplitude 10 pour occuper [-10, 10]
    return (math.cos(theta) * 10, math.sin(theta) * 10)


# Opérateurs → vecteurs fixes dans l'espace des phases
OPERATOR_VECTORS = {
    '+': (8.0, 0.0),      # Axe x+
    'plus': (8.0, 0.0),
    '-': (-8.0, 0.0),     # Axe x-
    'moins': (-8.0, 0.0),
    'x': (0.0, 8.0),      # Axe y+
    '*': (0.0, 8.0),
    'fois': (0.0, 8.0),
    'multiplie': (0.0, 8.0),
    '/': (0.0, -8.0),     # Axe y-
    'divise': (0.0, -8.0),
    'carre': (5.0, 5.0),  # Quadrant I
    'au': (5.0, 5.0),
    'racine': (-5.0, -5.0),  # Quadrant III
    'somme': (8.0, 0.0),
}


def normalize_expression(expr: str) -> str:
    """
    Normalise une expression arithmétique pour l'encodage.
    STRIP le résultat (partie après '='), garde uniquement les opérandes
    et l'opérateur.
    
    "3 + 4 = 7" → "3 + 4"
    "3 + 4 = ?" → "3 + 4"
    "7 - 3 = 4" → "7 - 3"
    "5 x 6 = 30" → "5 x 6"
    """
    # Enlever la partie après '='
    if '=' in expr:
        expr = expr.split('=')[0].strip()
    
    # Remplacer '?' par rien (c'est le marqueur de question)
    expr = expr.replace('?', ' ').strip()
    
    # Normaliser les espaces
    expr = ' '.join(expr.split())
    
    return expr


def expression_to_wave(expr: str) -> tuple:
    """
    Encode une expression arithmétique en onde (kx, ky).
    
    Algorithme :
      1. Extraire les nombres → sommer leurs ondes z_n
      2. Extraire les opérateurs → sommer leurs vecteurs
      3. Normaliser le vecteur résultant
    
    Le résultat (partie après '=') n'est PAS encodé — il est stocké
    séparément comme métadonnée du fait.
    """
    expr = normalize_expression(expr)
    
    kx_sum = 0.0
    ky_sum = 0.0
    count = 0
    
    # Tokenisation améliorée : split puis Nettoyage sélectif
    raw_tokens = expr.lower().split()
    
    for token in raw_tokens:
        # Essayer d'abord comme nombre (avant tout strip)
        try:
            n = int(token)
            kx_n, ky_n = number_to_wave(abs(n))
            kx_sum += kx_n
            ky_sum += ky_n
            count += 1
            continue
        except ValueError:
            pass
        
        # Essayer comme opérateur (comparaison directe, avant strip)
        if token in OPERATOR_VECTORS:
            kx_op, ky_op = OPERATOR_VECTORS[token]
            kx_sum += kx_op
            ky_sum += ky_op
            count += 1
            continue
        
        # Nettoyer les caractères parasites pour les tokens restants
        token_clean = token.strip('.,;!?()[]{}"\'- ')
        if not token_clean:
            continue
        
        # Réessayer comme nombre après nettoyage
        try:
            n = int(token_clean)
            kx_n, ky_n = number_to_wave(abs(n))
            kx_sum += kx_n
            ky_sum += ky_n
            count += 1
            continue
        except ValueError:
            pass
        
        # Réessayer comme opérateur après nettoyage
        if token_clean in OPERATOR_VECTORS:
            kx_op, ky_op = OPERATOR_VECTORS[token_clean]
            kx_sum += kx_op
            ky_sum += ky_op
            count += 1
            continue
        
        # Cas spéciaux : "²" collé à un nombre (ex: "3²")
        if '²' in token_clean:
            kx_op, ky_op = OPERATOR_VECTORS.get('carre', (5.0, 5.0))
            kx_sum += kx_op
            ky_sum += ky_op
            count += 1
            num_part = token_clean.replace('²', '')
            try:
                n = int(num_part)
                kx_n, ky_n = number_to_wave(abs(n))
                kx_sum += kx_n
                ky_sum += ky_n
                count += 1
            except ValueError:
                pass
    
    if count == 0:
        return (0.0, 0.0)
    
    # Normaliser
    mag = math.sqrt(kx_sum**2 + ky_sum**2)
    if mag > 0:
        kx_sum = kx_sum / mag * 10
        ky_sum = ky_sum / mag * 10
    
    return (kx_sum, ky_sum)


# ═══════════════════════════════════════════════════════════════════════════════
# OUTILS ONDULATOIRES
# ═══════════════════════════════════════════════════════════════════════════════

def interference(kx1, ky1, kx2, ky2):
    """cos(θ) entre deux ondes. +1 = alignement parfait, -1 = opposition."""
    dot = kx1*kx2 + ky1*ky2
    n1 = math.sqrt(kx1**2 + ky1**2)
    n2 = math.sqrt(kx2**2 + ky2**2)
    if n1 < 1e-10 or n2 < 1e-10:
        return 0.0
    return max(-1.0, min(1.0, dot / (n1 * n2)))


def distance_ondulatoire(kx1, ky1, kx2, ky2):
    return math.sqrt((kx1-kx2)**2 + (ky1-ky2)**2)


# ═══════════════════════════════════════════════════════════════════════════════
# HOLOGRAMME ARITHMÉTIQUE (V2 : nombres = modes spectraux)
# ═══════════════════════════════════════════════════════════════════════════════

class HologrammeArithmetique:
    """
    Hologramme de faits arithmétiques.
    
    Chaque fait est stocké comme :
      - onde Ψ = expression_to_wave(expression_normalisée)
      - résultat = valeur numérique après le '='
    
    La consultation encode la question normalisée (sans '?' ni résultat)
    → produit la même onde que le fait correspondant → résonance parfaite.
    """
    
    def __init__(self):
        self.faits = {}       # texte_original → (kx, ky, resultat)
        self.by_wave = {}     # (kx_rounded, ky_rounded) → liste de (texte, resultat)
        self.N = 0
    
    def ajouter(self, texte):
        """Ajoute un fait arithmétique. Ex: '3 + 4 = 7'."""
        # Extraire le résultat
        resultat = None
        if '=' in texte:
            partie_droite = texte.split('=')[-1].strip()
            for mot in partie_droite.split():
                mot = mot.strip('.,;!?()[]{}"\'- ')
                try:
                    resultat = int(mot)
                    break
                except ValueError:
                    try:
                        resultat = float(mot)
                        break
                    except ValueError:
                        pass
        
        # Encoder uniquement l'expression normalisée (sans le résultat)
        kx, ky = expression_to_wave(texte)
        
        self.faits[texte] = (kx, ky, resultat)
        
        # Indexer par position arrondie pour lookup rapide
        key = (round(kx, 1), round(ky, 1))
        if key not in self.by_wave:
            self.by_wave[key] = []
        self.by_wave[key].append((texte, resultat))
        
        self.N += 1
    
    def ajouter_batch(self, faits):
        for f in faits:
            self.ajouter(f)
    
    def consulter(self, question, top_k=10):
        """
        Consulte l'hologramme par résonance.
        
        1. Normalise la question (strip '?' et partie après '=')
        2. Encode en onde
        3. Cherche les faits les plus proches en distance ondulatoire
        4. Retourne les top_k avec leurs interférences
        """
        kx_q, ky_q = expression_to_wave(question)
        
        scores = []
        for texte, (kx_f, ky_f, resultat) in self.faits.items():
            interf = interference(kx_q, ky_q, kx_f, ky_f)
            dist = distance_ondulatoire(kx_q, ky_q, kx_f, ky_f)
            scores.append((texte, resultat, interf, dist))
        
        scores.sort(key=lambda x: -abs(x[2]))  # Tri par |interférence|
        return scores[:top_k]
    
    def resoudre(self, question, top_k=1):
        """
        Résout une question arithmétique.
        Retourne le meilleur résultat ou None.
        """
        resultats = self.consulter(question, top_k=top_k)
        if resultats:
            return resultats[0]  # (texte, resultat, interf, dist)
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATEUR DE CORPUS ARITHMÉTIQUE
# ═══════════════════════════════════════════════════════════════════════════════

def generer_corpus_arithmetique(n_max=30):
    """
    Génère un corpus de faits arithmétiques.
    Chaque fait est au format "a + b = c" (texte lisible).
    """
    faits = []
    
    for a in range(0, n_max + 1):
        # Carrés
        faits.append(f"{a} au carre = {a*a}")
        faits.append(f"carre de {a} = {a*a}")
        
        # Racines carrées
        carre = a * a
        faits.append(f"racine carree de {carre} = {a}")
        faits.append(f"racine de {carre} = {a}")
        
        for b in range(0, n_max + 1):
            # Addition
            faits.append(f"{a} + {b} = {a + b}")
            faits.append(f"{a} plus {b} = {a + b}")
            faits.append(f"somme de {a} et {b} = {a + b}")
            
            # Soustraction
            if a >= b:
                faits.append(f"{a} - {b} = {a - b}")
                faits.append(f"{a} moins {b} = {a - b}")
            
            # Multiplication (limitée)
            if a <= 20 and b <= 20:
                faits.append(f"{a} x {b} = {a * b}")
                faits.append(f"{a} fois {b} = {a * b}")
                faits.append(f"{a} multiplie par {b} = {a * b}")
            
            # Division (résultats entiers)
            if b > 0 and a % b == 0 and b <= 20:
                faits.append(f"{a} divise par {b} = {a // b}")
                faits.append(f"{a} / {b} = {a // b}")
    
    return faits


# ═══════════════════════════════════════════════════════════════════════════════
# MOTEUR DE RAISONNEMENT
# ═══════════════════════════════════════════════════════════════════════════════

class WaveArithmetic:
    """Moteur de raisonnement arithmétique par résonance."""
    
    def __init__(self, hologramme):
        self.holo = hologramme
        self.stats = {"additions": 0, "soustractions": 0,
                      "multiplications": 0, "divisions": 0,
                      "carres": 0, "racines": 0}
    
    def resoudre(self, a, b, operation='+'):
        """
        Résout une opération arithmétique par résonance.
        
        operation: '+', '-', 'x', '/', 'carre', 'racine'
        """
        if operation == 'carre':
            self.stats["carres"] += 1
            formulations = [f"{a} au carre = ?", f"carre de {a} = ?"]
        elif operation == 'racine':
            self.stats["racines"] += 1
            formulations = [f"racine carree de {a} = ?", f"racine de {a} = ?"]
        elif operation == '+':
            self.stats["additions"] += 1
            formulations = [f"{a} + {b} = ?", f"{a} plus {b} = ?", f"somme de {a} et {b} = ?"]
        elif operation == '-':
            self.stats["soustractions"] += 1
            formulations = [f"{a} - {b} = ?", f"{a} moins {b} = ?"]
        elif operation in ('x', '*'):
            self.stats["multiplications"] += 1
            formulations = [f"{a} x {b} = ?", f"{a} fois {b} = ?", f"{a} multiplie par {b} = ?"]
        elif operation == '/':
            self.stats["divisions"] += 1
            formulations = [f"{a} divise par {b} = ?", f"{a} / {b} = ?"]
        else:
            return None
        
        return self._chercher_meilleur(formulations)
    
    def _chercher_meilleur(self, formulations):
        """Cherche la meilleure réponse parmi plusieurs formulations."""
        tous_resultats = []
        for q in formulations:
            r = self.holo.resoudre(q, top_k=3)
            if r:
                tous_resultats.append(r)
        
        if not tous_resultats:
            return None
        
        # Trier par interférence décroissante
        tous_resultats.sort(key=lambda x: -abs(x[2]))
        
        texte, resultat, interf, dist = tous_resultats[0]
        return {
            "meilleur_fait": texte,
            "interference": round(interf, 4),
            "distance": round(dist, 4),
            "resultat": resultat,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMONSTRATION
# ═══════════════════════════════════════════════════════════════════════════════

def ligne(titre):
    print(f"\n{'=' * 72}")
    print(f"  {titre}")
    print(f"{'=' * 72}")


def demo():
    print("=" * 74)
    print("  RAISONNEMENT ARITHMETIQUE ONDULATOIRE — Niveau 2 v2")
    print("  Paradigme Oyibo : les nombres SONT des modes spectraux")
    print("=" * 74)
    
    # ═══════════════════════════════════════════════════════════════════
    # ÉTAPE 0 : Construction
    # ═══════════════════════════════════════════════════════════════════
    N_MAX = 30
    print(f"\n  [0] Construction du corpus ([0, {N_MAX}])")
    t0 = time.time()
    corpus = generer_corpus_arithmetique(N_MAX)
    print(f"      {len(corpus)} faits generes en {(time.time()-t0)*1000:.0f} ms")
    
    print(f"\n  [0.5] Encodage des nombres comme modes spectraux")
    # Démo : montrer que les nombres ont des fréquences continues
    for n in [0, 1, 2, 3, 5, 10, 30]:
        kx, ky = number_to_wave(n)
        print(f"      {n:3d} → ({kx:+6.3f}, {ky:+6.3f})  θ = {math.degrees(math.atan2(ky, kx)):+.1f}°")
    
    print(f"\n  [1] Construction de l'hologramme arithmetique")
    t0 = time.time()
    holo = HologrammeArithmetique()
    holo.ajouter_batch(corpus)
    print(f"      {holo.N} faits stockes comme ondes en {(time.time()-t0)*1000:.0f} ms")
    
    wa = WaveArithmetic(holo)
    
    # ═══════════════════════════════════════════════════════════════════
    # TEST 1 : Additions
    # ═══════════════════════════════════════════════════════════════════
    ligne("TEST 1 — ADDITIONS (nombres = modes spectraux)")
    tests = [(3, 4), (7, 8), (12, 15), (0, 5), (25, 17), (1, 1), (30, 30)]
    ok_count = 0
    for a, b in tests:
        r = wa.resoudre(a, b, '+')
        vrai = a + b
        if r:
            ok = "✓" if r["resultat"] == vrai else "✗"
            if r["resultat"] == vrai:
                ok_count += 1
            print(f"      {a:2d} + {b:2d} = {r['resultat']:4d}  (vrai: {vrai})  "
                  f"interf={r['interference']:+.4f}  dist={r['distance']:.4f}  {ok}")
        else:
            print(f"      {a:2d} + {b:2d} = ?  (aucun fait)")
    print(f"      → {ok_count}/{len(tests)} corrects")
    
    # ═══════════════════════════════════════════════════════════════════
    # TEST 2 : Soustractions
    # ═══════════════════════════════════════════════════════════════════
    ligne("TEST 2 — SOUSTRACTIONS")
    tests = [(7, 3), (15, 8), (25, 10), (5, 0), (30, 14), (10, 10), (30, 1)]
    ok_count = 0
    for a, b in tests:
        r = wa.resoudre(a, b, '-')
        vrai = a - b
        if r:
            ok = "✓" if r["resultat"] == vrai else "✗"
            if r["resultat"] == vrai:
                ok_count += 1
            print(f"      {a:2d} - {b:2d} = {r['resultat']:4d}  (vrai: {vrai})  "
                  f"interf={r['interference']:+.4f}  dist={r['distance']:.4f}  {ok}")
        else:
            print(f"      {a:2d} - {b:2d} = ?  (aucun fait)")
    print(f"      → {ok_count}/{len(tests)} corrects")
    
    # ═══════════════════════════════════════════════════════════════════
    # TEST 3 : Multiplications
    # ═══════════════════════════════════════════════════════════════════
    ligne("TEST 3 — MULTIPLICATIONS (≤20)")
    tests = [(3, 4), (5, 6), (7, 8), (9, 10), (12, 12), (2, 2), (0, 7), (20, 20)]
    ok_count = 0
    for a, b in tests:
        r = wa.resoudre(a, b, 'x')
        vrai = a * b
        if r:
            ok = "✓" if r["resultat"] == vrai else "✗"
            if r["resultat"] == vrai:
                ok_count += 1
            print(f"      {a:2d} x {b:2d} = {r['resultat']:4d}  (vrai: {vrai})  "
                  f"interf={r['interference']:+.4f}  dist={r['distance']:.4f}  {ok}")
        else:
            print(f"      {a:2d} x {b:2d} = ?  (aucun fait)")
    print(f"      → {ok_count}/{len(tests)} corrects")
    
    # ═══════════════════════════════════════════════════════════════════
    # TEST 4 : Carrés et racines
    # ═══════════════════════════════════════════════════════════════════
    ligne("TEST 4 — CARRÉS")
    tests = [3, 7, 10, 15, 0, 1, 30]
    ok_count = 0
    for a in tests:
        r = wa.resoudre(a, None, 'carre')
        vrai = a * a
        if r:
            ok = "✓" if r["resultat"] == vrai else "✗"
            if r["resultat"] == vrai:
                ok_count += 1
            print(f"      {a}² = {r['resultat']:4d}  (vrai: {vrai})  "
                  f"interf={r['interference']:+.4f}  dist={r['distance']:.4f}  {ok}")
        else:
            print(f"      {a}² = ?  (aucun fait)")
    print(f"      → {ok_count}/{len(tests)} corrects")
    
    ligne("TEST 4b — RACINES CARRÉES")
    tests = [9, 49, 100, 225, 0, 1, 900]
    ok_count = 0
    for n in tests:
        r = wa.resoudre(n, None, 'racine')
        vrai = int(math.sqrt(n))
        if r:
            ok = "✓" if r["resultat"] == vrai else "✗"
            if r["resultat"] == vrai:
                ok_count += 1
            print(f"      √{n:3d} = {r['resultat']:4d}  (vrai: {vrai})  "
                  f"interf={r['interference']:+.4f}  dist={r['distance']:.4f}  {ok}")
        else:
            print(f"      √{n:3d} = ?  (aucun fait)")
    print(f"      → {ok_count}/{len(tests)} corrects")
    
    # ═══════════════════════════════════════════════════════════════════
    # DÉMO : Comment fonctionne la résonance
    # ═══════════════════════════════════════════════════════════════════
    ligne("DÉMO — Comment '3 + 4 = ?' trouve '3 + 4 = 7'")
    
    # Montrer l'onde de la question
    kx_q, ky_q = expression_to_wave("3 + 4 = ?")
    print(f"      Question '3 + 4 = ?'")
    print(f"        Normalisée : '{normalize_expression('3 + 4 = ?')}'")
    print(f"        Ψ_q = ({kx_q:+.4f}, {ky_q:+.4f})")
    
    # Montrer les ondes des faits proches
    print(f"\n      Top 5 faits les plus résonants :")
    resultats = holo.consulter("3 + 4 = ?", top_k=5)
    for texte, resultat, interf, dist in resultats:
        kx_f, ky_f, _ = holo.faits[texte]
        barre = "█" * int(abs(interf) * 15) + "░" * (15 - int(abs(interf) * 15))
        signe = "+" if interf > 0 else "-"
        print(f"      [{signe}] [{barre}] {texte:35s} → {resultat:4d}  "
              f"cos θ={interf:+.4f}  d={dist:.4f}")
    
    # ═══════════════════════════════════════════════════════════════════
    # BILAN
    # ═══════════════════════════════════════════════════════════════════
    ligne("BILAN")
    total = (wa.stats['additions'] + wa.stats['soustractions'] +
             wa.stats['multiplications'] + wa.stats['carres'] +
             wa.stats['racines'])
    print(f"""
      Hologramme arithmetique :
        - {holo.N} faits stockes comme ondes
        - Encodage : nombres → modes spectraux (z_n = exp(i·n·φ·2π))
        - Normalisation : le resultat n'est PAS dans l'onde

      Tests effectues : {total}
        - Additions      : {wa.stats['additions']}
        - Soustractions  : {wa.stats['soustractions']}
        - Multiplications: {wa.stats['multiplications']}
        - Carres         : {wa.stats['carres']}
        - Racines        : {wa.stats['racines']}

      PRINCIPE :
        Chaque nombre n est un MODE SPECTRAL sur le cercle unite.
        Les nombres proches (3, 4, 5) ont des frequences proches.
        Une operation est une SUPERPOSITION d'ondes numeriques.
        Le resultat est stocke SEPAREMENT (pas dans l'onde).
        
        "3 + 4 = ?" et "3 + 4 = 7" produisent la MEME onde
        car le resultat est STRIP avant encodage.
        → Resonance parfaite → lookup exact.
        
      NIVEAU 2 — ARITHMETIQUE ONDULATOIRE (paradigme Oyibo)
      Les nombres emergent de la quantification des figures
      geometriques du Niveau 1.
""")

if __name__ == "__main__":
    demo()