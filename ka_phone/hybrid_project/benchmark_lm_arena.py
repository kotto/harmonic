#!/usr/bin/env python3
"""
LM ARENA BENCHMARK — KA HYBRID Configuration (Hologramme + DeepSeek)
=====================================================================
Benchmark style LM Arena sur 200 questions aleatoires.
Evalue :
  - Tracabilite (trace_score)
  - Hallucinations detectees
  - Temps de reponse
  - Couverture des faits
  - Performance par domaine

Usage :
  python benchmark_lm_arena.py              # Benchmark complet (200 questions)
  python benchmark_lm_arena.py --quick 20   # Test rapide (20 questions)
  python benchmark_lm_arena.py --report     # Afficher le dernier rapport
"""

import os, sys, json, time, random, math
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Tuple

BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR.parent))
sys.path.insert(0, str(BASE_DIR))

RESULTS_FILE = BASE_DIR / "benchmark_results.json"
REPORT_FILE = BASE_DIR / "benchmark_report.md"

# ==============================================================================
# 200 QUESTIONS REPARTIES PAR DOMAINE
# ==============================================================================

LM_ARENA_QUESTIONS = [
    # === GEOGRAPHIE (20) ===
    ("Quelle est la capitale du Senegal ?", "geography"),
    ("Quelle est la capitale du Japon ?", "geography"),
    ("Ou se trouve le fleuve Amazone ?", "geography"),
    ("Quel est le plus grand pays du monde ?", "geography"),
    ("Combien de continents y a-t-il ?", "geography"),
    ("Quelle est la capitale du Bresil ?", "geography"),
    ("Ou se trouve le desert du Sahara ?", "geography"),
    ("Quel ocean borde la cote ouest de l'Afrique ?", "geography"),
    ("Quelle est la plus haute montagne du monde ?", "geography"),
    ("Quel pays a le plus d'habitants ?", "geography"),
    ("Ou se trouve la mer Morte ?", "geography"),
    ("Quelle est la capitale de l'Australie ?", "geography"),
    ("Combien de pays y a-t-il en Afrique ?", "geography"),
    ("Quel est le plus petit pays du monde ?", "geography"),
    ("Ou se trouve le fleuve Nil ?", "geography"),
    ("Quelle est la capitale du Canada ?", "geography"),
    ("Quel pays est connu comme le toit du monde ?", "geography"),
    ("Ou se trouve la foret amazonienne ?", "geography"),
    ("Quelle est la capitale de l'Inde ?", "geography"),
    ("Quel est le plus grand ocean du monde ?", "geography"),

    # === MATHEMATIQUES (30) ===
    ("Combien font 15 x 8 ?", "math"),
    ("Quelle est la racine carree de 256 ?", "math"),
    ("Combien font 144 / 12 ?", "math"),
    ("Quelle est la derivee de x^3 ?", "math"),
    ("Combien font 7^3 ?", "math"),
    ("Quel est le PGCD de 48 et 36 ?", "math"),
    ("Combien font 1 + 2 + 3 + ... + 10 ?", "math"),
    ("Quelle est l'integrale de sin(x) ?", "math"),
    ("Combien font 99 + 1 ?", "math"),
    ("Quel est 25% de 200 ?", "math"),
    ("Combien font 1000 / 25 ?", "math"),
    ("Quelle est la derivee de cos(x) ?", "math"),
    ("Combien font 2^10 ?", "math"),
    ("Quel est le determinant de [[1,2],[3,4]] ?", "math"),
    ("Combien font 5! ?", "math"),
    ("Quelle est la formule du discriminant ?", "math"),
    ("Combien font 17 x 13 ?", "math"),
    ("Quelle est la limite de sin(x)/x quand x tend vers 0 ?", "math"),
    ("Combien font 999 + 1 ?", "math"),
    ("Quel est le PPCM de 12 et 18 ?", "math"),
    ("Combien font 10^6 ?", "math"),
    ("Quelle est la derivee de ln(x) ?", "math"),
    ("Combien font 3.14 x 100 ?", "math"),
    ("Quel est 10% de 500 ?", "math"),
    ("Combien font 64 / 8 ?", "math"),
    ("Quelle est l'integrale de 1/x ?", "math"),
    ("Combien font 13^2 ?", "math"),
    ("Quel est le nombre d'or (phi) ?", "math"),
    ("Combien font 2 + 2 x 2 ?", "math"),
    ("Quelle est la somme des angles d'un triangle ?", "math"),

    # === HISTOIRE (20) ===
    ("Qui etait Napoleon Bonaparte ?", "history"),
    ("En quelle annee a eu lieu la Revolution francaise ?", "history"),
    ("Qui a decouvert l'Amerique ?", "history"),
    ("Qu'est-ce que l'Empire du Mali ?", "history"),
    ("Quand a eu lieu la Seconde Guerre mondiale ?", "history"),
    ("Qui etait Jules Cesar ?", "history"),
    ("Qu'est-ce que la Renaissance ?", "history"),
    ("Qui a ecrit l'Iliade et l'Odyssee ?", "history"),
    ("Quand est tombe l'Empire romain ?", "history"),
    ("Qui etait Cleopatre ?", "history"),
    ("Qu'est-ce que la revolution industrielle ?", "history"),
    ("Qui etait Martin Luther King ?", "history"),
    ("Quand a eu lieu la Premiere Guerre mondiale ?", "history"),
    ("Qui etait Charlemagne ?", "history"),
    ("Qu'est-ce que la route de la soie ?", "history"),
    ("Qui etait Albert Einstein ?", "history"),
    ("Quand a ete abolie l'esclavage aux Etats-Unis ?", "history"),
    ("Qui etait Genghis Khan ?", "history"),
    ("Qu'est-ce que la guerre froide ?", "history"),
    ("Qui a peint la Joconde ?", "history"),

    # === SCIENCES (30) ===
    ("Qu'est-ce que la gravite ?", "science"),
    ("Quelle est la vitesse de la lumiere ?", "science"),
    ("Qu'est-ce que l'ADN ?", "science"),
    ("Comment fonctionne la photosynthese ?", "science"),
    ("Qu'est-ce qu'un atome ?", "science"),
    ("Quelle est la formule de l'eau ?", "science"),
    ("Qu'est-ce que la relativite ?", "science"),
    ("Comment fonctionne un ordinateur ?", "science"),
    ("Qu'est-ce que le changement climatique ?", "science"),
    ("Comment se forment les volcans ?", "science"),
    ("Qu'est-ce que la fission nucleaire ?", "science"),
    ("Comment fonctionne le systeme immunitaire ?", "science"),
    ("Qu'est-ce qu'un trou noir ?", "science"),
    ("Quelle est la temperature du soleil ?", "science"),
    ("Comment fonctionne un moteur electrique ?", "science"),
    ("Qu'est-ce que la theorie de l'evolution ?", "science"),
    ("Comment se forment les arc-en-ciel ?", "science"),
    ("Qu'est-ce que l'effet de serre ?", "science"),
    ("Comment fonctionne un telephone portable ?", "science"),
    ("Qu'est-ce que la radioactivite ?", "science"),
    ("Comment fonctionne le coeur humain ?", "science"),
    ("Qu'est-ce que la tectonique des plaques ?", "science"),
    ("Comment fonctionne une batterie ?", "science"),
    ("Qu'est-ce que l'energie nucleaire ?", "science"),
    ("Comment fonctionne Internet ?", "science"),
    ("Qu'est-ce que l'effet Doppler ?", "science"),
    ("Comment fonctionne un micro-ondes ?", "science"),
    ("Qu'est-ce que la matiere noire ?", "science"),
    ("Comment fonctionne le cerveau humain ?", "science"),
    ("Qu'est-ce que la mecanique quantique ?", "science"),

    # === CULTURE & ARTS (15) ===
    ("Qu'est-ce que le jazz ?", "culture"),
    ("Qui etait William Shakespeare ?", "culture"),
    ("Qu'est-ce que la philosophie ?", "culture"),
    ("Qui etait Frida Kahlo ?", "culture"),
    ("Qu'est-ce que l'impressionnisme ?", "culture"),
    ("Qui etait Mozart ?", "culture"),
    ("Qu'est-ce que le cubisme ?", "culture"),
    ("Qui etait Socrate ?", "culture"),
    ("Qu'est-ce que la tragedie grecque ?", "culture"),
    ("Qui etait Nelson Mandela ?", "culture"),
    ("Qu'est-ce que le cinema muet ?", "culture"),
    ("Qui etait Marie Curie ?", "culture"),
    ("Qu'est-ce que la poesie ?", "culture"),
    ("Qui a ecrit Les Miserables ?", "culture"),
    ("Qu'est-ce que le surralisme ?", "culture"),

    # === LOGIQUE & RAISONNEMENT (15) ===
    ("Si tous les hommes sont mortels et que Socrate est un homme, que peut-on conclure ?", "logic"),
    ("Si A implique B et B implique C, qu'implique A ?", "logic"),
    ("Est-ce que la negation de tous les chats sont noirs est aucun chat n'est noir ?", "logic"),
    ("Si un train roule a 100 km/h pendant 3h, quelle distance parcourt-il ?", "logic"),
    ("Dans une piece, il y a 5 personnes. Chacune serre la main de toutes les autres. Combien de poignees de main ?", "logic"),
    ("Un boulanger vend 3 baguettes pour 2 euros. Combien coutent 12 baguettes ?", "logic"),
    ("Si je suis plus grand que Paul et Paul est plus grand que Marie, qui est le plus petit ?", "logic"),
    ("Combien y a-t-il de secondes dans une heure ?", "logic"),
    ("Si un robinet remplit un bassin en 4h et un autre en 6h, combien de temps pour le remplir ensemble ?", "logic"),
    ("Un escargot monte un mur de 10m. Il monte 3m le jour et descend 2m la nuit. Combien de jours ?", "logic"),
    ("Si 5 machines produisent 5 pieces en 5 minutes, combien de pieces produisent 10 machines en 10 minutes ?", "logic"),
    ("Un nombre est multiple de 3 et de 5. Est-il forcement multiple de 15 ?", "logic"),
    ("Si je divise 100 par un demi et j'ajoute 50, combien obtiens-je ?", "logic"),
    ("Dans une course, je double le deuxieme. Quelle est ma position ?", "logic"),
    ("Un pere a 30 ans de plus que son fils. Dans 5 ans, il aura 3 fois son age. Quel age a le fils ?", "logic"),

    # === PROGRAMMATION & IA (10) ===
    ("Qu'est-ce qu'un algorithme ?", "programming"),
    ("Qu'est-ce que Python ?", "programming"),
    ("A quoi sert une base de donnees ?", "programming"),
    ("Qu'est-ce que l'intelligence artificielle ?", "programming"),
    ("Qu'est-ce que le machine learning ?", "programming"),
    ("Qu'est-ce qu'une API ?", "programming"),
    ("Qu'est-ce que le cloud computing ?", "programming"),
    ("Qu'est-ce que Git ?", "programming"),
    ("Qu'est-ce qu'un compilateur ?", "programming"),
    ("Qu'est-ce que la blockchain ?", "programming"),

    # === SANTE & MEDECINE (10) ===
    ("Quels sont les symptomes de la grippe ?", "health"),
    ("Comment prevenir les maladies cardiovasculaires ?", "health"),
    ("Qu'est-ce que le diabete ?", "health"),
    ("Comment fonctionne la vaccination ?", "health"),
    ("Quels sont les bienfaits du sport ?", "health"),
    ("Qu'est-ce que le cancer ?", "health"),
    ("Comment traiter une brulure mineure ?", "health"),
    ("Qu'est-ce que l'hypertension ?", "health"),
    ("Quels aliments sont riches en vitamine C ?", "health"),
    ("Comment reconnaitre un AVC ?", "health"),

    # === DIVERS (10) ===
    ("Quelle est la signification de la vie ?", "philosophy"),
    ("Comment le riz est-il cultive ?", "agriculture"),
    ("Qu'est-ce que le rechauffement climatique ?", "environment"),
    ("Comment fonctionne un avion ?", "engineering"),
    ("Qu'est-ce que l'ONU ?", "politics"),
    ("Comment lire l'heure sur un cadran solaire ?", "general"),
    ("Qu'est-ce que le PIB ?", "economics"),
    ("Comment faire du pain ?", "cooking"),
    ("Qu'est-ce que le Big Bang ?", "cosmology"),
    ("Pourquoi le ciel est-il bleu ?", "physics"),
]

# ==============================================================================
# BENCHMARK ENGINE
# ==============================================================================

class LMArenaBenchmark:
    """Benchmark style LM Arena pour l'architecture hybride."""

    def __init__(self):
        self.engine = None
        self.results = []
        self.stats = {
            "started_at": datetime.now().isoformat(),
            "total_questions": 0,
            "completed": 0,
            "failed": 0,
            "by_domain": defaultdict(lambda: {"count": 0, "avg_trace": 0, "avg_time": 0,
                                               "hallucinated": 0, "total_trace": 0, "total_time": 0}),
        }
        self._init_engine()

    def _init_engine(self):
        try:
            from server import HybridEngine
            self.engine = HybridEngine()
        except Exception as e:
            print(f"Erreur initialisation moteur : {e}")

    def run(self, questions: List[Tuple[str, str]] = None, limit: int = None):
        """Execute le benchmark sur les questions donnees."""
        if questions is None:
            questions = LM_ARENA_QUESTIONS

        if limit:
            # Selection aleatoire si limite
            if limit < len(questions):
                questions = random.sample(questions, limit)

        self.stats["total_questions"] = len(questions)
        print(f"\n{'='*60}")
        print(f"  LM ARENA BENCHMARK — KA HYBRID")
        print(f"  Questions : {len(questions)}")
        print(f"  DeepSeek : {'[CONNECTE]' if self.engine else '[ERREUR]'}")
        print(f"{'='*60}")

        for i, (question, domain) in enumerate(questions):
            print(f"\n[{i+1}/{len(questions)}] [{domain}] {question[:80]}...")
            t0 = time.time()

            try:
                result = self.engine.query(question, style="general", max_tokens=300)
                elapsed_ms = round((time.time() - t0) * 1000, 1)

                entry = {
                    "id": i + 1,
                    "question": question,
                    "domain": domain,
                    "text": result.get("text", ""),
                    "source": result.get("source", "error"),
                    "verified": result.get("verified", False),
                    "trace_score": result.get("trace_score", 0),
                    "trace_verdict": result.get("trace_verdict", "error"),
                    "hallucination_phrases": len(result.get("hallucination_phrases", [])),
                    "facts_used": result.get("facts_used", 0),
                    "confidence": result.get("confidence", 0),
                    "temps_ms": elapsed_ms,
                    "timestamp": datetime.now().isoformat(),
                }

                self.results.append(entry)
                self.stats["completed"] += 1

                # Mettre a jour les stats par domaine
                ds = self.stats["by_domain"][domain]
                ds["count"] += 1
                ds["total_trace"] += entry["trace_score"]
                ds["total_time"] += elapsed_ms
                ds["avg_trace"] = round(ds["total_trace"] / ds["count"], 2)
                ds["avg_time"] = round(ds["total_time"] / ds["count"], 1)
                if entry["hallucination_phrases"] > 0:
                    ds["hallucinated"] += 1

                # Affichage rapide
                status = "OK" if entry["verified"] else "!!"
                trace_bar = "=" * min(int(entry["trace_score"] * 20), 20)
                print(f"  [{status}] Trace: {entry['trace_score']:.0%} {trace_bar}")
                print(f"  Facts: {entry['facts_used']} | Time: {elapsed_ms}ms | Source: {entry['source']}")

            except Exception as e:
                print(f"  [ERREUR] {e}")
                self.stats["failed"] += 1
                self.results.append({
                    "id": i + 1, "question": question, "domain": domain,
                    "text": str(e), "source": "error", "verified": False,
                    "trace_score": 0, "trace_verdict": "error",
                    "hallucination_phrases": 0, "facts_used": 0,
                    "confidence": 0, "temps_ms": 0,
                })

            # Sauvegarde incrementielle toutes les 20 questions
            if (i + 1) % 20 == 0:
                self._save_results()

        # Sauvegarde finale
        self._save_results()
        self._generate_report()
        return self.results

    def _save_results(self):
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "stats": {k: dict(v) if isinstance(v, defaultdict) else v for k, v in self.stats.items()},
                "results": self.results,
            }, f, ensure_ascii=False, indent=2)

    def _generate_report(self):
        """Genere un rapport Markdown."""
        s = self.stats
        n = s["completed"]
        if n == 0:
            return

        avg_trace = sum(r["trace_score"] for r in self.results) / n * 100
        avg_time = sum(r["temps_ms"] for r in self.results) / n
        verified = sum(1 for r in self.results if r["verified"])
        api_used = sum(1 for r in self.results if r["source"] == "deepseek_api")
        hallucinated = sum(1 for r in self.results if r["hallucination_phrases"] > 0)
        by_domain = s["by_domain"]

        report = f"""# Rapport Benchmark LM Arena — KA Hybrid

**Date :** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Questions :** {n}
**Modele :** deepseek-chat (API) + Hologramme ABC 1024x1024

## Resume Global

| Metrique | Valeur |
|---|---|
| Questions traitees | {n} |
| Reponses verifiees | {verified}/{n} ({verified/n*100:.0f}%) |
| Via API DeepSeek | {api_used}/{n} ({api_used/n*100:.0f}%) |
| Hallucinations detectees | {hallucinated}/{n} ({hallucinated/n*100:.0f}%) |
| Tracabilite moyenne | {avg_trace:.1f}% |
| Temps de reponse moyen | {avg_time:.0f}ms |
| Faits moyens par requete | {sum(r['facts_used'] for r in self.results)/n:.0f} |

## Performance par Domaine

| Domaine | Questions | Trace Moy. | Temps Moy. | Hallucinations |
|---|---|---|---|---|
"""
        for domain in sorted(by_domain.keys()):
            d = by_domain[domain]
            report += f"| {domain} | {d['count']} | {d['avg_trace']:.0%} | {d['avg_time']:.0f}ms | {d['hallucinated']} |\n"

        report += f"""
## Distribution des Scores de Tracabilite

```
"""
        # Histogramme ASCII
        bins = [0] * 11  # 0-10%, 10-20%, ...
        for r in self.results:
            idx = min(int(r["trace_score"] * 10), 10)
            bins[idx] += 1
        max_bin = max(bins) or 1
        for i in range(11):
            bar_len = int(bins[i] / max_bin * 40)
            pct = f"{i*10}-{(i+1)*10}%" if i < 10 else "100%"
            report += f"{pct:>8s} |{'#' * bar_len} {bins[i]}\n"

        report += """
```

## Top 5 Questions (Meilleure Tracabilite)

"""
        sorted_by_trace = sorted(self.results, key=lambda r: r["trace_score"], reverse=True)
        for r in sorted_by_trace[:5]:
            report += f"- **{r['trace_score']:.0%}** — {r['question'][:80]}\n"
            report += f"  Reponse : {r['text'][:120]}...\n"

        report += """
## Top 5 Questions (Plus Faible Tracabilite)

"""
        for r in sorted_by_trace[-5:]:
            report += f"- **{r['trace_score']:.0%}** — {r['question'][:80]}\n"
            report += f"  Reponse : {r['text'][:120]}...\n"

        report += f"""
## Configuration

- Hologramme : ABC 1024x1024, 961 patches
- Mapping : spatial + semantique (TF-IDF)
- Faits QuickFacts : 950
- LLM : DeepSeek API (deepseek-chat)
- Temperature : 0.3
- System prompt : contrainte stricte de non-invention
- Verification : couche 4 active

---

*Rapport genere automatiquement par benchmark_lm_arena.py*
"""

        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n[Rapport sauvegarde] {REPORT_FILE}")

    def print_summary(self):
        """Affiche un resume console."""
        if not self.results:
            print("Aucun resultat.")
            return

        n = len(self.results)
        avg_trace = sum(r["trace_score"] for r in self.results) / n * 100
        avg_time = sum(r["temps_ms"] for r in self.results) / n
        verified = sum(1 for r in self.results if r["verified"])
        hallucinated = sum(1 for r in self.results if r["hallucination_phrases"] > 0)

        print(f"\n{'='*60}")
        print(f"  RESUME BENCHMARK")
        print(f"{'='*60}")
        print(f"  Questions       : {n}")
        print(f"  Verifiees       : {verified}/{n} ({verified/n*100:.0f}%)")
        print(f"  Hallucinations  : {hallucinated}/{n} ({hallucinated/n*100:.0f}%)")
        print(f"  Trace moyenne   : {avg_trace:.1f}%")
        print(f"  Temps moyen     : {avg_time:.0f}ms")


# ==============================================================================
# CLI
# ==============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="LM Arena Benchmark — KA Hybrid")
    parser.add_argument("--quick", type=int, metavar="N", default=None,
                        help=f"Test rapide sur N questions (max {len(LM_ARENA_QUESTIONS)})")
    parser.add_argument("--full", action="store_true",
                        help=f"Benchmark complet ({len(LM_ARENA_QUESTIONS)} questions)")
    parser.add_argument("--report", action="store_true",
                        help="Afficher le dernier rapport")
    parser.add_argument("--domain", type=str, default=None,
                        help="Filtrer par domaine (ex: math, science, history)")

    args = parser.parse_args()

    if args.report:
        if REPORT_FILE.exists():
            with open(REPORT_FILE, 'r', encoding='utf-8') as f:
                print(f.read())
        else:
            print("Aucun rapport trouve. Lancez un benchmark d'abord.")
        return

    questions = LM_ARENA_QUESTIONS

    if args.domain:
        questions = [(q, d) for q, d in questions if d == args.domain]
        if not questions:
            print(f"Domaine '{args.domain}' non trouve.")
            return
        print(f"Domaine filtre : {args.domain} ({len(questions)} questions)")

    n = args.quick if args.quick else (len(questions) if args.full else None)

    if n is None:
        print("Specifiez --quick N ou --full")
        print(f"  --quick 20 : test rapide sur 20 questions")
        print(f"  --full     : benchmark complet ({len(questions)} questions)")
        return

    benchmark = LMArenaBenchmark()
    benchmark.run(questions, limit=n)
    benchmark.print_summary()


if __name__ == "__main__":
    main()