"""
🏥 prepare_medical_corpus.py — Préparation corpus médical pour HWAT-Med
=====================================================================
Fusionne toutes les sources médicales disponibles en un corpus d'entraînement unique.

Sources :
  1. vital_ka_*.json (14 fichiers structurés)
  2. data/clinical/train.csv (948MB - cas cliniques avec diagnostics différentiels)
  3. data/clinical/validate.csv + test.csv
  4. data/real_clinical_dataset.json (21MB)
  5. data/corpus/ (autres corpus)

Sortie : data/medical_corpus/train.txt (texte brut pour tokenizer + training)
"""

import sys, json, os, csv, re
from pathlib import Path
from typing import List, Dict, Any

_ENGINE = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE))

OUTPUT_DIR = _ENGINE / "data" / "medical_corpus"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# NETTOYAGE & FORMATAGE
# ═══════════════════════════════════════════════════════════════════════════════

def clean_text(text: str) -> str:
    """Nettoie le texte pour l'entraînement."""
    if not text:
        return ""
    # Normaliser espaces
    text = re.sub(r'\s+', ' ', text)
    # Supprimer caractères de contrôle
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)
    return text.strip()

def format_clinical_case(row: Dict) -> str:
    """Formate un cas clinique en texte d'entraînement."""
    parts = []
    
    # Patient info
    age = row.get('AGE', '')
    sex = row.get('SEX', '')
    if age or sex:
        parts.append(f"Patient: {age} ans, {'Homme' if sex == 'M' else 'Femme' if sex == 'F' else 'Inconnu'}.")
    
    # Évidences / symptômes
    evidences = row.get('EVIDENCES', '') or row.get('INITIAL_EVIDENCE', '')
    if evidences:
        # Nettoyer la liste d'évidence
        evidences = evidences.replace("['", "").replace("']", "").replace("', '", ", ")
        parts.append(f"Symptômes et signes: {evidences}.")
    
    # Diagnostic différentiel
    diff_diag = row.get('DIFFERENTIAL_DIAGNOSIS', '')
    if diff_diag:
        parts.append(f"Diagnostic différentiel: {diff_diag}.")
    
    # Pathologie confirmée
    pathology = row.get('PATHOLOGY', '')
    if pathology:
        parts.append(f"Diagnostic confirmé: {pathology}.")
    
    return " ".join(parts)

def extract_from_vital_ka_json(data: Dict, source_name: str) -> List[str]:
    """Extrait des phrases d'entraînement depuis les JSON vital_ka."""
    texts = []
    
    def process_dict(d: Dict, prefix: str = ""):
        for k, v in d.items():
            if isinstance(v, str):
                if len(v) > 20:  # Ignorer trop courts
                    texts.append(f"{prefix}{k}: {v}")
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, str):
                        if len(item) > 20:
                            texts.append(f"{prefix}{k}: {item}")
                    elif isinstance(item, dict):
                        process_dict(item, f"{prefix}{k} > ")
            elif isinstance(v, dict):
                process_dict(v, f"{prefix}{k} > ")
    
    process_dict(data)
    return texts

# ═══════════════════════════════════════════════════════════════════════════════
# EXTRACTION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

def extract_vital_ka_corpus() -> List[str]:
    """Extrait tout le corpus depuis les fichiers vital_ka_*.json."""
    texts = []
    vital_ka_dir = _ENGINE / "data"
    
    for f in sorted(vital_ka_dir.glob("vital_ka_*.json")):
        print(f"  📖 Lecture: {f.name}")
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
            extracted = extract_from_vital_ka_json(data, f.stem)
            texts.extend(extracted)
            print(f"     → {len(extracted)} segments extraits")
        except Exception as e:
            print(f"     ❌ Erreur: {e}")
    
    return texts

def extract_clinical_csv(csv_path: Path, max_rows: int = None) -> List[str]:
    """Extrait le corpus depuis les CSV cliniques."""
    texts = []
    print(f"  📖 Lecture CSV: {csv_path.name}")
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as fp:
            reader = csv.DictReader(fp)
            for i, row in enumerate(reader):
                if max_rows and i >= max_rows:
                    break
                text = format_clinical_case(row)
                if text and len(text) > 50:
                    texts.append(text)
                if i % 10000 == 0 and i > 0:
                    print(f"     → {i:,} lignes traitées...")
    except Exception as e:
        print(f"     ❌ Erreur: {e}")
    
    print(f"     → {len(texts):,} cas cliniques extraits")
    return texts

def extract_real_clinical_json() -> List[str]:
    """Extrait depuis real_clinical_dataset.json (21MB)."""
    texts = []
    path = _ENGINE / "data" / "real_clinical_dataset.json"
    print(f"  📖 Lecture: {path.name}")
    
    try:
        with open(path, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    # Essayer différents formats
                    for key in ['text', 'content', 'case', 'description', 'clinical_text']:
                        if key in item and item[key]:
                            texts.append(clean_text(str(item[key])))
                    # Si format inconnu, serializer
                    if not any(k in item for k in ['text', 'content', 'case', 'description', 'clinical_text']):
                        texts.append(clean_text(json.dumps(item, ensure_ascii=False)))
        elif isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, str):
                            texts.append(clean_text(item))
                        elif isinstance(item, dict):
                            for key in ['text', 'content', 'case', 'description']:
                                if key in item:
                                    texts.append(clean_text(str(item[key])))
    except Exception as e:
        print(f"     ❌ Erreur: {e}")
    
    print(f"     → {len(texts):,} segments extraits")
    return texts

# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATION CORPUS SYNTHÉTIQUE (Q/A médical)
# ════════════════════════════════════════════════════════════════════════════════

def generate_synthetic_qa() -> List[str]:
    """Génère des paires Q/A médicales synthétiques pour l'instruction tuning."""
    qa_pairs = [
        # Diagnostic
        ("Quels sont les signes d'alerte d'une méningite bactérienne chez l'adulte ?",
         "Fièvre brutale, céphalées intenses, raideur de nuque (méningisme), photophobie, vomissements, troubles de la conscience, purpura. Urgence vitale : antibiotiques IV immédiats (céphalosporine 3e génération + ampicilline) + dexaméthasone."),
        
        ("Comment différencier une pneumonie typique d'une pneumonie atypique ?",
         "Typique : début brutal, fièvre élevée, toux grasse, douleurs thoraciques, leucocytose, opacité alvéolaire radio. Atypique : début progressif, fièvre modérée, toux sèche, maux de tête, myalgies, leucocytes normaux, infiltrats interstitiels radio. Étio : S. pneumoniae vs M. pneumoniae, C. pneumoniae, Legionella, virus."),
        
        # Pharmacologie
        ("Quelle est la posologie d'amoxicilline chez l'enfant de 15 kg pour une angine streptococcique ?",
         "Amoxicilline 50 mg/kg/jour en 2 ou 3 prises. Pour 15 kg : 750 mg/jour = 375 mg matin + 375 mg soir (si 2×/j) pendant 6 jours. Soit 7,5 ml de suspension 100 mg/ml matin et soir."),
        
        ("Quelles sont les interactions majeures de la warfarine ?",
         "Augmentation INR : antibiotiques (cotrimoxazole, métronidazole, fluoroquinolones), AINS, amiodarone, allopurinol, phytothérapie (millepertuis diminue l'effet). Surveillance INR rapprochée à toute modification."),
        
        # Urgences
        ("Conduite à tenir devant un syndrome coronarien aigu sans sus-décalage ST (NSTEMI) ?",
         "1) Aspirine 300 mg per os + clopidogrel 300 mg (ou ticagrélor 180 mg) 2) Anticoagulation (héparine bas poids moléculaire ou fondaparinux) 3) Bêta-bloquant si pas de CI 4) Statin haute dose 5) Coronarographie < 24-72h selon score GRACE."),
        
        ("Traitement de l'œdème pulmonaire aigu cardiogène ?",
         "Position assise, O2 haut débit (VNI si PaCO2 > 45), furosémide IV 40-80 mg (bolus), nitrates IV (nitroglycérine) si TA > 110, morphique si anxiété majeure. Recherche cause : AVC, arythmie, insuffisance valvulaire, IAM."),
        
        # Pédiatrie
        ("Signes de gravité d'une diarrhée aiguë chez l'enfant < 5 ans (OMS) ?",
         "Déshydratation sévère : yeux enfoncés, pli cutané > 2s, impossibilité de boire, léthargie. Signes d'alarme : sang dans selles, fièvre > 38.5°C, vomissements incoercibles, signes de choc. Réhydratation IV immédiate (Ringer lactate) plan C OMS."),
        
        # Maladies tropicales
        ("Diagnostic et traitement du paludisme grave à P. falciparum ?",
         "Critères OMS : hyperparasitémie >10%, anémie sévère Hb<5, hypoglycémie, acidose, détresse respiratoire, convulsions, troubles conscience, ictère, hémoglobinurie. Traitement : artésunate IV 2,4 mg/kg H0/H12/H24 puis q24h, relais ACT oral dès que possible. Transfusion si Hb<5."),
        
        ("Prophylaxie du paludisme pour voyageur en zone à résistance chloroquine ?",
         "Atovaquone-proguanil (Malarone) 1 cp/jour (début J-1, pendant séjour, 7j après retour) OU doxycycline 100 mg/jour (début J-1, pendant, 4 sem après) OU méfloquine 250 mg/sem (début 2-3 sem avant). Choix selon tolérance, coût, durée."),
        
        # VIH/TB
        ("Initiation ARV chez patient VIH+ nouvellement diagnostiqué, CD4 150 ?",
         "Démarrer ARV immédiatement (même jour si possible). 1ère ligne OMS : TLD (Ténofovir + Lamivudine + Dolutégravir) 1 cp/jour. Surveillance : charge virale à 3 et 6 mois, fonction rénale (créatinine), poids. Prophylaxie cotrimoxazole si CD4<350 ou stade 3-4."),
        
        ("Schéma standard tuberculose pulmonaire sensible (OMS 2022) ?",
         "Phase intensive 2 mois : RHZE (Rifampicine, Isoniazide, Pyrazinamide, Ethambutol) quotidien. Phase continuation 4 mois : RH. Doses selon poids. Surveillance hépatique mensuelle. DOT (observance directe) recommandé."),
        
        # Gynéco-Obstétrique
        ("Conduite à tenir devant une hémorragie de la délivrance (HPP) ?",
         "Appel aide, massage utérin, perfusion cristalloïdes 2 gros calibres, oxytocine 10-20 UI IV + 20-40 UI en perfusion. Si échec : misoprostol 800 µg sublingual/rectal, puis carboprost (Hémabate) 250 µg IM, acide tranexamique 1g IV. Revue utérine, ligatures artères utérines, hystérectomie si vital."),
        
        # Santé mentale
        ("Critères DSM-5 trouble dépressif majeur ?",
         "≥ 5 symptômes pendant ≥ 2 semaines dont 1 obligatoire : humeur dépressive OU perte d'intérêt/plaisir. Autres : perte/prise poids, insomnie/hypersomnie, agitation/ralentissement, fatigue, sentiment dévalorisation/culpabilité, trouble concentration, idées mortelles/suicide. Pertes fonctionnelles significatives."),
    ]
    
    texts = []
    for q, a in qa_pairs:
        texts.append(f"Question: {q}\nRéponse: {a}")
    
    # Variantes
    for q, a in qa_pairs[:5]:
        texts.append(f"Q: {q} R: {a}")
    
    return texts

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("═" * 70)
    print("  🏥 PRÉPARATION CORPUS MÉDICAL — HWAT-Med")
    print("═" * 70)
    
    all_texts = []
    
    # 1. Corpus vital_ka (structuré, haute qualité)
    print("\n📚 1. Extraction vital_ka_*.json...")
    vital_texts = extract_vital_ka_corpus()
    all_texts.extend(vital_texts)
    print(f"   Total vital_ka: {len(vital_texts):,} segments")
    
    # 2. Corpus clinique CSV (massif, réaliste)
    print("\n🏥 2. Extraction clinical CSV...")
    # Échantillonner pour éviter trop gros (on prendra tout pour le training final)
    clinical_texts = extract_clinical_csv(_ENGINE / "data" / "clinical" / "train.csv", max_rows=50000)
    all_texts.extend(clinical_texts)
    
    # Validation + test
    val_texts = extract_clinical_csv(_ENGINE / "data" / "clinical" / "validate.csv", max_rows=5000)
    all_texts.extend(val_texts)
    
    test_texts = extract_clinical_csv(_ENGINE / "data" / "clinical" / "test.csv", max_rows=5000)
    all_texts.extend(test_texts)
    
    print(f"   Total clinique: {len(clinical_texts) + len(val_texts) + len(test_texts):,} cas")
    
    # 3. Real clinical dataset
    print("\n📊 3. Extraction real_clinical_dataset.json...")
    real_texts = extract_real_clinical_json()
    all_texts.extend(real_texts)
    print(f"   Total real_clinical: {len(real_texts):,} segments")
    
    # 4. Q/A synthétiques pour instruction tuning
    print("\n🤖 4. Génération Q/A synthétiques...")
    qa_texts = generate_synthetic_qa()
    all_texts.extend(qa_texts)
    print(f"   Total Q/A: {len(qa_texts)} paires")
    
    # 5. Nettoyage et déduplication
    print("\n🧹 5. Nettoyage et déduplication...")
    cleaned = [clean_text(t) for t in all_texts if t and len(t) > 30]
    # Déduplication simple
    seen = set()
    unique = []
    for t in cleaned:
        h = hash(t[:200])  # Hash sur les 200 premiers chars
        if h not in seen:
            seen.add(h)
            unique.append(t)
    
    print(f"   Avant dédup: {len(cleaned):,}")
    print(f"   Après dédup: {len(unique):,}")
    
    # 6. Sauvegarde
    print("\n💾 6. Sauvegarde corpus...")
    train_path = OUTPUT_DIR / "train.txt"
    with open(train_path, 'w', encoding='utf-8') as f:
        for t in unique:
            f.write(t + "\n\n")
    
    # Split train/val (95/5)
    split_idx = int(len(unique) * 0.95)
    train_data = unique[:split_idx]
    val_data = unique[split_idx:]
    
    with open(OUTPUT_DIR / "train.txt", 'w', encoding='utf-8') as f:
        f.write("\n\n".join(train_data))
    with open(OUTPUT_DIR / "val.txt", 'w', encoding='utf-8') as f:
        f.write("\n\n".join(val_data))
    
    # Stats
    total_chars = sum(len(t) for t in unique)
    total_words = sum(len(t.split()) for t in unique)
    
    print(f"\n{'='*70}")
    print(f"  ✅ CORPUS MÉDICAL PRÊT")
    print(f"{'='*70}")
    print(f"  Fichiers: {OUTPUT_DIR}/train.txt, {OUTPUT_DIR}/val.txt")
    print(f"  Segments: {len(unique):,}")
    print(f"  Caractères: {total_chars/1e6:.1f}M")
    print(f"  Mots (est.): {total_words/1e6:.1f}M")
    print(f"  Train: {len(train_data):,} | Val: {len(val_data):,}")
    
    # Sauvegarder métadonnées
    meta = {
        'total_segments': len(unique),
        'total_chars': total_chars,
        'total_words_est': total_words,
        'train_segments': len(train_data),
        'val_segments': len(val_data),
        'sources': ['vital_ka_*.json (14)', 'clinical/train.csv (50k)', 'clinical/val.csv (5k)', 
                   'clinical/test.csv (5k)', 'real_clinical_dataset.json', 'synthetic_qa (15)'],
        'created_at': str(Path(__file__).stat().st_mtime)
    }
    with open(OUTPUT_DIR / "corpus_meta.json", 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())