#!/usr/bin/env python3
"""
SOLVEUR CHIMIE — Extension harmonique au domaine de la chimie
=============================================================
Module pluggable pour le système harmonique universel.

Domaines couverts :
  - Stoechiométrie (masse molaire, moles, masse, nombre d'Avogadro)
  - Équations bilan (équilibrage simple, réactif limitant)
  - pH et solutions (acides forts/faibles, dilution, neutralisation)
  - Gaz parfaits (PV = nRT, volume molaire, pression partielle)
  - Cinétique chimique (concentration, dilution, temps de demi-réaction)
  - Tableau périodique (masses molaires des 30 éléments les plus courants)

Usage :
  python solveur_chimie.py                       # démo
  python solveur_chimie.py -p "masse molaire H2O"
"""

import re
import math
from typing import Dict, List, Tuple, Optional

# ═══════════════════════════════════════════════════════════════
# VOCABULAIRE CHIMIE (~160 tokens)
# ═══════════════════════════════════════════════════════════════

VOCAB_CHIMIE = [
    # Éléments (30 plus courants)
    'H', 'He', 'Li', 'C', 'N', 'O', 'F', 'Ne', 'Na', 'Mg',
    'Al', 'Si', 'P', 'S', 'Cl', 'Ar', 'K', 'Ca', 'Fe', 'Cu',
    'Zn', 'Br', 'Ag', 'I', 'Ba', 'Pt', 'Au', 'Hg', 'Pb', 'U',
    # Molécules courantes
    'H2O', 'CO2', 'NaCl', 'HCl', 'NaOH', 'H2SO4', 'NH3', 'CH4',
    'C2H5OH', 'CaCO3', 'NaHCO3', 'KMnO4', 'H2O2', 'O2', 'N2',
    'H2', 'Cl2', 'C6H12O6', 'CaO', 'MgO', 'Fe2O3', 'Al2O3',
    # Concepts
    'masse_molaire', 'mole', 'moles', 'masse', 'volume', 'nombre',
    'avogadro', 'concentration', 'molarite', 'mol/l', 'mol/litre',
    'ph', 'acide', 'base', 'neutre', 'dilution', 'neutralisation',
    'reaction', 'reactif', 'produit', 'limitant', 'exces',
    'equation', 'bilan', 'equilibre', 'coefficient',
    'gaz', 'pression', 'temperature', 'kelvin', 'celsius',
    'cinetique', 'vitesse_reaction', 'demi_vie', 'catalyseur',
    # Unités
    'g', 'kg', 'mg', 'mol', 'mmol', 'l', 'ml', 'cm3', 'm3',
    'atm', 'bar', 'pa', 'kpa', '°C', 'K', 'g/mol', 'mol/l',
    # Mots-clés calculatoires
    'calcule', 'calculer', 'determiner', 'quelle', 'quel', 'combien',
    'trouve', 'donne', 'vaut', 'resultat', 'masse', 'nombre',
    'concentration', 'volume', 'pression', 'temperature', 'ph',
    # Nombres
    '0','1','2','3','4','5','6','7','8','9','10',
    '12','14','16','18','20','22.4','23','24','25',
    '30','32','36.5','40','44','50','56','58.5','60',
    '70','80','84','98','100','1000',
    '+','-','*','/','=','^','(',')','.',',','->','→',
]

# ═══════════════════════════════════════════════════════════════
# TABLEAU PÉRIODIQUE — Masses molaires (g/mol)
# ═══════════════════════════════════════════════════════════════

MASSES_MOLAIRES = {
    'H': 1.008,   'He': 4.003,  'Li': 6.941,  'C': 12.011,
    'N': 14.007,  'O': 15.999,  'F': 18.998,  'Ne': 20.180,
    'Na': 22.990, 'Mg': 24.305, 'Al': 26.982, 'Si': 28.086,
    'P': 30.974,  'S': 32.065,  'Cl': 35.453, 'Ar': 39.948,
    'K': 39.098,  'Ca': 40.078, 'Fe': 55.845, 'Cu': 63.546,
    'Zn': 65.380, 'Br': 79.904, 'Ag': 107.868,'I': 126.904,
    'Ba': 137.327,'Pt': 195.084,'Au': 196.967,'Hg': 200.590,
    'Pb': 207.200,'U': 238.029,
}

# Molécules courantes pré-calculées
MOLECULES_MASSES = {
    'H2O': 18.015, 'CO2': 44.009, 'NaCl': 58.443, 'HCl': 36.461,
    'NaOH': 39.997, 'H2SO4': 98.079, 'NH3': 17.031, 'CH4': 16.043,
    'C2H5OH': 46.069, 'CaCO3': 100.087, 'NaHCO3': 84.007,
    'KMnO4': 158.034, 'H2O2': 34.015, 'O2': 31.998, 'N2': 28.013,
    'H2': 2.016, 'Cl2': 70.906, 'C6H12O6': 180.156,
    'CaO': 56.077, 'MgO': 40.304, 'Fe2O3': 159.688, 'Al2O3': 101.961,
}

# ═══════════════════════════════════════════════════════════════
# PARSEUR DE FORMULE CHIMIQUE
# ═══════════════════════════════════════════════════════════════

def masse_molaire_formule(formule: str) -> Optional[float]:
    """
    Calcule la masse molaire à partir d'une formule chimique.
    Exemples: H2O → 18.015, NaCl → 58.443, H2SO4 → 98.079
    """
    if formule in MOLECULES_MASSES:
        return MOLECULES_MASSES[formule]

    # Parser générique : H2SO4 → 2*H + 1*S + 4*O
    masse = 0.0
    i = 0
    while i < len(formule):
        # Lire l'élément (1 ou 2 lettres)
        if i + 1 < len(formule) and formule[i+1].islower():
            element = formule[i:i+2]
            i += 2
        else:
            element = formule[i]
            i += 1

        if element not in MASSES_MOLAIRES:
            return None

        # Lire l'indice stoechiométrique
        indice = 0
        while i < len(formule) and formule[i].isdigit():
            indice = indice * 10 + int(formule[i])
            i += 1
        if indice == 0:
            indice = 1

        masse += MASSES_MOLAIRES[element] * indice

    return round(masse, 3)


# ═══════════════════════════════════════════════════════════════
# EXTRACTEUR CHIMIE
# ═══════════════════════════════════════════════════════════════

def extraire_chimie(texte: str) -> Dict:
    """
    Extrait les paramètres d'un problème de chimie.

    Types supportés :
    - masse_molaire : calcul de M à partir d'une formule
    - stoechiometrie : n = m/M, m = n×M, N = n×NA
    - ph : pH = -log[H⁺], dilution, neutralisation
    - gaz_parfaits : PV = nRT
    - concentration : C = n/V, dilution C₁V₁ = C₂V₂
    - equation_bilan : équilibrage, réactif limitant
    """
    t = texte.lower()
    nums = [float(n) for n in re.findall(r'(\d+\.?\d*)', texte)]
    params = {'type_probleme': 'inconnu', 'numeros': nums}

    # ── Détection du type ──
    if any(m in t for m in ['ph', 'acide', 'base', 'neutre', 'h3o', 'h+',
                              'acide fort', 'acide faible', 'neutralisation']):
        params['type_probleme'] = 'ph'

    elif any(m in t for m in ['gaz', 'pression', 'pv=nrt', 'volume_molaire',
                                'gaz_parfait', 'atm', 'loi des gaz']):
        params['type_probleme'] = 'gaz_parfaits'

    elif any(m in t for m in ['masse_molaire', 'masse molaire', 'formule',
                                'g/mol', 'poids moleculaire']):
        params['type_probleme'] = 'masse_molaire'
        _extraire_formule(texte, params)

    elif any(m in t for m in ['mole', 'moles', 'nombre_moles', 'avogadro',
                                'quantite', 'n=']):
        params['type_probleme'] = 'stoechiometrie'
        _extraire_stoechio(texte, params)

    elif any(m in t for m in ['concentration', 'molarite', 'mol/l',
                                'dilution', 'c1v1', 'c2v2']):
        params['type_probleme'] = 'concentration'
        _extraire_concentration(texte, params)

    elif any(m in t for m in ['reaction', 'equation', 'reactif', 'produit',
                                'limitant', 'bilan', 'coefficient']):
        params['type_probleme'] = 'equation_bilan'

    # Fallback : si "masse" et "g" ou "kg" et une formule → masse_molaire
    if params['type_probleme'] == 'inconnu':
        formules = re.findall(r'\b([A-Z][a-z]?\d*){2,}\b', texte)
        if formules:
            params['type_probleme'] = 'masse_molaire'
            params['formule'] = formules[0]

    return params


def _extraire_formule(texte, params):
    """Extrait la formule chimique du texte."""
    # Chercher une formule comme H2O, NaCl, H2SO4
    m = re.search(r'\b([A-Z][a-z]?\d*(?:[A-Z][a-z]?\d*)+)\b', texte)
    if m:
        params['formule'] = m.group(1)
    # Chercher dans les molécules connues
    for mol in MOLECULES_MASSES:
        if mol.lower() in texte.lower():
            params['formule'] = mol
            break


def _extraire_stoechio(texte, params):
    """Extrait paramètres stoechiométriques."""
    t = texte.lower()
    # Masse
    m_m = re.search(r'(\d+\.?\d*)\s*(g|kg|mg)', texte)
    if m_m:
        val = float(m_m.group(1))
        if m_m.group(2) == 'kg': val *= 1000
        elif m_m.group(2) == 'mg': val /= 1000
        params['masse'] = val
        params['masse_unite'] = 'g'

    # Nombre de moles
    m_n = re.search(r'(\d+\.?\d*)\s*(mol|moles?)', texte)
    if m_n: params['n'] = float(m_n.group(1))

    # Volume (gaz)
    m_v = re.search(r'(\d+\.?\d*)\s*(l|litres?|ml)', texte)
    if m_v:
        val = float(m_v.group(1))
        if m_v.group(2).startswith('ml'): val /= 1000
        params['volume'] = val

    # Formule
    _extraire_formule(texte, params)


def _extraire_concentration(texte, params):
    """Extrait paramètres de concentration/dilution."""
    t = texte.lower()

    # Concentrations C1, C2
    for label in ['c1', 'c2', 'ci', 'cf', 'concentration']:
        m = re.search(rf'{label}\s*[=:]\s*(\d+\.?\d*)', t)
        if m: params[label] = float(m.group(1))

    # Volumes V1, V2
    for label in ['v1', 'v2', 'vi', 'vf', 'volume']:
        m = re.search(rf'{label}\s*[=:]\s*(\d+\.?\d*)', t)
        if m: params[label] = float(m.group(1))

    # Autres patterns
    m_c = re.search(r'(\d+\.?\d*)\s*(mol/l|mol\.l|m|M)\b', t)
    if m_c and 'c1' not in params: params['c1'] = float(m_c.group(1))

    m_v = re.search(r'(\d+\.?\d*)\s*(ml|l|litres?)', t)
    if m_v:
        val = float(m_v.group(1))
        if m_v.group(2).startswith('ml'): val /= 1000
        if 'v1' not in params: params['v1'] = val


# ═══════════════════════════════════════════════════════════════
# SOLVEUR CHIMIE
# ═══════════════════════════════════════════════════════════════

def resoudre_chimie(params: Dict) -> Dict:
    """Résout un problème de chimie."""
    ptype = params.get('type_probleme', 'inconnu')
    resultat = {'domaine': 'chimie', 'type_probleme': ptype}

    if ptype == 'masse_molaire':
        return _resoudre_masse_molaire(params)
    elif ptype == 'stoechiometrie':
        return _resoudre_stoechiometrie(params)
    elif ptype == 'ph':
        return _resoudre_ph(params)
    elif ptype == 'gaz_parfaits':
        return _resoudre_gaz_parfaits(params)
    elif ptype == 'concentration':
        return _resoudre_concentration(params)
    elif ptype == 'equation_bilan':
        return _resoudre_equation_bilan(params)
    else:
        resultat['erreur'] = f'Type de problème non reconnu: {ptype}'
        return resultat


# ── Masse molaire ──

def _resoudre_masse_molaire(params):
    formule = params.get('formule', '')
    if not formule:
        return {'type_probleme': 'masse_molaire',
                'erreur': 'Aucune formule chimique identifiée'}

    M = masse_molaire_formule(formule)
    if M is None:
        return {'type_probleme': 'masse_molaire',
                'erreur': f'Formule non reconnue ou élément inconnu: {formule}'}

    return {
        'type_probleme': 'masse_molaire',
        'formule': formule,
        'masse_molaire': M,
        'unite': 'g/mol',
        'formule_calcul': f'M({formule}) = {M:.3f} g/mol',
    }


# ── Stoechiométrie ──

def _resoudre_stoechiometrie(params):
    formule = params.get('formule', '')
    masse = params.get('masse')
    n = params.get('n')
    volume = params.get('volume')
    resultat = {'type_probleme': 'stoechiometrie'}

    # Masse molaire
    M = None
    if formule:
        M = masse_molaire_formule(formule)
        if M:
            resultat['formule'] = formule
            resultat['masse_molaire'] = M
            resultat['masse_molaire_unite'] = 'g/mol'

    # n = m / M
    if masse is not None and M is not None and n is None:
        n = masse / M
        resultat['n'] = round(n, 4)
        resultat['n_unite'] = 'mol'
        resultat['formule_calcul'] = f'n = m/M = {masse}/{M} = {n:.4f} mol'

    # m = n × M
    elif n is not None and M is not None and masse is None:
        masse = n * M
        resultat['masse'] = round(masse, 3)
        resultat['masse_unite'] = 'g'
        resultat['formule_calcul'] = f'm = n×M = {n}×{M} = {masse:.3f} g'

    # Nombre de molécules N = n × NA
    if n is not None:
        NA = 6.022e23
        N = n * NA
        resultat['N_molecules'] = f'{N:.3e}'
        resultat['NA'] = '6.022×10²³ mol⁻¹'

    # Volume molaire (gaz à CNTP : Vm = 22.4 L/mol)
    if n is not None and volume is None and formule in ('O2','N2','H2','CO2','CH4','NH3','Cl2'):
        Vm = n * 22.4
        resultat['volume_gaz_cntp'] = round(Vm, 3)
        resultat['volume_gaz_unite'] = 'L (CNTP : 22.4 L/mol)'
    elif volume is not None and n is None and formule in ('O2','N2','H2','CO2','CH4','NH3','Cl2'):
        n = volume / 22.4
        resultat['n'] = round(n, 4)
        resultat['n_unite'] = 'mol'
        resultat['formule_calcul'] = f'n = V/Vm = {volume}/22.4 = {n:.4f} mol'

    return resultat


# ── pH ──

def _resoudre_ph(params):
    resultat = {'type_probleme': 'ph'}
    nums = params.get('numeros', [])

    # Si [H⁺] est donnée
    if len(nums) >= 1 and nums[0] < 1 and nums[0] > 1e-14:
        concentration_h = nums[0]
        ph = -math.log10(concentration_h)
        resultat['concentration_h'] = concentration_h
        resultat['concentration_h_unite'] = 'mol/L'
        resultat['ph'] = round(ph, 2)
        resultat['formule_calcul'] = f'pH = -log([H+]) = -log({concentration_h}) = {ph:.2f}'

        # Nature acide/base/neutre
        if ph < 7:
            nature = 'Acide' + (' fort' if ph < 2 else ' faible')
        elif ph > 7:
            nature = 'Basique' + (' fort' if ph > 12 else ' faible')
        else:
            nature = 'Neutre'
        resultat['nature'] = nature

        # [OH⁻] = 10⁻¹⁴ / [H⁺]
        oh = 1e-14 / concentration_h
        resultat['concentration_oh'] = f'{oh:.2e}'
        resultat['concentration_oh_unite'] = 'mol/L'

    # Si pH est donné
    elif len(nums) >= 1 and 0 <= nums[0] <= 14:
        ph = nums[0]
        h_concentration = 10**(-ph)
        resultat['ph'] = ph
        resultat['concentration_h'] = f'{h_concentration:.2e}'
        resultat['concentration_h_unite'] = 'mol/L'
        oh = 1e-14 / h_concentration
        resultat['concentration_oh'] = f'{oh:.2e}'
        resultat['concentration_oh_unite'] = 'mol/L'

        if ph < 7: resultat['nature'] = 'Acide'
        elif ph > 7: resultat['nature'] = 'Basique'
        else: resultat['nature'] = 'Neutre'

    return resultat


# ── Gaz parfaits ──

def _resoudre_gaz_parfaits(params):
    resultat = {'type_probleme': 'gaz_parfaits'}
    R = 0.08206  # L·atm/(mol·K)
    R_si = 8.314  # J/(mol·K)
    nums = params.get('numeros', [])

    # PV = nRT — essayer d'extraire P, V, n, T
    t = str(params).lower()

    # Pression
    p = None
    m_p_atm = re.search(r'(\d+\.?\d*)\s*atm', t)
    m_p_pa = re.search(r'(\d+\.?\d*)\s*(pa|kpa)', t)
    if m_p_atm: p = float(m_p_atm.group(1))
    elif m_p_pa:
        p = float(m_p_pa.group(1))
        if m_p_pa.group(2) == 'kpa': p *= 1000
        p = p / 101325  # Pa → atm

    # Volume
    v = None
    m_v = re.search(r'(\d+\.?\d*)\s*(l|litres?|ml|m3)', t)
    if m_v:
        v = float(m_v.group(1))
        if m_v.group(2) == 'ml': v /= 1000
        elif m_v.group(2) == 'm3': v *= 1000

    # Température
    T = None
    m_T_k = re.search(r'(\d+\.?\d*)\s*K', t)
    m_T_c = re.search(r'(\d+\.?\d*)\s*°C', t)
    if m_T_k: T = float(m_T_k.group(1))
    elif m_T_c: T = float(m_T_c.group(1)) + 273.15

    # n
    n = params.get('n') or (nums[0] if nums else None)

    resultat['R'] = f'{R} L·atm/(mol·K)'
    resultat['conditions'] = {}

    # Résoudre pour l'inconnue
    if p is not None and v is not None and n is not None and T is None:
        T = (p * v) / (n * R)
        resultat['T'] = round(T, 2)
        resultat['T_unite'] = 'K'
        resultat['T_celsius'] = round(T - 273.15, 1)
        resultat['formule'] = f'T = PV/nR = {p}×{v}/({n}×{R}) = {T:.1f} K'

    elif p is not None and v is not None and T is not None and n is None:
        n = (p * v) / (R * T)
        resultat['n'] = round(n, 4)
        resultat['n_unite'] = 'mol'
        resultat['formule'] = f'n = PV/RT = {p}×{v}/({R}×{T}) = {n:.4f} mol'

    elif p is not None and n is not None and T is not None and v is None:
        v = (n * R * T) / p
        resultat['v'] = round(v, 3)
        resultat['v_unite'] = 'L'
        resultat['formule'] = f'V = nRT/P = {n}×{R}×{T}/{p} = {v:.2f} L'

    elif v is not None and n is not None and T is not None and p is None:
        p = (n * R * T) / v
        resultat['p'] = round(p, 4)
        resultat['p_unite'] = 'atm'
        resultat['formule'] = f'P = nRT/V = {n}×{R}×{T}/{v} = {p:.4f} atm'

    else:
        resultat['info'] = 'Loi des gaz parfaits : PV = nRT'
        resultat['constante_R'] = '0.08206 L·atm/(mol·K)'
        if p: resultat['p'] = p; resultat['p_unite'] = 'atm'
        if v: resultat['v'] = v; resultat['v_unite'] = 'L'
        if n: resultat['n'] = n; resultat['n_unite'] = 'mol'
        if T: resultat['T'] = T; resultat['T_unite'] = 'K'

    return resultat


# ── Concentration / Dilution ──

def _resoudre_concentration(params):
    resultat = {'type_probleme': 'concentration'}
    c1 = params.get('c1')
    v1 = params.get('v1')
    c2 = params.get('c2')
    v2 = params.get('v2')

    # C₁V₁ = C₂V₂
    if c1 is not None and v1 is not None and c2 is not None and v2 is None:
        v2 = (c1 * v1) / c2
        resultat['v2'] = round(v2, 3)
        resultat['v2_unite'] = 'L'
        resultat['formule'] = f'V₂ = C₁V₁/C₂ = {c1}×{v1}/{c2} = {v2:.3f} L'
    elif c1 is not None and v1 is not None and v2 is not None and c2 is None:
        c2 = (c1 * v1) / v2
        resultat['c2'] = round(c2, 4)
        resultat['c2_unite'] = 'mol/L'
        resultat['formule'] = f'C₂ = C₁V₁/V₂ = {c1}×{v1}/{v2} = {c2:.4f} mol/L'

    # Concentration: C = n/V
    n = params.get('n')
    v = params.get('volume') or v1
    if n is not None and v is not None and v > 0:
        c = n / v
        resultat['c'] = round(c, 4)
        resultat['c_unite'] = 'mol/L'
        resultat['formule'] = f'C = n/V = {n}/{v} = {c:.4f} mol/L'

    if len(resultat) <= 1:
        resultat['info'] = 'Dilution : C₁V₁ = C₂V₂  |  Concentration : C = n/V'

    return resultat


# ── Équation bilan (réactif limitant) ──

def _resoudre_equation_bilan(params):
    return {
        'type_probleme': 'equation_bilan',
        'info': 'Équilibrage et réactif limitant — module en développement',
        'exemples': [
            '2H₂ + O₂ → 2H₂O',
            'NaOH + HCl → NaCl + H₂O',
            'CaCO₃ → CaO + CO₂',
        ],
    }


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

EXEMPLES_CHIMIE = [
    "Masse molaire de H2SO4 ?",
    "Combien de moles dans 36 g de H2O ?",
    "pH d'une solution acide a [H+] = 0.001 mol/L",
    "Quel est le pH d'une solution basique a 0.0001 mol/L ?",
    "Quel volume occupe 2 moles de CO2 a 25°C et 1 atm ?",
    "Dilution : C1=0.5 mol/L V1=100 ml, C2=0.1 mol/L. Trouver V2.",
    "Quelle est la masse de 0.5 moles de NaCl ?",
    "Calculer la concentration : 0.1 mol dans 250 ml",
]


def test_chimie():
    print(f"\n{'='*75}")
    print(f"  SOLVEUR CHIMIE — Test extracteur + solveur")
    print(f"{'='*75}\n")
    for i, texte in enumerate(EXEMPLES_CHIMIE):
        params = extraire_chimie(texte)
        resultat = resoudre_chimie(params)
        ptype = params.get('type_probleme', '?')
        print(f"  [{i+1}] {texte[:60]:<60s}")
        print(f"      Type: {ptype:<18s}")

        if 'masse_molaire' in resultat and 'formule' in resultat:
            print(f"      M({resultat['formule']}) = {resultat['masse_molaire']} g/mol")
        if 'n' in resultat:
            print(f"      n = {resultat['n']} {resultat.get('n_unite', 'mol')}")
        if 'masse' in resultat:
            print(f"      m = {resultat['masse']} {resultat.get('masse_unite', 'g')}")
        if 'ph' in resultat:
            print(f"      pH = {resultat['ph']} ({resultat.get('nature', '')})")
        if 'v2' in resultat:
            print(f"      V₂ = {resultat['v2']} {resultat.get('v2_unite', 'L')}")
        if 'v' in resultat:
            print(f"      V = {resultat['v']} {resultat.get('v_unite', 'L')}")
        if 'T' in resultat:
            print(f"      T = {resultat['T']} K ({resultat.get('T_celsius', '')} °C)")
        if 'c' in resultat and 'c_unite' in resultat:
            print(f"      C = {resultat['c']} {resultat['c_unite']}")
        if 'formule_calcul' in resultat:
            print(f"      {resultat['formule_calcul']}")
        if 'formule' in resultat and not isinstance(resultat.get('formule'), dict):
            print(f"      {resultat['formule']}")
        if 'info' in resultat:
            print(f"      {resultat['info']}")
        if 'erreur' in resultat:
            print(f"      [ERREUR] {resultat['erreur']}")
        print()


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Solveur Chimie Harmonique')
    p.add_argument('--test', '-t', action='store_true', help='Lancer les tests')
    p.add_argument('--probleme', '-p', type=str, default=None, help='Résoudre un problème')
    args = p.parse_args()

    if args.probleme:
        params = extraire_chimie(args.probleme)
        resultat = resoudre_chimie(params)
        import json
        print(json.dumps(resultat, ensure_ascii=False, indent=2, default=str))
    else:
        test_chimie()