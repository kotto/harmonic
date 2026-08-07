"""
PageForge — Forge de Pages Harmonique
=======================================
Génération de pages entières à partir des données de base de l'IA Harmonique.
Mode conversationnel logique pour co-écrire et raffiner.

PRINCIPE FONDAMENTAL :
  Une page = une interférence organisée d'ondes-faits.
  Le squelette logique est la partition, les faits sont les musiciens,
  le tisseur est le chef d'orchestre.

ARCHITECTURE :
  1. LogicalSkeleton — Génère le plan (partition)
  2. ContentWeaver   — Tisse les faits en paragraphes (musiciens)
  3. PropagationOp   — Assure la cohérence section à section
  4. ConversationForge — Mode conversationnel d'édition
  5. PageExporter    — Export MD, HTML

Usage :
    from page_forge import PageForge

    forge = PageForge()

    # Mode one-shot
    page = forge.generate("Le paludisme : causes, symptômes et traitements")
    print(page.to_markdown())

    # Mode conversationnel
    forge.start_conversation()
    > écris une page sur la photosynthèse
    > développe la section sur la chlorophylle
    > rends-le plus poétique
    > export html
"""

import os, sys, json, math, time, random, re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque, Counter
from enum import Enum

import numpy as np

_MODULE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_MODULE_DIR))

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES HARMONIQUES
# ═══════════════════════════════════════════════════════════════════════════════

PHI = 1.618033988749895
TAU = 2.0 * math.pi
PHI_INV = 1.0 / PHI

# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS GRACEFUL — tout est optionnel, avec fallbacks
# ═══════════════════════════════════════════════════════════════════════════════

_HARMONIC_BRAIN = None
_HOLOGRAPHIC_ENCODER = None
_SECTORS = None
_KNOWLEDGE_BASE = None
_RESPONSE_COMPOSER = None
_KNOWLEDGE_ENRICHER = None
_DIALOGUE_PATTERNS = None
_FAST_RETRIEVER = None  # Retriever rapide (O(1), évite le brain lent)

def _lazy_imports():
    """Importe paresseusement les composants du cerveau harmonique."""
    global _HARMONIC_BRAIN, _HOLOGRAPHIC_ENCODER, _SECTORS
    global _KNOWLEDGE_BASE, _RESPONSE_COMPOSER, _KNOWLEDGE_ENRICHER, _DIALOGUE_PATTERNS
    global _FAST_RETRIEVER

    if _HARMONIC_BRAIN is not None:
        return True

    try:
        from harmonic_brain import HarmonicBrain
        _HARMONIC_BRAIN = HarmonicBrain
    except Exception:
        _HARMONIC_BRAIN = False

    try:
        from holographic_encoder import HolographicEncoder
        _HOLOGRAPHIC_ENCODER = HolographicEncoder
    except Exception:
        _HOLOGRAPHIC_ENCODER = False

    try:
        from qualitative_knowledge import SECTORS as _sec
        _SECTORS = _sec
    except Exception:
        _SECTORS = {}

    try:
        from harmonic_model import KNOWLEDGE_BASE as _kb
        _KNOWLEDGE_BASE = _kb
    except Exception:
        _KNOWLEDGE_BASE = []

    try:
        from response_composer import ResponseComposer
        _RESPONSE_COMPOSER = ResponseComposer()
    except Exception:
        _RESPONSE_COMPOSER = None

    try:
        from knowledge_enricher import KnowledgeEnricher
        _KNOWLEDGE_ENRICHER = KnowledgeEnricher()
        _KNOWLEDGE_ENRICHER.load_curated_defaults()
    except Exception:
        _KNOWLEDGE_ENRICHER = None

    try:
        from harmonic_dialogue import EXPRESSION_PATTERNS as _ep
        _DIALOGUE_PATTERNS = _ep
    except Exception:
        _DIALOGUE_PATTERNS = {}

    return _HARMONIC_BRAIN is not False


def _init_fast_retriever():
    """Initialise le FastRetriever — séparé pour éviter le délai du brain."""
    global _FAST_RETRIEVER, _KNOWLEDGE_BASE
    if _FAST_RETRIEVER is not None:
        return
    try:
        from fast_retriever import FastRetriever
        _FAST_RETRIEVER = FastRetriever()
        import os
        
        # 1. Shard enrichi Wikidata (28K faits propres)
        shard_path = os.path.join(os.path.dirname(__file__), 'data/kb_enriched/shard_0000.npz')
        if os.path.exists(shard_path):
            _FAST_RETRIEVER.load(shard_path)
        
        # 2. kb_final.npz (100K faits) — chargement rapide sans sectorisation
        kb_final_path = os.path.join(os.path.dirname(__file__), 'data/bootstrapper_output/kb_final.npz')
        if os.path.exists(kb_final_path):
            import numpy as np
            data = np.load(kb_final_path, allow_pickle=True)
            facts_raw = data.get('facts', [])
            clean = []
            seen = set()
            for f in facts_raw[:80000]:  # Top 80K
                s = str(f[0]).strip()
                r = str(f[1]).strip()
                o = str(f[2]).strip()
                sec = str(f[3]).strip() if len(f) > 3 else 'GENERAL'
                if s and s[0].isdigit() and '. ' in s[:6]:
                    s = s.split('. ', 1)[1]
                if len(s) < 2 or len(r) < 2 or len(o) < 2:
                    continue
                key = (s.lower()[:50], r.lower()[:50], o.lower()[:70])
                if key not in seen:
                    seen.add(key)
                    clean.append((s, r, o, sec))
            _FAST_RETRIEVER.add_facts(clean)
        
        # 3. KB original (SFT + curated)
        if _KNOWLEDGE_BASE is None or len(_KNOWLEDGE_BASE) == 0:
            _lazy_imports()
        if _KNOWLEDGE_BASE:
            _FAST_RETRIEVER.add_facts(_KNOWLEDGE_BASE)
        
        # 4. SFT haute amplitude
        try:
            from harmonic_quality import HIGH_AMPLITUDE_FACTS
            sft_facts = [(s, r, o, 'SFT') for (s, r, o), amp in HIGH_AMPLITUDE_FACTS.items()]
            _FAST_RETRIEVER.add_facts(sft_facts)
        except ImportError:
            pass
            
    except Exception as e:
        _FAST_RETRIEVER = None


# ═══════════════════════════════════════════════════════════════════════════════
# TYPES DE DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════════

DOCUMENT_TYPES = {
    'article': {
        'label': 'Article',
        'sections': ['introduction', 'contexte', 'point_1', 'point_2', 'point_3', 'conclusion'],
        'labels_fr': {
            'introduction': 'Introduction',
            'contexte': 'Contexte',
            'point_1': 'Premier aspect',
            'point_2': 'Deuxième aspect',
            'point_3': 'Troisième aspect',
            'conclusion': 'Conclusion'
        },
        'intro_weight': 0.15,
        'conclusion_weight': 0.12,
    },
    'rapport': {
        'label': 'Rapport',
        'sections': ['resume', 'introduction', 'analyse', 'resultats', 'discussion', 'conclusion'],
        'labels_fr': {
            'resume': 'Résumé',
            'introduction': 'Introduction',
            'analyse': 'Analyse',
            'resultats': 'Résultats',
            'discussion': 'Discussion',
            'conclusion': 'Conclusion'
        },
        'intro_weight': 0.10,
        'conclusion_weight': 0.15,
    },
    'lettre': {
        'label': 'Lettre',
        'sections': ['objet', 'introduction', 'corps', 'conclusion', 'signature'],
        'labels_fr': {
            'objet': 'Objet',
            'introduction': 'Introduction',
            'corps': 'Corps de la lettre',
            'conclusion': 'Conclusion',
            'signature': 'Formule de politesse'
        },
        'intro_weight': 0.10,
        'conclusion_weight': 0.10,
    },
    'tutoriel': {
        'label': 'Tutoriel',
        'sections': ['introduction', 'prerequis', 'etapes', 'details', 'conclusion'],
        'labels_fr': {
            'introduction': 'Introduction',
            'prerequis': 'Prérequis',
            'etapes': 'Étapes principales',
            'details': 'Détails et astuces',
            'conclusion': 'Conclusion'
        },
        'intro_weight': 0.12,
        'conclusion_weight': 0.10,
    },
    'page_web': {
        'label': 'Page web',
        'sections': ['hero', 'probleme', 'solution', 'avantages', 'appel_action'],
        'labels_fr': {
            'hero': 'Accroche',
            'probleme': 'Le problème',
            'solution': 'Notre solution',
            'avantages': 'Avantages clés',
            'appel_action': 'Passez à l\'action'
        },
        'intro_weight': 0.20,
        'conclusion_weight': 0.15,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# STRUCTURES DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

class StyleLevel(Enum):
    ACADEMIQUE = 'academique'
    VULGARISE = 'vulgarise'
    POETIQUE = 'poetique'
    TECHNIQUE = 'technique'
    JOURNALISTIQUE = 'journalistique'
    CONVERSATIONNEL = 'conversationnel'


@dataclass
class StyleConfig:
    """Configuration stylistique d'une page."""
    level: StyleLevel = StyleLevel.VULGARISE
    formality: float = 0.5       # 0 = décontracté, 1 = formel
    verbosity: float = 0.6       # 0 = concis, 1 = détaillé
    creativity: float = 0.3      # 0 = factuel, 1 = poétique
    language: str = 'fr'

    def to_dict(self):
        return {
            'level': self.level.value,
            'formality': self.formality,
            'verbosity': self.verbosity,
            'creativity': self.creativity,
            'language': self.language,
        }


@dataclass
class Section:
    """Une section de la page."""
    id: str                       # identifiant unique (ex: 'introduction')
    title: str                    # titre affiché
    content: str = ''             # contenu généré
    facts_used: List = field(default_factory=list)  # faits utilisés
    psi: Optional[np.ndarray] = None  # onde de la section (C^512)
    position_angle: float = 0.0   # angle dans le squelette (0° = début, 180° = fin)
    word_count: int = 0
    parent_id: Optional[str] = None


@dataclass
class PageState:
    """État complet d'une page en cours de rédaction."""
    topic: str                    # sujet principal
    doc_type: str = 'article'     # type de document
    title: str = ''               # titre de la page
    sections: List[Section] = field(default_factory=list)
    psi_page: Optional[np.ndarray] = None  # onde cumulée C^512
    style: StyleConfig = field(default_factory=StyleConfig)
    history: List[str] = field(default_factory=list)  # historique des commandes
    turn_count: int = 0
    created_at: float = 0.0
    updated_at: float = 0.0

    def get_section(self, section_id: str) -> Optional[Section]:
        for s in self.sections:
            if s.id == section_id:
                return s
        return None

    def section_index(self, section_id: str) -> int:
        for i, s in enumerate(self.sections):
            if s.id == section_id:
                return i
        return -1

    def total_words(self) -> int:
        return sum(s.word_count for s in self.sections)

    def to_dict(self) -> dict:
        return {
            'topic': self.topic,
            'doc_type': self.doc_type,
            'title': self.title,
            'sections': [
                {
                    'id': s.id,
                    'title': s.title,
                    'content': s.content,
                    'word_count': s.word_count,
                    'position_angle': s.position_angle,
                }
                for s in self.sections
            ],
            'style': self.style.to_dict(),
            'total_words': self.total_words(),
            'turn_count': self.turn_count,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SQUELETTE LOGIQUE
# ═══════════════════════════════════════════════════════════════════════════════

class LogicalSkeleton:
    """
    Génère le plan d'une page à partir d'un topic.
    Utilise la résonance sectorielle pour trouver des sous-thèmes connexes.
    """

    # Verbes d'exploration par type de relation cherchée
    _ASPECT_VERBS = [
        'est', 'constitue', 'implique', 'cause', 'provoque',
        'permet', 'nécessite', 'caractérise', 'définit', 'comprend',
        'inclut', 'a pour conséquence', 'est lié à', 'dépend de',
        'influence', 'régule', 'contrôle', 'maintient', 'produit',
    ]

    def __init__(self):
        self._encoder = None
        self._brain = None
        _lazy_imports()

    def _get_encoder(self):
        if self._encoder is None and _HOLOGRAPHIC_ENCODER and _HOLOGRAPHIC_ENCODER is not False:
            try:
                self._encoder = _HOLOGRAPHIC_ENCODER()
            except Exception:
                self._encoder = False
        return self._encoder if self._encoder and self._encoder is not False else None

    def _get_brain(self):
        if self._brain is None and _HARMONIC_BRAIN and _HARMONIC_BRAIN is not False:
            try:
                if _KNOWLEDGE_BASE:
                    self._brain = _HARMONIC_BRAIN(_KNOWLEDGE_BASE)
                else:
                    self._brain = _HARMONIC_BRAIN()
            except Exception:
                try:
                    self._brain = _HARMONIC_BRAIN([])
                except Exception:
                    self._brain = False
        return self._brain if self._brain and self._brain is not False else None

    def _detect_domain(self, topic: str) -> str:
        """Détecte le domaine principal d'un topic."""
        topic_lower = topic.lower()

        domain_keywords = {
            'sante_medical': ['maladie', 'symptôme', 'traitement', 'diagnostic', 'patient',
                            'médecin', 'infection', 'virus', 'bactérie', 'vaccin', 'paludisme',
                            'malaria', 'cancer', 'diabète', 'santé', 'médical', 'soin',
                            'chirurgie', 'hôpital', 'clinique', 'depistage', 'dépistage'],
            'sciences': ['physique', 'chimie', 'biologie', 'mathématique', 'atome', 'molécule',
                        'énergie', 'force', 'gravité', 'lumière', 'onde', 'électron',
                        'proton', 'neutron', 'quantique', 'relativité', 'évolution',
                        'gène', 'ADN', 'cellule', 'organisme', 'écosystème'],
            'technologie': ['code', 'programme', 'logiciel', 'algorithme', 'donnée',
                           'internet', 'réseau', 'serveur', 'application', 'mobile',
                           'intelligence artificielle', 'machine learning', 'cloud'],
            'philosophie': ['conscience', 'esprit', 'être', 'existence', 'réalité',
                           'vérité', 'moral', 'éthique', 'liberté', 'justice', 'âme'],
            'culture': ['art', 'musique', 'littérature', 'poésie', 'peinture', 'sculpture',
                       'cinéma', 'théâtre', 'histoire', 'civilisation', 'langue'],
            'economie': ['économie', 'marché', 'finance', 'investissement', 'croissance',
                        'PIB', 'inflation', 'emploi', 'commerce', 'entreprise'],
        }

        scores = Counter()
        for domain, keywords in domain_keywords.items():
            for kw in keywords:
                if kw in topic_lower:
                    scores[domain] += 1

        if scores:
            return scores.most_common(1)[0][0]
        return 'general'

    def _estimate_kb_coverage(self, topic: str) -> int:
        """
        Estime combien de faits pertinents existent dans le KB pour un topic.
        Détermine le niveau de couverture : 0-3 = faible, 4-8 = moyen, 9+ = bon.
        """
        count = 0
        topic_lower = topic.lower()
        topic_keywords = set(topic_lower.split())

        if _KNOWLEDGE_BASE:
            for fact in _KNOWLEDGE_BASE:
                s, r, o = fact[0].lower(), fact[1].lower(), fact[2].lower()
                text = f"{s} {r} {o}"
                # Compter comme pertinent si au moins un mot-clé du topic est présent
                if any(kw in s for kw in topic_keywords if len(kw) > 2):
                    count += 1
                elif topic_lower in text:
                    count += 1

        return count

    def _find_related_aspects(self, topic: str, count: int = 6) -> List[str]:
        """
        Trouve des aspects connexes par résonance dans le KB.
        Analyse les faits contenant le topic pour trouver des sujets reliés.
        """
        aspects = []

        # 1. Chercher dans le KB local
        if _KNOWLEDGE_BASE:
            topic_lower = topic.lower()
            related = Counter()
            for fact in _KNOWLEDGE_BASE:
                s, r, o, sec = fact[0], fact[1], fact[2], fact[3]
                text = f"{s} {r} {o}".lower()
                if topic_lower in text:
                    # Extraire les mots-clés (les plus longs)
                    for field in [s, r, o]:
                        words = field.lower().split()
                        for w in words:
                            if len(w) > 5 and w != topic_lower:
                                related[w] += 1

            # Les mots les plus fréquents sont probablement des aspects pertinents
            for word, _ in related.most_common(count * 2):
                if word not in aspects and word != topic_lower:
                    aspects.append(word)

        # 2. Générer des aspects par type de relation (si pas assez trouvés)
        aspect_templates = {
            'sante_medical': [
                'causes et facteurs de risque',
                'symptômes et manifestations cliniques',
                'diagnostic et dépistage',
                'traitements disponibles',
                'prévention et mesures de santé publique',
                'impact sur la population',
            ],
            'sciences': [
                'principes fondamentaux',
                'découvertes historiques',
                'applications pratiques',
                'implications théoriques',
                'recherches récentes',
                'perspectives futures',
            ],
            'technologie': [
                'fonctionnement technique',
                'architecture et conception',
                'cas d\'usage',
                'avantages et limites',
                'comparaison avec les alternatives',
                'tendances et évolution',
            ],
            'philosophie': [
                'origines et contexte historique',
                'concepts fondamentaux',
                'implications éthiques',
                'critiques et débats',
                'applications contemporaines',
                'liens avec d\'autres domaines',
            ],
            'culture': [
                'contexte historique',
                'figures et œuvres majeures',
                'influence et héritage',
                'interprétations et analyses',
                'liens avec la société',
                'actualité et pertinence',
            ],
            'economie': [
                'mécanismes fondamentaux',
                'facteurs d\'influence',
                'indicateurs clés',
                'acteurs et institutions',
                'impacts sur la société',
                'projections et tendances',
            ],
            'general': [
                'définition et concepts clés',
                'contexte et historique',
                'aspects principaux',
                'applications et exemples',
                'enjeux et défis',
                'perspectives d\'avenir',
            ],
        }

        domain = self._detect_domain(topic)
        templates = aspect_templates.get(domain, aspect_templates['general'])

        # Mélanger aspects trouvés et templates pour compléter
        result = []
        for a in aspects[:count]:
            result.append(a)
        for t in templates:
            if len(result) >= count:
                break
            if t.lower() not in [r.lower() for r in result]:
                result.append(t)

        return result[:count]

    def generate(self, topic: str, doc_type: str = 'article',
                 custom_sections: Optional[List[str]] = None) -> List[Section]:
        """
        Génère un squelette de page pour un topic donné.
        Adapte le nombre de sections à la couverture du KB.

        Args:
            topic: le sujet principal
            doc_type: type de document (article, rapport, lettre, tutoriel, page_web)
            custom_sections: titres de sections personnalisés (prioritaires)

        Returns:
            Liste de Sections avec titres et positions angulaires
        """
        doc_config = DOCUMENT_TYPES.get(doc_type, DOCUMENT_TYPES['article'])
        section_ids = list(doc_config['sections'])
        labels = doc_config['labels_fr']

        # Évaluer la couverture du KB pour ce topic
        kb_coverage = self._estimate_kb_coverage(topic)

        # Adapter le nombre de sections à la couverture (sans créer de doublons)
        if kb_coverage < 5 and not custom_sections:
            # Pour un KB pauvre, garder : intro, 1-2 contenu, conclusion
            essential = []
            content = []
            seen_ids = set()
            for sid in section_ids:
                if sid in seen_ids:
                    continue
                seen_ids.add(sid)
                if sid in ('introduction', 'conclusion', 'hero', 'resume', 'objet', 'signature', 'appel_action'):
                    essential.append(sid)
                else:
                    content.append(sid)

            # Construire la liste propre : intro(s) + max 2 contenu + conclusion(s)
            new_ids = []
            # Intro
            for eid in essential:
                if eid in ('introduction', 'hero', 'resume', 'objet'):
                    new_ids.append(eid)
            # Contenu (max 2)
            for cid in content[:max(1, kb_coverage)]:
                new_ids.append(cid)
            # Conclusion
            for eid in essential:
                if eid in ('conclusion', 'signature', 'appel_action'):
                    new_ids.append(eid)

            # Dédupliquer en gardant l'ordre
            section_ids = []
            seen = set()
            for sid in new_ids:
                if sid not in seen:
                    section_ids.append(sid)
                    seen.add(sid)
            # Si on a perdu des sections essentielles, les rajouter
            if 'introduction' not in section_ids:
                section_ids.insert(0, 'introduction')
            if 'conclusion' not in section_ids:
                section_ids.append('conclusion')
            # Re-dédupliquer
            section_ids = list(dict.fromkeys(section_ids))

        # Trouver des aspects pour enrichir les sections
        aspects = self._find_related_aspects(topic, count=len(section_ids))

        sections = []
        n = len(section_ids)

        for i, sec_id in enumerate(section_ids):
            # Position angulaire : 0° (intro) → 180° (conclusion)
            angle = (i / max(n - 1, 1)) * math.pi  # 0 à π

            # Titre par défaut
            title = labels.get(sec_id, sec_id.replace('_', ' ').title())

            # Enrichir les sections génériques avec des aspects
            if sec_id.startswith('point_') and aspects:
                idx = int(sec_id.split('_')[1]) if '_' in sec_id else i
                aspect_idx = idx - 1
                if aspect_idx < len(aspects):
                    aspect = aspects[aspect_idx]
                    # Nettoyer et capitaliser proprement
                    aspect_clean = aspect.strip().lower()
                    # Capitaliser chaque mot significatif
                    words = aspect_clean.split('_')
                    title = ' '.join(w[0].upper() + w[1:] if len(w) > 1 else w.upper() for w in words)
                    # Si le titre est trop court ou identique au topic, utiliser un titre plus descriptif
                    if len(title) < 5 or title.lower() == topic.lower():
                        fallback_titles = [
                            f'Aspect {idx} : {topic}',
                            f'Dimension {idx}',
                            f'Approfondissement {idx}',
                            f'Angle {idx}',
                        ]
                        title = fallback_titles[min(idx - 1, len(fallback_titles) - 1)]

            # Personnalisation selon le type
            if custom_sections and i < len(custom_sections):
                title = custom_sections[i]

            sections.append(Section(
                id=sec_id,
                title=title,
                position_angle=angle,
            ))

        return sections


# ═══════════════════════════════════════════════════════════════════════════════
# 2. TISSEUR DE CONTENU
# ═══════════════════════════════════════════════════════════════════════════════

class ContentWeaver:
    """
    Tisse les faits en paragraphes cohérents.
    V2 — fusion multi-faits au lieu de simple concaténation.
    """

    # ═══ PATTERNS DE TISSAGE (fusion multi-faits) ═══

    # Ouvertures de section (variées, non répétitives)
    _SECTION_OPENINGS = [
        "Abordons d'abord {topic}.",
        "Commençons par examiner {topic}.",
        "Le premier point à considérer est {topic}.",
        "Entrons dans le vif du sujet : {topic}.",
        "{topic} constitue un aspect fondamental.",
        "Pour bien comprendre, il faut d'abord saisir {topic}.",
        "Intéressons-nous à présent à {topic}.",
    ]

    # Fusion de 2 faits
    _FUSION_2 = [
        "{s1}, c'est-à-dire {o1}. De plus, {s1} {r2} {o2}.",
        "{s1} se définit comme {o1} — et {r2} {o2}.",
        "D'une part, {s1} {r1} {o1} ; d'autre part, {s1} {r2} {o2}.",
        "{s1} présente deux caractéristiques : {o1}, et {r2} {o2}.",
        "Non seulement {s1} {r1} {o1}, mais également {r2} {o2}.",
    ]

    # Fusion de 3+ faits
    _FUSION_3 = [
        "{s1} est caractérisé par trois aspects : premièrement, {o1} ; deuxièmement, {r2} {o2} ; troisièmement, {r3} {o3}.",
        "Pour cerner {s1}, il faut considérer que {o1}, que {r2} {o2}, et enfin que {r3} {o3}.",
        "{s1} — qui {r1} {o1} — {r2} {o2}, ce qui implique également que {r3} {o3}.",
    ]

    # Transitions entre paragraphes
    _TRANSITIONS = [
        "Cela nous amène à un autre point important.",
        "Approfondissons maintenant cet aspect.",
        "Cette analyse ouvre sur une autre dimension.",
        "Voyons à présent les implications concrètes.",
        "Ce qui précède éclaire le point suivant.",
        "Poursuivons avec un autre angle.",
        "Un autre élément mérite notre attention.",
    ]

    # Connecteurs intra-paragraphe
    _CONNECTORS = [
        "En effet, ", "Plus précisément, ", "Concrètement, ",
        "Autrement dit, ", "C'est-à-dire que ", "Il s'ensuit que ",
        "Par conséquent, ", "Ainsi, ", "De ce fait, ",
        "Notons que ", "Soulignons que ", "Il est important de noter que ",
    ]

    # Formules de conclusion
    _CONCLUSIONS = [
        "En définitive, {topic} apparaît comme un sujet riche aux multiples facettes.",
        "Ces différents aspects montrent la complexité et l'importance de {topic}.",
        "Ainsi, {topic} se révèle être bien plus qu'une simple notion : c'est un carrefour de connaissances.",
        "Pour conclure, {topic} mérite une attention soutenue, tant ses implications sont vastes.",
        "Au terme de cette exploration, {topic} nous laisse avec des perspectives stimulantes.",
        "En somme, comprendre {topic}, c'est ouvrir la porte à de nombreuses autres questions.",
    ]

    def __init__(self):
        self._brain = None
        self._encoder = None
        self._used_patterns: deque = deque(maxlen=30)

    def _get_brain(self):
        if self._brain is None:
            _lazy_imports()
            if _HARMONIC_BRAIN and _HARMONIC_BRAIN is not False:
                try:
                    if _KNOWLEDGE_BASE:
                        self._brain = _HARMONIC_BRAIN(_KNOWLEDGE_BASE)
                    else:
                        self._brain = _HARMONIC_BRAIN([])
                except Exception:
                    self._brain = False
        return self._brain if self._brain and self._brain is not False else None

    def _get_encoder(self):
        if self._encoder is None and _HOLOGRAPHIC_ENCODER and _HOLOGRAPHIC_ENCODER is not False:
            try:
                self._encoder = _HOLOGRAPHIC_ENCODER()
            except Exception:
                self._encoder = False
        return self._encoder if self._encoder and self._encoder is not False else None

    def _retrieve_facts(self, topic: str, max_facts: int = 8) -> List[Tuple[str, str, str, str]]:
        """Récupère les faits pertinents pour un topic, avec filtrage strict de pertinence."""
        facts = []
        topic_lower = topic.lower().strip()
        stopwords = {'le', 'la', 'les', 'de', 'des', 'du', 'un', 'une', 'et', 'est', 'a',
                     'que', 'qui', 'quoi', 'dans', 'sur', 'pour', 'avec', 'par', 'en',
                     'the', 'a', 'an', 'is', 'are', 'of', 'in', 'on', 'at', 'to', 'or',
                     'comment', 'pourquoi', 'quand', 'combien', 'cette', 'cet', 'ces',
                     'son', 'sa', 'ses', 'leur', 'leurs', 'aux', 'au', 'du', 'des',
                     'pas', 'plus', 'très', 'trop', 'peu', 'tout', 'tous', 'toute',
                     'bien', 'mal', 'mieux', 'comme', 'donc', 'alors', 'car',
                     'avec', 'sans', 'entre', 'chez', 'selon', 'entre', 'pendant',
                     'depuis', 'avant', 'après', 'contre', 'vers', 'sous', 'sur',
                     'aussi', 'ainsi', 'cependant', 'néanmoins', 'toutefois'}
        topic_keywords = [w for w in topic_lower.split() if len(w) > 2 and w not in stopwords]

        # 0. Via le FastRetriever (O(1), très rapide même sur 100K faits)
        _init_fast_retriever()
        if _FAST_RETRIEVER:
            try:
                results = _FAST_RETRIEVER.retrieve(topic, max_facts=max_facts, min_score=0.3)
                for s, r, o, sec, score in results:
                    facts.append((s, r, o, sec))
            except Exception:
                pass

        # 1. Via le cerveau harmonique (si dispo et pas déjà assez de faits)
        if len(facts) < 3:
            brain = self._get_brain()
            if brain:
                try:
                    result = brain.process(topic, lang='fr', max_accepted=max_facts)
                    if result and result.facts_used:
                        for f in result.facts_used[:max_facts]:
                            fact_tuple = (f.sujet, f.relation, f.objet, f.secteur if hasattr(f, 'secteur') else '')
                            if fact_tuple not in facts:
                                facts.append(fact_tuple)
                except Exception:
                    pass

        # 2. Via la base de connaissance locale — avec filtrage strict
        if not facts and _KNOWLEDGE_BASE and topic_keywords:
            scored = []
            for fact in _KNOWLEDGE_BASE:
                s, r, o, sec = fact[0].lower(), fact[1].lower(), fact[2].lower(), fact[3]
                text = f"{s} {r} {o}"

                # VÉRIFICATION STRICTE : au moins un mot-clé du topic doit apparaître
                # dans le sujet du fait (pas juste n'importe où)
                topic_in_subject = any(kw in s for kw in topic_keywords)
                topic_in_object = any(kw in o for kw in topic_keywords)
                topic_in_text = any(kw in text for kw in topic_keywords)

                if not (topic_in_subject or topic_in_object):
                    continue

                # Calculer le score de pertinence
                score = 0.0
                # Bonus fort si le topic entier est dans le sujet
                if topic_lower in s:
                    score += 5.0
                elif any(kw == s.strip() for kw in topic_keywords):
                    score += 4.0
                # Bonus si mot-clé dans le sujet
                if topic_in_subject:
                    score += 3.0
                # Bonus si mot-clé dans l'objet
                if topic_in_object:
                    score += 2.0
                # Bonus mineur si mot-clé ailleurs dans le fait
                if topic_in_text:
                    score += 0.5

                if score >= 2.0:  # Seuil minimum de pertinence
                    scored.append((score, fact))

            scored.sort(key=lambda x: x[0], reverse=True)

            # Garder seulement les faits vraiment pertinents (top scores)
            if scored:
                best_score = scored[0][0]
                # Garder les faits qui ont au moins 40% du meilleur score
                for score, fact in scored:
                    if score >= best_score * 0.4 and len(facts) < max_facts:
                        if fact not in facts:
                            facts.append(fact)

        # 3. Via l'enrichisseur (seulement si on a très peu de faits)
        if _KNOWLEDGE_ENRICHER and len(facts) < 2:
            try:
                # Chercher par mots-clés
                for kw in topic_keywords[:3]:
                    bloc = _KNOWLEDGE_ENRICHER.get_bloc(kw, 'definition')
                    if bloc:
                        facts.append((kw, 'se définit comme', bloc[:200] + '...', 'ENRICHISSEMENT'))
                        break
            except Exception:
                pass

        return facts[:max_facts]

    def _pick_pattern(self, patterns: List[str]) -> str:
        """Choisit un pattern non utilisé récemment."""
        available = [p for p in patterns if p not in self._used_patterns]
        if not available:
            available = patterns
        chosen = random.choice(available)
        self._used_patterns.append(chosen)
        if len(self._used_patterns) > 30:
            self._used_patterns.popleft()
        return chosen

    def _fuse_facts(self, facts: List[Tuple[str, str, str, str]], topic: str,
                    style: StyleConfig, section_type: str = 'development') -> str:
        """
        Fusionne plusieurs faits en un paragraphe cohérent.
        Utilise WaveNarrative pour une génération ondulatoire variée.
        """
        if not facts:
            if style.language == 'fr':
                return f"Les informations spécifiques sur {topic} sont encore en cours d'acquisition dans notre base de connaissance."
            return f"Specific information about {topic} is still being acquired."

        # Tenter la synthèse ondulatoire d'abord
        try:
            if not hasattr(self, '_wave_narrative'):
                from wave_narrative import WaveNarrative
                self._wave_narrative = WaveNarrative()
            text = self._wave_narrative.synthesize(facts, topic=topic,
                                                    section_type=section_type)
            if text and len(text) > 30:
                return text
        except Exception:
            pass

        # Fallback : ancien système de templates
        return self._fuse_facts_template(facts, topic, style)

    def _fuse_facts_template(self, facts: List[Tuple[str, str, str, str]], topic: str,
                             style: StyleConfig) -> str:
        """Ancien système de templates (fallback)."""
        if not facts:
            if style.language == 'fr':
                return f"Les informations spécifiques sur {topic} sont encore en cours d'acquisition dans notre base de connaissance. Nous enrichissons ce sujet continuellement."
            return f"Specific information about {topic} is still being acquired in our knowledge base. We continuously enrich this topic."

        n = len(facts)

        # Capitaliser la première lettre
        def cap(text: str) -> str:
            return text[0].upper() + text[1:] if text else text

        def decap(text: str) -> str:
            return text[0].lower() + text[1:] if text else text

        # Nettoyer un fait pour l'affichage
        def clean_fact(fact):
            s, r, o = fact[0], fact[1], fact[2]
            s = s.strip()
            r = r.strip()
            o = o.strip()
            # Éviter la répétition du sujet dans la relation
            if r.startswith(s):
                r = r[len(s):].strip()
            return s, r, o

        # Si un seul fait
        if n == 1:
            s, r, o = clean_fact(facts[0])
            openings = [
                f"{cap(s)} {r} {o}.",
                f"L'essentiel à savoir : {s} {r} {o}.",
                f"Pour commencer, {s} {r} {o}.",
                f"{cap(s)} — {decap(r)} {o}.",
            ]
            return random.choice(openings)

        # Fusion de 2 faits
        if n == 2:
            s1, r1, o1 = clean_fact(facts[0])
            s2, r2, o2 = clean_fact(facts[1])

            # Si même sujet → fusion élégante
            if s1.lower() == s2.lower():
                pattern = self._pick_pattern(self._FUSION_2)
                return pattern.format(s1=cap(s1), r1=r1, o1=o1, r2=r2, o2=o2).replace('  ', ' ')
            else:
                # Sujets différents → deux phrases avec connecteur
                connectors = ['De plus, ', 'Par ailleurs, ', 'En complément, ', 'Aussi, ']
                conn = random.choice(connectors)
                return f"{cap(s1)} {r1} {o1}. {conn}{s2} {r2} {o2}."

        # Fusion de 3+ faits
        if n >= 3:
            s1, r1, o1 = clean_fact(facts[0])
            s2, r2, o2 = clean_fact(facts[1])
            s3, r3, o3 = clean_fact(facts[2])

            # Essayer la fusion si le sujet est le même
            if s1.lower() == s2.lower() == s3.lower():
                pattern = self._pick_pattern(self._FUSION_3)
                return pattern.format(s1=cap(s1), r1=r1, o1=o1, r2=r2, o2=o2, r3=r3, o3=o3).replace('  ', ' ')

            # Sinon, construire un paragraphe structuré
            parts = []
            for i, fact in enumerate(facts[:4]):
                s, r, o = clean_fact(fact)
                if i == 0:
                    parts.append(f"{cap(s)} {r} {o}.")
                else:
                    conn = random.choice(self._CONNECTORS)
                    if s.lower() == facts[0][0].lower():
                        parts.append(f"{conn}{r} {o}.")
                    else:
                        parts.append(f"{conn}{s} {r} {o}.")

            return ' '.join(parts)

    def weave(self, section: Section, page: PageState,
              facts_override: Optional[List] = None,
              used_facts: Optional[set] = None) -> Section:
        """
        Tisse le contenu d'une section.

        Args:
            section: la section à remplir
            page: l'état complet de la page
            facts_override: faits à utiliser (prioritaires sur le retrieval)
            used_facts: ensemble de signatures de faits déjà utilisés (pour déduplication)

        Returns:
            La section mise à jour avec son contenu
        """
        if used_facts is None:
            used_facts = set()

        topic = section.title
        page_topic = page.topic if page else topic  # Utiliser le sujet de la page pour le wave narrative
        style = page.style

        # Récupérer les faits
        if facts_override:
            facts = facts_override
        else:
            # Générer des sous-thèmes pertinents pour cette section
            generic_ids = {'introduction', 'conclusion', 'hero', 'resume', 'objet', 'signature',
                          'contexte', 'discussion', 'appel_action'}
            
            # Pour les sections de contenu, chercher des aspects variés
            aspect_terms = {
                'introduction': ['définition', 'est', 'origines', 'fondements'],
                'contexte': ['histoire', 'évolution', 'contexte', 'origine', 'découverte'],
                'conclusion': ['impact', 'héritage', 'importance', 'futur', 'perspectives'],
            }
            
            search_terms = aspect_terms.get(section.id, [])
            search_query = page_topic
            
            # Ajouter des termes de recherche pour diversifier
            if search_terms and section.id not in ('introduction', 'conclusion'):
                extra_term = random.choice(search_terms)
                search_query = f"{page_topic} {extra_term}"
            elif section.id not in generic_ids:
                # Sections nommées : utiliser le titre comme aspect
                search_query = f"{page_topic} {section.title}"
            
            facts = self._retrieve_facts(search_query, max_facts=6)

        # Dédupliquer les faits déjà utilisés dans d'autres sections
        fresh_facts = []
        for f in facts:
            sig = (f[0].lower().strip(), f[1].lower().strip(), f[2].lower().strip())
            if sig not in used_facts:
                fresh_facts.append(f)
                used_facts.add(sig)

        # Si pas assez de faits frais, compléter avec les faits trouvés
        if len(fresh_facts) < 2:
            for f in facts:
                sig = (f[0].lower().strip(), f[1].lower().strip(), f[2].lower().strip())
                if f not in fresh_facts and len(fresh_facts) < 4:
                    fresh_facts.append(f)
                    used_facts.add(sig)

        facts = fresh_facts

        # Fusionner en paragraphe
        # Déterminer le type de section pour le wave narrative
        section_type_map = {
            'introduction': 'introduction', 'hero': 'introduction',
            'resume': 'introduction', 'objet': 'introduction',
            'conclusion': 'conclusion', 'signature': 'conclusion',
            'appel_action': 'conclusion',
        }
        sec_type = section_type_map.get(section.id, 'development')

        content = self._fuse_facts(facts, page_topic, style, section_type=sec_type)

        # Ajouter une phrase de transition si ce n'est pas l'intro
        if section.id not in ('introduction', 'hero', 'resume', 'objet'):
            transition = random.choice(self._TRANSITIONS)
            content = transition + ' ' + content

        # Pour l'introduction, ajouter une accroche
        if section.id in ('introduction', 'hero'):
            openings = [
                f"{page.topic} est un sujet fascinant qui mérite une exploration approfondie.",
                f"Dans cette page, nous allons explorer {page.topic} sous ses différents aspects.",
                f"Bienvenue dans cette exploration de {page.topic}.",
                f"{page.topic} — un sujet aux multiples dimensions que nous allons décortiquer ensemble.",
            ]
            hook = random.choice(openings)
            content = hook + ' ' + content

        # Pour la conclusion
        if section.id == 'conclusion':
            conclusions = [
                f"En définitive, {page.topic} apparaît comme un sujet riche aux multiples facettes.",
                f"Ces différents aspects montrent la complexité et l'importance de {page.topic}.",
                f"Ainsi, {page.topic} se révèle être bien plus qu'une simple notion : c'est un carrefour de connaissances.",
                f"Pour conclure, {page.topic} mérite une attention soutenue, tant ses implications sont vastes.",
                f"Au terme de cette exploration, {page.topic} nous laisse avec des perspectives stimulantes.",
                f"En somme, comprendre {page.topic}, c'est ouvrir la porte à de nombreuses autres questions.",
            ]
            content = random.choice(conclusions) + ' ' + content

        section.content = content
        section.facts_used = facts
        section.word_count = len(content.split())
        return section


# ═══════════════════════════════════════════════════════════════════════════════
# 3. OPÉRATEUR DE PROPAGATION LOGIQUE
# ═══════════════════════════════════════════════════════════════════════════════

class PropagationOperator:
    """
    L'opérateur P qui assure la cohérence section à section.

    ψ_k = P(ψ_{k-1}, ψ_topic_k, ψ_skeleton)

    Math :
      ψ_k = γ · ψ_faits + (1-γ) · ψ_{k-1} · e^{iδ}

    où :
      - γ = coefficient de nouveauté (0.7 = 70% nouveau contenu)
      - δ = déphasage de progression (~π/6)
      - ψ_faits = superposition cohérente des faits de la section k
    """

    def __init__(self, gamma: float = 0.7, delta: float = None):
        self.gamma = gamma  # nouveauté
        self.delta = delta if delta is not None else math.pi / 6  # progression
        self._encoder = None

    def _get_encoder(self):
        if self._encoder is None:
            _lazy_imports()
            if _HOLOGRAPHIC_ENCODER and _HOLOGRAPHIC_ENCODER is not False:
                try:
                    self._encoder = _HOLOGRAPHIC_ENCODER()
                except Exception:
                    self._encoder = False
        return self._encoder if self._encoder and self._encoder is not False else None

    def _encode_text(self, text: str, dim: int = 512) -> np.ndarray:
        """Encode un texte en vecteur d'onde complexe."""
        encoder = self._get_encoder()
        if encoder:
            try:
                return encoder.encode_query(text)
            except Exception:
                pass

        # Fallback déterministe
        np.random.seed(hash(text) & 0xFFFFFFFF)
        real = np.random.randn(dim)
        imag = np.random.randn(dim)
        v = real + 1j * imag
        return v / (np.linalg.norm(v) + 1e-10)

    def _coherence(self, psi_a: np.ndarray, psi_b: np.ndarray) -> float:
        """Cohérence entre deux ondes."""
        if psi_a is None or psi_b is None:
            return 0.0
        dot = np.abs(np.dot(psi_a.conj(), psi_b))
        na = np.linalg.norm(psi_a)
        nb = np.linalg.norm(psi_b)
        return min(1.0, float(dot / (na * nb + 1e-10)))

    def _bind(self, psi_a: np.ndarray, psi_b: np.ndarray) -> np.ndarray:
        """Binding HRR : convolution circulaire via FFT."""
        A = np.fft.fft(psi_a)
        B = np.fft.fft(psi_b)
        result = np.fft.ifft(A * B)
        return result / (np.linalg.norm(result) + 1e-10)

    def propagate(self, psi_prev: Optional[np.ndarray],
                  section_topic: str, psi_skeleton: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Calcule l'onde de la section courante par propagation logique.

        Args:
            psi_prev: onde de la section précédente (None si première section)
            section_topic: le sujet de la section courante
            psi_skeleton: onde contraignante du squelette (None si pas de contrainte)

        Returns:
            ψ_section ∈ C^512
        """
        dim = 512

        # Encoder le topic de la section
        psi_topic = self._encode_text(section_topic, dim)

        if psi_prev is None:
            # Première section : pas de précédent
            if psi_skeleton is not None:
                return self._bind(psi_skeleton, psi_topic)
            return psi_topic

        # Calculer la cohérence entre le précédent et le nouveau
        coh = self._coherence(psi_prev, psi_topic)

        # Ajuster gamma selon la cohérence
        # Forte cohérence → plus de rappel du contexte précédent
        # Faible cohérence → plus de nouveau contenu
        gamma_eff = self.gamma * (1.0 - coh * 0.3)

        # Déphasage de progression
        delta_phase = self.delta * math.exp(-coh)  # déphasage plus grand si faible cohérence
        psi_prev_rotated = psi_prev * np.exp(1j * delta_phase)

        # Superposition
        psi_section = gamma_eff * psi_topic + (1.0 - gamma_eff) * psi_prev_rotated

        # Appliquer la contrainte du squelette si présente
        if psi_skeleton is not None:
            psi_section = 0.7 * psi_section + 0.3 * self._bind(psi_skeleton, psi_topic)

        # Normaliser
        psi_section = psi_section / (np.linalg.norm(psi_section) + 1e-10)

        return psi_section


# ═══════════════════════════════════════════════════════════════════════════════
# 4. FORGE CONVERSATIONNELLE
# ═══════════════════════════════════════════════════════════════════════════════

class ConversationForge:
    """
    Mode conversationnel pour co-écrire une page.
    Interprète les commandes en langage naturel comme des modulations de ψ_page.
    """

    _COMMAND_PATTERNS = [
        # (regex, command_name, target_group, param_group)
        (r"(?:développe|developpe|détaille|detail|expande?|plus sur| approfondi)\s+(?:la\s+)?(?:section\s+)?['\"]?(\w+(?:\s+\w+)?)['\"]?", 'expand', 0, None),
        (r"(?:résume|resume|condense|raccourci|abrège|abrege)\s+(?:la\s+)?(?:section\s+)?['\"]?(\w+(?:\s+\w+)?)['\"]?", 'condense', 0, None),
        (r"(?:reformule|réécris|reecris|rephrase|change)\s+(?:la\s+)?(?:section\s+)?['\"]?(\w+(?:\s+\w+)?)['\"]?", 'rephrase', 0, None),
        (r"(?:ajoute|ajouter|nouvelle)\s+(?:une\s+)?(?:section|partie)\s+['\"]?(.+?)['\"]?(?:\s*$)", 'add_section', 0, None),
        (r"(?:supprime|enlève|enleve|retire|efface)\s+(?:la\s+)?(?:section\s+)?['\"]?(\w+(?:\s+\w+)?)['\"]?", 'remove', 0, None),
        (r"(?:réorganise|reorganise|réordonne|reordonne|déplace|deplace)\s+(?:les\s+sections?\s+)?(.+)", 'reorder', 0, None),
        (r"(?:rends?|rendre|fais|faire)\s+(?:le|la|plus|moins|ça|ca)\s*(.+)?", 'restyle', 0, None),
        (r"(?:exporte?|export|sauvegarde?|save)\s+(?:en\s+)?(md|markdown|html|json|txt)", 'export', 0, None),
        (r"génère?\s+(?:toute?\s+)?(?:la\s+)?page", 'weave_all', None, None),
        (r"(?:affiche|montre|voir|lis)\s+(?:le\s+)?(?:plan|squelette|skeleton|outline)", 'show_skeleton', None, None),
        (r"change\s+(?:le\s+)?type\s+(?:en\s+)?(\w+)", 'change_type', 0, None),
        (r"change\s+(?:le\s+)?(?:style|ton)\s+(?:en\s+)?(\w+)", 'change_style', 0, None),
        (r"aide|help|\?", 'help', None, None),
    ]

    def __init__(self):
        self._conversation_context: List[str] = []

    def parse_command(self, user_input: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse une commande en langage naturel.

        Returns:
            (command_name, target, params) ou (None, None, None) si pas une commande
        """
        text = user_input.strip().lower()

        for pattern, cmd, target_idx, param_idx in self._COMMAND_PATTERNS:
            match = re.search(pattern, text)
            if match:
                target = match.group(1) if match.lastindex and match.lastindex >= 1 else None
                params = match.group(2) if match.lastindex and match.lastindex >= 2 else None
                return cmd, target, params

        return None, None, None

    def handle_command(self, user_input: str, page: PageState) -> Tuple[str, PageState]:
        """
        Traite une commande conversationnelle.

        Returns:
            (response_message, updated_page_state)
        """
        cmd, target, params = self.parse_command(user_input)

        if cmd is None:
            # Pas une commande → considérer comme une question/commentaire
            return self._handle_free_text(user_input, page)

        handlers = {
            'expand': self._handle_expand,
            'condense': self._handle_condense,
            'rephrase': self._handle_rephrase,
            'add_section': self._handle_add_section,
            'remove': self._handle_remove,
            'reorder': self._handle_reorder,
            'restyle': self._handle_restyle,
            'export': self._handle_export,
            'weave_all': self._handle_weave_all,
            'show_skeleton': self._handle_show_skeleton,
            'change_type': self._handle_change_type,
            'change_style': self._handle_change_style,
            'help': self._handle_help,
        }

        handler = handlers.get(cmd)
        if handler:
            return handler(page, target, params)

        return f"Commande '{cmd}' non reconnue. Tapez 'aide' pour voir les commandes disponibles.", page

    def _handle_free_text(self, text: str, page: PageState) -> Tuple[str, PageState]:
        """Texte libre — considéré comme une demande de nouvelle page ou une question."""
        # Détecter si c'est une demande de création de page
        creation_patterns = [
            r"(?:écris|ecris|crée|cree|rédige|redige|génère|genere|écrire|ecrire)\s+(?:une\s+)?(?:page|article|rapport|lettre)\s+(?:sur\s+|à\s+propos\s+de\s+|au\s+sujet\s+de\s+)?(.+)",
            r"(?:parle|explique|décris|decris)\s+(?:moi\s+)?(?:de\s+|du\s+|des\s+|d'\s*)?(.+)",
        ]

        for pattern in creation_patterns:
            match = re.search(pattern, text.lower())
            if match:
                topic = match.group(1).strip()
                return (
                    f"Je vais créer une page sur « {topic} ». "
                    f"Je vous propose d'abord un plan. Tapez 'génère la page' quand vous êtes prêt, "
                    f"ou modifiez le plan avec des commandes comme 'ajoute une section ...'.",
                    page
                )

        return (
            f"Je ne comprends pas cette demande. "
            f"Essayez 'écris une page sur [sujet]' ou tapez 'aide' pour voir les commandes.",
            page
        )

    def _handle_expand(self, page: PageState, target: str, params: str) -> Tuple[str, PageState]:
        section = page.get_section(target)
        if section:
            section.content += "\n\n[Contenu développé — cette section mérite plus de faits et d'exemples.]"
            return f"✅ Section '{section.title}' développée.", page
        return f"❌ Section '{target}' non trouvée.", page

    def _handle_condense(self, page: PageState, target: str, params: str) -> Tuple[str, PageState]:
        section = page.get_section(target)
        if section:
            # Garder la première phrase
            sentences = section.content.split('.')
            section.content = '.'.join(sentences[:2]) + '.'
            section.word_count = len(section.content.split())
            return f"✅ Section '{section.title}' condensée.", page
        return f"❌ Section '{target}' non trouvée.", page

    def _handle_rephrase(self, page: PageState, target: str, params: str) -> Tuple[str, PageState]:
        section = page.get_section(target)
        if section:
            # Simuler une reformulation
            section.content = f"[Reformulé] {section.content}"
            return f"✅ Section '{section.title}' reformulée.", page
        return f"❌ Section '{target}' non trouvée.", page

    def _handle_add_section(self, page: PageState, target: str, params: str) -> Tuple[str, PageState]:
        if target:
            new_id = target.lower().replace(' ', '_')
            new_section = Section(
                id=new_id,
                title=target,
                position_angle=math.pi / 2,  # milieu
            )
            # Insérer avant la conclusion
            concl_idx = page.section_index('conclusion')
            if concl_idx >= 0:
                page.sections.insert(concl_idx, new_section)
            else:
                page.sections.append(new_section)
            return f"✅ Nouvelle section '{target}' ajoutée.", page
        return "❌ Précisez le titre de la section à ajouter.", page

    def _handle_remove(self, page: PageState, target: str, params: str) -> Tuple[str, PageState]:
        idx = page.section_index(target)
        if idx >= 0:
            removed = page.sections.pop(idx)
            return f"✅ Section '{removed.title}' supprimée.", page
        return f"❌ Section '{target}' non trouvée.", page

    def _handle_reorder(self, page: PageState, target: str, params: str) -> Tuple[str, PageState]:
        return "🔄 Fonction de réorganisation : décrivez l'ordre souhaité (ex: 'introduction, point_2, point_1, conclusion').", page

    def _handle_restyle(self, page: PageState, target: str, params: str) -> Tuple[str, PageState]:
        style_map = {
            'académique': StyleLevel.ACADEMIQUE,
            'academique': StyleLevel.ACADEMIQUE,
            'vulgarisé': StyleLevel.VULGARISE,
            'vulgarise': StyleLevel.VULGARISE,
            'poétique': StyleLevel.POETIQUE,
            'poetique': StyleLevel.POETIQUE,
            'technique': StyleLevel.TECHNIQUE,
            'journalistique': StyleLevel.JOURNALISTIQUE,
            'conversationnel': StyleLevel.CONVERSATIONNEL,
            'simple': StyleLevel.VULGARISE,
            'formel': StyleLevel.ACADEMIQUE,
            'créatif': StyleLevel.POETIQUE,
            'creatif': StyleLevel.POETIQUE,
        }

        if target and target.lower() in style_map:
            page.style.level = style_map[target.lower()]
            return f"✅ Style changé en '{page.style.level.value}'.", page
        return (
            f"🎨 Styles disponibles : académique, vulgarisé, poétique, technique, journalistique, conversationnel.\n"
            f"Style actuel : {page.style.level.value}.",
            page
        )

    def _handle_export(self, page: PageState, target: str, params: str) -> Tuple[str, PageState]:
        exporter = PageExporter()
        fmt = target or 'md'

        if fmt == 'html':
            output = exporter.to_html(page)
            filename = f"page_{page.topic.lower().replace(' ', '_')[:30]}.html"
        else:
            output = exporter.to_markdown(page)
            filename = f"page_{page.topic.lower().replace(' ', '_')[:30]}.md"

        # Écrire le fichier
        filepath = _MODULE_DIR / filename
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output)
            return f"✅ Page exportée : {filepath}", page
        except Exception as e:
            return f"❌ Erreur d'export : {e}", page

    def _handle_weave_all(self, page: PageState, target: str, params: str) -> Tuple[str, PageState]:
        return "📝 Demande de génération complète — sera traitée par PageForge.generate().", page

    def _handle_show_skeleton(self, page: PageState, target: str, params: str) -> Tuple[str, PageState]:
        lines = [f"📋 Plan de la page : {page.title or page.topic}"]
        for i, s in enumerate(page.sections):
            status = "✅" if s.content else "⏳"
            lines.append(f"  {i+1}. {status} {s.title}")
        return '\n'.join(lines), page

    def _handle_change_type(self, page: PageState, target: str, params: str) -> Tuple[str, PageState]:
        if target and target.lower() in DOCUMENT_TYPES:
            page.doc_type = target.lower()
            return f"✅ Type changé en '{target}'. Le plan sera mis à jour.", page
        types = ', '.join(DOCUMENT_TYPES.keys())
        return f"📄 Types disponibles : {types}. Type actuel : {page.doc_type}.", page

    def _handle_change_style(self, page: PageState, target: str, params: str) -> Tuple[str, PageState]:
        return self._handle_restyle(page, target, params)

    def _handle_help(self, page: PageState, target: str, params: str) -> Tuple[str, PageState]:
        help_text = """
🛠️ **COMMANDES DISPONIBLES**

**Création :**
  écris une page sur [sujet]   → Créer une nouvelle page
  génère la page               → Générer tout le contenu

**Édition du plan :**
  ajoute une section [titre]   → Ajouter une section
  supprime [section]           → Supprimer une section
  change le type en [type]     → Changer le type de document

**Édition du contenu :**
  développe [section]          → Développer une section
  résume [section]             → Condenser une section
  reformule [section]          → Reformuler une section

**Style :**
  rends-le plus [style]        → Changer le style
  change le style en [style]   → Styles : académique, vulgarisé, poétique, technique

**Export :**
  export [md|html]             → Sauvegarder la page

**Navigation :**
  montre le plan               → Afficher le squelette
  aide                         → Cette aide
"""
        return help_text, page


# ═══════════════════════════════════════════════════════════════════════════════
# 5. EXPORTEUR
# ═══════════════════════════════════════════════════════════════════════════════

class PageExporter:
    """Exporte une page en Markdown, HTML ou texte brut."""

    def to_markdown(self, page: PageState) -> str:
        """Export en Markdown."""
        lines = []
        title = page.title or page.topic

        lines.append(f"# {title}\n")
        lines.append(f"*Page générée par KA PageForge — {time.strftime('%d %B %Y')}*\n")

        for section in page.sections:
            if section.content:
                lines.append(f"## {section.title}\n")
                lines.append(section.content)
                lines.append('')

        if not any(s.content for s in page.sections):
            lines.append("*Aucune section n'a encore été générée. Utilisez 'génère la page' pour créer le contenu.*\n")

        return '\n'.join(lines)

    def to_html(self, page: PageState) -> str:
        """Export en HTML avec style harmonique."""
        md_content = self.to_markdown(page)

        # Conversion basique MD → HTML
        html_content = md_content
        html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'\n\n', '</p>\n<p>', html_content)
        html_content = '<p>' + html_content + '</p>'
        html_content = html_content.replace('<p></p>', '<br>')
        html_content = html_content.replace('</p>\n<p>', '</p>\n\n<p>')

        return f"""<!DOCTYPE html>
<html lang="{page.style.language}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page.title or page.topic}</title>
<style>
  :root {{
    --bg: #0a0a1a;
    --text: #e0e0e0;
    --accent: #c9a0dc;
    --gold: #d4a843;
    --green: #7ec8a0;
    --heading: #f0e6ff;
  }}
  body {{
    font-family: 'Georgia', 'Segoe UI', serif;
    background: var(--bg);
    color: var(--text);
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    line-height: 1.8;
  }}
  h1 {{ color: var(--heading); border-bottom: 2px solid var(--accent); padding-bottom: 0.5rem; }}
  h2 {{ color: var(--accent); margin-top: 2rem; }}
  p {{ margin: 1rem 0; text-align: justify; }}
  em {{ color: var(--gold); }}
  strong {{ color: var(--green); }}
</style>
</head>
<body>
{html_content}
<hr>
<footer>
  <p><em>Généré par KA PageForge — Intelligence Ondulatoire</em></p>
  <p>{time.strftime('%d/%m/%Y %H:%M')} — {page.total_words()} mots</p>
</footer>
</body>
</html>"""

    def to_text(self, page: PageState) -> str:
        """Export texte brut."""
        lines = [page.title or page.topic, '=' * len(page.title or page.topic), '']
        for s in page.sections:
            if s.content:
                lines.append(s.title.upper())
                lines.append('-' * len(s.title))
                lines.append(s.content)
                lines.append('')
        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ORCHESTRATEUR PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class PageForge:
    """
    Forge de Pages Harmonique — Interface unifiée.

    Usage :
        forge = PageForge()

        # Mode one-shot
        page = forge.generate("La photosynthèse")
        print(page.to_markdown())

        # Mode conversationnel
        forge.start_conversation()
    """

    def __init__(self):
        self.skeleton_gen = LogicalSkeleton()
        self.weaver = ContentWeaver()
        self.propagator = PropagationOperator()
        self.conversation = ConversationForge()
        self.exporter = PageExporter()

        self._current_page: Optional[PageState] = None
        self._ready = False

        # Chargement paresseux des composants lourds
        _lazy_imports()

    @property
    def ready(self) -> bool:
        return self._ready

    def generate_outline(self, topic: str, doc_type: str = 'article',
                         custom_sections: Optional[List[str]] = None) -> PageState:
        """
        Génère le squelette d'une page (sans le contenu).

        Args:
            topic: le sujet principal
            doc_type: type de document ('article', 'rapport', 'lettre', 'tutoriel', 'page_web')
            custom_sections: titres de sections personnalisés

        Returns:
            PageState avec le squelette prêt
        """
        sections = self.skeleton_gen.generate(topic, doc_type, custom_sections)

        page = PageState(
            topic=topic,
            doc_type=doc_type,
            title=topic,
            sections=sections,
            created_at=time.time(),
            updated_at=time.time(),
        )

        self._current_page = page
        return page

    def generate(self, topic: str, doc_type: str = 'article',
                 custom_sections: Optional[List[str]] = None,
                 style: Optional[StyleConfig] = None) -> PageState:
        """
        Génère une page complète en one-shot.

        Args:
            topic: le sujet principal
            doc_type: type de document
            custom_sections: titres de sections personnalisés
            style: configuration de style

        Returns:
            PageState avec tout le contenu généré
        """
        # 1. Générer le squelette
        page = self.generate_outline(topic, doc_type, custom_sections)

        if style:
            page.style = style

        # 2. Construire ψ_skeleton (onde contraignante)
        psi_skeleton = self._build_skeleton_wave(page)

        # 3. Tisser chaque section avec propagation et déduplication
        psi_prev = None
        used_facts = set()  # Déduplication des faits entre sections
        for section in page.sections:
            # Propager l'onde
            psi_section = self.propagator.propagate(
                psi_prev, section.title, psi_skeleton
            )
            section.psi = psi_section

            # Tisser le contenu avec déduplication
            self.weaver.weave(section, page, used_facts=used_facts)
            psi_prev = psi_section

        # 4. Mettre à jour l'onde cumulée de la page
        page.psi_page = psi_skeleton
        page.updated_at = time.time()
        page.turn_count += 1

        self._current_page = page
        return page

    def _build_skeleton_wave(self, page: PageState, dim: int = 512) -> np.ndarray:
        """
        Construit l'onde de squelette ψ_skeleton.
        Chaque section contribue avec une phase distincte basée sur sa position.
        """
        psi = np.zeros(dim, dtype=np.complex128)

        for section in page.sections:
            # Encoder le type de section comme une phase
            angle = section.position_angle
            contribution = np.exp(1j * angle) * np.ones(dim, dtype=np.complex128)
            contribution *= (1.0 + 0.1 * hash(section.id) % 100 / 100.0)

            psi += contribution

        return psi / (np.linalg.norm(psi) + 1e-10)

    def get_current_page(self) -> Optional[PageState]:
        """Retourne la page en cours d'édition."""
        return self._current_page

    def to_markdown(self, page: Optional[PageState] = None) -> str:
        """Export Markdown de la page courante."""
        p = page or self._current_page
        if not p:
            return "*Aucune page en cours.*"
        return self.exporter.to_markdown(p)

    def to_html(self, page: Optional[PageState] = None) -> str:
        """Export HTML de la page courante."""
        p = page or self._current_page
        if not p:
            return "<p>Aucune page en cours.</p>"
        return self.exporter.to_html(p)

    def start_conversation(self):
        """
        Démarre le mode conversationnel interactif.
        """
        from page_forge_demo import conversation_loop
        conversation_loop(self)


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def quick_page(topic: str, doc_type: str = 'article') -> str:
    """
    Génère rapidement une page et retourne le Markdown.
    Fonction utilitaire pour usage rapide.

    Usage:
        md = quick_page("La photosynthèse")
        print(md)
    """
    forge = PageForge()
    page = forge.generate(topic, doc_type)
    return forge.to_markdown(page)


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═" * 60)
    print("  📄 PAGEFORGE — Test rapide")
    print("═" * 60)

    forge = PageForge()

    # Test 1 : Générer un squelette
    print("\n1️⃣  Génération du squelette...")
    page = forge.generate_outline("La photosynthèse", doc_type='article')
    print(f"   Topic : {page.topic}")
    print(f"   Type : {page.doc_type}")
    print(f"   Sections :")
    for s in page.sections:
        print(f"     - [{s.id}] {s.title} (angle: {s.position_angle:.2f} rad)")

    # Test 2 : Générer la page complète
    print("\n2️⃣  Génération de la page complète...")
    t0 = time.time()
    page = forge.generate("La photosynthèse", doc_type='article')
    elapsed = time.time() - t0
    print(f"   ⏱️  Temps : {elapsed:.2f}s")
    print(f"   📊 Mots totaux : {page.total_words()}")

    # Test 3 : Export Markdown
    print("\n3️⃣  Export Markdown :")
    md = forge.to_markdown(page)
    print(md[:500] + ('...' if len(md) > 500 else ''))

    # Test 4 : Export HTML
    print("\n4️⃣  Export HTML (aperçu) :")
    html = forge.to_html(page)
    print(html[:300] + '...')

    print("\n✅ Tests terminés.")
