#!/usr/bin/env python3
"""
Test qualitatif des reponses de l'hologramme.

Evalue la PERTINENCE des tokens resonants pour differentes
requetes domaine-specifiques, en mesurant :
  - Ratio de tokens pertinents dans le top-K
  - Presence de mots-cles attendus
  - Couverture semantique (combien de domaines couverts)
  - Score de qualite global
"""

import sys, os, time, math, json
import numpy as np

_proj_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_proj_root, ".."))

# Couleurs
class C:
    OK = '\033[92m'
    FAIL = '\033[91m'
    WARN = '\033[93m'
    BOLD = '\033[1m'
    END = '\033[0m'

# =========================================================================
# Jeu de requetes avec mots-cles attendus
# =========================================================================
REQUETES = [
    {
        "requete": "histoire du Ghana empire africain",
        "attendu": ["ghana", "empire", "afrique", "royaume", "soninke"],
        "domaine": "histoire",
    },
    {
        "requete": "empire du Mali et Songhai",
        "attendu": ["mali", "songhai", "empire", "tombouctou", "sankore"],
        "domaine": "histoire",
    },
    {
        "requete": "Nelson Mandela apartheid Afrique du Sud",
        "attended": ["mandela", "apartheid", "decolonisation", "souverainete"],
        "domaine": "histoire",
    },
    {
        "requete": "infarctus du myocarde hypertension arterielle",
        "attendu": ["infarctus", "hypertension", "cardiaque", "cardiovasculaire", "therapie"],
        "domaine": "medecine",
    },
    {
        "requete": "traitement du diabete insulinoresistance",
        "attendu": ["diabete", "insuline", "metabolisme", "therapeutique", "chronique"],
        "domaine": "medecine",
    },
    {
        "requete": "cancer du poumon metastases",
        "attendu": ["cancer", "metastatique", "tumeur", "diagnostic", "therapie"],
        "domaine": "medecine",
    },
    {
        "requete": "maladie dAlzheimer neurodegenerescence",
        "attendu": ["alzheimer", "neurodegenerative", "demenence", "therapie", "chronique"],
        "domaine": "medecine",
    },
    {
        "requete": "systeme immunitaire inflammation cytokines",
        "attendu": ["immunitaire", "inflammation", "pathogene", "anticorps", "therapie"],
        "domaine": "immunologie",
    },
    {
        "requete": "therapie genetique et biotechnologie",
        "attendu": ["genetique", "therapie", "therapeutique", "biomarqueur", "proteine"],
        "domaine": "biotechnologie",
    },
    {
        "requete": "philosophie ontologie epistemologie",
        "attendu": ["ontologie", "phenomenologie", "linguistique", "raisonnement", "conscience"],
        "domaine": "philosophie",
    },
]

# Domaines et leurs mots-cles de pertinence
PERTINENCE_PAR_DOMAINE = {
    "histoire": [
        "ghana", "empire", "afrique", "mali", "songhai", "tombouctou",
        "mandela", "apartheid", "decolonisation", "royaume", "nubie",
        "ethiopie", "carthage", "souverainete", "colonisation", "peuple",
    ],
    "medecine": [
        "infarctus", "hypertension", "cardiaque", "diabete", "cancer",
        "alzheimer", "therapie", "therapeutique", "traitement", "diagnostic",
        "chronique", "aigue", "metabolisme", "inflammation", "infection",
        "pathogene", "anticorps", "vaccination", "symptome", "demenence",
    ],
    "immunologie": [
        "immunitaire", "inflammation", "pathogene", "anticorps", "therapie",
        "infection", "vaccination", "lymphocyte", "cytokine",
    ],
    "biotechnologie": [
        "genetique", "therapie", "therapeutique", "biomarqueur", "proteine",
        "phenotype", "genome", "biologie",
    ],
    "philosophie": [
        "ontologie", "phenomenologie", "linguistique", "raisonnement",
        "conscience", "epistemologie", "hermeneutique",
    ],
}


def test_resonance_qualitative(connecteur):
    """Test qualitatif : pour chaque requete, mesurer la pertinence
    des tokens resonants."""
    print(f"\n{C.BOLD}{'='*60}{C.END}")
    print(f"{C.BOLD}  TEST QUALITE DES REPONSES HOLOGRAMME{C.END}")
    print(f"{C.BOLD}{'='*60}{C.END}")
    
    # Stats globales
    total_tokens_pertinents = 0
    total_tokens_top10 = 0
    total_attendus_trouves = 0
    total_attendus = 0
    scores_par_domaine = {}
    
    for i, q in enumerate(REQUETES):
        requete = q["requete"]
        attendus = q.get("attendu", []) + q.get("attended", [])
        domaine = q["domaine"]
        mots_pertinence = PERTINENCE_PAR_DOMAINE.get(domaine, [])
        
        print(f"\n{C.BOLD}--- Requete {i+1}: \"{requete}\" [{domaine}] ---{C.END}")
        
        t0 = time.time()
        res = connecteur.resonner(requete, top_k=20)
        dt = time.time() - t0
        
        top_tokens = res.get("top_tokens", [])
        
        if not top_tokens:
            print(f"  {C.FAIL}[FAIL] Aucun token retourne{C.END}")
            continue
        
        # Afficher le top 15
        print(f"  Top 15 tokens resonants ({dt*1000:.0f} ms):")
        
        tokens_trouves = set()
        tokens_pertinents_domaine = 0
        
        for j, (tok, val) in enumerate(top_tokens[:15]):
            # Marquer les tokens attendus specifiquement
            marqueur = ""
            if tok in attendus:
                marqueur = f" {C.OK}<== ATTENDU{C.END}"
                tokens_trouves.add(tok)
            elif tok in mots_pertinence:
                marqueur = f" {C.WARN}<== PERTINENT{C.END}"
                tokens_pertinents_domaine += 1
            
            # Verifier la pertinence semantique grossiere
            print(f"    {j+1:2d}. {tok:25s} {val:.6f}{marqueur}")
        
        # Statistiques de qualite
        n_attendus_trouves = len(tokens_trouves)
        n_attendus_total = len(attendus)
        n_pertinents_top10 = sum(1 for tok, _ in top_tokens[:10] if tok in mots_pertinence)
        n_pertinents_top20 = sum(1 for tok, _ in top_tokens[:20] if tok in mots_pertinence)
        
        total_attendus_trouves += n_attendus_trouves
        total_attendus += n_attendus_total
        total_tokens_pertinents += n_pertinents_top20
        total_tokens_top10 += 10
        
        # Energie et delta
        energie_avant = res.get("energie_avant", 0)
        energie_apres = res.get("energie_apres", 0)
        
        # Score de qualite pour cette requete
        ratio_pertinence_top10 = n_pertinents_top10 / 10.0
        ratio_attendus = n_attendus_trouves / max(n_attendus_total, 1)
        score_requete = (ratio_pertinence_top10 * 0.5 + ratio_attendus * 0.5) * 10
        
        print(f"\n  Stats requete:")
        print(f"    Attendus trouves: {n_attendus_trouves}/{n_attendus_total}")
        print(f"    Pertinence domaine top10: {n_pertinents_top10}/10 ({ratio_pertinence_top10*100:.0f}%)")
        print(f"    Pertinence domaine top20: {n_pertinents_top20}/20 ({n_pertinents_top20/20*100:.0f}%)")
        print(f"    Energie: {energie_avant:.0f} -> {energie_apres:.0f}")
        print(f"    Score qualite: {score_requete:.1f}/10")
        
        # Accumuler par domaine
        if domaine not in scores_par_domaine:
            scores_par_domaine[domaine] = []
        scores_par_domaine[domaine].append(score_requete)
    
    # === Rapport global ===
    print(f"\n{C.BOLD}{'='*60}{C.END}")
    print(f"{C.BOLD}  RAPPORT QUALITE GLOBAL{C.END}")
    print(f"{C.BOLD}{'='*60}{C.END}")
    
    if total_attendus > 0:
        ratio_attendus_global = total_attendus_trouves / total_attendus
    else:
        ratio_attendus_global = 0
    pertinence_moyenne = total_tokens_pertinents / max(len(REQUETES) * 20, 1)
    
    print(f"\n  Mots-cles attendus trouves: {total_attendus_trouves}/{total_attendus} "
          f"({ratio_attendus_global*100:.1f}%)")
    print(f"  Pertinence domaine moyenne (top20): {pertinence_moyenne*100:.1f}%")
    
    print(f"\n  Scores par domaine:")
    for domaine, scores in sorted(scores_par_domaine.items()):
        moy = sum(scores) / len(scores)
        bar = "#" * int(moy)
        print(f"    {domaine:20s}: {moy:.1f}/10 |{bar}")
    
    score_global = (ratio_attendus_global * 0.4 + pertinence_moyenne * 0.6) * 10
    print(f"\n  {C.BOLD}SCORE QUALITE GLOBAL: {score_global:.1f}/10{C.END}")
    
    if score_global >= 7.0:
        print(f"  {C.OK}[OK] Qualite satisfaisante{C.END}")
    elif score_global >= 5.0:
        print(f"  {C.WARN}[WARN] Qualite moyenne, peut etre amelioree{C.END}")
    else:
        print(f"  {C.FAIL}[FAIL] Qualite insuffisante{C.END}")
    
    return {
        "score_global": score_global,
        "attendus_trouves": total_attendus_trouves,
        "attendus_total": total_attendus,
        "pertinence_moyenne": pertinence_moyenne,
        "scores_par_domaine": {d: sum(s)/len(s) for d, s in scores_par_domaine.items()},
    }


def test_compare_ancien_nouveau():
    """Compare qualitativement l'ancien et le nouveau vocabulaire
    sur quelques requetes cle."""
    print(f"\n{C.BOLD}--- Comparaison Ancien vs Nouveau vocabulaire ---{C.END}")
    
    from engine.hologram_connector import HologrammeConnecteur
    
    # Creer deux connecteurs temporaires avec le meme hologramme
    # mais des tokenizers differents
    from harmonic_training.model.vocabulaire_etendu import VOCABULAIRE_BASE, VOCABULAIRE_ETENDU
    from harmonic_training.model.harmonic_resonance_generator import TokeniseurOndes, HologrammeMonde
    
    HOLOGRAMME_PATH = os.path.join(_proj_root, "..", "ka_knowledge_base", "hologramme.npy")
    HOLOGRAMME_PATH = os.path.normpath(HOLOGRAMME_PATH)
    
    if not os.path.exists(HOLOGRAMME_PATH):
        print(f"  {C.FAIL}[FAIL] Hologramme introuvable: {HOLOGRAMME_PATH}{C.END}")
        return {"ok": False}
    
    # Charger l'hologramme
    monde = HologrammeMonde(64, 64)
    monde.H = np.load(HOLOGRAMME_PATH)
    monde.n_experiences = 172872
    
    tokenizer_old = TokeniseurOndes(VOCABULAIRE_BASE, use_pi_over_6=True)
    tokenizer_new = TokeniseurOndes(VOCABULAIRE_ETENDU, use_pi_over_6=True)
    
    requetes_test = [
        "histoire de l'empire du Ghana",
        "traitement de l'hypertension et infarctus",
        "Maladie d'Alzheimer et Parkinson",
    ]
    
    for requete in requetes_test:
        print(f"\n  Requete: \"{requete}\"")
        
        # Ancien vocabulaire
        tokens_old = tokenizer_old.tokeniser(requete)
        unk_old = sum(1 for t in tokens_old if t == 1)
        
        # Nouveau vocabulaire
        tokens_new = tokenizer_new.tokeniser(requete)
        unk_new = sum(1 for t in tokens_new if t == 1)
        
        old_tokens_str = [tokenizer_old.i2w.get(t, f'<UNK({t})>') for t in tokens_old]
        new_tokens_str = [tokenizer_new.i2w.get(t, f'<UNK({t})>') for t in tokens_new]
        
        print(f"    Ancien ({len(VOCABULAIRE_BASE)} tok): {unk_old}/{len(tokens_old)} UNK")
        print(f"      Tokens: {' '.join(old_tokens_str)}")
        print(f"    Nouveau ({len(VOCABULAIRE_ETENDU)} tok): {unk_new}/{len(tokens_new)} UNK")
        print(f"      Tokens: {' '.join(new_tokens_str)}")
        
        if unk_new < unk_old:
            print(f"    {C.OK}[OK] Amelioration: -{unk_old - unk_new} UNK{C.END}")
        elif unk_new == unk_old:
            print(f"    {C.WARN}[=] Identique{C.END}")
        else:
            print(f"    {C.FAIL}[FAIL] Degradation{C.END}")
    
    return {"ok": True}


def test_contexte_formate():
    """Verifie que le contexte formate contient des informations
    utiles et pas juste des tokens isoles."""
    print(f"\n{C.BOLD}--- Evaluation du contexte formate ---{C.END}")
    
    from engine.hologram_connector import HologrammeConnecteur
    
    HOLOGRAMME_PATH = os.path.join(_proj_root, "..", "ka_knowledge_base", "hologramme.npy")
    HOLOGRAMME_PATH = os.path.normpath(HOLOGRAMME_PATH)
    
    if not os.path.exists(HOLOGRAMME_PATH):
        print(f"  {C.FAIL}[FAIL] Hologramme introuvable{C.END}")
        return
    
    connecteur = HologrammeConnecteur(HOLOGRAMME_PATH)
    
    requetes_contexte = [
        "Parle-moi de l'empire du Ghana en Afrique",
        "Quels sont les traitements pour l'hypertension",
        "Explique la maladie d'Alzheimer",
    ]
    
    for requete in requetes_contexte:
        print(f"\n  Requete: \"{requete}\"")
        t0 = time.time()
        res = connecteur.resonner(requete, top_k=25)
        dt = time.time() - t0
        
        contexte = res.get("contexte", "")
        top_tokens = res.get("top_tokens", [])
        
        # Verifier que le contexte n'est pas vide
        if contexte:
            # Verification qualitative : le contexte contient-il les tokens ?
            tokens_utilises = [t[0] for t in top_tokens[:10]]
            tokens_dans_contexte = sum(1 for t in tokens_utilises if t in contexte.lower())
            ratio = tokens_dans_contexte / max(len(tokens_utilises), 1)
            
            print(f"    Contexte ({len(contexte)} chars, {dt*1000:.0f} ms):")
            # Afficher les 200 premiers caracteres
            if len(contexte) > 200:
                print(f"      \"{contexte[:200]}...\"")
            else:
                print(f"      \"{contexte}\"")
            print(f"    Ratio tokens dans contexte: {tokens_dans_contexte}/{len(tokens_utilises)} ({ratio*100:.0f}%)")
        else:
            print(f"    {C.WARN}[WARN] Contexte vide{C.END}")
    
    print(f"\n  {C.OK}[OK] Test contexte termine{C.END}")


def main():
    print(f"{C.BOLD}{'='*60}{C.END}")
    print(f"{C.BOLD}  EVALUATION QUALITE DES REPONSES HOLOGRAMME{C.END}")
    print(f"{C.BOLD}{'='*60}{C.END}")
    
    from engine.hologram_connector import HologrammeConnecteur
    
    HOLOGRAMME_PATH = os.path.join(_proj_root, "..", "ka_knowledge_base", "hologramme.npy")
    HOLOGRAMME_PATH = os.path.normpath(HOLOGRAMME_PATH)
    
    if not os.path.exists(HOLOGRAMME_PATH):
        print(f"{C.FAIL}[FAIL] Hologramme introuvable: {HOLOGRAMME_PATH}{C.END}")
        print(f"Lancez d'abord: python scripts/reinjecter_connaissances.py")
        sys.exit(1)
    
    connecteur = HologrammeConnecteur(HOLOGRAMME_PATH)
    
    if not connecteur.est_charge():
        print(f"{C.FAIL}[FAIL] Impossible de charger l'hologramme{C.END}")
        sys.exit(1)
    
    # Test 1: Comparaison ancien vs nouveau vocabulaire
    r_compare = test_compare_ancien_nouveau()
    
    # Test 2: Resonance qualitative
    r_qualite = test_resonance_qualitative(connecteur)
    
    # Test 3: Contexte formate
    test_contexte_formate()
    
    # Synthese
    print(f"\n{C.BOLD}{'='*60}{C.END}")
    print(f"{C.BOLD}  SYNTHESE QUALITE{C.END}")
    print(f"{C.BOLD}{'='*60}{C.END}")
    
    score = r_qualite.get("score_global", 0)
    attendus = r_qualite.get("attendus_trouves", 0)
    total_att = r_qualite.get("attendus_total", 3)
    
    print(f"  Score qualite global: {score:.1f}/10")
    print(f"  Mots-cles attendus: {attendus}/{total_att}")
    print(f"  Vocabulaire: 2125 tokens (pi/6)")
    print(f"  Hologramme: {connecteur.monde.energie():.0f} energie")
    
    if score >= 7.0:
        print(f"\n{C.BOLD}{C.OK}  [OK] Qualite satisfaisante - L'hologramme repond correctement{C.END}")
    elif score >= 5.0:
        print(f"\n{C.WARN}  [WARN] Qualite moyenne - Des injections supplementaires pourraient ameliorer les resultats{C.END}")
    else:
        print(f"\n{C.FAIL}  [FAIL] Qualite insuffisante - Necessite plus de donnees d'injection{C.END}")
    
    print(f"{C.BOLD}{'='*60}{C.END}")
    
    return r_qualite


if __name__ == "__main__":
    main()
