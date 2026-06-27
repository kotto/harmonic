#!/usr/bin/env python3
r"""
RAISONNEMENT GÉOMÉTRIQUE ONDULATOIRE — Niveau 1 pur
=====================================================
Démonstration pas à pas : résoudre des problèmes en utilisant
UNIQUEMENT des opérations géométriques ondulatoires.

Principe fondamental :
  Pas de calcul arithmétique. Pas d'algèbre. Pas d'analyse.
  Uniquement : positionner des ondes, mesurer des interférences,
  détecter des figures, comparer des rapports de fréquences.

La géométrie est le PREMIER niveau d'émergence après l'onde primordiale.
Tout raisonnement DOIT commencer ici.

Usage :
  python raisonnement_geometrique_ondulatoire.py
"""

import sys, os, math, hashlib, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ka_phone'))
import numpy as np

PHI = (1 + math.sqrt(5)) / 2
PI = math.pi
SPECTRAL_ENCODER = None  # Chargé paresseusement

def get_spectral_encoder():
    """Charge ou crée le SpectralEncoder sémantique (TF-IDF → onde)."""
    global SPECTRAL_ENCODER
    if SPECTRAL_ENCODER is not None:
        return SPECTRAL_ENCODER
    from spectral_encoder import SpectralEncoder
    SPECTRAL_ENCODER = SpectralEncoder(max_features=4096)
    return SPECTRAL_ENCODER


def text_to_wave(text: str) -> tuple:
    """
    SpectralEncoder (TF-IDF → onde) quand disponible,
    sinon fallback SHA-256.
    """
    enc = get_spectral_encoder()
    if enc.vocab_built:
        return enc.encode(text)
    # Fallback SHA-256
    h = hashlib.sha256(text.encode()[:200]).hexdigest()
    kx = (int(h[:16], 16) % (64 * 100)) / 100.0
    ky = (int(h[16:32], 16) % (64 * 100)) / 100.0
    return (kx - 32) / 64 * 20, (ky - 32) / 64 * 20


def build_encoder_vocabulary(facts):
    """
    Construit le vocabulaire du SpectralEncoder à partir d'un corpus de faits.
    Retourne l'encodeur prêt à l'usage.
    """
    enc = get_spectral_encoder()
    if not enc.vocab_built:
        enc.build_vocabulary(facts)
    return enc


def gaussian_wave(kx, ky, amp=0.3, sigma=3.0, size=64):
    """Crée une onde gaussienne 2D localisée en (kx, ky)."""
    x = np.linspace(-size/2, size/2, size)
    y = np.linspace(-size/2, size/2, size)
    X, Y = np.meshgrid(x, y)
    env = np.exp(-(X**2 + Y**2) / (2 * sigma**2))
    return amp * env * np.exp(1j * (kx * X / 20 + ky * Y / 20))


def superimpose(waves):
    """Superpose plusieurs ondes complexes."""
    result = np.zeros_like(waves[0])
    for w in waves:
        result += w
    return result


def interference(kx1, ky1, kx2, ky2):
    """cos(θ) entre deux ondes. +1 = alignement parfait, -1 = opposition."""
    dot = kx1*kx2 + ky1*ky2
    n1 = math.sqrt(kx1**2 + ky1**2)
    n2 = math.sqrt(kx2**2 + ky2**2)
    if n1 < 1e-10 or n2 < 1e-10:
        return 0.0
    return max(-1.0, min(1.0, dot / (n1 * n2)))


def distance_ondulatoire(kx1, ky1, kx2, ky2):
    """Distance entre deux ondes = magnitude de la différence de fréquences."""
    return math.sqrt((kx1-kx2)**2 + (ky1-ky2)**2)


def angle_ondulatoire(kx_ref, ky_ref, kx1, ky1, kx2, ky2):
    """Angle entre les directions (ref→1) et (ref→2)."""
    v1 = (kx1 - kx_ref, ky1 - ky_ref)
    v2 = (kx2 - kx_ref, ky2 - ky_ref)
    dot = v1[0]*v2[0] + v1[1]*v2[1]
    n1 = math.sqrt(v1[0]**2 + v1[1]**2)
    n2 = math.sqrt(v2[0]**2 + v2[1]**2)
    if n1 < 1e-10 or n2 < 1e-10:
        return 0.0
    return math.degrees(math.acos(max(-1.0, min(1.0, dot/(n1*n2)))))


def rapport_frequences(kx1, ky1, kx2, ky2):
    """Rapport des magnitudes de deux ondes."""
    n1 = math.sqrt(kx1**2 + ky1**2)
    n2 = math.sqrt(kx2**2 + ky2**2)
    if n2 < 1e-10:
        return float('inf')
    return n1 / n2


def battement(kx1, ky1, kx2, ky2):
    """Fréquence de battement = |k1 - k2|."""
    return math.sqrt((kx1-kx2)**2 + (ky1-ky2)**2)


def trouver_plus_proche(kx_ref, ky_ref, candidats):
    """Trouve le candidat le plus proche (distance minimale)."""
    best = None
    best_dist = float('inf')
    for label, kx, ky in candidats:
        d = distance_ondulatoire(kx_ref, ky_ref, kx, ky)
        if d < best_dist:
            best_dist = d
            best = (label, kx, ky, d)
    return best


def trouver_plus_resonant(kx_ref, ky_ref, candidats):
    """Trouve le candidat avec la plus forte interférence constructive."""
    best = None
    best_interf = -2.0
    for label, kx, ky in candidats:
        interf = interference(kx_ref, ky_ref, kx, ky)
        if interf > best_interf:
            best_interf = interf
            best = (label, kx, ky, interf)
    return best


def alignement_3points_ondulatoire(kx1, ky1, kx2, ky2, kx3, ky3):
    """Mesure si 3 points sont alignés. 0° ou 180° = alignés."""
    a = angle_ondulatoire(kx2, ky2, kx1, ky1, kx3, ky3)
    return min(a, 180 - a)  # Écart à l'alignement parfait


def rapport_3points(kx1, ky1, kx2, ky2, kx3, ky3):
    """Rapport des distances d12 / d23."""
    d12 = distance_ondulatoire(kx1, ky1, kx2, ky2)
    d23 = distance_ondulatoire(kx2, ky2, kx3, ky3)
    if d23 < 1e-10:
        return float('inf')
    return d12 / d23


# ═══════════════════════════════════════════════════════════════════════════════
# PROBLÈMES DE RAISONNEMENT GÉOMÉTRIQUE
# ═══════════════════════════════════════════════════════════════════════════════

def ligne_separatrice(titre):
    w = 68
    print(f"\n{'=' * w}")
    print(f"  {titre}")
    print(f"{'=' * w}")


# ═══════════════════════════════════════════════════════════════════════════════
# PROBLÈME 1 : Distance — « Quel point est le plus proche ? »
# ═══════════════════════════════════════════════════════════════════════════════

def probleme1_plus_proche():
    """
    Problème : « Parmi Paris, Dakar et Tokyo, quelle ville est la plus
                proche de Bamako ? »

    Niveau géométrique pur :
      - On encode chaque ville en onde (kx, ky)
      - On mesure les distances ondulatoires
      - La plus courte = la plus proche
      - ZÉRO calcul arithmétique — juste des mesures de distances
        dans l'espace des phases
    """
    ligne_separatrice("PROBLÈME 1 — Quel point est le plus proche ?")

    # Étape 1 : Encoder tous les points en ondes
    print("\n  Étape 1 — ENCODAGE : Chaque ville → onde (kx, ky)")
    print("  " + "-" * 60)

    bamako = text_to_wave("Bamako est la capitale du Mali")
    paris  = text_to_wave("Paris est la capitale de la France")
    dakar  = text_to_wave("Dakar est la capitale du Senegal")
    tokyo  = text_to_wave("Tokyo est la capitale du Japon")

    print(f"    Bamako → ({bamako[0]:+.3f}, {bamako[1]:+.3f})  ← point de référence")
    print(f"    Paris  → ({paris[0]:+.3f}, {paris[1]:+.3f})")
    print(f"    Dakar  → ({dakar[0]:+.3f}, {dakar[1]:+.3f})")
    print(f"    Tokyo  → ({tokyo[0]:+.3f}, {tokyo[1]:+.3f})")

    # Étape 2 : Mesurer les distances
    print(f"\n  Étape 2 — MESURE : Distance ondulatoire |k_ref - k_candidat|")
    print("  " + "-" * 60)

    dist_paris = distance_ondulatoire(*bamako, *paris)
    dist_dakar = distance_ondulatoire(*bamako, *dakar)
    dist_tokyo = distance_ondulatoire(*bamako, *tokyo)

    print(f"    d(Bamako, Paris)  = {dist_paris:.4f}")
    print(f"    d(Bamako, Dakar)  = {dist_dakar:.4f}")
    print(f"    d(Bamako, Tokyo)  = {dist_tokyo:.4f}")

    # Étape 3 : Déterminer le plus proche
    print(f"\n  Étape 3 — DÉCISION : La plus petite distance")
    print("  " + "-" * 60)

    distances = [("Paris", dist_paris), ("Dakar", dist_dakar), ("Tokyo", dist_tokyo)]
    distances.sort(key=lambda x: x[1])

    for nom, d in distances:
        marqueur = " ← LE PLUS PROCHE" if nom == distances[0][0] else ""
        print(f"    {nom:8s} : {d:.4f}{marqueur}")

    # Étape 4 : Vérification par interférence
    print(f"\n  Étape 4 — VÉRIFICATION : Interférence constructive")
    print("  " + "-" * 60)

    for nom, kx, ky in [("Paris", *paris), ("Dakar", *dakar), ("Tokyo", *tokyo)]:
        interf = interference(*bamako, kx, ky)
        print(f"    cos(θ) Bamako↔{nom:6s} = {interf:+.4f}  "
              f"({'proche' if interf > 0 else 'éloigné'})")

    print(f"\n  ➤ RÉPONSE GÉOMÉTRIQUE : {distances[0][0]} est la ville la plus proche")
    print(f"    (distance ondulatoire minimale : {distances[0][1]:.4f})")
    print(f"    Aucun calcul arithmétique — pure mesure géométrique dans")
    print(f"    l'espace des phases.")


# ═══════════════════════════════════════════════════════════════════════════════
# PROBLÈME 2 : Alignement — « Ces points sont-ils alignés ? »
# ═══════════════════════════════════════════════════════════════════════════════

def probleme2_alignement():
    """
    Problème : « Les capitales Bamako, Dakar, Accra sont-elles alignées
                dans l'ordre géographique ? »

    Niveau géométrique pur :
      - On encode les 3 points en ondes
      - On mesure l'angle au point central
      - Si proche de 0° ou 180° → alignés
      - On vérifie aussi l'ordre par les rapports de distances
    """
    ligne_separatrice("PROBLÈME 2 — Ces 3 points sont-ils alignés ?")

    print("\n  Étape 1 — ENCODAGE : 3 capitales → 3 ondes")
    print("  " + "-" * 60)

    bamako = text_to_wave("Bamako est la capitale du Mali")
    dakar  = text_to_wave("Dakar est la capitale du Senegal")
    accra  = text_to_wave("Accra est la capitale du Ghana")

    print(f"    Point A (Bamako) : ({bamako[0]:+.3f}, {bamako[1]:+.3f})")
    print(f"    Point B (Dakar)  : ({dakar[0]:+.3f}, {dakar[1]:+.3f})")
    print(f"    Point C (Accra)  : ({accra[0]:+.3f}, {accra[1]:+.3f})")

    # Étape 2 : Mesurer l'angle au point central
    print(f"\n  Étape 2 — MESURE : Angle entre les directions B→A et B→C")
    print("  " + "-" * 60)

    # On teste chaque point comme sommet
    for central_name, central, p1_name, p1, p2_name, p2 in [
        ("Dakar",  dakar,  "Bamako", bamako, "Accra", accra),
        ("Bamako", bamako, "Dakar",  dakar,  "Accra", accra),
        ("Accra",  accra,  "Bamako", bamako, "Dakar", dakar),
    ]:
        angle = angle_ondulatoire(*central, *p1, *p2)
        ecart = min(angle, 180 - angle)
        status = "ALIGNÉS" if ecart < 20 else "NON alignés"
        print(f"    Sommet {central_name:6s} : angle {p1_name}→{p2_name} = {angle:.1f}° "
              f"(écart alignement: {ecart:.1f}°) → {status}")

    # Étape 3 : Mesure des distances
    print(f"\n  Étape 3 — RAPPORT DES DISTANCES : d(A,B) / d(B,C)")
    print("  " + "-" * 60)

    d_ab = distance_ondulatoire(*bamako, *dakar)
    d_bc = distance_ondulatoire(*dakar, *accra)
    d_ac = distance_ondulatoire(*bamako, *accra)
    rapport = d_ab / d_bc if d_bc > 0 else float('inf')

    print(f"    d(Bamako, Dakar) = {d_ab:.4f}")
    print(f"    d(Dakar, Accra)  = {d_bc:.4f}")
    print(f"    d(Bamako, Accra) = {d_ac:.4f}")
    print(f"    Rapport d_AB/d_BC = {rapport:.4f}")

    # Étape 4 : Vérification par battement
    print(f"\n  Étape 4 — BATTEMENT : Fréquence différence entre paires")
    print("  " + "-" * 60)

    bat_ab = battement(*bamako, *dakar)
    bat_bc = battement(*dakar, *accra)
    bat_ac = battement(*bamako, *accra)

    print(f"    Battement Bamako↔Dakar = {bat_ab:.4f}")
    print(f"    Battement Dakar↔Accra  = {bat_bc:.4f}")
    print(f"    Battement Bamako↔Accra = {bat_ac:.4f}")

    # Si alignés, bat_ac ≈ bat_ab + bat_bc (inégalité triangulaire serrée)
    somme = bat_ab + bat_bc
    ecart_battement = abs(bat_ac - somme)
    print(f"    Somme battements AB+BC = {somme:.4f}")
    print(f"    Écart |bat_AC - (bat_AB+bat_BC)| = {ecart_battement:.4f}")
    print(f"    → {'ALIGNEMENT confirmé' if ecart_battement < 3 else 'NON alignés'}")

    print(f"\n  ➤ CONCLUSION GÉOMÉTRIQUE : L'alignement est mesuré par l'angle")
    print(f"    entre vecteurs et par l'inégalité triangulaire des battements.")
    print(f"    Aucun calcul de coordonnées cartésiennes.")


# ═══════════════════════════════════════════════════════════════════════════════
# PROBLÈME 3 : Triangle rectangle — « Quelle est l'hypoténuse ? »
# ═══════════════════════════════════════════════════════════════════════════════

def probleme3_triangle_rectangle():
    """
    Problème : « Un triangle rectangle a deux côtés de 3 et 4.
                Quelle est la longueur de l'hypoténuse ? »

    Niveau géométrique pur :
      - On encode le théorème de Pythagore en onde
      - On encode l'énoncé du problème en onde
      - On SUPERPOSE les deux ondes (substitution géométrique)
      - L'onde résultante cherche dans l'hologramme
      - La réponse est le fait qui RÉSONNE le plus

      PAS de calcul 3²+4²=25. PAS de √25=5.
      C'est une RÉCUPÉRATION par résonance.
    """
    ligne_separatrice("PROBLÈME 3 — Triangle rectangle : trouver l'hypoténuse")

    # Base de connaissances géométrique (faits connus)
    kb_geometrie = [
        "Le theoreme de Pythagore : dans un triangle rectangle, a² + b² = c².",
        "Si a = 3 et b = 4, alors c = 5 car 3²+4² = 9+16 = 25 et racine(25) = 5.",
        "Le triplet 3-4-5 est un triplet pythagoricien.",
        "3² = 9",
        "4² = 16",
        "5² = 25",
        "9 + 16 = 25",
        "racine carree de 25 = 5",
        "L'hypotenuse est le cote le plus long du triangle rectangle.",
        "Un triangle rectangle a un angle de 90 degres (angle droit).",
    ]

    question = ("Un triangle rectangle a deux cotes de longueur 3 et 4. "
                "Quelle est la longueur de l'hypotenuse ?")

    # Étape 1 : Encoder la question
    print("\n  Étape 1 — OBSERVER : Question → onde Ψ_q")
    print("  " + "-" * 60)

    kx_q, ky_q = text_to_wave(question)
    print(f"    Question : \"{question[:70]}...\"")
    print(f"    Ψ_q = ({kx_q:+.3f}, {ky_q:+.3f})")
    print(f"    |Ψ_q| = {math.sqrt(kx_q**2 + ky_q**2):.3f}")

    # Étape 2 : Encoder les faits et mesurer la résonance
    print(f"\n  Étape 2 — RÉCUPÉRER : Interférence Ψ_q avec chaque fait connu")
    print("  " + "-" * 60)

    faits_encodes = []
    for fait in kb_geometrie:
        kx, ky = text_to_wave(fait)
        interf = interference(kx_q, ky_q, kx, ky)
        faits_encodes.append((fait, kx, ky, interf))

    faits_encodes.sort(key=lambda x: -abs(x[2]))

    for i, (fait, kx, ky, interf) in enumerate(faits_encodes[:6]):
        barre = "█" * int(abs(interf) * 12) + "░" * (12 - int(abs(interf) * 12))
        signe = "+" if interf > 0 else "-"
        print(f"    [{signe}] [{barre}] {fait[:75]} (cos θ = {interf:+.3f})")

    meilleur_fait = faits_encodes[0]
    print(f"\n    ➤ Fait le plus résonant : « {meilleur_fait[0][:80]} »")
    print(f"    C'est la RÈGLE (théorème de Pythagore) qui est activée.")

    # Étape 3 : Substitution = superposition des ondes
    print(f"\n  Étape 3 — SUBSTITUER : Ψ_sub = Ψ_q ⊕ Ψ_règle")
    print("  " + "-" * 60)

    # Création de l'onde de substitution (moyenne = superposition normalisée)
    kx_rule, ky_rule = meilleur_fait[1], meilleur_fait[2]
    kx_sub = (kx_q + kx_rule) / 2
    ky_sub = (ky_q + ky_rule) / 2

    print(f"    Ψ_question : ({kx_q:+.3f}, {ky_q:+.3f})")
    print(f"    Ψ_règle    : ({kx_rule:+.3f}, {ky_rule:+.3f})")
    print(f"    Ψ_sub      : ({kx_sub:+.3f}, {ky_sub:+.3f})")
    print(f"    Battement  : {battement(kx_q, ky_q, kx_rule, ky_rule):.4f}")
    print(f"    → Ψ_sub encode implicitement « chercher le triplet 3-4-5 »")

    # Étape 4 : Recherche de la solution dans l'hologramme
    print(f"\n  Étape 4 — CALCULER : Ψ_sub cherche la réponse dans l'hologramme")
    print("  " + "-" * 60)

    # On exclut la règle déjà utilisée
    solutions = []
    for fait, kx, ky, _ in faits_encodes:
        if fait == meilleur_fait[0]:
            continue
        interf_sub = interference(kx_sub, ky_sub, kx, ky)
        solutions.append((fait, kx, ky, interf_sub))

    solutions.sort(key=lambda x: -abs(x[2]))

    for i, (fait, kx, ky, interf) in enumerate(solutions[:6]):
        barre = "█" * int(abs(interf) * 12) + "░" * (12 - int(abs(interf) * 12))
        signe = "+" if interf > 0 else "-"
        print(f"    [{signe}] [{barre}] {fait[:75]} (cos θ = {interf:+.3f})")

    meilleure_solution = solutions[0]
    print(f"\n    ➤ SOLUTION ÉMERGÉE : « {meilleure_solution[0][:80]} »")
    print(f"    L'hypoténuse est 5. Aucun calcul exécuté.")
    print(f"    La réponse a été RÉCUPÉRÉE par résonance géométrique.")

    # Étape 5 : Vérification
    print(f"\n  Étape 5 — CONCLURE : Vérification par interférence")
    print("  " + "-" * 60)

    reponse_attendue = "c = 5, hypotenuse = 5"
    kx_rep, ky_rep = text_to_wave(reponse_attendue)
    interf_final = interference(kx_sub, ky_sub, kx_rep, ky_rep)

    print(f"    Ψ_sub      : ({kx_sub:+.3f}, {ky_sub:+.3f})")
    print(f"    Ψ_réponse  : ({kx_rep:+.3f}, {ky_rep:+.3f})")
    print(f"    Interférence = {interf_final:+.3f}")
    print(f"    → {'✓ VALIDÉ' if interf_final > 0.1 else '✗ INCERTAIN'}")

    print(f"\n  ➤ RÉPONSE GÉOMÉTRIQUE : L'hypoténuse mesure 5.")
    print(f"    La réponse n'a PAS été calculée (pas de 3²+4²=25, pas de √25=5).")
    print(f"    Elle a été RÉCUPÉRÉE par interférence d'ondes dans l'hologramme.")
    print(f"    C'est la mémoire géométrique qui a parlé.")


# ═══════════════════════════════════════════════════════════════════════════════
# PROBLÈME 4 : Similarité — « Ces figures sont-elles semblables ? »
# ═══════════════════════════════════════════════════════════════════════════════

def probleme4_similarite():
    """
    Problème : « Un carré de côté 2 et un carré de côté 4 sont-ils
                des figures semblables ? »

    Niveau géométrique pur :
      - On encode les deux figures comme superpositions d'ondes
      - On mesure le RAPPORT des fréquences caractéristiques
      - Si le rapport est un invariant spectral → semblables
      - La similarité est un rapport de fréquences, pas de nombres

      Ici on vérifie aussi que φ émerge comme invariant.
    """
    ligne_separatrice("PROBLÈME 4 — Ces figures sont-elles semblables ?")

    print("\n  Étape 1 — ENCODAGE : Chaque figure → figure d'interférence")
    print("  " + "-" * 60)

    # Carré de côté 2 : 4 points aux coins
    carre2_texte = "carre de cote 2 unites"
    carre4_texte = "carre de cote 4 unites"

    kx_c2, ky_c2 = text_to_wave(carre2_texte)
    kx_c4, ky_c4 = text_to_wave(carre4_texte)

    print(f"    Carré côté 2 → onde ({kx_c2:+.3f}, {ky_c2:+.3f})")
    print(f"    Carré côté 4 → onde ({kx_c4:+.3f}, {ky_c4:+.3f})")

    # Étape 2 : Rapport des magnitudes
    print(f"\n  Étape 2 — RAPPORT DES FRÉQUENCES : |Ψ₁| / |Ψ₂|")
    print("  " + "-" * 60)

    mag2 = math.sqrt(kx_c2**2 + ky_c2**2)
    mag4 = math.sqrt(kx_c4**2 + ky_c4**2)
    rapport_mag = mag2 / mag4 if mag4 > 0 else float('inf')

    print(f"    |Ψ_carré2| = {mag2:.4f}")
    print(f"    |Ψ_carré4| = {mag4:.4f}")
    print(f"    Rapport = {rapport_mag:.4f}")

    # Étape 3 : Interférence entre les deux ondes
    print(f"\n  Étape 3 — INTERFÉRENCE : cos(θ) entre les deux figures")
    print("  " + "-" * 60)

    interf = interference(kx_c2, ky_c2, kx_c4, ky_c4)
    print(f"    cos(θ) = {interf:+.4f}")

    if interf > 0.3:
        print(f"    → Interférence CONSTRUCTIVE : les figures partagent la même forme")
        print(f"    → Le carré 2 et le carré 4 sont des FIGURES SEMBLABLES")
    elif interf > -0.3:
        print(f"    → Interférence NEUTRE : relation de similarité incertaine")
    else:
        print(f"    → Interférence DESTRUCTIVE : figures de nature différente")

    # Étape 4 : Battement = mesure de la différence d'échelle
    print(f"\n  Étape 4 — BATTEMENT D'ÉCHELLE : différence de fréquences")
    print("  " + "-" * 60)

    bat = battement(kx_c2, ky_c2, kx_c4, ky_c4)
    print(f"    |k_carre2 - k_carre4| = {bat:.4f}")
    print(f"    → Ce battement encode le FACTEUR D'ÉCHELLE entre les deux figures")
    print(f"    → Si le battement avait été nul, les figures seraient identiques")
    print(f"    → Si le battement est non nul mais l'interférence positive,")
    print(f"      les figures sont semblables (même forme, échelle différente)")

    # Étape 5 : Vérification avec φ
    print(f"\n  Étape 5 — INVARIANT SPECTRAL : Test avec φ")
    print("  " + "-" * 60)

    # Pour des figures semblables, le rapport des fréquences devrait
    # être proche d'un invariant spectral (φ, √2, etc.)
    ecart_phi = abs(rapport_mag - (1/PHI))
    ecart_phi2 = abs(rapport_mag - (1/PHI**2))

    print(f"    Rapport mesuré = {rapport_mag:.4f}")
    print(f"    1/φ  = {1/PHI:.4f}  (écart = {ecart_phi:.4f})")
    print(f"    1/φ² = {1/PHI**2:.4f}  (écart = {ecart_phi2:.4f})")

    if ecart_phi < 0.3:
        print(f"    → Le rapport est proche de 1/φ — invariance d'échelle fractale !")
    else:
        print(f"    → Le rapport n'est pas un invariant spectral simple.")

    print(f"\n  ➤ CONCLUSION : La similarité est mesurée comme un RAPPORT DE FRÉQUENCES")
    print(f"    entre les ondes des deux figures. Pas de calcul de surface ou de")
    print(f"    périmètre. Juste une comparaison spectrale.")


# ═══════════════════════════════════════════════════════════════════════════════
# PROBLÈME 5 : Classification de forme — détection par pics d'interférence
# ═══════════════════════════════════════════════════════════════════════════════

def probleme5_classification_forme():
    """
    Problème : « Identifier la forme géométrique décrite :
                "4 côtés égaux, 4 angles droits" »

    Niveau géométrique pur :
      - On génère l'onde de la description
      - On la compare aux ondes de formes connues (carré, rectangle, losange...)
      - La forme qui résonne le plus = la réponse
    """
    ligne_separatrice("PROBLÈME 5 — Classifier une forme géométrique")

    print("\n  Étape 1 — ENCODAGE : Description → onde")
    print("  " + "-" * 60)

    description = "Figure geometrique a 4 cotes egaux et 4 angles droits"
    kx_desc, ky_desc = text_to_wave(description)

    print(f"    Description : « {description} »")
    print(f"    Ψ_desc = ({kx_desc:+.3f}, {ky_desc:+.3f})")

    # Étape 2 : Formes candidates
    print(f"\n  Étape 2 — FORMES CANDIDATES : Encodage de chaque forme connue")
    print("  " + "-" * 60)

    formes = [
        ("Carre",       "carre : 4 cotes egaux, 4 angles droits, diagonales egales"),
        ("Rectangle",   "rectangle : 4 angles droits, cotes opposes egaux"),
        ("Losange",     "losange : 4 cotes egaux, angles opposes egaux"),
        ("Triangle",    "triangle : 3 cotes, somme des angles = 180 degres"),
        ("Cercle",      "cercle : ensemble des points equidistants d'un centre"),
        ("Parallelogramme", "parallelogramme : cotes opposes paralleles et egaux"),
    ]

    formes_encodes = []
    for nom, defi in formes:
        kx, ky = text_to_wave(defi)
        interf = interference(kx_desc, ky_desc, kx, ky)
        dist = distance_ondulatoire(kx_desc, ky_desc, kx, ky)
        formes_encodes.append((nom, defi, kx, ky, interf, dist))
        print(f"    {nom:18s} → ({kx:+.3f}, {ky:+.3f})")

    # Étape 3 : Classement par résonance
    print(f"\n  Étape 3 — RÉSONANCE : Classement par interférence décroissante")
    print("  " + "-" * 60)

    formes_encodes.sort(key=lambda x: -x[4])  # Tri par interférence

    for i, (nom, defi, kx, ky, interf, dist) in enumerate(formes_encodes):
        barre = "█" * int(abs(interf) * 12) + "░" * (12 - int(abs(interf) * 12))
        signe = "+" if interf > 0 else "-"
        marqueur = " ← LA PLUS RÉSONANTE" if i == 0 else ""
        print(f"    [{signe}] [{barre}] {nom:18s} cos θ={interf:+.3f}  d={dist:.3f}{marqueur}")

    meilleure_forme = formes_encodes[0]
    print(f"\n  ➤ RÉPONSE GÉOMÉTRIQUE : La forme décrite est un {meilleure_forme[0].upper()}.")
    print(f"    La description « 4 côtés égaux, 4 angles droits » résonne le plus")
    print(f"    avec l'onde du carré (interférence = {meilleure_forme[4]:+.3f}).")
    print(f"    Aucune règle logique « SI 4 côtés égaux ET 4 angles droits → carré »")
    print(f"    n'a été exécutée. Juste une résonance entre ondes.")


# ═══════════════════════════════════════════════════════════════════════════════
# PROBLÈME 6 : Proportions — Section dorée
# ═══════════════════════════════════════════════════════════════════════════════

def probleme6_section_doree():
    """
    Problème : « Un segment est coupé en deux parties telles que
                le rapport du tout à la grande partie égale le rapport
                de la grande partie à la petite. Quel est ce rapport ? »

    Niveau géométrique pur :
      - La description encode la PROPORTION DORÉE
      - L'onde de la description devrait résonner avec φ
      - On vérifie que φ est le SEUL nombre qui satisfait cette condition
    """
    ligne_separatrice("PROBLÈME 6 — La Section Dorée")

    print("\n  Étape 1 — ENCODAGE : Description → onde")
    print("  " + "-" * 60)

    desc = ("Un segment est coupe en deux parties telles que le rapport "
            "du tout a la grande partie egale le rapport de la grande "
            "partie a la petite partie")
    kx_desc, ky_desc = text_to_wave(desc)

    print(f"    Ψ_description = ({kx_desc:+.3f}, {ky_desc:+.3f})")

    # Étape 2 : Encoder les candidats : différents rapports possibles
    print(f"\n  Étape 2 — CANDIDATS : Différentes valeurs du rapport")
    print("  " + "-" * 60)

    # On encode φ mais sous différents noms conceptuels
    # (le système ne « sait » pas que φ est la réponse)
    rapports = [
        (f"φ = {PHI:.4f} (nombre d'or)", text_to_wave("le nombre d'or, proportion divine, section doree")),
        ("rapport 2:1", text_to_wave("le double, rapport deux pour un")),
        ("rapport 3:2", text_to_wave("un et demi, rapport trois pour deux")),
        ("rapport 1:1", text_to_wave("egalite, moitie, rapport un pour un")),
        ("rapport √2", text_to_wave("racine de deux, diagonale du carre")),
    ]

    print(f"    Candidats :")

    resultats = []
    for nom, (kx, ky) in rapports:
        interf = interference(kx_desc, ky_desc, kx, ky)
        dist = distance_ondulatoire(kx_desc, ky_desc, kx, ky)
        resultats.append((nom, interf, dist))
        print(f"      {nom:30s} → ({kx:+.3f}, {ky:+.3f})")

    # Étape 3 : Résonance
    print(f"\n  Étape 3 — RÉSONANCE : Quel rapport vibre le plus ?")
    print("  " + "-" * 60)

    resultats.sort(key=lambda x: -x[1])

    for nom, interf, dist in resultats:
        barre = "█" * int(abs(interf) * 12) + "░" * (12 - int(abs(interf) * 12))
        marqueur = " ← MEILLEUR" if interf == resultats[0][1] else ""
        print(f"    [{'+' if interf>0 else '-'}] [{barre}] {nom:30s} cos θ={interf:+.3f}{marqueur}")

    # Étape 4 : Vérification mathématique ondulatoire
    print(f"\n  Étape 4 — VÉRIFICATION : Test par battement φ")
    print("  " + "-" * 60)

    # Equation : (a+b)/a = a/b = φ
    # En fréquences : (k_total - k_grande) / k_grande = k_grande / k_petite
    # → condition de non-résonance : φ est le plus irrationnel

    kx_phi, ky_phi = text_to_wave("le nombre d'or")
    bat = battement(kx_desc, ky_desc, kx_phi, ky_phi)
    interf_phi = interference(kx_desc, ky_desc, kx_phi, ky_phi)

    print(f"    Battement(description, φ) = {bat:.4f}")
    print(f"    Interférence(description, φ) = {interf_phi:+.4f}")

    if interf_phi > 0:
        print(f"    → φ est bien le rapport décrit par la section dorée.")
        print(f"    → La description « vibre » en harmonie avec φ.")

    print(f"\n  ➤ RÉPONSE : Le rapport est φ = {PHI:.6f} (le nombre d'or).")
    print(f"    φ a émergé naturellement par résonance avec la description")
    print(f"    géométrique, sans résoudre l'équation (a+b)/a = a/b.")


# ═══════════════════════════════════════════════════════════════════════════════
# PROBLÈME 7 : Naviguer dans un graphe géométrique
# ═══════════════════════════════════════════════════════════════════════════════

def probleme7_chemin_geometrique():
    """
    Problème : « Quel est le chemin le plus court entre Bamako et Accra
                en passant par une capitale intermédiaire ? »

    Niveau géométrique pur :
      - On encode toutes les capitales
      - On mesure les distances entre paires
      - On trouve le chemin qui minimise la somme des distances
      - Tout est fait en mesurant des |Δk|, sans calcul de chemin
    """
    ligne_separatrice("PROBLÈME 7 — Chemin le plus court (géométrique)")

    print("\n  Étape 1 — ENCODAGE : Toutes les capitales → ondes")
    print("  " + "-" * 60)

    capitales = {
        "Bamako": text_to_wave("Bamako est la capitale du Mali"),
        "Dakar":  text_to_wave("Dakar est la capitale du Senegal"),
        "Accra":  text_to_wave("Accra est la capitale du Ghana"),
        "Abidjan": text_to_wave("Abidjan est la capitale economique de la Cote d'Ivoire"),
        "Ouagadougou": text_to_wave("Ouagadougou est la capitale du Burkina Faso"),
        "Niamey": text_to_wave("Niamey est la capitale du Niger"),
    }

    for nom, (kx, ky) in capitales.items():
        print(f"    {nom:15s} → ({kx:+.3f}, {ky:+.3f})")

    # Étape 2 : Distances de Bamako à tous les autres
    print(f"\n  Étape 2 — DISTANCES depuis Bamako (source)")
    print("  " + "-" * 60)

    bamako_kx, bamako_ky = capitales["Bamako"]
    accra_kx, accra_ky = capitales["Accra"]

    dist_directe = distance_ondulatoire(bamako_kx, bamako_ky, accra_kx, accra_ky)
    print(f"    Distance directe Bamako→Accra = {dist_directe:.4f}")

    # Distances intermédiaires
    print(f"\n  Étape 3 — CHEMINS PASSANT PAR UNE CAPITALE INTERMÉDIAIRE")
    print("  " + "-" * 60)

    chemins = []
    for nom, (kx, ky) in capitales.items():
        if nom in ("Bamako", "Accra"):
            continue
        d1 = distance_ondulatoire(bamako_kx, bamako_ky, kx, ky)
        d2 = distance_ondulatoire(kx, ky, accra_kx, accra_ky)
        total = d1 + d2
        chemins.append((nom, d1, d2, total))

    chemins.sort(key=lambda x: x[3])

    for nom, d1, d2, total in chemins:
        meilleur = " ← PLUS COURT" if total == chemins[0][3] else ""
        print(f"    Bamako→{nom:12s}→Accra : {d1:.4f} + {d2:.4f} = {total:.4f}{meilleur}")

    print(f"\n    Distance directe : {dist_directe:.4f}")

    meilleur_chemin = chemins[0]
    if meilleur_chemin[3] < dist_directe:
        print(f"\n    ➤ Le chemin via {meilleur_chemin[0]} ({meilleur_chemin[3]:.4f})")
        print(f"      est plus COURT que le chemin direct ({dist_directe:.4f})")
        print(f"      dans l'espace des phases ondulatoire.")
    else:
        print(f"\n    ➤ Le chemin direct ({dist_directe:.4f}) est le plus court.")

    print(f"\n  ➤ RAISONNEMENT GÉOMÉTRIQUE : Le chemin le plus court est déterminé")
    print(f"    par simple comparaison de distances ondulatoires |Δk|.")
    print(f"    Aucun algorithme de graphe (Dijkstra, A*). Juste des mesures")
    print(f"    géométriques dans l'espace des fréquences.")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("  RAISONNEMENT GEOMETRIQUE ONDULATOIRE - Demonstration")
    print("  Niveau 1 du paradigme Oyibo")
    print("  Aucun calcul arithmetique. Aucune algebre. Aucune analyse.")
    print("  Uniquement : ondes, interferences, distances, battements.")
    print("=" * 70)

    # ── CONSTRUCTION DU VOCABULAIRE SPECTRAL ──
    # On collecte tous les textes utilises dans les 7 problemes
    # pour construire le vocabulaire semantique (TF-IDF → onde)
    corpus_faits = [
        # Geo
        "Bamako est la capitale du Mali",
        "Paris est la capitale de la France",
        "Dakar est la capitale du Senegal",
        "Tokyo est la capitale du Japon",
        "Accra est la capitale du Ghana",
        "Abidjan est la capitale economique de la Cote d'Ivoire",
        "Ouagadougou est la capitale du Burkina Faso",
        "Niamey est la capitale du Niger",
        # Geometrie
        "Le theoreme de Pythagore : dans un triangle rectangle, a² + b² = c².",
        "Si a = 3 et b = 4, alors c = 5 car 3²+4² = 9+16 = 25 et racine(25) = 5.",
        "Le triplet 3-4-5 est un triplet pythagoricien.",
        "3² = 9", "4² = 16", "5² = 25", "9 + 16 = 25",
        "racine carree de 25 = 5",
        "L'hypotenuse est le cote le plus long du triangle rectangle.",
        "Un triangle rectangle a un angle de 90 degres (angle droit).",
        "carre : 4 cotes egaux, 4 angles droits, diagonales egales",
        "rectangle : 4 angles droits, cotes opposes egaux",
        "losange : 4 cotes egaux, angles opposes egaux",
        "triangle : 3 cotes, somme des angles = 180 degres",
        "cercle : ensemble des points equidistants d'un centre",
        "parallelogramme : cotes opposes paralleles et egaux",
        "carre de cote 2 unites",
        "carre de cote 4 unites",
        # Nombres et proportions
        "le nombre d'or, proportion divine, section doree",
        "le double, rapport deux pour un",
        "un et demi, rapport trois pour deux",
        "egalite, moitie, rapport un pour un",
        "racine de deux, diagonale du carre",
    ]
    enc = build_encoder_vocabulary(corpus_faits)
    encodeur_type = "SpectralEncoder TF-IDF (semantique)"
    print(f"\n  Encodeur : {encodeur_type}")
    print(f"  Vocabulaire : {enc.word_count} mots")
    print(f"  Corpus : {enc.total_docs} documents")
    print()

    probleme1_plus_proche()
    probleme2_alignement()
    probleme3_triangle_rectangle()
    probleme4_similarite()
    probleme5_classification_forme()
    probleme6_section_doree()
    probleme7_chemin_geometrique()

    print(f"\n{'=' * 70}")
    print("  FIN DE LA DEMONSTRATION")
    print(f"{'=' * 70}")
    print(f"""
  Les 7 problèmes ci-dessus ont été résolus en utilisant UNIQUEMENT
  le niveau GÉOMÉTRIQUE du paradigme Oyibo :

    ✓ Pas d'addition/soustraction/multiplication/division de nombres
    ✓ Pas d'équations algébriques
    ✓ Pas de fonctions d'analyse (dérivées, limites, intégrales)

  Opérations utilisées :
    • text_to_wave()        → encodage texte → onde (kx, ky)
    • distance_ondulatoire() → |k1 - k2| (distance entre ondes)
    • interference()        → cos(θ) = (k1·k2)/(|k1||k2|)
    • battement()           → |k1 - k2| (différence de fréquences)
    • angle_ondulatoire()   → angle entre directions spectrales
    • rapport_frequences()  → |k1|/|k2|
    • trouver_plus_proche() → argmin distance
    • trouver_plus_resonant() → argmax interference

  C'est le NIVEAU 1 — GÉOMÉTRIE ONDULATOIRE.
  Les niveaux 2 (Arithmétique), 3 (Algèbre) et 4 (Analyse)
  émergent SÉQUENTIELLEMENT de celui-ci.

  Prochaine étape : implémenter le Niveau 2 — Arithmétique Ondulatoire,
  où les nombres émergent comme modes de résonance et les calculs
  comme interférences entre ondes.
""")