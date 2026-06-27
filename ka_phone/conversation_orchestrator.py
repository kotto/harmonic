#!/usr/bin/env python3
"""
CONVERSATION ORCHESTRATOR — Soutient des conversations cohérentes multi-tours
================================================================================
Résout le problème de cohérence conversationnelle dans KA en maintenant
un état de conversation explicite entre les tours.

Principe : contrairement aux LLMs qui "devine" le contexte via l'attention,
KA le fait de façon déterministe via une machine d'états + mémoire.

Composants :
  1. ConversationState — état courant (topic, dernier sujet, tours)
  2. TopicTracker — suit le fil conducteur de la conversation
  3. FollowUpDetector — détecte si le prompt est lié au précédent
  4. ContextualEnricher — enrichit le prompt avec le contexte précédent

Architecture dans le pipeline :
  Prompt → ConversationOrchestrator (enrichit) → Pipeline normal → Réponse
                                                       ↓
                                              ConversationOrchestrator (met à jour)

Usage :
  from conversation_orchestrator import ConversationOrchestrator
  co = ConversationOrchestrator()
  
  # Tour 1
  enriched, ctx = co.process("Quelle est la capitale du Senegal ?")
  # → Prompt enrichi, ctx = {"topic": "geography", "last_subject": "Senegal"}
  
  # Tour 2 (follow-up)
  enriched, ctx = co.process("Et sa population ?")
  # → "Quelle est la population du Senegal ?" (auto-complété avec le sujet)
  
  # Tour 3 (changement de sujet)
  enriched, ctx = co.process("Parle-moi de la musique africaine")
  # → Nouveau topic, pas de lien avec le précédent
"""

import re, json, time, os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque

# ══════════════════════════════════════════════════════════════════════════
# FOLLOW-UP PATTERNS — Questions qui font référence au contexte précédent
# ══════════════════════════════════════════════════════════════════════════

FOLLOW_UP_PATTERNS = [
    # Questions elliptiques (référence implicite au sujet précédent)
    (r'^(?:et|and)\s+(?:sa|son|ses|leur|leurs|la |le |les |l[\'e])\s*(.+?)\s*\??$', 'literal'),  # "Et sa population ?"
    (r'^(?:qu[\'e]est-ce que|que|quest-ce que|quelle|quel|quels|quelles)\s+(?:c[\'e]est|ca veut dire|signifie)\s*\??$', 'definition'),  # "Qu'est-ce que c'est ?"
    (r'^(?:pourquoi|why)\s*\??$', 'why'),  # "Pourquoi ?"
    (r'^(?:comment|how)\s*(?:ca|ça|cel[aà])\s*(?:marche|fonctionne)\s*\??$', 'how'),  # "Comment ça marche ?"
    (r'^(?:combien|how many|how much)\s*\??$', 'how_many'),  # "Combien ?"
    (r'^(?:quand|when)\s*\??$', 'when'),  # "Quand ?"
    (r'^(?:où|ou|where)\s*\??$', 'where'),  # "Où ?"
    (r'^(?:qui|who)\s*\??$', 'who'),  # "Qui ?"
    (r'^(?:vraiment|really|ah bon|serieux)\s*\??$', 'confirmation'),  # "Vraiment ?"
    (r'^(?:dis-moi|dis moi|parle-moi|parle moi)\s+(?:plus|davantage|encore)\s*(?:sur |de |du |des? )?\s*\??$', 'more'),  # "Dis-moi plus sur..."
    (r'^(?:continue|vas-y|go on|poursuis)\s*[.!]*$', 'continue'),  # "Continue"
    (r'^(?:donne-moi|donne moi|peux-tu|peux tu)\s+(?:un |une |des? )?(?:exemple|example)s?\s*\??$', 'example'),  # "Donne-moi un exemple"
    # Questions avec pronom mais sans sujet explicite
    (r'^(?:et|and)\s+(?:qu[\'e]est-ce que|que|comment|pourquoi|quand|où|qui)\s+(.+?)\s*\??$', 'follow_up_with_content'),  # "Et qu'est-ce que X ?"
]

# ══════════════════════════════════════════════════════════════════════════
# CONVERSATION TOPIC CATEGORIES
# ══════════════════════════════════════════════════════════════════════════

TOPIC_CATEGORIES = {
    "greeting": ["bonjour", "salut", "hello", "coucou", "hey", "yo", "bonsoir"],
    "farewell": ["au revoir", "bye", "adieu", "ciao", "a plus", "bonne nuit", "a demain"],
    "thanks": ["merci", "thanks", "thank you", "super", "parfait", "genial", "cool"],
    "question_factual": ["quelle", "quel", "quels", "quelles", "comment", "pourquoi", "quand", "combien", "qui", "que", "quoi", "est-ce que", "peux-tu", "sais-tu", "connais-tu"],
    "question_creative": ["ecris", "écris", "compose", "raconte", "imagine", "cree", "invente", "poeme", "poème", "histoire", "conte", "chanson"],
    "command": ["fais", "fait", "lance", "ouvre", "ferme", "active", "desactive", "affiche", "montre"],
}

# ══════════════════════════════════════════════════════════════════════════
# CONTEXTUAL ENRICHER
# ══════════════════════════════════════════════════════════════════════════

class ConversationOrchestrator:
    """
    Maintient la cohérence conversationnelle entre les tours.
    Enrichit les prompts avec le contexte précédent quand nécessaire.
    """

    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self.history = deque(maxlen=max_history)
        self.current_state = {
            "topic": None,           # "geography", "history", "creative", etc.
            "last_subject": None,    # "Senegal", "le Nil", "Kemet"
            "last_domain": None,     # Détecté par DomainRouter
            "last_response_type": None,  # "fact", "creative", "greeting"
            "last_confidence": 0.0,
            "conversation_depth": 0, # Nombre de tours sur le même sujet
            "subtopics": [],         # Sujets abordés dans ce fil
        }
        self.stats = {"total_turns": 0, "follow_ups_detected": 0, "topic_changes": 0}

    def process(self, prompt: str) -> Tuple[str, Dict]:
        """
        Traite un prompt dans le contexte de la conversation.
        
        Retourne :
          - prompt enrichi (avec contexte si follow-up détecté)
          - contexte actuel (pour injection dans la réponse)
        """
        self.stats["total_turns"] += 1
        prompt_clean = prompt.strip()

        # Step 1: Détecter le type de message
        msg_type = self._detect_message_type(prompt_clean)

        # Step 2: Détecter si c'est un follow-up
        is_follow_up, follow_up_type = self._detect_follow_up(prompt_clean)

        # Step 3: Enrichir le prompt si nécessaire
        enriched_prompt = prompt_clean
        if is_follow_up and self.current_state["last_subject"]:
            enriched_prompt = self._enrich_prompt(prompt_clean, follow_up_type)
            self.stats["follow_ups_detected"] += 1
            self.current_state["conversation_depth"] += 1
        elif msg_type in ("question_factual", "question_creative", "command"):
            # Nouveau sujet → reset du fil
            self.current_state["conversation_depth"] = 1
            self.current_state["subtopics"] = []

        # Step 4: Détecter changement de topic
        new_topic = self._detect_topic(prompt_clean)
        if new_topic and new_topic != self.current_state.get("topic"):
            if self.current_state.get("topic") is not None:
                self.stats["topic_changes"] += 1
            self.current_state["topic"] = new_topic

        # Step 5: Extraire le sujet principal
        subject = self._extract_subject(enriched_prompt)
        if subject and subject != self.current_state.get("last_subject"):
            if self.current_state.get("last_subject"):
                self.current_state["subtopics"].append(self.current_state["last_subject"])
            self.current_state["last_subject"] = subject

        # Build context for response
        context = {
            "is_follow_up": is_follow_up,
            "follow_up_type": follow_up_type,
            "topic": self.current_state["topic"],
            "last_subject": self.current_state["last_subject"],
            "conversation_depth": self.current_state["conversation_depth"],
            "recent_turns": list(self.history)[-3:],  # 3 derniers tours
            "subtopics_covered": self.current_state["subtopics"][-5:],
        }

        # Save this turn
        self.history.append({
            "prompt": prompt_clean,
            "enriched": enriched_prompt,
            "type": msg_type,
            "timestamp": time.time(),
        })

        return enriched_prompt, context

    def update_after_response(self, response_text: str, domain: str = None, 
                              confidence: float = 0.0, response_type: str = "fact"):
        """Met à jour l'état après avoir reçu la réponse du pipeline."""
        self.current_state["last_domain"] = domain
        self.current_state["last_confidence"] = confidence
        self.current_state["last_response_type"] = response_type
        if self.history:
            self.history[-1]["response"] = response_text[:200]

    # ═══ DETECTION ═══

    def _detect_message_type(self, prompt: str) -> str:
        p = prompt.lower().strip()
        for category, keywords in TOPIC_CATEGORIES.items():
            if any(kw in p for kw in keywords):
                return category
        return "statement"

    def _detect_follow_up(self, prompt: str) -> Tuple[bool, str]:
        """Détecte si le prompt est une question de suivi."""
        if not self.history:
            return False, "none"

        p = prompt.lower().strip()

        # Vérifier si le prompt est très court (indice de follow-up)
        if len(p.split()) <= 3 and any(p.startswith(w) for w in ["et ", "and ", "ou ", "or ", "mais ", "but "]):
            return True, "short_follow_up"

        # Vérifier les patterns de follow-up
        for pattern, ftype in FOLLOW_UP_PATTERNS:
            if re.match(pattern, p):
                return True, ftype

        return False, "none"

    def _detect_topic(self, prompt: str) -> Optional[str]:
        """Détecte le topic principal de la conversation."""
        p = prompt.lower()
        topic_keywords = {
            "geography": ["capitale", "pays", "ville", "continent", "population", "monnaie", "fleuve", "ocean", "montagne", "desert", "carte", "frontiere", "km", "superficie"],
            "history": ["guerre", "revolution", "roi", "empereur", "empire", "independance", "bataille", "traite", "colonie", "dynastie", "pharaon", "siecle", "avant jc", "apres jc"],
            "science": ["formule", "atome", "physique", "chimie", "biologie", "adn", "cellule", "etoile", "planete", "univers", "force", "energie"],
            "culture": ["musique", "film", "livre", "art", "peinture", "sculpture", "theatre", "opera", "litterature", "poeme", "roman"],
            "health": ["sante", "medecin", "maladie", "symptome", "traitement", "vaccin", "virus", "bacterie", "hopital", "medicament"],
            "tech": ["internet", "ordinateur", "code", "python", "programme", "algorithme", "ia", "intelligence artificielle", "app", "software"],
            "kemet": ["egypte", "kemet", "pharaon", "nil", "pyramide", "hieroglyphe", "maat", "sphinx", "obelisque", "kheops", "nubie"],
            "africa": ["afrique", "africain", "senegal", "mali", "cameroun", "congo", "ethiopie", "sahara", "griot", "baobab"],
            "creative": ["ecris", "poeme", "histoire", "conte", "raconte", "imagine", "chanson", "poeme", "sonnet", "haiku"],
        }
        scores = {t: sum(1 for kw in kws if kw in p) for t, kws in topic_keywords.items()}
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else None

    def _extract_subject(self, prompt: str) -> Optional[str]:
        """Extrait le sujet principal du prompt."""
        # Nettoyer les mots question
        clean = re.sub(r'^(?:et\s+)?(?:quelle|quel|quels|quelles|qu[\'e]est[-\s]ce que|comment|pourquoi|quand|combien|qui|que|quoi)\s+(?:est|sont|était|etaient|a |ont |le |la |les |l[\'e]|un |une |des? )?', '', prompt, flags=re.IGNORECASE)
        clean = re.sub(r'^(?:dis-moi|parle-moi|raconte-moi|explique-moi|donne-moi)\s+(?:de |du |des? |le |la |les |l[\'e])?\s*', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'^(?:ecris|compose|fais|peux-tu|sais-tu|connais-tu)\s+(?:un |une |le |la |les |des? )?', '', clean, flags=re.IGNORECASE)
        clean = clean.strip().rstrip("?!.,;: ")

        if clean and len(clean) > 2:
            # Garder les 5 premiers mots significatifs
            words = clean.split()
            stop = {'de', 'du', 'des', 'le', 'la', 'les', 'un', 'une', 'et', 'ou', 'a', 'au', 'aux', 'en', 'dans', 'sur', 'pour', 'avec', 'sans', 'pas', 'plus', 'moins'}
            meaningful = [w for w in words if w.lower() not in stop]
            return ' '.join(meaningful[:5]) if meaningful else clean[:60]
        return None

    def _enrich_prompt(self, prompt: str, follow_up_type: str) -> str:
        """Enrichit un prompt de follow-up avec le contexte précédent."""
        last_subject = self.current_state.get("last_subject", "")

        if follow_up_type == "short_follow_up" and last_subject:
            return f"{prompt} ({last_subject})"

        if follow_up_type == "why" and last_subject:
            return f"Pourquoi {last_subject} ?"

        if follow_up_type == "how" and last_subject:
            return f"Comment fonctionne {last_subject} ?"

        if follow_up_type == "when" and last_subject:
            return f"Quand {last_subject} ?"

        if follow_up_type == "where" and last_subject:
            return f"Où se trouve {last_subject} ?"

        if follow_up_type == "who" and last_subject:
            return f"Qui est {last_subject} ?"

        if follow_up_type == "how_many" and last_subject:
            return f"Combien de {last_subject} ?"

        if follow_up_type == "definition" and last_subject:
            return f"Qu'est-ce que {last_subject} ?"

        if follow_up_type == "more" and last_subject:
            return f"Dis-moi plus sur {last_subject}"

        if follow_up_type == "example" and last_subject:
            return f"Donne-moi un exemple de {last_subject}"

        if follow_up_type == "confirmation" and last_subject:
            return f"Confirme que {last_subject}"

        # Si c'est un follow-up avec du contenu mais sans sujet explicite
        if last_subject and not any(w.lower() in prompt.lower() for w in last_subject.lower().split()):
            return f"{prompt} concernant {last_subject}"

        return prompt

    def get_conversation_summary(self) -> Dict:
        """Résumé de la conversation en cours."""
        return {
            "topic": self.current_state["topic"],
            "subject": self.current_state["last_subject"],
            "depth": self.current_state["conversation_depth"],
            "turns_total": self.stats["total_turns"],
            "follow_ups": self.stats["follow_ups_detected"],
            "topic_changes": self.stats["topic_changes"],
            "recent": [h.get("prompt", "")[:60] for h in list(self.history)[-5:]],
        }

    def reset(self):
        """Réinitialise la conversation (nouveau départ)."""
        self.history.clear()
        self.current_state = {
            "topic": None, "last_subject": None, "last_domain": None,
            "last_response_type": None, "last_confidence": 0.0,
            "conversation_depth": 0, "subtopics": [],
        }


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    co = ConversationOrchestrator()

    print("=" * 60)
    print("CONVERSATION ORCHESTRATOR — Test de cohérence")
    print("=" * 60)

    conversation = [
        "Bonjour !",
        "Quelle est la capitale du Senegal ?",
        "Et sa population ?",
        "Pourquoi ?",
        "Parle-moi de la musique africaine",
        "Quels instruments ?",
        "Continue",
        "Merci, au revoir !",
    ]

    for i, prompt in enumerate(conversation):
        enriched, ctx = co.process(prompt)
        print(f"\nTour {i+1}: '{prompt}'")
        print(f"  Enrichi: '{enriched}'")
        print(f"  Follow-up: {ctx['is_follow_up']} | Topic: {ctx['topic']} | Sujet: {ctx['last_subject']} | Profondeur: {ctx['conversation_depth']}")

    print(f"\nRésumé: {json.dumps(co.get_conversation_summary(), ensure_ascii=False, indent=2)}")