"""
🌊 Wave Orchestrator — Chef d'orchestre de l'écosystème ondulatoire
====================================================================

Ce module lit les tables d'équivalence ondulatoires, détecte les gaps,
et orchestre les skills pour maintenir la cohérence globale.

Usage :
    python orchestrator.py status       # Afficher l'état de l'écosystème
    python orchestrator.py gaps         # Lister les gaps
    python orchestrator.py coverage     # Couverture des skills
    python orchestrator.py sync         # Synchroniser les tables

Architecture :
    orchestrator.py
      ├── lit TRADUCTION_ONDULATOIRE_*.md
      ├── parse les tableaux markdown
      ├── détecte les 🆕 et les fichiers manquants
      └── génère les recommandations
"""

from __future__ import annotations

import os
import re
import sys
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════════
# MODÈLES DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Equivalence:
    """Une ligne d'un tableau d'équivalence."""
    number: int
    capability: str
    equivalent: str
    file: str
    status: str  # ✅ ou 🆕
    domain: str  # "LLM", "TTS", "HPU"

@dataclass
class TableStatus:
    """Statut d'une table d'équivalence."""
    path: str
    domain: str
    total: int = 0
    existing: int = 0
    missing: int = 0
    equivalences: List[Equivalence] = field(default_factory=list)

@dataclass
class EcosystemStatus:
    """Statut global de l'écosystème."""
    tables: List[TableStatus] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    adapters: List[str] = field(default_factory=list)
    total_equivalences: int = 0
    total_existing: int = 0
    total_missing: int = 0
    gaps: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# PARSER DE TABLEAUX MARKDOWN
# ═══════════════════════════════════════════════════════════════════════════════

def parse_equivalence_table(filepath: str, domain: str) -> TableStatus:
    """
    Parse un tableau d'équivalence markdown.

    Cherche les lignes de tableau du type :
    | # | Capacité | Équivalent | Fichier | Statut |
    """
    if not os.path.exists(filepath):
        return TableStatus(path=filepath, domain=domain)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    status = TableStatus(path=filepath, domain=domain)
    equivalences = []

    # Pattern pour les lignes de tableau d'équivalence
    # Format : | 1 | Capacité LLM | Équivalent Ondulatoire | `fichier.py` | ✅/🆕 |
    # L'équivalent peut contenir des | échappés (\|) et des formules LaTeX
    pattern = re.compile(
        r'\|\s*(\d+)\s*\|'           # numéro
        r'\s*(.+?)\s*\|'             # capacité (non-greedy jusqu'au prochain |)
        r'\s*(.+?)\s*\|'             # équivalent
        r'\s*`?([^`|\n]+?)`?\s*\|'   # fichier (sans backticks)
        r'\s*(✅|🆕)\s*\|'           # statut
    )

    for match in pattern.finditer(content):
        num = int(match.group(1))
        capability = match.group(2).strip()
        equivalent = match.group(3).strip()
        filename = match.group(4).strip()
        status_mark = match.group(5).strip()

        eq = Equivalence(
            number=num,
            capability=capability,
            equivalent=equivalent,
            file=filename,
            status=status_mark,
            domain=domain,
        )
        equivalences.append(eq)

        if status_mark == '✅':
            status.existing += 1
        else:
            status.missing += 1

    status.total = len(equivalences)
    status.equivalences = equivalences

    return status


def check_file_exists(filename: str, search_dirs: List[str] = None) -> bool:
    """
    Vérifie si un fichier existe dans l'arborescence du projet.

    Args:
        filename: nom du fichier à chercher
        search_dirs: répertoires où chercher

    Returns:
        True si le fichier existe quelque part
    """
    if search_dirs is None:
        search_dirs = [
            'vital-ka/core/python/',
            'ka_sonic/',
            'alphafold/',
            '',  # racine
        ]

    # Noms spéciaux
    if filename in ('Partout', 'Architecture'):
        return True

    filename_clean = filename.strip('`').strip()
    # Supprimer les suffixes comme :decode(), :encode(), etc.
    filename_clean = re.sub(r':\w+\(\)', '', filename_clean)
    filename_clean = filename_clean.strip()

    for d in search_dirs:
        full_path = os.path.join(d, filename_clean)
        if os.path.exists(full_path):
            return True

    # Chercher récursivement dans vital-ka/
    for root, dirs, files in os.walk('vital-ka'):
        if filename_clean in files:
            return True

    # Chercher à la racine
    if os.path.exists(filename_clean):
        return True

    return False


def verify_files(table: TableStatus, project_root: str = '.') -> List[str]:
    """
    Vérifie que tous les fichiers listés dans une table existent réellement.

    Returns:
        liste des fichiers marqués ✅ mais introuvables
    """
    issues = []
    original_cwd = os.getcwd()

    try:
        if project_root != '.':
            os.chdir(project_root)

        for eq in table.equivalences:
            if eq.status == '✅' and eq.file not in ('Partout', 'Architecture'):
                if not check_file_exists(eq.file):
                    issues.append(
                        f"{table.domain}#{eq.number}: {eq.file} marqué ✅ mais introuvable"
                    )
            elif eq.status == '🆕':
                # Vérifier si le fichier existe quand même (désynchronisation)
                if check_file_exists(eq.file):
                    issues.append(
                        f"{table.domain}#{eq.number}: {eq.file} marqué 🆕 mais existe déjà"
                    )
    finally:
        if project_root != '.':
            os.chdir(original_cwd)

    return issues


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSE DE L'ÉCOSYSTÈME
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_ecosystem(project_root: str = '.') -> EcosystemStatus:
    """
    Analyse complète de l'écosystème ondulatoire.

    Returns:
        EcosystemStatus avec l'état global
    """
    eco = EcosystemStatus()

    # Tables d'équivalence
    tables_config = [
        ('TRADUCTION_ONDULATOIRE_LLM.md', 'LLM'),
        ('TRADUCTION_ONDULATOIRE_TTS.md', 'TTS'),
    ]

    for filepath, domain in tables_config:
        full_path = os.path.join(project_root, filepath)
        table = parse_equivalence_table(full_path, domain)
        eco.tables.append(table)
        eco.total_equivalences += table.total
        eco.total_existing += table.existing
        eco.total_missing += table.missing

    # Skills disponibles
    skills_dir = os.path.join(project_root, '.agents', 'skills')
    if os.path.exists(skills_dir):
        eco.skills = [
            d for d in os.listdir(skills_dir)
            if os.path.isdir(os.path.join(skills_dir, d)) and not d.startswith('.')
        ]

    # Adaptateurs wave-bridge
    adapters = [
        # TTS/Audio
        'PsiDiphoneBank', 'ABCMemoryKernel', 'HarmonicEnergyCore',
        'SpectralAnalyzer', 'VoiceSignature', 'GlottalSource', 'HarmonicCloner',
        # LLM v1
        'CoherenceAttention', 'HolographicEncoderBridge', 'PhasePropagator',
        'WaveDecoderBridge', 'HolographicRAG', 'FewShotPhaseLock', 'CoherenceGate',
        # LLM v2
        'FeedbackLoopBridge', 'WaveSamplingBridge', 'WaveToolUseBridge',
        'WaveBeamSearchBridge', 'WavePerplexityBridge',
        # LLM v3
        'WaveFineTuneBridge', 'DomainGateBridge', 'SystemPromptBridge',
        'WavePoetryBridge', 'WaveNarrativeBridge', 'WaveSynthesizerBridge',
        # LLM v4
        'WaveStylerBridge', 'HarmonicStyleBridge', 'HologramLoaderBridge',
    ]
    eco.adapters = adapters

    # Détecter les gaps
    for table in eco.tables:
        for eq in table.equivalences:
            if eq.status == '🆕':
                eco.gaps.append(f"[{table.domain}] #{eq.number} {eq.capability} → {eq.file} (🆕)")

    # Vérifier les fichiers
    for table in eco.tables:
        issues = verify_files(table, project_root)
        for issue in issues:
            eco.gaps.append(f"[VÉRIFICATION] {issue}")

    return eco


# ═══════════════════════════════════════════════════════════════════════════════
# COMMANDES
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_status(project_root: str = '.') -> str:
    """Affiche le statut complet de l'écosystème."""
    eco = analyze_ecosystem(project_root)

    lines = [
        "=" * 65,
        "  🌊 WAVE ORCHESTRATOR — Statut de l'écosystème ondulatoire",
        "=" * 65,
        "",
    ]

    # Résumé global
    lines.append("📊 RÉSUMÉ GLOBAL")
    lines.append(f"  Équivalences totales : {eco.total_equivalences}")
    lines.append(f"  Existantes (✅)      : {eco.total_existing} ({100*eco.total_existing/max(1,eco.total_equivalences):.0f}%)")
    lines.append(f"  Manquantes (🆕)      : {eco.total_missing}")
    lines.append(f"  Skills actifs        : {len(eco.skills)}")
    lines.append(f"  Adaptateurs          : {len(eco.adapters)}")
    lines.append("")

    # Par table
    for table in eco.tables:
        pct = 100 * table.existing / max(1, table.total)
        lines.append(f"📋 {table.domain} : {table.existing}/{table.total} ({pct:.0f}%) — {table.path}")
        if table.missing > 0:
            missing_items = [f"#{e.number} {e.capability}" for e in table.equivalences if e.status == '🆕']
            for m in missing_items:
                lines.append(f"   🆕 {m}")
        lines.append("")

    # Skills
    lines.append("🔧 SKILLS")
    for skill in sorted(eco.skills):
        lines.append(f"  - {skill}")
    lines.append("")

    # Adaptateurs
    lines.append("🔌 ADAPTATEURS WAVE-BRIDGE")
    tts_adapters = eco.adapters[:7]
    llm_adapters = eco.adapters[7:]
    lines.append(f"  TTS/Audio ({len(tts_adapters)}) : {', '.join(tts_adapters)}")
    lines.append(f"  LLM ({len(llm_adapters)})      : {', '.join(llm_adapters)}")
    lines.append("")

    # Gaps
    if eco.gaps:
        lines.append("⚠️  GAPS DÉTECTÉS")
        for gap in eco.gaps:
            lines.append(f"  - {gap}")
        lines.append("")
    else:
        lines.append("✅ Aucun gap détecté — écosystème cohérent.")
        lines.append("")

    lines.append("=" * 65)
    return "\n".join(lines)


def cmd_gaps(project_root: str = '.') -> str:
    """Liste uniquement les gaps."""
    eco = analyze_ecosystem(project_root)

    if not eco.gaps:
        return "✅ Aucun gap détecté."

    lines = ["⚠️  Gaps détectés :", ""]
    for gap in eco.gaps:
        lines.append(f"  - {gap}")

    return "\n".join(lines)


def cmd_coverage(project_root: str = '.') -> str:
    """Rapport de couverture des skills."""
    eco = analyze_ecosystem(project_root)

    lines = [
        "📊 COUVERTURE DES SKILLS",
        "",
        f"{'Skill':<25} {'Équivalences':>15} {'Domaine':>15}",
        "-" * 58,
    ]

    coverage = {
        'langage-ondulatoire': (eco.total_equivalences, 'Universel'),
        'wave-bridge': (len(eco.adapters), 'TTS+LLM+Protéines'),
        'wave-code-generator': (10, 'LLM (intentions)'),
        'wave-ir-compiler': (eco.total_equivalences, 'Universel'),
        'harmonic-hardware': (7, 'HPU'),
        'wave-orchestrator': (eco.total_equivalences, 'Orchestration'),
        'wave-validator': (eco.total_equivalences, 'Conformité'),
    }

    for skill, (count, domain) in coverage.items():
        lines.append(f"{skill:<25} {count:>15} {domain:>15}")

    return "\n".join(lines)


def cmd_verify(project_root: str = '.') -> Tuple[str, int]:
    """
    Lance le wave-validator (Axe 2) et retourne (sortie, exit_code).

    Le validator couvre 3 niveaux :
      1. Primitives wave_lang (13 tests)
      2. Adaptateurs wave_bridge (19 contrats)
      3. Équivalences (tables LLM + TTS)
    + détection de dérive root vs vital-ka.

    Returns:
        (texte du rapport, exit code 0/1)
    """
    validator_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'wave-validator', 'validator.py'
    )
    validator_path = os.path.abspath(validator_path)

    if not os.path.exists(validator_path):
        return ("⚠️  wave-validator introuvable : "
                f"{validator_path}"), 1

    import subprocess
    try:
        proc = subprocess.run(
            [sys.executable, validator_path, '--root', project_root],
            capture_output=True, text=True, timeout=300
        )
        output = proc.stdout + proc.stderr
        return output, proc.returncode
    except Exception as e:
        return f"⚠️  Erreur validator: {e}", 1


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN (avec exit codes pour CI)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Wave Orchestrator — Chef d\'orchestre de l\'écosystème ondulatoire'
    )
    parser.add_argument(
        'command',
        nargs='?',
        default='status',
        choices=['status', 'gaps', 'coverage', 'sync', 'verify'],
        help='Commande à exécuter (défaut: status)'
    )
    parser.add_argument(
        '--root',
        default='.',
        help='Racine du projet (défaut: .)'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Mode CI : exit code 1 si des gaps existent (sortie concise)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Affiche le rapport complet même en mode --check'
    )

    args = parser.parse_args()

    # ── verify : lance le wave-validator ──
    if args.command == 'verify':
        output, exit_code = cmd_verify(args.root)
        print(output)
        sys.exit(exit_code)

    # ── Autres commandes ──
    commands = {
        'status': cmd_status,
        'gaps': cmd_gaps,
        'coverage': cmd_coverage,
        'sync': cmd_status,  # sync est un alias de status pour l'instant
    }

    result = commands[args.command](args.root)

    # ── Mode CI : exit code selon les gaps ──
    if args.command in ('status', 'sync'):
        eco = analyze_ecosystem(args.root)
        has_gaps = len(eco.gaps) > 0

        if args.check:
            if has_gaps:
                if not args.verbose:
                    # Sortie concise pour CI
                    print(f"❌ {len(eco.gaps)} gap(s) détecté(s) — release BLOQUÉE")
                    for gap in eco.gaps[:10]:
                        print(f"   - {gap}")
                    if len(eco.gaps) > 10:
                        print(f"   ... et {len(eco.gaps) - 10} autres")
                else:
                    print(result)
                sys.exit(1)
            else:
                if not args.verbose:
                    print(f"✅ Écosystème cohérent — {eco.total_existing}/{eco.total_equivalences} équivalences")
                else:
                    print(result)
                sys.exit(0)
        else:
            print(result)
            sys.exit(1 if has_gaps else 0)
    else:
        print(result)
