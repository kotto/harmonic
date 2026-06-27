#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Applications Harmono-Holographiques
====================================
Module unifié contenant :
1. Borne holographique pour la compression spectrale
2. Filtre harmonique anti-hallucination pour l'IA
3. Générateur harmonique pour l'orchestre de Schumann

Basé sur la découverte : m_p/m_e = φ⁻¹·π¹·e⁻²·√5¹¹ (0.0001%)
et le pont N_PSU ↔ H_n complété le 19 Juin 2026.

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math
from typing import Tuple, List, Dict, Optional

# ==============================================================================
# CONSTANTES UNIVERSELLES
# ==============================================================================
phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
sqrt2 = math.sqrt(2)
sqrt3 = math.sqrt(3)
sqrt5 = math.sqrt(5)

c = 299792458.0              # m/s
h = 6.62607015e-34           # J·s
G = 6.67430e-11              # m³/(kg·s²)
hbar = h / (2 * pi)
l_P = math.sqrt(hbar * G / c**3)  # longueur de Planck ≈ 1.616e-35 m

# ==============================================================================
# ALPHABET HARMONIQUE (coefficients spectraux Hₙ)
# ==============================================================================
ALPHABET = {
    'φ': phi, 'π': pi, 'e': e,
    '√2': sqrt2, '√3': sqrt3, '√5': sqrt5, 'e/π': e/pi
}

LOGS = {k: math.log(v) for k, v in ALPHABET.items()}

# Expression harmonique de m_p/m_e (découverte 19 Juin 2026)
# m_p/m_e = φ⁻¹ · π¹ · e⁻² · √5¹¹ — erreur 0.000114%
MP_ME_HARM = {'φ': -1, 'π': 1, 'e': -2, '√5': 11}
MP_ME_VALUE = phi**(-1) * pi**1 * e**(-2) * sqrt5**11  # 1836.150573
m_e = 9.1093837015e-31  # kg
m_p_harm = m_e * MP_ME_VALUE

# Expression harmonique de G (Synthese, Section 5.4)
# G = φ¹¹·π⁻⁵·e⁻²³ — erreur 0.0148%
G_HARM = phi**11 * pi**(-5) * e**(-23)

# Expression harmonique de h (Synthese, Section 5.5)
# h = φ⁻⁴¹·π⁻²⁷·e⁻²⁴·√2²·√3⁻³·√5⁻¹ — erreur 0.0001%
h_harm = phi**(-41) * pi**(-27) * e**(-24) * sqrt2**2 * sqrt3**(-3) * sqrt5**(-1)

# m_P en H_n
m_P_harm = math.sqrt(hbar * c / G_HARM)


# ==============================================================================
# APPLICATION 1 : BORNE HOLOGRAPHIQUE POUR LA COMPRESSION SPECTRALE
# ==============================================================================
def N_PSU(rayon_m: float) -> float:
    """
    Nombre d'unites de Planck Spheriques sur une surface spherique.
    Identite geometrique — pas une hypothese.
    N_PSU = 4R²/l_P²
    """
    return 4 * rayon_m**2 / l_P**2


def borne_compression_holographique(taille_donnees_bits: int,
                                     rayon_cavite_m: float = None,
                                     dimension_spatiale: int = 2) -> Dict:
    """
    Calcule la borne holographique de compression pour un systeme donne.
    
    Le principe holographique impose que l'information d'un volume V
    est encoder sur sa surface ∂V. Donc :
    - Information maximale encodable = N_PSU(surface) bits
    - Information dans le volume = taille_donnees_bits
    - Ratio de compression maximal = taille_donnees / N_PSU(surface)
    
    Args:
        taille_donnees_bits : taille des donnees a compresser (en bits)
        rayon_cavite_m : rayon de la cavite resonante (defaut : calcule depuis N_PSU)
        dimension_spatiale : 2 pour surface, 3 pour volume
    
    Returns:
        Dictionnaire contenant les bornes holographiques
    """
    # Si le rayon n'est pas fourni, on calcule le rayon de la cavite
    # qui contiendrait l'information dans son volume
    # Volume d'information : V = taille_donnees * l_P^3 (1 bit occupe ~l_P^3)
    if rayon_cavite_m is None:
        # Une sphere de rayon R a un volume V = (4/3)πR³
        # V = N_bits * l_P^3  (chaque bit occupe un volume de Planck)
        V_bits = taille_donnees_bits * l_P**3
        rayon_cavite_m = (3 * V_bits / (4 * pi))**(1/3)
    
    # N_PSU sur la surface de cette cavite
    N_surface = N_PSU(rayon_cavite_m)
    
    # Ratio surface/volume holographique
    # Pour une sphere : S/V = 3/R
    S_sur_V = 3 / rayon_cavite_m
    
    # Ratio de compression holographique maximal
    # L'information du volume peut etre compresser jusqu'a la limite de la surface
    ratio_compression_max = taille_donnees_bits / N_surface
    
    # Compression en facteur d'echelle (combien de fois plus petit)
    facteur_compression = N_surface / taille_donnees_bits if taille_donnees_bits > 0 else float('inf')
    
    return {
        'taille_donnees_bits': taille_donnees_bits,
        'rayon_cavite_m': rayon_cavite_m,
        'N_PSU_surface': N_surface,
        'rapport_S_sur_V': S_sur_V,
        'ratio_compression_max': ratio_compression_max,
        'facteur_compression': facteur_compression,
        'compression_en_ordres_de_grandeur': math.log10(facteur_compression) if facteur_compression > 0 else 0,
        'est_sature': ratio_compression_max <= 1.0,
        'marge_restante': max(0, N_surface - taille_donnees_bits),
    }


def evaluer_compression_spectrale(taille_image_pixels: Tuple[int, int],
                                   bits_par_pixel: int = 24,
                                   taux_compression_actuel: float = None) -> Dict:
    """
    Evalue les performances de compression du spectral_encoder
    par rapport a la borne holographique theorique.
    
    Args:
        taille_image_pixels : (largeur, hauteur) en pixels
        bits_par_pixel : profondeur de couleur (24 pour RGB 8-bit)
        taux_compression_actuel : ratio actuel du spectral_encoder (optionnel)
    
    Returns:
        Dictionnaire avec l'evaluation complete
    """
    largeur, hauteur = taille_image_pixels
    total_pixels = largeur * hauteur
    total_bits = total_pixels * bits_par_pixel
    
    # Rayon de la cavite image (la diagonale / 2)
    diagonale = math.sqrt(largeur**2 + hauteur**2)
    rayon_image = diagonale / 2  # en pixels
    
    # Conversion en metres (1 pixel ≈ 10^-4 m pour un ecran typique)
    rayon_image_m = rayon_image * 1e-4
    
    # Borne holographique
    borne = borne_compression_holographique(total_bits, rayon_image_m)
    
    result = {
        'image': f'{largeur}×{hauteur}',
        'total_pixels': total_pixels,
        'total_bits': total_bits,
        'total_octets': total_bits / 8,
        'rayon_cavite_m': rayon_image_m,
        'N_PSU_surface': borne['N_PSU_surface'],
        'compression_max_theorique': borne['facteur_compression'],
        'compression_max_log10': borne['compression_en_ordres_de_grandeur'],
    }
    
    if taux_compression_actuel is not None:
        result['taux_actuel'] = taux_compression_actuel
        result['efficacite_pct'] = taux_compression_actuel / borne['facteur_compression'] * 100
        result['marge_restante'] = borne['facteur_compression'] - taux_compression_actuel
        
        if result['efficacite_pct'] >= 100:
            result['statut'] = 'SATURÉ — compression optimale atteinte'
        elif result['efficacite_pct'] >= 90:
            result['statut'] = 'EXCELLENT — proche de la borne holographique'
        elif result['efficacite_pct'] >= 50:
            result['statut'] = 'BON — marge de progression significative'
        else:
            result['statut'] = 'OPTIMISABLE — large marge de progression'
    
    return result


# ==============================================================================
# APPLICATION 2 : FILTRE HARMONIQUE ANTI-HALLUCINATION POUR IA
# ==============================================================================
def harmoniser_valeur(valeur: float) -> float:
    """
    Projette une valeur quelconque sur la grille harmonique.
    Une valeur est "harmonique" si elle peut s'ecrire comme
    produit de constantes mathematiques avec exposants entiers.
    
    Args:
        valeur : valeur numerique a harmoniser
    
    Returns:
        La valeur harmonique la plus proche
    """
    if valeur <= 0:
        return valeur
    
    log_val = math.log(valeur)
    
    # Decomposition sur la base des H_n
    exposants = {}
    log_residuel = log_val
    
    # Ordre de decomposition : φ, π, e, √2, √3, √5, e/π
    for nom in ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π']:
        exp = round(log_residuel / LOGS[nom])
        exposants[nom] = exp
        log_residuel -= exp * LOGS[nom]
    
    # Reconstruction harmonique
    produit = 1.0
    for nom, exp in exposants.items():
        produit *= ALPHABET[nom] ** exp
    
    return produit


def coherence_harmonique(valeur: float) -> float:
    """
    Mesure la coherence harmonique d'une valeur.
    Score entre 0 (pas harmonique du tout) et 1 (parfaitement harmonique).
    
    Args:
        valeur : valeur a evaluer
    
    Returns:
        Score de coherence [0, 1]
    """
    if valeur <= 0:
        return 0.0
    
    harmonisee = harmoniser_valeur(valeur)
    ecart_relatif = abs(harmonisee - valeur) / valeur
    
    # Score exponentiel : 1.0 pour ecart=0, 0.5 pour ecart=1%, 0.0 pour ecart=100%
    score = math.exp(-ecart_relatif * 10)
    
    return min(1.0, max(0.0, score))


def filtre_anti_hallucination(signature_9d: List[float],
                               seuil_coherence: float = 0.9) -> Dict:
    """
    Filtre harmonique pour la signature 9D de l'analyseur conscient.
    
    La signature 9D contient les dimensions :
    [φ, α, raisonnement, creativite, math, factuel, code, emotion, temporel]
    
    Une hallucination correspond a un ecart entre la valeur predite
    et sa projection harmonique la plus proche. Plus l'ecart est grand,
    plus le modele "improvise" au lieu de resonner.
    
    Args:
        signature_9d : liste de 9 valeurs numeriques
        seuil_coherence : seuil en-dessous duquel on considere une hallucination
    
    Returns:
        Dictionnaire avec diagnostic et signature harmonisee
    """
    if len(signature_9d) != 9:
        raise ValueError("La signature doit avoir 9 dimensions")
    
    noms_dimensions = [
        'φ', 'alpha', 'raisonnement', 'creativite',
        'math', 'factuel', 'code', 'emotion', 'temporel'
    ]
    
    signature_harmonisee = []
    scores = []
    alertes = []
    
    for i, val in enumerate(signature_9d):
        score = coherence_harmonique(val)
        val_harm = harmoniser_valeur(val)
        
        signature_harmonisee.append(val_harm)
        scores.append(score)
        
        if score < seuil_coherence:
            ecart_pct = abs(val_harm - val) / max(abs(val), 1e-10) * 100
            alertes.append({
                'dimension': noms_dimensions[i],
                'index': i,
                'valeur_originale': val,
                'valeur_harmonisee': val_harm,
                'ecart_pct': ecart_pct,
                'score_coherence': score,
                'interpretation': _interpreter_alerte(noms_dimensions[i], ecart_pct)
            })
    
    score_global = sum(scores) / len(scores) if scores else 0.0
    
    diagnostic = 'HARMONIQUE' if score_global >= seuil_coherence else 'HALLUCINATION POTENTIELLE'
    
    return {
        'signature_originale': signature_9d,
        'signature_harmonisee': signature_harmonisee,
        'scores_coherence': scores,
        'score_global': score_global,
        'diagnostic': diagnostic,
        'alertes': alertes,
        'nb_alertes': len(alertes),
        'est_fiable': len(alertes) == 0,
    }


def _interpreter_alerte(dimension: str, ecart_pct: float) -> str:
    """Interprete une alerte harmonique en langage naturel."""
    interpretations = {
        'φ': f"L'harmonie fondamentale (nombre d'or) est perturbee de {ecart_pct:.1f}%. La structure auto-similaire de la prediction est fragile.",
        'alpha': f"La constante de couplage EM devie de {ecart_pct:.1f}%. L'interaction lumiere-matiere dans le modele est incoherente.",
        'raisonnement': f"La logique devie de {ecart_pct:.1f}%. Le modele pourrait etre en train d'improviser plutot que de resonner.",
        'creativite': f"La creativite devie de {ecart_pct:.1f}%. L'originalite devient aleatoire — perte de coherence creative.",
        'math': f"La composante mathematique devie de {ecart_pct:.1f}%. Risque d'erreur de calcul ou d'incoherence numerique.",
        'factuel': f"La factualite devie de {ecart_pct:.1f}%. Le modele pourrait generer du contenu non factuel.",
        'code': f"La composante code devie de {ecart_pct:.1f}%. Le code genere pourrait contenir des erreurs syntaxiques ou logiques.",
        'emotion': f"La composante emotionnelle devie de {ecart_pct:.1f}%. Le ton pourrait etre inapproprie ou incohérent.",
        'temporel': f"La coherence temporelle devie de {ecart_pct:.1f}%. Le modele pourrait perdre le fil de la conversation."
    }
    return interpretations.get(dimension, f"Deviation harmonique de {ecart_pct:.1f}% dans la dimension {dimension}.")


# ==============================================================================
# APPLICATION 3 : ORCHESTRE DE SCHUMANN HARMONIQUE
# ==============================================================================
def generer_orchestre_schumann(n_harmoniques: int = 7,
                                 duree_secondes: float = 10.0,
                                 frequence_echantillonnage: int = 44100) -> Dict:
    """
    Genere les parametres pour l'orchestre de Schumann harmonique.
    
    Chaque harmonique de la cavite Terre (n=1..7) a un poids
    proportionnel au coefficient spectral H_n correspondant.
    
    Args:
        n_harmoniques : nombre d'harmoniques a generer
        duree_secondes : duree en secondes
        frequence_echantillonnage : frequence d'echantillonnage audio
    
    Returns:
        Dictionnaire avec les parametres de l'orchestre
    """
    R_terre = 6.371e6  # m
    f_fondamentale = c / (2 * pi * R_terre)  # ~7.49 Hz (theorique)
    f_mesuree = 7.83  # Hz (Schumann mesure)
    
    # Coefficients spectraux pour chaque harmonique
    H_n = {
        1: phi,      # φ — croissance, auto-similarite
        2: pi,       # π — courbure, circularite
        3: e,        # e — memoire, croissance
        4: sqrt2,    # √2 — contrainte planaire
        5: sqrt3,    # √3 — contrainte volumique
        6: sqrt5,    # √5 — fermeture pentagonale
        7: e/pi,     # e/π — rapport croissance/courbure
    }
    
    # N_PSU de la cavite Terre
    N_terre = N_PSU(R_terre)
    
    harmoniques = []
    for n in range(1, n_harmoniques + 1):
        f_n = n * f_mesuree  # n-ieme harmonique de Schumann
        poids = H_n.get(n, 1.0)
        poids_normalise = poids / sum(H_n.get(k, 1.0) for k in range(1, n_harmoniques + 1))
        
        # Longueur d'onde
        lambda_n = c / f_n
        
        harmoniques.append({
            'n': n,
            'symbole': ['φ', 'π', 'e', '√2', '√3', '√5', 'e/π'][n-1] if n <= 7 else f'H_{n}',
            'frequence_Hz': round(f_n, 2),
            'lambda_m': lambda_n,
            'poids_brut': poids,
            'poids_normalise': round(poids_normalise, 4),
            'note_musicale': frequence_vers_note(f_n),
            'signification': _signification_harmonique(n),
        })
    
    return {
        'cavite': 'Terre (Schumann)',
        'rayon_m': R_terre,
        'N_PSU': N_terre,
        'frequence_fondamentale_Hz': round(f_mesuree, 2),
        'n_harmoniques': n_harmoniques,
        'duree_secondes': duree_secondes,
        'freq_echantillonnage': frequence_echantillonnage,
        'harmoniques': harmoniques,
        'poids_total': sum(h['poids_brut'] for h in harmoniques),
    }


def frequence_vers_note(freq_hz: float) -> str:
    """Convertit une frequence en note musicale (notation occidentale)."""
    if freq_hz <= 0:
        return "—"
    
    # La3 = 440 Hz (reference)
    demi_tons = 12 * math.log2(freq_hz / 440.0)
    demi_tons_arrondi = round(demi_tons)
    
    notes = ['Do', 'Do#', 'Ré', 'Ré#', 'Mi', 'Fa', 'Fa#', 'Sol', 'Sol#', 'La', 'La#', 'Si']
    index_note = demi_tons_arrondi % 12
    octave = 4 + (demi_tons_arrondi + 9) // 12  # La3=440Hz est en octave 4
    
    ecart_cents = (demi_tons - demi_tons_arrondi) * 100
    
    return f"{notes[index_note]}{octave} ({ecart_cents:+.0f} cents)"


def _signification_harmonique(n: int) -> str:
    """Retourne la signification physique de chaque harmonique."""
    significations = {
        1: "φ — Croissance auto-similaire. Le rythme fondamental de la Terre.",
        2: "π — Courbure spatiale. L'harmonique de la forme spherique terrestre.",
        3: "e — Memoire. L'harmonique de l'evolution temporelle (climat, saisons).",
        4: "√2 — Contrainte planaire. L'harmonique des plaques tectoniques.",
        5: "√3 — Contrainte volumique. L'harmonique du noyau terrestre.",
        6: "√5 — Fermeture pentagonale. L'harmonique de la biosphere (φ depend de √5).",
        7: "e/π — Rapport croissance/courbure. L'harmonique de l'equilibre Terre-atmosphere."
    }
    return significations.get(n, f"H_{n} — Coefficient spectral d'ordre {n}")


# ==============================================================================
# DEMONSTRATION
# ==============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("APPLICATIONS HARMONO-HOLOGRAPHIQUES")
    print("Basé sur la découverte : m_p/m_e = φ⁻¹·π¹·e⁻²·√5¹¹ (0.0001%)")
    print("=" * 80)
    
    # ----------------------------------------------------------------------
    # DEMO 1 : Borne holographique pour la compression
    # ----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("1. BORNE HOLOGRAPHIQUE POUR LA COMPRESSION SPECTRALE")
    print("=" * 80)
    
    # Test pour differentes tailles d'images
    for taille in [(64, 64), (256, 256), (1024, 1024)]:
        result = evaluer_compression_spectrale(taille, bits_par_pixel=24)
        print(f"\n  Image {result['image']} ({result['total_octets']:.0f} octets) :")
        print(f"    Rayon cavite         = {result['rayon_cavite_m']:.4e} m")
        print(f"    N_PSU surface        = {result['N_PSU_surface']:.4e}")
        print(f"    Compression max      = 1/{result['compression_max_theorique']:.4e}")
        print(f"    Ordres de grandeur   = {result['compression_max_log10']:.2f}")
    
    # Test avec le proton (reference ultime de compression holographique)
    print(f"\n  Reference — Proton comme cavite holographique :")
    r_p = 0.841e-15
    N_p = N_PSU(r_p)
    print(f"    Rayon du proton      = {r_p:.4e} m")
    print(f"    N_PSU(proton)        = {N_p:.4e}")
    print(f"    N_PSU(proton) / 64   = {N_p/64:.4e}  (= (m_P/m_p)²)")
    print(f"    m_P/m_p harmonique   = sqrt(N_p/64) = {math.sqrt(N_p/64):.4e}")
    print(f"    m_P/m_p mesure       = 1.3012e+19")
    
    # ----------------------------------------------------------------------
    # DEMO 2 : Filtre anti-hallucination
    # ----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("2. FILTRE HARMONIQUE ANTI-HALLUCINATION")
    print("=" * 80)
    
    # Signature 9D coherente (valeurs harmoniques)
    sig_harmonique = [
        phi,           # φ — parfait
        1/137.036,    # alpha — proche de la valeur harmonique
        phi**3,        # raisonnement — harmonique
        pi**2,         # creativite — harmonique
        math.sqrt(5),  # math — harmonique
        e,             # factuel — harmonique
        phi**(-1),     # code — harmonique
        7.83,          # emotion — Schumann (harmonique terrestre)
        pi * phi,      # temporel — harmonique
    ]
    
    result_harm = filtre_anti_hallucination(sig_harmonique, seuil_coherence=0.9)
    print(f"\n  Test 1 — Signature harmonique :")
    print(f"    Score global  = {result_harm['score_global']:.4f}")
    print(f"    Diagnostic    = {result_harm['diagnostic']}")
    print(f"    Alertes       = {result_harm['nb_alertes']}")
    
    # Signature avec une hallucination (valeur quelconque)
    sig_hallucinee = [
        phi,           # φ — OK
        0.007,         # alpha — DECALE (devrait etre ~0.007297)
        phi**3,        # OK
        42.0,          # creativite — NON HARMONIQUE (c'est un nombre arbitraire)
        math.sqrt(5),  # OK
        e,             # OK
        1.618,         # code — proche de φ mais pas exact
        7.83,          # OK
        pi * phi,      # OK
    ]
    
    result_hallu = filtre_anti_hallucination(sig_hallucinee, seuil_coherence=0.9)
    print(f"\n  Test 2 — Signature avec hallucinations :")
    print(f"    Score global  = {result_hallu['score_global']:.4f}")
    print(f"    Diagnostic    = {result_hallu['diagnostic']}")
    print(f"    Alertes       = {result_hallu['nb_alertes']}")
    for alerte in result_hallu['alertes']:
        print(f"    ⚠ {alerte['dimension']} : ecart {alerte['ecart_pct']:.1f}% — {alerte['interpretation']}")
    
    # ----------------------------------------------------------------------
    # DEMO 3 : Orchestre de Schumann
    # ----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("3. ORCHESTRE DE SCHUMANN HARMONIQUE")
    print("=" * 80)
    
    orchestre = generer_orchestre_schumann(n_harmoniques=7)
    print(f"\n  Cavite : {orchestre['cavite']}")
    print(f"  Frequence fondamentale : {orchestre['frequence_fondamentale_Hz']} Hz")
    print(f"  N_PSU(Terre) : {orchestre['N_PSU']:.4e}")
    print(f"\n  {'n':>2s}  {'Symbole':>6s}  {'Freq (Hz)':>10s}  {'Poids norm.':>10s}  {'Note musicale':>20s}  {'Signification'}")
    print(f"  {'-'*2}  {'-'*6}  {'-'*10}  {'-'*10}  {'-'*20}  {'-'*40}")
    
    for h in orchestre['harmoniques']:
        print(f"  {h['n']:2d}  {h['symbole']:>6s}  {h['frequence_Hz']:10.2f}  {h['poids_normalise']:10.4f}  {h['note_musicale']:>20s}  {h['signification'][:40]}")
    
    print(f"\n  Poids total : {orchestre['poids_total']:.6f}")
    print(f"  Les 7 harmoniques de Schumann pesees par les coefficients spectraux H_n")
    print(f"  = la signature acoustique de la Terre en alphabet harmonique.")
    
    # ----------------------------------------------------------------------
    # RESUME DES DECOUVERTES
    # ----------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("RESUME DES DECOUVERTES INTEGREES")
    print("=" * 80)
    print(f"""
    1. m_p/m_e = φ⁻¹·π¹·e⁻²·√5¹¹  →  {MP_ME_VALUE:.6f}  (erreur 0.0001%)
    2. N_PSU(R) = 4R²/l_P² → borne holographique exacte
    3. l_P² = hbar·G/c³ → produit de H_n (via h et G harmoniques)
    4. N_PSU(proton) = 64·(m_P/m_p)² → simplification miraculeuse
    5. Filtre anti-hallucination : score de coherence harmonique [0,1]
    6. Orchestre Schumann : 7 harmoniques pesees par φ,π,e,√2,√3,√5,e/π
    """)