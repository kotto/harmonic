"""
Creative Dialogue — Interaction Conscient ↔ Inconscient
=========================================================
Architecture de créativité inspirée du cerveau humain.

Ce n'est PAS un pipeline (inconscient → conscient → réponse).
C'est un DIALOGUE entre deux systèmes :

    CONSCIENT                      INCONSCIENT
    ─────────                      ───────────
    "Trouve des faits              →  KB retrieval
     sur le Japon"                 ←  [tokyo, sushi, anime...]
    
    "Trop évident.                 →  Cross-domain search
     Cherche ailleurs"             ←  [haiku (poésie), tsunami (physique)]
    
    "Intéressant.                  →  Deep dive sur 'haiku'
     Explore le haiku"             ←  [17 syllabes, Basho, zen...]
    
    "Connexion trouvée:            →  Compose la réponse créative
     le Japon et la France         ←  [japonisme, Monet, Van Gogh...]
     partagent l'esthétique"

PRINCIPE : La créativité émerge de l'INTERACTION, pas de la retrieval.

Usage:
    from creative_dialogue import CreativeDialogue
    dialogue = CreativeDialogue(kb, retriever)
    result = dialogue.create("trouve une connexion entre le Japon et la France")
"""

import re
import random
import math
from typing import List, Tuple, Optional, Dict, Set

Fact = Tuple[str, str, str, str]


class CreativeDialogue:
    """
    Dialogue créatif entre le conscient et l'inconscient.
    
    Le conscient POSE des intentions, ÉVALUE les réponses,
    et GUIDE l'exploration créative.
    
    L'inconscient RETROUVE des faits, suit des CHAÎNES
    associatives, et propose des CONNEXIONS inattendues.
    """
    
    STOPWORDS = {
        'the','a','an','is','are','was','were','of','in','on','at','to',
        'for','with','by','from','and','or','le','la','les','un','une',
        'des','de','du','est','dans','sur','pour','par','avec','qui',
        'quoi','ou','quand','comment','pourquoi','et','il','elle',
    }
    
    def __init__(self, knowledge_base: List[Fact], retriever=None):
        self.kb = knowledge_base
        self.retriever = retriever
        
        # Index inversé pour l'inconscient
        if retriever is None:
            try:
                from inverted_index import InvertedIndex
                self.retriever = InvertedIndex(knowledge_base)
            except ImportError:
                self.retriever = None
        
        # Mémoire de travail (ce que le conscient a "en tête")
        self.working_memory: List[Tuple[str, float]] = []  # (concept, pertinence)
        
        # Historique du dialogue
        self.dialogue_log: List[str] = []
        
        # Paramètres de créativité
        self.creativity_level = 0.5  # 0 = factuel pur, 1 = surréaliste
        self.max_iterations = 5
    
    # ═══════════════════════════════════════════════════════════════
    # CONSCIENT — Intention et Évaluation
    # ═══════════════════════════════════════════════════════════════
    
    def _extract_intention(self, question: str) -> Dict:
        """
        Le conscient analyse la question et formule une INTENTION.
        
        Types d'intention :
        - 'factual' : répondre avec des faits
        - 'creative' : trouver une connexion inattendue
        - 'explanatory' : expliquer un mécanisme
        - 'comparative' : comparer deux choses
        - 'why' : trouver la cause
        """
        q_lower = question.lower()
        
        intention = {
            'type': 'factual',
            'targets': [],
            'depth': 1,
            'creativity': 0.3,  # bas par défaut
        }
        
        # Détecter l'intention créative
        creative_markers = [
            'connexion', 'connection', 'metaphore', 'metaphor',
            'de maniere creative', 'de façon créative', 'creatively',
            'surprenant', 'surprising', 'inattendu', 'unexpected',
            'poeme', 'poem', 'haiku', 'histoire', 'story',
            'imagine', 'invente', 'cree',
        ]
        if any(m in q_lower for m in creative_markers):
            intention['type'] = 'creative'
            intention['creativity'] = 0.8
            intention['depth'] = 3
        
        # Détecter l'intention comparative
        if any(w in q_lower for w in ['difference', 'différence', 'compare',
                                        'versus', 'vs', 'ou', 'or']):
            intention['type'] = 'comparative'
            intention['depth'] = 2
        
        # Détecter l'intention explicative
        if any(w in q_lower for w in ['pourquoi', 'why', 'comment', 'how',
                                        'explique', 'explain']):
            intention['type'] = 'explanatory'
            intention['depth'] = 2
        
        # Extraire les cibles (concepts clés)
        targets = self._extract_targets(question)
        intention['targets'] = targets
        
        return intention
    
    def _extract_targets(self, question: str) -> List[str]:
        """Extrait les concepts-clés de la question."""
        q = question.lower()
        # Retirer les préfixes de question
        for p in ['what is the ', 'what is ', 'who ', 'when ', 'where ',
                  'why ', 'how ', 'explain ', 'qu est ce que ', 'qui ',
                  'quand ', 'ou ', 'pourquoi ', 'comment ']:
            if q.startswith(p):
                q = q[len(p):]
                break
        q = q.strip('?.,!;:')
        
        # Extraire les mots significatifs (≥3 lettres, pas stopwords)
        words = [w for w in q.split() if len(w) >= 3 and w not in self.STOPWORDS]
        return words[:5]  # top 5 concepts
    
    def _evaluate_response(self, intention: Dict, facts: List[Fact],
                           context: List[str] = None) -> float:
        """
        Le conscient ÉVALUE la réponse de l'inconscient.
        
        Critères :
        - Pertinence : les faits répondent-ils à l'intention ?
        - Surprise (créativité) : les faits sont-ils inattendus ?
        - Profondeur : peut-on creuser plus ?
        
        Retourne un score 0-1.
        """
        if not facts:
            return 0.0
        
        targets = set(intention.get('targets', []))
        if context:
            targets.update(context)
        
        scores = []
        for fact in facts:
            s, r, o, sec = fact
            combined = (s + ' ' + r + ' ' + o).lower()
            
            # 1. Pertinence : overlap avec les cibles
            relevance = sum(1 for t in targets if t in combined) / max(len(targets), 1)
            
            # 2. Surprise : le fait vient d'un domaine DIFFÉRENT
            # (plus le domaine est éloigné, plus c'est créatif)
            surprise = 0.0
            if intention.get('creativity', 0.3) > 0.5:
                # Bonus pour les domaines inattendus
                creative_sectors = {'ART', 'MUSIQUE', 'LITTERATURE', 'PHILOSOPHIE',
                                   'SPIRITUALITE', 'EMOTION_POS', 'CULTURE_G'}
                if sec in creative_sectors:
                    surprise = 0.5
            
            # 3. Spécificité : le fait n'est pas trop générique
            specificity = min(1.0, len(combined) / 100)
            
            score = relevance * 0.4 + surprise * 0.3 + specificity * 0.3
            scores.append(score)
        
        return sum(scores) / len(scores)
    
    # ═══════════════════════════════════════════════════════════════
    # INCONSCIENT — Retrieval et Association
    # ═══════════════════════════════════════════════════════════════
    
    def _unconscious_search(self, question: str, intention: Dict,
                            context: List[str] = None, iteration: int = 0) -> List[Fact]:
        """
        L'inconscient cherche des faits selon l'intention.
        
        Plus l'itération avance, plus la recherche s'élargit
        (domaines différents, associations libres).
        """
        if not self.retriever:
            return []
        
        # Itération 0 : recherche directe
        if iteration == 0:
            return self.retriever.search(question, max_results=5)
        
        # Itération 1 : élargir le domaine
        if iteration == 1:
            # Chercher les mêmes concepts dans d'autres secteurs
            targets = intention.get('targets', [])
            if targets:
                # Chercher chaque cible séparément
                all_facts = []
                for t in targets:
                    results = self.retriever.search(t, max_results=3)
                    all_facts.extend(results)
                return self._deduplicate(all_facts)[:5]
            return []
        
        # Itération 2+ : associations libres
        if iteration >= 2:
            if not context:
                return []
            
            # Suivre la chaîne associative : pour chaque concept du contexte,
            # chercher des faits où ce concept apparaît
            all_facts = []
            for ctx_word in context[-3:]:  # 3 derniers concepts
                if len(ctx_word) < 3:
                    continue
                results = self.retriever.search(ctx_word, max_results=3)
                all_facts.extend(results)
            
            # Filtrer : garder les faits les plus INATTENDUS
            # (ceux qui ne sont pas directement liés à la question originale)
            targets = set(intention.get('targets', []))
            creative = []
            for fact in self._deduplicate(all_facts):
                s, r, o, sec = fact
                combined = (s + ' ' + r + ' ' + o).lower()
                overlap = sum(1 for t in targets if t in combined)
                if overlap <= 1:  # peu de recouvrement = surprise
                    creative.append(fact)
            
            return creative[:5]
    
    def _deduplicate(self, facts: List[Fact]) -> List[Fact]:
        """Déduplique les faits par sujet."""
        seen = set()
        result = []
        for f in facts:
            if f[0] not in seen:
                result.append(f)
                seen.add(f[0])
        return result
    
    # ═══════════════════════════════════════════════════════════════
    # DIALOGUE — La boucle interactive
    # ═══════════════════════════════════════════════════════════════
    
    def create(self, question: str, lang: str = 'fr',
               max_iterations: int = 5) -> Tuple[List[Fact], Dict, List[str]]:
        """
        Boucle de dialogue créatif entre conscient et inconscient.
        
        Retourne :
        - faits_finaux : les meilleurs faits trouvés
        - dialogue_log : l'historique du dialogue
        - creative_score : score de créativité final
        """
        self.dialogue_log = []
        self.working_memory = []
        
        # Phase 0 : Le conscient analyse l'intention
        intention = self._extract_intention(question)
        self.dialogue_log.append(f"[CONSCIENT] Intention: {intention['type']}, "
                                 f"cibles: {intention['targets']}")
        
        best_facts = []
        best_score = 0.0
        context = intention['targets'][:]
        creativity_threshold = intention.get('creativity', 0.3)
        
        for iteration in range(max_iterations):
            # L'inconscient cherche
            facts = self._unconscious_search(
                question, intention, context, iteration
            )
            
            if not facts:
                self.dialogue_log.append(
                    f"[INCONSCIENT] Itération {iteration}: rien trouvé"
                )
                break
            
            # Le conscient évalue
            score = self._evaluate_response(intention, facts, context)
            
            self.dialogue_log.append(
                f"[CONSCIENT] Itération {iteration}: score={score:.2f}, "
                f"faits={len(facts)}, top={facts[0][0][:30] if facts else '?'}"
            )
            
            if score > best_score:
                best_score = score
                best_facts = facts[:]
            
            # Si assez bon ou créativité atteinte → stop
            if score > 0.7 or (score > 0.4 and iteration >= 2):
                self.dialogue_log.append(
                    f"[CONSCIENT] Satisfait (score={score:.2f}), arrêt"
                )
                break
            
            # Sinon, le conscient donne un feedback à l'inconscient
            # et élargit le contexte pour l'itération suivante
            if iteration == 0 and score < 0.4:
                self.dialogue_log.append(
                    f"[CONSCIENT] Score faible, élargissement du contexte"
                )
                # Ajouter des mots du premier fait au contexte
                if facts:
                    s, r, o, _ = facts[0]
                    new_words = [w for w in (s+' '+r+' '+o).lower().split()
                                if len(w) >= 3 and w not in intention['targets']]
                    context.extend(new_words[:2])
            
            elif iteration == 1 and score < 0.5 and creativity_threshold > 0.5:
                self.dialogue_log.append(
                    f"[CONSCIENT] Cherche connexions créatives"
                )
                # Activer le mode créatif : chercher dans d'autres domaines
                creativity_threshold = 0.8
        
        # Résultat final
        self.dialogue_log.append(
            f"[CONSCIENT] Réponse finale: {len(best_facts)} faits, "
            f"score créatif={best_score:.2f}"
        )
        
        return best_facts, intention, best_score
    
    # ═══════════════════════════════════════════════════════════════
    # COMPOSITION CRÉATIVE
    # ═══════════════════════════════════════════════════════════════
    
    def compose_creative(self, question: str, facts: List[Fact],
                         intention: Dict, lang: str = 'fr') -> str:
        """
        Compose une réponse créative à partir du dialogue.
        
        Selon le type d'intention :
        - factual : réponse directe
        - creative : réponse avec connexion inattendue
        - comparative : mise en contraste
        """
        if not facts:
            if lang == 'en':
                return "I couldn't find a creative connection for that question."
            return "Je n'ai pas trouvé de connexion créative pour cette question."
        
        intention_type = intention.get('type', 'factual')
        s0, r0, o0, sec0 = facts[0]
        s0_cap = s0[0].upper() + s0[1:] if s0 else s0
        
        if intention_type == 'factual':
            if lang == 'en':
                return f"{s0_cap} {r0} {o0}."
            return f"{s0_cap} {r0} {o0}."
        
        if intention_type == 'creative':
            # Réponse créative : connexion inattendue
            if len(facts) >= 2:
                s1, r1, o1, sec1 = facts[1]
                if lang == 'en':
                    return (f"{s0_cap} reminds us that {r0} {o0}. "
                            f"Surprisingly, this connects to {s1}: {r1} {o1}.")
                return (f"{s0_cap} nous rappelle que {r0} {o0}. "
                        f"De façon inattendue, cela rejoint {s1} : {r1} {o1}.")
            return f"{s0_cap} {r0} {o0}."
        
        if intention_type == 'comparative':
            if len(facts) >= 2:
                s1, r1, o1, sec1 = facts[1]
                if lang == 'en':
                    return (f"On one hand, {s0_cap} {r0} {o0}. "
                            f"On the other hand, {s1} {r1} {o1}.")
                return (f"D'un côté, {s0_cap} {r0} {o0}. "
                        f"De l'autre, {s1} {r1} {o1}.")
        
        if intention_type == 'explanatory':
            if len(facts) >= 2:
                s1, r1, o1, sec1 = facts[1]
                if lang == 'en':
                    return (f"{s0_cap} {r0} {o0}. "
                            f"This is because {s1} {r1} {o1}.")
                return (f"{s0_cap} {r0} {o0}. "
                        f"C'est parce que {s1} {r1} {o1}.")
        
        return f"{s0_cap} {r0} {o0}."
    
    def get_dialogue_summary(self) -> str:
        """Retourne un résumé lisible du dialogue conscient/inconscient."""
        return '\n'.join(self.dialogue_log[-10:])  # 10 derniers échanges
