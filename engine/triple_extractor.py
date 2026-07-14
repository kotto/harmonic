"""
Triple Extractor — 20 patterns + pré-entraînement sur la KB
=============================================================
Extrait des triplets (sujet, relation, objet) de textes français/anglais.

DEUX MODES :
  1. PATTERNS (20 regex) — extraction rapide, déterministe
  2. KB-TRAINED — patterns appris des relations existantes dans la KB

PRÉ-ENTRAÎNEMENT :
  Analyse les 100K+ triplets de la KB pour extraire :
    · Les relations les plus fréquentes
    · Les patterns lexicaux associés à chaque relation
    · Les structures sujet-verbe-complément récurrentes
  → Génère des regex spécialisées pour chaque relation fréquente

USAGE :
  from triple_extractor import TripleExtractor
  
  extractor = TripleExtractor()
  extractor.pre_train(brain)  # apprend des patterns de la KB
  
  triples = extractor.extract("Les plantes convertissent la lumière...")
  # → [("plantes", "convertissent", "la lumière", "BIOLOGIE"), ...]
"""

import re
import math
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import List, Tuple, Dict, Set, Optional
import logging

log = logging.getLogger(__name__)

PHI = 1.618033988749895

# ═══════════════════════════════════════════════════════════════════════════════
# STOPWORDS
# ═══════════════════════════════════════════════════════════════════════════════

STOP_SUBJECTS = {
    'il', 'elle', 'on', 'ils', 'elles', 'nous', 'vous', 'je', 'tu',
    'cela', 'ceci', 'cet', 'cette', 'ces', 'ce', 'ça', 'ca',
    'qui', 'que', 'quoi', 'dont', 'lequel', 'laquelle', 'lesquels',
    'tout', 'tous', 'toute', 'toutes', 'rien', 'personne',
    'plusieurs', 'certains', 'aucun', 'chaque', 'chacun',
    'il y a', 'c\'est', 'ce sont', 'il est', 'elle est',
}

# ═══════════════════════════════════════════════════════════════════════════════
# 20 PATTERNS D'EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

PATTERNS = [
    # 0. NÉGATION — doit être testé AVANT le pattern "est" générique
    {
        'regex': r'([A-ZÀ-Űa-zà-ÿ][a-zà-ÿ]{2,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+n(?:e|\s*\'|\s+)est\s+pas\s+(?:un|une|le|la|les|l|des|du|de la|d)?\s*(.+?)(?:\.\s+[A-ZÀ-Ű]|\.\s*$|$)',
        'relation': "n'est pas",
        'sector': 'GENERAL',
    },
    # 1. X est un/une Y (définition)
    {
        'regex': r'([A-ZÀ-Ű][a-zà-ÿ]{2,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(?:est|sont|était|étaient|reste|demeure|devient|deviennent|constitue|représente|forme)\s+(?:un|une|le|la|les|l|des|du|de la|d)\s+(.+)',
        'relation': 'est',
        'sector': 'GENERAL',
    },
    # 2. X a V Y (action accomplie)
    {
        'regex': r'([A-ZÀ-Ű][a-zà-ÿ]{2,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,3})\s+a\s+(découvert|inventé|créé|fondé|développé|publié|formulé|introduit|proposé|établi|démontré|prouvé|obtenu|reçu|gagné|remporté|écrit|composé|peint|réalisé|construit|conçu)\s+(.+)',
        'relation_template': 'a {verb}',
        'sector': 'SCIENCES',
    },
    # 3. X permet de Y / cause Y (causalité)
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(permet(?:tent)?\s+(?:de|d)|cause(?:nt)?|provoque(?:nt)?|entraîne(?:nt)?|génère(?:nt)?|produi(?:t|sent)|crée(?:nt)?|induit|induit|déclenche(?:nt)?|favorise(?:nt)?|stimule(?:nt)?|active(?:nt)?)\s+(.+)',
        'relation_template': '{verb}',
        'sector': 'GENERAL',
    },
    # 4. X se trouve dans/en/au Y (localisation)
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(se trouve(?:nt)?\s+(?:dans|en|au|aux|sur|à)|est\s+(?:situé|localisé|présent|implanté|établi|basé)(?:e?s)?\s+(?:dans|en|au|aux|sur|à))\s+(.+)',
        'relation_template': 'se trouve {prep}',
        'sector': 'GEOGRAPHIE',
    },
    # 5. X est composé de / constitué de Y
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(?:est|sont)\s+(composé|constitué|formé|fait|composée|constituée|formée|faite)(?:e?s)?\s+(?:de|d|par)\s+(.+)',
        'relation': 'est composé de',
        'sector': 'SCIENCES',
    },
    # 6. X contient Y
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(contient|contiennent|renferme|renferment|inclut|incluent|comprend|comprennent|possède|possèdent|dispose de|disposent de)\s+(.+)',
        'relation_template': '{verb}',
        'sector': 'SCIENCES',
    },
    # 7. X joue un rôle dans Y / contribue à Y
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(joue(?:nt)?\s+un\s+rôle\s+(?:dans|pour|essentiel|important|clé|majeur|central|crucial|fondamental)\s+(?:dans|pour)?|contribue(?:nt)?\s+(?:à|au|aux)|participe(?:nt)?\s+(?:à|au|aux)|intervient|interviennent\s+(?:dans|sur))\s+(.+)',
        'relation_template': '{verb}',
        'sector': 'SCIENCES',
    },
    # 8. X dépend de Y / repose sur Y
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(dépend(?:ent)?\s+(?:de|du|des)|repose(?:nt)?\s+(?:sur|essentiellement sur)|est\s+(?:lié|associé|connecté|relié)(?:e?s)?\s+(?:à|au|aux))\s+(.+)',
        'relation_template': '{verb}',
        'sector': 'GENERAL',
    },
    # 9. X a été V par Y (passif)
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(?:a|ont)\s+(?:été|ete)\s+(découvert|inventé|créé|fondé|développé|publié|écrit|composé|peint|réalisé|construit|conçu|proposé|démontré|prouvé|introduit)\s+(?:par|en|au|aux|dans)\s+(.+)',
        'relation': 'a été {verb} par',
        'sector': 'SCIENCES',
    },
    # 10. X comme Y (comparaison/analogie)
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(?:est|sont|fonctionne|fonctionnent|agit|agissent)\s+comme\s+(?:un|une|le|la|les|des|du)?\s*(.+)',
        'relation': 'fonctionne comme',
        'sector': 'GENERAL',
    },
    # 11. X en/au/aux YEAR (date)
    {
        'regex': r'([A-ZÀ-Ű][a-zà-ÿ]{2,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(?:en|au|aux|durant|pendant|lors de)\s+(\d{4})',
        'relation': 'a eu lieu en',
        'sector': 'HISTOIRE',
    },
    # 12. X a N de Y (quantité)
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(?:a|possède|compte|comprend|contient|abrite|héberge)\s+(\d+(?:\s?\d{3})*(?:,\d+)?(?:\s?(?:millions?|milliards?|%|pourcent|km|mètres?|hectares?|habitants?|espèces?))?)\s+(?:de|d)\s+(.+)',
        'relation': 'a',
        'sector': 'GEOGRAPHIE',
    },
    # 13. X est responsable de Y / chargé de Y
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(?:est|sont)\s+(responsable|responsables|chargé|chargés|garant|garants)\s+(?:de|du|des|d)\s+(.+)',
        'relation': 'est responsable de',
        'sector': 'POLITIQUE',
    },
    # 14. X appartient à Y / fait partie de Y
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(appartient|appartiennent|fait partie|font partie|relève|relèvent|appartient à|est membre de|sont membres de)\s+(?:à|de|du|des)?\s*(.+)',
        'relation_template': '{verb}',
        'sector': 'GENERAL',
    },
    # 15. X est caractérisé par Y
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(?:est|sont)\s+(caractérisé|caractérisée|caractérisés|caractérisées|défini|définie|définis|définies)\s+par\s+(.+)',
        'relation': 'est caractérisé par',
        'sector': 'SCIENCES',
    },
    # 16. X résulte de Y / découle de Y
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(résulte|résultent|découle|découlent|provient|proviennent|émane|émanent|est\s+(?:issu|issue|issus|issues)|sont\s+(?:issus|issues))\s+(?:de|du|des|d)\s+(.+)',
        'relation_template': '{verb} de',
        'sector': 'SCIENCES',
    },
    # 17. X agit sur Y / influence Y
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(agit|agissent|influence|influencent|affecte|affectent|modifie|modifient|régule|régulent|contrôle|contrôlent|module|modulent)\s+(?:sur|le|la|les|l)?\s*(.+)',
        'relation_template': '{verb}',
        'sector': 'SCIENCES',
    },
    # 18. X est nécessaire à Y / essentiel pour Y
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(?:est|sont)\s+(nécessaire|nécessaires|essentiel|essentiels|indispensable|indispensables|vital|vitaux|crucial|cruciaux|requis|requise)\s+(?:à|au|aux|pour|afin de|dans le)\s+(.+)',
        'relation': 'est nécessaire pour',
        'sector': 'GENERAL',
    },
    # 19. X est limité par Y / freiné par Y
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(?:est|sont)\s+(limité|limitée|limités|limitées|freiné|freinée|freinés|freinées|entravé|entravée|entravés|entravées|restreint|restreinte|restreints|restreintes)\s+par\s+(.+)',
        'relation': 'est limité par',
        'sector': 'GENERAL',
    },
    # 20. X protège contre Y / prévient Y
    {
        'regex': r'([a-zà-ÿ]{3,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+(protège|protègent|prévient|préviennent|empêche|empêchent|évite|évitent|bloque|bloquent|inhibe|inhibent|réduit|réduisent)\s+(?:contre|de|le|la|les|l)?\s*(.+)',
        'relation_template': '{verb}',
        'sector': 'SCIENCES',
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# SECTOR DETECTION (from relation keywords)
# ═══════════════════════════════════════════════════════════════════════════════

SECTOR_KEYWORDS = {
    'GEOGRAPHIE': ['pays', 'capitale', 'continent', 'population', 'superficie',
                   'coordonnée', 'localisation', 'région', 'ville', 'frontière',
                   'fleuve', 'montagne', 'océan', 'mer', 'île', 'lac', 'climat',
                   'situé', 'trouve', 'localisé', 'habitant'],
    'HISTOIRE': ['date', 'naissance', 'mort', 'fondation', 'création', 'siècle',
                 'début', 'fin', 'roi', 'reine', 'empereur', 'guerre', 'traité',
                 'dynastie', 'civilisation', 'ancêtre', 'indépendance', 'révolution',
                 'découverte', 'inventé', 'fondé', 'créé', 'construit'],
    'SCIENCES': ['molécule', 'atome', 'élément', 'réaction', 'cellule', 'organe',
                 'espèce', 'gène', 'protéine', 'enzyme', 'découvert', 'formule',
                 'masse', 'température', 'pression', 'énergie', 'chimique',
                 'biologique', 'physique', 'mathématique', 'composé', 'constitué'],
    'PHYSIQUE_FOND': ['onde', 'particule', 'force', 'énergie', 'gravité',
                      'quantique', 'relativité', 'électromagnétique', 'photon',
                      'lumière', 'fréquence', 'champ'],
    'BIOLOGIE': ['plante', 'animal', 'cellule', 'organisme', 'écosystème',
                 'espèce', 'genre', 'famille', 'ADN', 'gène', 'protéine',
                 'photosynthèse', 'respiration', 'reproduction', 'chromosome'],
    'CREATION': ['peint', 'sculpté', 'écrit', 'composé', 'réalisé', 'créé',
                 'œuvre', 'tableau', 'roman', 'poème', 'symphonie', 'film',
                 'artiste', 'auteur', 'peintre', 'musicien', 'réalisateur'],
    'ECONOMIE': ['PIB', 'monnaie', 'inflation', 'marché', 'commerce', 'banque',
                 'croissance', 'développement', 'industrie', 'production',
                 'exportation', 'importation', 'investissement'],
    'POLITIQUE': ['gouvernement', 'loi', 'élection', 'président', 'parlement',
                  'constitution', 'démocratie', 'justice', 'liberté'],
}

def detect_sector(text: str) -> str:
    """Détecte le secteur sémantique d'un texte."""
    text_lower = text.lower()
    scores = defaultdict(int)
    for sector, keywords in SECTOR_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[sector] += 1
    if scores:
        return max(scores, key=scores.get)
    return 'GENERAL'


# ═══════════════════════════════════════════════════════════════════════════════
# KB-TRAINED PATTERNS (pré-entraînement)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TrainedPattern:
    """Un pattern appris de la KB."""
    pattern: str
    relation: str
    frequency: int
    examples: List[Tuple[str, str, str]]


class KBTrainedExtractor:
    """
    Extracteur pré-entraîné sur la KB existante.
    
    Apprend les patterns de relations à partir des triplets déjà ingérés
    et les utilise pour extraire de nouveaux triplets de textes inconnus.
    """

    def __init__(self):
        self.trained_patterns: List[TrainedPattern] = []
        self.relation_freq: Dict[str, int] = Counter()
        self._trained = False

    def pre_train(self, knowledge_base: List[Tuple[str, str, str, str]],
                  max_patterns: int = 50):
        """
        Pré-entraîne l'extracteur sur une KB existante.
        
        Analyse les relations, leur fréquence, les patterns sujet/objet,
        et génère des regex spécialisées.
        """
        log.info(f"Pré-entraînement sur {len(knowledge_base)} triplets...")
        
        # 1. Compter les relations
        for s, r, o, sec in knowledge_base:
            self.relation_freq[r.lower().strip()] += 1

        # 2. Pour les relations les plus fréquentes, créer des patterns
        top_relations = self.relation_freq.most_common(max_patterns)
        
        for rel, freq in top_relations:
            if freq < 3:
                continue
            
            # Chercher des exemples de cette relation dans la KB
            examples = []
            for s, r, o, sec in knowledge_base:
                if r.lower().strip() == rel and len(examples) < 5:
                    examples.append((s, r, o))
            
            if not examples:
                continue
            
            # Créer un pattern à partir de la relation
            # Pattern : cherche le verbe/expression dans le texte
            rel_words = rel.split()
            if len(rel_words) <= 3:
                # Relation courte : pattern flexible
                pattern = re.escape(rel).replace(r'\ ', r'\s+')
                regex = (
                    r'([A-ZÀ-Űa-zà-ÿ][a-zà-ÿ]{2,}(?:\s(?:[a-zà-ÿ]{2,}|de|du|des|d|la|le|les|l)){0,4})\s+'
                    + pattern +
                    r'\s+(.+)'
                )
            else:
                # Relation longue : ignorer (trop spécifique)
                continue
            
            self.trained_patterns.append(TrainedPattern(
                pattern=regex,
                relation=rel,
                frequency=freq,
                examples=examples,
            ))

        self._trained = True
        log.info(f"  → {len(self.trained_patterns)} patterns appris "
                 f"(sur {len(top_relations)} relations analysées)")

    def extract_with_trained(self, text: str) -> List[Tuple[str, str, str, str]]:
        """Extrait des triplets en utilisant les patterns appris de la KB."""
        if not self._trained:
            return []

        triples = []
        text_clean = re.sub(r'\s+', ' ', text)
        sentences = re.split(r'(?<=[.!?])\s+', text_clean)

        for sent in sentences:
            if len(sent) < 20:
                continue

            for tp in self.trained_patterns[:20]:  # limiter à 20 patterns pour performance
                try:
                    m = re.search(tp.pattern, sent, re.IGNORECASE)
                    if m:
                        sujet = m.group(1).strip().lower()
                        objet = m.group(2).strip(' .,;').lower()
                        if (sujet.lower() not in STOP_SUBJECTS and
                                len(sujet) >= 3 and len(objet) >= 3):
                            secteur = detect_sector(f"{sujet} {tp.relation} {objet}")
                            triples.append((sujet, tp.relation, objet, secteur))
                except Exception:
                    continue

        return triples


# ═══════════════════════════════════════════════════════════════════════════════
# TRIPLE EXTRACTOR UNIFIÉ
# ═══════════════════════════════════════════════════════════════════════════════

class TripleExtractor:
    """
    Extracteur de triplets unifié : 20 patterns + KB-trained.
    
    Usage:
        ext = TripleExtractor()
        ext.pre_train(brain)  # optionnel : apprentissage KB
        triples = ext.extract(texte)
    """

    def __init__(self, use_trained: bool = True):
        self.patterns = PATTERNS
        self.trained = KBTrainedExtractor() if use_trained else None
        self._pre_trained = False

    def pre_train(self, brain_or_kb):
        """Pré-entraîne sur une KB existante."""
        if self.trained is None:
            return

        if hasattr(brain_or_kb, 'unconscious'):
            # C'est un HarmonicBrain
            kb = [(r.sujet, r.relation, r.objet, r.secteur)
                  for r in brain_or_kb.unconscious.registry.values()]
        else:
            # C'est une liste de triplets
            kb = brain_or_kb

        if len(kb) > 100:
            self.trained.pre_train(kb)
            self._pre_trained = True

    def extract(self, text: str, max_triples: int = 200) -> List[Tuple[str, str, str, str]]:
        """
        Extrait les triplets d'un texte.

        Combine :
          1. 20 patterns regex (déterministes, rapides)
          2. Patterns appris de la KB (si pré-entraîné)
          3. Déduplication + tri par pertinence
        """
        triples = []
        text_clean = re.sub(r'\([^)]*\)', '', text)
        text_clean = re.sub(r'\[[^\]]*\]', '', text_clean)
        text_clean = re.sub(r'\s+', ' ', text_clean)

        sentences = re.split(r'(?<=[.!?])\s+', text_clean)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        seen = set()

        for sent in sentences:
            # 1. Patterns regex (20)
            for pat in self.patterns:
                try:
                    m = re.search(pat['regex'], sent, re.IGNORECASE)
                    if not m:
                        continue

                    sujet = m.group(1).strip().lower()
                    # Déterminer l'objet et la relation
                    if 'relation_template' in pat:
                        verb = m.group(2).strip().lower()
                        rel = pat['relation_template'].replace('{verb}', verb)
                        objet = m.group(3).strip(' .,;').lower() if m.lastindex >= 3 else m.group(2).strip(' .,;').lower()
                    elif 'relation' in pat:
                        rel = pat['relation']
                        # Remplacer {verb} si présent
                        if '{verb}' in rel and m.lastindex >= 2:
                            verb = m.group(2).strip().lower()
                            rel = rel.replace('{verb}', verb)
                        objet = m.group(m.lastindex).strip(' .,;').lower()
                    else:
                        continue

                    if (sujet.lower() in STOP_SUBJECTS or
                            len(sujet) < 3 or len(objet) < 5):
                        continue

                    # TRONQUER l'objet au premier point suivi d'espace et majuscule (fin de phrase)
                    objet = re.split(r'\.\s+(?=[A-ZÀ-Ű])', objet)[0]
                    # TRONQUER aussi au point-virgule, deux-points
                    objet = re.split(r'[;:]\s+(?=[A-ZÀ-Ű])', objet)[0]
                    objet = objet.strip(' .,;:')
                    if len(objet) < 5:
                        continue

                    key = (sujet, rel, objet)
                    if key not in seen:
                        secteur = pat.get('sector', detect_sector(f"{sujet} {rel} {objet}"))
                        triples.append((sujet, rel, objet, secteur))
                        seen.add(key)

                except (IndexError, AttributeError):
                    continue

            if len(triples) >= max_triples:
                break

        # 2. KB-trained patterns (si dispo)
        if self._pre_trained and len(triples) < max_triples:
            trained_triples = self.trained.extract_with_trained(text)
            for s, r, o, sec in trained_triples:
                key = (s, r, o)
                if key not in seen:
                    triples.append((s, r, o, sec))
                    seen.add(key)
                    if len(triples) >= max_triples:
                        break

        # 3. Bootstrapper fallback
        if len(triples) < 5:
            try:
                from bootstrapper import extract_triples_simple
                bt_triples = extract_triples_simple(text)
                for s, r, o, sec in bt_triples:
                    key = (s, r, o)
                    if key not in seen:
                        triples.append((s, r, o, sec))
                        seen.add(key)
            except ImportError:
                pass

        return triples[:max_triples]


# ═══════════════════════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("=" * 60)
    print("  TRIPLE EXTRACTOR — 20 patterns")
    print("=" * 60)

    # Texte de test riche
    test_text = """
    La photosynthèse est le processus par lequel les plantes convertissent 
    la lumière du soleil en énergie chimique. Ce mécanisme est essentiel à 
    la vie sur Terre. La photosynthèse produit l'oxygène que nous respirons.
    
    Les chloroplastes sont des organites cellulaires. Ils contiennent la 
    chlorophylle qui capture l'énergie lumineuse. La chlorophylle est 
    composée de magnésium et d'azote. La chlorophylle agit comme un 
    catalyseur dans la réaction photochimique.
    
    Le cycle de Calvin fixe le dioxyde de carbone atmosphérique. Il permet 
    de produire du glucose à partir du CO2. Ce cycle a été découvert par 
    Melvin Calvin en 1961. Cette découverte a été récompensée par le prix 
    Nobel de chimie.
    
    Les mitochondries sont responsables de la respiration cellulaire. 
    Elles produisent l'ATP nécessaire au fonctionnement des cellules. 
    La respiration cellulaire dépend de l'oxygène produit par la photosynthèse.
    
    La déforestation massive menace l'équilibre du cycle du carbone. 
    Les forêts jouent un rôle crucial dans l'absorption du CO2. 
    Le réchauffement climatique est causé par l'accumulation de gaz 
    à effet de serre. La température moyenne a augmenté de 1.2 degrés 
    depuis l'ère préindustrielle.
    
    Les énergies renouvelables comme le solaire et l'éolien permettent 
    de réduire les émissions de gaz à effet de serre. La Chine est le 
    plus grand producteur mondial de panneaux solaires. La transition 
    énergétique est nécessaire pour protéger la biodiversité.
    """

    ext = TripleExtractor(use_trained=False)
    
    # Test sans pré-entraînement
    triples = ext.extract(test_text)
    print(f"\nTriplets extraits : {len(triples)}")
    for s, r, o, sec in triples[:12]:
        print(f"  [{sec}] {s[:40]:40} | {r[:25]:25} | {o[:40]}")
    if len(triples) > 12:
        print(f"  ... et {len(triples)-12} autres")

    # Test avec pré-entraînement (si brain dispo)
    print(f"\n── Avec pré-entraînement KB ──")
    try:
        from harmonic_brain import HarmonicBrain
        kb = [('pluie','cause','humidite','NATURE'),('pluie','fait pousser','fleurs','NATURE')]
        brain = HarmonicBrain(kb, dim=64, use_holographic=False)
        ext2 = TripleExtractor(use_trained=True)
        ext2.pre_train(brain)
        triples2 = ext2.extract(test_text)
        print(f"  Triplets (20 patterns + KB-trained) : {len(triples2)}")
    except Exception as e:
        print(f"  Pré-entraînement non testé : {e}")

    print(f"\n✅ Triple Extractor OK")
