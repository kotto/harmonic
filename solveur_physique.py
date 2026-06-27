#!/usr/bin/env python3
"""
SOLVEUR PHYSIQUE — Extension harmonique au domaine de la physique
==================================================================
Module pluggable pour le système harmonique universel.
Chaque domaine fournit : vocabulaire, extracteur, solveur.

Domaines couverts :
  - Mécanique classique (F=ma, énergie cinétique/potentielle, travail, puissance)
  - Électricité (U=RI, P=UI, résistances série/parallèle)
  - Gravitation/Newton (F=GmM/r², poids P=mg)
  - Optique/Ondes (v=fλ, période, fréquence)
  - Thermodynamique (Q=mcΔT, gaz parfait PV=nRT)
  - Énergie (E=mc², énergie cinétique, conservation)

Usage :
  python solveur_physique.py                     # démo
  python solveur_physique.py -p "F=10N m=2kg a=?"
"""

import re
import math
from typing import Dict, List, Tuple, Optional

# ═══════════════════════════════════════════════════════════════
# VOCABULAIRE PHYSIQUE (~150 tokens)
# ═══════════════════════════════════════════════════════════════

VOCAB_PHYSIQUE = [
    # Unités SI
    'm', 'kg', 's', 'N', 'J', 'W', 'Pa', 'Hz', 'V', 'A', 'Ω',
    'C', 'F', 'T', 'K', 'mol', '°C', 'm/s', 'm/s²', 'kg/m³',
    'km', 'cm', 'mm', 'g', 'h', 'min', '°', 'rad',
    # Grandeurs mécaniques
    'force', 'masse', 'acceleration', 'vitesse', 'deplacement',
    'energie', 'travail', 'puissance', 'pression', 'volume',
    'densite', 'frottement', 'tension_corde', 'ressort',
    'moment', 'couple', 'impulsion', 'quantite_mouvement',
    # Grandeurs électriques
    'tension', 'courant', 'resistance', 'capacite', 'inductance',
    'charge', 'potentiel', 'conductance', 'impedance',
    'ohm', 'ampere', 'volt', 'watt', 'farad', 'henry', 'coulomb',
    'serie', 'parallele', 'circuit', 'batterie',
    # Grandeurs thermodynamiques
    'temperature', 'chaleur', 'entropie', 'enthalpie',
    'capacite_calorifique', 'gaz_parfait', 'isotherme',
    # Optique / Ondes
    'frequence', 'periode', 'longueur_onde', 'amplitude',
    'vitesse_lumiere', 'indice_refraction', 'diffraction',
    'interference', 'photon', 'onde',
    # Gravitation / Cosmologie
    'gravite', 'attraction', 'poids', 'masse_terre', 'orbite',
    'satellite', 'kepler', 'newton', 'einstein',
    # Constantes
    'g', 'G', 'c', 'h', 'e', 'k', 'R', 'π',
    # Lois / Équations
    'loi', 'equation', 'formule', 'theoreme', 'principe',
    'conservation', 'equilibre', 'newton', 'ohm', 'joule',
    'coulomb', 'faraday', 'maxwell', 'planck',
    # Mots-clés généraux
    'calcule', 'trouve', 'determine', 'quelle', 'quel', 'combien',
    'vaut', 'donne', 'resultat', 'solution', 'reponse',
    'accelere', 'freine', 'tombe', 'monte', 'descend',
    'chauffe', 'refroidit', 'circule', 'resiste',
    # Tokens existants réutilisés (opérateurs, nombres)
    '0','1','2','3','4','5','6','7','8','9','10',
    '20','30','40','50','100','1000',
    '+','-','*','/','=','^','(',')','.',',',
]

# ═══════════════════════════════════════════════════════════════
# CONSTANTES PHYSIQUES
# ═══════════════════════════════════════════════════════════════

CONSTANTES = {
    'g': 9.81,         # pesanteur terrestre (m/s²)
    'G': 6.674e-11,     # constante gravitationnelle (N·m²/kg²)
    'c': 299792458,     # vitesse de la lumière (m/s)
    'e': 1.602e-19,     # charge élémentaire (C)
    'k_B': 1.381e-23,   # Boltzmann (J/K)
    'R': 8.314,         # gaz parfait (J/(mol·K))
    'h': 6.626e-34,     # Planck (J·s)
    'masse_terre': 5.972e24,  # kg
    'rayon_terre': 6371000,   # m
}

# ═══════════════════════════════════════════════════════════════
# EXTRACTEUR PHYSIQUE
# ═══════════════════════════════════════════════════════════════

def extraire_physique(texte: str) -> Dict:
    """
    Extrait les paramètres d'un problème de physique.
    Supporte: mécanique (F=ma), électricité (U=RI), énergie (E=½mv²),
              gravitation (poids), ondes (v=fλ), thermo (Q=mcΔT).

    Retourne: dict avec 'type_probleme' et les paramètres extraits
    """
    t = texte.lower()
    nums = [float(n) for n in re.findall(r'(\d+\.?\d*)', texte)]

    params = {'type_probleme': 'inconnu', 'numeros': nums}

    # ── Détection du type de problème ──
    if any(m in t for m in ['force', 'newton', 'accelere', 'acceleration',
                              'pousse', 'tire', 'frottement']):
        params['type_probleme'] = 'mecanique'

    elif any(m in t for m in ['electrique', 'tension', 'courant', 'resistance',
                                'ohm', 'volt', 'ampere', 'circuit', 'batterie']):
        params['type_probleme'] = 'electricite'

    elif any(m in t for m in ['energie', 'cinetique', 'potentielle', 'travail',
                                'puissance', 'joule', 'watt']):
        params['type_probleme'] = 'energie'

    elif any(m in t for m in ['poids', 'gravite', 'gravitation', 'masse_terre',
                                'attraction', 'orbite', 'satellite']):
        params['type_probleme'] = 'gravitation'

    elif any(m in t for m in ['frequence', 'periode', 'longueur_onde', 'onde',
                                'optique', 'lumiere', 'photon']):
        params['type_probleme'] = 'ondes'

    elif any(m in t for m in ['temperature', 'chaleur', 'thermique', 'chauffe',
                                'refroidit', 'gaz', 'entropie']):
        params['type_probleme'] = 'thermodynamique'

    # ── Mécanique : F = m·a ──
    if params['type_probleme'] == 'mecanique':
        # Force en Newtons
        m_F = re.search(r'(\d+\.?\d*)\s*N', texte)
        # Masse en kg
        m_m = re.search(r'(\d+\.?\d*)\s*kg', texte)
        # Accélération en m/s²
        m_a = re.search(r'(\d+\.?\d*)\s*m/s²', texte)

        if m_F: params['F'] = float(m_F.group(1))
        if m_m: params['m'] = float(m_m.group(1))
        if m_a: params['a'] = float(m_a.group(1))
        params['loi'] = 'F = m·a (2ᵉ loi de Newton)'

    # ── Électricité : U = R·I ──
    elif params['type_probleme'] == 'electricite':
        m_U = re.search(r'(\d+\.?\d*)\s*V', texte)
        m_R = re.search(r'(\d+\.?\d*)\s*(Ω|ohms?|ohm)', texte)
        m_I = re.search(r'(\d+\.?\d*)\s*A', texte)
        m_P = re.search(r'(\d+\.?\d*)\s*W', texte)

        if m_U: params['U'] = float(m_U.group(1))
        if m_R: params['R'] = float(m_R.group(1))
        if m_I: params['I'] = float(m_I.group(1))
        if m_P: params['P'] = float(m_P.group(1))

        # Détection série/parallèle
        if 'serie' in t: params['montage'] = 'serie'
        elif 'parallele' in t: params['montage'] = 'parallele'

        params['loi'] = 'U = R·I (loi d\'Ohm), P = U·I'

    # ── Énergie : E = ½mv², W = Fd, P = W/t ──
    elif params['type_probleme'] == 'energie':
        m_m = re.search(r'(\d+\.?\d*)\s*kg', texte)
        m_v = re.search(r'(\d+\.?\d*)\s*m/s', texte)
        m_F = re.search(r'(\d+\.?\d*)\s*N', texte)
        m_d = re.search(r'(\d+\.?\d*)\s*m', texte)
        m_t = re.search(r'(\d+\.?\d*)\s*s', texte)
        m_P = re.search(r'(\d+\.?\d*)\s*W', texte)
        m_h = re.search(r'(\d+\.?\d*)\s*m(?![a-z])', texte)

        if m_m: params['m'] = float(m_m.group(1))
        if m_v: params['v'] = float(m_v.group(1))
        if m_F: params['F'] = float(m_F.group(1))
        if m_d: params['d'] = float(m_d.group(1))
        if m_t: params['t'] = float(m_t.group(1))
        if m_P: params['P'] = float(m_P.group(1))
        if m_h: params['h'] = float(m_h.group(1))

        if 'cinetique' in t:
            params['loi'] = 'Ec = ½·m·v² (énergie cinétique)'
        elif 'potentielle' in t:
            params['loi'] = 'Ep = m·g·h (énergie potentielle)'
        else:
            params['loi'] = 'E = ½·m·v², W = F·d, P = W/t'

    # ── Gravitation : poids, F=GmM/r² ──
    elif params['type_probleme'] == 'gravitation':
        m_m = re.search(r'(\d+\.?\d*)\s*kg', texte)
        m_h = re.search(r'(\d+\.?\d*)\s*m\b', texte)
        if m_m: params['m'] = float(m_m.group(1))
        if m_h: params['h'] = float(m_h.group(1))
        params['loi'] = 'P = m·g, F = G·m·M/r²'

    # ── Ondes : v = f·λ ──
    elif params['type_probleme'] == 'ondes':
        m_v = re.search(r'(\d+\.?\d*)\s*m/s', texte)
        m_f = re.search(r'(\d+\.?\d*)\s*Hz', texte)
        m_λ = re.search(r'(\d+\.?\d*)\s*m\b', texte)
        m_T = re.search(r'(\d+\.?\d*)\s*s', texte)
        if m_v: params['v'] = float(m_v.group(1))
        if m_f: params['f'] = float(m_f.group(1))
        if m_λ: params['λ'] = float(m_λ.group(1))
        if m_T: params['T'] = float(m_T.group(1))
        params['loi'] = 'v = f·λ, T = 1/f'

    # ── Thermo : Q = m·c·ΔT ──
    elif params['type_probleme'] == 'thermodynamique':
        m_m = re.search(r'(\d+\.?\d*)\s*kg', texte)
        m_ΔT = re.search(r'(\d+\.?\d*)\s*[°K]', texte)
        m_Q = re.search(r'(\d+\.?\d*)\s*J', texte)
        m_c = re.search(r'(\d+\.?\d*)\s*J/(kg|Kg)', texte)
        if m_Q: params['Q'] = float(m_Q.group(1))
        if m_m: params['m'] = float(m_m.group(1))
        if m_c: params['c'] = float(m_c.group(1))
        if m_ΔT: params['ΔT'] = float(m_ΔT.group(1))
        params['loi'] = 'Q = m·c·ΔT'

    return params


# ═══════════════════════════════════════════════════════════════
# SOLVEUR PHYSIQUE
# ═══════════════════════════════════════════════════════════════

def resoudre_physique(params: Dict) -> Dict:
    """
    Résout un problème de physique à partir des paramètres extraits.

    Retourne: dict avec 'solution', 'formule', 'unites', 'explication'
    """
    ptype = params.get('type_probleme', 'inconnu')
    resultat = {
        'domaine': 'physique',
        'type_probleme': ptype,
        'loi': params.get('loi', ''),
    }

    # ── Mécanique : F = m·a ──
    if ptype == 'mecanique':
        F = params.get('F')
        m = params.get('m')
        a = params.get('a')

        if F is not None and m is not None and a is None:
            a = F / m
            resultat['inconnue'] = 'a (accélération)'
            resultat['valeur'] = round(a, 4)
            resultat['unite'] = 'm/s²'
            resultat['formule'] = f'a = F/m = {F}/{m} = {a:.3f} m/s²'
        elif m is not None and a is not None and F is None:
            F = m * a
            resultat['inconnue'] = 'F (force)'
            resultat['valeur'] = round(F, 4)
            resultat['unite'] = 'N'
            resultat['formule'] = f'F = m·a = {m}×{a} = {F:.3f} N'
        elif F is not None and a is not None and m is None:
            m = F / a
            resultat['inconnue'] = 'm (masse)'
            resultat['valeur'] = round(m, 4)
            resultat['unite'] = 'kg'
            resultat['formule'] = f'm = F/a = {F}/{a} = {m:.3f} kg'
        else:
            resultat['erreur'] = 'Données insuffisantes (besoin de 2 sur F, m, a)'

    # ── Électricité : U = R·I ──
    elif ptype == 'electricite':
        U = params.get('U')
        R = params.get('R')
        I = params.get('I')
        P = params.get('P')

        if U is not None and R is not None and I is None:
            I = U / R
            resultat['inconnue'] = 'I (courant)'
            resultat['valeur'] = round(I, 4)
            resultat['unite'] = 'A'
            resultat['formule'] = f'I = U/R = {U}/{R} = {I:.3f} A'
        elif U is not None and I is not None and R is None:
            R = U / I
            resultat['inconnue'] = 'R (résistance)'
            resultat['valeur'] = round(R, 4)
            resultat['unite'] = 'Ω'
            resultat['formule'] = f'R = U/I = {U}/{I} = {R:.3f} Ω'
        elif R is not None and I is not None and U is None:
            U = R * I
            resultat['inconnue'] = 'U (tension)'
            resultat['valeur'] = round(U, 4)
            resultat['unite'] = 'V'
            resultat['formule'] = f'U = R·I = {R}×{I} = {U:.3f} V'
        elif U is not None and I is not None and P is None:
            P = U * I
            resultat['inconnue'] = 'P (puissance)'
            resultat['valeur'] = round(P, 4)
            resultat['unite'] = 'W'
            resultat['formule'] = f'P = U·I = {U}×{I} = {P:.3f} W'
        else:
            resultat['erreur'] = 'Données insuffisantes (besoin de U, R ou I)'

    # ── Énergie ──
    elif ptype == 'energie':
        m = params.get('m')
        v = params.get('v')
        F = params.get('F')
        d = params.get('d')
        t = params.get('t')
        h = params.get('h')

        if m is not None and v is not None:
            Ec = 0.5 * m * v**2
            resultat['inconnue'] = 'Ec (énergie cinétique)'
            resultat['valeur'] = round(Ec, 4)
            resultat['unite'] = 'J'
            resultat['formule'] = f'Ec = ½·m·v² = 0.5×{m}×{v}² = {Ec:.3f} J'
        elif m is not None and h is not None:
            Ep = m * CONSTANTES['g'] * h
            resultat['inconnue'] = 'Ep (énergie potentielle)'
            resultat['valeur'] = round(Ep, 4)
            resultat['unite'] = 'J'
            resultat['formule'] = f'Ep = m·g·h = {m}×9.81×{h} = {Ep:.3f} J'
        elif F is not None and d is not None:
            W = F * d
            resultat['inconnue'] = 'W (travail)'
            resultat['valeur'] = round(W, 4)
            resultat['unite'] = 'J'
            resultat['formule'] = f'W = F·d = {F}×{d} = {W:.3f} J'
        else:
            resultat['erreur'] = 'Données insuffisantes'

    # ── Gravitation ──
    elif ptype == 'gravitation':
        m = params.get('m')
        h = params.get('h')
        if m is not None:
            P = m * CONSTANTES['g']
            resultat['inconnue'] = 'P (poids)'
            resultat['valeur'] = round(P, 4)
            resultat['unite'] = 'N'
            resultat['formule'] = f'P = m·g = {m}×9.81 = {P:.3f} N'
            if h is not None:
                Ep = m * CONSTANTES['g'] * h
                resultat['Ep'] = round(Ep, 4)
                resultat['Ep_unite'] = 'J'
        else:
            resultat['erreur'] = 'Masse requise pour calculer le poids'

    # ── Ondes ──
    elif ptype == 'ondes':
        v = params.get('v')
        f = params.get('f')
        λ = params.get('λ')
        T = params.get('T')

        if f is not None and λ is None and v is not None:
            λ = v / f
            resultat['inconnue'] = 'λ (longueur d\'onde)'
            resultat['valeur'] = round(λ, 6)
            resultat['unite'] = 'm'
        elif f is not None and T is None:
            T = 1.0 / f
            resultat['inconnue'] = 'T (période)'
            resultat['valeur'] = round(T, 6)
            resultat['unite'] = 's'
        elif T is not None and f is None:
            f = 1.0 / T
            resultat['inconnue'] = 'f (fréquence)'
            resultat['valeur'] = round(f, 4)
            resultat['unite'] = 'Hz'
        else:
            resultat['erreur'] = 'Données insuffisantes'

    # ── Thermo ──
    elif ptype == 'thermodynamique':
        Q = params.get('Q')
        m = params.get('m')
        c = params.get('c', 4186)  # eau par défaut
        ΔT = params.get('ΔT')
        if m is not None and ΔT is not None and Q is None:
            Q = m * c * ΔT
            resultat['inconnue'] = 'Q (chaleur)'
            resultat['valeur'] = round(Q, 4)
            resultat['unite'] = 'J'
    else:
        resultat['erreur'] = f'Type de problème non reconnu: {ptype}'

    return resultat


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

EXEMPLES_PHYSIQUE = [
    "Une force de 10 N accelere une masse de 2 kg. Quelle est l'acceleration ?",
    "A resistor of 100 ohms has 12 volts. What is the current?",
    "What is the kinetic energy of a 5 kg mass moving at 10 m/s?",
    "Quel est le poids d'une masse de 70 kg ?",
    "Une onde de frequence 50 Hz a une vitesse de 340 m/s. Longueur d'onde ?",
]


def test_physique():
    print(f"\n{'='*75}")
    print(f"  SOLVEUR PHYSIQUE — Test extracteur + solveur")
    print(f"{'='*75}\n")
    for i, texte in enumerate(EXEMPLES_PHYSIQUE):
        params = extraire_physique(texte)
        resultat = resoudre_physique(params)
        ptype = params.get('type_probleme', '?')
        val = resultat.get('valeur', resultat.get('erreur', '—'))
        unite = resultat.get('unite', '')
        formule = resultat.get('formule', '')
        print(f"  [{i+1}] {texte[:55]:<55s}")
        print(f"      Type: {ptype:<15s} | Résultat: {val} {unite}")
        if formule:
            print(f"      {formule}")
        print()


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Solveur Physique Harmonique')
    p.add_argument('--test', '-t', action='store_true', help='Lancer les tests')
    p.add_argument('--probleme', '-p', type=str, default=None, help='Résoudre un problème')
    args = p.parse_args()

    if args.probleme:
        params = extraire_physique(args.probleme)
        resultat = resoudre_physique(params)
        import json
        print(json.dumps(resultat, ensure_ascii=False, indent=2, default=str))
    else:
        test_physique()