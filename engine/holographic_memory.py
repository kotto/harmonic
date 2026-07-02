"""
Holographic Memory — Mémoire holographique structurée
=====================================================
Stocke les faits comme ondes (binding HRR) dans l'hologramme,
avec une architecture N×64×64 pour une scalabilité linéaire.

Principe ondulatoire :
  fait = ψ_s ⊛ ψ_r ⊛ ψ_o    (binding par convolution circulaire)
  mémoire = Σ faits          (superposition additive)
  requête = ψ_q
  réponse = mémoire ⊗ ψ_q    (unbinding = corrélation circulaire)

Architecture multi-hologrammes :
  Au lieu d'un seul hologramme géant (où les faits se brouillent),
  on utilise N hologrammes par SECTEUR (PHYSIQUE, BIOLOGIE, etc.).
  Le secteur est déterminé par la PHASE θ du sujet.
  
  Chaque hologramme a une capacité de ~144 concepts (grille 64×64).
  N=1000 hologrammes → 144 000 concepts, 64 Mo.

Usage :
  from holographic_memory import HolographicMemory
  mem = HolographicMemory(encoder, dim=512)
  mem.store('lumiere', 'est une', 'onde electromagnetique')
  mem.store('coeur', 'pompe', 'le sang')
  
  result = mem.query('explique la lumiere')
  # result.top_words = [('lumiere', 0.9), ('onde', 0.7), ...]
"""

import sys, math, logging
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))

log = logging.getLogger(__name__)

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI
TAU = 2.0 * math.pi


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPALE
# ═══════════════════════════════════════════════════════════════════════════════

class HolographicMemory:
    """
    Mémoire holographique multi-secteurs.
    
    Au lieu de superposer TOUS les faits dans un seul vecteur
    (ce qui crée du bruit croisé), on maintient :
      1. Un hologramme global (pour la recherche par résonance)
      2. Un index par sujet (pour la récupération précise)
    
    La recherche se fait en deux phases :
      Phase 1 : Trouver les sujets qui résonnent avec la question
      Phase 2 : Pour chaque sujet résonant, récupérer ses faits par unbinding
    """
    
    def __init__(self, encoder, dim: int = 512):
        self.encoder = encoder
        self.dim = dim
        
        # Index par sujet : sujet → liste de (relation, objet)
        self._index: Dict[str, List[Tuple[str, str, np.ndarray]]] = defaultdict(list)
        
        # Vecteur de sujet (pour la recherche par résonance)
        self._subject_vectors: Dict[str, np.ndarray] = {}
        
        # Hologramme global (superposition de TOUS les faits)
        self._hologram: np.ndarray = np.zeros(dim, dtype=np.complex128)
        self._n_facts: int = 0
        
        # Vocabulaire pré-encodé pour le décodage rapide
        self._vocab_words: List[str] = []
        self._vocab_matrix: Optional[np.ndarray] = None
    
    # ═════════════════════════════════════════════════════════════════════════
    # STOCKAGE
    # ═════════════════════════════════════════════════════════════════════════
    
    def store(self, sujet: str, relation: str, objet: str):
        """
        Stocke un fait comme onde dans la mémoire.
        
        1. Encode chaque composant : ψ_s, ψ_r, ψ_o
        2. Bind : fait = ψ_s ⊛ ψ_r ⊛ ψ_o
        3. Superpose : hologramme += fait
        4. Indexe : sujet → (relation, objet, vecteur_fait)
        """
        v_s = self.encoder.encode_word(sujet.lower())
        v_r = self.encoder.encode_word(relation.lower())
        v_o = self.encoder.encode_word(objet.lower())
        
        # Binding HRR : convolution circulaire
        fact_vec = self._bind3(v_s, v_r, v_o)
        
        # Superposition
        self._hologram += fact_vec
        self._n_facts += 1
        
        # Indexage
        sujet_lower = sujet.lower().strip()
        self._index[sujet_lower].append((relation.lower(), objet.lower(), fact_vec))
        
        if sujet_lower not in self._subject_vectors:
            self._subject_vectors[sujet_lower] = v_s
    
    def store_kb(self, knowledge_base: List[Tuple[str, str, str, str]]):
        """Stocke toute la base de connaissance."""
        for s, r, o, sec in knowledge_base:
            self.store(s, r, o)
        log.info(f"  Mémoire holographique : {self._n_facts} faits stockés")
    
    def store_kb_weighted(self, knowledge_base: List[Tuple[str, str, str, str]],
                           curated_subjects: set = None, boost: float = 5.0):
        """
        Stocke la KB avec un boost pour les sujets curated.
        
        Les faits dont le sujet est dans curated_subjects sont stockés
        avec une amplitude boost× normale → ils dominent la résonance.
        
        Args:
            knowledge_base: faits (sujet, relation, objet, secteur)
            curated_subjects: ensemble de sujets à booster
            boost: facteur d'amplification (5.0 = 5× plus fort)
        """
        curated_subjects = curated_subjects or set()
        curated_count = 0
        
        for s, r, o, sec in knowledge_base:
            v_s = self.encoder.encode_word(s.lower())
            v_r = self.encoder.encode_word(r.lower())
            v_o = self.encoder.encode_word(o.lower())
            
            fact_vec = self._bind3(v_s, v_r, v_o)
            
            # Booster les faits curated
            amplitude = boost if s.lower().strip() in curated_subjects else 1.0
            self._hologram += amplitude * fact_vec
            
            s_lower = s.lower().strip()
            self._index[s_lower].append((r.lower(), o.lower(), fact_vec))
            
            if s_lower not in self._subject_vectors:
                self._subject_vectors[s_lower] = v_s
            
            if amplitude > 1.0:
                curated_count += 1
        
        self._n_facts = len(knowledge_base)
        log.info(f"  Mémoire holographique : {self._n_facts} faits "
                 f"({curated_count} boostés ×{boost:.0f})")
    
    def inject_curated_block(self, sujet: str, block_text: str,
                              boost: float = 3.0, segment_type: str = 'definition'):
        """
        Injecte un bloc curated directement comme onde dans l'hologramme.
        
        Args:
            sujet: sujet du bloc
            block_text: texte du bloc (1-5 phrases)
            boost: facteur d'amplification
            segment_type: 'definition' | 'mecanisme' | 'importance' | 'historique'
        """
        import re
        phrases = re.split(r'[.!?]\s+', block_text)
        
        sujet_lower = sujet.lower().strip()
        v_s = self.encoder.encode_word(sujet_lower)
        
        for phrase in phrases:
            phrase = phrase.strip()
            if len(phrase) < 10:
                continue
            
            psi = self.encoder.encode_query(phrase)
            self._hologram += boost * psi
            
            # Stocker avec le type de segment comme relation
            self._index[sujet_lower].append(
                (segment_type, phrase, boost * psi)
            )
        
        if sujet_lower not in self._subject_vectors:
            self._subject_vectors[sujet_lower] = v_s
        
        self._n_facts += 1
    
    def _bind3(self, a, b, c):
        """Binding triple par double convolution : a ⊛ b ⊛ c."""
        from holographic_encoder import _circular_convolve
        return _circular_convolve(_circular_convolve(a, b), c)
    
    # ═════════════════════════════════════════════════════════════════════════
    # RECHERCHE PAR SUJET
    # ═════════════════════════════════════════════════════════════════════════
    
    def find_resonant_subjects(self, query_vector: np.ndarray,
                                top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Trouve les sujets qui résonnent le plus avec la requête.
        
        Pour chaque sujet connu :
          score = Re(⟨ψ_sujet | Ψ_Q⟩)
        
        Tri par score décroissant.
        """
        scores = []
        for sujet, v_s in self._subject_vectors.items():
            score = float(np.real(np.dot(v_s, np.conj(query_vector))))
            if score > 0.01:
                scores.append((sujet, score))
        
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]
    
    def retrieve_subject_facts(self, sujet: str) -> List[Tuple[str, str]]:
        """
        Récupère tous les faits d'un sujet.
        
        Comme on indexe les faits par sujet, la récupération est
        exacte (pas de bruit croisé de l'hologramme).
        """
        return [(r, o) for r, o, _ in self._index.get(sujet.lower().strip(), [])]
    
    # ═════════════════════════════════════════════════════════════════════════
    # RECHERCHE COMPLÈTE (query → réponse)
    # ═════════════════════════════════════════════════════════════════════════
    
    def query(self, question: str, top_k: int = 5) -> Dict:
        """
        Requête complète : question → faits résonnants.
        
        1. Encoder la question → Ψ_Q
        2. Trouver les sujets résonnants
        3. Pour chaque sujet, récupérer ses faits
        4. Scorer chaque fait par résonance avec Ψ_Q
        5. Retourner les top-K faits
        
        Returns:
            Dict avec :
              - 'facts': liste de (sujet, relation, objet, score)
              - 'subjects': sujets résonnants
              - 'query_vector': vecteur de la question
        """
        # 1. Encoder
        psi_q = self.encoder.encode_query(question)
        
        if np.sum(np.abs(psi_q)) < 1e-10:
            return {'facts': [], 'subjects': [], 'query_vector': psi_q}
        
        # 2. Sujets résonnants
        resonant_subjects = self.find_resonant_subjects(psi_q, top_k=top_k)
        
        if not resonant_subjects:
            # Fallback : chercher dans l'hologramme global
            return self._query_global(psi_q, top_k)
        
        # 3-4. Récupérer et scorer les faits
        all_facts = []
        for sujet, subj_score in resonant_subjects:
            facts = self.retrieve_subject_facts(sujet)
            for relation, objet in facts:
                # Score du fait = résonance de l'objet avec la question
                v_o = self.encoder.encode_word(objet)
                obj_score = float(np.real(np.dot(v_o, np.conj(psi_q))))
                # Score combiné : sujet × objet
                combined = subj_score * 0.5 + max(0, obj_score) * 0.5
                all_facts.append((sujet, relation, objet, combined))
        
        # 5. Trier
        all_facts.sort(key=lambda x: -x[3])
        
        # Dédupliquer par (sujet, objet)
        seen = set()
        unique_facts = []
        for s, r, o, sc in all_facts:
            key = (s, o)
            if key not in seen:
                seen.add(key)
                unique_facts.append((s, r, o, sc))
        
        return {
            'facts': unique_facts[:top_k],
            'subjects': [s for s, _ in resonant_subjects],
            'query_vector': psi_q,
        }
    
    def _query_global(self, psi_q: np.ndarray, top_k: int) -> Dict:
        """
        Requête dans l'hologramme global (quand aucun sujet ne résonne).
        
        Unbinding : réponse = hologramme ⊗ Ψ_Q
        Puis décodage : quels mots résonnent avec la réponse ?
        """
        from holographic_encoder import _circular_correlate
        
        # Unbinding
        response = _circular_correlate(self._hologram, psi_q)
        
        # Décoder les mots résonnants
        if self._vocab_matrix is not None:
            scores = np.real(self._vocab_matrix @ np.conj(response))
            top_idx = np.argsort(-scores)[:top_k]
            facts = []
            for idx in top_idx:
                if scores[idx] > 0.01:
                    word = self._vocab_words[idx]
                    facts.append((word, '?', word, float(scores[idx])))
            return {'facts': facts, 'subjects': [], 'query_vector': psi_q}
        
        return {'facts': [], 'subjects': [], 'query_vector': psi_q}
    
    # ═════════════════════════════════════════════════════════════════════════
    # GESTION DU VOCABULAIRE
    # ═════════════════════════════════════════════════════════════════════════
    
    def build_vocab(self, max_words: int = 3000):
        """
        Construit la matrice de vocabulaire pour le décodage rapide.
        Doit être appelé après store_kb().
        """
        word_set = set()
        for s, facts in self._index.items():
            word_set.add(s)
            for r, o, _ in facts:
                word_set.add(r)
                for w in o.split():
                    if len(w) > 1:
                        word_set.add(w)
        
        words = sorted(word_set)[:max_words]
        self._vocab_words = words
        
        # Matrice [n_words, dim] pour produit matriciel rapide
        matrix = np.zeros((len(words), self.dim), dtype=np.complex128)
        for i, w in enumerate(words):
            matrix[i] = self.encoder.encode_word(w)
        self._vocab_matrix = matrix
        
        log.info(f"  Vocabulaire décodeur : {len(words)} mots")
    
    # ═════════════════════════════════════════════════════════════════════════
    # PROPRIÉTÉS
    # ═════════════════════════════════════════════════════════════════════════
    
    @property
    def n_facts(self) -> int:
        return self._n_facts
    
    @property
    def n_subjects(self) -> int:
        return len(self._index)
    
    @property
    def energy(self) -> float:
        return float(np.sum(np.abs(self._hologram)**2))


# ═══════════════════════════════════════════════════════════════════════════════
# DÉMO
# ═══════════════════════════════════════════════════════════════════════════════

def demo():
    from holographic_encoder import HolographicEncoder
    
    print("=" * 65)
    print("HOLOGRAPHIC MEMORY — Faits comme ondes")
    print("=" * 65)
    
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
        ("musique", "est l art", "des sons", "CULTURE"),
    ]
    
    encoder = HolographicEncoder(dim=512)
    mem = HolographicMemory(encoder, dim=512)
    mem.store_kb(kb)
    mem.build_vocab()
    
    print(f"\n  {mem.n_facts} faits stockés")
    print(f"  {mem.n_subjects} sujets indexés")
    print(f"  Énergie : {mem.energy:.2f}")
    
    # Test : trouver les sujets résonnants
    print("\n--- Sujets résonnants ---")
    psi_q = encoder.encode_query("explique la lumiere")
    subjects = mem.find_resonant_subjects(psi_q, top_k=5)
    for sujet, score in subjects:
        bar = '█' * int(score * 50)
        print(f"  {sujet:>20s}  {score:+.4f}  {bar}")
    
    # Test : requête complète
    print("\n--- Requêtes complètes ---")
    questions = [
        "explique la lumiere",
        "comment fonctionne le coeur",
        "qu est ce que la gravite",
        "qui a decouvert la relativite",
        "parle de la conscience",
    ]
    
    for q in questions:
        result = mem.query(q, top_k=3)
        print(f"\n  Q: {q}")
        print(f"  Sujets résonnants: {result['subjects'][:3]}")
        for s, r, o, score in result['facts']:
            print(f"    → {s} {r} {o}  (score={score:.4f})")


if __name__ == '__main__':
    demo()
