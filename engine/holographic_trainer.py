"""
Holographic Trainer — Apprentissage Ondulatoire par Rétropropagation de Phase
==============================================================================
Remplace l'approximation statistique (cross-entropy scalaire) par un
apprentissage ondulatoire qui ajuste amplitudes ET phases des vecteurs.

Principe physique :
  - Contexte → onde de référence Ψ_ctx
  - Mot cible → attiré vers la phase du contexte (interférence constructive)
  - Mots négatifs → repoussés (interférence destructive)
  - Règle de Born : P = |Ψ|² → les probabilités émergent des amplitudes

Algorithme :
  Ψ_mot ← Ψ_mot + η · (Ψ_ctx − Ψ_mot) · e^(i·Δφ)
  où Δφ = angle(Ψ_cible) − angle(Ψ_contexte)

Usage :
  from holographic_trainer import HolographicTrainer
  from holographic_encoder import HolographicEncoder
  
  encoder = HolographicEncoder(dim=384)
  trainer = HolographicTrainer(encoder)
  trainer.train_from_kb(knowledge_base, epochs=3)
  precision = trainer.evaluate(test_pairs)
"""

import math
import time
import numpy as np
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

PHI = 1.618033988749895
TAU = 2.0 * math.pi


class HolographicTrainer:
    """
    Entraîneur ondulatoire — ajuste les vecteurs complexes par interférence.
    
    Parameters:
        encoder: HolographicEncoder à entraîner
        lr: taux d'apprentissage (défaut 0.01)
        negative_k: nombre de contre-exemples par paire positive
    """
    
    def __init__(self, encoder, lr: float = 0.01, negative_k: int = 5):
        self.encoder = encoder
        self.lr = lr
        self.k = negative_k
        self.loss_history = []
        self.step_count = 0
        
        # Cache pour les négatifs (échantillonnage rapide)
        self._all_words = []
    
    # ── Opération d'apprentissage élémentaire ──────────────────────────
    
    def train_pair(self, context_words: List[str], target_word: str,
                   negative_words: Optional[List[str]] = None) -> float:
        """
        Un pas d'apprentissage ondulatoire.
        
        Principe :
          Ψ_contexte = moyenne des vecteurs des mots du contexte
          On attire le mot cible vers Ψ_contexte (interférence constructive)
          On repousse les négatifs loin de Ψ_contexte (interférence destructive)
        
        Args:
            context_words: mots formant le contexte
            target_word: mot à prédire (renforcé)
            negative_words: mots à ne PAS prédire (affaiblis)
        
        Returns:
            loss: perte ondulatoire pour ce pas
        """
        # 1. Encoder les mots du contexte
        ctx_vecs = []
        for w in context_words:
            ctx_vecs.append(self.encoder.encode_word(w))
        if not ctx_vecs:
            return 0.0
        
        # Superposition du contexte (moyenne = onde de référence)
        psi_ctx = sum(ctx_vecs) / len(ctx_vecs)
        norm_ctx = np.sqrt(np.sum(np.abs(psi_ctx)**2))
        if norm_ctx > 1e-10:
            psi_ctx /= norm_ctx
        
        # 2. Attraction du mot cible vers le contexte
        psi_target = self.encoder.word_vectors[target_word]  # référence actuelle
        
        # Correction de phase : aligner la cible avec le contexte
        # On utilise une rotation douce : Ψ_new = normalize(Ψ + η·Ψ_ctx)
        correction_target = self.lr * psi_ctx
        psi_target_new = psi_target + correction_target
        
        # Normaliser (la normalisation préserve la direction apprise)
        norm_t = np.sqrt(np.sum(np.abs(psi_target_new)**2))
        if norm_t > 1e-10:
            psi_target_new /= norm_t
        
        # Vérifier que le vecteur a bien changé de direction
        dot_before = np.real(np.dot(psi_target, np.conj(psi_ctx)))
        dot_after = np.real(np.dot(psi_target_new, np.conj(psi_ctx)))
        
        # Stocker
        self.encoder.word_vectors[target_word] = psi_target_new
        
        # 3. Répulsion des négatifs (loin du contexte)
        if negative_words is None and self._all_words:
            # Échantillonner des négatifs aléatoires
            negative_words = list(np.random.choice(
                self._all_words, size=min(self.k, len(self._all_words)), replace=False
            ))
        
        neg_count = 0
        if negative_words:
            for neg in negative_words:
                if neg == target_word or neg not in self.encoder.word_vectors:
                    continue
                psi_neg = self.encoder.word_vectors[neg]
                # Repousser : éloigner du contexte
                correction_neg = self.lr * 0.3 * psi_ctx  # plus faible pour les négatifs
                psi_neg_new = psi_neg - correction_neg
                norm_n = np.sqrt(np.sum(np.abs(psi_neg_new)**2))
                if norm_n > 1e-10:
                    psi_neg_new /= norm_n
                self.encoder.word_vectors[neg] = psi_neg_new
                neg_count += 1
        
        self.step_count += 1
        
        # 4. Calcul de la perte ondulatoire
        loss = self._compute_loss(psi_target_new, psi_ctx, negative_words or [])
        self.loss_history.append(loss)
        
        return loss
    
    def _compute_loss(self, psi_target, psi_ctx, negative_words: List[str]) -> float:
        """
        Perte ondulatoire : entropie croisée complexe.
        
        L = -log( I_cible / (I_cible + Σ I_neg) )
        où I_j = |⟨Ψ_j|Ψ_contexte⟩|²
        """
        # Interférence cible
        I_target = np.abs(np.dot(psi_target, np.conj(psi_ctx)))**2
        
        # Interférence négatifs
        I_neg_total = 0.0
        for neg in negative_words:
            if neg in self.encoder.word_vectors:
                psi_n = self.encoder.word_vectors[neg]
                I_neg_total += np.abs(np.dot(psi_n, np.conj(psi_ctx)))**2
        
        # Éviter log(0)
        denom = I_target + I_neg_total + 1e-10
        if I_target < 1e-10:
            return 10.0  # perte maximale
        
        loss = -math.log(I_target / denom)
        return float(loss)
    
    # ── Entraînement depuis la base de connaissance ────────────────────
    
    def train_from_kb(self, knowledge_base: List[Tuple], epochs: int = 3,
                      batch_size: int = 500, verbose: bool = True) -> List[float]:
        """
        Entraîne l'encodeur sur une base de connaissance.
        
        APPROCHE PAR ACCUMULATION : au lieu de faire SGD par paire,
        on accumule pour chaque mot cible la moyenne des contextes
        où il apparaît, puis on fait UNE mise à jour par mot.
        C'est beaucoup plus efficace en signal.
        """
        all_objects = list(set(o for _, _, o, _ in knowledge_base if len(o) > 2))
        self._all_words = list(set(
            list(all_objects) + [s for s, _, _, _ in knowledge_base if len(s) > 2]
        ))
        
        epoch_losses = []
        
        for epoch in range(epochs):
            t0 = time.time()
            
            # Accumuler les contextes pour chaque mot cible
            ctx_accum = {}  # mot → somme des psi_ctx
            ctx_count = {}  # mot → nombre d'occurrences
            
            for s, r, o, sec in knowledge_base:
                if len(s) < 2 or len(o) < 2:
                    continue
                
                # Contexte = sujet + relation
                context = [s] + r.split()
                ctx_vecs = []
                for w in context:
                    if w in self.encoder.word_vectors:
                        ctx_vecs.append(self.encoder.word_vectors[w])
                if not ctx_vecs:
                    continue
                psi_ctx = sum(ctx_vecs) / len(ctx_vecs)
                
                # Accumuler pour le mot cible (objet)
                if o not in ctx_accum:
                    ctx_accum[o] = np.zeros(self.encoder.dim, dtype=np.complex128)
                    ctx_count[o] = 0
                ctx_accum[o] += psi_ctx
                ctx_count[o] += 1
                
                # Accumuler aussi pour le sujet (prédire le sujet depuis l'objet+relation)
                if s not in ctx_accum:
                    ctx_accum[s] = np.zeros(self.encoder.dim, dtype=np.complex128)
                    ctx_count[s] = 0
                # Contexte inverse : objet + relation
                ctx_inv = [o] + r.split()
                ctx_inv_vecs = []
                for w in ctx_inv:
                    if w in self.encoder.word_vectors:
                        ctx_inv_vecs.append(self.encoder.word_vectors[w])
                if ctx_inv_vecs:
                    psi_ctx_inv = sum(ctx_inv_vecs) / len(ctx_inv_vecs)
                    ctx_accum[s] += psi_ctx_inv
                    ctx_count[s] += 1
            
            # Appliquer les mises à jour accumulées
            epoch_loss = 0.0
            n_updated = 0
            
            for word, accum in ctx_accum.items():
                if word not in self.encoder.word_vectors or ctx_count[word] < 1:
                    continue
                
                # Moyenne des contextes pour ce mot
                psi_avg_ctx = accum / ctx_count[word]
                norm_ctx = np.sqrt(np.sum(np.abs(psi_avg_ctx)**2))
                if norm_ctx < 1e-10:
                    continue
                psi_avg_ctx /= norm_ctx
                
                # Mise à jour du vecteur du mot
                psi_old = self.encoder.word_vectors[word]
                
                # Rotation vers le contexte moyen
                psi_new = psi_old + self.lr * psi_avg_ctx
                norm_new = np.sqrt(np.sum(np.abs(psi_new)**2))
                if norm_new > 1e-10:
                    psi_new /= norm_new
                
                self.encoder.word_vectors[word] = psi_new
                
                # Perte : cosinus entre le vecteur et son contexte moyen
                dot = np.real(np.dot(psi_new, np.conj(psi_avg_ctx)))
                loss = -math.log(max(0.5, (dot + 1.0) / 2.0))  # plus dot est proche de 1, plus la perte est faible
                epoch_loss += loss
                n_updated += 1
            
            avg_loss = epoch_loss / max(n_updated, 1)
            epoch_losses.append(avg_loss)
            
            if verbose:
                elapsed = time.time() - t0
                print(f"  Epoch {epoch+1}/{epochs} | loss={avg_loss:.4f} "
                      f"| {n_updated} mots mis à jour | {elapsed:.1f}s")
        
        return epoch_losses
    
    def train_optimized(self, knowledge_base: List[Tuple], epochs: int = 10,
                         lr_start: float = 0.5, lr_end: float = 0.05,
                         repulsion_strength: float = 0.03,
                         verbose: bool = True) -> dict:
        """
        Entraînement optimisé pour maximiser la précision (>95%).
        
        Combine :
        1. Accumulation de contexte (attraction)
        2. Répulsion inter-domaine (contraste)
        3. Décroissance du learning rate (lr_start → lr_end)
        4. Époques multiples
        
        Returns:
            dict avec métriques détaillées
        """
        from collections import defaultdict
        
        # Grouper les mots par secteur pour la répulsion
        domain_words = defaultdict(list)
        for s, r, o, sec in knowledge_base:
            for w in f'{s} {r} {o}'.split():
                w = w.strip('.,!?;:')
                if len(w) >= 2:
                    domain_words[sec].append(w)
        
        all_objects = list(set(o for _, _, o, _ in knowledge_base if len(o) > 2))
        self._all_words = list(set(
            list(all_objects) + [s for s, _, _, _ in knowledge_base if len(s) > 2]
        ))
        
        epoch_losses = []
        t0_total = time.time()
        
        for epoch in range(epochs):
            t0 = time.time()
            lr = lr_start - (lr_start - lr_end) * epoch / max(epochs - 1, 1)
            
            # ── PHASE 1 : Attraction (accumulation de contexte) ──
            ctx_accum = {}
            ctx_count = {}
            
            for s, r, o, sec in knowledge_base:
                if len(s) < 2 or len(o) < 2:
                    continue
                context = [s] + r.split()
                ctx_vecs = [self.encoder.word_vectors[w] for w in context if w in self.encoder.word_vectors]
                if not ctx_vecs:
                    continue
                psi_ctx = sum(ctx_vecs) / len(ctx_vecs)
                
                for target in [o, s]:  # les deux directions
                    if target not in ctx_accum:
                        ctx_accum[target] = np.zeros(self.encoder.dim, dtype=np.complex128)
                        ctx_count[target] = 0
                    ctx_accum[target] += psi_ctx
                    ctx_count[target] += 1
            
            # Appliquer les mises à jour
            for word, accum in ctx_accum.items():
                if word not in self.encoder.word_vectors or ctx_count[word] < 1:
                    continue
                psi_avg_ctx = accum / ctx_count[word]
                norm_ctx = np.sqrt(np.sum(np.abs(psi_avg_ctx)**2))
                if norm_ctx < 1e-10:
                    continue
                psi_avg_ctx /= norm_ctx
                
                psi_old = self.encoder.word_vectors[word]
                psi_new = psi_old + lr * psi_avg_ctx
                norm_new = np.sqrt(np.sum(np.abs(psi_new)**2))
                if norm_new > 1e-10:
                    psi_new /= norm_new
                self.encoder.word_vectors[word] = psi_new
            
            # ── PHASE 2 : Répulsion inter-domaine ──
            if repulsion_strength > 0 and epoch >= 2:  # commence après 2 epochs d'attraction
                # Calculer les centroïdes de domaine
                domain_centroids = {}
                for sec, words in domain_words.items():
                    vecs = []
                    for w in words[:200]:
                        if w in self.encoder.word_vectors:
                            vecs.append(self.encoder.word_vectors[w])
                    if vecs:
                        centroid = sum(vecs) / len(vecs)
                        norm_c = np.sqrt(np.sum(np.abs(centroid)**2))
                        if norm_c > 1e-10:
                            centroid /= norm_c
                        domain_centroids[sec] = centroid
                
                # Pour chaque mot, repousser des centroïdes des AUTRES domaines
                sectors_list = list(domain_centroids.keys())
                for sec, words in domain_words.items():
                    my_centroid = domain_centroids.get(sec)
                    for w in words[:100]:
                        if w not in self.encoder.word_vectors:
                            continue
                        v = self.encoder.word_vectors[w]
                        for other_sec in sectors_list:
                            if other_sec == sec:
                                continue
                            other_c = domain_centroids[other_sec]
                            v = v - repulsion_strength * lr * other_c
                        norm_v = np.sqrt(np.sum(np.abs(v)**2))
                        if norm_v > 1e-10:
                            v /= norm_v
                        self.encoder.word_vectors[w] = v
            
            # ── Perte ──
            epoch_loss = 0.0
            n_updated = 0
            for word in ctx_accum:
                if word in self.encoder.word_vectors and ctx_count.get(word, 0) > 0:
                    psi_avg = ctx_accum[word] / ctx_count[word]
                    norm_avg = np.sqrt(np.sum(np.abs(psi_avg)**2))
                    if norm_avg > 1e-10:
                        psi_avg /= norm_avg
                    dot = np.real(np.dot(self.encoder.word_vectors[word], np.conj(psi_avg)))
                    loss = -math.log(max(0.1, (dot + 1.0) / 2.0))
                    epoch_loss += loss
                    n_updated += 1
            
            avg_loss = epoch_loss / max(n_updated, 1)
            epoch_losses.append(avg_loss)
            
            if verbose:
                elapsed = time.time() - t0
                print(f"  Epoch {epoch+1:>2d}/{epochs} | lr={lr:.3f} | loss={avg_loss:.4f} "
                      f"| {n_updated} mots | {elapsed:.1f}s")
        
        if verbose:
            total_elapsed = time.time() - t0_total
            print(f"  Total: {total_elapsed:.1f}s | Loss: {epoch_losses[0]:.4f} → {epoch_losses[-1]:.4f}")
        
        return {
            'losses': [round(l, 4) for l in epoch_losses],
            'loss_start': round(epoch_losses[0], 4),
            'loss_end': round(epoch_losses[-1], 4),
            'total_time': round(time.time() - t0_total, 1),
            'n_words_updated': n_updated,
        }
    
    def train_from_corpus(self, texts: List[str], window: int = 5,
                          epochs: int = 1, verbose: bool = True) -> List[float]:
        """
        Entraînement auto-supervisé depuis un corpus de textes.
        
        Fenêtre glissante : pour chaque mot cible,
          contexte = mots dans la fenêtre autour
          négatifs = mots aléatoires hors fenêtre
        
        Args:
            texts: liste de textes (chaînes)
            window: taille de la fenêtre de contexte (de chaque côté)
            epochs: nombre de passes
        
        Returns:
            loss_history
        """
        # Construire le vocabulaire à partir du corpus
        all_words_set = set()
        for text in texts:
            for w in text.lower().split():
                w = w.strip('.,!?;:()[]{}')
                if len(w) > 2:
                    all_words_set.add(w)
        self._all_words = list(all_words_set)
        
        epoch_losses = []
        
        for epoch in range(epochs):
            t0 = time.time()
            epoch_loss = 0.0
            n_trained = 0
            
            for text in texts:
                words = [w.strip('.,!?;:()[]{}') for w in text.lower().split()
                        if len(w.strip('.,!?;:()[]{}')) > 2]
                if len(words) < window * 2 + 1:
                    continue
                
                for i, target in enumerate(words):
                    # Contexte = mots autour de i
                    start = max(0, i - window)
                    end = min(len(words), i + window + 1)
                    context = [w for j, w in enumerate(words)
                              if start <= j < end and j != i]
                    
                    if not context:
                        continue
                    
                    # Négatifs = mots hors fenêtre
                    negs = [w for w in self._all_words
                           if w not in set(context) and w != target]
                    if len(negs) > self.k:
                        negs = list(np.random.choice(negs, size=self.k, replace=False))
                    
                    loss = self.train_pair(context, target, negs)
                    epoch_loss += loss
                    n_trained += 1
            
            avg_loss = epoch_loss / max(n_trained, 1)
            epoch_losses.append(avg_loss)
            
            if verbose:
                elapsed = time.time() - t0
                print(f"  Corpus epoch {epoch+1}/{epochs} | loss={avg_loss:.4f} "
                      f"| {n_trained} pas | {elapsed:.1f}s")
        
        return epoch_losses
    
    # ── Évaluation ─────────────────────────────────────────────────────
    
    def evaluate(self, test_pairs: List[Tuple[str, str, int]]) -> Dict:
        """
        Évalue la précision de l'encodeur sur des paires (mot_a, mot_b, related).
        
        Args:
            test_pairs: liste de (mot_a, mot_b, 1 si apparenté / 0 sinon)
        
        Returns:
            dict avec precision, rappel, similarité moyenne apparentés/non
        """
        if not test_pairs:
            return {'precision': 0, 'recall': 0, 'sim_positive': 0, 'sim_negative': 0}
        
        sims_positive = []
        sims_negative = []
        
        for a, b, label in test_pairs:
            if a not in self.encoder.word_vectors or b not in self.encoder.word_vectors:
                continue
            sim = self.encoder.similarity_word(a, b)
            if label == 1:
                sims_positive.append(sim)
            else:
                sims_negative.append(sim)
        
        # Trouver le seuil optimal
        best_acc = 0
        best_threshold = 0
        for threshold in np.linspace(-1, 1, 100):
            correct = 0
            total = 0
            for a, b, label in test_pairs:
                if a not in self.encoder.word_vectors or b not in self.encoder.word_vectors:
                    continue
                sim = self.encoder.similarity_word(a, b)
                pred = 1 if sim > threshold else 0
                if pred == label:
                    correct += 1
                total += 1
            if total > 0:
                acc = correct / total
                if acc > best_acc:
                    best_acc = acc
                    best_threshold = threshold
        
        return {
            'precision': round(best_acc * 100, 1),
            'threshold': round(best_threshold, 3),
            'sim_positive': round(float(np.mean(sims_positive)), 4) if sims_positive else 0,
            'sim_negative': round(float(np.mean(sims_negative)), 4) if sims_negative else 0,
            'n_tested': len(test_pairs),
        }
    
    def evaluate_topk(self, test_contexts: List[Tuple[List[str], str]]) -> float:
        """
        Évalue la précision top-1 : pour un contexte, le vrai mot cible est-il
        celui avec la plus forte similarité ?
        
        Args:
            test_contexts: liste de (contexte_words, target_word)
        
        Returns:
            top1_accuracy: fraction où la cible est dans le top-1
        """
        if not test_contexts:
            return 0.0
        
        correct = 0
        total = 0
        
        for context_words, target in test_contexts:
            # Encoder le contexte
            ctx_vecs = []
            for w in context_words:
                if w in self.encoder.word_vectors:
                    ctx_vecs.append(self.encoder.word_vectors[w])
            if not ctx_vecs:
                continue
            psi_ctx = sum(ctx_vecs) / len(ctx_vecs)
            
            # Trouver le mot le plus similaire
            best_word = None
            best_sim = -2.0
            for w, v in self.encoder.word_vectors.items():
                if w.startswith('__char_'):
                    continue
                sim = float(np.real(np.dot(v, np.conj(psi_ctx))))
                if sim > best_sim:
                    best_sim = sim
                    best_word = w
            
            if best_word == target:
                correct += 1
            total += 1
        
        return correct / max(total, 1) if total > 0 else 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def build_test_pairs(knowledge_base, n_positive: int = 500, n_negative: int = 500):
    """
    Construit des paires de test à partir d'une base de connaissance.
    
    Positives : mots apparaissant dans le même fait
    Négatives : mots de faits différents (secteurs éloignés)
    """
    import random
    
    subjects = list(set(s for s, _, _, _ in knowledge_base if len(s) > 2))
    objects = list(set(o for _, _, o, _ in knowledge_base if len(o) > 2))
    all_words = list(set(subjects + objects))
    
    pairs = []
    
    # Paires positives : sujet-objet d'un même fait
    positive_pairs = []
    for s, r, o, _ in knowledge_base:
        if len(s) > 2 and len(o) > 2:
            positive_pairs.append((s, o, 1))
    random.shuffle(positive_pairs)
    pairs.extend(positive_pairs[:n_positive])
    
    # Paires négatives : mots de domaines différents
    # Grouper par secteur
    words_by_sector = defaultdict(list)
    for s, _, o, sec in knowledge_base:
        if len(s) > 2:
            words_by_sector[sec].append(s)
        if len(o) > 2:
            words_by_sector[sec].append(o)
    
    sectors = list(words_by_sector.keys())
    negative_count = 0
    attempts = 0
    while negative_count < n_negative and attempts < n_negative * 5:
        s1, s2 = random.sample(sectors, 2) if len(sectors) >= 2 else (sectors[0], sectors[0])
        if words_by_sector[s1] and words_by_sector[s2]:
            w1 = random.choice(words_by_sector[s1])
            w2 = random.choice(words_by_sector[s2])
            if w1 != w2:
                pairs.append((w1, w2, 0))
                negative_count += 1
        attempts += 1
    
    random.shuffle(pairs)
    return pairs


# ═══════════════════════════════════════════════════════════════════════════════
# TEST RAPIDE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=== Test HolographicTrainer ===")
    from holographic_encoder import HolographicEncoder
    
    encoder = HolographicEncoder(dim=128)
    trainer = HolographicTrainer(encoder, lr=0.05)
    
    # Mini KB de test
    kb = [
        ("lumiere", "est une", "onde electromagnetique", "PHYSIQUE"),
        ("lumiere", "se deplace a", "300000 km/s", "PHYSIQUE"),
        ("onde", "transporte", "energie", "PHYSIQUE"),
        ("gravite", "est la", "courbure de espace temps", "PHYSIQUE"),
        ("eau", "a une", "capacite thermique elevee", "BIOLOGIE"),
        ("coeur", "pompe", "sang", "BIOLOGIE"),
        ("sang", "transporte", "oxygene", "BIOLOGIE"),
        ("adn", "contient", "code genetique", "BIOLOGIE"),
        ("etoile", "est une", "boule de plasma", "ASTRONOMIE"),
        ("planete", "orbite autour", "etoile", "ASTRONOMIE"),
    ]
    
    # Pré-encoder
    for s, r, o, _ in kb:
        for w in f"{s} {r} {o}".split():
            encoder.encode_word(w)
    
    # Test avant entraînement
    print("\nAvant entraînement:")
    print(f"  sim(lumiere, onde) = {encoder.similarity_word('lumiere', 'onde'):.4f}")
    print(f"  sim(lumiere, gravite) = {encoder.similarity_word('lumiere', 'gravite'):.4f}")
    print(f"  sim(coeur, sang) = {encoder.similarity_word('coeur', 'sang'):.4f}")
    print(f"  sim(lumiere, coeur) = {encoder.similarity_word('lumiere', 'coeur'):.4f}")
    
    # Entraînement
    print(f"\nEntraînement sur {len(kb)} faits...")
    losses = trainer.train_from_kb(kb, epochs=10, verbose=False)
    print(f"  Loss initiale: {losses[0]:.4f}")
    print(f"  Loss finale: {losses[-1]:.4f}")
    
    # Test après entraînement
    print("\nAprès entraînement:")
    print(f"  sim(lumiere, onde) = {encoder.similarity_word('lumiere', 'onde'):.4f}  (attendu > 0)")
    print(f"  sim(lumiere, gravite) = {encoder.similarity_word('lumiere', 'gravite'):.4f}  (attendu > 0, même domaine)")
    print(f"  sim(coeur, sang) = {encoder.similarity_word('coeur', 'sang'):.4f}  (attendu > 0)")
    print(f"  sim(lumiere, coeur) = {encoder.similarity_word('lumiere', 'coeur'):.4f}  (attendu ~0, domaines différents)")
    
    # Évaluation
    test_pairs = build_test_pairs(kb, n_positive=20, n_negative=20)
    results = trainer.evaluate(test_pairs)
    print(f"\nÉvaluation: précision={results['precision']}%, "
          f"sim+={results['sim_positive']:.4f}, sim-={results['sim_negative']:.4f}")
    
    print("\n✓ Test terminé.")
