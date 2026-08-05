"""
Holographic Retriever — Retrieval par interférence d'ondes HRR
================================================================
Solution structurelle : utiliser l'encodeur holographique pour
retrouver les faits par RÉSONANCE I×P×H, pas par mots-clés.

Pipeline :
  1. Au démarrage : encoder TOUS les faits de la KB dans l'hologramme
  2. À chaque question : encoder la requête en vecteur
  3. Pour chaque fait : calculer le score de résonance I×P×H
  4. Retourner les top-k faits par score

C'est EXACTEMENT le principe de la théorie harmonique :
  question = onde → hologramme → résonance → réponse

Usage:
    from holographic_retriever import HolographicRetriever
    
    retriever = HolographicRetriever(kb)   # build une fois
    facts = retriever.retrieve(question)    # query rapide
"""

import math
import re
import numpy as np
from typing import List, Tuple, Dict, Optional


class HolographicRetriever:
    """
    Retrieval de faits par résonance holographique.
    
    Utilise l'encodeur HRR pour :
    1. Encoder chaque fait de la KB comme vecteur composite (s⊗r⊗o)
    2. Encoder la question comme vecteur de requête
    3. Calculer la résonance (produit scalaire complexe) entre requête et chaque fait
    4. Le fait avec la plus haute résonance est le plus pertinent
    
    Avantage vs keyword matching :
    - "chute du mur de Berlin" ne résonne PAS avec "chute de Constantinople"
      car les vecteurs de "mur de Berlin" et "Constantinople" sont orthogonaux
    - "Mona Lisa" résonne avec "Joconde" car les vecteurs sont proches
      (les mots partagent des composantes phonétiques/sémantiques)
    """
    
    STOPWORDS = {
        'le','la','les','un','une','des','de','du','d','l',
        'et','est','sont','a','ont','au','aux','ce','cet','cette','ces',
        'que','qui','quoi','dont','ou','ne','pas','ni',
        'dans','sur','sous','pour','par','avec','sans','vers',
        'mais','donc','or','car','aussi','puis','ensuite',
        'mon','ma','mes','ton','ta','tes','son','sa','ses',
        'notre','votre','leur','leurs',
        'tres','trop','encore','deja',
        'tu','vous','nous','on','il','elle','ils','elles',
        'quand','comment','pourquoi',
        'the','a','an','is','are','was','were','be','been','being',
        'have','has','had','do','does','did','will','would','could',
        'should','may','might','can','shall',
        'of','in','on','at','to','for','with','by','from',
        'it','its','and','or','not','but','if','so','as','than',
        'that','this','these','those','which','who','whom','whose',
        'i','you','he','she','we','they','me','him','her','us','them',
        'my','your','his','our','their',
        'explain','describe','tell','give','say','make',
        'le','la','les','un','une','des','de','du',
        'que','qui','quoi','dont','ou','ne','pas',
        'dans','sur','pour','par','avec','sans',
    }
    # Note: on retire 'what','when','where','why','how' des stopwords
    # parce qu'ils sont des mots-clés utiles pour la retrieval
    
    def __init__(self, knowledge_base: List[Tuple], dim: int = 512):
        """
        Construit le retriever holographique.
        
        Args:
            knowledge_base : liste de (sujet, relation, objet, secteur)
            dim : dimension des vecteurs complexes (D=512 par défaut)
        """
        self.kb = list(knowledge_base)
        self.dim = dim
        
        # L'encodeur HRR
        from holographic_encoder import HolographicEncoder
        self.encoder = HolographicEncoder()
        
        # Index des vecteurs de faits (pré-calculés)
        self.fact_vectors: List[np.ndarray] = []
        self._word_cache: Dict[str, np.ndarray] = {}
        
        # Construire les vecteurs de faits
        self._build_fact_vectors()
    
    def _encode_word_cached(self, word: str) -> np.ndarray:
        """Encode un mot avec cache."""
        w = word.lower().strip()
        if w not in self._word_cache:
            self._word_cache[w] = self.encoder.encode_word(w)
        return self._word_cache[w]
    
    def _encode_text(self, text: str) -> np.ndarray:
        """
        Encode un texte multi-mots en vecteur composite.
        Stratégie : superposition (somme) des vecteurs de mots.
        """
        words = text.lower().split()
        vecs = []
        for w in words:
            w = w.strip('.,!?;:()[]{}""\'\'¿¡')
            if len(w) < 2 or w in self.STOPWORDS:
                continue
            vecs.append(self._encode_word_cached(w))
        
        if not vecs:
            return np.zeros(self.dim, dtype=np.complex128)
        
        # Superposition (somme) puis normalisation
        result = np.sum(vecs, axis=0)
        norm = np.linalg.norm(result)
        if norm > 0:
            result = result / norm
        return result
    
    def _build_fact_vectors(self):
        """
        Pré-calcule le vecteur de chaque fait.
        fait_vec = superposition(sujet, relation, objet)
        
        On utilise la superposition (pas le binding) pour la retrieval
        parce qu'on cherche une RÉSONANCE générale, pas un unbinding exact.
        """
        for s, r, o, sec in self.kb:
            # Vecteur du fait = superposition des mots significatifs
            text = s + ' ' + r + ' ' + o
            vec = self._encode_text(text)
            self.fact_vectors.append(vec)
        
        # Matrice pour calcul vectorisé
        if self.fact_vectors:
            self.fact_matrix = np.array(self.fact_vectors)  # shape (N, D)
        else:
            self.fact_matrix = np.zeros((0, self.dim), dtype=np.complex128)
    
    def retrieve(self, question: str, max_results: int = 5,
                 pre_filter: int = 100) -> List[Tuple]:
        """
        Retrouve les faits par résonance holographique.
        
        Le sujet est extrait de la question puis utilisé pour le pre-filter
        et le scoring.
        """
        if len(self.kb) == 0:
            return []
        
        # 0. EXTRAIRE LE SUJET de la question (retirer préfixes)
        q_lower = question.lower().strip()
        sujet = q_lower
        prefixes = [
            'what is the ', 'what is a ', 'what is an ', 'what is ', 'what are ',
            'who is ', 'who was ', 'who wrote ', 'who painted ', 'who discovered ',
            'who invented ', 'who created ', 'who founded ', 'who composed ',
            'when did ', 'when was ', 'when ', 'where is ', 'where are ', 'where ',
            'why is ', 'why does ', 'why do ', 'why ', 'how does ', 'how do ',
            'how to ', 'how ', 'explain ', 'describe ', 'define ',
            'tell me about ', 'tell me ', 'can you help me understand ',
            'can you ', 'help me ', 'name three ', 'name ',
            'is ', 'are ', 'the ', 'a ', 'an ',
            "qu'est ce que ", "qu'est-ce que ", 'qu est ce que ',
            'qui a ecrit ', 'qui a peint ', 'qui a decouvert ',
            'qui a invente ', 'qui a cree ', 'qui a fonde ',
            'qui a compose ', 'qui est ', 'qui etait ',
            'quand ', 'ou ', 'pourquoi ', 'comment ',
            'explique ', 'definis ', 'parle de ', 'parle moi de ',
            'quelle est la capitale de ', 'quel est la capitale de ',
            'capitale de ', 'capital of ', 'donne moi ',
        ]
        for prefix in sorted(prefixes, key=len, reverse=True):
            if sujet.startswith(prefix):
                sujet = sujet[len(prefix):].strip()
                break
        sujet = sujet.strip('?.,!;:')
        
        # 1. MOTS-CLÉS de la question (tous les mots significatifs)
        all_q_words = [w for w in q_lower.split()
                       if len(w) >= 2 and w not in self.STOPWORDS]
        q_word_set = set(all_q_words)
        
        # 2. PRE-FILTER : tous les faits contenant au moins 1 mot-clé du sujet
        sujet_words = [w for w in sujet.split() if len(w) >= 2 and w not in self.STOPWORDS]
        
        # ÉLARGIR : inclure tous les mots de la question originale
        all_q_words = list(q_word_set) + sujet_words
        
        # Pre-filter rapide : chercher les faits avec au moins 1 mot-clé
        candidate_ids_set = set()
        for fid, (s, r, o, sec) in enumerate(self.kb):
            combined = (s + ' ' + r + ' ' + o).lower()
            
            # Cas spécial : sujet EXACT dans le sujet ou l'objet du fait
            if sujet and (sujet in s.lower() or sujet in o.lower()):
                candidate_ids_set.add(fid)
                continue
            
            # Sinon : au moins 1 mot-clé
            if any(kw in combined for kw in all_q_words):
                candidate_ids_set.add(fid)
        
        # Si trop peu de candidats, élargir aux mots de 2 lettres
        if len(candidate_ids_set) < 5:
            all_q_words_short = [w for w in q_lower.split() if len(w) >= 2 and w not in self.STOPWORDS]
            for fid, (s, r, o, sec) in enumerate(self.kb):
                combined = (s + ' ' + r + ' ' + o).lower()
                if any(kw in combined for kw in all_q_words_short):
                    candidate_ids_set.add(fid)
        
        candidate_ids = list(candidate_ids_set)[:pre_filter]
        
        if not candidate_ids:
            return []
        
        # 3. ENCODER LA QUESTION et calculer la résonance
        q_vec = self._encode_text(question)
        
        scored = []
        for fid in candidate_ids:
            fact_vec = self.fact_vectors[fid]
            
            # Résonance = Re(<q | fact>)
            resonance = float(np.real(np.dot(np.conj(q_vec), fact_vec)))
            
            # BONUS : match du sujet dans le fait
            s, r, o, sec = self.kb[fid]
            s_lower = s.lower()
            o_lower = o.lower()
            
            sujet_score = 0
            for sw in sujet_words:
                if sw in s_lower.split():
                    sujet_score += 1.0  # match exact dans le sujet
                elif sw in o_lower.split():
                    sujet_score += 0.5  # match dans l'objet
            
            # PÉNALITÉ : collision de nombres
            penalty = 1.0
            q_numbers = [w for w in all_q_words if w.isdigit()]
            if q_numbers:
                combined = (s + ' ' + r + ' ' + o).lower()
                for qn in q_numbers:
                    for fw in combined.split():
                        if fw.isdigit() and fw != qn:
                            penalty *= 0.1
            
            total_score = (resonance + sujet_score * 0.5) * penalty
            scored.append((total_score, fid))
        
        # 4. TRIER
        scored.sort(key=lambda x: -x[0])
        
        # 5. DÉDUPLIQUER
        results = []
        seen = set()
        for score, fid in scored:
            fact = self.kb[fid]
            if fact[0] not in seen:
                results.append(fact)
                seen.add(fact[0])
            if len(results) >= max_results:
                break
        
        return results
    
    def retrieve_with_iph(self, question: str, max_results: int = 5) -> List[Tuple]:
        """
        Retrieval utilisant le score I×P×H complet.
        
        Plus précis mais plus lent (calcul P et H pour chaque mot).
        """
        # Pre-filter par keyword
        q_words = set(w for w in question.lower().split()
                      if len(w) >= 3 and w not in self.STOPWORDS)
        
        candidate_ids = set()
        for fid, (s, r, o, sec) in enumerate(self.kb):
            combined = (s + ' ' + r + ' ' + o).lower()
            if any(kw in combined for kw in q_words):
                candidate_ids.add(fid)
        
        if not candidate_ids:
            return []
        
        candidate_ids = list(candidate_ids)[:50]
        
        # Encoder la question
        q_vec = self._encode_text(question)
        
        # Pour chaque candidat, calculer I×P×H
        scored = []
        for fid in candidate_ids:
            s, r, o, sec = self.kb[fid]
            
            # I : interférence (cosine similarity)
            fact_vec = self.fact_vectors[fid]
            dot = np.real(np.dot(np.conj(q_vec), fact_vec))
            I = (dot + 1.0) / 2.0
            
            # P : cohérence de phase
            # Comparer la phase du fait avec la phase de la question
            if self.encoder.n_facts > 5:
                mem_resp = np.dot(self.encoder.memory, np.conj(fact_vec))
                phase_diff = abs(np.angle(mem_resp))
                if phase_diff > math.pi:
                    phase_diff = 2 * math.pi - phase_diff
                P = (math.cos(phase_diff) + 1.0) / 2.0
            else:
                P = 0.5
            
            # H : amplitude holographique
            mem_amp = np.abs(np.dot(self.encoder.memory, np.conj(fact_vec)))
            H = min(1.0, math.log1p(mem_amp * 10.0) / math.log1p(10.0))
            
            # Score I×P×H
            score = I * (0.3 + 0.4 * P + 0.3 * H)
            
            # Bonus sujet
            s_lower = s.lower()
            for qw in q_words:
                if qw in s_lower:
                    score += 0.1
            
            scored.append((score, fid))
        
        scored.sort(key=lambda x: -x[0])
        
        results = []
        seen = set()
        for score, fid in scored:
            fact = self.kb[fid]
            if fact[0] not in seen:
                results.append(fact)
                seen.add(fact[0])
            if len(results) >= max_results:
                break
        
        return results
