"""
Hologram Store — Magasin de Connaissances Harmoniques
=======================================================
Registre central d'hologrammes spécialisés téléchargeables.

TROIS TYPES D'HOLOGRAMMES :
  1. OFFICIELS — pré-construits par l'équipe KA (médecine, sciences, etc.)
  2. COMMUNAUTAIRES — publiés par les utilisateurs
  3. PRIVÉS — créés localement, jamais partagés

FORMAT : fichiers .npz (subjects, relations, objects, sectors, amplitudes)

Usage :
    from hologram_store import HologramStore
    
    store = HologramStore()
    
    # Lister les hologrammes disponibles
    holo_list = store.list_holograms()
    
    # Télécharger un hologramme
    facts = store.download('medicine')
    
    # Publier un hologramme communautaire
    store.publish('my_specialty', facts, author='user_123')
"""

import os, sys, json, time, logging, shutil
from pathlib import Path
from collections import Counter
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field

import numpy as np

log = logging.getLogger(__name__)

_ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

STORE_DIR = _ENGINE_DIR / "data" / "hologram_store"
STORE_DIR.mkdir(parents=True, exist_ok=True)

# Domaines officiels pré-définis avec filtres sectoriels
OFFICIAL_DOMAINS = {
    'medecine': {
        'name': 'Médecine & Santé',
        'icon': '🏥',
        'sectors': ['SANTE', 'CORPS_ORGANES', 'CORPS_SANTE', 'BIOLOGIE'],
        'keywords': ['maladie', 'symptôme', 'traitement', 'vaccin', 'médicament',
                     'patient', 'diagnostic', 'cancer', 'diabète', 'infection',
                     'virus', 'bactérie', 'cellule', 'gène', 'système', 'organe'],
        'description': 'Maladies, traitements, anatomie, diagnostics',
    },
    'sciences': {
        'name': 'Sciences Fondamentales',
        'icon': '🔬',
        'sectors': ['PHYSIQUE_FOND', 'PHYSIQUE_APPLI', 'SCIENCES', 'MATHS_PURES', 'MATHS_APPLI'],
        'keywords': ['physique', 'chimie', 'atome', 'énergie', 'force', 'lumière',
                     'onde', 'quantique', 'relativité', 'gravité', 'électron',
                     'molécule', 'équation', 'théorème', 'nombre'],
        'description': 'Physique, chimie, mathématiques',
    },
    'geographie': {
        'name': 'Géographie & Pays',
        'icon': '🌍',
        'sectors': ['GEOGRAPHIE', 'GEO'],
        'keywords': ['pays', 'capitale', 'ville', 'continent', 'population',
                     'fleuve', 'montagne', 'frontière', 'région', 'coordonnées'],
        'description': 'Pays, capitales, populations, géographie',
    },
    'histoire': {
        'name': 'Histoire & Civilisations',
        'icon': '📜',
        'sectors': ['HISTOIRE', 'HIST', 'PASSE'],
        'keywords': ['histoire', 'guerre', 'roi', 'empire', 'révolution',
                     'civilisation', 'siècle', 'traité', 'bataille', 'dynastie'],
        'description': 'Événements, personnages, civilisations',
    },
    'culture': {
        'name': 'Art & Culture',
        'icon': '🎨',
        'sectors': ['CULTURE', 'CREATION', 'EXPRESSION'],
        'keywords': ['art', 'musique', 'littérature', 'peinture', 'cinéma',
                     'théâtre', 'poésie', 'sculpture', 'danse', 'œuvre'],
        'description': 'Arts, littérature, musique, patrimoine',
    },
    'technologie': {
        'name': 'Technologie & Innovation',
        'icon': '💻',
        'sectors': ['TECHNOLOGIE', 'TECH'],
        'keywords': ['technologie', 'ordinateur', 'internet', 'code', 'logiciel',
                     'algorithme', 'robot', 'innovation', 'numérique', 'donnée'],
        'description': 'Informatique, ingénierie, innovation',
    },
    'nature': {
        'name': 'Nature & Environnement',
        'icon': '🌿',
        'sectors': ['ECOLOGIE', 'BIOLOGIE', 'NATURE_ANIM', 'NATURE_VEGET'],
        'keywords': ['écosystème', 'climat', 'environnement', 'plante', 'animal',
                     'forêt', 'océan', 'biodiversité', 'conservation', 'espèce'],
        'description': 'Écologie, faune, flore, environnement',
    },
    'economie': {
        'name': 'Économie & Finance',
        'icon': '💰',
        'sectors': ['ECONOMIE'],
        'keywords': ['économie', 'marché', 'finance', 'entreprise', 'commerce',
                     'banque', 'monnaie', 'PIB', 'investissement', 'emploi'],
        'description': 'Économie, finance, commerce',
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# HOLOGRAM METADATA
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class HologramMeta:
    id: str                    # identifiant unique
    name: str                  # nom affiché
    domain: str                # domaine
    icon: str                  # emoji
    description: str           # description
    facts_count: int           # nombre de faits
    sectors: List[str]         # secteurs couverts
    author: str                # 'KA' pour officiel, user_id pour communautaire
    type: str                  # 'official' | 'community' | 'private'
    created_at: float          # timestamp
    downloads: int = 0         # nombre de téléchargements
    quality_score: float = 1.0 # score de qualité (0-1)
    top_concepts: List[str] = field(default_factory=list)
    benchmark_questions: int = 0  # 🆕 nombre de questions benchmark (0 = pas mesuré)
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'domain': self.domain,
            'icon': self.icon,
            'description': self.description,
            'facts_count': self.facts_count,
            'sectors': self.sectors,
            'author': self.author,
            'type': self.type,
            'created_at': self.created_at,
            'downloads': self.downloads,
            'quality_score': self.quality_score,
            'top_concepts': self.top_concepts[:10],
            'size_kb': round(self._size_kb, 1) if hasattr(self, '_size_kb') else 0,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# HOLOGRAM STORE
# ═══════════════════════════════════════════════════════════════════════════════

class HologramStore:
    """
    Magasin d'hologrammes spécialisés.
    
    Gère :
      - Pré-construction des hologrammes officiels depuis le KB 110K
      - Liste, téléchargement, publication
      - Compteur de popularité
    """
    
    def __init__(self, store_dir: str = None):
        self.store_dir = Path(store_dir) if store_dir else STORE_DIR
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.store_dir / 'registry.json'
        self._registry: Dict[str, HologramMeta] = {}
        self._load_registry()
    
    # ═══ REGISTRE ═══
    
    def _load_registry(self):
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for hid, meta in data.items():
                    self._registry[hid] = HologramMeta(**meta)
            except Exception:
                pass
    
    def _save_registry(self):
        data = {}
        for hid, meta in self._registry.items():
            data[hid] = meta.__dict__.copy()
            if '_size_kb' in data[hid]:
                del data[hid]['_size_kb']
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # ═══ PRÉ-CONSTRUCTION DES HOLOGRAMMES OFFICIELS ═══
    
    def build_official_holograms(self, source_shards: List[str] = None):
        """
        Pré-construit les hologrammes officiels en filtrant le KB existant.
        
        Args:
            source_shards: liste de chemins .npz. Si None, utilise kb_enriched.
        """
        if source_shards is None:
            shard_path = _ENGINE_DIR / 'data' / 'kb_enriched' / 'shard_0000.npz'
            kb_final = _ENGINE_DIR / 'data' / 'bootstrapper_output' / 'kb_final.npz'
            source_shards = []
            if shard_path.exists():
                source_shards.append(str(shard_path))
            if kb_final.exists():
                source_shards.append(str(kb_final))
        
        # Charger tous les faits sources
        all_facts = []
        for shard_path in source_shards:
            try:
                data = np.load(shard_path, allow_pickle=True)
                if 'subjects' in data:
                    for i in range(len(data['subjects'])):
                        all_facts.append((
                            str(data['subjects'][i]),
                            str(data['relations'][i]),
                            str(data['objects'][i]),
                            str(data['sectors'][i]) if 'sectors' in data else 'GENERAL',
                        ))
                elif 'facts' in data:
                    for f in data['facts']:
                        all_facts.append((str(f[0]), str(f[1]), str(f[2]),
                                         str(f[3]) if len(f) > 3 else 'GENERAL'))
            except Exception as e:
                log.warning(f"Erreur chargement {shard_path}: {e}")
        
        log.info(f"KB source: {len(all_facts):,} faits")
        
        # Construire un hologramme par domaine officiel
        for domain_id, domain_info in OFFICIAL_DOMAINS.items():
            self._build_one_hologram(domain_id, domain_info, all_facts)
    
    def _build_one_hologram(self, domain_id: str, domain_info: dict,
                            all_facts: List[Tuple]):
        """
        Construit un hologramme pour un domaine spécifique.
        """
        sectors = set(domain_info['sectors'])
        keywords = set(kw.lower() for kw in domain_info['keywords'])
        
        filtered = []
        seen = set()
        
        for s, r, o, sec in all_facts:
            sec_upper = str(sec).upper()
            text = f"{s} {r} {o}".lower()
            
            # Critère 1 : secteur correspondant
            sector_match = any(s_target in sec_upper for s_target in sectors)
            
            # Critère 2 : mot-clé du domaine dans le fait
            keyword_match = any(kw in text for kw in keywords)
            
            if sector_match or keyword_match:
                key = (s.lower()[:60], r.lower()[:60], o.lower()[:80])
                if key not in seen:
                    seen.add(key)
                    filtered.append((s, r, o, sec))
        
        if not filtered:
            log.info(f"  ⚠️ {domain_id}: 0 faits trouvés")
            return
        
        # Sauvegarder l'hologramme
        holo_path = self.store_dir / f'official_{domain_id}.npz'
        subjects = np.array([f[0] for f in filtered], dtype=object)
        relations = np.array([f[1] for f in filtered], dtype=object)
        objects = np.array([f[2] for f in filtered], dtype=object)
        sectors_arr = np.array([f[3] for f in filtered], dtype=object)
        
        np.savez_compressed(str(holo_path),
            subjects=subjects, relations=relations,
            objects=objects, sectors=sectors_arr,
            amplitudes=np.ones(len(filtered), dtype=np.float32),
            psies_real=np.zeros((len(filtered), 64), dtype=np.float32),
            psies_imag=np.zeros((len(filtered), 64), dtype=np.float32))
        
        # Top concepts
        subj_count = Counter(str(f[0]).lower() for f in filtered)
        top_concepts = [s for s, _ in subj_count.most_common(10)]
        
        # Enregistrer dans le registre
        size_kb = holo_path.stat().st_size / 1024
        meta = HologramMeta(
            id=f'official_{domain_id}',
            name=domain_info['name'],
            domain=domain_id,
            icon=domain_info['icon'],
            description=domain_info['description'],
            facts_count=len(filtered),
            sectors=list(sectors),
            author='KA',
            type='official',
            created_at=time.time(),
            top_concepts=top_concepts,
        )
        meta._size_kb = size_kb
        self._registry[meta.id] = meta
        
        log.info(f"  ✅ {domain_info['icon']} {domain_id}: {len(filtered):,} faits ({size_kb:.0f} KB)")
    
    # ═══ LIST / DOWNLOAD / PUBLISH ═══
    
    def list_holograms(self, holo_type: str = None) -> List[dict]:
        """
        Liste les hologrammes disponibles.
        
        Args:
            holo_type: 'official', 'community', ou None (tous)
        """
        result = []
        for meta in sorted(self._registry.values(),
                          key=lambda m: (-m.downloads, m.name)):
            if holo_type and meta.type != holo_type:
                continue
            result.append(meta.to_dict())
        return result
    
    def download(self, holo_id: str) -> List[Tuple[str, str, str, str]]:
        """
        Télécharge un hologramme — retourne les faits.
        """
        # ⚡ Cache mémoire : le rechargement npz est lent (~18s pour 5K faits)
        if not hasattr(self, '_dl_cache'):
            self._dl_cache = {}
        if holo_id in self._dl_cache:
            return self._dl_cache[holo_id]
        if holo_id not in self._registry:
            return []
        
        # Trouver le fichier
        meta = self._registry[holo_id]
        holo_path = self.store_dir / f'{holo_id}.npz'
        
        if not holo_path.exists():
            return []
        
        # Charger — ⚡ conversion en listes d'abord (l'accès indexé np est ~1000× plus lent)
        data = np.load(str(holo_path), allow_pickle=True)
        subs = list(data['subjects'])
        rels = list(data['relations'])
        objs = list(data['objects'])
        secs = list(data['sectors']) if 'sectors' in data else None
        facts = []
        for i in range(len(subs)):
            facts.append((
                str(subs[i]), str(rels[i]), str(objs[i]),
                str(secs[i]) if secs else 'GENERAL',
            ))
        
        # ⚡ Mettre en cache (max 20 hologrammes en mémoire)
        if len(self._dl_cache) >= 20:
            self._dl_cache.pop(next(iter(self._dl_cache)))
        self._dl_cache[holo_id] = facts
        
        # Incrémenter le compteur de téléchargements
        meta.downloads += 1
        self._save_registry()
        
        log.info(f"⬇️ Téléchargement {holo_id}: {len(facts):,} faits")
        return facts
    
    def download_metadata(self, holo_id: str) -> Optional[dict]:
        """Retourne les métadonnées d'un hologramme sans les faits."""
        meta = self._registry.get(holo_id)
        return meta.to_dict() if meta else None
    
    def publish(self, domain: str, facts: List[Tuple[str, str, str, str]],
                author: str, name: str = None, description: str = "") -> dict:
        """
        Publie un hologramme communautaire.
        """
        holo_id = f'community_{author}_{domain.lower().replace(" ", "_")[:20]}'
        
        if not facts:
            return {'success': False, 'error': 'Aucun fait à publier'}
        
        # Sauvegarder
        holo_path = self.store_dir / f'{holo_id}.npz'
        subjects = np.array([f[0] for f in facts], dtype=object)
        relations = np.array([f[1] for f in facts], dtype=object)
        objects = np.array([f[2] for f in facts], dtype=object)
        sectors_arr = np.array([f[3] for f in facts], dtype=object)
        
        np.savez_compressed(str(holo_path),
            subjects=subjects, relations=relations,
            objects=objects, sectors=sectors_arr,
            amplitudes=np.ones(len(facts), dtype=np.float32),
            psies_real=np.zeros((len(facts), 64), dtype=np.float32),
            psies_imag=np.zeros((len(facts), 64), dtype=np.float32))
        
        # Métadonnées
        subj_count = Counter(str(f[0]).lower() for f in facts)
        top_concepts = [s for s, _ in subj_count.most_common(10)]
        
        size_kb = holo_path.stat().st_size / 1024
        meta = HologramMeta(
            id=holo_id,
            name=name or f'{domain} (par {author})',
            domain=domain,
            icon='🌐',
            description=description or f'Hologramme communautaire: {domain}',
            facts_count=len(facts),
            sectors=list(set(f[3] for f in facts)),
            author=author,
            type='community',
            created_at=time.time(),
            top_concepts=top_concepts,
        )
        meta._size_kb = size_kb
        self._registry[holo_id] = meta
        self._save_registry()
        
        log.info(f"📤 Publication {holo_id}: {len(facts):,} faits par {author}")
        return {'success': True, 'holo_id': holo_id, 'facts_count': len(facts)}
    
    def stats(self) -> dict:
        official = sum(1 for m in self._registry.values() if m.type == 'official')
        community = sum(1 for m in self._registry.values() if m.type == 'community')
        total_facts = sum(m.facts_count for m in self._registry.values())
        total_downloads = sum(m.downloads for m in self._registry.values())
        return {
            'official_count': official,
            'community_count': community,
            'total_facts': total_facts,
            'total_downloads': total_downloads,
            'store_size_mb': round(
                sum(f.stat().st_size for f in self.store_dir.glob('*.npz')) / 1e6, 1
            ),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   📦 HOLOGRAM STORE — Construction des hologrammes        ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    store = HologramStore()
    
    # Construire les hologrammes officiels
    print("Construction des hologrammes officiels depuis le KB...")
    store.build_official_holograms()
    
    # Lister
    print()
    print("="*60)
    print("📦 HOLOGRAMMES DISPONIBLES")
    print("="*60)
    for h in store.list_holograms():
        print(f"  {h['icon']} {h['name']:30s} | {h['facts_count']:>6,} faits | "
              f"{h.get('size_kb', 0):>6.0f} KB | {h['type']}")
    
    # Stats
    print()
    print(store.stats())
    
    # Test download
    print()
    print("="*60)
    print("⬇️ TEST TÉLÉCHARGEMENT: medecine")
    print("="*60)
    facts = store.download('official_medecine')
    if facts:
        print(f"Téléchargé: {len(facts):,} faits")
        print("Échantillons:")
        for s, r, o, sec in facts[:5]:
            print(f"  [{sec}] {str(s)[:40]} | {str(r)[:25]} | {str(o)[:40]}")
