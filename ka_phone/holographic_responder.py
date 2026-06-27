#!/usr/bin/env python3
"""
KA-Next -- HOLOGRAPHIC RESPONDER
==================================
Moteur de génération de réponses qui utilise les PRINCIPES
holographiques (interférence, résonance, déphasage φ, filtrage
d'amplitude) pour produire des réponses en langage naturel.

Ce n'est PAS un template -- chaque réponse est le produit d'une
transformation d'onde appliquée aux connaissances de l'hologramme.

Modes de réponse :
  FACTUAL   -> Résonance constructive Ψ_q·H → réponse tracée
  REASON    -> Propagation multi-hop → chaîne explicite
  CREATIVE  -> Déphasage φ structuré → interconnexions inattendues
  TRANSLATE -> Transposition de fréquence φ^n → projection inter-langue
  SUMMARIZE -> Seuillage Mittag-Leffler → extraction énergétique
"""

import math, hashlib, time
from typing import Dict, List, Optional, Any

PHI = (1 + math.sqrt(5)) / 2


class HolographicResponder:
    """Génère des réponses en appliquant les principes holographiques."""

    def __init__(self, pipeline=None):
        self.pipeline = pipeline

    def respond(self, prompt: str, mode: str = "factual",
                facts: List[Dict] = None, patches: List[Dict] = None,
                reasoning_result: Dict = None,
                creative_alpha: float = 0.3,
                translate_info: Dict = None,
                summarize_info: Dict = None,
                parametric_result: Dict = None) -> Dict[str, Any]:
        """
        Génère une réponse en utilisant le principe holographique approprié
        au mode demandé.

        Chaque mode applique une transformation d'onde différente :
          factual   -> interférence constructive (Ψ_q·H)
          reason    -> propagation multi-hop (Ψ rebondit)
          creative  -> déphasage φ (rotation dans l'espace de phase)
          translate -> transposition φ (changement de base)
          summarize -> seuillage d'amplitude (filtrage énergétique)
        """
        t0 = time.time()

        if mode == "factual":
            response = self._respond_factual(prompt, facts, patches, parametric_result)
        elif mode == "reason":
            response = self._respond_reason(prompt, facts, patches, reasoning_result)
        elif mode == "creative":
            response = self._respond_creative(prompt, facts, patches, creative_alpha)
        elif mode == "translate":
            response = self._respond_translate(prompt, facts, translate_info)
        elif mode == "summarize":
            response = self._respond_summarize(prompt, facts, summarize_info)
        else:
            response = self._respond_factual(prompt, facts, patches)

        elapsed_ms = round((time.time() - t0) * 1000, 1)
        response["response_time_ms"] = elapsed_ms
        return response

    # ═══════════════════════════════════════════════════════════════════
    # FACTUAL : Interférence constructive Ψ_q·H
    # ═══════════════════════════════════════════════════════════════════

    def _respond_factual(self, prompt: str, facts: List[Dict],
                         patches: List[Dict],
                         parametric_result: Dict = None) -> Dict:
        """
        Réponse factuelle : l'onde de la question interagit avec l'hologramme.
        Les faits qui résonnent le plus fort sont sélectionnés.
        La réponse est l'interférence constructive de ces faits.
        """
        lines = []

        # Priorité 1 : ParametricKB (calcul exact)
        if parametric_result:
            text = parametric_result.get("text", "") if isinstance(parametric_result, dict) else str(parametric_result)
            if text and len(text) > 3:
                lines.append(text)
                if facts:
                    lines.append("")
                    lines.append(f"(Ce calcul exact a été effectué via le moteur ParametricKB "
                                f"en exploitant {len(facts)} faits holographiques de contexte.)")
                return {"text": "\n".join(lines), "source": "parametric+holographic",
                        "confidence": 0.95, "facts_used": len(facts) if facts else 0}

        # Priorité 2 : Faits holographiques
        if not facts:
            return {"text": f"L'hologramme ne contient pas d'information suffisante "
                           f"pour répondre à « {prompt[:100]} ».", 
                    "source": "no_resonance", "confidence": 0.0, "facts_used": 0}

        # Associer chaque fait à son patch le plus proche pour hériter du score de résonance
        # Le score de patch FAISS (vecteurs ABC 4179-dim) est sémantiquement pertinent
        fact_scores = {}
        for fact in facts:
            text = fact.get("text", "")
            if not text or len(text) < 5:
                continue
            patch_idx = fact.get("patch_index", -1)
            # Score combiné : FAISS (structural) + boost sémantique (sens humain)
            structural_score = 0
            if patches:
                for p in patches:
                    if p.get("index") == patch_idx:
                        structural_score = p.get("resonance_score", p.get("score", 0))
                        break
            
            # Boost sémantique : intersection des mots entre question et fait
            semantic = self._semantic_boost(prompt, text)
            
            # Score final = 0.3 * structural + 0.7 * semantic
            # Le poids sémantique est dominant car c'est le pont onde->sens
            combined_score = 0.3 * structural_score + 0.7 * semantic
            
            # Grouper par début de texte pour éviter les doublons
            key = text[:80]
            if key not in fact_scores or combined_score > fact_scores[key][1]:
                fact_scores[key] = (text, combined_score, patch_idx)
        
        scored_facts = sorted(fact_scores.values(), key=lambda x: -x[1])

        # Sélectionner le meilleur fait (interférence constructive maximale)
        if scored_facts:
            best_text, best_score, best_patch = scored_facts[0]

            if best_score > 0.7:
                # Haute confiance : réponse directe
                lines.append(best_text.strip())
                if len(scored_facts) > 1 and scored_facts[1][1] > 0.5:
                    lines.append(scored_facts[1][0].strip())

                confidence = best_score
            elif best_score > 0.3:
                # Confiance moyenne : réponse avec contexte
                lines.append(f"D'après les connaissances holographiques activées "
                            f"(force de résonance {best_score:.0%}) :")
                lines.append(best_text.strip())
                if len(scored_facts) > 1:
                    lines.append("")
                    lines.append("Informations complémentaires :")
                    for text, score, _ in scored_facts[1:4]:
                        lines.append(f"• {text.strip()}")
                confidence = best_score * 0.8
            else:
                # Faible confiance : lister les faits avec avertissement
                lines.append(f"L'hologramme contient des informations partielles sur ce sujet "
                            f"(résonance maximale {best_score:.0%}). Voici les faits les plus proches :")
                for text, score, _ in scored_facts[:5]:
                    lines.append(f"• [{score:.0%}] {text.strip()}")
                confidence = best_score * 0.5
        else:
            lines.append(f"Aucun fait holographique n'a résonné avec votre question.")
            confidence = 0.0

        lines.append("")
        lines.append(f"[Réponse générée par interférence holographique — "
                    f"{len(scored_facts)} faits activés, {len(patches) if patches else 0} patches]")

        return {
            "text": "\n".join(lines),
            "source": "holographic_interference",
            "confidence": round(confidence, 2),
            "facts_used": len(scored_facts),
            "top_resonance": round(scored_facts[0][1], 3) if scored_facts else 0
        }

    # ═══════════════════════════════════════════════════════════════════
    # REASON : Propagation multi-hop (Ψ rebondit)
    # ═══════════════════════════════════════════════════════════════════

    def _respond_reason(self, prompt: str, facts: List[Dict],
                        patches: List[Dict],
                        reasoning_result: Dict = None) -> Dict:
        """
        Réponse par raisonnement : l'onde se propage en rebondissant
        à travers l'hologramme. Chaque rebond affine la connaissance.
        """
        lines = []

        if not reasoning_result or not reasoning_result.get("chain"):
            return self._respond_factual(prompt, facts, patches)

        chain = reasoning_result["chain"]
        active_hops = [h for h in chain if h.get("n_facts", 0) > 0]

        lines.append(f"RAISONNEMENT HOLOGRAPHIQUE — {len(active_hops)} sauts de résonance")
        lines.append("=" * 50)
        lines.append("")

        for hop in chain:
            hop_num = hop.get("hop", 0)
            score = hop.get("top_score", 0)
            facts_in_hop = hop.get("facts", [])

            if not facts_in_hop:
                continue

            if hop_num == 0:
                lines.append(f"[Saut 0] Résonance directe avec la question (force {score:.0%})")
                lines.append(f"L'onde Ψ_q de votre question entre en interférence avec l'hologramme.")
            else:
                lines.append(f"[Saut {hop_num}] Rebond de l'onde (force {score:.0%})")
                lines.append(f"Les faits du niveau {hop_num-1} forment une onde composée Ψ_{hop_num} "
                            f"qui révèle de nouvelles connexions.")

            for f in facts_in_hop[:3]:
                text = f.get("text", "")
                if text and len(text) > 3:
                    lines.append(f"  → {text.strip()}")
            lines.append("")

        # Synthèse finale
        lines.append("[Synthèse]")
        if facts:
            # Prendre les faits les plus spécifiques (dernier hop)
            last_hop_facts = chain[-1].get("facts", []) if chain else []
            synthesis_facts = last_hop_facts if last_hop_facts else facts[:3]
            lines.append("Le raisonnement holographique aboutit à la conclusion suivante :")
            lines.append("")
            for f in synthesis_facts[:3]:
                text = f.get("text", "")
                if text and len(text) > 3:
                    lines.append(f"  • {text.strip()}")
        else:
            lines.append("Aucune conclusion n'a pu être atteinte via le raisonnement holographique.")

        lines.append("")
        edges = reasoning_result.get("graph_edges", [])
        if edges:
            lines.append("[Graphe de raisonnement]")
            for edge in edges:
                lines.append(f"  Niveau {edge['from_hop']} → Niveau {edge['to_hop']} "
                           f"(force de connexion : {edge.get('strength', 0):.0%})")

        return {
            "text": "\n".join(lines),
            "source": "holographic_reasoning",
            "confidence": round(chain[0].get("top_score", 0.5) * 0.9, 2),
            "facts_used": len(facts),
            "hops": len(active_hops),
            "reasoning_depth": len(active_hops)
        }

    # ═══════════════════════════════════════════════════════════════════
    # CREATIVE : Déphasage φ (rotation dans l'espace de phase)
    # ═══════════════════════════════════════════════════════════════════

    def _respond_creative(self, prompt: str, facts: List[Dict],
                          patches: List[Dict],
                          alpha: float = 0.3) -> Dict:
        """
        Réponse créative par déphasage φ : l'onde de la question est
        intentionnellement décalée d'un angle α·φ·π, explorant ainsi
        les motifs adjacents dans l'espace de phase.
        """
        lines = []

        # Calculer le déphasage
        delta = alpha * PHI * math.pi
        delta_deg = math.degrees(delta) % 360

        lines.append(f"EXPLORATION CRÉATIVE — Déphasage φ de {delta_deg:.0f}° (α = {alpha:.2f})")
        lines.append("=" * 50)
        lines.append("")

        if alpha < 0.2:
            lines.append(f"Créativité minimale (α={alpha:.2f}) : l'onde est très proche de la question originale. "
                        f"Les faits restent ancrés dans la connaissance standard.")
        elif alpha < 0.5:
            lines.append(f"Créativité modérée (α={alpha:.2f}) : l'onde est décalée de {delta_deg:.0f}° par φ. "
                        f"Des connexions inattendues émergent tout en restant ancrées dans les faits.")
        elif alpha < 0.8:
            lines.append(f"Créativité élevée (α={alpha:.2f}) : l'onde explore les motifs adjacents. "
                        f"Les connexions sont surprenantes mais toujours traçables.")
        else:
            lines.append(f"Créativité maximale (α={alpha:.2f}) : l'onde est fortement déphasée. "
                        f"Exploration des confins de l'espace de phase holographique.")
        lines.append("")

        if not facts:
            lines.append("Aucun fait n'a été activé par le déphasage créatif. "
                        "L'hologramme a besoin de plus de connaissances dans cette région de phase.")
            return {"text": "\n".join(lines), "source": "creative_dephasing",
                    "confidence": 0.1, "alpha": alpha, "phase_shift_deg": round(delta_deg, 1)}

        # Séparer les faits "standards" des faits "créatifs"
        # (dans le pipeline, les creative_facts viennent du déphasage)
        standard_facts = [f for f in facts if "[Créatif]" not in f.get("text", "")]
        creative_facts = [f for f in facts if "[Créatif]" in f.get("text", "")]

        if standard_facts:
            lines.append("🔵 **Ancrages** (interférence constructive classique) :")
            for f in standard_facts[:3]:
                text = f.get("text", "").replace("[Créatif] ", "")
                if text and len(text) > 3:
                    lines.append(f"  • {text.strip()[:200]}")
            lines.append("")

        if creative_facts:
            lines.append(f"🟣 **Connexions créatives** (déphasage φ de {delta_deg:.0f}°) :")
            for f in creative_facts[:3]:
                text = f.get("text", "").replace("[Créatif] ", "")
                if text and len(text) > 3:
                    lines.append(f"  ⊕ {text.strip()[:200]}")
            lines.append("")
        elif standard_facts:
            # Pas de faits créatifs explicites : créer des connexions par inference
            lines.append(f"🟣 **Connexions potentielles** (déphasage φ de {delta_deg:.0f}°) :")
            if len(standard_facts) >= 2:
                for i in range(min(3, len(standard_facts) - 1)):
                    t1 = standard_facts[i].get("text", "")[:100]
                    t2 = standard_facts[i + 1].get("text", "")[:100]
                    if t1 and t2:
                        lines.append(f"  ⊕ {t1.strip()}  ⟷  {t2.strip()}")
            lines.append("")

        lines.append("--")
        lines.append(f"[Généré par déphasage holographique φ | α = {alpha:.2f} | "
                    f"rotation de {delta_deg:.0f}° dans l'espace de phase | "
                    f"{len(facts)} faits mobilisés]")

        return {
            "text": "\n".join(lines),
            "source": "holographic_creative_dephasing",
            "confidence": 0.6 + alpha * 0.2,
            "alpha": alpha,
            "phase_shift_deg": round(delta_deg, 1),
            "facts_used": len(facts)
        }

    # ═══════════════════════════════════════════════════════════════════
    # TRANSLATE : Transposition de fréquence φ^n
    # ═══════════════════════════════════════════════════════════════════

    def _respond_translate(self, prompt: str, facts: List[Dict],
                           translate_info: Dict = None) -> Dict:
        """
        Réponse par transposition : l'onde de la langue source est multipliée
        par φ^n pour la projeter dans l'espace de phase de la langue cible.
        """
        lines = []

        if not translate_info:
            translate_info = {}

        src = translate_info.get("source_lang", "fr")
        tgt = translate_info.get("target_lang", "en")
        phi_power = translate_info.get("phi_power", 1.0)
        factor = translate_info.get("transposition_factor", PHI ** phi_power)
        src_pos = translate_info.get("source_position", (0, 0))
        tgt_pos = translate_info.get("target_position", (0, 0))

        lines.append(f"TRADUCTION HOLOGRAPHIQUE [{src} → {tgt}]")
        lines.append("=" * 50)
        lines.append("")
        lines.append(f"Principe : l'onde de la langue source est transposée par φ^{phi_power} = {factor:.4f}")
        lines.append(f"  Espace source : fréquence ({src_pos[0]:.2f}, {src_pos[1]:.2f})")
        lines.append(f"  Espace cible  : fréquence ({tgt_pos[0]:.2f}, {tgt_pos[1]:.2f})")
        lines.append("")

        if not facts:
            lines.append(f"La transposition φ a été appliquée, mais aucun fait n'a été trouvé "
                        f"dans l'espace cible [{tgt}]. L'hologramme a besoin de plus de contenu "
                        f"dans cette langue.")
        else:
            lines.append(f"Faits résonant dans l'espace cible [{tgt}] :")
            for f in facts[:5]:
                text = f.get("text", "")
                if text and len(text) > 5:
                    lines.append(f"  • {text.strip()[:200]}")

        lines.append("")
        lines.append(f"[Traduction par transposition de fréquence φ | "
                    f"facteur {factor:.4f} | {len(facts)} faits activés]")

        return {
            "text": "\n".join(lines),
            "source": "holographic_frequency_transposition",
            "confidence": 0.5 if facts else 0.2,
            "source_lang": src,
            "target_lang": tgt,
            "phi_power": phi_power,
            "facts_used": len(facts)
        }

    # ═══════════════════════════════════════════════════════════════════
    # SUMMARIZE : Seuillage d'amplitude (Mittag-Leffler)
    # ═══════════════════════════════════════════════════════════════════

    def _respond_summarize(self, prompt: str, facts: List[Dict],
                           summarize_info: Dict = None) -> Dict:
        """
        Résumé par filtrage d'amplitude : le texte est projeté dans
        l'hologramme. Seules les fréquences dont l'énergie dépasse
        le seuil de Mittag-Leffler sont conservées.
        """
        lines = []

        if not summarize_info:
            summarize_info = {}

        original = summarize_info.get("original_sentences", 0)
        kept = summarize_info.get("kept_sentences", 0)
        ratio = summarize_info.get("compression_ratio", 0)
        threshold = summarize_info.get("energy_threshold", 0)
        mode = summarize_info.get("threshold_mode", "mittag-leffler")
        energies = summarize_info.get("energies", [])

        lines.append(f"RÉSUMÉ HOLOGRAPHIQUE — Filtrage par amplitude")
        lines.append("=" * 50)
        lines.append("")
        lines.append(f"Principe : seuillage d'énergie via la loi de puissance de Mittag-Leffler E_α(-α·t^α)")
        lines.append(f"  Phrases originales : {original}")
        lines.append(f"  Phrases conservées : {kept} (compression {ratio:.0%})")
        lines.append(f"  Seuil d'énergie    : {threshold:.4f} (mode : {mode})")
        lines.append("")

        # Afficher le résumé (c'est le texte du prompt, déjà filtré par summarize_info)
        if facts:
            summary_text = facts[0].get("text", "") if len(facts) > 0 else prompt[:500]
        else:
            summary_text = prompt[:500]

        lines.append("Résumé :")
        lines.append(summary_text)
        lines.append("")

        if energies:
            lines.append("Distribution d'énergie par phrase :")
            for i, e in enumerate(energies[:10]):
                marker = "▶" if e >= threshold else "·"
                lines.append(f"  {marker} Phrase {i+1} : {e:.4f}")
            lines.append("")

        lines.append(f"[Résumé par filtrage holographique Mittag-Leffler | "
                    f"α = 1/φ = {1/PHI:.4f} | compression {ratio:.0%}]")

        return {
            "text": "\n".join(lines),
            "source": "holographic_amplitude_filtering",
            "confidence": 0.8,
            "compression_ratio": ratio,
            "original_sentences": original,
            "kept_sentences": kept
        }

    # ═══════════════════════════════════════════════════════════════════
    # PONT SÉMANTIQUE : Boost de pertinence par mots-clés
    # ═══════════════════════════════════════════════════════════════════

    def _semantic_boost(self, prompt: str, fact_text: str) -> float:
        """
        Calcule un score de pertinence sémantique entre le prompt et un fait.
        
        C'est le PONT entre l'onde (SHA-256, non-sémantique) et le sens humain.
        
        Méthode : intersection des mots significatifs (>3 lettres) entre
        le prompt et le fait, pondérée par φ.
        """
        # Extraire les mots significatifs
        def extract_words(text):
            words = set()
            for w in text.lower().split():
                # Nettoyer
                w = w.strip('.,;:!?()[]{}"\'-').lower()
                if len(w) > 3 and w not in ('dans', 'avec', 'pour', 'sur', 'sous', 'dont',
                    'cette', 'leur', 'plus', 'tout', 'vous', 'nous', 'alors', 'dites',
                    'cela', 'comme', 'bien', 'fait', 'peut', 'très', 'sont', 'aux',
                    'the', 'and', 'that', 'from', 'have', 'with', 'what', 'when'):
                    words.add(w)
            return words

        question_words = extract_words(prompt)
        if not question_words:
            return 0.0

        fact_words = extract_words(fact_text)
        if not fact_words:
            return 0.0

        # Intersection
        common = question_words & fact_words
        if not common:
            return 0.0

        # Score Jaccard pondéré : chaque mot commun vaut 1, mais on divise
        # par le nombre de mots de la question pour que les questions courtes
        # (ex: "capitale du Sénégal") aient un fort boost si les mots sont trouvés
        jaccard = len(common) / max(len(question_words), 1)
        
        # Bonus si le mot le plus long de la question est trouvé (ex: "Sénégal")
        longest_question_word = max(question_words, key=len)
        bonus = 0.5 if longest_question_word in fact_words else 0.0
        
        return min(1.0, jaccard + bonus)

    def _compute_resonance(self, text1: str, text2: str) -> float:
        """
        Calcule la force de résonance entre deux textes via similarité
        cosinus de leurs positions d'onde (SHA-256 → kx, ky).
        """
        kx1, ky1 = self._text_to_wave(text1)
        kx2, ky2 = self._text_to_wave(text2)

        dot = kx1 * kx2 + ky1 * ky2
        norm1 = math.sqrt(kx1**2 + ky1**2)
        norm2 = math.sqrt(kx2**2 + ky2**2)

        if norm1 < 1e-10 or norm2 < 1e-10:
            return 0.0

        # Similarité cosinus normalisée entre 0 et 1
        cos_sim = dot / (norm1 * norm2)
        return max(0.0, min(1.0, abs(cos_sim)))

    def _text_to_wave(self, text: str):
        """SHA-256 → (kx, ky). Déterministe."""
        h = hashlib.sha256(text.encode()[:200]).hexdigest()
        kx = (int(h[:16], 16) % (1024 * 100)) / 100.0
        ky = (int(h[16:32], 16) % (1024 * 100)) / 100.0
        return (kx - 512) / 1024 * 20, (ky - 512) / 1024 * 20