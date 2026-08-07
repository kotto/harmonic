#!/usr/bin/env python3
"""
Hologram Builder — Création d'hologrammes spécialisés ultra-performants
=========================================================================
Prend une source de connaissances (texte, Wikipedia, Wikidata, web)
→ extrait les faits → valide → benchmark → publie.

L'hologramme résultant est un fichier .npz + metadata dans le Store,
prêt à être téléchargé par les utilisateurs.

Usage :
    # Depuis un fichier texte
    python hologram_builder.py --source manuel_medecine.txt --domain medecine

    # Depuis une catégorie Wikipedia
    python hologram_builder.py --wiki "Médecine" --domain medecine --lang fr

    # Depuis un dump Wikidata JSON
    python hologram_builder.py --wikidata data/wikidata_med.json --domain medecine

    # Depuis un répertoire de fichiers
    python hologram_builder.py --corpus data/corpus_astronomie/ --domain astronomie

    # Mode interactif : guidé pas-à-pas
    python hologram_builder.py --interactive

Architecture :
    SOURCE → [kb_scaler / extract_triples] → VALIDATE → BENCHMARK → PUBLISH
"""

import re, json, time, argparse, sys, os
from pathlib import Path
from collections import Counter
from typing import List, Tuple, Dict, Optional

# ═══════════════════════════════════════════════════════════════════════════════
# 1. EXTRACTION DE TRIPLETS
# ═══════════════════════════════════════════════════════════════════════════════

# Patterns d'extraction de triples (sujet, relation, objet) à partir de texte
_RELATION_PATTERNS = [
    # Définitions (plus tolérant : sujet peut commencer après "Le ", "La ", "L'")
    (r"(?:Le\s+|La\s+|L'|Les\s+|Un\s+|Une\s+)?([A-ZÉÈÊËÀÂÎÏÔÖÙÛÜÇ][a-zéèêëàâîïôöùûüç]{2,}(?:\s(?:de|du|des|d'|à|au|aux|en|sur|dans|pour|par|avec|sans|entre)\s[A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}){0,2})\s+est\s+(?:un|une|le|la|l'|les\s+)?([a-zéèêëàâîïôöùûüç][^\.]{5,150})\.?", "est"),
    # A pour/de
    (r"([A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}(?:\s[A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}){0,3})\s+a\s+(?:pour|de|comme)\s+(?:rôle\s+de\s+)?([a-zéèêëàâîïôöùûüç][^\.]{5,100})\.?", "a"),
    # Découvert/inventé/écrit/formulé/développé PAR
    (r"([A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}(?:\s[A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}){0,3})\s+a\s+été\s+(découvert|inventé|créé|fondé|écrit|développé|proposé|formulé|exploré|observé|démontré|établi|mesuré|calculé)\s+(?:par\s+)?([A-ZÉÈ][^\.]{3,100})\.?", "decouvert"),
    # Découvre/invente/fonde/écrit/développe (présent actif) — "X découvre Y"
    (r"([A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}(?:\s[A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}){0,3})\s+(découvre|invente|fonde|écrit|développe|propose|formule|explore|observe|démontre|établit)\s+(?:le\s+|la\s+|l'|un\s+|une\s+)?([a-zéèêëàâîïôöùûüç][^\.]{5,100})\.?", "decouvre"),
    # Situé à/dans
    (r"([A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}(?:\s[A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}){0,3})\s+(?:est\s+)?(?:situé|localisé|trouve|situe)\s+(?:à|dans|en|au|aux|sur)\s+([a-zéèêëàâîïôöùûüç][^\.]{5,100})\.?", "situe"),
    # Contient/composé de
    (r"([A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}(?:\s[A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}){0,3})\s+(?:contient|est\s+composé\s+de|comprend|inclut|renferme|possède)\s+([a-zéèêëàâîïôöùûüç][^\.]{5,100})\.?", "contient"),
    # Produit/génère
    (r"([A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}(?:\s[A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}){0,3})\s+(?:produit|génère|fabrique|synthétise|sécrète|émet|libère)\s+([a-zéèêëàâîïôöùûüç][^\.]{5,100})\.?", "produit"),
    # Cause/provoque
    (r"([A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}(?:\s[A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}){0,3})\s+(?:cause|provoque|entraîne|déclenche|induit|engendre)\s+([a-zéèêëàâîïôöùûüç][^\.]{5,100})\.?", "cause"),
    # Permet/facilite
    (r"([A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}(?:\s[A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}){0,3})\s+(?:permet|facilite|autorise|contribue\s+à)\s+([a-zéèêëàâîïôöùûüç][^\.]{5,100})\.?", "permet"),
    # Régule/contrôle
    (r"([A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}(?:\s[A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}){0,3})\s+(?:régule|contrôle|maintient|assure|garantit)\s+([a-zéèêëàâîïôöùûüç][^\.]{5,100})\.?", "regule"),
    # Rôle
    (r"([A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}(?:\s[A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}){0,3})\s+joue\s+un\s+rôle\s+(?:essentiel|important|clé|majeur|fondamental|central|crucial)\s+(?:dans|pour)\s+([a-zéèêëàâîïôöùûüç][^\.]{5,120})\.?", "joue_role_dans"),
    # Capitales
    (r"([A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}(?:\s[A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}){0,2})\s+(?:est\s+)?(?:la\s+)?capitale\s+(?:de\s+)?(?:la\s+)?(?:l'|le\s+)?([A-ZÉÈ][^\.]{2,60})\.?", "capitale_de"),
    # Propriété physique : "X se déplace à Y km/s", "X a une masse de Y"
    (r"([A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}(?:\s[A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}){0,3})\s+(?:se\s+déplace|voyage|se\s+propage)\s+à\s+([^\.]{5,60})\.?", "vitesse"),
    # Surnom : "X est surnommé(e) Y"
    (r"([A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}(?:\s[A-ZÉÈ][a-zéèêëàâîïôöùûüç]{2,}){0,3})\s+est\s+surnommée?\s+(?:la\s+|le\s+)?([a-zéèêëàâîïôöùûüç][^\.]{5,60})\.?", "surnom"),
]

def extract_triples_from_text(text: str, domain: str = "GENERAL") -> List[Tuple[str, str, str]]:
    """
    Extrait des triplets d'un texte en utilisant le meilleur extracteur disponible.
    
    Priorité :
      1. bootstrapper.extract_triples_ml() — KB-trained + entités multi-mots
      2. bootstrapper.extract_triples_enhanced() — 25+ patterns regex
      3. Fallback interne — 14 patterns simples
    """
    # Essayer l'extracteur ML (le plus puissant)
    try:
        from bootstrapper import extract_triples_ml
        enhanced = extract_triples_ml(text)
        if enhanced:
            return [(s, r, o) for s, r, o, sec in enhanced]
    except ImportError:
        pass
    
    # Essayer l'extracteur enrichi (25+ patterns)
    try:
        from bootstrapper import extract_triples_enhanced
        enhanced = extract_triples_enhanced(text)
        if enhanced:
            return [(s, r, o) for s, r, o, sec in enhanced]
    except ImportError:
        pass
    
    # Fallback : patterns internes
    return _extract_triples_simple(text)


# ═══════════════════════════════════════════════════════════════════════════════
# Fallback interne si bootstrapper non disponible
# ═══════════════════════════════════════════════════════════════════════════════

def _extract_triples_simple(text: str) -> List[Tuple[str, str, str]]:
    """Extracteur interne de secours (14 patterns regex)."""
    triples = []
    seen = set()

    for pattern, relation in _RELATION_PATTERNS:
        for match in re.finditer(pattern, text):
            sujet = match.group(1).strip()
            if relation == "decouvert":
                rel = match.group(2).strip()
                obj = match.group(3).strip()
            else:
                rel = relation
                obj = match.group(2).strip()

            sujet = re.sub(r'\s+', ' ', sujet).strip(' ,;:')
            obj = re.sub(r'\s+', ' ', obj).strip(' ,;:')
            if len(sujet) < 2 or len(obj) < 3:
                continue
            if len(sujet) > 120 or len(obj) > 200:
                continue

            key = (sujet.lower(), rel.lower(), obj.lower())
            if key not in seen:
                seen.add(key)
                triples.append((sujet, rel, obj))

    return triples


def extract_triples_simple(text: str, domain: str = "GENERAL") -> List[Tuple[str, str, str, str]]:
    """
    Version enrichie : extraction + attribution du secteur.
    Retourne (sujet, relation, objet, secteur) pour compatibilité Store.
    """
    raw = extract_triples_from_text(text, domain)
    sector = _domain_to_sector(domain)
    return [(s, r, o, sector) for s, r, o in raw]


def _domain_to_sector(domain: str) -> str:
    """Mappe un domaine vers un secteur harmonique standard."""
    mapping = {
        'medecine': 'SANTE', 'sante': 'SANTE', 'médecine': 'SANTE',
        'astronomie': 'PHYSIQUE_FOND', 'physique': 'PHYSIQUE_FOND',
        'biologie': 'BIOLOGIE', 'biologie': 'BIOLOGIE',
        'chimie': 'CHIMIE', 'chimie': 'CHIMIE',
        'mathematiques': 'MATHEMATIQUES', 'maths': 'MATHEMATIQUES',
        'histoire': 'HISTOIRE', 'histoire': 'HISTOIRE',
        'geographie': 'GEOGRAPHIE', 'géographie': 'GEOGRAPHIE',
        'economie': 'ECONOMIE', 'économie': 'ECONOMIE',
        'philosophie': 'PHILOSOPHIE', 'philosophie': 'PHILOSOPHIE',
        'droit': 'DROIT', 'droit': 'DROIT',
        'informatique': 'TECHNOLOGIE', 'technologie': 'TECHNOLOGIE',
        'linguistique': 'CULTURE', 'litterature': 'CULTURE',
        'musique': 'CULTURE', 'art': 'CULTURE', 'culture': 'CULTURE',
    }
    return mapping.get(domain.lower(), domain.upper().replace(' ', '_')[:30])


# ═══════════════════════════════════════════════════════════════════════════════
# 2. INGESTION DE SOURCES
# ═══════════════════════════════════════════════════════════════════════════════

def ingest_text_file(path: str, domain: str) -> List[Tuple[str, str, str, str]]:
    """Ingère un fichier texte brut (.txt, .md)."""
    text = Path(path).read_text(encoding='utf-8')
    return extract_triples_simple(text, domain)


def ingest_corpus(directory: str, domain: str) -> List[Tuple[str, str, str, str]]:
    """Ingère tous les fichiers texte d'un répertoire."""
    all_triples = []
    n_files = 0
    for ext in ['*.txt', '*.md', '*.rst']:
        for path in Path(directory).rglob(ext):
            try:
                text = path.read_text(encoding='utf-8')
                triples = extract_triples_simple(text, domain)
                all_triples.extend(triples)
                n_files += 1
                sys.stdout.write(f"\r  Fichiers: {n_files} | Triplets: {len(all_triples)}")
                sys.stdout.flush()
            except Exception:
                pass
    print()
    return all_triples


def ingest_wikipedia_category(category: str, lang: str = 'fr',
                              max_articles: int = 200) -> List[Tuple[str, str, str, str]]:
    """
    Ingère les articles d'une catégorie Wikipedia.
    Utilise l'API Wikipedia (gratuite, pas de clé nécessaire).

    Args:
        category: nom de la catégorie (ex: "Médecine", "Astronomie")
        lang: code langue Wikipedia ('fr', 'en')
        max_articles: nombre max d'articles à télécharger
    """
    import urllib.request
    import urllib.parse

    all_triples = []
    api_url = f"https://{lang}.wikipedia.org/w/api.php"

    try:
        # 1. Récupérer les titres de la catégorie
        params = urllib.parse.urlencode({
            'action': 'query',
            'format': 'json',
            'list': 'categorymembers',
            'cmtitle': f'Catégorie:{category}',
            'cmlimit': min(max_articles, 500),
            'cmtype': 'page',
        })
        url = f"{api_url}?{params}"
        req = urllib.request.Request(url, headers={'User-Agent': 'KA-HologramBuilder/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())

        pages = data.get('query', {}).get('categorymembers', [])
        titles = [p['title'] for p in pages
                 if not p['title'].startswith(('Catégorie:', 'Portail:', 'Modèle:', 'Fichier:'))]
        titles = titles[:max_articles]

        print(f"  Catégorie '{category}': {len(titles)} articles trouvés")

        # 2. Télécharger les extraits
        for i, title in enumerate(titles):
            try:
                params2 = urllib.parse.urlencode({
                    'action': 'query',
                    'format': 'json',
                    'prop': 'extracts',
                    'exintro': 1,
                    'explaintext': 1,
                    'titles': title,
                })
                url2 = f"{api_url}?{params2}"
                req2 = urllib.request.Request(url2, headers={'User-Agent': 'KA-HologramBuilder/1.0'})
                with urllib.request.urlopen(req2, timeout=15) as resp:
                    data2 = json.loads(resp.read())

                pages_data = data2.get('query', {}).get('pages', {})
                for page_id, page_data in pages_data.items():
                    extract = page_data.get('extract', '')
                    if extract and len(extract) > 100:
                        triples = extract_triples_simple(extract, category)
                        all_triples.extend(triples)

                if (i + 1) % 20 == 0:
                    print(f"  [{i+1}/{len(titles)}] {title[:50]} | {len(all_triples)} triplets")
            except Exception:
                continue

        print(f"  Terminé: {len(titles)} articles → {len(all_triples)} triplets")

    except Exception as e:
        print(f"  ⚠️  Wikipedia indisponible: {e}")

    return all_triples


def ingest_bulk_text(text: str, domain: str) -> List[Tuple[str, str, str, str]]:
    """Ingère un texte fourni directement (mode programmatique)."""
    return extract_triples_simple(text, domain)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. BUILDER PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class HologramBuilder:
    """
    Constructeur d'hologramme spécialisé.

    Pipeline complet :
      1. Ingérer la source → triplets bruts
      2. Valider (dédup, contradictions, cohérence)
      3. Benchmarker (precision, recall, F1)
      4. Publier dans le Store
    """

    def __init__(self):
        self.store = None
        self.validator = None
        self.benchmark = None

    def build(self, source: str, source_type: str, domain: str,
              lang: str = 'fr', name: str = None, description: str = "",
              max_facts: int = 100_000, skip_benchmark: bool = False) -> dict:
        """
        Construit un hologramme complet.

        Args:
            source: chemin du fichier, URL, catégorie Wikipedia, ou texte brut
            source_type: 'file', 'corpus', 'wikipedia', 'text', 'wikidata'
            domain: domaine de l'hologramme (ex: 'medecine', 'astronomie')
            lang: langue ('fr', 'en')
            name: nom affiché (défaut: domain)
            description: description textuelle
            max_facts: nombre max de faits à conserver
            skip_benchmark: sauter le benchmark (plus rapide)

        Returns:
            dict: rapport complet avec quality_score, benchmark, etc.
        """
        t0 = time.time()
        report = {'domain': domain, 'source_type': source_type, 'status': 'started'}

        # ═══ ÉTAPE 1 : INGESTION ═══
        print(f"\n{'='*60}")
        print(f"  ÉTAPE 1/4 — INGESTION: {source_type} → {domain}")
        print(f"{'='*60}")

        if source_type == 'file':
            facts = ingest_text_file(source, domain)
        elif source_type == 'corpus':
            facts = ingest_corpus(source, domain)
        elif source_type == 'wikipedia':
            facts = ingest_wikipedia_category(source, lang=lang,
                                              max_articles=100)
        elif source_type == 'text':
            facts = ingest_bulk_text(source, domain)
        else:
            raise ValueError(f"Type de source inconnu: {source_type}")

        report['raw_facts'] = len(facts)
        print(f"  → {len(facts)} triplets bruts extraits")

        if len(facts) < 5:
            print("  ❌ Pas assez de triplets extraits. Vérifiez la source.")
            report['status'] = 'failed_ingestion'
            return report

        # ═══ ÉTAPE 2 : VALIDATION ═══
        print(f"\n{'='*60}")
        print(f"  ÉTAPE 2/4 — VALIDATION")
        print(f"{'='*60}")

        from validate_hologram import validate_hologram
        validation = validate_hologram(facts[:max_facts], domain)
        report['validation'] = validation
        report['quality_score'] = validation.get('quality_score', 0)

        print(f"  → Score qualité: {validation['quality_score']:.3f}")
        print(f"  → Déduplication: {validation['deduplication']['duplicates_removed']} doublons")
        for rec in validation.get('recommendations', []):
            print(f"     {rec}")

        # ═══ ÉTAPE 3 : BENCHMARK ═══
        if not skip_benchmark:
            print(f"\n{'='*60}")
            print(f"  ÉTAPE 3/4 — BENCHMARK")
            print(f"{'='*60}")

            try:
                from benchmark_hologram import benchmark_hologram
                from harmonic_brain import HarmonicBrain

                unique_facts = list(facts[:max_facts])
                brain = HarmonicBrain(unique_facts)
                benchmark = benchmark_hologram(unique_facts, brain, domain,
                                               max_questions=30)
                report['benchmark'] = benchmark
                print(f"  → F1: {benchmark.get('f1_score', 0):.3f}")
                print(f"  → Precision: {benchmark.get('precision', 0):.1%}")
                print(f"  → Recall: {benchmark.get('recall', 0):.1%}")
                print(f"  → Coverage: {benchmark.get('coverage', 0):.1%}")
            except Exception as e:
                print(f"  ⚠️  Benchmark indisponible: {e}")
                report['benchmark'] = {'error': str(e)}

        # ═══ ÉTAPE 4 : PUBLICATION ═══
        print(f"\n{'='*60}")
        print(f"  ÉTAPE 4/4 — PUBLICATION")
        print(f"{'='*60}")

        try:
            from hologram_store import HologramStore
            self.store = HologramStore()

            holo_id = f"official_{domain.lower().replace(' ', '_')}"
            holo_name = name or domain.capitalize()

            # Limiter aux max_facts meilleurs (les plus longs = plus informatifs)
            unique = list(facts[:max_facts])
            unique.sort(key=lambda x: len(str(x[0])) + len(str(x[2])), reverse=True)

            self.store.publish(
                domain=domain,
                facts=unique,
                author='KA Builder',
                name=holo_name,
                description=description or f"Hologramme spécialisé en {domain}",
            )
            # Lire l'ID réel depuis le registry (publié en community_...)
            published_id = None
            for hid, meta in self.store._registry.items():
                if meta.domain == domain and meta.author == 'KA Builder':
                    published_id = hid
                    break
            report['published'] = True
            report['hologram_id'] = published_id or f'community_KA Builder_{domain.lower()}'
            report['published_facts'] = min(len(unique), max_facts)
            print(f"  ✅ Publié: {report['hologram_id']} ({report['published_facts']} faits)")

            # Mettre à jour le quality_score dans le registry
            registry_path = Path('data/hologram_store/registry.json')
            if registry_path.exists():
                reg = json.loads(registry_path.read_text(encoding='utf-8'))
                if published_id and published_id in reg:
                    reg[published_id]['quality_score'] = report['quality_score']
                    bm = report.get('benchmark', {})
                    if 'questions' in bm:
                        reg[published_id]['benchmark_questions'] = bm['questions']
                registry_path.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding='utf-8')

        except Exception as e:
            print(f"  ❌ Publication échouée: {e}")
            report['published'] = False
            report['publish_error'] = str(e)

        report['duration_seconds'] = round(time.time() - t0, 1)
        report['status'] = 'completed'

        # Sauvegarder le rapport
        report_path = Path(f'data/hologram_store/build_report_{domain.lower()}.json')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n  Rapport: {report_path}")
        print(f"  Durée totale: {report['duration_seconds']:.0f}s")
        return report


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Hologram Builder — Créer des hologrammes spécialisés ultra-performants")

    # Source
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--source', '-s', help='Fichier texte (.txt, .md)')
    group.add_argument('--corpus', '-c', help='Répertoire de fichiers texte')
    group.add_argument('--wiki', '-w', help='Catégorie Wikipedia (ex: "Médecine")')
    group.add_argument('--text', '-t', help='Texte brut (en ligne de commande)')
    group.add_argument('--interactive', '-i', action='store_true',
                       help='Mode interactif guidé')

    # Configuration
    parser.add_argument('--domain', '-d', default='general', help='Domaine (ex: medecine, astronomie)')
    parser.add_argument('--lang', '-l', default='fr', help='Langue (fr, en)')
    parser.add_argument('--name', '-n', help='Nom affiché de l\'hologramme')
    parser.add_argument('--desc', help='Description')
    parser.add_argument('--max-facts', type=int, default=50000,
                       help='Nombre max de faits (défaut: 50000)')
    parser.add_argument('--skip-benchmark', action='store_true',
                       help='Sauter le benchmark (plus rapide)')

    args = parser.parse_args()

    # Mode interactif
    if args.interactive:
        print("\n🌟 HOLOGRAM BUILDER — Mode interactif\n")
        domain = input("  Domaine (ex: astronomie, droit, medecine): ").strip() or "general"
        print("\n  Source de connaissances:")
        print("    1. Fichier texte (.txt, .md)")
        print("    2. Répertoire de fichiers")
        print("    3. Catégorie Wikipedia")
        print("    4. Texte collé")
        choice = input("  Choix [1-4]: ").strip()

        if choice == '1':
            source = input("  Chemin du fichier: ").strip()
            source_type = 'file'
        elif choice == '2':
            source = input("  Chemin du répertoire: ").strip()
            source_type = 'corpus'
        elif choice == '3':
            source = input("  Nom de la catégorie Wikipedia: ").strip()
            source_type = 'wikipedia'
        elif choice == '4':
            print("  Collez le texte (Ctrl+D ou ligne vide pour terminer):")
            lines = []
            while True:
                try:
                    line = input()
                    if line == '':
                        break
                    lines.append(line)
                except EOFError:
                    break
            source = '\n'.join(lines)
            source_type = 'text'
        else:
            print("  Choix invalide.")
            return

        name = input("  Nom affiché (Enter = domaine): ").strip() or None
        desc = input("  Description (Enter = auto): ").strip() or ""
        skip_bench = input("  Sauter le benchmark ? [o/N]: ").strip().lower() == 'o'
        max_facts = 50000
    else:
        if args.source:
            source, source_type = args.source, 'file'
        elif args.corpus:
            source, source_type = args.corpus, 'corpus'
        elif args.wiki:
            source, source_type = args.wiki, 'wikipedia'
        elif args.text:
            source, source_type = args.text, 'text'
        else:
            source, source_type = None, None

        domain = args.domain
        name = args.name
        desc = args.desc or ""
        skip_bench = args.skip_benchmark
        max_facts = args.max_facts

    if source is None:
        print("❌ Aucune source spécifiée.")
        return

    builder = HologramBuilder()
    report = builder.build(
        source=source,
        source_type=source_type,
        domain=domain,
        lang=args.lang,
        name=name,
        description=desc,
        max_facts=max_facts,
        skip_benchmark=skip_bench,
    )

    if report.get('status') == 'completed':
        print(f"\n{'='*60}")
        print(f"  🌟 HOLOGRAMME CRÉÉ AVEC SUCCÈS")
        print(f"{'='*60}")
        print(f"  ID: {report.get('hologram_id', '?')}")
        print(f"  Faits: {report.get('published_facts', 0)}")
        print(f"  Qualité: {report.get('quality_score', 0):.3f}")
        if 'benchmark' in report:
            b = report['benchmark']
            if 'f1_score' in b:
                print(f"  F1: {b['f1_score']:.3f}")
        print(f"  Durée: {report.get('duration_seconds', 0):.0f}s")


if __name__ == '__main__':
    main()
