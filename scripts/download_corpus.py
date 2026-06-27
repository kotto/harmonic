#!/usr/bin/env python3
"""
Script de téléchargement des corpus vocaux de référence
========================================================
Télécharge les 8 corpus listés dans IMPLEMENTATION_MODELE_VOCAL_HARMONIQUE.md :
  - LJSpeech (24h) — priorité 1, référence mono-locuteur
  - CSS10 FR (1 langue) — priorité 1, français natif
  - VCTK (110 locuteurs) — priorité 2, diversité timbres
  - TED-LIUM v3 (conférences) — priorité 2, prosodie naturelle
  - LibriTTS (585h) — priorité 3, entraînement principal
  - Common Voice FR (Mozilla) — priorité 3, masse multilingue
  - LibriSpeech (1000h) — priorité 4, base propre (optionnel)
  - Fleurs (Google) — priorité 4, couverture linguistique (optionnel)

Volumes estimés : ~50-80 Go (corpus prioritaires), ~200 Go (complet)
Stockage : data/corpus/

Usage :
    python scripts/download_corpus.py                    # Tous les corpus
    python scripts/download_corpus.py --priority 1       # Que priorité 1
    python scripts/download_corpus.py --priority 1,2     # Priorités 1 et 2
    python scripts/download_corpus.py --list             # Lister sans télécharger
"""

import os
import sys
import json
import time
import argparse
import subprocess
import shutil
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# =========================================================================
# CONFIGURATION
# =========================================================================

CORPUS_DIR = Path("data/corpus")
LOG_FILE = CORPUS_DIR / "download_log.json"

# 8 corpus avec URLs et métadonnées
CORPUS_CONFIG = {
    "ljspeech": {
        "name": "LJSpeech-1.1",
        "description": "24h, 1 voix feminine US, excellente qualite",
        "priority": 1,
        "size_gb": 2.6,
        "url": "https://data.keithito.com/data/speech/LJSpeech-1.1.tar.bz2",
        "format": "tar.bz2",
        "extract_dir": "LJSpeech-1.1",
        "audio_format": ".wav",
        "hours": 24,
        "speakers": 1,
        "language": "en-US",
    },
    "css10_fr": {
        "name": "CSS10-FR",
        "description": "Francais natif, bonne qualite",
        "priority": 1,
        "size_gb": 0.15,
        "url": "https://github.com/Kyubyong/css10/archive/refs/heads/master.zip",
        "format": "zip",
        "extract_dir": "css10-master/fr",
        "audio_format": ".wav",
        "hours": 2,
        "speakers": 1,
        "language": "fr-FR",
    },
    "vctk": {
        "name": "VCTK-Corpus-0.92",
        "description": "110 locuteurs anglais, qualite studio",
        "priority": 2,
        "size_gb": 11,
        "url": "https://datashare.ed.ac.uk/download/DS_10283_3443.zip",
        "format": "zip",
        "extract_dir": "VCTK-Corpus-0.92/wav48_silence_trimmed",
        "audio_format": ".flac",
        "hours": 44,
        "speakers": 110,
        "language": "en-UK",
        "alt_url": "https://zenodo.org/record/6387820/files/VCTK-Corpus-0.92.zip",
    },
    "tedlium": {
        "name": "TED-LIUM Release 3",
        "description": "Conferences TED, prosodie naturelle",
        "priority": 2,
        "size_gb": 23,
        "url": "https://projets-lium.univ-lemans.fr/wp-content/uploads/corpus/TED-LIUM/TEDLIUM_release-3.tgz",
        "format": "tgz",
        "extract_dir": "TEDLIUM_release-3",
        "audio_format": ".sph",
        "hours": 452,
        "speakers": 2000,
        "language": "multilingual",
        "alt_url": "https://www.openslr.org/resources/51/TEDLIUM_release-3.tgz",
    },
    "libritts": {
        "name": "LibriTTS",
        "description": "585h anglais, tres haute qualite, entrainement principal",
        "priority": 3,
        "size_gb": 40,
        "url": "https://www.openslr.org/resources/60/",
        "format": "multi_tar",
        "extract_dir": "LibriTTS",
        "audio_format": ".wav",
        "hours": 585,
        "speakers": 2456,
        "language": "en-US",
        "sub_parts": [
            "train-clean-100.tar.gz",
            "train-clean-360.tar.gz",
            "dev-clean.tar.gz",
            "test-clean.tar.gz",
        ],
    },
    "common_voice_fr": {
        "name": "Common Voice FR 19.0",
        "description": "Mozilla Common Voice, francais, grande masse",
        "priority": 3,
        "size_gb": 45,
        "url": "https://mozilla-common-voice-datasets.s3.us-west-2.amazonaws.com/cv-corpus-19.0/cv-corpus-19.0-2025-09-10-fr.tar.gz",
        "format": "tar.gz",
        "extract_dir": "cv-corpus-19.0-fr",
        "audio_format": ".mp3",
        "hours": 600,
        "speakers": 8000,
        "language": "fr-FR",
    },
    "librispeech": {
        "name": "LibriSpeech",
        "description": "1000h anglais, base propre (optionnel)",
        "priority": 4,
        "size_gb": 60,
        "url": "https://www.openslr.org/resources/12/",
        "format": "multi_tar",
        "extract_dir": "LibriSpeech",
        "audio_format": ".flac",
        "hours": 1000,
        "speakers": 2484,
        "language": "en-US",
        "sub_parts": [
            "train-clean-100.tar.gz",
            "train-clean-360.tar.gz",
            "train-other-500.tar.gz",
            "dev-clean.tar.gz",
            "dev-other.tar.gz",
            "test-clean.tar.gz",
            "test-other.tar.gz",
        ],
        "optional": True,
    },
    "fleurs": {
        "name": "Fleurs (Google)",
        "description": "100+ langues, couverture linguistique (optionnel)",
        "priority": 4,
        "size_gb": 12,
        "url": "https://storage.googleapis.com/xtreme_translations/FLEURS/fleurs-fr_fr.tar.gz",
        "format": "tar.gz",
        "extract_dir": "fleurs_fr",
        "audio_format": ".wav",
        "hours": 12,
        "speakers": 100,
        "language": "fr-FR",
        "optional": True,
    },
}


# =========================================================================
# FONCTIONS DE TÉLÉCHARGEMENT
# =========================================================================

def download_file(url: str, dest_path: Path, description: str = "",
                  timeout: int = 3600) -> bool:
    """
    Télécharge un fichier avec barre de progression.

    Args:
        url: URL du fichier
        dest_path: Chemin de destination
        description: Description pour l'affichage
        timeout: Timeout en secondes

    Returns:
        True si succès
    """
    import urllib.request
    import urllib.error

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if dest_path.exists():
        size = dest_path.stat().st_size
        if size > 1000:  # Fichier > 1 Ko, on suppose complet
            print(f"  [SKIP] {description} deja present ({size / 1e6:.1f} Mo)")
            return True
        print(f"  [RETRY] {description} incomplet ({size} octets), re-telechargement...")
        dest_path.unlink()

    print(f"  [DOWNLOAD] {description} -> {dest_path.name}")

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (HarmonicAI Voice Corpus Downloader)'
        })

        with urllib.request.urlopen(req, timeout=timeout) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            chunk_size = 8192 * 8  # 64 Ko

            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total_size > 0:
                        pct = downloaded / total_size * 100
                        mb = downloaded / 1e6
                        total_mb = total_size / 1e6
                        print(f"\r    {pct:5.1f}% ({mb:.0f}/{total_mb:.0f} Mo)",
                              end='', flush=True)

            if total_size > 0:
                print()  # Nouvelle ligne après la progression
            print(f"  [OK] {description} telecharge ({downloaded / 1e6:.1f} Mo)")
            return True

    except urllib.error.HTTPError as e:
        print(f"\n  [ERROR] HTTP {e.code} pour {url}")
        return False
    except urllib.error.URLError as e:
        print(f"\n  [ERROR] URL invalide pour {url}: {e.reason}")
        return False
    except Exception as e:
        print(f"\n  [ERROR] {e}")
        return False


def extract_archive(archive_path: Path, extract_to: Path,
                    archive_format: str) -> bool:
    """
    Extrait une archive.

    Args:
        archive_path: Chemin de l'archive
        extract_to: Répertoire d'extraction
        archive_format: 'zip', 'tar.gz', 'tar.bz2', 'tgz', 'tar'

    Returns:
        True si succès
    """
    extract_to.mkdir(parents=True, exist_ok=True)

    print(f"  [EXTRACT] {archive_path.name} -> {extract_to}")

    try:
        if archive_format == 'zip':
            with zipfile.ZipFile(archive_path, 'r') as zf:
                total = len(zf.namelist())
                for i, member in enumerate(zf.namelist()):
                    zf.extract(member, extract_to)
                    if i % 100 == 0:
                        print(f"\r    {i / total * 100:5.1f}%", end='', flush=True)
                print()

        elif archive_format in ('tar.gz', 'tar.bz2', 'tgz', 'tar'):
            mode = 'r:gz' if archive_format in ('tar.gz', 'tgz') else 'r:bz2'
            with tarfile.open(archive_path, mode) as tf:
                tf.extractall(path=extract_to)
            print(f"    OK")

        else:
            print(f"  [ERROR] Format d'archive inconnu: {archive_format}")
            return False

        print(f"  [OK] Archive extraite dans {extract_to}")
        return True

    except Exception as e:
        print(f"  [ERROR] Extraction echouee: {e}")
        return False


def download_corpus(corpus_id: str, config: Dict,
                    corpus_dir: Path, log: Dict) -> bool:
    """
    Télécharge et extrait un corpus complet.

    Args:
        corpus_id: Identifiant du corpus
        config: Configuration du corpus
        corpus_dir: Répertoire racine des corpus
        log: Dictionnaire de log

    Returns:
        True si succès
    """
    name = config['name']
    desc = config['description']

    print(f"\n{'=' * 60}")
    print(f"Corpus: {name} (priorite {config['priority']})")
    print(f"  {desc}")
    print(f"  Volume: ~{config['size_gb']:.1f} Go | "
          f"{config['hours']}h | {config['speakers']} locuteurs")
    print(f"{'=' * 60}")

    target_dir = corpus_dir / corpus_id
    target_dir.mkdir(parents=True, exist_ok=True)

    archive_format = config['format']
    ext = '.zip' if archive_format == 'zip' else \
          '.tar.bz2' if archive_format == 'tar.bz2' else \
          '.tgz' if archive_format == 'tgz' else '.tar.gz'

    # Cas spécial : multi-part (plusieurs fichiers tar.gz)
    if archive_format == 'multi_tar':
        base_url = config['url']
        all_ok = True

        for part in config.get('sub_parts', []):
            part_url = base_url + part
            part_path = target_dir / part
            part_dir = target_dir / part.replace('.tar.gz', '').replace('.tgz', '')

            if part_dir.exists() and any(part_dir.iterdir()):
                print(f"  [SKIP] {part} deja extrait")
                continue

            if download_file(part_url, part_path,
                           f"{name}/{part}", timeout=7200):
                for fmt in ['tar.gz', 'tgz', 'tar']:
                    if extract_archive(part_path, part_dir, fmt):
                        break
                part_path.unlink(missing_ok=True)  # Nettoyer
            else:
                all_ok = False
                # Essayer URL alternative si dispo
                if 'alt_url' in config and part == config['sub_parts'][0]:
                    alt_url = config['alt_url']
                    print(f"  [ALT] Tentative URL alternative: {alt_url}")
                    alt_path = target_dir / "alt_download" / f"{name}.{archive_format}"
                    if download_file(alt_url, alt_path, f"{name} (alt)", timeout=7200):
                        extract_archive(alt_path, target_dir, archive_format)
                        alt_path.unlink(missing_ok=True)

        return all_ok

    # Téléchargement simple
    archive_path = target_dir / f"{corpus_id}{ext}"

    # Vérifier si déjà extrait
    extract_dir = target_dir / config['extract_dir']
    if extract_dir.exists() and any(extract_dir.iterdir()):
        print(f"  [SKIP] {name} deja present dans {extract_dir}")
        log[corpus_id] = {"status": "already_present", "path": str(extract_dir)}
        return True

    # Télécharger
    if not download_file(config['url'], archive_path, name, timeout=7200):
        # Essayer URL alternative
        if 'alt_url' in config:
            print(f"  [ALT] Tentative URL alternative: {config['alt_url']}")
            if not download_file(config['alt_url'], archive_path,
                               f"{name} (alt)", timeout=7200):
                log[corpus_id] = {"status": "download_failed"}
                return False
        else:
            log[corpus_id] = {"status": "download_failed"}
            return False

    # Extraire
    if extract_archive(archive_path, target_dir, archive_format):
        # Nettoyer l'archive
        archive_path.unlink(missing_ok=True)
        log[corpus_id] = {"status": "success", "path": str(extract_dir)}
        return True
    else:
        log[corpus_id] = {"status": "extract_failed"}
        return False


# =========================================================================
# MAIN
# =========================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Telechargement des corpus vocaux de reference"
    )
    parser.add_argument('--priority', type=str, default="1,2,3,4",
                        help="Priorites a telecharger (ex: 1,2)")
    parser.add_argument('--corpus', type=str, default=None,
                        help="Corpus specifique (ex: ljspeech,vctk)")
    parser.add_argument('--list', action='store_true',
                        help="Lister les corpus sans telecharger")
    parser.add_argument('--dir', type=str, default=str(CORPUS_DIR),
                        help="Repertoire de destination")
    parser.add_argument('--force', action='store_true',
                        help="Forcer le re-telechargement")
    parser.add_argument('--skip-optional', action='store_true',
                        help="Ignorer les corpus optionnels")
    args = parser.parse_args()

    corpus_dir = Path(args.dir)
    corpus_dir.mkdir(parents=True, exist_ok=True)

    priorities = set(int(p.strip()) for p in args.priority.split(','))

    # Charger le log existant
    log = {}
    if LOG_FILE.exists():
        with open(LOG_FILE, 'r') as f:
            log = json.load(f)

    # Filtrer les corpus
    if args.corpus:
        corpus_ids = [c.strip() for c in args.corpus.split(',')]
        selected = {cid: CORPUS_CONFIG[cid] for cid in corpus_ids if cid in CORPUS_CONFIG}
    else:
        selected = {
            cid: cfg for cid, cfg in CORPUS_CONFIG.items()
            if cfg['priority'] in priorities
            and not (args.skip_optional and cfg.get('optional', False))
        }

    # Lister
    if args.list:
        print("=" * 80)
        print("CORPUS VOCAUX DE REFERENCE")
        print("=" * 80)
        total_hours = 0
        total_size = 0
        for cid, cfg in sorted(CORPUS_CONFIG.items(), key=lambda x: x[1]['priority']):
            status = log.get(cid, {}).get('status', 'not_downloaded')
            marker = "[*]" if status == "success" else "[ ]"
            optional = " (OPTIONNEL)" if cfg.get('optional') else ""
            print(f"  {marker} P{cfg['priority']} {cfg['name']:<25} "
                  f"{cfg['hours']:>5}h | {cfg['speakers']:>5} locuteurs | "
                  f"~{cfg['size_gb']:>5.1f} Go | {cfg['language']}{optional}")
            print(f"       {cfg['description']}")
            if status != "not_downloaded":
                print(f"       Status: {status} -> {log[cid].get('path', '')}")
            total_hours += cfg['hours']
            total_size += cfg['size_gb']
        print(f"\n  Total: {total_hours}h, ~{total_size:.0f} Go")
        print("=" * 80)
        return 0

    # Télécharger
    print("=" * 80)
    print("TELECHARGEMENT DES CORPUS VOCAUX DE REFERENCE")
    print(f"Destination: {corpus_dir.absolute()}")
    print(f"Priorites: {sorted(priorities)}")
    print(f"Corpus selectionnes: {len(selected)}")
    total_size = sum(c['size_gb'] for c in selected.values())
    total_hours = sum(c['hours'] for c in selected.values())
    print(f"Volume estime: ~{total_size:.0f} Go | {total_hours}h")
    print("=" * 80)

    # Vérifier espace disque
    try:
        import shutil as sh
        usage = sh.disk_usage(corpus_dir)
        free_gb = usage.free / 1e9
        print(f"\nEspace disque disponible: {free_gb:.1f} Go")
        if free_gb < total_size * 1.2:
            print(f"[WARN] Espace disque insuffisant ! "
                  f"Besoin: ~{total_size * 1.2:.0f} Go, "
                  f"Disponible: {free_gb:.0f} Go")
            proceed = input("Continuer quand meme ? (o/N) ").strip().lower()
            if proceed != 'o':
                print("Annule.")
                return 1
    except Exception:
        pass

    # Téléchargement séquentiel (les corpus sont volumineux)
    success_count = 0
    failed_list = []

    for corpus_id, config in sorted(selected.items(), key=lambda x: x[1]['priority']):
        if args.force:
            # Supprimer le log pour forcer le re-téléchargement
            log.pop(corpus_id, None)

        if download_corpus(corpus_id, config, corpus_dir, log):
            success_count += 1
        else:
            failed_list.append(corpus_id)

        # Sauvegarder le log après chaque corpus
        with open(LOG_FILE, 'w') as f:
            json.dump(log, f, indent=2)

    # Résumé
    print("\n" + "=" * 80)
    print(f"RESULTAT: {success_count}/{len(selected)} corpus telecharges avec succes")
    if failed_list:
        print(f"Echecs: {', '.join(failed_list)}")
    print(f"Log sauvegarde dans: {LOG_FILE}")
    print("=" * 80)

    # Afficher la commande d'extraction
    if success_count > 0:
        print(f"\nProchaine etape :")
        print(f"  python -c \"from engine.spectral_voice_pipeline import get_pipeline; "
              f"p = get_pipeline(); "
              f"p.extract_corpus_signatures('{corpus_dir}')\"")
        print(f"\nPuis entrainement :")
        print(f"  python -c \"from engine.spectral_voice_pipeline import get_pipeline; "
              f"p = get_pipeline(); "
              f"p.train('{corpus_dir / 'corpus_signatures_*.json'}', epochs=200)\"")

    return 0 if len(failed_list) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())