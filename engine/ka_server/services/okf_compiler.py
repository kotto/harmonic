"""
🌊 okf_compiler.py — Compilateur OKF : Markdown → Hologramme
=================================================================
Compile le wiki de connaissances (knowledge/**/*.md) en hologrammes
wave-native ℂ⁵¹², un par domaine.

Fonctionnalités :
  - Compile les .md → hologrammes (--compile, défaut)
  - Génère index.md (catalogue des concepts)
  - Génère log.md (chronologie append-only)
  - Détecte doublons et conflits (--validate)
  - Accumulation : --file crée un .md + recompile

Usage :
  python ka_server/services/okf_compiler.py               # compile tout
  python ka_server/services/okf_compiler.py --validate    # valide seulement
  python ka_server/services/okf_compiler.py --list        # lister concepts
  python ka_server/services/okf_compiler.py --file d=phys id=laser t=... f=...  # créer + compiler
"""

import logging
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ENGINE_DIR))
sys.path.insert(0, str(_ENGINE_DIR / 'vital-ka' / 'core' / 'python'))

from hologram_store import HologramStore, _circular_convolve
from holographic_encoder import HolographicEncoder

WIKI_DIR = _ENGINE_DIR / 'knowledge'
SCHEMA_PATH = WIKI_DIR / '.schema.json'
INDEX_PATH = WIKI_DIR / 'index.md'
LOG_PATH = WIKI_DIR / 'log.md'


# ═══════════════════════════════════════════════════════════
# PARSING
# ═══════════════════════════════════════════════════════════

_FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
_KV_RE = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.+?)\s*$')


def parse_frontmatter(text: str) -> dict:
    m = _FRONTMATTER_RE.search(text)
    if not m:
        return {}
    meta = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        kv = _KV_RE.match(line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip()
            val = val.strip('"\'')
            meta[key] = val
    return meta


def parse_facts(body: str) -> list:
    facts = []
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('>'):
            continue
        line = line.lstrip('-*•').strip()
        if '|' not in line:
            continue
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 3 and parts[0] and parts[1] and parts[2]:
            facts.append((parts[0], parts[1], parts[2]))
    return facts


def parse_file(path: Path) -> dict:
    text = path.read_text(encoding='utf-8')
    meta = parse_frontmatter(text)
    body = _FRONTMATTER_RE.sub('', text)
    facts = parse_facts(body)
    return {
        'id': meta.get('id', path.stem),
        'domain': meta.get('domain', path.parent.name),
        'title': meta.get('title', path.stem),
        'type': meta.get('type', 'concept'),
        'source': meta.get('source', ''),
        'facts': facts,
        'path': path,
    }


# ═══════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════

def validate_entry(entry: dict) -> list:
    errors = []
    if not entry['id']:       errors.append('id manquant')
    if not entry['domain']:   errors.append('domain manquant')
    if not entry['title']:    errors.append('title manquant')
    if not entry['facts']:    errors.append(f"aucun fait dans {entry['path'].name}")
    return errors


def find_duplicates(entries: list) -> list:
    seen = {}
    conflicts = []
    for e in entries:
        for s, r, o in e['facts']:
            key = (s.lower().strip(), r.lower().strip(), o.lower().strip())
            if key in seen:
                conflicts.append((key, seen[key], e['path'].name))
            else:
                seen[key] = e['path'].name
    return conflicts


# ═══════════════════════════════════════════════════════════
# INDEX & LOG
# ═══════════════════════════════════════════════════════════

def generate_index(entries: list) -> str:
    """Génère index.md : catalogue de tous les concepts, par domaine."""
    by_domain = defaultdict(list)
    for e in entries:
        by_domain[e['domain']].append(e)

    lines = []
    lines.append("# KA Knowledge Wiki — Index")
    lines.append(f"\n*Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')} — "
                 f"{len(entries)} concepts, "
                 f"{sum(len(e['facts']) for e in entries)} faits*\n")

    for domain in sorted(by_domain):
        entries_d = sorted(by_domain[domain], key=lambda x: x['id'])
        n_facts = sum(len(e['facts']) for e in entries_d)
        lines.append(f"\n## {domain} ({len(entries_d)} concepts, {n_facts} faits)\n")
        for e in entries_d:
            n = len(e['facts'])
            src = f" — [{e['source']}]({e['source']})" if e.get('source') else ''
            path_rel = e['path'].relative_to(WIKI_DIR)
            lines.append(f"- [{e['title']}]({path_rel}) — {n} fait{'s' if n>1 else ''}{src}")

    return '\n'.join(lines) + '\n'


def generate_log_entry(action: str, entries: list, report: dict = None) -> str:
    """Génère une ligne de log au format Karpathy."""
    today = datetime.now().strftime('%Y-%m-%d')
    n_concepts = len(entries)
    n_facts = sum(len(e['facts']) for e in entries)
    domains = sorted(set(e['domain'] for e in entries))
    line = f"## [{today}] {action} | {n_concepts} concepts, {n_facts} faits, {', '.join(domains)}"
    if report:
        line += f" | {report.get('errors', 0)} erreurs, {report.get('conflicts', 0)} conflits"
    return line + '\n'


def append_log(action: str, entries: list, report: dict = None):
    """Append une ligne au log.md."""
    line = generate_log_entry(action, entries, report)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception as e:
        log.warning(f"Impossible d'écrire log.md: {e}")


# ═══════════════════════════════════════════════════════════
# CRÉATION D'UN FICHIER (boucle d'accumulation)
# ═══════════════════════════════════════════════════════════

def create_file(domain: str, concept_id: str, title: str,
                facts: list, source: str = '', overwrite: bool = False) -> Path:
    """
    Crée un fichier markdown dans le wiki.
    C'est la boucle d'accumulation : une bonne réponse → fichier wiki.
    """
    domain_dir = WIKI_DIR / domain
    domain_dir.mkdir(parents=True, exist_ok=True)
    path = domain_dir / f'{concept_id}.md'

    if path.exists() and not overwrite:
        log.warning(f"{path} existe déjà. Utilisez overwrite=True pour écraser.")
        return path

    src_line = f"source: {source}\n" if source else ""
    lines = [
        "---\n",
        f"id: {concept_id}\n",
        f"domain: {domain}\n",
        f"title: {title}\n",
        f"type: concept\n",
        src_line,
        "---\n",
        f"\n# {title}\n",
    ]
    for s, r, o in facts:
        lines.append(f"\n- {s} | {r} | {o}")

    path.write_text(''.join(lines), encoding='utf-8')
    return path


# ═══════════════════════════════════════════════════════════
# COMPILATION
# ═══════════════════════════════════════════════════════════

def compile_wiki(store: HologramStore = None, write_index: bool = True,
                 write_log: bool = True, action: str = 'compile') -> dict:
    """Compile tout le wiki en hologrammes (un par domaine)."""
    store = store or HologramStore()

    md_files = sorted(WIKI_DIR.rglob('*.md'))
    md_files = [f for f in md_files if f.name not in ('README.md', 'index.md', 'log.md', '.schema.json')]
    md_files = [f for f in md_files if 'raw' not in f.parts]  # exclure les sources
    if not md_files:
        return {'error': 'Aucun fichier .md'}

    entries = [parse_file(f) for f in md_files]

    # Validation
    all_errors = []
    valid_entries = []
    for e in entries:
        errs = validate_entry(e)
        if errs:
            all_errors.extend(f"{e['path'].relative_to(WIKI_DIR)}: {', '.join(errs)}")
        else:
            valid_entries.append(e)

    conflicts = find_duplicates(valid_entries)

    # Regrouper par domaine
    by_domain = defaultdict(list)
    for e in valid_entries:
        by_domain[e['domain']].append(e)

    # Compiler chaque domaine
    from hologram_store import HologramMeta
    from collections import Counter

    results = {}
    for domain, domain_entries in sorted(by_domain.items()):
        holo_id = f'okf_{domain}'
        facts = []
        sources = []
        for e in domain_entries:
            for s, r, o in e['facts']:
                facts.append((s, r, o))
                sources.append(e['id'])

        if not facts:
            continue

        # Encoder les mots
        word_set = set()
        for s, r, o in facts:
            for w in s.split() + r.split() + o.split():
                w = w.strip('.,!?;:()[]{}«»""\'\'¿¡')
                if len(w) >= 2:
                    word_set.add(w)
        for w in word_set:
            store._encoder.encode_word(w)

        # Binding + hologramme
        psi_facts = []
        for s, r, o in facts:
            psi_s = store._encoder.encode_word(s)
            psi_r = store._encoder.encode_word(r)
            psi_o = store._encoder.encode_word(o)
            psi_fact = _circular_convolve(_circular_convolve(psi_s, psi_r), psi_o)
            psi_facts.append(psi_fact)

        hologram_memory = np.sum(psi_facts, axis=0)
        hologram_memory = hologram_memory / np.sqrt(len(psi_facts))

        # Sauvegarde NPZ
        holo_path = store.store_dir / f'{holo_id}.npz'
        np.savez_compressed(str(holo_path),
            subjects=np.array([f[0] for f in facts], dtype=object),
            relations=np.array([f[1] for f in facts], dtype=object),
            objects=np.array([f[2] for f in facts], dtype=object),
            sources=np.array(sources, dtype=object),
            psi_subjects=np.array([store._encoder.encode_word(f[0]) for f in facts], dtype=np.complex64),
            psi_relations=np.array([store._encoder.encode_word(f[1]) for f in facts], dtype=np.complex64),
            psi_objects=np.array([store._encoder.encode_word(f[2]) for f in facts], dtype=np.complex64),
            hologram_memory=hologram_memory.astype(np.complex64),
            amplitudes=np.ones(len(facts), dtype=np.float32),
            version=2, kb_hash=f'okf_{time.time():.0f}', domain=domain,
            created_at=time.time(),
        )

        size_kb = holo_path.stat().st_size / 1024
        meta = HologramMeta(
            id=holo_id, name=f'OKF — {domain}', domain=domain,
            icon='📖', description=f'Wiki OKF compilé — domaine {domain}',
            facts_count=len(facts), sectors=[e['id'] for e in domain_entries],
            author='KA', type='official', created_at=time.time(),
            top_concepts=[e['id'] for e in domain_entries[:8]],
            quality_score=0.0, benchmark_questions=0,
            version=2, kb_hash=f'okf_{time.time():.0f}',
        )
        meta._size_kb = size_kb
        store._registry[holo_id] = meta
        store._save_registry()

        results[domain] = {
            'holo_id': holo_id, 'facts': len(facts),
            'concepts': len(domain_entries), 'size_kb': round(size_kb, 1),
        }

    report = {
        'results': results, 'errors': all_errors, 'conflicts': conflicts,
        'total_files': len(md_files), 'valid_files': len(valid_entries),
    }

    # Générer index.md
    if write_index and valid_entries:
        try:
            index_content = generate_index(valid_entries)
            INDEX_PATH.write_text(index_content, encoding='utf-8')
        except Exception as e:
            log.warning(f"Impossible d'écrire index.md: {e}")

    # Ajouter au log.md
    if write_log:
        append_log(action, valid_entries, report)

    return report


# ═══════════════════════════════════════════════════════════
# COMMANDES UTILISATEUR
# ═══════════════════════════════════════════════════════════

def cmd_file(args: list):
    """--file d=domain id=concept_id t=title [f='s|r|o\ns|r|o'] [src=source] [overwrite]"""
    kwargs = {}
    for a in args:
        if '=' in a:
            k, v = a.split('=', 1)
            kwargs[k] = v

    domain = kwargs.get('d') or kwargs.get('domain')
    cid = kwargs.get('id') or kwargs.get('cid')
    title = kwargs.get('t') or kwargs.get('title')
    facts_raw = kwargs.get('f', '')
    source = kwargs.get('src', '')
    overwrite = kwargs.get('overwrite', '') in ('yes', 'true', '1')

    if not domain or not cid or not title or not facts_raw:
        print("Usage: --file d=domain id=concept_id t=title f='sujet|relation|objet\\nsujet|relation|objet...'")
        return

    facts = []
    for line in facts_raw.split('\\n'):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 3 and parts[0] and parts[1] and parts[2]:
            facts.append((parts[0], parts[1], parts[2]))

    if not facts:
        print("Aucun fait valide dans la chaîne fournie.")
        return

    path = create_file(domain, cid, title, facts, source, overwrite)
    print(f"📄 Fichier créé : {path.relative_to(_ENGINE_DIR)}")

    # Recompiler
    print("🔄 Recompilation...")
    report = compile_wiki(action=f'file|{cid}')
    _print_report(report)


def cmd_list():
    md_files = sorted(WIKI_DIR.rglob('*.md'))
    md_files = [f for f in md_files if f.name not in ('README.md', 'index.md', 'log.md')]
    print(f"{len(md_files)} concepts dans le wiki :\n")
    for f in md_files:
        e = parse_file(f)
        print(f"  [{e['domain']:12s}] {e['id']:24s} {len(e['facts']):>3d} faits — {e['title']}")


def cmd_validate():
    md_files = sorted(WIKI_DIR.rglob('*.md'))
    md_files = [f for f in md_files if f.name not in ('README.md', 'index.md', 'log.md')]
    md_files = [f for f in md_files if 'raw' not in f.parts]
    entries = [parse_file(f) for f in md_files]
    all_errors = []
    valid = []
    for e in entries:
        errs = validate_entry(e)
        if errs:
            all_errors.extend(f"{e['path'].relative_to(WIKI_DIR)}: {', '.join(errs)}")
        else:
            valid.append(e)
    conflicts = find_duplicates(valid)
    print(f"Validation : {len(valid)}/{len(entries)} fichiers valides")
    if all_errors:
        print("\n❌ Erreurs :")
        for err in all_errors:
            print(f"  {err}")
    if conflicts:
        print("\n⚠️  Conflits :")
        for key, f1, f2 in conflicts:
            print(f"  {key[0]} | {key[1]} | {key[2]}  →  {f1} vs {f2}")
    if not all_errors and not conflicts:
        print("✅ Aucun conflit, tout est valide.")


def cmd_help():
    print("""📖 Compilateur OKF — Markdown → Hologramme

Commandes :
  (aucune)              Compiler tout le wiki → hologrammes
  --list                Lister les concepts
  --validate            Valider les fichiers sans compiler
  --lint                Analyse santé du wiki
  --search "requête"    Recherche texte BM25
  --check-sources       Vérifier la traçabilité raw/ → wiki
  --file d=...          Créer un concept + recompiler
  --ingest --url/--text Ingestion LLM (Oracle Cloud)
  --ingest --file/--interactive
""")


def _print_report(report: dict):
    print(f"  {report['valid_files']}/{report['total_files']} fichiers valides")
    if report['errors']:
        for err in report['errors']:
            print(f"  ❌ {err}")
    if report['conflicts']:
        for key, f1, f2 in report['conflicts']:
            print(f"  ⚠️  {key[0]} | {key[1]} | {key[2]}  →  {f1} vs {f2}")
    print()
    for domain, r in sorted(report['results'].items()):
        print(f"  📖 {r['holo_id']:20s} {r['facts']:>4d} faits ({r['concepts']:>2d} concepts, {r['size_kb']} KB)")
    total = sum(r['facts'] for r in report['results'].values())
    print(f"\n  TOTAL : {total} faits dans {len(report['results'])} hologrammes")


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

def main():
    logging.basicConfig(level=logging.WARNING, format='%(message)s')

    if '--list' in sys.argv:
        cmd_list()
        return
    if '--validate' in sys.argv:
        cmd_validate()
        return
    if '--help' in sys.argv or '-h' in sys.argv:
        cmd_help()
        return
    if '--file' in sys.argv:
        idx = sys.argv.index('--file')
        cmd_file(sys.argv[idx + 1:])
        return
    if '--lint' in sys.argv:
        try:
            from ka_server.services.wiki_lint import lint_wiki, print_report
            report = lint_wiki()
            print_report(report)
        except ImportError as e:
            print(f"Lint non disponible: {e}")
        return
    if '--ingest' in sys.argv:
        # Déléguer à okf_ingest.py avec les mêmes arguments
        from ka_server.services.okf_ingest import main as ingest_main
        sys.argv = [sys.argv[0]] + sys.argv[sys.argv.index('--ingest')+1:]
        ingest_main()
        return
    if '--search' in sys.argv:
        try:
            from ka_server.services.wiki_search import WikiSearch
            ws = WikiSearch()
            if not ws.load():
                ws.index()
                ws.save()
            idx = sys.argv.index('--search')
            query = ' '.join(sys.argv[idx + 1:])
            t0 = time.time()
            results = ws.search(query, top_k=8)
            dt = (time.time() - t0) * 1000
            print(f"🔍 Recherche: « {query} » ({dt:.0f} ms)\n")
            if results:
                for doc_id, score, info in results:
                    print(f"  [{score:.3f}] [{info['domain']}] {info['title']}")
                    print(f"          {info['path']}")
            else:
                print("  Aucun résultat.")
        except ImportError as e:
            print(f"Recherche non disponible: {e}")
        return
    if '--check-sources' in sys.argv:
        try:
            from ka_server.services.wiki_lint import lint_wiki
            report = lint_wiki()
            if report['source_issues']:
                print(f"🔗 SOURCES MANQUANTES ({len(report['source_issues'])}) :")
                for i in report['source_issues']:
                    print(f"  {i['message']}")
            else:
                print("✅ Toutes les sources référencées existent dans raw/")
            # Générer raw/index.md
            raw_dir = WIKI_DIR / 'raw'
            if raw_dir.exists():
                raw_files = sorted(raw_dir.glob('*.md'))
                raw_files = [f for f in raw_files if f.name != 'README.md']
                lines = ["# Sources brutes — Index\n"]
                for f in raw_files:
                    text = f.read_text(encoding='utf-8')
                    title = f.stem
                    m = re.search(r'^title:\s*(.+?)$', text, re.MULTILINE)
                    if m:
                        title = m.group(1).strip().strip('"\'')
                    lines.append(f"- [{title}]({f.name})")
                (raw_dir / 'index.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
                print(f"  📋 raw/index.md mis à jour ({len(raw_files)} sources)")
        except ImportError as e:
            print(f"Check sources non disponible: {e}")
        return

    # Compilation
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║   📖 COMPILATEUR OKF — Markdown → Hologramme                  ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    t0 = time.time()
    report = compile_wiki()
    elapsed = time.time() - t0

    print(f"\n[1] Compilation : {report['valid_files']}/{report['total_files']} fichiers valides en {elapsed:.1f}s")
    _print_report(report)

    print(f"\n  📋 index.md : {INDEX_PATH.relative_to(_ENGINE_DIR)}")
    print(f"  📋 log.md   : {LOG_PATH.relative_to(_ENGINE_DIR)}")
    print("\n✅ Compilation terminée.")


if __name__ == '__main__':
    main()