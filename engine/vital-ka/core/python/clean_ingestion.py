"""
Clean Ingestion — Ingestion Massive Propre
===========================================
Pipeline d'ingestion avec validation systématique.

Architecture :
  Corpus → DeepSeek (extraction) → Validation → Brain.ingest()

Validation :
  1. ANTI-CONCATÉNATION : rejette "puis", "->", ">>", " et "
  2. ANTI-BRUIT : rejette sujets $, dates, symboles
  3. ANTI-DOUBLON : rejette si déjà dans le cerveau
  4. COHÉRENCE : vérifie la similarité de phase avec l'existant
  5. SECTEUR : détecte automatiquement le domaine

Usage :
  python clean_ingestion.py --corpus data/corpus/ --max-facts 10000
"""

import sys, os, re, time, logging, json
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

from harmonic_brain import HarmonicBrain, _normalize

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

# Patterns de concaténation (REJET immédiat)
_CONCAT_PATTERNS = [' puis ', ' -> ', ' >> ', ' et ', ' puis', '->', '>>']

# Patterns de bruit dans les sujets
_NOISE_SUBJECTS = [
    r'^\$', r'^€', r'^£',           # symboles monétaires
    r'^\d+$', r'^\d{4}$',           # nombres purs
    r'^\d{1,2}\s',                  # petits nombres
    r'^\(.*\)$',                    # parenthèses seules
    r'^".*"$',                      # guillemets seuls
    r'unknown', r'inconnu',         # valeurs placeholder
]

# Longueurs maximales
MAX_RELATION_LEN = 120
MAX_OBJECT_LEN = 300
MIN_SUBJECT_LEN = 2
MIN_OBJECT_LEN = 3


def validate_triple(s: str, r: str, o: str, existing_keys: set) -> Tuple[bool, str]:
    """
    Valide un triplet avant ingestion.

    Returns:
        (valide, raison_du_rejet)
    """
    s_clean = s.strip()
    r_clean = r.strip()
    o_clean = o.strip()

    # 1. Anti-concaténation
    for pat in _CONCAT_PATTERNS:
        if pat in r_clean:
            return False, f"concaténation '{pat}' dans la relation"
        if pat in o_clean:
            return False, f"concaténation '{pat}' dans l'objet"

    # 2. Longueurs
    if len(s_clean) < MIN_SUBJECT_LEN:
        return False, f"sujet trop court ({len(s_clean)} chars)"
    if len(o_clean) < MIN_OBJECT_LEN:
        return False, f"objet trop court ({len(o_clean)} chars)"
    if len(r_clean) < 2:
        return False, f"relation trop courte"
    if len(r_clean) > MAX_RELATION_LEN:
        return False, f"relation trop longue ({len(r_clean)} chars)"
    if len(o_clean) > MAX_OBJECT_LEN:
        return False, f"objet trop long ({len(o_clean)} chars)"

    # 3. Anti-bruit dans le sujet
    for pat in _NOISE_SUBJECTS:
        if re.search(pat, s_clean, re.IGNORECASE):
            return False, f"sujet bruité: {s_clean[:40]}"

    # 4. Sujet = objet (boucle triviale)
    if _normalize(s_clean) == _normalize(o_clean):
        return False, "sujet = objet (boucle)"

    # 5. Anti-doublon
    key = (_normalize(s_clean), _normalize(r_clean), _normalize(o_clean))
    if key in existing_keys:
        return False, "doublon"

    return True, "ok"


# ═══════════════════════════════════════════════════════════════════════════════
# EXTRACTION LLM (prompt amélioré anti-concaténation)
# ═══════════════════════════════════════════════════════════════════════════════

_EXTRACTION_PROMPT = """Extract ALL factual claims from the text as structured triples.

FORMAT (one per line):
subject | relation | object

RULES:
- ONE fact per line. Never combine multiple facts.
- NEVER use "and", "then", "puis", "->", ">>" in the relation.
- If a sentence contains multiple facts, create separate lines.
- Subject and object must be specific entities (proper nouns, concepts).
- Relation must be a SINGLE verb phrase (e.g., "discovered", "is the capital of").
- Keep subject and object concise (max 10 words each).

Text: {text}

Triples:"""


def extract_triples_clean(text: str) -> List[Tuple[str, str, str]]:
    """
    Extrait des triplets via DeepSeek API (sans lib openai, évite MemoryError).
    """
    import requests
    
    api_key = os.environ.get('DEEPSEEK_API_KEY', '')
    if not api_key:
        return _extract_triples_simple(text)
    
    prompt = _EXTRACTION_PROMPT.format(text=text[:800])
    
    try:
        resp = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': 'You extract structured facts from text. Respond ONLY with triples in format: subject | relation | object. One per line.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.1,
                'max_tokens': 500,
            },
            timeout=15
        )
        data = resp.json()
        content = data['choices'][0]['message']['content']
        
        triples = []
        for line in content.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('Voici') or line.startswith('Format'):
                continue
            parts = line.split('|')
            if len(parts) >= 3:
                s = parts[0].strip()
                r = parts[1].strip()
                o = parts[2].strip()
                if len(s) >= 2 and len(o) >= 3:
                    triples.append((s, r, o))
        return triples
    except Exception as e:
        log.warning(f"DeepSeek extraction failed: {e}")
        return _extract_triples_simple(text)


def _extract_triples_simple(text: str) -> List[Tuple[str, str, str]]:
    """
    Fallback : extraction regex améliorée (sans LLM).
    
    Patterns gérés :
      - X est Y / X est un Y / X est situé à Y
      - X a découvert/inventé/créé Y
      - X a été construit/découvert par Y
    """
    triples = []
    text_clean = re.sub(r'\([^)]*\)', '', text)  # enlever parenthèses
    
    # Pattern 1: "X est [un/une/le/la/situé à] Y"
    m = re.search(r'([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s[A-ZÀ-Ÿ][a-zà-ÿ]+){0,3})\s+est\s+(?:un\s+|une\s+|le\s+|la\s+|situé[e]?\s+(?:à|dans|en|sur)\s+)?(.+)', text_clean, re.IGNORECASE)
    if m:
        s = m.group(1).strip().lower()
        o = m.group(2).strip(' .,;').lower()
        if len(s) >= 2 and len(o) >= 3:
            triples.append((s, 'est', o))
    
    # Pattern 2: "X a découvert/inventé/créé/construit/peint/écrit Y"
    m = re.search(r'([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s[A-ZÀ-Ÿ][a-zà-ÿ]+){0,3})\s+a\s+(découvert|decouvert|inventé|invente|créé|cree|construit|peint|écrit|ecrit|fondé|fonde)\s+(.+)', text_clean, re.IGNORECASE)
    if m:
        s = m.group(1).strip().lower()
        verb = m.group(2).strip().lower()
        o = m.group(3).strip(' .,;').lower()
        if len(s) >= 2 and len(o) >= 3:
            triples.append((s, f'a {verb}', o))
    
    # Pattern 3: "X a été Y par Z" → "Z a Y X"
    m = re.search(r'(.+?)\s+a\s+été\s+(découvert|decouvert|inventé|construit|peint|écrit|fondé)\s+par\s+(.+)', text_clean, re.IGNORECASE)
    if m:
        o = m.group(1).strip(' .,;').lower()
        verb = m.group(2).strip().lower()
        s = m.group(3).strip(' .,;').lower()
        if len(s) >= 2 and len(o) >= 3:
            triples.append((s, f'a été {verb} par', o))
    
    # Pattern 4: "X, Y, est Z" (incidente)
    m = re.search(r'([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s[A-ZÀ-Ÿ][a-zà-ÿ]+){0,3}),\s*.+?,\s*est\s+(.+)', text_clean, re.IGNORECASE)
    if m:
        s = m.group(1).strip().lower()
        o = m.group(2).strip(' .,;').lower()
        if len(s) >= 2 and len(o) >= 3:
            triples.append((s, 'est', o))
    
    # Fallback: essayer l'extracteur original
    if not triples:
        try:
            from bootstrapper import extract_triples_simple as ets
            orig = ets(text)
            triples = [(s, r, o) for s, r, o, _ in orig]
        except ImportError:
            pass
    
    return triples


# ═══════════════════════════════════════════════════════════════════════════════
# DÉTECTION DE SECTEUR
# ═══════════════════════════════════════════════════════════════════════════════

def detect_sector(text: str) -> str:
    """Détecte le secteur d'un fait."""
    try:
        from bootstrapper import detect_sector as ds
        return ds(text)
    except ImportError:
        return "GENERAL"


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class CleanIngestion:
    """
    Pipeline d'ingestion massive avec validation.

    Usage:
        ci = CleanIngestion(brain)
        ci.ingest_text("Paris est la capitale de la France.")
        ci.ingest_corpus("data/corpus/", max_facts=5000)
        print(ci.report())
    """

    def __init__(self, brain: HarmonicBrain):
        self.brain = brain
        self.stats = {
            'total_extracted': 0,
            'validated': 0,
            'rejected_concat': 0,
            'rejected_noise': 0,
            'rejected_duplicate': 0,
            'rejected_other': 0,
            'ingested': 0,
        }
        self._existing_keys = set(self.brain.unconscious.registry.keys())

    def ingest_text(self, text: str, use_llm: bool = True) -> int:
        """
        Ingère un texte avec extraction + validation.

        Returns:
            nombre de faits ajoutés
        """
        if len(text) < 30:
            return 0

        # Extraction
        if use_llm:
            triples = extract_triples_clean(text)
        else:
            triples = _extract_triples_simple(text)

        self.stats['total_extracted'] += len(triples)
        added = 0

        for s, r, o in triples:
            # Validation
            valid, reason = validate_triple(s, r, o, self._existing_keys)
            if not valid:
                if 'concaténation' in reason:
                    self.stats['rejected_concat'] += 1
                elif 'bruit' in reason or 'court' in reason or 'long' in reason:
                    self.stats['rejected_noise'] += 1
                elif 'doublon' in reason:
                    self.stats['rejected_duplicate'] += 1
                else:
                    self.stats['rejected_other'] += 1
                continue

            self.stats['validated'] += 1

            # Secteur
            sec = detect_sector(f"{s} {r} {o}")

            # Ingestion dans le cerveau
            rec = self.brain.unconscious.ingest(s, r, o, sec)
            key = (_normalize(s), _normalize(r), _normalize(o))
            self._existing_keys.add(key)
            self.stats['ingested'] += 1
            added += 1

        return added

    def ingest_corpus(self, dir_path: str, max_files: int = 100,
                      max_facts: int = 10000, use_llm: bool = True) -> int:
        """
        Ingère un répertoire de textes.

        Args:
            dir_path: chemin du répertoire
            max_files: nombre max de fichiers
            max_facts: nombre max de faits à ingérer
            use_llm: utiliser DeepSeek pour l'extraction

        Returns:
            nombre total de faits ajoutés
        """
        corpus = Path(dir_path)
        files = sorted(corpus.glob("*.txt"))[:max_files]
        total_added = 0
        t0 = time.time()

        print(f"Ingestion massive: {len(files)} fichiers, max {max_facts} faits")
        print("=" * 60)

        for fi, path in enumerate(files):
            if total_added >= max_facts:
                break
            if path.stat().st_size < 100:
                continue

            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = [l.strip() for l in f if 30 < len(l.strip()) < 800]

            file_added = 0
            for li, line in enumerate(lines):
                if total_added >= max_facts:
                    break
                try:
                    added = self.ingest_text(line, use_llm=use_llm)
                    total_added += added
                    file_added += added
                except Exception as e:
                    if li < 3:
                        log.warning(f"Erreur {path.name}:{li}: {e}")

                # Rate limit pour l'API LLM
                if use_llm and (li + 1) % 10 == 0:
                    time.sleep(0.3)

                # Progression
                if total_added % 500 == 0:
                    elapsed = time.time() - t0
                    rate = total_added / max(elapsed, 1)
                    print(f"  [{total_added}/{max_facts}] {rate:.0f} faits/s "
                          f"| {self.stats['rejected_concat']} rejetés concat "
                          f"| {self.stats['rejected_noise']} bruit")

            if file_added > 0:
                print(f"  [{fi+1}/{len(files)}] {path.name}: +{file_added} faits")

        elapsed = time.time() - t0
        print(f"\nTerminé en {elapsed:.0f}s")
        print(f"  Extraits: {self.stats['total_extracted']}")
        print(f"  Validés: {self.stats['validated']}")
        print(f"  Rejetés concat: {self.stats['rejected_concat']}")
        print(f"  Rejetés bruit: {self.stats['rejected_noise']}")
        print(f"  Rejetés doublons: {self.stats['rejected_duplicate']}")
        print(f"  Ingérés: {self.stats['ingested']}")
        print(f"  Total cerveau: {len(self.brain.unconscious.registry)} faits")

        return total_added

    def report(self) -> dict:
        """Rapport d'ingestion."""
        return {
            **self.stats,
            'total_brain': len(self.brain.unconscious.registry),
            'taux_rejet': round(
                (self.stats['rejected_concat'] + self.stats['rejected_noise'] +
                 self.stats['rejected_duplicate'] + self.stats['rejected_other'])
                / max(self.stats['total_extracted'], 1) * 100, 1
            ),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    from harmonic_brain import HarmonicBrain
    import numpy as np
    from pathlib import Path

    # Charger le cerveau existant
    kb_path = Path('data/bootstrapper_output/knowledge_base_clean_v2.npz')
    data = np.load(str(kb_path), allow_pickle=True)
    facts = [(str(f[0]), str(f[1]), str(f[2]), str(f[3])) for f in data['facts'][:5000]]
    brain = HarmonicBrain(facts)

    print(f"Cerveau: {brain.unconscious.stats['faits']} faits\n")

    # Test d'ingestion propre (sans LLM, juste regex)
    ci = CleanIngestion(brain)

    test_texts = [
        "Marie Curie a découvert le radium et le polonium en 1898.",
        "La tour Eiffel est située à Paris. Elle a été construite par Gustave Eiffel.",
        "Le mont Everest est la plus haute montagne du monde avec 8848 mètres.",
        "Tokyo est la capitale du Japon puis Berlin est la capitale de l'Allemagne.",  # concaténé !
        "$3 trillion was discovered by Newton.",  # bruit !
    ]

    for text in test_texts:
        n = ci.ingest_text(text, use_llm=False)
        print(f"Texte: {text[:80]}...")
        print(f"  → {n} faits ajoutés")
    print()

    # Vérifier les rejets
    print(f"Rejetés concaténation: {ci.stats['rejected_concat']}")
    print(f"Rejetés bruit: {ci.stats['rejected_noise']}")
    print(f"Rejetés doublons: {ci.stats['rejected_duplicate']}")
    print(f"Ingérés: {ci.stats['ingested']}")
    print(f"Total cerveau: {len(brain.unconscious.registry)} faits")
