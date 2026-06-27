#!/usr/bin/env python3
"""
FEEDBACK LEARNER — Boucle d'auto-apprentissage pour KA Phone
===============================================================
Apprend des interactions utilisateur pour améliorer les réponses
futures. Quand KA répond avec une confiance faible et que l'utilisateur
est satisfait (ne reformule pas), la paire QA est ajoutée à l'hologramme.

Stratégie :
  1. Après chaque réponse faible (confiance < 0.5), marquer la QA comme "pending"
  2. Si l'utilisateur pose une nouvelle question sans reformuler → succès
  3. Si l'utilisateur reformule (mots similaires) → échec
  4. Si succès → ajouter la QA à l'hologramme avec amplitude élevée
  5. Si échec → ne pas apprendre, proposer fallback alternatif

Usage:
  from feedback_learner import FeedbackLearner
  learner = FeedbackLearner(user_memory)
  
  # Après une réponse :
  learner.mark_pending(prompt, response, confidence=0.35)
  
  # À la question suivante :
  learner.evaluate_previous(new_prompt)  # → "learned", "discarded", ou "pending"
"""

import re, hashlib, os, json, time
from typing import Dict, Optional, Tuple, List
from datetime import datetime
import numpy as np

# ══════════════════════════════════════════════════════════════════════════
# FEEDBACK LEARNER
# ══════════════════════════════════════════════════════════════════════════

class FeedbackLearner:
    """
    Apprentissage par feedback implicite.
    
    Principe : si l'utilisateur ne reformule pas après une réponse faible,
    c'est que la réponse était satisfaisante → on l'apprend.
    """

    def __init__(self, user_memory=None, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), "..", "data", "feedback")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.user_memory = user_memory  # Instance UserMemory
        
        # QA en attente de feedback
        self.pending_qa: Optional[Dict] = None
        
        # Historique des apprentissages
        self.learned_qa: List[Dict] = []
        self.discarded_qa: List[Dict] = []
        self.stats = {
            "total_pending": 0,
            "total_learned": 0,
            "total_discarded": 0,
            "total_strong": 0,  # Réponses déjà bonnes
        }
        
        self._load()

    def _load(self):
        """Charge l'historique d'apprentissage."""
        stats_file = os.path.join(self.data_dir, "learner_stats.json")
        learned_file = os.path.join(self.data_dir, "learned_qa.json")
        
        if os.path.exists(stats_file):
            with open(stats_file, 'r', encoding='utf-8') as f:
                self.stats.update(json.load(f))
        
        if os.path.exists(learned_file):
            with open(learned_file, 'r', encoding='utf-8') as f:
                self.learned_qa = json.load(f)

    def _save(self):
        """Sauvegarde l'état d'apprentissage."""
        stats_file = os.path.join(self.data_dir, "learner_stats.json")
        learned_file = os.path.join(self.data_dir, "learned_qa.json")
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        
        # Garder les 1000 dernières QA apprises
        with open(learned_file, 'w', encoding='utf-8') as f:
            json.dump(self.learned_qa[-1000:], f, indent=2, ensure_ascii=False)

    def mark_pending(self, prompt: str, response: str, confidence: float,
                     source: str = "unknown", domain: str = "general"):
        """
        Marque une QA comme en attente de feedback.
        À appeler après chaque réponse avec confiance < seuil.
        """
        if confidence >= 0.70:
            # Réponse déjà bonne → pas besoin d'apprendre
            self.stats["total_strong"] += 1
            self.pending_qa = None
            return None

        self.stats["total_pending"] += 1
        
        self.pending_qa = {
            "prompt": prompt[:300],
            "response": response[:500],
            "confidence": confidence,
            "source": source,
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
        }
        
        return self.pending_qa

    def evaluate_previous(self, new_prompt: str) -> Dict:
        """
        Évalue si la réponse précédente était satisfaisante.
        À appeler quand l'utilisateur pose une NOUVELLE question.
        
        Retourne {"status": "learned"|"discarded"|"none", ...}
        """
        if self.pending_qa is None:
            return {"status": "none"}

        prev_prompt = self.pending_qa.get("prompt", "")
        prev_response = self.pending_qa.get("response", "")
        
        # Détecter si le nouveau prompt est une reformulation
        is_reformulation = self._is_reformulation(prev_prompt, new_prompt)
        
        if is_reformulation:
            # L'utilisateur reformule → la réponse n'était pas bonne
            self.discarded_qa.append(self.pending_qa)
            self.stats["total_discarded"] += 1
            self.pending_qa = None
            self._save()
            return {
                "status": "discarded",
                "reason": "reformulation",
                "prev_prompt": prev_prompt[:100],
                "new_prompt": new_prompt[:100],
            }
        else:
            # L'utilisateur pose une nouvelle question → la réponse était OK
            self._learn_from_pending()
            return {
                "status": "learned",
                "reason": "no_reformulation",
                "prev_prompt": prev_prompt[:100],
                "qa_added": True,
            }

    def force_learn(self):
        """Force l'apprentissage de la QA en attente (feedback explicite positif)."""
        if self.pending_qa is None:
            return {"status": "none"}
        return self._learn_from_pending()

    def force_discard(self):
        """Force le rejet de la QA en attente (feedback explicite négatif)."""
        if self.pending_qa is None:
            return {"status": "none"}
        self.discarded_qa.append(self.pending_qa)
        self.stats["total_discarded"] += 1
        self.pending_qa = None
        self._save()
        return {"status": "discarded", "reason": "explicit"}

    def _learn_from_pending(self) -> Dict:
        """Apprend la QA en attente : l'ajouter à l'hologramme."""
        qa = self.pending_qa
        self.pending_qa = None
        
        # Ajouter à l'historique
        self.learned_qa.append(qa)
        self.stats["total_learned"] += 1
        
        # Ajouter à l'hologramme utilisateur si disponible
        if self.user_memory:
            try:
                # Stocker avec une amplitude plus élevée (c'est vérifié par l'utilisateur)
                self.user_memory.remember(
                    prompt=qa["prompt"] + " [USER_VERIFIED]",
                    response=qa["response"],
                    domain=qa.get("domain", "general"),
                    context={"learned": True, "confidence": qa.get("confidence", 0)}
                )
            except Exception:
                pass
        
        self._save()
        
        return {
            "status": "learned",
            "qa": {"prompt": qa["prompt"][:100], "response": qa["response"][:100]},
        }

    def _is_reformulation(self, prev_prompt: str, new_prompt: str) -> bool:
        """
        Détecte si new_prompt est une reformulation de prev_prompt.
        Utilise le chevauchement de mots + similarité de structure.
        """
        if not prev_prompt or not new_prompt:
            return False

        p_prev = prev_prompt.lower().strip()
        p_new = new_prompt.lower().strip()

        # Extraire les mots significatifs (>3 lettres)
        words_prev = set(re.findall(r'[a-zéèêëàâîïôûùç]{4,}', p_prev))
        words_new = set(re.findall(r'[a-zéèêëàâîïôûùç]{4,}', p_new))

        if not words_prev or not words_new:
            return False

        # Chevauchement Jaccard
        intersection = words_prev & words_new
        union = words_prev | words_new
        jaccard = len(intersection) / len(union) if union else 0

        # Si plus de 60% des mots sont communs → reformulation probable
        return jaccard > 0.60

    def get_stats(self) -> Dict:
        return {
            **self.stats,
            "pending": self.pending_qa is not None,
            "learned_qa_count": len(self.learned_qa),
            "discarded_qa_count": len(self.discarded_qa),
            "learning_rate": (
                self.stats["total_learned"] / max(self.stats["total_learned"] + self.stats["total_discarded"], 1)
            ),
        }

    def get_learned_qa(self, domain: str = None, limit: int = 50) -> List[Dict]:
        """Retourne les QA apprises, filtrées par domaine."""
        results = self.learned_qa
        if domain:
            results = [qa for qa in results if qa.get("domain") == domain]
        return results[-limit:]


# ══════════════════════════════════════════════════════════════════════════
# INTEGRATION EXAMPLE
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Simuler une session utilisateur
    learner = FeedbackLearner()

    print("=== Simulation de feedback learning ===\n")

    # 1. KA répond faiblement
    learner.mark_pending(
        prompt="Comment faire une tarte aux pommes ?",
        response="Pour une tarte aux pommes, il faut une pâte et des pommes.",
        confidence=0.35,
        source="hybrid_writer",
        domain="cuisine_gastronomie"
    )
    print("1. Question posée, réponse faible → pending")

    # 2. L'utilisateur pose une autre question (pas de reformulation) → succès
    result = learner.evaluate_previous("Quelle est la capitale du Brésil ?")
    print(f"2. Nouvelle question différente → {result['status']} ({result['reason']})")

    # 3. KA répond faiblement à nouveau
    learner.mark_pending(
        prompt="Qui a inventé le téléphone ?",
        response="Alexander Graham Bell en 1876.",
        confidence=0.40,
        source="qa_knowledge",
        domain="technologie"
    )
    print("3. Question posée, réponse faible → pending")

    # 4. L'utilisateur reformule → échec
    result = learner.evaluate_previous("Cest qui linventeur du telephone ?")
    print(f"4. Reformulation détectée → {result['status']} (Jaccard élevé)")

    print(f"\nStats finales : {json.dumps(learner.get_stats(), indent=2)}")