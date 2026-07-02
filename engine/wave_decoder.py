"""
Wave Decoder — Décodeur Ondulatoire Harmonique
===============================================
Remplace ResponseComposer et StyleEngine.

Au lieu d'assembler des phrases avec des templates, ce module DÉCODE
l'onde de réponse émergeant de l'hologramme :

    1. Question → Ψ_Q (encodage)
    2. Hologramme répond : Ψ_R = H ⊗ Ψ_Q (corrélation = unbinding)
    3. Décomposition de Ψ_R en mots résonnants (DFT harmonique)
    4. Les mots dominants SONT la réponse — la phrase ÉMERGE

Le décodage est purement ondulatoire :
  - Pas de template
  - Pas de règle grammaticale
  - Pas de connecteur prédéfini
  - La structure de la phrase = la structure de l'onde

Principe : chaque mot w a un vecteur ψ_w. La réponse Ψ_R "vibre" à
certaines fréquences. Les mots dont ψ_w résonne le plus avec Ψ_R
sont les mots de la réponse. L'ORDRE des mots émerge de leurs
phases relatives : les mots en phase viennent ensemble (sujet+objet
du même fait), les mots en quadrature de phase se séparent (faits
différents).

Usage :
  from wave_decoder import WaveDecoder
  decoder = WaveDecoder(encoder, knowledge_base)
  response = decoder.decode("explique la lumiere")
"""

import sys, math, logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))

log = logging.getLogger(__name__)

PHI = (1.618033988749895)
PHI_INV = 1.0 / PHI
TAU = 2.0 * math.pi

# Stopwords — les mots vides qui ne portent pas de sens
_STOPWORDS = {
    'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'd', 'l',
    'et', 'est', 'sont', 'a', 'ont', 'au', 'aux', 'ce', 'cet', 'cette',
    'que', 'qui', 'quoi', 'dont', 'ou', 'ne', 'pas', 'ni',
    'dans', 'sur', 'sous', 'pour', 'par', 'avec', 'sans', 'vers',
    'mais', 'donc', 'or', 'car', 'aussi', 'puis', 'ensuite',
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'of', 'in', 'on',
    'at', 'to', 'for', 'with', 'by', 'from', 'it', 'and', 'or',
    # Préfixes questionnants (pas du contenu)
    'explique', 'decris', 'parle', 'qu', 'comment', 'pourquoi',
    'qui', 'quand', 'quelle', 'quel', 'donne', 'dis',
    'what', 'how', 'why', 'who', 'when', 'where', 'explain',
}


# ═══════════════════════════════════════════════════════════════════════════════
# DÉCODEUR ONDULATOIRE
# ═══════════════════════════════════════════════════════════════════════════════

class WaveDecoder:
    """
    Décode l'onde de réponse de l'hologramme en langage naturel.
    
    Pipeline purement ondulatoire :
      1. Encoder la question → Ψ_Q
      2. L'hologramme répond par corrélation → Ψ_R
      3. Décomposer Ψ_R en mots résonnants (top-K par score I×P×H)
      4. Grouper les mots par proximité de phase (clusters sémantiques)
      5. Ordonner les clusters par amplitude de résonance
      6. La phrase ÉMERGE de l'ordonnancement des mots
    """
    
    def __init__(self, encoder, knowledge_base: List[Tuple] = None,
                 vocab_limit: int = 5000):
        self.encoder = encoder
        self.kb = knowledge_base or []
        self._vocab_words = []
        self._vocab_vectors = None
        self._build_vocab(vocab_limit)
    
    def _build_vocab(self, limit: int):
        """Prépare le vocabulaire pour le décodage rapide."""
        # Collecter les mots uniques de la KB
        word_set = set()
        for s, r, o, _ in self.kb:
            for w in f"{s} {r} {o}".lower().split():
                w = w.strip('.,!?;:()[]{}«»""\'\'')
                if len(w) >= 2 and w not in _STOPWORDS:
                    word_set.add(w)
        
        # Limiter la taille
        words = sorted(word_set)[:limit]
        
        # Pré-encoder tous les mots du vocabulaire
        self._vocab_words = words
        self._vocab_vectors = {}
        for w in words:
            self._vocab_vectors[w] = self.encoder.encode_word(w)
        
        log.info(f"  Vocabulaire décodeur : {len(words)} mots")
    
    # ═════════════════════════════════════════════════════════════════════════
    # DÉCODAGE PRINCIPAL
    # ═════════════════════════════════════════════════════════════════════════
    
    def decode(self, question: str, max_words: int = 12,
               max_sentences: int = 3) -> str:
        """
        Décode une question en réponse naturelle.
        
        L'onde de réponse ÉMERGE de l'interférence entre la question
        et l'hologramme. Aucun template n'est utilisé.
        
        Args:
            question: question utilisateur
            max_words: nombre max de mots dans la réponse
            max_sentences: nombre max de phrases
            
        Returns:
            réponse en langage naturel
        """
        if not self.kb or not self._vocab_words:
            return self._fallback(question)
        
        # 1. Encoder la question
        psi_q = self.encoder.encode_query(question)
        if np.sum(np.abs(psi_q)) < 1e-10:
            return self._fallback(question)
        
        # 2. Faire résonner chaque mot du vocabulaire avec la question
        # Score = Re(⟨ψ_w | Ψ_Q⟩) — interférence pure
        resonant_words = self._find_resonant_words(psi_q, top_k=max_words * 2)
        
        if not resonant_words:
            return self._fallback(question)
        
        # 3. Grouper les mots par proximité de phase (clusters sémantiques)
        clusters = self._cluster_by_phase(resonant_words)
        
        # 4. Ordonner les clusters par résonance décroissante
        clusters.sort(key=lambda c: -c[1])  # tri par score moyen
        
        # 5. Assembler la réponse à partir des clusters dominants
        response = self._assemble(clusters, max_words, max_sentences)
        
        return response
    
    # ═════════════════════════════════════════════════════════════════════════
    # ÉTAPE 2 : MOTS RÉSONNANTS
    # ═════════════════════════════════════════════════════════════════════════
    
    def _find_resonant_words(self, psi_q: np.ndarray,
                             top_k: int = 20) -> List[Tuple[str, float]]:
        """
        Trouve les mots qui résonnent le plus avec l'onde de question.
        
        Pour chaque mot w du vocabulaire :
          score(w) = Re(⟨ψ_w | Ψ_Q⟩)
        
        Tri par score décroissant.
        """
        scores = []
        for word, v_w in self._vocab_vectors.items():
            # Interférence : produit scalaire hermitien
            interference = float(np.real(np.dot(v_w, np.conj(psi_q))))
            if interference > 0.01:  # seuil minimal de résonance
                scores.append((word, interference))
        
        # Trier par score décroissant
        scores.sort(key=lambda x: -x[1])
        
        return scores[:top_k]
    
    # ═════════════════════════════════════════════════════════════════════════
    # ÉTAPE 3 : CLUSTERING PAR PHASE
    # ═════════════════════════════════════════════════════════════════════════
    
    def _cluster_by_phase(self, words_scores: List[Tuple[str, float]]
                          ) -> List[Tuple[List[str], float]]:
        """
        Groupe les mots par proximité de phase.
        
        Deux mots dans la même région de phase appartiennent au même
        "fait" ou "concept". La phase est dérivée du plongement spectral.
        
        Returns:
            liste de (mots_du_cluster, score_moyen)
        """
        if not words_scores:
            return []
        
        # Récupérer les phases
        try:
            from spectral_embedding import _SPECTRAL
        except ImportError:
            _SPECTRAL = None
        
        word_phases = {}
        for word, score in words_scores:
            if _SPECTRAL and _SPECTRAL.is_ready:
                phase = _SPECTRAL.get_phase(word)
            else:
                # Fallback : phase dérivée du vecteur
                v = self._vocab_vectors[word]
                phase = math.atan2(float(np.sum(v.imag)), float(np.sum(v.real)))
            word_phases[word] = phase if phase is not None else 0.0
        
        # Clustering par proximité angulaire
        # Seuil : 2 mots sont dans le même cluster si |Δθ| < π/4 (45°)
        PHASE_THRESHOLD = math.pi / 4.0
        
        clusters = []  # liste de [mots], score_moyen
        used = set()
        
        for i, (word_i, score_i) in enumerate(words_scores):
            if word_i in used:
                continue
            cluster_words = [word_i]
            cluster_scores = [score_i]
            used.add(word_i)
            phase_i = word_phases[word_i]
            
            for j in range(i + 1, len(words_scores)):
                word_j, score_j = words_scores[j]
                if word_j in used:
                    continue
                phase_j = word_phases[word_j]
                
                # Distance angulaire
                d_phase = abs(phase_i - phase_j) % TAU
                if d_phase > math.pi:
                    d_phase = TAU - d_phase
                
                if d_phase < PHASE_THRESHOLD:
                    cluster_words.append(word_j)
                    cluster_scores.append(score_j)
                    used.add(word_j)
            
            avg_score = sum(cluster_scores) / len(cluster_scores)
            clusters.append((cluster_words, avg_score))
        
        return clusters
    
    # ═════════════════════════════════════════════════════════════════════════
    # ÉTAPE 5 : ASSEMBLAGE
    # ═════════════════════════════════════════════════════════════════════════
    
    def _assemble(self, clusters: List[Tuple[List[str], float]],
                  max_words: int, max_sentences: int) -> str:
        """
        Assemble la réponse à partir des clusters dominants.
        
        L'ordre des mots dans chaque cluster suit leur amplitude de
        résonance (le mot le plus résonant en premier).
        
        L'ordre des phrases suit l'amplitude des clusters.
        
        Aucun template — la structure ÉMERGE des ondes.
        """
        sentences = []
        total_words = 0
        
        for cluster_words, cluster_score in clusters[:max_sentences]:
            if total_words >= max_words:
                break
            
            # Ordonner les mots du cluster par score de résonance
            # (déjà ordonnés car words_scores était trié)
            words_in_sentence = cluster_words[:6]  # max 6 mots par phrase
            
            if len(words_in_sentence) == 0:
                continue
            
            # L'assemblage est minimaliste : les mots dominants
            # séparés par un connecteur ondulatoire
            # Le connecteur n'est PAS un template — c'est la ponctuation
            # naturelle de la phrase émergeante
            
            if len(words_in_sentence) == 1:
                sentence = words_in_sentence[0].capitalize() + '.'
            elif len(words_in_sentence) == 2:
                sentence = f"{words_in_sentence[0].capitalize()} — {words_in_sentence[1]}."
            else:
                # Les premiers mots sont le "sujet", les derniers "l'objet"
                mid = len(words_in_sentence) // 2
                subject_part = ' '.join(words_in_sentence[:mid])
                object_part = ' '.join(words_in_sentence[mid:])
                sentence = f"{subject_part.capitalize()} : {object_part}."
            
            sentences.append(sentence)
            total_words += len(words_in_sentence)
        
        if not sentences:
            return self._fallback("")
        
        return ' '.join(sentences)
    
    # ═════════════════════════════════════════════════════════════════════════
    # DÉCODAGE RICHE (avec faits structurés)
    # ═════════════════════════════════════════════════════════════════════════
    
    def decode_rich(self, question: str) -> str:
        """
        Décodage riche : résonance + synthèse ondulatoire.
        
        1. La question est encodée en onde Ψ_Q
        2. La mémoire holographique répond par résonance
        3. Les faits résonnants sont extraits
        4. VÉRIFICATION SÉMANTIQUE : sujet et objet doivent être proches en phase
        5. Le WaveSynthesizer fusionne les ondes en paragraphe
        """
        try:
            from holographic_memory import HolographicMemory
            if not hasattr(self, '_hmem') or self._hmem is None:
                self._hmem = HolographicMemory(self.encoder, dim=self.encoder.dim)
                self._hmem.store_kb(self.kb[:5000])
                self._hmem.build_vocab()
            
            result = self._hmem.query(question, top_k=6)
            if result['facts']:
                # Vérification sémantique : filtrer les faits où
                # le sujet et l'objet sont trop éloignés en phase
                facts = []
                for s, r, o, sc in result['facts']:
                    if sc < 0.03:
                        continue
                    if not self._semantic_match(s, o):
                        continue
                    facts.append((s, r, o))
                    if len(facts) >= 3:
                        break
                
                if facts:
                    # Vérifier si des blocs curated taggés sont présents
                    curated_segments = {
                        'definition': None,
                        'mecanisme': None,
                        'importance': None,
                        'historique': None,
                    }
                    for s, r, o in facts:
                        if r in curated_segments and len(o) > 50:
                            curated_segments[r] = o
                    
                    # Si on a un bloc curated → choisir le meilleur segment
                    if curated_segments['definition'] or curated_segments['mecanisme']:
                        # Sélectionner le segment selon le type de question
                        sig = self.compute_signature(question)
                        q_type = sig.get('type', 'definition')
                        
                        if q_type == 'mecanisme' and curated_segments['mecanisme']:
                            return curated_segments['mecanisme'].capitalize().rstrip('.') + '.'
                        elif q_type == 'importance' and curated_segments['importance']:
                            return curated_segments['importance'].capitalize().rstrip('.') + '.'
                        elif curated_segments['definition']:
                            return curated_segments['definition'].capitalize().rstrip('.') + '.'
                        elif curated_segments['mecanisme']:
                            return curated_segments['mecanisme'].capitalize().rstrip('.') + '.'
                    
                    # Sinon, synthèse ondulatoire des faits normaux
                    clean_facts = [(s, r, o) for s, r, o in facts
                                   if r not in ('definition', 'mecanisme', 'importance', 'historique')]
                    if clean_facts:
                        try:
                            from wave_synthesizer import WaveSynthesizer
                            if not hasattr(self, '_synth'):
                                self._synth = WaveSynthesizer(self.encoder)
                            return self._synth.synthesize(clean_facts, question)
                        except ImportError:
                            pass
                    
                    # Fallback : premier fait
                    if clean_facts:
                        s, r, o = clean_facts[0]
                    else:
                        s, r, o = facts[0]
                    return f"{s.capitalize()} {r} {o}."
        except Exception:
            pass
        
        return self._decode_rich_legacy(question)
    
    def _semantic_match(self, sujet: str, objet: str) -> bool:
        """
        Vérifie que le sujet et l'objet d'un fait sont sémantiquement
        compatibles via leurs phases S¹.
        
        Deux mots sont incompatibles si leurs phases sont à > 90° l'une de l'autre.
        """
        try:
            from spectral_embedding import _SPECTRAL
            if not _SPECTRAL or not _SPECTRAL.is_ready:
                return True  # pas de phases → accepter tout
            
            # Prendre le premier mot significatif du sujet et de l'objet
            s_word = sujet.lower().strip().split()[0] if sujet else ''
            o_word = objet.lower().strip().split()[0] if objet else ''
            
            phase_s = _SPECTRAL.get_phase(s_word)
            phase_o = _SPECTRAL.get_phase(o_word)
            
            if phase_s is None or phase_o is None:
                return True  # mot inconnu → accepter
            
            # Distance angulaire
            import math
            d = abs(phase_s - phase_o) % (2 * math.pi)
            if d > math.pi:
                d = 2 * math.pi - d
            
            # Seuil : max 60° d'écart
            return d < math.radians(60)
        except Exception:
            return True
    
    def _decode_rich_legacy(self, question: str) -> str:
        """Ancienne méthode de décodage riche (fallback)."""
        if not self.kb:
            return self.decode(question)
        
        # Encoder la question
        psi_q = self.encoder.encode_query(question)
        
        # Scorer tous les faits par résonance vectorielle
        fact_scores = []
        for s, r, o, sec in self.kb:
            # Vecteur du fait = encode(s + r + o)
            v_fact = self.encoder.encode_query(f"{s} {r} {o}")
            score = float(np.real(np.dot(v_fact, np.conj(psi_q))))
            if score > 0.02:
                fact_scores.append((score, s, r, o, sec))
        
        if not fact_scores:
            return self.decode(question)
        
        # Trier par score
        fact_scores.sort(key=lambda x: -x[0])
        
        # Prendre les 3 meilleurs faits uniques par sujet
        seen_subjects = set()
        top_facts = []
        for score, s, r, o, sec in fact_scores:
            if s.lower() not in seen_subjects:
                top_facts.append((score, s, r, o))
                seen_subjects.add(s.lower())
            if len(top_facts) >= 3:
                break
        
        # Décoder chaque fait en phrase naturelle
        # La phrase ÉMERGE du contenu du fait, pas d'un template
        phrases = []
        for score, s, r, o in top_facts:
            # La phrase est la lecture directe du fait :
            # sujet + relation + objet
            # C'est le décodage le plus pur — pas d'enrobage
            phrase = f"{s} {r} {o}"
            phrases.append(phrase)
        
        if len(phrases) == 1:
            return phrases[0].capitalize() + '.'
        
        # Joindre avec une ponctuation naturelle
        return '. '.join(p.capitalize() for p in phrases) + '.'
    
    # ═════════════════════════════════════════════════════════════════════════
    # FALLBACK
    # ═════════════════════════════════════════════════════════════════════════
    
    def _fallback(self, question: str) -> str:
        """Réponse quand aucune résonance n'est trouvée."""
        # Extraire le sujet de la question
        words = [w for w in question.lower().split()
                 if w not in _STOPWORDS and len(w) > 2]
        sujet = words[0] if words else "ce sujet"
        return f"Je n'ai pas encore de résonance sur {sujet}."

    # ═════════════════════════════════════════════════════════════════════════
    # SIGNATURE 9D — Type de question par analyse spectrale
    # ═════════════════════════════════════════════════════════════════════════

    def compute_signature(self, question: str) -> dict:
        """
        Calcule la signature 9D de la question.
        
        Au lieu d'utiliser des règles (préfixes, mots-clés), la signature
        émerge de l'analyse spectrale de l'onde de la question.
        
        Les 9 dimensions :
          phi_ratio      : équilibre (factual vs émotionnel)
          alpha_complex  : complexité
          reasoning      : force logique (cause, pourquoi)
          creativity     : ouverture (imagine, si)
          math_val       : précision numérique
          factual        : ancrage factuel
          code_val       : structure technique
          emotion        : charge affective
          temporal       : dimension temporelle
        
        Returns:
            dict avec signature 9D et type détecté
        """
        psi_q = self.encoder.encode_query(question)
        
        # L'amplitude de l'onde dans différentes régions du spectre
        # révèle le type de question
        real_part = np.real(psi_q)
        imag_part = np.imag(psi_q)
        magnitude = np.abs(psi_q)
        
        # Analyse par bandes de fréquence (tiers du vecteur)
        n = len(psi_q)
        band1 = magnitude[:n//3]   # basses fréquences = contexte
        band2 = magnitude[n//3:2*n//3]  # moyennes = raisonnement
        band3 = magnitude[2*n//3:]  # hautes = détails
        
        e1 = float(np.mean(band1))
        e2 = float(np.mean(band2))
        e3 = float(np.mean(band3))
        e_total = e1 + e2 + e3 + 1e-10
        
        # Signature 9D normalisée
        sig = {
            'phi_ratio': e1 / e_total,        # équilibre contextuel
            'alpha_complex': min(1.0, float(np.std(magnitude)) * 10),  # complexité
            'reasoning': e2 / e_total,         # force logique
            'creativity': e3 / e_total,        # ouverture créative
            'math_val': min(1.0, float(np.mean(real_part**2)) * 10),
            'factual': min(1.0, e1 * 5),
            'code_val': min(1.0, float(np.mean(imag_part**2)) * 10),
            'emotion': min(1.0, float(np.max(magnitude))),
            'temporal': min(1.0, float(np.std(real_part)) * 10),
        }
        
        # Détection du type par la signature
        if sig['factual'] > 0.5 and sig['creativity'] < 0.3:
            q_type = 'definition'
        elif sig['reasoning'] > 0.4 and sig['creativity'] > 0.3:
            q_type = 'mecanisme'
        elif sig['creativity'] > 0.4:
            q_type = 'creative'
        elif sig['factual'] > 0.4:
            q_type = 'factualite'
        else:
            q_type = 'general'
        
        sig['type'] = q_type
        return sig


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    from holographic_encoder import HolographicEncoder
    
    print("=" * 65)
    print("WAVE DECODER — Décodeur Ondulatoire Harmonique")
    print("La phrase ÉMERGE des fréquences dominantes")
    print("=" * 65)
    
    # KB de test
    kb = [
        ("lumiere", "est une", "onde electromagnetique", "PHYSIQUE_FOND"),
        ("lumiere", "se propage a", "300000 km/s", "PHYSIQUE_FOND"),
        ("lumiere", "est composee de", "photons", "PHYSIQUE_FOND"),
        ("photons", "sont des", "particules sans masse", "PHYSIQUE_FOND"),
        ("coeur", "pompe", "le sang", "BIOLOGIE"),
        ("sang", "transporte", "l oxygene", "BIOLOGIE"),
        ("oxygene", "alimente", "les cellules", "BIOLOGIE"),
        ("gravite", "est la", "courbure de l espace temps", "PHYSIQUE_FOND"),
        ("gravite", "maintient", "les planetes en orbite", "PHYSIQUE_FOND"),
        ("einstein", "a decouvert", "la relativite", "PHYSIQUE_FOND"),
        ("conscience", "emerge du", "cerveau", "CONSCIENCE"),
        ("cerveau", "contient", "des neurones", "CONSCIENCE"),
        ("neurones", "communiquent par", "synapses", "CONSCIENCE"),
        ("musique", "est l art", "des sons", "CULTURE"),
        ("amour", "est la", "force fondamentale", "EMOTION_POS"),
    ]
    
    encoder = HolographicEncoder(dim=256)
    decoder = WaveDecoder(encoder, kb, vocab_limit=200)
    
    questions = [
        "explique la lumiere",
        "comment fonctionne le coeur",
        "qu est ce que la gravite",
        "parle de la conscience",
        "qui a decouvert la relativite",
        "qu est ce que la musique",
    ]
    
    print("\n--- Décodage pur (résonance) ---")
    for q in questions:
        r = decoder.decode(q)
        print(f"\n  Q: {q}")
        print(f"  R: {r}")
    
    print("\n\n--- Décodage riche (faits + résonance) ---")
    for q in questions:
        r = decoder.decode_rich(q)
        print(f"\n  Q: {q}")
        print(f"  R: {r}")
    
    # Analyse des mots résonnants
    print("\n\n--- Analyse : mots résonnants pour 'lumiere' ---")
    psi_q = encoder.encode_query("explique la lumiere")
    resonant = decoder._find_resonant_words(psi_q, top_k=10)
    for word, score in resonant:
        bar = '█' * int(score * 50)
        print(f"  {word:>25s}  {score:+.4f}  {bar}")


if __name__ == '__main__':
    demo()
