"""
DeepSeek Style Fallback — Reformulation élégante des réponses harmoniques.
==========================================================================
Prend la réponse du système harmonique et la fait reformuler par DeepSeek
avec une consigne stricte : améliorer UNIQUEMENT le style et la formulation,
sans ajouter ni modifier aucun fait.

C'est une béquille stylistique temporaire — le temps que le système
harmonique atteigne la qualité de formulation souhaitée.

Usage:
    from llm.deepseek_styler import DeepSeekStyleFormatter

    styler = DeepSeekStyleFormatter()
    polished = styler.polish(reponse_harmonique, question_utilisateur)

Configuration (variables d'environnement):
    DEEPSEEK_STYLER_ENABLED=true     # activer (défaut: true si clé dispo)
    DEEPSEEK_STYLER_MODEL=deepseek-chat  # modèle à utiliser
    DEEPSEEK_STYLER_TEMPERATURE=0.7  # température (0.0-1.0)
    DEEPSEEK_STYLER_TIMEOUT=8        # timeout en secondes
"""

import os
import time
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

# ── System prompt : strict, français, zéro ajout ──────────────────────────

_SYSTEM_PROMPT = (
    "Tu es un reformulateur de texte. Ta SEULE tâche est de reformuler "
    "le texte fourni pour améliorer le style, la clarté, la fluidité et "
    "le naturel de l'expression en français.\n\n"
    "RÈGLES ABSOLUES :\n"
    "1. N'ajoute AUCUNE information, aucun fait, aucun chiffre, aucune date "
    "qui ne soit DÉJÀ présent dans le texte source.\n"
    "2. Ne supprime aucun fait important du texte source.\n"
    "3. Ne pose pas de questions à l'utilisateur.\n"
    "4. Garde EXACTEMENT le même sens, la même intention.\n"
    "5. Conserve le ton (chaleureux, factuel, pédagogique) du texte source.\n"
    "6. Réponds UNIQUEMENT avec le texte reformulé, SANS préambule, "
    "SANS guillemets, SANS commentaire.\n"
    "7. Si le texte source est déjà parfait, recopie-le tel quel."
)


class DeepSeekStyleFormatter:
    """
    Formateur stylistique utilisant DeepSeek comme « polisseur » final.

    Prend une réponse brute du système harmonique, la confie à DeepSeek
    avec instruction stricte de ne faire que reformuler. En cas d'échec
    (timeout, erreur API, clé manquante), retourne le texte original
    sans interruption — le système continue de fonctionner normalement.

    Attributes:
        enabled: True si le styler est activé et la clé API disponible.
        model: Nom du modèle DeepSeek à utiliser.
        temperature: Niveau de créativité stylistique (0.0 = sobre, 1.0 = varié).
        timeout: Timeout en secondes pour l'appel API.
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
    ):
        # Déterminer si activé
        if enabled is None:
            env_enabled = os.environ.get("DEEPSEEK_STYLER_ENABLED", "").lower()
            if env_enabled in ("false", "0", "no", "off"):
                enabled = False
            else:
                # Activé par défaut si la clé API est présente
                api_key = os.environ.get("DEEPSEEK_API_KEY", "")
                enabled = bool(api_key) and env_enabled not in ("false", "0", "no", "off")
                if not api_key and env_enabled in ("true", "1", "yes", "on"):
                    logger.warning(
                        "DeepSeekStyleFormatter: DEEPSEEK_STYLER_ENABLED=true "
                        "mais DEEPSEEK_API_KEY n'est pas définie — désactivé."
                    )
                    enabled = False

        self.enabled = enabled
        self.model = model or os.environ.get("DEEPSEEK_STYLER_MODEL", "deepseek-chat")
        self.temperature = temperature or float(
            os.environ.get("DEEPSEEK_STYLER_TEMPERATURE", "0.7")
        )
        self.timeout = timeout or float(
            os.environ.get("DEEPSEEK_STYLER_TIMEOUT", "8")
        )

        self._provider = None
        self._stats = {"calls": 0, "successes": 0, "fallbacks": 0, "total_latency_ms": 0.0}

        if self.enabled:
            logger.info(
                f"DeepSeekStyleFormatter activé: model={self.model}, "
                f"temperature={self.temperature}, timeout={self.timeout}s"
            )
        else:
            logger.info("DeepSeekStyleFormatter désactivé (DEEPSEEK_STYLER_ENABLED=false "
                        "ou DEEPSEEK_API_KEY manquante)")

    def _get_provider(self):
        """Initialisation paresseuse du provider OpenAI (DeepSeek-compatible)."""
        if self._provider is None and self.enabled:
            from .base import LLMConfig
            from .openai_client import OpenAILLM

            cfg = LLMConfig(
                model=self.model,
                api_key=os.environ.get("DEEPSEEK_API_KEY"),
                api_base="https://api.deepseek.com/v1",
                temperature=self.temperature,
                max_tokens=2048,
                system_prompt=_SYSTEM_PROMPT,
                timeout=self.timeout,
            )
            self._provider = OpenAILLM(cfg)
        return self._provider

    def _build_user_prompt(self, response_text: str, user_question: str = "") -> str:
        """Construit le prompt utilisateur avec le texte à reformuler."""
        texte = response_text.strip()

        if user_question:
            return (
                f"Question originale de l'utilisateur : {user_question.strip()}\n\n"
                f"Réponse à reformuler :\n{texte}\n\n"
                f"Texte reformulé :"
            )
        else:
            return (
                f"Texte à reformuler :\n{texte}\n\n"
                f"Texte reformulé :"
            )

    def polish(self, response_text: str, user_question: str = "") -> str:
        """
        Reformule une réponse harmonique avec le style DeepSeek.

        Args:
            response_text: La réponse brute du système harmonique.
            user_question: La question originale de l'utilisateur (pour contexte).

        Returns:
            Le texte reformulé par DeepSeek, ou le texte original en cas d'échec.
            Ne lève jamais d'exception.
        """
        if not self.enabled:
            return response_text

        if not response_text or len(response_text.strip()) < 30:
            # Texte trop court, pas besoin de reformulation
            return response_text

        self._stats["calls"] += 1

        provider = self._get_provider()
        if provider is None:
            self._stats["fallbacks"] += 1
            return response_text

        prompt = self._build_user_prompt(response_text, user_question)

        # Appel avec timeout via thread (comme _llm_fallback dans bootstrapper.py)
        result = [None]
        error = [None]

        def _call():
            try:
                from .base import LLMConfig
                cfg = LLMConfig(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=2048,
                    system_prompt=_SYSTEM_PROMPT,
                )
                resp = provider.generate(prompt, cfg)
                if resp.content and len(resp.content.strip()) > 20:
                    result[0] = resp.content.strip()
                else:
                    error[0] = resp.error or "réponse vide ou trop courte"
            except Exception as e:
                error[0] = str(e)

        t_start = time.time()
        thread = threading.Thread(target=_call, daemon=True)
        thread.start()
        thread.join(timeout=self.timeout)

        latency = (time.time() - t_start) * 1000
        self._stats["total_latency_ms"] += latency

        if thread.is_alive():
            logger.warning(
                f"DeepSeekStyleFormatter: timeout après {self.timeout}s "
                f"pour '{user_question[:60]}...' — fallback au texte original"
            )
            self._stats["fallbacks"] += 1
            return response_text

        if result[0] is not None:
            polished = result[0]
            # Nettoyer les guillemets/artefacts fréquents
            polished = polished.strip().strip('"').strip("«»").strip()
            self._stats["successes"] += 1
            logger.debug(
                f"DeepSeekStyleFormatter: reformulé en {latency:.0f}ms "
                f"({len(response_text)}→{len(polished)} chars)"
            )
            return polished

        # Échec
        logger.warning(
            f"DeepSeekStyleFormatter: échec — {error[0] or 'réponse vide'} "
            f"— fallback au texte original"
        )
        self._stats["fallbacks"] += 1
        return response_text

    def get_stats(self) -> dict:
        """Retourne les statistiques d'utilisation du styler."""
        return {
            "enabled": self.enabled,
            "model": self.model,
            "temperature": self.temperature,
            "timeout_s": self.timeout,
            **self._stats,
            "success_rate": (
                self._stats["successes"] / max(self._stats["calls"], 1)
            ),
            "avg_latency_ms": (
                self._stats["total_latency_ms"] / max(self._stats["calls"], 1)
            ),
        }


# ── Instance globale (initialisation paresseuse par le serveur) ────────────

_global_styler: Optional[DeepSeekStyleFormatter] = None


def get_styler() -> DeepSeekStyleFormatter:
    """Retourne l'instance globale du DeepSeekStyleFormatter (créée au besoin)."""
    global _global_styler
    if _global_styler is None:
        _global_styler = DeepSeekStyleFormatter()
    return _global_styler


def polish_response(response_text: str, user_question: str = "") -> str:
    """
    Fonction utilitaire : reformule une réponse via le styler global.
    Pratique pour les intégrations rapides sans gérer l'instance.
    """
    return get_styler().polish(response_text, user_question)
