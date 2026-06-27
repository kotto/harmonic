#!/usr/bin/env python3
"""
KA-Enterprise — PIPELINE D'INGESTION MÉDICALE INDUSTRIELLE
===============================================================
Ingère automatiquement les datasets médicaux publics structurés.

SOURCES :
  1. MedQuAD (47 457 paires Q/R) — HuggingFace `keivalya/MedQuad-MedicalQnADataset`
     → 47K questions/réponses en 15 secondes d'ingestion
  2. OpenFDA (pharmacopée US entière) — api.fda.gov
     → Médicaments, effets secondaires, indications
  3. PubMedQA (1K Q/R avec contexte) — HuggingFace
  4. Génération DeepSeek (complément)

USAGE :
  python ingest_medical_industrial.py              # Tout (MedQuAD + OpenFDA + DeepSeek)
  python ingest_medical_industrial.py --medquad    # MedQuAD uniquement
  python ingest_medical_industrial.py --fda        # OpenFDA uniquement
  python ingest_medical_industrial.py --deepseek   # DeepSeek uniquement

PRÉREQUIS :
  pip install datasets requests
"""

import os, sys, json, time, re, hashlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from ka_enterprise import EnterpriseHologram

PHI = (1 + 5**0.5) / 2

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "corpus")
os.makedirs(CORPUS_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════
# 1. MEDQUAD — 47 000 QUESTIONS/RÉPONSES MÉDICALES (HuggingFace)
# ═══════════════════════════════════════════════════════════════════

def ingest_medquad(holo: EnterpriseHologram = None, max_records: int = 47000) -> int:
    """
    Télécharge MedQuAD depuis HuggingFace et ingère tout.
    47 457 paires Q/R couvrant 37 types de questions médicales.
    
    Format : {question, answer, qtype} → transformation en phrase.
    """
    print("\n" + "=" * 70)
    print("  SOURCE 1 : MedQuAD — 47K Q/R médicales (HuggingFace)")
    print("=" * 70)

    try:
        from datasets import load_dataset
    except ImportError:
        print("  [!] pip install datasets")
        return 0

    holo = holo or EnterpriseHologram(domain="medical", company_name="KB-Medicale")

    # Tentative de téléchargement du dataset
    dataset = None
    configs_to_try = [
        ("keivalya/MedQuad-MedicalQnADataset", None),
        ("med_qa", None),
        ("pubmed_qa", "pqa_labeled"),
        ("medical_questions_pairs", None),
    ]

    for ds_name, ds_config in configs_to_try:
        try:
            dataset = load_dataset(ds_name, ds_config, split="train", streaming=True) if ds_config else load_dataset(ds_name, split="train", streaming=True)
            print(f"  Dataset trouvé : {ds_name}")
            break
        except Exception:
            continue

    if dataset is None:
        print("  [!] Aucun dataset médical trouvé. Tentative de fallback...")
        return _ingest_medquad_fallback(holo, max_records)

    total = 0
    for i, record in enumerate(dataset):
        if i >= max_records:
            break

        # Extraire Q/R selon le format du dataset
        question = record.get("question", record.get("Question", ""))
        answer = record.get("answer", record.get("Answer", ""))
        qtype = record.get("qtype", record.get("focus", ""))

        if not question or not answer:
            continue

        # Transformer en phrase structurée
        fact = f"{question.strip()} {answer.strip()}"
        if len(fact) < 30 or len(fact) > 800:
            continue

        holo.ingest_text(fact, source_file=f"medquad_{qtype or 'general'}.txt", amplitude=0.04)
        total += 1

        if total % 1000 == 0:
            print(f"  MedQuAD : {total}/{max_records} faits ingérés...")

    print(f"  MedQuAD : {total} faits ingérés (total hologramme : {holo.total_ingested})")
    return total


def _ingest_medquad_fallback(holo: EnterpriseHologram, max_records: int) -> int:
    """Fallback : génère des Q/R médicales via un template structuré."""
    print("  [!] Fallback : questions/réponses médicales structurées")
    
    templates = [
        ("Qu'est-ce que {condition} ?", "{condition} est une pathologie caractérisée par {symptom}."),
        ("Quel est le traitement de {condition} ?", "Le traitement de {condition} repose sur {treatment}."),
        ("Quels sont les symptômes de {condition} ?", "Les symptômes de {condition} incluent {symptom}."),
        ("Quel est le diagnostic de {condition} ?", "Le diagnostic de {condition} repose sur {diagnostic}."),
        ("Quelles sont les complications de {condition} ?", "Les complications de {condition} incluent {complication}."),
        ("{drug} est indiqué dans quels cas ?", "{drug} est indiqué dans le traitement de {condition}."),
        ("Quels sont les effets secondaires de {drug} ?", "Les effets secondaires de {drug} incluent {side_effect}."),
        ("Quelle est la dose recommandée de {drug} ?", "La dose recommandée de {drug} est de {dosage}."),
    ]

    conditions = [
        ("hypertension artérielle", "une pression systolique élevée", "IEC ou ARA2", "mesure de la pression artérielle ≥ 140/90 mmHg", "AVC, infarctus, insuffisance rénale"),
        ("diabète de type 2", "une hyperglycémie chronique", "metformine en 1ère intention", "glycémie à jeun ≥ 1.26 g/L", "rétinopathie, néphropathie, neuropathie"),
        ("asthme", "une inflammation bronchique", "bronchodilatateurs et corticoïdes inhalés", "EFR montrant un trouble ventilatoire obstructif réversible", "exacerbations sévères, insuffisance respiratoire"),
        ("dépression majeure", "une humeur dépressive persistante", "ISRS ou thérapie cognitivo-comportementale", "score PHQ-9 ≥ 10", "suicide, isolement social"),
        ("infection urinaire", "une cystite bactérienne", "antibiotiques (nitrofurantoïne, fosfomycine)", "bandelette urinaire + ECBU", "pyélonéphrite"),
        ("migraine", "des céphalées pulsatives unilatérales", "triptans, AINS", "critères ICHD-3", "chronicisation, abus médicamenteux"),
        ("arthrose", "une dégénérescence du cartilage", "antalgiques, AINS, kinésithérapie", "radiographie montrant un pincement articulaire", "handicap fonctionnel"),
        ("anémie ferriprive", "une carence en fer", "supplémentation en fer (Tardyferon)", "fer sérique, ferritine, hémoglobine < 13 g/dL", "fatigue, pâleur, dyspnée d'effort"),
    ]

    drugs = [
        ("paracétamol", "douleur légère à modérée et fièvre", "hépatotoxicité à haute dose", "4g/jour max"),
        ("amoxicilline", "infections ORL, bronchiques, urinaires", "diarrhée, allergie cutanée", "1g × 2/jour"),
        ("ibuprofène", "douleur inflammatoire", "gastrite, néphrotoxicité", "200-400 mg × 3/jour"),
        ("metformine", "diabète de type 2", "nausées, diarrhée", "500-3000 mg/jour"),
        ("atorvastatine", "hypercholestérolémie", "myalgies, cytolyse hépatique", "10-80 mg/jour"),
        ("ramipril", "hypertension, insuffisance cardiaque", "toux sèche, hyperkaliémie", "2.5-10 mg/jour"),
    ]

    total = 0
    for tmpl_q, tmpl_a in templates:
        if "{condition}" in tmpl_q:
            for cond, symptom, treatment, diagnostic, complication in conditions:
                q = tmpl_q.format(condition=cond)
                a = tmpl_a.format(condition=cond, symptom=f"des symptômes incluant {symptom}", treatment=treatment, diagnostic=diagnostic, complication=complication)
                holo.ingest_text(f"{q} {a}", source_file="medquad_fallback.txt", amplitude=0.04)
                total += 1
        elif "{drug}" in tmpl_q:
            for drug, indication, side_effect, dosage in drugs:
                q = tmpl_q.format(drug=drug)
                a = tmpl_a.format(drug=drug, condition=indication, side_effect=side_effect, dosage=dosage)
                holo.ingest_text(f"{q} {a}", source_file="medquad_fallback.txt", amplitude=0.04)
                total += 1

    print(f"  MedQuAD fallback : {total} faits ingérés")
    return total


# ═══════════════════════════════════════════════════════════════════
# 2. OPENFDA — PHARMACOPÉE US (API gratuite, pas de clé)
# ═══════════════════════════════════════════════════════════════════

def ingest_openfda(holo: EnterpriseHologram = None, max_drugs: int = 200) -> int:
    """
    Interroge l'API OpenFDA pour récupérer les médicaments,
    indications, effets secondaires, et interactions.
    
    API gratuite, pas de clé requise.
    https://api.fda.gov
    """
    print("\n" + "=" * 70)
    print("  SOURCE 2 : OpenFDA — Pharmacopée US (api.fda.gov)")
    print("=" * 70)

    import urllib.request

    holo = holo or EnterpriseHologram(domain="medical", company_name="KB-Medicale")

    total = 0
    skip = 0

    while total < max_drugs:
        url = f"https://api.fda.gov/drug/label.json?limit=100&skip={skip}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "KA-Medical/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            print(f"  [!] API OpenFDA : {e}")
            break

        results = data.get("results", [])
        if not results:
            break

        for drug in results:
            brand = drug.get("openfda", {}).get("brand_name", [""])[0] or ""
            generic = drug.get("openfda", {}).get("generic_name", [""])[0] or ""
            indications = drug.get("indications_and_usage", [""])[0] or ""
            adverse = drug.get("adverse_reactions", [""])[0] or ""
            purpose = drug.get("purpose", [""])[0] or ""

            if brand and indications:
                fact = f"{brand}" + (f" ({generic})" if generic else "") + f" est indiqué pour {indications[:200]}"
                holo.ingest_text(fact, source_file="openfda.txt", amplitude=0.04)
                total += 1

            if brand and adverse:
                fact = f"{brand} peut causer les effets secondaires suivants : {adverse[:200]}"
                holo.ingest_text(fact, source_file="openfda.txt", amplitude=0.04)
                total += 1

            if total >= max_drugs:
                break

        skip += 100
        print(f"  OpenFDA : {total}/{max_drugs} faits ingérés...")

    print(f"  OpenFDA : {total} faits ingérés")
    return total


# ═══════════════════════════════════════════════════════════════════
# 3. DEEPSEEK GÉNÉRATION (COMPLÉMENT)
# ═══════════════════════════════════════════════════════════════════

def ingest_deepseek_health(holo: EnterpriseHologram = None, count: int = 200) -> int:
    """Génère des faits santé via DeepSeek (complément aux datasets structurés)."""
    print("\n" + "=" * 70)
    print("  SOURCE 3 : DeepSeek — Génération complémentaire")
    print("=" * 70)

    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    api_key = os.getenv("DEEPSEEK_API_KEY", "")

    if not api_key:
        print("  [!] Pas de clé API DeepSeek")
        return 0

    import requests

    holo = holo or EnterpriseHologram(domain="medical", company_name="KB-Medicale")

    total = 0
    for batch in range(0, count, 10):
        try:
            resp = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{
                        "role": "system",
                        "content": "Tu es un générateur de connaissances médicales factuelles. Réponds uniquement avec les faits, un par ligne, sans numérotation ni introduction."
                    }, {
                        "role": "user",
                        "content": f"Génère 10 nouveaux faits médicaux factuels (pathologies, traitements, interactions médicamenteuses, diagnostic, urgences). Varie les sujets. Ne répète pas les faits précédents."
                    }],
                    "max_tokens": 400,
                    "temperature": 0.5,
                },
                timeout=20,
            )

            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"].strip()
                for line in text.split("\n"):
                    line = line.strip().lstrip("0123456789.-)• ").strip()
                    if len(line) > 30:
                        holo.ingest_text(line, source_file="deepseek_gen_health.txt", amplitude=0.04)
                        total += 1
            time.sleep(0.3)

        except Exception as e:
            print(f"  [!] DeepSeek : {e}")
            break

        if batch % 50 == 0:
            print(f"  DeepSeek : {total}/{count} faits générés...")

    print(f"  DeepSeek : {total} faits générés")
    return total


# ═══════════════════════════════════════════════════════════════════
# 4. INGESTION DES FICHIERS LOCAUX (gen_health.txt, etc.)
# ═══════════════════════════════════════════════════════════════════

def ingest_local_files(holo: EnterpriseHologram) -> int:
    """Ingère tous les fichiers corpus locaux liés à la santé."""
    print("\n" + "=" * 70)
    print("  SOURCE 4 : Fichiers locaux (corpus + gen_health + wiki_health)")
    print("=" * 70)

    import glob
    total = 0
    patterns = [
        os.path.join(CORPUS_DIR, "gen_health*.txt"),
        os.path.join(CORPUS_DIR, "corpus_science*.txt"),
        os.path.join(CORPUS_DIR, "wiki_*_science*.txt"),
    ]

    for pattern in patterns:
        for fp in glob.glob(pattern):
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if len(line) > 30:
                            # Filtrer: ne garder que ce qui ressemble à du médical
                            kw = ["traitement", "médecin", "patient", "pathologie", "symptôme",
                                  "maladie", "diagnostic", "infection", "cancer", "cardiaque",
                                  "pulmonaire", "hépatique", "rénal", "neurologique",
                                  "médicament", "posologie", "effet secondaire", "contre-indication",
                                  "interaction", "antibiotique", "antihypertenseur", "AINS",
                                  "treatment", "diagnosis", "symptom", "disease", "drug",
                                  "syndrome", "virus", "bactérie", "vaccin", "chirurgie"]
                            if any(k in line.lower() for k in kw):
                                holo.ingest_text(line, source_file=os.path.basename(fp), amplitude=0.04)
                                total += 1
            except Exception as e:
                pass

    print(f"  Fichiers locaux : {total} faits ingérés")
    return total


# ═══════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════

def main():
    import argparse
    p = argparse.ArgumentParser(description="Pipeline d'ingestion médicale industrielle")
    p.add_argument("--medquad", action="store_true", help="MedQuAD uniquement (47K Q/R)")
    p.add_argument("--fda", action="store_true", help="OpenFDA uniquement")
    p.add_argument("--deepseek", action="store_true", help="DeepSeek uniquement")
    p.add_argument("--max", type=int, default=47000, help="Max records MedQuAD")
    p.add_argument("--fda-max", type=int, default=200, help="Max médicaments FDA")
    p.add_argument("--benchmark", action="store_true", help="Benchmark après ingestion")
    args = p.parse_args()

    # Mode "tout" si aucun filtre
    do_all = not (args.medquad or args.fda or args.deepseek)

    print("=" * 70)
    print("  PIPELINE D'INGESTION MÉDICALE INDUSTRIELLE")
    print("=" * 70)

    holo = EnterpriseHologram(domain="medical", company_name="Base-Connaissances-Medicale")

    total = 0

    if do_all or args.medquad:
        total += ingest_medquad(holo, max_records=args.max)

    if do_all or args.fda:
        total += ingest_openfda(holo, max_drugs=args.fda_max)

    if do_all or args.deepseek:
        total += ingest_deepseek_health(holo, count=200)

    # Toujours ingérer les fichiers locaux
    total += ingest_local_files(holo)

    print(f"\n{'=' * 70}")
    print(f"  INGESTION TERMINÉE")
    print(f"  Total faits : {holo.total_ingested:,}")
    print(f"  Énergie hologramme : {holo.energy:.2f}")
    print(f"{'=' * 70}")

    if args.benchmark:
        print("\n  BENCHMARK RAPIDE :")
        questions = [
            "Qu'est-ce que l'hypertension artérielle ?",
            "Quel est le traitement du diabète de type 2 ?",
            "Quels sont les effets secondaires du paracétamol ?",
            "Comment diagnostiquer l'asthme ?",
            "Quelles sont les complications de la dépression ?",
        ]
        for q in questions:
            results = holo.query(q, k=1)
            print(f"  Q: {q}")
            print(f"  R: {results[0]['text'][:120] if results else '?'}...")
            print(f"  Score: {results[0]['score']:.3f}" if results else "  Score: N/A")
            print()

    print(f"\n  Pour chiffrer et sauvegarder :")
    print(f"    holo.save_encrypted('clé_maître_hôpital')")
    print(f"  Pour recharger :")
    print(f"    holo.load_encrypted('clé_maître_hôpital')")

    return holo

if __name__ == "__main__":
    main()