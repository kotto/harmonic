# -*- coding: utf-8 -*-
"""
📦 build_hologram_bundle.py — Bundle offline pour l'APK Android
================================================================
Génère un fichier JSON compact embarquable dans Capacitor (www/data/)
contenant :
  - Les faits médicaux par domaine (pour le retrieval)
  - L'index lexical par domaine (pour le routage, pré-calculé)
  - Les templates de phrasé naturel

Le routeur JS (ka_hologram_router.js) charge ce bundle et répond
100% offline — aucune API nécessaire sur le téléphone.

Usage : python build_hologram_bundle.py
Sortie : vital-ka-android/www/data/hologram_bundle.json
"""

import json, re, sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
HOLO = ENGINE / "data" / "medical_holograms"
# Source (versionnée) + destination www (pour Capacitor)
SRC_OUT = ENGINE / "data" / "hologram_bundle.json"
WWW_OUT = ENGINE / "vital-ka-android" / "www" / "data" / "hologram_bundle.json"
WWW_OUT.parent.mkdir(parents=True, exist_ok=True)

STOP = {'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou',
        'au', 'aux', 'en', 'pour', 'avec', 'sur', 'est', 'sont', 'ce',
        'cette', 'dans', 'à', 'a', 'mon', 'ma', 'mes', 'son', 'sa',
        'ses', 'qui', 'que', 'si', 'au', 'par', 'pas', 'plus', 'parmi',
        'chez', 'sans', 'sous', 'vers', 'depuis', 'pendant', 'entre'}

# ── Templates de phrasé (portage du routeur Python) ──
TEMPLATES = {
    'présente_symptôme': 'Le patient présente le symptôme « {o} » dans le cadre de {s}.',
    'presente_symptome': 'Le patient présente le symptôme « {o} » dans le cadre de {s}.',
    'traitement': 'Traitement de {s} : {o}.',
    'dose_adulte': 'Dose adulte de {s} : {o}.',
    'dose_enfant': 'Dose pédiatrique de {s} : {o}.',
    'dose_pediatrique': 'Dose pédiatrique de {s} : {o}.',
    'dose': 'Dose de {s} : {o}.',
    'indication': '{s} est indiqué pour : {o}.',
    'contre_indications': 'Contre-indication de {s} : {o}.',
    'effets_secondaires': 'Effets secondaires possibles de {s} : {o}.',
    'gravité': 'Niveau de gravité de {s} : {o}.',
    'gravite': 'Niveau de gravité de {s} : {o}.',
    'conduite_à_tenir': 'Conduite à tenir face à {s} : {o}.',
    'conduite_a_tenir': 'Conduite à tenir face à {s} : {o}.',
    'délai_consultation': 'Consulter dans les délais suivants pour {s} : {o}.',
    'delai_consultation': 'Consulter dans les délais suivants pour {s} : {o}.',
    'interaction': 'Interaction médicamenteuse : {s} → {o}.',
    'classe': '{s} appartient à la classe : {o}.',
    'voie': 'Voie d\'administration de {s} : {o}.',
    'grossesse': 'Grossesse — {s} : {o}.',
    'âge_fréquent': '{s} survient fréquemment à l\'âge de : {o}.',
    'age_frequent': '{s} survient fréquemment à l\'âge de : {o}.',
    'sexe_fréquent': '{s} survient plus fréquemment chez : {o}.',
    'sexe_frequent': '{s} survient plus fréquemment chez : {o}.',
    'prévention': 'Prévention de {s} : {o}.',
    'prevention': 'Prévention de {s} : {o}.',
    'urgence': 'SITUATION D\'URGENCE — {s} : {o}.',
    'urgences': 'SITUATION D\'URGENCE — {s} : {o}.',
    'definition': 'Définition : {s} correspond à {o}.',
    'signes_cliniques': 'Signes cliniques de {s} : {o}.',
    'signes_indicateurs': 'Signes indicateurs de {s} : {o}.',
    'facteurs_risque': 'Facteurs de risque de {s} : {o}.',
    'complications': 'Complications possibles de {s} : {o}.',
    'vaccination': 'Vaccination {s} : {o}.',
    'calendrier': 'Calendrier {s} : {o}.',
    'age_recommande': 'Âge recommandé pour {s} : {o}.',
    'maladies_previent': '{s} prévient : {o}.',
    'mode_preparation': 'Préparation de {s} : {o}.',
    'partie_utilisee': 'Partie utilisée de {s} : {o}.',
}
DEFAULT_TEMPLATE = 'Information sur {s} : {o}.'


def tokenize(text):
    return [w for w in re.findall(r"[a-zà-ÿ0-9]+", text.lower())
            if w not in STOP]


def build():
    bundle = {
        'version': '1.1',
        'domains': {},   # domaine → {facts: [[s, r, o]], vocab: [mots]}
        'templates': TEMPLATES,
        'default_template': DEFAULT_TEMPLATE,
    }

    for facts_file in sorted(HOLO.glob('*_facts.json')):
        domain = facts_file.name.replace('_facts.json', '')
        with open(facts_file, encoding='utf-8') as f:
            facts = json.load(f)

        # Faits compactés [s, r, o] + index lexical
        vocab = set()
        compact = []
        for fact in facts:
            s, r, o = str(fact.get('s', '')), str(fact.get('r', '')), str(fact.get('o', ''))
            compact.append([s, r, o])
            # Sujets (poids fort au routage) + objets
            vocab.update(w for w in tokenize(s))
            vocab.update(w for w in tokenize(o) if len(w) > 3)

        bundle['domains'][domain] = {
            'facts': compact,
            'vocab': sorted(vocab),
        }

    out_path = SRC_OUT
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(bundle, f, ensure_ascii=False, separators=(',', ':'))
    # Copie vers www/data pour Capacitor
    import shutil
    shutil.copy2(SRC_OUT, WWW_OUT)

    size_kb = out_path.stat().st_size / 1024
    total_facts = sum(len(d['facts']) for d in bundle['domains'].values())
    print(f"✅ Bundle généré : {out_path.name}")
    print(f"   {len(bundle['domains'])} domaines | {total_facts:,} faits | {size_kb:.0f} KB")
    for dom, d in bundle['domains'].items():
        print(f"   • {dom:<18} {len(d['facts']):>6} faits | vocab {len(d['vocab']):>5}")


if __name__ == '__main__':
    build()
