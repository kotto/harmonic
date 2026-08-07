#!/usr/bin/env python3
"""
make_demo_dataset.py — Dataset de démonstration réaliste (cabinet comptable)
============================================================================

Le kit de vente : un cabinet d'expertise comptable avec ses clients, ses
factures, sa paie, son bilan et ses procédures internes — des données
CRÉDIBLES, déterministes (aucun aléa) et prêtes à ingérer.

  - clients.csv      : 12 sociétés clientes (nom, ville, secteur, CA, statut)
  - factures.csv     : 12 factures (référence, client, montant, date, statut)
  - salaries.csv     : 6 collaborateurs du cabinet (nom, poste, salaire)
  - bilan_2025.txt   : extrait du bilan du cabinet
  - procedures.txt   : procédures internes (TVA, clôture, accueil, paie…)
  - notes_marche.txt : évolutions réglementaires 2026

Valeurs attendues (utilisées par run_demo.py et les tests) :
  - 12 clients, dont 10 actifs et 2 en cessation
  - CA total 4 128 000 € ; CA des clients actifs 3 668 000 €
  - 12 factures dont 3 en retard (40 600 €), 2 en attente
"""

from typing import Dict, List

# ── Valeurs attendues (assertions du script de démo) ───────────────────────────
CA_TOTAL = 4128000          # somme des chiffres d'affaires des 12 clients
CA_ACTIFS = 3668000         # somme des CA des 10 clients actifs
FACTURES_RETARD = 3         # factures en retard
MONTANT_RETARD = 40600.0    # total des factures en retard

# ── Données ────────────────────────────────────────────────────────────────────

_CLIENTS = [
    # nom, ville, secteur, ca, statut
    ('SARL Dupont Bâtiment', 'Lyon', 'bâtiment', 450000, 'actif'),
    ('Menuiserie Martin', 'Villeurbanne', 'bois', 210000, 'actif'),
    ('SARL Perrin Transport', 'Grenoble', 'transport', 380000, 'actif'),
    ('Boulangerie Chabrol', 'Lyon', 'commerce', 95000, 'actif'),
    ('Clinique des Cèdres', 'Annecy', 'santé', 1200000, 'actif'),
    ('SARL Morel & Fils', 'Saint-Étienne', 'industrie', 720000, 'actif'),
    ('Cabinet Vétérinaire Ardent', 'Valence', 'santé', 180000, 'actif'),
    ('SARL Roux Paysage', 'Bourg-en-Bresse', 'services', 64000, 'actif'),
    ('Restaurant Le Beaulieu', 'Lyon', 'restauration', 280000, 'actif'),
    ('SARL Garcia Bâtiment', 'Vienne', 'bâtiment', 89000, 'actif'),
    ('SARL Fontaine Électricité', 'Chambéry', 'bâtiment', 310000, 'en cessation'),
    ('Transports Neyrat', 'Oyonnax', 'transport', 150000, 'en cessation'),
]

_FACTURES = [
    # reference, client, montant, date, statut
    ('FAC-2026-001', 'SARL Dupont Bâtiment', '12 500,00', '02/01/2026', 'payee'),
    ('FAC-2026-002', 'Menuiserie Martin', '4 800,50', '15/01/2026', 'payee'),
    ('FAC-2026-003', 'Clinique des Cèdres', '28 500,00', '28/01/2026', 'en retard'),
    ('FAC-2026-004', 'SARL Perrin Transport', '9 200,00', '05/02/2026', 'payee'),
    ('FAC-2026-005', 'Boulangerie Chabrol', '1 850,00', '12/02/2026', 'payee'),
    ('FAC-2026-006', 'SARL Morel & Fils', '15 600,00', '20/02/2026', 'en attente'),
    ('FAC-2026-007', 'Restaurant Le Beaulieu', '4 300,00', '03/03/2026', 'en retard'),
    ('FAC-2026-008', 'SARL Roux Paysage', '1 200,00', '10/03/2026', 'payee'),
    ('FAC-2026-009', 'Cabinet Vétérinaire Ardent', '3 600,00', '18/03/2026', 'payee'),
    ('FAC-2026-010', 'Transports Neyrat', '7 800,00', '25/03/2026', 'en retard'),
    ('FAC-2026-011', 'SARL Fontaine Électricité', '9 800,00', '02/04/2026', 'en attente'),
    ('FAC-2026-012', 'SARL Garcia Bâtiment', '2 650,00', '09/04/2026', 'payee'),
]

_SALARIES = [
    # nom, poste, salaire, service
    ('Marie Lefebvre', 'Expert-comptable', 5200, 'audit'),
    ('Thomas Girard', 'Expert-comptable', 4800, 'social'),
    ('Sarah Benali', 'Collaboratrice comptable', 3100, 'tenue'),
    ('Julien Mercier', 'Collaborateur fiscal', 3400, 'fiscal'),
    ('Nadia Kaci', 'Assistante', 2300, 'accueil'),
    ('Paul Marchand', 'Stagiaire', 1200, 'tenue'),
]

_BILAN = """Bilan 2025 du cabinet :
Total actif : 845 000 euros. Total passif : 845 000 euros.
Résultat net de l'exercice : 142 300 euros.
Fonds de roulement : 210 000 euros. Trésorerie nette : 96 500 euros.
Les honoraires facturés en 2025 s'élèvent à 486 000 euros."""

_PROCEDURES = """Procédures internes du cabinet — TVA : la déclaration de TVA est déposée chaque mois avant le 19 pour les clients au régime réel. Pour les clients au régime simplifié, l'acompte est versé en juillet et en décembre, et la déclaration annuelle est établie en mai.
Clôture annuelle : la clôture se déroule de décembre à avril. Les étapes sont l'inventaire physique, le rapprochement bancaire, le lettrage des comptes, la constitution des provisions pour risques, puis l'établissement du bilan et du compte de résultat.
Accueil d'un nouveau client : le client signe la lettre de mission. Un dossier est ouvert avec ses statuts, ses contrats en cours et ses trois dernières déclarations fiscales.
Paie : la paie est établie chaque mois avant le 25. Les cotisations URSSAF sont déclarées en DSN le 5 du mois suivant. Le prélèvement à la source est reversé le 15.
Conservation des documents : les pièces comptables sont conservées 10 ans et les documents sociaux 5 ans."""

_NOTES_MARCHE = """Notes réglementaires 2026 :
Réforme de la TVA : le seuil de la franchise en base passe à 85 000 euros pour les ventes de marchandises.
Échéance URSSAF : la DSN mensuelle doit être transmise au plus tard le 5 de chaque mois.
Prélèvement à la source : le taux neutre reste appliqué par défaut ; les salariés peuvent moduler leur taux via le site des impôts.
Loi de finances 2026 : crédit d'impôt pour la transition énergétique des PME au taux de 30 %, plafonné à 50 000 euros."""


_HEADERS = {
    'clients.csv': ['nom', 'ville', 'secteur', 'chiffre_affaires', 'statut'],
    'factures.csv': ['reference', 'client', 'montant', 'date', 'statut'],
    'salaries.csv': ['nom', 'poste', 'salaire', 'service'],
}


def _lines_csv(filename: str, rows: List[tuple]) -> str:
    """Lignes au format « clé : valeur | clé : valeur » (mode clefs du moteur)."""
    headers = _HEADERS[filename]
    return '\n'.join(' | '.join(f'{k} : {v}' for k, v in zip(headers, r))
                     for r in rows)


def build_demo_dataset() -> Dict[str, str]:
    """Retourne {nom_fichier: contenu} — le dataset complet et déterministe."""
    return {
        'clients.csv': _lines_csv('clients.csv', _CLIENTS),
        'factures.csv': _lines_csv('factures.csv', _FACTURES),
        'salaries.csv': _lines_csv('salaries.csv', _SALARIES),
        'bilan_2025.txt': _BILAN,
        'procedures.txt': _PROCEDURES,
        'notes_marche.txt': _NOTES_MARCHE,
    }


# Départements de démo et fichiers associés
DEMO_LAYOUT: Dict[str, List[str]] = {
    'demo_comptabilite': ['clients.csv', 'factures.csv', 'salaries.csv',
                          'bilan_2025.txt'],
    'demo_procedures': ['procedures.txt', 'notes_marche.txt'],
}

# Les questions du script de vente (parcours guidé)
DEMO_QUESTIONS: List[str] = [
    "combien de clients actifs avons-nous ?",
    "quel est le chiffre d'affaires total de nos clients actifs ?",
    "liste des factures en retard",
    "quel est le montant total des factures en retard ?",
    "quelles sont les échéances de TVA à respecter ?",
    "quelle est la procédure de clôture annuelle ?",
    "rédige un email aux clients en retard de paiement",
    "fais le rapport sur la situation des clients",
]


if __name__ == '__main__':
    from pathlib import Path
    out = Path(__file__).resolve().parent / 'demo_data'
    out.mkdir(exist_ok=True)
    for name, content in build_demo_dataset().items():
        (out / name).write_text(content, encoding='utf-8')
        print(f"  ✍️  {name} ({len(content)} caractères)")
    print(f"\n📁 Dataset écrit dans {out}")
