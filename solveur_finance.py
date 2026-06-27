#!/usr/bin/env python3
"""
SOLVEUR FINANCE — Extension harmonique au domaine financier
===========================================================
Module pluggable pour le système harmonique universel.

Domaines couverts :
  - Intérêts composés (valeur future, valeur actuelle, taux, durée)
  - Emprunts / Crédits (mensualité, capital restant dû, tableau amortissement)
  - Investissement (VAN/NPV, TRI/IRR approché, ROI, rendement)
  - Épargne (versements périodiques, capital constitué)
  - Rentabilité (marge, taux de marque, seuil rentabilité)
  - Fiscalité (TVA, impôt proportionnel, prélèvement forfaitaire)
  - Conversion de devises (EUR/USD/GBP/CHF/JPY)
  - Inflation (valeur réelle, taux réel)

Usage :
  python solveur_finance.py                       # démo
  python solveur_finance.py -p "interets composes 10000 euros a 5% sur 10 ans"
"""

import re
import math
from typing import Dict, List, Tuple, Optional

# ═══════════════════════════════════════════════════════════════
# VOCABULAIRE FINANCE (~170 tokens)
# ═══════════════════════════════════════════════════════════════

VOCAB_FINANCE = [
    # Concepts fondamentaux
    'interet', 'interets', 'taux', 'capital', 'duree', 'annee', 'ans',
    'mois', 'trimestre', 'semestre', 'echeance', 'terme',
    'valeur_future', 'valeur_actuelle', 'actualisation', 'capitalisation',
    'interets_composes', 'interets_simples', 'placement', 'epargne',
    # Emprunt / Crédit
    'emprunt', 'credit', 'pret', 'mensualite', 'annuite', 'remboursement',
    'amortissement', 'capital_restant', 'echeancier', 'taeg', 'teg',
    'assurance', 'frais_dossier', 'apport', 'taux_endettement',
    # Investissement
    'investissement', 'van', 'npv', 'tri', 'irr', 'roi', 'rendement',
    'dividende', 'plus_value', 'moins_value', 'flux', 'cash_flow',
    'actualisation', 'valeur_nette', 'payback', 'rentabilite',
    # Épargne
    'versement', 'depot', 'virement', 'epargne', 'capital_constitue',
    'plan_epargne', 'assurance_vie', 'pea', 'livret', 'compte',
    # Fiscalité
    'tva', 'taxe', 'impot', 'prelevement', 'forfaitaire', 'liberatoire',
    'tranche', 'bareme', 'abattement', 'deduction', 'credit_impot',
    'prelevement_source',
    # Rentabilité commerciale
    'marge', 'taux_marque', 'prix_achat', 'prix_vente', 'chiffre_affaires',
    'benefice', 'perte', 'seuil_rentabilite', 'point_mort',
    'cout_fixe', 'cout_variable', 'resultat', 'ebitda',
    # Devises
    'eur', 'usd', 'gbp', 'chf', 'jpy', 'cny', 'change', 'conversion',
    'taux_change', 'devise', 'forex',
    # Inflation
    'inflation', 'valeur_reelle', 'taux_reel', 'pouvoir_achat',
    'indexation', 'deflateur',
    # Unités et symboles
    '%', '€', '$', '£', 'k€', 'M€', 'euro', 'euros', 'dollar', 'dollars',
    # Nombres utiles
    '0','1','2','3','4','5','6','7','8','9','10',
    '12','15','20','25','30','50','100','1000',
    '10000','50000','100000','200000','500000','1000000',
    '+','-','*','/','=','^','(',')','.',',',
]

# ═══════════════════════════════════════════════════════════════
# TAUX DE CHANGE (valeurs indicatives fixes)
# ═══════════════════════════════════════════════════════════════

TAUX_CHANGE = {
    'EUR': 1.0,
    'USD': 1.08,    # 1 EUR = 1.08 USD
    'GBP': 0.85,    # 1 EUR = 0.85 GBP
    'CHF': 0.95,    # 1 EUR = 0.95 CHF
    'JPY': 158.0,   # 1 EUR = 158 JPY
    'CNY': 7.80,    # 1 EUR = 7.80 CNY
}

TAUX_TVA = 20.0  # TVA standard France (%)


# ═══════════════════════════════════════════════════════════════
# EXTRACTEUR FINANCE
# ═══════════════════════════════════════════════════════════════

def extraire_finance(texte: str) -> Dict:
    """
    Extrait les paramètres d'un problème financier.

    Types supportés :
    - interets_composes : FV = PV × (1+r)^n
    - emprunt : PMT = P × r(1+r)^n / ((1+r)^n - 1)
    - epargne : FV = PMT × ((1+r)^n - 1) / r
    - investissement : VAN, ROI, TRI approché
    - rentabilite : marge, taux de marque, seuil rentabilité
    - tva : HT → TTC, TTC → HT
    - change : conversion devise
    - inflation : valeur réelle, taux réel
    """
    t = texte.lower()
    nums = [float(n) for n in re.findall(r'(\d+\.?\d*)', texte)]
    params = {'type_probleme': 'inconnu', 'numeros': nums}

    # ── Détection du type ──
    if any(m in t for m in ['emprunt', 'credit', 'pret', 'mensualite',
                              'annuite', 'remboursement', 'amortissement']):
        params['type_probleme'] = 'emprunt'
        _extraire_emprunt(texte, params)

    elif any(m in t for m in ['interets_composes', 'interets composes',
                                'valeur future', 'valeur acquise',
                                'capitalisation', 'placement']):
        params['type_probleme'] = 'interets_composes'
        _extraire_interets(texte, params)

    elif any(m in t for m in ['epargne', 'versement', 'capital_constitue',
                                'plan epargne', 'depot', 'virement periodique']):
        params['type_probleme'] = 'epargne'
        _extraire_interets(texte, params)

    elif any(m in t for m in ['van', 'npv', 'tri', 'irr', 'roi', 'rendement',
                                'investissement', 'payback', 'cash_flow']):
        params['type_probleme'] = 'investissement'
        _extraire_investissement(texte, params)

    elif any(m in t for m in ['marge', 'taux_marque', 'prix_achat', 'prix_vente',
                                'benefice', 'seuil', 'rentabilite']):
        params['type_probleme'] = 'rentabilite'
        _extraire_rentabilite(texte, params)

    elif any(m in t for m in ['tva', 'ht', 'ttc', 'hors_taxe', 'taxe']):
        params['type_probleme'] = 'tva'
        _extraire_tva(texte, params)

    elif any(m in t for m in ['change', 'conversion', 'devise', 'eur', 'usd',
                                'gbp', 'chf', 'jpy', 'dollar', 'euro']):
        params['type_probleme'] = 'change'
        _extraire_change(texte, params)

    elif any(m in t for m in ['inflation', 'valeur_reelle', 'taux_reel',
                                'pouvoir_achat']):
        params['type_probleme'] = 'inflation'
        _extraire_inflation(texte, params)

    # Fallback : si taux + durée → intérêts composés
    if params['type_probleme'] == 'inconnu' and ('%' in t or 'taux' in t):
        params['type_probleme'] = 'interets_composes'
        _extraire_interets(texte, params)

    return params


def _extraire_montant(texte, params, cle='capital'):
    """Extrait un montant monétaire (€, k€, M€, $)."""
    # Format : 10000 €, 10 k€, 1.5 M€, 5000 euros
    m = re.search(r'(\d+[\s.]?\d*)\s*(k€|M€|€|euros?|dollars?|\$)', texte)
    if m:
        val = float(m.group(1).replace(' ', '').replace(',', '.'))
        unite = m.group(2)
        if 'k€' in unite: val *= 1000
        elif 'M€' in unite: val *= 1000000
        params[cle] = val
    elif params.get('numeros') and len(params['numeros']) >= 1:
        # Prendre le premier nombre comme montant
        params[cle] = params['numeros'][0]


def _extraire_taux(texte, params, cle='taux'):
    """Extrait un taux en pourcentage."""
    m = re.search(r'(\d+[.,]?\d*)\s*%', texte)
    if m:
        taux = float(m.group(1).replace(',', '.'))
        params[cle] = taux / 100.0  # Convertir en décimal
    elif params.get('numeros') and len(params['numeros']) >= 2:
        # 2ème nombre comme taux
        params[cle] = params['numeros'][1] / 100.0


def _extraire_duree(texte, params, cle='duree'):
    """Extrait une durée en années."""
    m_annees = re.search(r'(\d+)\s*(ans?|années?|annee)', texte)
    m_mois = re.search(r'(\d+)\s*(mois|mensualites?)', texte)
    m_jours = re.search(r'(\d+)\s*(jours?)', texte)
    if m_annees:
        params[cle] = int(m_annees.group(1))
        params['duree_unite'] = 'années'
    elif m_mois:
        params[cle] = int(m_mois.group(1)) / 12.0
        params['duree_unite'] = 'années (converti de mois)'
    elif m_jours:
        params[cle] = int(m_jours.group(1)) / 365.0
        params['duree_unite'] = 'années (converti de jours)'


def _extraire_interets(texte, params):
    """Extrait paramètres intérêts composés."""
    _extraire_montant(texte, params, 'capital')
    _extraire_taux(texte, params, 'taux')
    _extraire_duree(texte, params, 'duree')

    # Versement périodique
    m_v = re.search(r'versement\s*(de\s*)?(\d+[\s.]?\d*)\s*(€|euros?)', texte)
    if m_v:
        params['versement'] = float(m_v.group(2).replace(' ', ''))

    # Fréquence des versements
    if 'mensuel' in texte.lower():
        params['frequence'] = 'mensuelle'
        params['periodes_par_an'] = 12
    elif 'trimestriel' in texte.lower():
        params['frequence'] = 'trimestrielle'
        params['periodes_par_an'] = 4
    elif 'semestriel' in texte.lower():
        params['frequence'] = 'semestrielle'
        params['periodes_par_an'] = 2
    else:
        params['frequence'] = 'annuelle'
        params['periodes_par_an'] = 1


def _extraire_emprunt(texte, params):
    """Extrait paramètres emprunt."""
    _extraire_montant(texte, params, 'capital')
    _extraire_taux(texte, params, 'taux')
    _extraire_duree(texte, params, 'duree')
    params['frequence'] = 'mensuelle'
    params['periodes_par_an'] = 12


def _extraire_investissement(texte, params):
    """Extrait paramètres investissement."""
    _extraire_montant(texte, params, 'capital')
    _extraire_taux(texte, params, 'taux')

    # Flux de trésorerie
    flux = re.findall(r'flux\s*[=:]\s*(\d+[\s.]?\d*)', texte.lower())
    if flux:
        params['flux'] = [float(f.replace(' ', '')) for f in flux]
    elif params.get('numeros') and len(params['numeros']) >= 3:
        params['flux'] = params['numeros'][1:4]


def _extraire_rentabilite(texte, params):
    """Extrait paramètres rentabilité commerciale."""
    m_pa = re.search(r'prix_achat\s*[=:]\s*(\d+[\s.]?\d*)', texte.lower())
    m_pv = re.search(r'prix_vente\s*[=:]\s*(\d+[\s.]?\d*)', texte.lower())
    m_ca = re.search(r'chiffre_affaires\s*[=:]\s*(\d+[\s.]?\d*)', texte.lower())
    m_cf = re.search(r'cout_fixe\s*[=:]\s*(\d+[\s.]?\d*)', texte.lower())
    m_cv = re.search(r'cout_variable\s*[=:]\s*(\d+[\s.]?\d*)', texte.lower())

    if m_pa: params['prix_achat'] = float(m_pa.group(1).replace(' ', ''))
    if m_pv: params['prix_vente'] = float(m_pv.group(1).replace(' ', ''))
    if m_ca: params['chiffre_affaires'] = float(m_ca.group(1).replace(' ', ''))
    if m_cf: params['cout_fixe'] = float(m_cf.group(1).replace(' ', ''))
    if m_cv: params['cout_variable'] = float(m_cv.group(1).replace(' ', ''))


def _extraire_tva(texte, params):
    """Extrait paramètres TVA."""
    _extraire_montant(texte, params, 'montant')
    # HT ou TTC ?
    if 'ht' in texte.lower() or 'hors_taxe' in texte.lower():
        params['mode'] = 'HT'
    elif 'ttc' in texte.lower() or 'toute_taxe' in texte.lower():
        params['mode'] = 'TTC'
    else:
        params['mode'] = 'HT'  # défaut


def _extraire_change(texte, params):
    """Extrait paramètres conversion devise."""
    _extraire_montant(texte, params, 'montant')

    # Devise source et cible
    for devise in ['eur', 'usd', 'gbp', 'chf', 'jpy', 'cny']:
        if devise in texte.lower():
            if 'source' not in params:
                params['source'] = devise.upper()
            else:
                params['cible'] = devise.upper()
                break

    if 'source' not in params: params['source'] = 'EUR'
    if 'cible' not in params: params['cible'] = 'USD'


def _extraire_inflation(texte, params):
    """Extrait paramètres inflation."""
    _extraire_montant(texte, params, 'capital')
    _extraire_taux(texte, params, 'taux')  # taux nominal
    _extraire_duree(texte, params, 'duree')

    m_inf = re.search(r'inflation\s*[=:]\s*(\d+[.,]?\d*)\s*%', texte.lower())
    if m_inf:
        params['inflation'] = float(m_inf.group(1).replace(',', '.')) / 100.0


# ═══════════════════════════════════════════════════════════════
# SOLVEUR FINANCE
# ═══════════════════════════════════════════════════════════════

def resoudre_finance(params: Dict) -> Dict:
    """Résout un problème financier."""
    ptype = params.get('type_probleme', 'inconnu')
    resultat = {'domaine': 'finance', 'type_probleme': ptype}

    if ptype == 'interets_composes':
        return _resoudre_interets_composes(params)
    elif ptype == 'emprunt':
        return _resoudre_emprunt(params)
    elif ptype == 'epargne':
        return _resoudre_epargne(params)
    elif ptype == 'investissement':
        return _resoudre_investissement(params)
    elif ptype == 'rentabilite':
        return _resoudre_rentabilite(params)
    elif ptype == 'tva':
        return _resoudre_tva(params)
    elif ptype == 'change':
        return _resoudre_change(params)
    elif ptype == 'inflation':
        return _resoudre_inflation(params)
    else:
        resultat['erreur'] = f'Type de problème non reconnu: {ptype}'
        return resultat


# ── Intérêts composés ──

def _resoudre_interets_composes(params):
    """
    FV = PV × (1 + r)^n
    Capital acquis après n périodes au taux r.
    """
    PV = params.get('capital')
    r = params.get('taux')
    n = params.get('duree')
    resultat = {'type_probleme': 'interets_composes'}

    if PV is not None and r is not None and n is not None:
        FV = PV * (1 + r) ** n
        interets = FV - PV
        resultat['capital_initial'] = round(PV, 2)
        resultat['valeur_future'] = round(FV, 2)
        resultat['interets'] = round(interets, 2)
        resultat['unite'] = '€'
        resultat['formule'] = f'FV = {PV} × (1 + {r*100:.1f}%)^{n} = {FV:,.2f} €'
        resultat['gain_texte'] = f'Gain total : {interets:,.2f} € (+{interets/PV*100:.1f}%)'

        # Tableau d'évolution
        evolution = []
        for an in range(int(n) + 1):
            val = PV * (1 + r) ** an
            evolution.append({'annee': an, 'valeur': round(val, 2)})
        resultat['evolution'] = evolution[:6]  # 6 premières années max

    else:
        resultat['info'] = 'Formule intérêts composés : FV = PV × (1 + r)^n'
        if PV: resultat['capital_initial'] = PV
        if r: resultat['taux'] = f'{r*100:.2f}%'
        if n: resultat['duree'] = f'{n} ans'

    return resultat


# ── Emprunt (crédit amortissable) ──

def _resoudre_emprunt(params):
    """
    Mensualité = P × r_m × (1+r_m)^n / ((1+r_m)^n - 1)
    où r_m = taux annuel / 12, n = durée en mois
    """
    P = params.get('capital')
    r_annuel = params.get('taux')
    n_annees = params.get('duree')
    resultat = {'type_probleme': 'emprunt'}

    if P is not None and r_annuel is not None and n_annees is not None:
        n_mois = int(n_annees * 12)
        r_mensuel = r_annuel / 12.0

        # Mensualité (formule de l'annuité constante)
        if r_mensuel > 0:
            mensualite = P * r_mensuel * (1 + r_mensuel) ** n_mois / \
                         ((1 + r_mensuel) ** n_mois - 1)
        else:
            mensualite = P / n_mois

        cout_total = mensualite * n_mois
        interets_total = cout_total - P

        resultat['capital_emprunte'] = round(P, 2)
        resultat['taux_annuel'] = f'{r_annuel*100:.2f}%'
        resultat['duree'] = f'{n_annees} ans ({n_mois} mois)'
        resultat['mensualite'] = round(mensualite, 2)
        resultat['cout_total'] = round(cout_total, 2)
        resultat['interets_total'] = round(interets_total, 2)
        resultat['unite'] = '€'
        resultat['formule'] = (
            f'Mensualité = {P:,.0f} × {r_mensuel:.6f} × (1+{r_mensuel:.6f})^{n_mois} / '
            f'((1+{r_mensuel:.6f})^{n_mois} - 1) = {mensualite:,.2f} €/mois'
        )
        resultat['ratio_endettement'] = (
            f'Coût total = {cout_total:,.0f} € '
            f'(dont {interets_total:,.0f} € d\'intérêts, '
            f'soit {interets_total/P*100:.1f}% du capital)'
        )

    else:
        resultat['info'] = 'Formule emprunt : M = P × r(1+r)^n / ((1+r)^n - 1)'
        if P: resultat['capital'] = round(P, 2)
        if r_annuel: resultat['taux'] = f'{r_annuel*100:.2f}%'

    return resultat


# ── Épargne (versements périodiques) ──

def _resoudre_epargne(params):
    """
    FV = PMT × ((1+r)^n - 1) / r   (versements de fin de période)
    """
    PMT = params.get('versement')
    r = params.get('taux')
    n = params.get('duree')
    P = params.get('capital')  # capital initial optionnel
    resultat = {'type_probleme': 'epargne'}

    if PMT is not None and r is not None and n is not None:
        if r > 0:
            FV_versements = PMT * ((1 + r) ** n - 1) / r
        else:
            FV_versements = PMT * n

        capital_initial = P or 0
        FV_capital = capital_initial * (1 + r) ** n if capital_initial > 0 else 0
        FV_total = FV_versements + FV_capital
        total_verse = PMT * n + capital_initial
        gain = FV_total - total_verse

        resultat['versement'] = round(PMT, 2)
        resultat['capital_initial'] = round(capital_initial, 2)
        resultat['duree'] = f'{n} ans'
        resultat['capital_final'] = round(FV_total, 2)
        resultat['total_verse'] = round(total_verse, 2)
        resultat['gain'] = round(gain, 2)
        resultat['unite'] = '€'
        resultat['formule'] = (
            f'FV = {PMT:,.0f} × ((1+{r*100:.1f}%)^{n} - 1) / {r:.4f} = {FV_total:,.0f} €'
        )
        resultat['resume'] = (
            f'Total verse : {total_verse:,.0f} EUR -> Capital final : {FV_total:,.0f} EUR '
            f'(Gain : {gain:,.0f} EUR, +{gain/total_verse*100:.1f}%)'
        )

    else:
        resultat['info'] = 'Formule épargne : FV = PMT × ((1+r)^n - 1) / r'
        if PMT: resultat['versement'] = round(PMT, 2)

    return resultat


# ── Investissement ──

def _resoudre_investissement(params):
    resultat = {'type_probleme': 'investissement'}
    P = params.get('capital')
    r = params.get('taux', 0.10)  # taux d'actualisation par défaut : 10%
    flux = params.get('flux', [])

    # ROI simple
    if P is not None and P > 0:
        if flux and len(flux) >= 1:
            gain = sum(flux)
            roi = (gain - P) / P * 100
            resultat['capital_investi'] = round(P, 2)
            resultat['gain_total'] = round(gain, 2)
            resultat['roi'] = f'{roi:.1f}%'
            if roi > 0:
                resultat['interpretation'] = 'Investissement rentable'
            else:
                resultat['interpretation'] = 'Investissement non rentable'

    # VAN (Net Present Value) avec taux d'actualisation
    if flux and len(flux) >= 1:
        van = -P if P else 0
        details_van = []
        for i, f in enumerate(flux):
            f_actualise = f / (1 + r) ** (i + 1)
            van += f_actualise
            details_van.append({
                'annee': i + 1,
                'flux': f,
                'flux_actualise': round(f_actualise, 2)
            })
        resultat['van'] = round(van, 2)
        resultat['taux_actualisation'] = f'{r*100:.1f}%'
        resultat['details_van'] = details_van[:5]

        if van > 0:
            resultat['decision_van'] = 'VAN > 0 -> Investissement rentable (cree de la valeur)'
        elif van < 0:
            resultat['decision_van'] = 'VAN < 0 -> Investissement NON rentable (detruit de la valeur)'
        else:
            resultat['decision_van'] = 'VAN = 0 -> Point mort (neutre)'

    if len(resultat) <= 1:
        resultat['info'] = 'ROI = (Gain - Investissement) / Investissement × 100'
        resultat['info_van'] = 'VAN = Σ Flux_n / (1+r)^n - Investissement initial'

    return resultat


# ── Rentabilité commerciale ──

def _resoudre_rentabilite(params):
    resultat = {'type_probleme': 'rentabilite'}
    pa = params.get('prix_achat')
    pv = params.get('prix_vente')
    ca = params.get('chiffre_affaires')
    cf = params.get('cout_fixe')
    cv = params.get('cout_variable')

    # Marge commerciale
    if pa is not None and pv is not None:
        marge = pv - pa
        taux_marge = (marge / pa) * 100
        taux_marque = (marge / pv) * 100
        resultat['prix_achat_ht'] = round(pa, 2)
        resultat['prix_vente_ht'] = round(pv, 2)
        resultat['marge_unitaire'] = round(marge, 2)
        resultat['taux_marge'] = f'{taux_marge:.1f}%'
        resultat['taux_marque'] = f'{taux_marque:.1f}%'
        resultat['formule'] = (
            f'Marge = {pv} - {pa} = {marge:.2f} € '
            f'(Taux marge = {taux_marge:.1f}%, Taux marque = {taux_marque:.1f}%)'
        )

    # Seuil de rentabilité
    if cf is not None and cv is not None and pv is not None:
        marge_cv = pv - cv
        if marge_cv > 0:
            seuil_qte = cf / marge_cv
            resultat['cout_fixe'] = round(cf, 2)
            resultat['cout_variable_unitaire'] = round(cv, 2)
            resultat['marge_cv'] = round(marge_cv, 2)
            resultat['seuil_rentabilite_qte'] = round(seuil_qte, 0)
            resultat['seuil_rentabilite_ca'] = round(seuil_qte * pv, 2)
            resultat['formule_seuil'] = (
                f'Seuil = CF / (PV - CV) = {cf} / ({pv} - {cv}) = {seuil_qte:.0f} unités '
                f'(CA : {seuil_qte*pv:,.0f} €)'
            )

    return resultat


# ── TVA ──

def _resoudre_tva(params):
    resultat = {'type_probleme': 'tva'}
    montant = params.get('montant')
    mode = params.get('mode', 'HT')
    taux_tva = TAUX_TVA / 100.0

    if montant is not None:
        if mode == 'HT':
            ttc = montant * (1 + taux_tva)
            tva = montant * taux_tva
            resultat['montant_ht'] = round(montant, 2)
            resultat['tva'] = round(tva, 2)
            resultat['montant_ttc'] = round(ttc, 2)
            resultat['formule'] = f'TTC = {montant} × 1.20 = {ttc:.2f} € (TVA : {tva:.2f} €)'
        else:
            ht = montant / (1 + taux_tva)
            tva = montant - ht
            resultat['montant_ttc'] = round(montant, 2)
            resultat['tva'] = round(tva, 2)
            resultat['montant_ht'] = round(ht, 2)
            resultat['formule'] = f'HT = {montant} / 1.20 = {ht:.2f} € (TVA : {tva:.2f} €)'

        resultat['taux_tva'] = f'{TAUX_TVA:.0f}%'
    else:
        resultat['info'] = f'TVA {TAUX_TVA:.0f}% : TTC = HT × 1.20, HT = TTC / 1.20'

    return resultat


# ── Change / Devises ──

def _resoudre_change(params):
    resultat = {'type_probleme': 'change'}
    montant = params.get('montant')
    source = params.get('source', 'EUR')
    cible = params.get('cible', 'USD')

    if montant is not None and source in TAUX_CHANGE and cible in TAUX_CHANGE:
        # Conversion via EUR comme pivot
        montant_eur = montant / TAUX_CHANGE[source]
        montant_cible = montant_eur * TAUX_CHANGE[cible]
        resultat['montant_source'] = round(montant, 2)
        resultat['devise_source'] = source
        resultat['montant_cible'] = round(montant_cible, 2)
        resultat['devise_cible'] = cible
        resultat['taux'] = round(TAUX_CHANGE[cible] / TAUX_CHANGE[source], 4)
        resultat['formule'] = (
            f'{montant:,.2f} {source} → {montant_cible:,.2f} {cible} '
            f'(taux : 1 {source} = {TAUX_CHANGE[cible]/TAUX_CHANGE[source]:.4f} {cible})'
        )
    else:
        resultat['info'] = 'Taux de change (via EUR) : '
        resultat['taux_disponibles'] = {
            k: v for k, v in TAUX_CHANGE.items()
        }

    return resultat


# ── Inflation ──

def _resoudre_inflation(params):
    resultat = {'type_probleme': 'inflation'}
    PV = params.get('capital')
    r_nominal = params.get('taux')
    n = params.get('duree')
    r_inflation = params.get('inflation', 0.02)  # 2% par défaut

    if PV is not None and r_nominal is not None and n is not None:
        FV_nominale = PV * (1 + r_nominal) ** n
        taux_reel = (1 + r_nominal) / (1 + r_inflation) - 1
        FV_reelle = PV * (1 + taux_reel) ** n

        resultat['capital_initial'] = round(PV, 2)
        resultat['taux_nominal'] = f'{r_nominal*100:.1f}%'
        resultat['taux_inflation'] = f'{r_inflation*100:.1f}%'
        resultat['taux_reel'] = f'{taux_reel*100:.2f}%'
        resultat['valeur_future_nominale'] = round(FV_nominale, 2)
        resultat['valeur_future_reelle'] = round(FV_reelle, 2)
        resultat['perte_pouvoir_achat'] = round(FV_nominale - FV_reelle, 2)
        resultat['formule'] = (
            f'Taux réel = (1+{r_nominal})/(1+{r_inflation}) - 1 = {taux_reel*100:.2f}%\n'
            f'Valeur future nominale = {FV_nominale:,.0f} €\n'
            f'Valeur future réelle (inflation déduite) = {FV_reelle:,.0f} €\n'
            f'Perte pouvoir d\'achat = {FV_nominale - FV_reelle:,.0f} €'
        )
    else:
        resultat['info'] = 'Taux réel = (1 + taux nominal) / (1 + inflation) - 1'
        resultat['info2'] = 'Valeur réelle = Valeur nominale × (1 + taux réel)^n'

    return resultat


# ═══════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════

EXEMPLES_FINANCE = [
    "Interets composes : 10000 euros a 5% sur 10 ans",
    "Emprunt de 200000 euros a 3.5% sur 20 ans, quelle mensualite ?",
    "Epargne : versement de 500 euros par mois a 3% pendant 15 ans",
    "Investissement de 50000 euros, flux : 15000, 20000, 25000. VAN a 10% ?",
    "Marge commerciale : prix achat 80 euros, prix vente 120 euros",
    "TVA : 1000 euros HT, quel est le TTC ?",
    "Conversion : 1000 euros en dollars",
    "Inflation : 10000 euros places a 4% sur 10 ans, inflation 2%",
    "Seuil de rentabilite : cout fixe 50000, cout variable 30, prix vente 80",
]


def test_finance():
    print(f"\n{'='*80}")
    print(f"  SOLVEUR FINANCE — Test extracteur + solveur")
    print(f"{'='*80}\n")
    for i, texte in enumerate(EXEMPLES_FINANCE):
        params = extraire_finance(texte)
        resultat = resoudre_finance(params)
        ptype = params.get('type_probleme', '?')
        print(f"  [{i+1}] {texte[:65]:<65s}")
        print(f"      Type: {ptype:<20s}")

        if 'valeur_future' in resultat:
            print(f"      Valeur future = {resultat['valeur_future']:,.2f} {resultat.get('unite', '€')}")
        if 'mensualite' in resultat:
            print(f"      Mensualité = {resultat['mensualite']:,.2f} €/mois")
            print(f"      {resultat.get('ratio_endettement', '')}")
        if 'capital_final' in resultat:
            print(f"      Capital final = {resultat['capital_final']:,.0f} €")
            if 'resume' in resultat:
                print(f"      {resultat['resume']}")
        if 'van' in resultat:
            print(f"      VAN = {resultat['van']:,.2f} €")
            print(f"      {resultat.get('decision_van', '')}")
        if 'roi' in resultat:
            print(f"      ROI = {resultat['roi']}")
        if 'taux_marge' in resultat:
            print(f"      Marge = {resultat['marge_unitaire']} € (Taux marge : {resultat['taux_marge']}, Taux marque : {resultat['taux_marque']})")
        if 'montant_ttc' in resultat:
            print(f"      HT = {resultat['montant_ht']} EUR -> TTC = {resultat['montant_ttc']} EUR (TVA : {resultat['tva']} EUR)")
        if 'montant_cible' in resultat:
            print(f"      {resultat['montant_source']:,.2f} {resultat['devise_source']} -> {resultat['montant_cible']:,.2f} {resultat['devise_cible']}")
        if 'taux_reel' in resultat:
            print(f"      Taux réel = {resultat['taux_reel']}")
            print(f"      Valeur réelle = {resultat['valeur_future_reelle']:,.0f} € (perte PA : {resultat.get('perte_pouvoir_achat', 0):,.0f} €)")
        if 'seuil_rentabilite_qte' in resultat:
            print(f"      Seuil rentabilité = {resultat['seuil_rentabilite_qte']:.0f} unités (CA : {resultat['seuil_rentabilite_ca']:,.0f} €)")

        if 'gain' in resultat:
            print(f"      Gain = {resultat['gain']:,.2f} €")
        if 'formule' in resultat:
            formule = resultat['formule']
            if isinstance(formule, str) and len(formule) > 100:
                formule = formule[:100] + '...'
            print(f"      {formule}")
        if 'info' in resultat:
            print(f"      {resultat['info']}")
        if 'erreur' in resultat:
            print(f"      [ERREUR] {resultat['erreur']}")
        print()


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Solveur Finance Harmonique')
    p.add_argument('--test', '-t', action='store_true', help='Lancer les tests')
    p.add_argument('--probleme', '-p', type=str, default=None, help='Résoudre un problème')
    args = p.parse_args()

    if args.probleme:
        params = extraire_finance(args.probleme)
        resultat = resoudre_finance(params)
        import json
        print(json.dumps(resultat, ensure_ascii=False, indent=2, default=str))
    else:
        test_finance()