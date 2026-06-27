#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Décodeur Auto-Régressif Harmonique (Phase 1)
==============================================
Génère une séquence de tokens à partir d'un vecteur de contexte 7D.

Principe :
- État initial = encodage 7D du contexte (question + faits)
- À chaque étape, on prédit le token suivant par similarité cosinus
- L'état évolue par résonance : état(t+1) = φ·état(t) + (1-φ)·embedding(token)
- Beam Search avec score de cohérence 7D (Phase 3 intégrée)
- Filtre de répétition pour éviter les boucles

Auteur : KOTTO Alain — 19 Juin 2026
"""

import math, time, sys, os
from typing import List, Tuple, Dict, Optional
import numpy as np

# ==============================================================================
# CONSTANTES HARMONIQUES
# ==============================================================================
phi = (1 + math.sqrt(5)) / 2
pi = math.pi
e = math.e
sqrt2 = math.sqrt(2); sqrt3 = math.sqrt(3); sqrt5 = math.sqrt(5)
e_sur_pi = e / pi

H = np.array([phi, pi, e, sqrt2, sqrt3, sqrt5, e_sur_pi], dtype=np.float64)
H_names = ['φ','π','e','√2','√3','√5','e/π']; H_sum = H.sum()

# ==============================================================================
# TOKENISEUR + EMBEDDINGS 7D
# ==============================================================================

class TokeniseurHarmonique:
    """
    Tokeniseur construit à partir d'un vocabulaire (issu des hologrammes).
    Chaque token a un embedding 7D basé sur les constantes Hₙ.
    """
    
    def __init__(self):
        self.token_to_id = {}
        self.id_to_token = {}
        self.embeddings = {}  # id → vecteur 7D
        self.vocabulaire = set()
    
    def _mot_vers_7d(self, mot: str) -> np.ndarray:
        """Convertit un mot en vecteur spectral 7D."""
        v = np.zeros(7, dtype=np.float64)
        for i, c in enumerate(mot):
            v[(ord(c) + i) % 7] += H[(ord(c) + i) % 7] / H_sum
        n = np.linalg.norm(v)
        return v / n if n > 0 else v
    
    def construire_depuis_corpus(self, corpus: List[str], min_freq: int = 2, max_tokens: int = 8000):
        """
        Construit le vocabulaire depuis un corpus de textes.
        
        Args:
            corpus: liste de phrases
            min_freq: fréquence minimale pour inclure un mot
            max_tokens: nombre maximum de tokens
        """
        from collections import Counter
        
        # Compter les mots
        compteur = Counter()
        for texte in corpus:
            for mot in texte.lower().split():
                if len(mot) >= 2:  # Ignorer les tokens d'un seul caractère
                    compteur[mot] += 1
        
        # Sélectionner les tokens les plus fréquents
        tokens_frequents = [mot for mot, freq in compteur.most_common(max_tokens) if freq >= min_freq]
        
        # Ajouter les tokens spéciaux
        tokens_speciaux = ["<PAD>", "<UNK>", "<BOS>", "<EOS>", "<SEP>"]
        for tok in tokens_speciaux:
            if tok not in tokens_frequents:
                tokens_frequents.insert(0, tok)
        
        # Construire le vocabulaire
        for i, mot in enumerate(tokens_frequents):
            self.token_to_id[mot] = i
            self.id_to_token[i] = mot
            self.embeddings[i] = self._mot_vers_7d(mot)
            self.vocabulaire.add(mot)
        
        # Embedding pour <UNK>
        self.unk_id = self.token_to_id.get("<UNK>", 0)
        
        return len(self.vocabulaire)
    
    def encoder(self, texte: str) -> List[int]:
        """Encode un texte en liste d'indices."""
        indices = []
        for mot in texte.lower().split():
            if mot in self.token_to_id:
                indices.append(self.token_to_id[mot])
            else:
                indices.append(self.unk_id)
        return indices
    
    def decoder(self, indices: List[int]) -> str:
        """Décode une liste d'indices en texte."""
        mots = []
        for idx in indices:
            if idx in self.id_to_token:
                mot = self.id_to_token[idx]
                if mot not in ["<PAD>", "<UNK>", "<BOS>", "<EOS>", "<SEP>"]:
                    mots.append(mot)
        return " ".join(mots)
    
    def texte_vers_7d(self, texte: str) -> np.ndarray:
        """Convertit un texte en vecteur 7D (moyenne pondérée des mots)."""
        mots = texte.lower().split()
        if not mots:
            return np.zeros(7, dtype=np.float64)
        
        v = np.zeros(7, dtype=np.float64)
        for mot in mots:
            v += self._mot_vers_7d(mot)
        
        n = np.linalg.norm(v)
        return v / n if n > 0 else v


# ==============================================================================
# DÉCODEUR AUTO-RÉGRESSIF HARMONIQUE
# ==============================================================================

class DecodeurHarmonique:
    """
    Décodeur auto-régressif basé sur la résonance harmonique.
    
    Génère du texte token par token en utilisant :
    - Un état interne 7D qui évolue par résonance (φ)
    - La similarité cosinus dans l'espace des embeddings 7D
    - Un beam search pour explorer plusieurs hypothèses
    - Un filtre de répétition pour éviter les boucles
    """
    
    def __init__(self, tokeniseur: TokeniseurHarmonique):
        self.tokeniseur = tokeniseur
        self.bos_id = tokeniseur.token_to_id.get("<BOS>", 0)
        self.eos_id = tokeniseur.token_to_id.get("<EOS>", 3)
        self.pad_id = tokeniseur.token_to_id.get("<PAD>", 0)
        self.unk_id = tokeniseur.unk_id
        
        # Masque pour exclure les tokens spéciaux de la génération
        self.tokens_speciaux = {
            tokeniseur.token_to_id.get(t, -1)
            for t in ["<PAD>", "<UNK>", "<BOS>", "<EOS>", "<SEP>"]
        }
        self.tokens_speciaux.discard(-1)
    
    def _initialiser_etat(self, contexte: str) -> np.ndarray:
        """Initialise l'état 7D à partir du contexte."""
        return self.tokeniseur.texte_vers_7d(contexte)
    
    def _score_cosinus(self, etat: np.ndarray, token_id: int) -> float:
        """Calcule le score de similarité cosinus entre l'état et un token."""
        if token_id not in self.tokeniseur.embeddings:
            return 0.0
        emb = self.tokeniseur.embeddings[token_id]
        dot = np.dot(etat, emb)
        norm_e = np.linalg.norm(etat)
        norm_t = np.linalg.norm(emb)
        return max(0.0, float(dot / (norm_e * norm_t + 1e-10)))
    
    def _evoluer_etat(self, etat: np.ndarray, token_id: int) -> np.ndarray:
        """
        Fait évoluer l'état par résonance.
        état(t+1) = φ · état(t) + (1-φ) · embedding(token)
        """
        if token_id in self.tokeniseur.embeddings:
            emb = self.tokeniseur.embeddings[token_id]
            nouvel_etat = phi * etat + (1 - phi) * emb
        else:
            nouvel_etat = phi * etat  # Atténuation si token inconnu
        
        # Normaliser
        norm = np.linalg.norm(nouvel_etat)
        return nouvel_etat / norm if norm > 0 else etat
    
    def _echantillonner(self, scores: List[Tuple[int, float]],
                        temperature: float = 0.7) -> int:
        """
        Échantillonne un token selon une distribution softmax avec température.
        
        Args:
            scores: liste de (token_id, score_cosinus)
            temperature: contrôle la diversité (0 = déterministe, 1 = aléatoire)
        
        Returns:
            token_id choisi
        """
        if not scores:
            return self.unk_id
        
        ids = np.array([s[0] for s in scores], dtype=np.int32)
        vals = np.array([s[1] for s in scores], dtype=np.float64)
        
        # Appliquer la température
        if temperature > 0:
            vals = vals / temperature
            # Softmax
            vals = np.exp(vals - np.max(vals))
            vals = vals / vals.sum()
            idx = np.random.choice(len(ids), p=vals)
        else:
            idx = np.argmax(vals)
        
        return int(ids[idx])
    
    def generer(self, contexte: str, max_tokens: int = 50,
                temperature: float = 0.7,
                penalite_repetition: float = 0.3) -> str:
        """
        Génère un texte à partir d'un contexte (génération gloutonne).
        
        Args:
            contexte: texte de départ (question + faits)
            max_tokens: nombre maximum de tokens à générer
            temperature: diversité (0.0 = déterministe, 1.0 = créatif)
            penalite_repetition: pénalité pour les tokens déjà vus
        
        Returns:
            Texte généré
        """
        etat = self._initialiser_etat(contexte)
        tokens_generees = []
        tokens_vus = set()
        
        for _ in range(max_tokens):
            # Calculer les scores pour tous les tokens du vocabulaire
            scores = []
            for tid in self.tokeniseur.embeddings:
                if tid in self.tokens_speciaux:
                    continue
                
                score = self._score_cosinus(etat, tid)
                
                # Pénalité de répétition
                if tid in tokens_vus:
                    score *= (1.0 - penalite_repetition)
                
                if score > 0:
                    scores.append((tid, score))
            
            if not scores:
                break
            
            # Choisir le prochain token
            next_token = self._echantillonner(scores, temperature)
            tokens_generees.append(next_token)
            tokens_vus.add(next_token)
            
            # Évoluer l'état
            etat = self._evoluer_etat(etat, next_token)
        
        return self.tokeniseur.decoder(tokens_generees)
    
    def generer_beam(self, contexte: str, max_tokens: int = 50,
                     beam_width: int = 5, temperature: float = 0.7,
                     penalite_repetition: float = 0.2) -> str:
        """
        Génère un texte avec Beam Search.
        
        Args:
            contexte: texte de départ
            max_tokens: nombre maximum de tokens
            beam_width: nombre d'hypothèses à explorer
            temperature: diversité
            penalite_repetition: pénalité pour les tokens déjà vus
        
        Returns:
            Meilleure séquence générée
        """
        etat_initial = self._initialiser_etat(contexte)
        
        # Chaque hypothèse : (tokens, état, score_cumulé, tokens_vus)
        hypotheses = [([], etat_initial, 0.0, set())]
        
        for _ in range(max_tokens):
            nouvelles = []
            
            for tokens, etat, score_cumul, tokens_vus in hypotheses:
                # Calculer les scores
                scores = []
                for tid in self.tokeniseur.embeddings:
                    if tid in self.tokens_speciaux:
                        continue
                    
                    score_token = self._score_cosinus(etat, tid)
                    if tid in tokens_vus:
                        score_token *= (1.0 - penalite_repetition)
                    
                    if score_token > 0:
                        scores.append((tid, score_token))
                
                if not scores:
                    nouvelles.append((tokens, etat, score_cumul, tokens_vus))
                    continue
                
                # Prendre les top beam_width tokens
                scores.sort(key=lambda x: x[1], reverse=True)
                for tid, score_t in scores[:beam_width]:
                    nouvel_etat = self._evoluer_etat(etat, tid)
                    nouveau_score = score_cumul + score_t
                    nouveaux_tokens = tokens + [tid]
                    nouveaux_vus = tokens_vus | {tid}
                    nouvelles.append((nouveaux_tokens, nouvel_etat, nouveau_score, nouveaux_vus))
            
            # Garder les beam_width meilleures hypothèses
            nouvelles.sort(key=lambda x: x[2] / max(len(x[0]), 1), reverse=True)
            hypotheses = nouvelles[:beam_width]
        
        # Retourner la meilleure hypothèse
        if hypotheses:
            best_tokens = hypotheses[0][0]
            return self.tokeniseur.decoder(best_tokens)
        
        return ""
    
    def generer_faits(self, question: str, faits: List[str],
                      max_tokens: int = 60, beam_width: int = 5) -> str:
        """
        Génère une réponse à partir de faits (mode assistant).
        
        Args:
            question: la question posée
            faits: liste de textes factuels trouvés
            max_tokens: nombre maximum de tokens
            beam_width: largeur du beam search
        
        Returns:
            Réponse générée
        """
        # Construire le contexte enrichi
        contexte = f"{question} {' '.join(faits)}"
        
        # Générer avec beam search (plus cohérent)
        return self.generer_beam(contexte, max_tokens, beam_width, temperature=0.5)


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================
def demo():
    """Démonstration du décodeur harmonique."""
    print("=" * 60)
    print("DÉCODEUR AUTO-RÉGRESSIF HARMONIQUE (Phase 1)")
    print("=" * 60)
    print()
    
    # Corpus d'entraînement (extrait des hologrammes)
    sys.path.insert(0, os.path.dirname(__file__))
    from assistant_harmonique_vocal import HologrammeMinimal
    
    print("Chargement du corpus depuis les hologrammes...")
    holo = HologrammeMinimal()
    holo.charger(max_total=5000)
    
    # Extraire les textes pour le tokeniseur
    corpus_textes = [c['texte'] for c in holo.connaissances[:3000]]
    print(f"  {len(corpus_textes)} textes pour le vocabulaire")
    print()
    
    # Construire le tokeniseur
    print("Construction du tokeniseur harmonique...")
    tokeniseur = TokeniseurHarmonique()
    n_tokens = tokeniseur.construire_depuis_corpus(corpus_textes, min_freq=2, max_tokens=5000)
    print(f"  {n_tokens} tokens dans le vocabulaire")
    print()
    
    # Créer le décodeur
    decodeur = DecodeurHarmonique(tokeniseur)
    
    # Tests de génération
    print("Tests de génération :")
    print()
    
    tests = [
        "la constante de Planck",
        "la vitesse de la lumiere",
        "la theorie de la relativite",
        "la photosynthese des plantes",
        "le Big Bang origine de l univers",
    ]
    
    for contexte in tests:
        print(f"  Contexte : \"{contexte}\"")
        
        # Génération gloutonne
        t1 = time.time()
        texte_genere = decodeur.generer(contexte, max_tokens=15, temperature=0.5)
        t_greedy = time.time() - t1
        
        # Génération beam search
        t2 = time.time()
        texte_beam = decodeur.generer_beam(contexte, max_tokens=15, beam_width=5, temperature=0.5)
        t_beam = time.time() - t2
        
        print(f"    Greedy ({t_greedy*1000:.0f}ms): {texte_genere[:120]}")
        print(f"    Beam   ({t_beam*1000:.0f}ms): {texte_beam[:120]}")
        print()
    
    print("=" * 60)
    print("✅ TERMINÉ")
    print("=" * 60)


if __name__ == "__main__":
    demo()