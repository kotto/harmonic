#!/usr/bin/env python3
"""
SYNTHETIC QA GENERATOR — Peuplement massif de KA Phone
=========================================================
Genere automatiquement des milliers de variantes de questions
a partir de faits existants ou de nouveaux sujets.

Strategie :
  1. Templates de questions (20+ variantes par fait)
  2. Paraphrases automatiques (reformulations)
  3. Generation de questions derivees (pourquoi, comment, qui, quand, ou...)
  4. Expansion multi-langue (FR principal, EN secondaire)

Usage :
  python ka_phone/synthetic_qa_generator.py                    # Tout generer
  python ka_phone/synthetic_qa_generator.py --topic "egypte"    # Un theme
  python ka_phone/synthetic_qa_generator.py --quick             # Test (50 faits)
  python ka_phone/synthetic_qa_generator.py --output qa_massive.json
"""

import os, sys, json, re, random, hashlib, argparse
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_qa")
OUTPUT_FILE = os.path.join(DATA_DIR, "qa_synthetic_massive.json")
os.makedirs(DATA_DIR, exist_ok=True)

# Charger les faits existants
sys.path.insert(0, os.path.dirname(__file__))
try:
    from quick_facts import FACTS
    HAS_FACTS = True
except ImportError:
    HAS_FACTS = False
    FACTS = []

# ══════════════════════════════════════════════════════════════════════════
# QUESTION TEMPLATES — 30+ variantes par reponse
# ══════════════════════════════════════════════════════════════════════════

# Templates organises par type de question
QUESTION_TEMPLATES_FR = {
    "qui": [
        "Qui est {sujet} ?",
        "Qui etait {sujet} ?",
        "Peux-tu me parler de {sujet} ?",
        "Qui est la personne nommee {sujet} ?",
        "Connais-tu {sujet} ?",
        "Dis-moi qui est {sujet}",
        "J'aimerais savoir qui est {sujet}",
        "Quelle est la biographie de {sujet} ?",
    ],
    "quoi": [
        "Qu'est-ce que {sujet} ?",
        "C'est quoi {sujet} ?",
        "Que signifie {sujet} ?",
        "Peux-tu expliquer {sujet} ?",
        "Explique-moi {sujet}",
        "Quelle est la definition de {sujet} ?",
        "Je voudrais comprendre {sujet}",
        "Parle-moi de {sujet}",
        "Donne-moi des informations sur {sujet}",
    ],
    "quand": [
        "Quand a eu lieu {sujet} ?",
        "A quelle date {sujet} ?",
        "Quand est-ce que {sujet} s'est produit ?",
        "En quelle annee {sujet} ?",
        "Quelle est la date de {sujet} ?",
    ],
    "ou": [
        "Ou se trouve {sujet} ?",
        "Ou est {sujet} ?",
        "Quel pays abrite {sujet} ?",
        "Dans quelle region est {sujet} ?",
        "Peux-tu me situer {sujet} ?",
    ],
    "pourquoi": [
        "Pourquoi {sujet} est-il important ?",
        "Pourquoi {sujet} est-il celebre ?",
        "Quelle est l'importance de {sujet} ?",
        "En quoi {sujet} est-il significatif ?",
    ],
    "comment": [
        "Comment fonctionne {sujet} ?",
        "Comment ca marche, {sujet} ?",
        "Peux-tu m'expliquer comment {sujet} ?",
        "Comment se passe {sujet} ?",
    ],
    "combien": [
        "Combien de {sujet} ?",
        "Quel est le nombre de {sujet} ?",
        "Quelle quantite de {sujet} ?",
    ],
    "informel": [
        "Tu sais quoi sur {sujet} ?",
        "Des infos sur {sujet} ?",
        "{sujet}, ca te dit quelque chose ?",
        "Tu connais {sujet} ?",
        "Raconte-moi {sujet}",
    ],
}

QUESTION_TEMPLATES_EN = {
    "who": [
        "Who is {subject}?",
        "Who was {subject}?",
        "Tell me about {subject}",
        "Can you tell me who {subject} is?",
        "I want to know about {subject}",
        "What do you know about {subject}?",
    ],
    "what": [
        "What is {subject}?",
        "What does {subject} mean?",
        "Explain {subject} to me",
        "Can you explain {subject}?",
        "Tell me what {subject} is",
        "I'd like to understand {subject}",
    ],
    "when": [
        "When did {subject} happen?",
        "When was {subject}?",
        "What year did {subject} occur?",
    ],
    "where": [
        "Where is {subject}?",
        "Where can I find {subject}?",
        "What country is {subject} in?",
    ],
}

# ══════════════════════════════════════════════════════════════════════════
# SUJET EXTRACTOR — Extrait le sujet principal d'un texte
# ══════════════════════════════════════════════════════════════════════════

def extract_subject(text: str) -> str:
    """Extrait le sujet principal d'un texte de reponse."""
    # Prendre les premiers mots (avant le verbe)
    first_sentence = text.split(".")[0].strip()
    # Extraire le sujet (premier groupe nominal)
    subject = first_sentence[:80].strip()
    return subject


def extract_keyword_subject(keywords: List[str]) -> str:
    """Convertit la liste de mots-cles en sujet lisible."""
    # Prendre le mot-cle le plus long (le plus specifique)
    sorted_kw = sorted(keywords, key=len, reverse=True)
    return sorted_kw[0].capitalize()


def generate_all_subjects(text: str, keywords: List[str]) -> List[str]:
    """
    Genere plusieurs sujets possibles a partir d'un texte et de mots-cles.
    Ex: text="Paris est la capitale de la France", keywords=["capitale","france","paris"]
    → ["Paris", "la capitale de la France", "la France"]
    """
    subjects = []

    # Sujet 1 : Premier mot-cle long
    if keywords:
        sorted_kw = sorted(keywords, key=len, reverse=True)
        subjects.append(sorted_kw[0])

    # Sujet 2 : Premier groupe nominal du texte
    first_part = text.split(",")[0].split(".")[0].split(":")
    if len(first_part) >= 1:
        sujet = first_part[-1].strip()[:60]
        if sujet and len(sujet) > 3:
            subjects.append(sujet)

    # Sujet 3 : Mot-cle suivant si disponible
    if len(sorted_kw) > 1:
        subjects.append(sorted_kw[1])

    # Sujet 4 : Dernier mot-cle
    if len(sorted_kw) > 2:
        subjects.append(sorted_kw[-1])

    return list(dict.fromkeys(subjects))  # dedupe en preservant l'ordre


# ══════════════════════════════════════════════════════════════════════════
# GENERATEUR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════

class SyntheticQAGenerator:
    """
    Genere des paires QA synthetiques a partir de faits existants
    ou de nouveaux sujets.
    """

    def __init__(self):
        self.qa_pairs = []
        self.stats = {"total_generated": 0, "by_template": {}, "by_domain": {}}

    def generate_from_facts(self, facts: List[Tuple], max_per_fact: int = 30,
                            languages: List[str] = None) -> List[Dict]:
        """
        Genere des variantes de questions pour chaque fait.

        Args:
            facts: Liste de (id, text, keywords)
            max_per_fact: Nombre max de variantes par fait
            languages: ['fr', 'en'] ou ['fr']

        Returns:
            Liste de paires QA
        """
        if languages is None:
            languages = ["fr", "en"]

        self.qa_pairs = []
        total_facts = len(facts)

        for i, (fact_id, text, keywords) in enumerate(facts):
            # Extraire les sujets possibles
            subjects = generate_all_subjects(text, keywords)

            # Generer des questions francaises
            for sujet in subjects[:3]:  # Max 3 sujets par fait
                fr_questions = self._generate_question_variants(sujet, "fr")
                for q in fr_questions:
                    if len(self.qa_pairs) - (i * max_per_fact // len(subjects)) < max_per_fact:
                        self.qa_pairs.append({
                            "question": q,
                            "answer": text,
                            "language": "fr",
                            "domain": self._infer_domain_from_keywords(keywords),
                            "source_fact": fact_id,
                            "generated": True,
                            "kx": round(hashlib.sha256(q.encode()).hexdigest()[:16], 6) if False else 0,
                        })

            # Generer des questions anglaises
            for sujet in subjects[:2]:
                en_questions = self._generate_question_variants(sujet, "en")
                for q in en_questions[:max_per_fact // 4]:
                    self.qa_pairs.append({
                        "question": q,
                        "answer": text,  # Answer stays in FR for now (could translate later)
                        "language": "en",
                        "domain": self._infer_domain_from_keywords(keywords),
                        "source_fact": fact_id,
                        "generated": True,
                    })

            if (i + 1) % 50 == 0:
                print(f"  [{i+1}/{total_facts}] {len(self.qa_pairs)} questions generees...")

        self.stats["total_generated"] = len(self.qa_pairs)
        return self.qa_pairs

    def generate_from_topic(self, topic: str, answer: str, keywords: List[str] = None,
                            variants: int = 20, languages: List[str] = None) -> List[Dict]:
        """
        Genere des variantes pour un nouveau sujet/theme.

        Args:
            topic: Le sujet (ex: "la Grande Muraille de Chine")
            answer: La reponse factuelle
            keywords: Mots-cles associes
            variants: Nombre de variantes souhaitees
        """
        if languages is None:
            languages = ["fr"]
        if keywords is None:
            keywords = [topic]

        pairs = []
        for _ in range(variants):
            q_fr = random.choice(list(QUESTION_TEMPLATES_FR.values()))
            q_fr_template = random.choice(q_fr)
            q = q_fr_template.format(sujet=topic)
            pairs.append({
                "question": q,
                "answer": answer,
                "language": "fr",
                "domain": self._infer_domain_from_keywords(keywords),
                "source_topic": topic,
                "generated": True,
            })
        return pairs

    def _generate_question_variants(self, sujet: str, langue: str) -> List[str]:
        """Genere toutes les variantes de questions pour un sujet dans une langue."""
        templates = QUESTION_TEMPLATES_FR if langue == "fr" else QUESTION_TEMPLATES_EN
        variants = []

        # 1 variante aleatoire par categorie de template
        for category, tmpl_list in templates.items():
            if tmpl_list:
                tmpl = random.choice(tmpl_list)
                try:
                    q = tmpl.format(sujet=sujet, subject=sujet)
                    variants.append(q)
                except KeyError:
                    pass

        # Ajouter des variantes aleatoires supplementaires
        for _ in range(5):
            category = random.choice(list(templates.keys()))
            tmpl = random.choice(templates[category])
            try:
                q = tmpl.format(sujet=sujet, subject=sujet)
                if q not in variants:
                    variants.append(q)
            except KeyError:
                pass

        return variants

    def _infer_domain_from_keywords(self, keywords: List[str]) -> str:
        """Devinne le domaine a partir des mots-cles."""
        domain_map = {
            "egypte": "egypte_ancienne", "pharaon": "egypte_ancienne", "kemet": "egypte_ancienne",
            "nubie": "egypte_ancienne", "koush": "egypte_ancienne", "pyramide": "egypte_ancienne",
            "dynastie": "egypte_ancienne", "dieu": "egypte_ancienne", "osiris": "egypte_ancienne",
            "capitale": "geographie", "pays": "geographie", "france": "geographie",
            "population": "geographie", "continent": "geographie", "superficie": "geographie",
            "guerre": "histoire", "revolution": "histoire", "napoleon": "histoire",
            "roi": "histoire", "empereur": "histoire",
            "sport": "sport_loisirs", "football": "sport_loisirs", "joueur": "sport_loisirs",
            "musique": "musique_arts", "peintre": "musique_arts", "film": "pop_culture",
            "cuisine": "cuisine_gastronomie", "vin": "cuisine_gastronomie", "recette": "cuisine_gastronomie",
            "economie": "economie_finances", "budget": "economie_finances", "euro": "economie_finances",
            "sante": "sante", "medecin": "medecine", "maladie": "medecine",
            "sommeil": "psychologie_bienetre", "stress": "psychologie_bienetre", "dormir": "psychologie_bienetre",
            "science": "sciences", "physique": "sciences", "chimie": "sciences",
            "planete": "sciences", "soleil": "sciences", "lumiere": "sciences",
            "internet": "technologie", "ordinateur": "technologie",
            "conseil": "conseil_pratique", "investir": "economie_finances",
        }
        for kw in keywords:
            if kw.lower() in domain_map:
                return domain_map[kw.lower()]
        return "general"

    def save(self, output_file: str = OUTPUT_FILE):
        """Sauvegarde les QA generees."""
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.qa_pairs, f, ensure_ascii=False, indent=2)
        print(f"\n  Sauvegarde : {len(self.qa_pairs)} paires QA dans {output_file}")

    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "total_qa": len(self.qa_pairs),
            "languages": list(set(qa.get("language", "fr") for qa in self.qa_pairs)),
            "domains": list(set(qa.get("domain", "general") for qa in self.qa_pairs)),
        }


# ══════════════════════════════════════════════════════════════════════════
# EXPANSION MASSIVE — Generation de "pourquoi", "comment", etc.
# ══════════════════════════════════════════════════════════════════════════

def generate_derived_questions(fact_text: str, fact_keywords: List[str]) -> List[Tuple[str, str]]:
    """
    Genere des questions derivees (pourquoi, comment, etc.) a partir d'un fait.
    L'idee est d'utiliser le fait comme reponse a de nouvelles questions.
    """
    derived = []
    sujet = " ".join(fact_keywords[:2])

    # "Pourquoi X ?" → le fait explique l'importance
    derived.append((f"Pourquoi {sujet} est-il important ?", fact_text))
    derived.append((f"Pourquoi {sujet} est-il connu ?", fact_text))

    # "Quelle est la particularite de X ?"
    derived.append((f"Quelle est la particularite de {sujet} ?", fact_text))

    # "Peux-tu me donner des details sur X ?"
    derived.append((f"Peux-tu me donner des details sur {sujet} ?", fact_text))

    return derived


# ══════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Synthetic QA Generator — Peuplement massif de KA Phone",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python ka_phone/synthetic_qa_generator.py                    # Tout generer (200 faits -> 5000+ QA)
  python ka_phone/synthetic_qa_generator.py --topic "egypte"   # Theme specifique
  python ka_phone/synthetic_qa_generator.py --quick            # Test rapide (20 faits)
  python ka_phone/synthetic_qa_generator.py --max 50           # 50 questions par fait
  python ka_phone/synthetic_qa_generator.py --output qa_massive.json
        """
    )

    parser.add_argument("--quick", action="store_true", help="Mode test rapide (20 faits)")
    parser.add_argument("--topic", type=str, default=None,
                       help="Theme/filtre (ex: egypte, cuisine, sport)")
    parser.add_argument("--max", type=int, default=30,
                       help="Nombre max de variantes par fait (defaut: 30)")
    parser.add_argument("--output", type=str, default=OUTPUT_FILE,
                       help="Fichier de sortie")
    parser.add_argument("--languages", type=str, default="fr,en",
                       help="Langues (fr,en)")
    parser.add_argument("--no-derived", action="store_true",
                       help="Ne pas generer de questions derivees")

    args = parser.parse_args()

    languages = [l.strip() for l in args.languages.split(",")]
    gen = SyntheticQAGenerator()

    if HAS_FACTS:
        # Filtrer par theme
        if args.topic:
            facts = [(fid, text, kw) for fid, text, kw in FACTS
                     if args.topic.lower() in text.lower()
                     or any(args.topic.lower() in k.lower() for k in kw)]
            print(f"  Theme '{args.topic}' : {len(facts)} faits correspondants sur {len(FACTS)}")
        elif args.quick:
            facts = FACTS[:20]
            print(f"  Mode rapide : 20 faits")
        else:
            facts = FACTS
            print(f"  Total : {len(facts)} faits")

        print(f"  Max variantes/fait : {args.max}")
        print(f"  Langues : {languages}")
        print(f"  Questions derivees : {'non' if args.no_derived else 'oui'}")
        print(f"\n  Generation en cours...")

        # Phase 1 : Variantes directes
        gen.generate_from_facts(facts, max_per_fact=args.max, languages=languages)

        # Phase 2 : Questions derivees
        if not args.no_derived:
            derived_count = 0
            for fact_id, text, keywords in facts:
                derived = generate_derived_questions(text, keywords)
                for q, a in derived:
                    gen.qa_pairs.append({
                        "question": q,
                        "answer": a,
                        "language": "fr",
                        "domain": gen._infer_domain_from_keywords(keywords),
                        "source_fact": fact_id,
                        "derived": True,
                        "generated": True,
                    })
                    derived_count += 1
            print(f"  Questions derivees ajoutees : {derived_count}")

    else:
        print("  Aucun fait QuickFacts trouve. Genereration minimale.")
        gen.qa_pairs = []

    # Sauvegarde
    gen.save(args.output)

    # Stats
    stats = gen.get_stats()
    print(f"\n  === STATISTIQUES ===")
    print(f"  QA generees      : {stats['total_qa']}")
    print(f"  Langues          : {stats['languages']}")
    domain_counts = {}
    for qa in gen.qa_pairs:
        d = qa.get("domain", "general")
        domain_counts[d] = domain_counts.get(d, 0) + 1
    print(f"  Domaines         :")
    for d, c in sorted(domain_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"    - {d}: {c}")

    print(f"\n  [OK] Fichier pret : {args.output}")


if __name__ == "__main__":
    main()