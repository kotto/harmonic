"""
Conscious Reasoning Engine — Architecture Conscience/Inconscience
===================================================================
Implémente l'architecture à 3 phases pour l'IA harmonique :

    INCONSCIENT (rapide, automatique) :
        - Retrieval de faits depuis la KB (index inversé)
        - Scoring rapide par TF-IDF
        → ~1ms

    CONSCIENT (vérification, créativité) :
        - Vérification de cohérence des faits trouvés
        - Si confiance basse → exploration d'alternatives
        - Connexions créatives entre domaines
        → ~10ms

    CORRECTION (raffinement) :
        - Si toujours incohérent → reformulation de la question
        - Si toujours pas → réponse "Je ne sais pas" honnête
        - Sinon → composition de réponse enrichie
        → ~5ms

Usage:
    from conscious_engine import ConsciousEngine
    engine = ConsciousEngine(kb, retriever)
    response = engine.process(question)
"""

import re
import random
import math
from typing import List, Tuple, Optional, Dict

Fact = Tuple[str, str, str, str]

# Seuils de confiance (mêmes que conscience_harmonique.py)
CONF_HIGH = 0.70
CONF_MEDIUM = 0.55
CONF_LOW = 0.40


class ConsciousEngine:
    """
    Moteur de raisonnement conscient pour l'IA harmonique.
    
    Phase 1 — INCONSCIENT : retrieval rapide
    Phase 2 — CONSCIENT : vérification + créativité
    Phase 3 — CORRECTION : reformulation ou refus
    """
    
    STOPWORDS = {
        'the','a','an','is','are','was','were','of','in','on','at','to',
        'for','with','by','from','and','or','what','who','when','where',
        'why','how','le','la','les','un','une','des','de','du','est',
        'dans','sur','pour','par','avec','qui','quoi','ou','quand',
        'comment','pourquoi','et','il','elle','ils','elles',
    }
    
    def __init__(self, knowledge_base: List[Fact], retriever=None):
        """
        Args:
            knowledge_base : la KB complète
            retriever : instance de InvertedIndex (ou autre retriever)
        """
        self.kb = knowledge_base
        self.retriever = retriever
        
        # Construire l'index inversé si pas fourni
        if self.retriever is None:
            try:
                from inverted_index import InvertedIndex
                self.retriever = InvertedIndex(knowledge_base)
            except ImportError:
                self.retriever = None
        
        # Cache pour éviter de répéter les mêmes recherches
        self._cache = {}
    
    # ═══════════════════════════════════════════════════════════════
    # PHASE 1 — INCONSCIENT : Retrieval rapide
    # ═══════════════════════════════════════════════════════════════
    
    def _unconscious_retrieve(self, question: str, max_facts: int = 8) -> List[Fact]:
        """
        Retrieval inconscient : rapide, automatique.
        Retourne jusqu'à max_facts candidats.
        """
        # Cache check
        cache_key = question.lower().strip()
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if self.retriever:
            results = self.retriever.search(question, max_results=max_facts)
        else:
            # Fallback : recherche simple par mots-clés
            results = self._simple_search(question, max_facts)
        
        self._cache[cache_key] = results
        return results
    
    def _simple_search(self, question: str, max_facts: int = 8) -> List[Fact]:
        """Recherche simple par mots-clés (fallback)."""
        q_words = set(w for w in question.lower().split()
                      if len(w) >= 3 and w not in self.STOPWORDS)
        
        scored = []
        for fact in self.kb:
            s, r, o, sec = fact
            combined = (s + ' ' + r + ' ' + o).lower()
            overlap = sum(1 for qw in q_words if qw in combined)
            if overlap > 0:
                scored.append((overlap, fact))
        
        scored.sort(key=lambda x: -x[0])
        return [f for _, f in scored[:max_facts]]
    
    # ═══════════════════════════════════════════════════════════════
    # PHASE 2 — CONSCIENT : Vérification + Créativité
    # ═══════════════════════════════════════════════════════════════
    
    def _conscious_verify(self, question: str, facts: List[Fact]) -> Tuple[float, List[Fact]]:
        """
        Vérification consciente de la pertinence des faits.
        
        Retourne (score_confiance, faits_validés).
        """
        if not facts:
            return 0.0, []
        
        q_lower = question.lower()
        q_words = set(w for w in q_lower.split()
                      if len(w) >= 3 and w not in self.STOPWORDS)
        
        # Extraire le sujet de la question
        sujet = self._extract_subject(question)
        
        scored_facts = []
        for fact in facts:
            s, r, o, sec = fact
            s_lower = s.lower()
            o_lower = o.lower()
            r_lower = r.lower()
            combined = s_lower + ' ' + r_lower + ' ' + o_lower
            
            relevance = 0.0
            
            # 1. Le sujet de la question est dans le sujet du fait (best)
            if sujet in s_lower:
                relevance += 0.5
            elif any(sw in s_lower for sw in sujet.split() if len(sw) >= 3):
                relevance += 0.3
            
            # 2. Overlap de mots-clés
            overlap = sum(1 for qw in q_words if qw in combined)
            relevance += overlap * 0.1
            
            # 3. Le fait n'est pas trop long (bruit)
            if len(combined) < 100:
                relevance += 0.1
            elif len(combined) > 200:
                relevance -= 0.1
            
            # 4. Facteur d'amplitude SFT
            from harmonic_quality import get_amplitude
            relevance += get_amplitude(fact) * 0.2
            
            scored_facts.append((relevance, fact))
        
        scored_facts.sort(key=lambda x: -x[0])
        validated = [f for s, f in scored_facts if s > 0.1]
        
        # Calculer la confiance
        if not validated:
            return 0.0, []
        
        top_score = scored_facts[0][0] if scored_facts else 0
        avg_score = sum(s for s, _ in scored_facts[:3]) / min(3, len(scored_facts))
        
        # Confiance = combinaison du meilleur score et du score moyen
        confidence = min(1.0, top_score * 1.5 + avg_score * 0.5)
        
        return confidence, validated
    
    def _creative_explore(self, question: str, facts: List[Fact]) -> List[Fact]:
        """
        Exploration créative : quand la confiance est basse,
        chercher des connexions inattendues entre domaines.
        
        C'est ici que la CRÉATIVITÉ se développe.
        """
        if not facts:
            return []
        
        # 1. Chercher des faits dans d'autres domaines qui partagent des mots
        current_sectors = set(f[3] for f in facts)
        q_words = set(w for w in question.lower().split()
                      if len(w) >= 3 and w not in self.STOPWORDS)
        
        creative_facts = []
        for fact in self.kb:
            s, r, o, sec = fact
            if sec in current_sectors:
                continue  # Déjà dans le même domaine
            
            combined = (s + ' ' + r + ' ' + o).lower()
            overlap = sum(1 for qw in q_words if qw in combined)
            
            if overlap >= 2:  # Au moins 2 mots en commun
                creative_facts.append(fact)
        
        # 2. Limiter à 3 connexions créatives
        creative_facts = creative_facts[:3]
        
        # Marquer comme créatif
        return [(s, r, o, 'CREATIF_' + sec) for s, r, o, sec in creative_facts]
    
    # ═══════════════════════════════════════════════════════════════
    # PHASE 3 — CORRECTION : Reformulation ou Refus
    # ═══════════════════════════════════════════════════════════════
    
    def _correct_refine(self, question: str, confidence: float,
                        facts: List[Fact]) -> Tuple[str, List[Fact]]:
        """
        Correction : selon la confiance, reformuler ou refuser.
        
        Retourne (message_correction, faits_ajustés).
        """
        if confidence >= CONF_HIGH:
            return None, facts  # Tout va bien
        
        if confidence >= CONF_MEDIUM:
            # Reformuler la question pour mieux chercher
            # (retirer les mots vagues, ajouter des synonymes)
            return None, facts  # Pour l'instant, on garde tel quel
        
        if confidence >= CONF_LOW:
            # Confiance basse : élargir la recherche
            # Chercher avec moins de mots-clés
            q_words = [w for w in question.lower().split()
                       if len(w) >= 4 and w not in self.STOPWORDS]
            if len(q_words) >= 2:
                new_question = ' '.join(q_words[:3])
                broader_facts = self._unconscious_retrieve(new_question, max_facts=5)
                if broader_facts:
                    return None, broader_facts[:3]
        
        # Confiance très basse : refus honnête
        return "Je ne suis pas assez confiant pour répondre à cette question. " \
               "Pouvez-vous la reformuler ?", []
    
    # ═══════════════════════════════════════════════════════════════
    # PROCESSUS PRINCIPAL
    # ═══════════════════════════════════════════════════════════════
    
    def process(self, question: str, lang: str = 'fr') -> Tuple[List[Fact], float, str]:
        """
        Traitement complet d'une question par le cycle conscience/inconscience.
        
        Retourne (faits_finaux, confiance, message_correction).
        """
        # Phase 1 — INCONSCIENT
        facts = self._unconscious_retrieve(question, max_facts=8)
        
        # Phase 2 — CONSCIENT
        confidence, validated = self._conscious_verify(question, facts)
        
        if confidence < CONF_MEDIUM:
            # Essayer l'exploration créative
            creative = self._creative_explore(question, validated)
            if creative:
                validated = creative + validated
                confidence = max(confidence, CONF_MEDIUM)  # Boost via créativité
        
        # Phase 3 — CORRECTION
        correction_msg, final_facts = self._correct_refine(
            question, confidence, validated
        )
        
        return final_facts, confidence, correction_msg
    
    # ═══════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═══════════════════════════════════════════════════════════════
    
    def _extract_subject(self, question: str) -> str:
        """Extrait le sujet central d'une question."""
        q = question.lower().strip()
        prefixes = [
            'what is the ', 'what is a ', 'what is ', 'what are ',
            'who is ', 'who was ', 'who wrote ', 'who painted ',
            'who discovered ', 'who invented ', 'who created ',
            'when did ', 'when was ', 'when ', 'where is ', 'where are ',
            'where ', 'why is ', 'why does ', 'why ', 'how does ',
            'how do ', 'how ', 'explain ', 'describe ', 'define ',
            'tell me about ', 'tell me ', 'is ', 'are ',
            'qu est ce que ', 'qui a ecrit ', 'qui a peint ',
            'qui a decouvert ', 'qui est ', 'quand ', 'ou ',
            'pourquoi ', 'comment ', 'explique ', 'quelle est la capitale de ',
            'capitale de ', 'capital of ',
        ]
        for p in sorted(prefixes, key=len, reverse=True):
            if q.startswith(p):
                q = q[len(p):].strip()
                break
        return q.strip('?.,!;:')
    
    def get_confidence_label(self, confidence: float) -> str:
        """Label de confiance."""
        if confidence >= CONF_HIGH:
            return "haute"
        if confidence >= CONF_MEDIUM:
            return "moyenne"
        if confidence >= CONF_LOW:
            return "basse"
        return "nulle"
