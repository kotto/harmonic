#!/usr/bin/env python3
"""
GENERATEUR AUTOMATIQUE DE VOCABULAIRE_ETENDU.
Analyse vocabulaire_extrait.py + VOCABULAIRE_BASE → génère MOTS_NOUVEAUX filtrés.
"""
import sys
import os

# Ajouter le chemin pour l'import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Importer VOCABULAIRE_BASE depuis le fichier partiel
from harmonic_training.model.vocabulaire_etendu import VOCABULAIRE_BASE

# Importer les mots extraits
from harmonic_training.model.vocabulaire_extrait import MOTS_PAR_FREQUENCE

# Stopwords français supplémentaires (non dans VOCABULAIRE_BASE)
STOPWORDS = {
    'environ', 'sont', 'ont', 'ans', 'était', 'avait', 'étaient', 'été', 'peut', 'être',
    'entre', 'très', 'chez', 'leur', 'tous', 'seul', 'non', 'ni', 'sans', 'chaque',
    'dont', 'entre', 'peut', 'faire', 'monde', 'tous', 'leur', 'non', 'ans', 'mois',
    'année', 'tous', 'chaque', 'entre', 'leurs', 'elles', 'touchent',
    'aussi', 'cette', 'donc', 'alors', 'car', 'puis', 'très',
    'première', 'nouveaux', 'grand', 'se', 'ce', 'sa', 'ces',
    'reste', 'cas', 'base', 'rapport', 'suivi', 'seul', 'ne',
    'pas', 'taux', 'dont', 'toutes', 'permet',
}

# Mots déjà dans VOCABULAIRE_BASE (normalisés)
BASE_SET = set(VOCABULAIRE_BASE)

def normaliser(mot: str) -> str:
    """Normalise un mot pour comparaison : lowercase, sans accents simples."""
    return mot.lower().strip().replace("'", "")

def main():
    # Filtrer les mots nouveaux
    nouveaux = []
    vus = set()
    
    for mot, freq in MOTS_PAR_FREQUENCE:
        mot_norm = normaliser(mot)
        
        # Skip si déjà dans BASE
        if mot_norm in BASE_SET:
            continue
        
        # Skip stopwords
        if mot_norm in STOPWORDS:
            continue
        
        # Skip les mots trop courts (1-2 chars) ou numériques
        if len(mot_norm) <= 2 and not mot_norm.isalpha():
            continue
        
        # Skip si déjà ajouté
        if mot_norm in vus:
            continue
        
        vus.add(mot_norm)
        nouveaux.append((mot, freq))
    
    # Trier par fréquence (desc) puis alpha
    nouveaux.sort(key=lambda x: (-x[1], x[0]))
    
    print(f"VOCABULAIRE_BASE: {len(VOCABULAIRE_BASE)} tokens")
    print(f"Mots extraits (uniques): {len(MOTS_PAR_FREQUENCE)}")
    print(f"Mots nouveaux (après filtre): {len(nouveaux)}")
    print(f"Total estimé: {len(VOCABULAIRE_BASE) + len(nouveaux)} tokens")
    
    # Classification heuristique par domaine
    histoire_mots = []
    medecine_mots = []
    sciences_mots = []
    divers_mots = []
    
    # Mots-clés d'histoire africaine
    HISTOIRE_CLEFS = {
        'afrique', 'africain', 'africaine', 'africaines', 'africains',
        'royaume', 'koush', 'méroé', 'ghana', 'mali', 'zimbabwe',
        'kongo', 'nzinga', 'ndongo', 'matamba', 'angola',
        'dahomey', 'samory', 'touré', 'ménélik', 'ranavalona',
        'madagascar', 'chaka', 'zoulou', 'bismarck', 'berlin',
        'nkrumah', 'kwame', 'garvey', 'marcus', 'equiano', 'olaudah',
        'panafricanisme', 'panafricain', 'panafricaniste',
        'colonisation', 'colonial', 'négrière', 'déporté',
        'transatlantique', 'abolitionniste',
        'tirailleurs', 'sénégalais', 'soldats',
        'siècle', 'xixe', 'xxe', 'xviie', 'xive', 'xiie', 'xiiie',
        'civilisation', 'écriture', 'hiéroglyphes', 'méroïtique',
        'langues', 'langue', 'swahilie', 'transsaharienne', 'transsahariennes',
        'mansa', 'kankan', 'moussa',
        'capitale', 'empereur', 'reine', 'roi',
        'bataille', 'guerre', 'guerres', 'résistance', 'résistances',
        'résisté', 'révoltes', 'combattu',
        'indépendant', 'indépendances', 'indépendante',
        'partage', 'conférence', 'chancelier',
        'exploitation', 'économique', 'brutale',
        'soldats', 'combattu', 'mondiales',
        'déterminante', 'massive', 'participation',
    }
    
    MEDECINE_CLEFS = {
        'cancer', 'cancers', 'traitement', 'traitements', 'maladie', 'maladies',
        'patient', 'patients', 'diagnostic', 'dépistage',
        'chronique', 'chroniques', 'aiguë', 'symptômes',
        'infection', 'infectieuse', 'bactérienne', 'bactéries', 'virale', 'virus',
        'tuberculose', 'tuberculosis', 'paludisme', 'vih/sida',
        'pneumonie', 'bronchopneumopathie', 'bpco',
        'bronchiolite', 'coqueluche', 'rougeole', 'oreillons', 'rubéole',
        'tétanos', 'diphtérie', 'poliomyélite',
        'diabète', 'hypertension', 'cardiaque', 'cardiovasculaire',
        'infarctus', 'fibrillation', 'atriale', 'arythmie',
        'accident', 'vasculaire', 'cérébral', 'avc',
        'parkinson', 'alzheimer', 'sclérose', 'plaques',
        'dépression', 'anxiété', 'schizophrénie', 'bipolaire',
        'psychiatrique', 'psychiatriques',
        'asthme', 'bronchite', 'pneumocoque', 'méningocoque',
        'hépatite', 'hépatites', 'cirrhose',
        'rénal', 'rénale', 'rénaux',
        'antibiotiques', 'antipsychotiques', 'immunosuppresseurs',
        'vaccination', 'vaccins', 'vaccinal',
        'chirurgie', 'radiothérapie', 'chimiothérapie',
        'transplantation', 'greffe',
        'médicament', 'médicaments', 'posologie', 'contre-indication',
        'épidémiologie', 'prévalence', 'incidence', 'mortalité',
        'soins', 'santé', 'publique', 'hôpital', 'clinique',
        'urgences', 'réanimation',
        'pédiatrie', 'néonatologie', 'gériatrie',
        'cardiaque', 'respiratoire', 'neurologique', 'rénal',
        'inflammatoire', 'auto-immune', 'dégénérative',
        'génétique', 'mutation', 'moléculaire', 'cellulaire',
        'staphylococcus', 'streptococcus', 'pseudomonas', 'aeruginosa',
        'escherichia', 'coli', 'entérobactéries',
        'méticilline', 'carbapénèmes', 'rifampicine', 'isoniazide',
        'statines', 'atorvastatine', 'rosuvastatine',
        'insuffisance', 'cardiaque', 'rénale', 'hépatique',
        'obésité', 'surpoids', 'métabolique', 'syndrome',
        'thyroïde', 'dysthyroïdies', 'cushing',
        'prostate', 'colorectal', 'poumon', 'mélanome', 'sein',
        'psoriasis', 'eczéma', 'dermatite', 'dermatose',
        'polyarthrite', 'rhumatoïde', 'goutte', 'arthropathie',
        'ostéoporose', 'fracture',
        'grossesse', 'pré-éclampsie', 'mammographie',
        'cataracte', 'glaucome', 'dégénérescence', 'maculaire',
        'dépistage', 'prévention', 'traitement',
        'rééducation', 'kinésithérapie', 'réhabilitation',
        'palliatif', 'soins', 'accompagnement',
    }
    
    SCIENCES_CLEFS = {
        'gène', 'protéine', 'cellule', 'cellules', 'neurones',
        'molécule', 'molécules', 'atome', 'particule',
        'quantique', 'mécanique', 'ondulatoire',
        'thermodynamique', 'entropie', 'énergie',
        'mathématique', 'algèbre', 'géométrie', 'calcul',
        'statistique', 'probabilité', 'corrélation',
        'données', 'analyse', 'algorithme',
        'réseau', 'neuronal', 'profond', 'apprentissage',
        'intelligence', 'artificielle',
        'classification', 'régression', 'optimisation',
    }
    
    for mot, freq in nouveaux:
        mot_lower = mot.lower()
        if mot_lower in HISTOIRE_CLEFS:
            histoire_mots.append((mot, freq))
        elif mot_lower in MEDECINE_CLEFS:
            medecine_mots.append((mot, freq))
        elif mot_lower in SCIENCES_CLEFS:
            sciences_mots.append((mot, freq))
        else:
            divers_mots.append((mot, freq))
    
    print(f"\n--- Répartition par domaine ---")
    print(f"Histoire africaine: {len(histoire_mots)} mots")
    print(f"Médecine (PubMed): {len(medecine_mots)} mots")
    print(f"Sciences: {len(sciences_mots)} mots")
    print(f"Divers: {len(divers_mots)} mots")
    
    # Afficher les mots divers non classifiés (batch)
    print(f"\n--- Mots divers non classifiés ({len(divers_mots)}) ---")
    for mot, freq in divers_mots[:30]:
        print(f"  {mot} (freq={freq})")
    if len(divers_mots) > 30:
        print(f"  ... et {len(divers_mots)-30} autres")
    
    # Générer la sortie
    output = []
    output.append("# MOTS_NOUVEAUX — Mots specifiques extraits des injections de connaissance\n")
    output.append("# Organises par domaine : Histoire africaine, Medecine (PubMed), Sciences\n")
    output.append("# (generes automatiquement par scripts/generer_vocabulaire_etendu.py)\n")
    
    # Section 1: Histoire africaine
    output.append("# " + "="*60)
    output.append("# SECTION 1 : HISTOIRE AFRICAINE (UNESCO)")
    output.append("# " + "="*60)
    for mot, freq in histoire_mots:
        output.append(f"    '{mot}',")
    
    # Section 2: Médecine
    output.append("\n# " + "="*60)
    output.append("# SECTION 2 : MEDECINE (PubMed)")
    output.append("# " + "="*60)
    for mot, freq in medecine_mots:
        output.append(f"    '{mot}',")
    
    # Section 3: Sciences
    output.append("\n# " + "="*60)
    output.append("# SECTION 3 : SCIENCES & DIVERS")
    output.append("# " + "="*60)
    for mot, freq in sciences_mots:
        output.append(f"    '{mot}',")
    for mot, freq in divers_mots:
        output.append(f"    '{mot}',")
    
    output.append("]")
    output.append("")
    
    # Code final
    output.append("# Filtrer les doublons avec VOCABULAIRE_BASE")
    output.append("MOTS_NOUVEAUX_FILTRES = []")
    output.append("for mot in MOTS_NOUVEAUX:")
    output.append("    if mot not in VOCAB_BASE_SET and mot not in MOTS_NOUVEAUX_FILTRES:")
    output.append("        MOTS_NOUVEAUX_FILTRES.append(mot)")
    output.append("")
    output.append("# Vocabulaire etendu final")
    output.append("VOCABULAIRE_ETENDU = VOCABULAIRE_BASE + MOTS_NOUVEAUX_FILTRES")
    output.append("VOCAB_SIZE_ETENDU = len(VOCABULAIRE_ETENDU)")
    output.append("")
    output.append("if __name__ == '__main__':")
    output.append("    print(f'VOCABULAIRE_BASE: {len(VOCABULAIRE_BASE)} tokens')")
    output.append("    print(f'MOTS_NOUVEAUX: {len(MOTS_NOUVEAUX)} tokens (bruts)')")
    output.append("    print(f'MOTS_NOUVEAUX_FILTRES: {len(MOTS_NOUVEAUX_FILTRES)} tokens (apres dedup)')")
    output.append("    print(f'VOCABULAIRE_ETENDU: {VOCAB_SIZE_ETENDU} tokens')")
    output.append("    # Verification : mots cibles doivent etre presents")
    output.append("    cibles = ['ghana','infarctus','fibrillation','paludisme','parkinson',")
    output.append("              'tuberculose','hypertension','alzheimer','cancer','diabete',")
    output.append("              'schizophrenie','hologramme','connaissance','resonance']")
    output.append("    print('\\n--- Verification mots cibles ---')")
    output.append("    VOCAB_SET = set(VOCABULAIRE_ETENDU)")
    output.append("    for c in cibles:")
    output.append("        present = c in VOCAB_SET")
    output.append("        print(f'  {c:25s} -> {\"OK\" if present else \"MANQUE\"}')")
    
    print("\n\n=== GENERATION ===\n" + "\n".join(output))
    
    # Sauvegarder dans un fichier temporaire
    outpath = os.path.join(os.path.dirname(__file__), '..', 
                          'harmonic_training', 'model', '_mots_nouveaux_generees.txt')
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write("\n".join(output))
    print(f"\n[SAUVEGARDE] -> {outpath}")
    
    return len(nouveaux)

if __name__ == '__main__':
    n = main()
    print(f"\nTermine. {n} nouveaux mots generes.")
