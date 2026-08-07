"""
Obsidian Connector — Pont entre Vaults Obsidian et IA Harmonique
=================================================================
Inspiré du pattern Karpathy (Ingest / Query / Lint) et de l'écosystème Obsidian.

Fonctionnalités :
  1. Import : vault Obsidian (.md) → triplets → Hologramme
  2. Export : Hologramme → vault Obsidian (notes + backlinks)
  3. Lint  : Gap Detection sur le vault → notes de suggestion
  4. Sync  : Maintien bidirectionnel vault ↔ KB

Usage :
  conn = ObsidianConnector(brain)
  conn.import_vault("~/Documents/Obsidian/")
  conn.export_to_vault("~/Documents/HarmonicVault/")
  conn.lint_vault("~/Documents/Obsidian/")
"""

import os, re, sys, json, time, logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import numpy as np

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(message)s')

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

# ── Imports lazy ──────────────────────────────────────────────────────────
_HarmonicBrain = None
_BOOTSTRAPPER = None
_QualityFilter = None


def _ensure_imports():
    global _HarmonicBrain, _BOOTSTRAPPER, _QualityFilter
    if _HarmonicBrain is None:
        from harmonic_brain import HarmonicBrain as HB
        _HarmonicBrain = HB
    if _BOOTSTRAPPER is None:
        try:
            from bootstrapper import extract_triples_enhanced
            _BOOTSTRAPPER = extract_triples_enhanced
        except ImportError:
            from bootstrapper import extract_triples_simple
            _BOOTSTRAPPER = extract_triples_simple
    if _QualityFilter is None:
        try:
            from domain_specializer import QualityFilter
            _QualityFilter = QualityFilter
        except ImportError:
            _QualityFilter = None


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ObsidianNote:
    """Représente une note Obsidian."""
    path: str
    title: str
    content: str
    backlinks: List[str] = field(default_factory=list)  # [[liens]]
    tags: List[str] = field(default_factory=list)        # #tags
    frontmatter: Dict = field(default_factory=dict)      # YAML frontmatter
    extracted_facts: List[Tuple] = field(default_factory=list)
    linked_notes: List[str] = field(default_factory=list)

@dataclass
class VaultStats:
    """Statistiques d'un vault."""
    path: str
    total_notes: int
    total_links: int
    total_tags: int
    facts_extracted: int
    orphan_notes: List[str]  # notes sans backlinks
    broken_links: List[Tuple[str, str]]  # (source, cible)
    top_tags: List[Tuple[str, int]]


# ═══════════════════════════════════════════════════════════════════════════════
# OBSIDIAN CONNECTOR
# ═══════════════════════════════════════════════════════════════════════════════

class ObsidianConnector:
    """
    Pont entre vaults Obsidian et le cerveau harmonique.
    
    Pattern Karpathy :
      Ingest : vault → triplets → hologramme
      Query  : question → retrieval → réponse + citations
      Lint   : détection de gaps/contradictions → notes de suggestion
    """
    
    def __init__(self, brain=None):
        _ensure_imports()
        self.brain = brain
        self._notes: Dict[str, ObsidianNote] = {}
        self._backlink_graph: Dict[str, Set[str]] = defaultdict(set)
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)
    
    # ═════════════════════════════════════════════════════════════════════════
    # IMPORT : VAULT → KB
    # ═════════════════════════════════════════════════════════════════════════
    
    def import_vault(self, vault_path: str, recursive: bool = True) -> VaultStats:
        """
        Importe un vault Obsidian dans la base de connaissances.
        
        Pour chaque note .md :
          1. Parse le markdown (frontmatter, liens, tags)
          2. Extrait les triplets via le bootstrapper
          3. Ingère dans le cerveau harmonique
          4. Construit le graphe de backlinks
        
        Args:
            vault_path: Chemin du dossier vault
            recursive: Parcourir les sous-dossiers
        
        Returns:
            VaultStats
        """
        vault_path = Path(vault_path).expanduser().resolve()
        if not vault_path.exists():
            raise FileNotFoundError(f"Vault introuvable: {vault_path}")
        
        log.info(f"📁 Import vault: {vault_path}")
        
        self._notes = {}
        self._backlink_graph = defaultdict(set)
        self._tag_index = defaultdict(set)
        
        total_facts = 0
        total_links = 0
        total_tags = 0
        
        # Découvrir tous les fichiers .md
        md_files = list(vault_path.glob('**/*.md' if recursive else '*.md'))
        # Exclure les dossiers cachés et templates
        md_files = [f for f in md_files if '.obsidian' not in str(f) and '.trash' not in str(f)]
        
        log.info(f"  → {len(md_files)} notes trouvées")
        
        for md_file in md_files:
            try:
                note = self._parse_note(md_file, vault_path)
                self._notes[note.title] = note
                
                # Indexer les backlinks
                for link in note.backlinks:
                    self._backlink_graph[note.title].add(link)
                    total_links += 1
                
                # Indexer les tags
                for tag in note.tags:
                    self._tag_index[tag].add(note.title)
                    total_tags += 1
                
                # Extraire les faits
                facts = self._extract_facts_from_note(note)
                note.extracted_facts = facts
                total_facts += len(facts)
                
                # Ingérer dans le cerveau
                if self.brain is not None:
                    for s, r, o, sec in facts:
                        self.brain.unconscious.ingest(s, r, o, sec)
                        self.brain._route_ingest(s, r, o, sec)
                
            except Exception as e:
                log.warning(f"  ⚠️ {md_file.name}: {e}")
        
        # Analyse du vault
        orphan_notes = [title for title, links in self._backlink_graph.items() 
                       if len(links) == 0 and not any(title in v for v in self._backlink_graph.values())]
        
        broken_links = []
        for title, note in self._notes.items():
            for link in note.backlinks:
                if link not in self._notes:
                    broken_links.append((title, link))
        
        top_tags = self._tag_index.most_common(20) if hasattr(self._tag_index, 'most_common') else \
                   sorted(self._tag_index.items(), key=lambda x: -len(x[1]))[:20]
        
        stats = VaultStats(
            path=str(vault_path),
            total_notes=len(self._notes),
            total_links=total_links,
            total_tags=total_tags,
            facts_extracted=total_facts,
            orphan_notes=orphan_notes,
            broken_links=broken_links,
            top_tags=[(tag, len(notes)) for tag, notes in top_tags],
        )
        
        log.info(f"  ✅ Importé: {stats.total_notes} notes, {stats.facts_extracted} faits, "
                 f"{stats.total_links} liens, {len(stats.orphan_notes)} orphelines")
        
        return stats
    
    def _parse_note(self, md_file: Path, vault_root: Path) -> ObsidianNote:
        """Parse une note Obsidian (markdown + frontmatter + wikilinks + tags)."""
        with open(md_file, 'r', encoding='utf-8', errors='replace') as f:
            raw = f.read()
        
        # Extraire le titre (nom du fichier sans extension)
        title = md_file.stem
        
        # Parser le frontmatter YAML
        frontmatter = {}
        content = raw
        if raw.startswith('---'):
            parts = raw.split('---', 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    frontmatter = yaml.safe_load(parts[1]) or {}
                except Exception:
                    # YAML simple: clé: valeur
                    for line in parts[1].strip().split('\n'):
                        if ':' in line:
                            k, v = line.split(':', 1)
                            frontmatter[k.strip()] = v.strip()
                content = parts[2]
        
        # Extraire les [[backlinks]]
        backlinks = re.findall(r'\[\[([^\]|#]+)(?:[|#][^\]]+)?\]\]', content)
        backlinks = [b.strip() for b in backlinks if b.strip()]
        
        # Extraire les #tags
        tags = re.findall(r'#([a-zA-Z0-9_\-/]+)', content)
        # Ajouter les tags du frontmatter
        if 'tags' in frontmatter:
            ft_tags = frontmatter['tags']
            if isinstance(ft_tags, list):
                tags.extend(ft_tags)
            elif isinstance(ft_tags, str):
                tags.extend([t.strip() for t in ft_tags.split(',')])
        
        # Nettoyer le contenu pour l'extraction (enlever les wikilinks, garder le texte)
        content_clean = re.sub(r'\[\[([^\]]+)\]\]', r'\1', content)  # [[lien]] → lien
        content_clean = re.sub(r'#([a-zA-Z0-9_\-/]+)', r'\1', content_clean)  # #tag → tag
        
        return ObsidianNote(
            path=str(md_file.relative_to(vault_root)),
            title=title,
            content=content_clean,
            backlinks=list(set(backlinks)),
            tags=list(set(tags)),
            frontmatter=frontmatter,
        )
    
    def _extract_facts_from_note(self, note: ObsidianNote) -> List[Tuple[str, str, str, str]]:
        """Extrait les triplets d'une note en utilisant le contexte des backlinks."""
        facts = []
        seen = set()
        
        # 1. Extraire avec le bootstrapper
        if _BOOTSTRAPPER:
            raw_facts = _BOOTSTRAPPER(note.content)
        else:
            raw_facts = []
        
        # 2. Enrichir avec les backlinks (créer des relations entre notes liées)
        for link in note.backlinks:
            if link not in seen:
                seen.add(link)
                facts.append((note.title.lower(), "est lié à", link.lower(), "OBSIDIAN_LINK"))
        
        # 3. Ajouter les faits extraits du contenu
        for s, r, o, sec in raw_facts:
            key = (s.lower().strip(), r.lower().strip(), o.lower().strip())
            if key not in seen:
                seen.add(key)
                # Si la note a des tags, les utiliser comme secteur
                if note.tags and sec == 'GENERAL':
                    sec = note.tags[0].upper().replace('/', '_')
                facts.append((s, r, o, sec))
        
        # 4. Créer des faits à partir du frontmatter (metadata = faits)
        for k, v in note.frontmatter.items():
            if k not in ('tags', 'title', 'date', 'created', 'modified'):
                key = (note.title.lower(), k.lower().replace('_', ' '), str(v).lower())
                if key not in seen:
                    seen.add(key)
                    facts.append((note.title.lower(), k.lower().replace('_', ' '), str(v).lower(), "OBSIDIAN_META"))
        
        return facts
    
    # ═════════════════════════════════════════════════════════════════════════
    # EXPORT : KB → VAULT
    # ═════════════════════════════════════════════════════════════════════════
    
    def export_to_vault(self, output_path: str, max_notes_per_domain: int = 50):
        """
        Exporte la base de connaissances harmonique en vault Obsidian.
        
        Structure générée :
          vault/
            🌳_Arbre_de_Connaissance.md    (index)
            sciences/
              physique.md
              chimie.md
              ...
            culture_generale/
              geographie.md
              ...
            _backlinks/                    (notes de connexion)
        
        Chaque note contient :
          - La liste des faits du domaine
          - Des [[backlinks]] vers les concepts liés
          - Des #tags pour la navigation
        """
        output_path = Path(output_path).expanduser().resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        
        if self.brain is None:
            log.error("Aucun cerveau harmonique connecté")
            return
        
        log.info(f"📁 Export vault: {output_path}")
        
        index_lines = ["# 🌳 Arbre de Connaissance", "", 
                       "Export automatique depuis l'IA Harmonique.", ""]
        
        total_exported = 0
        
        for domain_name, domain_store in self.brain._domain_stores.items():
            store = domain_store.store
            if not store.registry:
                continue
            
            # Créer le dossier du domaine
            domain_dir = output_path / domain_name
            domain_dir.mkdir(exist_ok=True)
            
            # Regrouper les faits par concept (sujet)
            facts_by_subject = defaultdict(list)
            for (s, r, o), record in store.registry.items():
                facts_by_subject[s].append((r, o, record.amplitude))
            
            # Top sujets (les plus de faits)
            top_subjects = sorted(facts_by_subject.items(), 
                                 key=lambda x: -len(x[1]))[:max_notes_per_domain]
            
            domain_notes = []
            
            for subject, fact_list in top_subjects:
                note_lines = [
                    f"---",
                    f"title: {subject.title()}",
                    f"domain: {domain_name}",
                    f"facts_count: {len(fact_list)}",
                    f"tags: [{domain_name}, {domain_store.sectors[0] if domain_store.sectors else 'general'}]",
                    f"---",
                    f"",
                    f"# {subject.title()}",
                    f"",
                    f"## Faits",
                    f"",
                ]
                
                # Ajouter les faits
                for r, o, amp in fact_list[:20]:
                    note_lines.append(f"- **{r}** → {o}  (amp: {amp:.1f})")
                
                # Ajouter les backlinks vers les concepts liés
                linked_concepts = set()
                for r, o, _ in fact_list:
                    # Trouver d'autres sujets qui partagent cet objet
                    for (s2, r2, o2), rec2 in store.registry.items():
                        if s2 != subject and (o.lower() in o2.lower() or o2.lower() in o.lower()):
                            linked_concepts.add(s2)
                
                if linked_concepts:
                    note_lines.append("")
                    note_lines.append("## Concepts liés")
                    note_lines.append("")
                    for lc in list(linked_concepts)[:10]:
                        note_lines.append(f"- [[{lc}]]")
                
                note_lines.append("")
                
                # Écrire la note
                note_path = domain_dir / f"{subject[:50].replace('/','_')}.md"
                note_path.write_text('\n'.join(note_lines), encoding='utf-8')
                
                domain_notes.append(subject)
                total_exported += 1
            
            # Ajouter à l'index
            index_lines.append(f"## {domain_store.domain}")
            index_lines.append("")
            for dn in domain_notes[:10]:
                index_lines.append(f"- [[{domain_name}/{dn}]]")
            index_lines.append("")
        
        # Écrire l'index
        index_path = output_path / "🌳_Arbre_de_Connaissance.md"
        index_path.write_text('\n'.join(index_lines), encoding='utf-8')
        
        log.info(f"  ✅ Exporté: {total_exported} notes dans {output_path}")
    
    # ═════════════════════════════════════════════════════════════════════════
    # LINT : AUDIT DU VAULT
    # ═════════════════════════════════════════════════════════════════════════
    
    def lint_vault(self, vault_path: str) -> Dict:
        """
        Audite un vault Obsidian (pattern Karpathy "Lint").
        
        Détecte :
          - Notes orphelines (sans backlinks)
          - Liens brisés
          - Tags sous-utilisés
          - Contenu dupliqué
          - Gaps de connaissance (connexions manquantes)
        
        Returns:
            Rapport d'audit
        """
        if not self._notes:
            stats = self.import_vault(vault_path)
        
        report = {
            'orphan_notes': [],
            'broken_links': [],
            'duplicate_content': [],
            'gap_suggestions': [],
            'stats': {},
        }
        
        # Notes orphelines
        all_linked = set()
        for note in self._notes.values():
            all_linked.update(note.backlinks)
        
        for title, note in self._notes.items():
            if title not in all_linked and len(note.backlinks) == 0:
                report['orphan_notes'].append(title)
        
        # Liens brisés
        for title, note in self._notes.items():
            for link in note.backlinks:
                if link not in self._notes:
                    report['broken_links'].append((title, link))
        
        # Contenu dupliqué (titres similaires)
        titles_lower = [(t.lower(), t) for t in self._notes.keys()]
        for i, (tl1, t1) in enumerate(titles_lower):
            for tl2, t2 in titles_lower[i+1:]:
                if tl1 != tl2 and (tl1 in tl2 or tl2 in tl1 or 
                    len(set(tl1.split()) & set(tl2.split())) > len(tl1.split()) * 0.7):
                    report['duplicate_content'].append((t1, t2))
        
        # Gap suggestions (concepts fréquents mais non liés)
        if self.brain is not None:
            from spectral_embedding import KnowledgeGapAnalyzer
            all_facts = []
            for note in self._notes.values():
                all_facts.extend(note.extracted_facts)
            if len(all_facts) > 100:
                analyzer = KnowledgeGapAnalyzer(max_nodes=1000)
                analyzer.build_from_facts(all_facts[:30000])
                for gap in analyzer.gaps[:5]:
                    report['gap_suggestions'].append({
                        'concept_a': gap['cluster_a'],
                        'concept_b': gap['cluster_b'],
                        'score': gap['score'],
                        'suggestion': f"Créer une note reliant {gap['cluster_a']} et {gap['cluster_b']}"
                    })
        
        report['stats'] = {
            'total_notes': len(self._notes),
            'orphan_notes': len(report['orphan_notes']),
            'broken_links': len(report['broken_links']),
            'duplicates': len(report['duplicate_content']),
            'gap_suggestions': len(report['gap_suggestions']),
        }
        
        return report
    
    def lint_report_markdown(self, report: Dict) -> str:
        """Génère un rapport d'audit en markdown (prêt pour Obsidian)."""
        lines = [
            "# 🔍 Rapport d'Audit — Vault Obsidian",
            "",
            f"**{report['stats']['total_notes']}** notes analysées.",
            "",
        ]
        
        if report['orphan_notes']:
            lines.append("## 📄 Notes orphelines")
            for n in report['orphan_notes'][:20]:
                lines.append(f"- [[{n}]]")
            lines.append("")
        
        if report['broken_links']:
            lines.append("## 🔗 Liens brisés")
            for src, tgt in report['broken_links'][:20]:
                lines.append(f"- [[{src}]] → ❌ [[{tgt}]] (cible inexistante)")
            lines.append("")
        
        if report['duplicate_content']:
            lines.append("## 📋 Contenu potentiellement dupliqué")
            for t1, t2 in report['duplicate_content'][:10]:
                lines.append(f"- [[{t1}]] ↔ [[{t2}]]")
            lines.append("")
        
        if report['gap_suggestions']:
            lines.append("## 🕳️ Connexions suggérées (Gaps)")
            for g in report['gap_suggestions']:
                lines.append(f"- **{g['concept_a']}** ↔ **{g['concept_b']}** (score: {g['score']:.2f})")
                lines.append(f"  → {g['suggestion']}")
            lines.append("")
        
        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN (test)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import tempfile
    
    print("═══ Test ObsidianConnector ═══")
    
    # Créer un vault de test
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "test_vault"
        vault.mkdir()
        
        # Créer quelques notes
        (vault / "Physique.md").write_text("""---
domaine: sciences
tags: [physique, fondamentale]
---
# Physique

La physique est la science qui étudie la [[matière]] et l'[[énergie]].

## Lois fondamentales

- La [[lumière]] est une onde électromagnétique
- La [[gravité]] attire les objets vers le centre de la [[Terre]]
- L'[[énergie]] se conserve (premier principe de la thermodynamique)

Voir aussi : [[Mathématiques]], [[Chimie]]
""", encoding='utf-8')
        
        (vault / "Chimie.md").write_text("""---
domaine: sciences
tags: [chimie, elements]
---
# Chimie

La chimie étudie la composition de la [[matière]].

- L'[[eau]] a pour formule H2O
- L'[[hydrogène]] est l'élément le plus abondant dans l'[[univers]]
- Le [[carbone]] est la base de la chimie organique

Voir aussi : [[Physique]], [[Biologie]]
""", encoding='utf-8')
        
        (vault / "Histoire.md").write_text("""---
domaine: histoire
tags: [histoire, dates]
---
# Histoire

- La [[Révolution française]] a eu lieu en 1789
- La [[Première Guerre mondiale]] a commencé en 1914
- Le [[mur de Berlin]] est tombé en 1989
""", encoding='utf-8')
        
        # Test import
        conn = ObsidianConnector()
        stats = conn.import_vault(str(vault))
        
        print(f"\n📊 Stats du vault:")
        print(f"  Notes: {stats.total_notes}")
        print(f"  Liens: {stats.total_links}")
        print(f"  Tags: {stats.total_tags}")
        print(f"  Faits extraits: {stats.facts_extracted}")
        print(f"  Notes orphelines: {stats.orphan_notes}")
        print(f"  Top tags: {stats.top_tags[:5]}")
        
        # Test lint
        report = conn.lint_vault(str(vault))
        print(f"\n🔍 Lint: {report['stats']}")
        
        # Afficher quelques faits extraits
        print(f"\n📝 Faits extraits (échantillon):")
        for note in conn._notes.values():
            for s, r, o, sec in note.extracted_facts[:3]:
                print(f"  [{sec}] {s} | {r} | {o}")
        
        print(f"\n✅ ObsidianConnector OK")
