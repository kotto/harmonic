#!/usr/bin/env python3
"""
INGESTION CORPUS MASSIVE — Multi-Sources, Streaming, Checkpoint
=================================================================
Télécharge et ingère du texte généraliste dans l'hologramme 256x256
depuis des corpus open-source gratuits et légaux.

Sources :
  - OpenSubtitles FR (sous-titres films/séries) — conversation naturelle
  - Euronews/Wikinews FR (actualités) — faits, vocabulaire courant
  - Gutenberg FR (livres classiques) — français littéraire
  - Wiktionnaire FR (définitions) — vocabulaire structuré

Stratégie :
  1. Téléchargement streaming (pas de stockage massif)
  2. Nettoyage automatique (balises, doublons, phrases courtes)
  3. Filtrage anti-bruit (ratio lettres/chiffres, langue)
  4. Injection dans l'hologramme avec amplitude adaptative
  5. Checkpoint toutes les 1000 phrases (reprise possible)

Usage :
  python ka_phone/ingest_corpus_massive.py                      # Ingestion complète
  python ka_phone/ingest_corpus_massive.py --source opensubtitles  # Une seule source
  python ka_phone/ingest_corpus_massive.py --quick               # Mode test (1000 phrases)
  python ka_phone/ingest_corpus_massive.py --target 1000000      # Objectif (1M tokens)
  python ka_phone/ingest_corpus_massive.py --resume              # Reprendre au checkpoint
  python ka_phone/ingest_corpus_massive.py --status              # Voir progression
"""

import os, sys, time, json, argparse, re, gzip, io, hashlib
import urllib.request, urllib.error
from typing import Iterator, Tuple, Optional, List, Dict
from datetime import datetime

import numpy as np

# ══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════

HOLOGRAM_SIZE = 256
PHI = 1.618033988749895
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "ingestion")
CHECKPOINT_FILE = os.path.join(DATA_DIR, "checkpoint_corpus.json")
HOLOGRAM_FILE = os.path.join(DATA_DIR, "hologram_generaliste.npy")
VOCAB_FILE = os.path.join(DATA_DIR, "vocab_generaliste.json")
LOG_FILE = os.path.join(DATA_DIR, "ingestion_log.jsonl")

# Amplitude par source (plus bas = moins d'impact, plus haut = plus marqué)
SOURCE_AMPLITUDE = {
    "opensubtitles": 0.12,    # Conversation — léger pour ne pas dominer
    "wikinews": 0.22,          # Actualités — modéré
    "gutenberg": 0.30,         # Littéraire — plus fort (français riche)
    "wiktionnaire": 0.35,      # Définitions — le plus fort (précision)
    "euronews_rss": 0.20,      # Actualités Europe
    "custom_dir": 0.25,        # Dossier personnalisé
}

# URLs des corpus open-source
CORPUS_SOURCES = {
    "opensubtitles": {
        "url": "https://opus.nlpl.eu/download/OpenSubtitles/v2018/mono/OpenSubtitles.raw.fr.gz",
        "type": "gzip_lines",
        "description": "Sous-titres français (conversations naturelles)",
        "max_lines": 500000,
    },
    "wiktionnaire": {
        "url": "https://dumps.wikimedia.org/frwiktionary/latest/frwiktionary-latest-pages-articles.xml.bz2",
        "type": "wiktionary_xml",
        "description": "Wiktionnaire français (définitions)",
        "max_entries": 100000,
    },
}


# ══════════════════════════════════════════════════════════════════════════
# HOLOGRAM ENGINE
# ══════════════════════════════════════════════════════════════════════════

class HologramIngester:
    """
    Ingère du texte dans l'hologramme 256x256.
    Similaire à UserMemory mais optimisé pour l'ingestion massive.
    """

    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or DATA_DIR
        os.makedirs(self.data_dir, exist_ok=True)

        # Charger ou créer l'hologramme
        self.hologram = None
        self.vocab = {}
        self.stats = {
            "total_phrases": 0,
            "total_tokens": 0,
            "total_chars": 0,
            "sources": {},
            "started_at": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
        }
        self._load()

    def _load(self):
        """Charge l'hologramme existant ou en crée un nouveau."""
        if os.path.exists(HOLOGRAM_FILE):
            self.hologram = np.load(HOLOGRAM_FILE)
            print(f"  📂 Hologramme chargé : {HOLOGRAM_FILE}")
        else:
            self.hologram = np.zeros((HOLOGRAM_SIZE, HOLOGRAM_SIZE), dtype=np.complex128)
            print(f"  🆕 Nouvel hologramme créé ({HOLOGRAM_SIZE}x{HOLOGRAM_SIZE})")

        if os.path.exists(VOCAB_FILE):
            with open(VOCAB_FILE, "r", encoding="utf-8") as f:
                self.vocab = json.load(f)
            print(f"  📖 Vocabulaire chargé : {len(self.vocab)} mots")

    def _save(self):
        """Sauvegarde l'hologramme et le vocabulaire."""
        np.save(HOLOGRAM_FILE, self.hologram)
        with open(VOCAB_FILE, "w", encoding="utf-8") as f:
            json.dump(self.vocab, f, ensure_ascii=False, indent=2)
        self.stats["last_update"] = datetime.now().isoformat()

    def _text_to_wave(self, text: str) -> Tuple[float, float]:
        """Convertit un texte en coordonnées (kx, ky) déterministes."""
        h = hashlib.sha256(text.encode()[:200]).hexdigest()
        kx = (int(h[:16], 16) % (HOLOGRAM_SIZE * 100)) / 100.0
        ky = (int(h[16:32], 16) % (HOLOGRAM_SIZE * 100)) / 100.0
        kx = (kx - HOLOGRAM_SIZE / 2) / HOLOGRAM_SIZE * 20
        ky = (ky - HOLOGRAM_SIZE / 2) / HOLOGRAM_SIZE * 20
        return kx, ky

    def _gaussian_wave(self, kx: float, ky: float, amp: float = 0.3, sigma: float = 4.0) -> np.ndarray:
        """Crée un paquet d'onde gaussien."""
        x = np.linspace(-HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE)
        y = np.linspace(-HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE)
        X, Y = np.meshgrid(x, y)
        env = np.exp(-(X ** 2 + Y ** 2) / (2 * sigma ** 2))
        wave = np.exp(1j * (kx * X / 20 + ky * Y / 20))
        return amp * env * wave

    def ingest_phrase(self, phrase: str, source: str = "unknown", amplitude: float = None) -> Dict:
        """
        Ingère une phrase dans l'hologramme.
        Retourne les stats de l'opération.
        """
        if not phrase or len(phrase.strip()) < 10:
            return {"ingested": False, "reason": "phrase_trop_courte"}

        # Nettoyage
        phrase = phrase.strip()
        phrase = re.sub(r'\s+', ' ', phrase)

        # Ratio de filtrage (doit contenir majoritairement des lettres)
        alpha_ratio = sum(1 for c in phrase if c.isalpha() or c.isspace()) / max(len(phrase), 1)
        if alpha_ratio < 0.6:
            return {"ingested": False, "reason": f"alpha_ratio={alpha_ratio:.2f}"}

        # Amplitude
        if amplitude is None:
            amplitude = SOURCE_AMPLITUDE.get(source, 0.2)

        # Coordonnées de l'onde
        kx, ky = self._text_to_wave(phrase)
        wave = self._gaussian_wave(kx, ky, amp=amplitude)

        # Superposition
        self.hologram += wave

        # Normalisation anti-saturation
        max_amp = np.max(np.abs(self.hologram))
        if max_amp > 500.0:
            self.hologram *= 0.98

        # Vocabulaire
        mots = re.findall(r'[a-zéèêëàâîïôûùçœæA-ZÉÈÊËÀÂÎÏÔÛÙÇŒÆ]+', phrase)
        for m in mots:
            m_lower = m.lower()
            self.vocab[m_lower] = self.vocab.get(m_lower, 0) + 1

        # Stats
        tokens = len(phrase.split())
        self.stats["total_phrases"] += 1
        self.stats["total_tokens"] += tokens
        self.stats["total_chars"] += len(phrase)
        self.stats["sources"][source] = self.stats["sources"].get(source, 0) + 1

        return {
            "ingested": True,
            "kx": float(kx), "ky": float(ky),
            "amplitude": amplitude,
            "tokens": tokens,
            "hologram_energy": float(np.sum(np.abs(self.hologram) ** 2)),
        }

    def get_stats_dict(self) -> Dict:
        """Retourne les statistiques complètes."""
        return {
            **self.stats,
            "vocab_size": len(self.vocab),
            "hologram_size": f"{HOLOGRAM_SIZE}x{HOLOGRAM_SIZE}",
            "hologram_energy": float(np.sum(np.abs(self.hologram) ** 2)),
            "hologram_density": float(np.mean(np.abs(self.hologram))),
            "hologram_max": float(np.max(np.abs(self.hologram))),
            "top_vocab": sorted(self.vocab.items(), key=lambda x: -x[1])[:50],
        }


# ══════════════════════════════════════════════════════════════════════════
# CLEANERS & FILTERS
# ══════════════════════════════════════════════════════════════════════════

def clean_opensubtitles_line(line: str) -> Optional[str]:
    """Nettoie une ligne de sous-titre."""
    line = line.strip()
    # Ignorer les lignes vides ou numériques
    if not line or len(line) < 5:
        return None
    # Ignorer les timecodes
    if re.match(r'^\d{2}:\d{2}:\d{2}[,\.]\d{3}', line):
        return None
    # Ignorer les lignes purement numériques
    if re.match(r'^\d+$', line):
        return None
    # Nettoyer les balises HTML/XML
    line = re.sub(r'<[^>]+>', '', line)
    line = re.sub(r'\{[^}]+\}', '', line)
    line = re.sub(r'\[[^\]]+\]', '', line)
    # Supprimer les caractères de contrôle
    line = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', line)
    # Normaliser les espaces
    line = re.sub(r'\s+', ' ', line).strip()
    # Filtrer les lignes trop courtes ou majoritairement non-alpha
    if len(line) < 10:
        return None
    alpha_ratio = sum(1 for c in line if c.isalpha() or c.isspace()) / max(len(line), 1)
    if alpha_ratio < 0.5:
        return None
    return line


def clean_gutenberg_line(line: str) -> Optional[str]:
    """Nettoie une ligne de Gutenberg."""
    line = line.strip()
    if not line or len(line) < 8:
        return None
    # Ignorer les en-têtes/pieds Gutenberg
    if "PROJECT GUTENBERG" in line.upper():
        return None
    if "*** START" in line.upper() or "*** END" in line.upper():
        return None
    if line.startswith("["):
        return None
    # Nettoyer
    line = re.sub(r'\s+', ' ', line).strip()
    if len(line) < 15:
        return None
    return line


def extract_wiktionary_definitions(text: str) -> List[str]:
    """Extrait les définitions du Wiktionnaire (format wiki markup simplifié)."""
    definitions = []
    # Pattern simplifié : lignes avec # (définitions numérotées)
    for line in text.split('\n'):
        line = line.strip()
        # Définition numérotée
        if line.startswith('#') and len(line) > 10:
            # Nettoyer les balises wiki
            cleaned = re.sub(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', r'\1', line[1:])
            cleaned = re.sub(r'\{\{[^}]+\}\}', '', cleaned)
            cleaned = re.sub(r'<[^>]+>', '', cleaned)
            cleaned = re.sub(r"'''?([^']+)'''?", r'\1', cleaned)
            cleaned = cleaned.strip()
            if len(cleaned) > 15:
                definitions.append(cleaned)
    return definitions


def split_into_phrases(text: str) -> List[str]:
    """Découpe un texte en phrases."""
    # Split sur ponctuation forte
    phrases = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in phrases if len(p.strip()) > 10]


# ══════════════════════════════════════════════════════════════════════════
# CORPUS DOWNLOADERS (STREAMING)
# ══════════════════════════════════════════════════════════════════════════

def download_opensubtitles_stream(max_lines: int = 500000) -> Iterator[str]:
    """
    Télécharge OpenSubtitles FR en streaming (gzip → lignes).
    Yield chaque ligne nettoyée.
    """
    url = CORPUS_SOURCES["opensubtitles"]["url"]
    print(f"  📥 Téléchargement streaming: OpenSubtitles FR...")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "KA-Phone-Ingestor/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            # Lire par chunks et décompresser à la volée
            decompressor = gzip.GzipFile(fileobj=io.BytesIO(resp.read()))
            line_count = 0
            for line_bytes in decompressor:
                try:
                    line = line_bytes.decode("utf-8", errors="ignore")
                    cleaned = clean_opensubtitles_line(line)
                    if cleaned:
                        yield cleaned
                        line_count += 1
                        if line_count >= max_lines:
                            break
                except Exception:
                    continue
            print(f"    ✅ {line_count} lignes traitées")
    except urllib.error.HTTPError as e:
        print(f"  ⚠️  Erreur HTTP {e.code} pour OpenSubtitles — source ignorée")
    except Exception as e:
        print(f"  ⚠️  Erreur OpenSubtitles: {e} — source ignorée")


def download_gutenberg_fr_stream() -> Iterator[str]:
    """
    Télécharge des livres Gutenberg FR en streaming.
    Utilise les URLs des livres les plus populaires.
    """
    # Liste de livres Gutenberg FR populaires (domaine public)
    gutenberg_ids = [
        # Les plus téléchargés en français
        "14149",  # Les Misérables (Victor Hugo)
        "17989",  # Le Comte de Monte-Cristo (Dumas)
        "13809",  # Madame Bovary (Flaubert)
        "25566",  # Les Fleurs du mal (Baudelaire)
        "25742",  # Candide (Voltaire)
        "12589",  # Germinal (Zola)
        "14756",  # Le Rouge et le Noir (Stendhal)
        "10879",  # Du côté de chez Swann (Proust)
        "11801",  # Les Trois Mousquetaires (Dumas)
        "1184",   # Vingt mille lieues sous les mers (Verne)
        "399",    # L'Île mystérieuse (Verne)
        "2529",   # Le Tour du monde en 80 jours (Verne)
        "36291",  # Notre-Dame de Paris (Hugo)
        "12735",  # La Chartreuse de Parme (Stendhal)
        "244",    # Le Père Goriot (Balzac)
    ]

    print(f"  📥 Téléchargement streaming: Gutenberg FR ({len(gutenberg_ids)} livres)")

    total_phrases = 0
    for gid in gutenberg_ids:
        url = f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "KA-Phone-Ingestor/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
                lines = text.split('\n')
                in_body = False
                for line in lines:
                    if "*** START" in line:
                        in_body = True
                        continue
                    if "*** END" in line:
                        in_body = False
                        continue
                    if not in_body:
                        continue
                    cleaned = clean_gutenberg_line(line)
                    if cleaned:
                        for phrase in split_into_phrases(cleaned):
                            yield phrase
                            total_phrases += 1
            print(f"    📖 Livre {gid} — OK")
        except Exception as e:
            print(f"    ⚠️ Livre {gid} — erreur: {e}")
            continue

    print(f"    ✅ {total_phrases} phrases extraites de Gutenberg")


def download_wiktionnaire_stream(max_entries: int = 100000) -> Iterator[str]:
    """
    Télécharge le Wiktionnaire FR en streaming (XML → définitions).
    Version simplifiée : utilise l'API au lieu du dump complet.
    """
    print(f"  📥 Téléchargement streaming: Wiktionnaire FR (via API)...")

    # Utiliser l'API MediaWiki pour récupérer des pages de définitions
    # Catégories : mots français, verbes, adjectifs, noms...
    api_url = "https://fr.wiktionary.org/w/api.php"
    categories = [
        "Catégorie:français",
        "Catégorie:Noms_communs_en_français",
        "Catégorie:Verbes_en_français",
        "Catégorie:Adjectifs_en_français",
    ]

    total_extracted = 0
    for category in categories:
        params = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtitle": category,
            "cmlimit": "500",
            "cmtype": "page",
        }
        try:
            query_string = urllib.parse.urlencode(params)
            full_url = f"{api_url}?{query_string}"
            req = urllib.request.Request(full_url, headers={"User-Agent": "KA-Phone-Ingestor/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                members = data.get("query", {}).get("categorymembers", [])
                for member in members:
                    title = member.get("title", "")
                    # Récupérer le contenu de la page
                    page_params = {
                        "action": "query",
                        "format": "json",
                        "titles": title,
                        "prop": "extracts",
                        "exintro": 1,
                        "explaintext": 1,
                    }
                    try:
                        pq = urllib.parse.urlencode(page_params)
                        pu = f"{api_url}?{pq}"
                        preq = urllib.request.Request(pu, headers={"User-Agent": "KA-Phone-Ingestor/1.0"})
                        with urllib.request.urlopen(preq, timeout=10) as presp:
                            pdata = json.loads(presp.read().decode())
                            pages = pdata.get("query", {}).get("pages", {})
                            for pid, pinfo in pages.items():
                                extract = pinfo.get("extract", "")
                                if extract and len(extract) > 20:
                                    # La première phrase est souvent la meilleure définition
                                    first_sentence = extract.split('.')[0].strip()
                                    if len(first_sentence) > 15:
                                        yield first_sentence + "."
                                        total_extracted += 1
                    except Exception:
                        continue

                if total_extracted >= max_entries:
                    break
        except Exception as e:
            print(f"    ⚠️ Erreur catégorie {category}: {e}")
            continue

    print(f"    ✅ {total_extracted} définitions extraites du Wiktionnaire")


def download_wikinews_fr_stream() -> Iterator[str]:
    """
    Récupère des articles Wikinews FR via l'API (actualités).
    Pas besoin de dump complet — l'API donne du texte frais.
    """
    print(f"  📥 Récupération: Wikinews FR (actualités)...")

    api_url = "https://fr.wikinews.org/w/api.php"
    total_extracted = 0

    # Récupérer les pages récentes
    params = {
        "action": "query",
        "format": "json",
        "list": "allpages",
        "apnamespace": "0",  # Articles uniquement
        "aplimit": "500",
    }

    try:
        query_string = urllib.parse.urlencode(params)
        full_url = f"{api_url}?{query_string}"
        req = urllib.request.Request(full_url, headers={"User-Agent": "KA-Phone-Ingestor/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            pages = data.get("query", {}).get("allpages", [])
            for page in pages:
                title = page.get("title", "")
                if title.startswith("Catégorie:") or title.startswith("Wikinews:"):
                    continue
                # Récupérer le contenu
                extract_params = {
                    "action": "query",
                    "format": "json",
                    "titles": title,
                    "prop": "extracts",
                    "explaintext": 1,
                }
                try:
                    eq = urllib.parse.urlencode(extract_params)
                    eu = f"{api_url}?{eq}"
                    ereq = urllib.request.Request(eu, headers={"User-Agent": "KA-Phone-Ingestor/1.0"})
                    with urllib.request.urlopen(ereq, timeout=10) as eresp:
                        edata = json.loads(eresp.read().decode())
                        epages = edata.get("query", {}).get("pages", {})
                        for eid, einfo in epages.items():
                            extract = einfo.get("extract", "")
                            if extract and len(extract) > 30:
                                for phrase in split_into_phrases(extract):
                                    if len(phrase) > 15:
                                        yield phrase
                                        total_extracted += 1
                except Exception:
                    continue

    except Exception as e:
        print(f"    ⚠️ Erreur Wikinews: {e}")

    print(f"    ✅ {total_extracted} phrases extraites de Wikinews")


def read_custom_directory(directory: str) -> Iterator[str]:
    """Lit tous les fichiers texte d'un répertoire."""
    print(f"  📂 Lecture du répertoire: {directory}")

    total_extracted = 0
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(('.txt', '.md', '.rst', '.json', '.jsonl')):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for phrase in split_into_phrases(content):
                            if 15 < len(phrase) < 500:
                                yield phrase
                                total_extracted += 1
                except Exception:
                    continue

    print(f"    ✅ {total_extracted} phrases extraites du répertoire")


# ══════════════════════════════════════════════════════════════════════════
# CHECKPOINT MANAGER
# ══════════════════════════════════════════════════════════════════════════

class CheckpointManager:
    """Gère les checkpoints pour la reprise d'ingestion."""

    def __init__(self, filepath: str = CHECKPOINT_FILE):
        self.filepath = filepath
        self.data = self._load()

    def _load(self) -> Dict:
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": 1,
            "sources_completed": [],
            "sources_current": None,
            "current_offset": 0,
            "total_phrases_ingested": 0,
            "last_saved": None,
        }

    def save(self):
        self.data["last_saved"] = datetime.now().isoformat()
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def mark_source_completed(self, source_name: str):
        if source_name not in self.data["sources_completed"]:
            self.data["sources_completed"].append(source_name)
        self.data["sources_current"] = None
        self.data["current_offset"] = 0
        self.save()

    def update_progress(self, source_name: str, offset: int, total_ingested: int):
        self.data["sources_current"] = source_name
        self.data["current_offset"] = offset
        self.data["total_phrases_ingested"] = total_ingested
        self.save()

    def is_source_completed(self, source_name: str) -> bool:
        return source_name in self.data["sources_completed"]

    def get_resume_info(self) -> Tuple[Optional[str], int]:
        return self.data["sources_current"], self.data["current_offset"]


# ══════════════════════════════════════════════════════════════════════════
# MAIN INGESTION ENGINE
# ══════════════════════════════════════════════════════════════════════════

def run_ingestion(
    hologram: HologramIngester,
    checkpoint: CheckpointManager,
    sources: List[str] = None,
    target_tokens: int = None,
    quick: bool = False,
    save_interval: int = 1000,
):
    """
    Lance l'ingestion massive multi-sources.

    Args:
        hologram: Instance HologramIngester
        checkpoint: Gestionnaire de checkpoint
        sources: Liste des sources à ingérer (None = toutes)
        target_tokens: Nombre cible de tokens (None = pas de limite)
        quick: Mode rapide (1000 phrases max par source)
        save_interval: Sauvegarde toutes les N phrases
    """
    all_sources = {
        "opensubtitles": (download_opensubtitles_stream, {"max_lines": 5000 if quick else 500000}),
        "gutenberg": (download_gutenberg_fr_stream, {}),
        "wiktionnaire": (download_wiktionnaire_stream, {"max_entries": 1000 if quick else 100000}),
        "wikinews": (download_wikinews_fr_stream, {}),
    }

    if sources is None:
        sources = list(all_sources.keys())

    print(f"\n{'=' * 70}")
    print(f"INGESTION CORPUS MASSIVE — Hologramme {HOLOGRAM_SIZE}x{HOLOGRAM_SIZE}")
    print(f"{'=' * 70}")
    print(f"  Mode : {'TEST (rapide)' if quick else 'COMPLET'}")
    print(f"  Sources : {', '.join(sources)}")
    print(f"  Objectif tokens : {target_tokens or 'illimité'}")
    print(f"  Checkpoint : {CHECKPOINT_FILE}")
    print(f"{'=' * 70}")

    t0 = time.time()
    total_phrases_session = 0
    total_ingested_session = 0

    for source_name in sources:
        if source_name not in all_sources:
            print(f"\n  ⚠️ Source inconnue : {source_name} — ignorée")
            continue

        if checkpoint.is_source_completed(source_name) and not quick:
            print(f"\n  ⏭️ Source déjà complétée : {source_name} — sautée")
            continue

        stream_fn, stream_kwargs = all_sources[source_name]
        amplitude = SOURCE_AMPLITUDE.get(source_name, 0.2)

        print(f"\n{'─' * 60}")
        print(f"📦 Source : {source_name.upper()} (amplitude={amplitude:.2f})")
        print(f"{'─' * 60}")

        source_phrases = 0
        source_ingested = 0
        source_tokens = 0
        last_save = 0

        try:
            for phrase in stream_fn(**stream_kwargs):
                source_phrases += 1

                # Mode rapide : limiter par source
                if quick and source_phrases > 1000:
                    break

                # Ingérer
                result = hologram.ingest_phrase(phrase, source=source_name, amplitude=amplitude)

                if result.get("ingested"):
                    source_ingested += 1
                    source_tokens += result.get("tokens", 0)
                    total_ingested_session += 1

                total_phrases_session += 1

                # Sauvegarde périodique
                if source_ingested - last_save >= save_interval:
                    hologram._save()
                    checkpoint.update_progress(source_name, source_phrases,
                                               checkpoint.data["total_phrases_ingested"] + source_ingested)
                    last_save = source_ingested

                    dt = time.time() - t0
                    v = total_phrases_session / dt if dt > 0 else 0
                    print(f"  [{source_ingested} ingérées] {source_phrases} phrases, "
                          f"{source_tokens} tokens | {v:.0f} phrases/sec")

                # Vérifier l'objectif de tokens
                if target_tokens and hologram.stats["total_tokens"] >= target_tokens:
                    print(f"\n  🎯 Objectif atteint : {hologram.stats['total_tokens']} tokens")
                    break

        except KeyboardInterrupt:
            print(f"\n  ⏸️ Interruption — sauvegarde...")
            hologram._save()
            checkpoint.update_progress(source_name, source_phrases,
                                       checkpoint.data["total_phrases_ingested"] + source_ingested)
            print(f"  ✅ Sauvegardé. Reprenez avec --resume")
            return

        # Fin de source
        print(f"  📊 {source_name}: {source_ingested}/{source_phrases} phrases ingérées, {source_tokens} tokens")
        checkpoint.mark_source_completed(source_name)

        if target_tokens and hologram.stats["total_tokens"] >= target_tokens:
            break

    # Sauvegarde finale
    hologram._save()
    checkpoint.save()

    dt = time.time() - t0

    print(f"\n{'=' * 70}")
    print(f"✅ INGESTION TERMINÉE")
    print(f"{'=' * 70}")
    print(f"  Durée          : {dt / 60:.1f} min")
    print(f"  Phrases traitées : {total_phrases_session:,}")
    print(f"  Phrases ingérées : {total_ingested_session:,}")
    print(f"  Tokens totaux    : {hologram.stats['total_tokens']:,}")
    print(f"  Vocabulaire      : {len(hologram.vocab):,} mots")
    print(f"  Énergie hologramme : {np.sum(np.abs(hologram.hologram) ** 2):.0f}")
    print(f"  Sources :")
    for src, count in sorted(hologram.stats["sources"].items()):
        print(f"    - {src}: {count} phrases")
    print(f"{'=' * 70}")


def show_status():
    """Affiche l'état actuel de l'ingestion."""
    print(f"\n{'=' * 50}")
    print(f"STATUT DE L'INGESTION")
    print(f"{'=' * 50}")

    if not os.path.exists(HOLOGRAM_FILE):
        print("  Aucune ingestion en cours.")
        print("  Lancez : python ka_phone/ingest_corpus_massive.py")
        return

    hologram = np.load(HOLOGRAM_FILE)
    print(f"  Hologramme : {HOLOGRAM_SIZE}x{HOLOGRAM_SIZE}")
    print(f"  Énergie    : {np.sum(np.abs(hologram) ** 2):.0f}")
    print(f"  Densité    : {np.mean(np.abs(hologram)):.4f}")
    print(f"  Max        : {np.max(np.abs(hologram)):.2f}")

    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            cp = json.load(f)
        print(f"  Sources complétées : {cp.get('sources_completed', [])}")
        print(f"  Source en cours    : {cp.get('sources_current', 'aucune')}")
        print(f"  Phrases ingérées   : {cp.get('total_phrases_ingested', 0):,}")
        print(f"  Dernière sauvegarde: {cp.get('last_saved', 'jamais')}")

    if os.path.exists(VOCAB_FILE):
        with open(VOCAB_FILE, 'r', encoding='utf-8') as f:
            vocab = json.load(f)
        print(f"  Vocabulaire        : {len(vocab)} mots")
        top = sorted(vocab.items(), key=lambda x: -x[1])[:10]
        print(f"  Top 10 : {', '.join(f'{w}({c})' for w, c in top)}")


# ══════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Ingestion Corpus Massif — Généralisation KA Phone",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python ka_phone/ingest_corpus_massive.py                         # Complet toutes sources
  python ka_phone/ingest_corpus_massive.py --quick                 # Test rapide
  python ka_phone/ingest_corpus_massive.py --source opensubtitles  # Une seule source
  python ka_phone/ingest_corpus_massive.py --target 500000         # 500K tokens
  python ka_phone/ingest_corpus_massive.py --resume                # Reprendre
  python ka_phone/ingest_corpus_massive.py --status                # Voir progression
  python ka_phone/ingest_corpus_massive.py --dir ./mes_textes/     # Dossier perso
        """
    )

    parser.add_argument("--quick", action="store_true",
                       help="Mode rapide (1000 phrases par source)")
    parser.add_argument("--source", type=str, default=None,
                       help="Source unique (opensubtitles, gutenberg, wiktionnaire, wikinews)")
    parser.add_argument("--target", type=int, default=None,
                       help="Nombre cible de tokens à ingérer")
    parser.add_argument("--resume", action="store_true",
                       help="Reprendre l'ingestion au checkpoint")
    parser.add_argument("--status", action="store_true",
                       help="Afficher l'état de l'ingestion")
    parser.add_argument("--dir", type=str, default=None,
                       help="Ingérer un répertoire de fichiers texte")
    parser.add_argument("--save-interval", type=int, default=1000,
                       help="Intervalle de sauvegarde en phrases (défaut: 1000)")

    args = parser.parse_args()

    # Status
    if args.status:
        show_status()
        return

    # Initialiser
    hologram = HologramIngester()
    checkpoint = CheckpointManager()

    if args.resume:
        resume_source, resume_offset = checkpoint.get_resume_info()
        print(f"  🔄 Reprise : source={resume_source}, offset={resume_offset}")

    # Déterminer les sources
    if args.dir:
        sources_list = ["custom_dir"]
        print(f"\n  📂 Ingestion du répertoire : {args.dir}")
        # Ingest custom directory directly
        hologram = HologramIngester()
        count = 0
        for phrase in read_custom_directory(args.dir):
            result = hologram.ingest_phrase(phrase, source="custom_dir", amplitude=0.25)
            if result.get("ingested"):
                count += 1
            if count % 500 == 0:
                hologram._save()
                print(f"  [{count}] phrases ingérées...")
        hologram._save()
        print(f"  ✅ {count} phrases ingérées depuis {args.dir}")
        return

    if args.source:
        sources_list = [args.source]
    else:
        sources_list = None  # Toutes

    # Lancer
    run_ingestion(
        hologram=hologram,
        checkpoint=checkpoint,
        sources=sources_list,
        target_tokens=args.target,
        quick=args.quick,
        save_interval=args.save_interval,
    )

    # Stats finales
    stats = hologram.get_stats_dict()
    print(f"\n📊 RÉSUMÉ FINAL")
    print(f"  Tokens totaux   : {stats['total_tokens']:,}")
    print(f"  Phrases totales : {stats['total_phrases']:,}")
    print(f"  Vocabulaire     : {stats['vocab_size']:,} mots")
    print(f"  Énergie         : {stats['hologram_energy']:.0f}")
    print(f"  Densité         : {stats['hologram_density']:.4f}")


if __name__ == "__main__":
    main()