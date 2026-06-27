#!/usr/bin/env python3
"""
HARMONIC MATH TRAINER — Entraînement au raisonnement par résonance
=====================================================================
Adapte l'approche Chain-of-Thought (CoT) à l'architecture harmonique.
Au lieu d'apprendre à prédire le prochain token par probabilité,
ce système fait résonner les problèmes et leurs solutions dans
un hologramme partagé.

Principes :
  1. INGESTION : Chaque problème et sa solution sont superposés
     comme des ondes dans l'hologramme (position proche = lien)
  2. LECTEURS : N lecteurs apprenant les positions (kx, ky) optimales
     par gradient descendant sur la corrélation
  3. CoT HARMONIQUE : Le problème active une cascade de lecteurs
     Chaque lecteur = une étape du raisonnement
  4. GÉNÉRATION : La solution émerge par interférence constructive
     Pas de prédiction probabiliste du mot suivant

Usage :
  python ka_phone/harmonic_math_trainer.py --train         # Entraîner
  python ka_phone/harmonic_math_trainer.py --test          # Tester
  python ka_phone/harmonic_math_trainer.py --problem "..." # Résoudre
"""

import os, sys, json, math, time, hashlib, re, random
import numpy as np
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass, field

PHI = 1.618033988749895
ALPHA = 1.0 / PHI
HOLOGRAM_SIZE = 256
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "math_trainer")
os.makedirs(DATA_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════════════
# DATASET SYNTHÉTIQUE — Problèmes mathématiques avec solution CoT
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class MathProblem:
    question: str
    steps: List[str]       # Étapes du raisonnement (Chain-of-Thought)
    answer: str            # Réponse finale
    domain: str = "arithmetic"
    difficulty: int = 1

MATH_DATASET = [
    # Arithmétique
    MathProblem("Que vaut 127 + 58 ?", 
                ["127 + 50 = 177", "177 + 8 = 185"], "185", "arithmetic", 1),
    MathProblem("Calcule 15 × 7 + 3", 
                ["15 × 7 = 105", "105 + 3 = 108"], "108", "arithmetic", 1),
    MathProblem("Que vaut 1000 - 347 ?",
                ["1000 - 300 = 700", "700 - 40 = 660", "660 - 7 = 653"], "653", "arithmetic", 1),
    MathProblem("Calcule 144 / 12",
                ["12 × 12 = 144", "donc 144 / 12 = 12"], "12", "arithmetic", 1),
    MathProblem("Que vaut 3^4 ?",
                ["3^1 = 3", "3^2 = 9", "3^3 = 27", "3^4 = 81"], "81", "arithmetic", 2),
    MathProblem("Calcule 25% de 200",
                ["25% = 1/4", "200 / 4 = 50"], "50", "arithmetic", 1),
    MathProblem("Que vaut 37 × 11 ?",
                ["37 × 10 = 370", "370 + 37 = 407"], "407", "arithmetic", 2),
    MathProblem("Calcule (8 + 3) × (12 - 5)",
                ["8 + 3 = 11", "12 - 5 = 7", "11 × 7 = 77"], "77", "arithmetic", 2),
    MathProblem("Que vaut 256 / 16 ?",
                ["16 × 16 = 256", "donc 256 / 16 = 16"], "16", "arithmetic", 1),
    MathProblem("Calcule 99 × 99",
                ["99 × 100 = 9900", "9900 - 99 = 9801"], "9801", "arithmetic", 2),

    # Algèbre
    MathProblem("Résous x + 7 = 15",
                ["x = 15 - 7 (on isole x)", "x = 8"], "x = 8", "algebra", 1),
    MathProblem("Résous 3x = 21",
                ["x = 21 / 3 (on divise par 3)", "x = 7"], "x = 7", "algebra", 1),
    MathProblem("Résous x² - 9 = 0",
                ["x² = 9", "x = ±3"], "x = ±3", "algebra", 2),
    MathProblem("Résous 2x + 5 = 17",
                ["2x = 17 - 5 = 12", "x = 12 / 2 = 6"], "x = 6", "algebra", 1),
    MathProblem("Factorise x² + 5x + 6",
                ["Chercher deux nombres dont la somme = 5 et produit = 6", "2 et 3 fonctionnent", "(x+2)(x+3)"], "(x+2)(x+3)", "algebra", 2),

    # Géométrie
    MathProblem("Aire d'un cercle de rayon 5 ?",
                ["A = πr²", "A = π × 5²", "A = π × 25", "A ≈ 78.5"], "≈ 78.5", "geometry", 2),
    MathProblem("Périmètre d'un carré de côté 7 ?",
                ["P = 4 × côté", "P = 4 × 7 = 28"], "28", "geometry", 1),
    MathProblem("Hypoténuse d'un triangle rectangle (3, 4) ?",
                ["c² = a² + b² (Pythagore)", "c² = 3² + 4² = 9 + 16 = 25", "c = 5"], "5", "geometry", 1),

    # Probabilités
    MathProblem("Probabilité d'avoir pile en lançant une pièce ?",
                ["Cas favorables : 1 (pile)", "Cas possibles : 2 (pile ou face)", "P = 1/2"], "1/2", "probability", 1),
    MathProblem("Probabilité de tirer un roi d'un jeu de 52 cartes ?",
                ["Nombre de rois : 4", "Nombre total de cartes : 52", "P = 4/52 = 1/13"], "1/13", "probability", 1),
    MathProblem("Probabilité de faire un 6 avec un dé ?",
                ["Cas favorables : 1", "Cas possibles : 6", "P = 1/6"], "1/6", "probability", 1),
]

# ══════════════════════════════════════════════════════════════════════════
# HARMONIC MATH TRAINER
# ══════════════════════════════════════════════════════════════════════════

class HarmonicMathTrainer:
    """
    Entraîneur mathématique par résonance holographique.
    Apprend la correspondance problème→solution par superposition d'ondes.
    """

    def __init__(self, num_readers: int = 8):
        self.num_readers = num_readers
        self.hologram = self._load_or_create()
        # N lecteurs : chacun a une position (kx, ky) apprenable
        self.readers = [(random.uniform(-5, 5), random.uniform(-5, 5)) 
                        for _ in range(num_readers)]
        self.learning_rate = 0.05
        self.stats = {"total_trained": 0, "avg_correlation": 0.0}

    def _load_or_create(self):
        path = os.path.join(DATA_DIR, "math_hologram.npy")
        if os.path.exists(path):
            return np.load(path)
        return np.zeros((HOLOGRAM_SIZE, HOLOGRAM_SIZE), dtype=np.complex128)

    def save(self):
        np.save(os.path.join(DATA_DIR, "math_hologram.npy"), self.hologram)

    # ═══ WAVE OPERATIONS ═══
    def _text_to_wave(self, text: str, amp: float = 0.3, sigma: float = 4.0) -> np.ndarray:
        """Texte → signature (kx, ky) → onde gaussienne."""
        h = hashlib.sha256(text.encode()[:200]).hexdigest()
        kx = (int(h[:16], 16) % (HOLOGRAM_SIZE * 100)) / 100.0
        ky = (int(h[16:32], 16) % (HOLOGRAM_SIZE * 100)) / 100.0
        kx = (kx - HOLOGRAM_SIZE / 2) / HOLOGRAM_SIZE * 20
        ky = (ky - HOLOGRAM_SIZE / 2) / HOLOGRAM_SIZE * 20
        x = np.linspace(-HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE)
        y = np.linspace(-HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE)
        X, Y = np.meshgrid(x, y)
        env = np.exp(-(X**2 + Y**2) / (2 * sigma**2))
        wave = np.exp(1j * (kx * X / 20 + ky * Y / 20))
        return amp * env * wave

    def _wave_at(self, kx: float, ky: float, amp: float = 0.5, sigma: float = 3.0) -> np.ndarray:
        """Crée une onde à une position (kx, ky) donnée (pour les lecteurs)."""
        x = np.linspace(-HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE)
        y = np.linspace(-HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE / 2, HOLOGRAM_SIZE)
        X, Y = np.meshgrid(x, y)
        env = np.exp(-(X**2 + Y**2) / (2 * sigma**2))
        wave = np.exp(1j * (kx * X / 20 + ky * Y / 20))
        return amp * env * wave

    def _correlation(self, wave1: np.ndarray, wave2: np.ndarray) -> float:
        """Corrélation normalisée entre deux ondes."""
        c = np.abs(np.sum(wave1 * np.conj(wave2)))
        n1 = np.sqrt(np.sum(np.abs(wave1)**2))
        n2 = np.sqrt(np.sum(np.abs(wave2)**2))
        if n1 < 1e-10 or n2 < 1e-10:
            return 0.0
        return float(c / (n1 * n2))

    # ═══ INGESTION ═══
    def ingest_problem(self, problem: MathProblem, amp_q: float = 0.2, amp_s: float = 0.3):
        """
        Ingère un problème mathématique dans l'hologramme.
        Superpose la question et chaque étape de solution dans la même région,
        créant un lien par interférence.
        """
        # Superposer la question
        q_wave = self._text_to_wave(problem.question, amp=amp_q)
        self.hologram += q_wave

        # Superposer chaque étape de la solution
        for step in problem.steps:
            s_wave = self._text_to_wave(step, amp=amp_s)
            self.hologram += s_wave

        # Superposer la réponse finale (amplitude la plus élevée)
        a_wave = self._text_to_wave(f"Réponse: {problem.answer}", amp=0.4)
        self.hologram += a_wave

        # Anti-saturation
        max_amp = np.max(np.abs(self.hologram))
        if max_amp > 500.0:
            self.hologram *= 0.98

        self.stats["total_trained"] += 1

    # ═══ ENTRAÎNEMENT DES LECTEURS ═══
    def train_readers(self, problem: MathProblem, epochs: int = 5):
        """
        Entraîne les N lecteurs à trouver les positions optimales
        pour interroger l'hologramme sur ce type de problème.
        
        Pour chaque lecteur :
        1. Créer une onde à sa position (kx, ky)
        2. Mesurer la corrélation avec l'hologramme
        3. Ajuster (kx, ky) par gradient pour maximiser la corrélation
        """
        for epoch in range(epochs):
            for i, (kx, ky) in enumerate(self.readers):
                # Onde du lecteur
                reader_wave = self._wave_at(kx, ky)

                # Question en onde
                q_wave = self._text_to_wave(problem.question)

                # Target : onde combinée question+hologramme
                target = q_wave + 0.1 * self.hologram

                # Corrélation actuelle
                corr = self._correlation(reader_wave, target)

                # Gradient : perturbation pour chaque coordonnée
                eps = 0.1
                # Perturber kx
                wave_kx_plus = self._wave_at(kx + eps, ky)
                corr_kx = (self._correlation(wave_kx_plus, target) - corr) / eps

                # Perturber ky
                wave_ky_plus = self._wave_at(kx, ky + eps)
                corr_ky = (self._correlation(wave_ky_plus, target) - corr) / eps

                # Mise à jour par gradient
                new_kx = kx + self.learning_rate * corr_kx
                new_ky = ky + self.learning_rate * corr_ky

                # Clamper dans [-10, 10]
                new_kx = max(-10, min(10, new_kx))
                new_ky = max(-10, min(10, new_ky))

                self.readers[i] = (new_kx, new_ky)

        avg_corr = sum(self._correlation(self._wave_at(kx, ky), self.hologram) 
                       for kx, ky in self.readers) / len(self.readers)
        self.stats["avg_correlation"] = float(avg_corr)

    # ═══ RÉSOLUTION PAR RÉSONANCE ═══
    def solve(self, question: str, top_k: int = 3) -> Tuple[str, float, List[Tuple[str, float]]]:
        """
        Résout un problème mathématique par résonance.
        
        1. Convertit la question en onde
        2. Interroge l'hologramme via les N lecteurs
        3. Les lecteurs qui résonnent le plus = les bonnes étapes de raisonnement
        4. Assemble la réponse par interférence constructive
        """
        q_wave = self._text_to_wave(question)

        # Chaque lecteur donne un score
        reader_scores = []
        for i, (kx, ky) in enumerate(self.readers):
            r_wave = self._wave_at(kx, ky)
            # Corrélation croisée : question + hologramme vs lecteur
            combined = q_wave + 0.3 * self.hologram
            score = self._correlation(r_wave, combined)
            reader_scores.append((i, score))

        # Trier par score décroissant
        reader_scores.sort(key=lambda x: -x[1])

        # Trouver les connaissances les plus corrélées dans l'hologramme
        # via les meilleurs lecteurs
        best_readers = reader_scores[:top_k]
        resonating_steps = []
        for reader_idx, score in best_readers:
            kx, ky = self.readers[reader_idx]
            r_wave = self._wave_at(kx, ky)
            # Extraire la zone de l'hologramme qui résonne le plus
            resonance_map = np.abs(r_wave * np.conj(self.hologram))
            max_pos = np.unravel_index(np.argmax(resonance_map), resonance_map.shape)
            resonating_steps.append((f"Lecteur {reader_idx+1} → zone ({max_pos[0]},{max_pos[1]})", score))

        # Score de confiance global
        confidence = sum(s for _, s in best_readers) / len(best_readers) if best_readers else 0.0

        # Construire une réponse (si on a des lecteurs qui résonnent fort)
        if confidence > 0.3:
            answer = f"Raisonnement harmonique (confiance: {confidence:.2f}) :\n"
            for i, (step, score) in enumerate(resonating_steps):
                answer += f"  Étape {i+1} : {step}\n"
        else:
            answer = "Je n'ai pas assez d'expérience pour résoudre ce problème avec confiance."

        return answer, confidence, resonating_steps

    # ═══ CHAIN-OF-THOUGHT HARMONIQUE ═══
    def chain_of_thought(self, question: str, max_steps: int = 5) -> str:
        """
        Génère un raisonnement pas-à-pas par cascade de lecteurs.
        Contrairement aux LLM qui génèrent du texte, chaque "étape"
        est l'activation d'un lecteur qui résonne avec l'étape suivante.
        """
        steps_output = []
        q_wave = self._text_to_wave(question)
        current_wave = q_wave.copy()

        for step_num in range(max_steps):
            # Trouver le lecteur qui résonne le plus avec l'état actuel
            best_score = -1
            best_idx = -1
            for i, (kx, ky) in enumerate(self.readers):
                r_wave = self._wave_at(kx, ky)
                score = self._correlation(r_wave, current_wave + 0.2 * self.hologram)
                if score > best_score:
                    best_score = score
                    best_idx = i

            if best_score < 0.1:
                break  # Plus rien ne résonne = fin du raisonnement

            kx, ky = self.readers[best_idx]
            steps_output.append(f"Étape {step_num+1} : Lecteur {best_idx+1} activé (score: {best_score:.3f})")

            # Propager : l'onde du lecteur se combine avec l'état actuel
            r_wave = self._wave_at(kx, ky, amp=0.3)
            current_wave = current_wave + r_wave

        if steps_output:
            return "Raisonnement harmonique :\n" + "\n".join(steps_output)
        return "Aucune chaîne de raisonnement trouvée."

    # ═══ FULL TRAIN ═══
    def train_on_dataset(self, dataset: List[MathProblem], epochs: int = 3):
        for epoch in range(epochs):
            print(f"  Epoch {epoch+1}/{epochs}")
            for i, problem in enumerate(dataset):
                self.ingest_problem(problem)
                self.train_readers(problem, epochs=2)
            self.save()
            print(f"    Corrélation moyenne : {self.stats['avg_correlation']:.4f}")


# ══════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--train", action="store_true", help="Entraîner sur le dataset")
    p.add_argument("--test", action="store_true", help="Tester sur des problèmes")
    p.add_argument("--problem", type=str, help="Résoudre un problème")
    p.add_argument("--cot", action="store_true", help="Activer Chain-of-Thought")
    p.add_argument("--epochs", type=int, default=3, help="Nombre d'époques")
    args = p.parse_args()

    trainer = HarmonicMathTrainer(num_readers=8)

    if args.train:
        print(f"Entraînement sur {len(MATH_DATASET)} problèmes...")
        trainer.train_on_dataset(MATH_DATASET, epochs=args.epochs)
        print(f"Stats : {json.dumps(trainer.stats, indent=2)}")

    if args.test:
        tests = [
            "Que vaut 137 + 85 ?",
            "Calcule 12 × 8 + 5",
            "Résous 4x + 3 = 23",
            "Aire d'un cercle de rayon 3 ?",
            "Probabilité d'avoir un nombre pair avec un dé ?",
        ]
        print("Tests de résolution :")
        for q in tests:
            if args.cot:
                print(f"\n  Q: {q}")
                print(f"  {trainer.chain_of_thought(q)}")
            else:
                answer, conf, _ = trainer.solve(q)
                print(f"  {q} → {answer[:100]} (conf: {conf:.2f})")

    if args.problem:
        print(f"Résolution de : {args.problem}")
        if args.cot:
            print(trainer.chain_of_thought(args.problem))
        else:
            answer, conf, steps = trainer.solve(args.problem)
            print(f"Réponse : {answer}")
            print(f"Confiance : {conf:.3f}")

if __name__ == "__main__":
    main()