#!/usr/bin/env python3
"""
DATASET D'ENTRAINEMENT POUR L'ADAPTATEUR HARMONIQUE
=====================================================
Collecte les logs du proxy harmonique et cree un dataset
pour entrainer l'adaptateur a generer les meilleures signatures 7D.

Usage:
    python train_harmonic_adapter_dataset.py --collect   # Collecter les logs
    python train_harmonic_adapter_dataset.py --train     # Entrainer l'adaptateur
    python train_harmonic_adapter_dataset.py --eval      # Evaluer les performances
"""

import os, sys, json, time, hashlib, random
import numpy as np
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple

# Constantes harmoniques
PHI = 1.618033988749895
ALPHA = 1.175569459083219

# ---------------------------------------------------------------------------
# Collecteur de logs
# ---------------------------------------------------------------------------
class HarmonicLogCollector:
    """Collecte les logs du proxy harmonique pour creer un dataset."""
    
    def __init__(self, log_dir: str = "harmonic_logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.logs = []
    
    def collect_from_server(self, server_url: str = "http://localhost:8080", 
                           num_samples: int = 100) -> List[Dict]:
        """Collecte des echantillons depuis le serveur harmonique."""
        import requests
        
        prompts = [
            # Mathematiques
            "Calcule la derivee de f(x) = x^3 * sin(x)",
            "Resous l'equation differentielle y'' + y = 0",
            "Quelle est la limite de (1+1/n)^n quand n tend vers l'infini?",
            "Integre de 0 a pi: sin(x) * cos(x) dx",
            "Montre que la serie harmonique diverge",
            
            # Code
            "Ecris une fonction Python qui implemente le tri fusion",
            "Explique le pattern decorateur en Python avec un exemple",
            "Comment optimiser une boucle for en numpy?",
            "Ecris une classe Singleton thread-safe en Python",
            "Implemente un cache LRU avec expiration",
            
            # Creatif
            "Ecris un poeme sur l'intelligence artificielle et l'harmonie",
            "Raconte l'histoire d'un scientifique qui decouvre une 5e dimension",
            "Decris un monde ou les emotions sont des couleurs visibles",
            "Imagine une conversation entre Pythagore et un ordinateur quantique",
            "Ecris une metaphore sur la resonance harmonique",
            
            # Raisonnement
            "Pourquoi le ciel est-il bleu? Explique en detail",
            "Compare les approches deductive et inductive en science",
            "Quelle est la difference entre correlation et causalite?",
            "Explique le paradoxe de Fermi et ses solutions possibles",
            "Analyse les implications de l'experience de la double fente",
            
            # General
            "Qu'est-ce que la conscience selon les neurosciences?",
            "Explique la theorie de la relativite generale simplement",
            "Comment fonctionne un transformer en deep learning?",
            "Quels sont les enjeux ethiques de l'IA generale?",
            "Decris l'architecture d'un LLM moderne",
            
            # Longs prompts
            "En considerant les travaux recents sur les modeles de langage, les avancees en apprentissage profond, et les decouvertes en neurosciences computationnelles, peux-tu elaborer une synthese sur la nature de l'intelligence et les conditions necessaires pour qu'un systeme artificiel puisse developper une forme de conscience? Developpe ta reponse en explorant les dimensions philosophiques, techniques et ethiques de cette question.",
            
            # Prompts techniques
            "Analyse la complexite algorithmique de l'algorithme de Dijkstra et propose une optimisation utilisant une file de priorite de Fibonacci. Compare avec l'utilisation d'un tas binaire standard.",
            "Explique le principe de fonctionnement des GANs (Generative Adversarial Networks) et leurs applications dans la generation d'images, en detaillant le processus d'entrainement et les defis associes.",
        ]
        
        results = []
        for i, prompt in enumerate(prompts[:num_samples]):
            try:
                r = requests.post(
                    f"{server_url}/v1/chat/completions",
                    json={
                        "model": "harmonic-proxy",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 300,
                    },
                    timeout=30
                )
                data = r.json()
                
                # Extraire les signatures et metriques
                harmonic = data.get("harmonic_analysis", {})
                signatures = harmonic.get("signatures", [0]*7)
                
                entry = {
                    "prompt": prompt,
                    "prompt_len": len(prompt),
                    "signatures": signatures,
                    "temperature": harmonic.get("temperature", 0.5),
                    "top_p": harmonic.get("top_p", 0.9),
                    "top_k": harmonic.get("top_k", 50),
                    "resonance": harmonic.get("resonance", 0.0),
                    "latency_ms": harmonic.get("latency_ms", 0),
                    "response": data.get("choices", [{}])[0].get("message", {}).get("content", ""),
                    "timestamp": time.time(),
                }
                results.append(entry)
                print(f"  [{i+1}/{len(prompts[:num_samples])}] Resonance: {entry['resonance']:.4f}")
                
            except Exception as e:
                print(f"  [{i+1}/{len(prompts[:num_samples])}] Erreur: {e}")
        
        self.logs = results
        return results
    
    def save_dataset(self, filename: str = "harmonic_dataset.json"):
        """Sauvegarde le dataset."""
        path = os.path.join(self.log_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Dataset sauvegarde: {path} ({len(self.logs)} echantillons)")
        return path
    
    def load_dataset(self, filename: str = "harmonic_dataset.json") -> List[Dict]:
        """Charge un dataset existant."""
        path = os.path.join(self.log_dir, filename)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.logs = json.load(f)
            print(f"[OK] Dataset charge: {path} ({len(self.logs)} echantillons)")
        return self.logs
    
    def analyze_dataset(self):
        """Analyse statistique du dataset."""
        if not self.logs:
            print("[ERREUR] Dataset vide")
            return
        
        signatures = np.array([e["signatures"] for e in self.logs])
        resonances = np.array([e["resonance"] for e in self.logs])
        latencies = np.array([e["latency_ms"] for e in self.logs])
        
        print(f"\n{'='*60}")
        print(f"ANALYSE DU DATASET HARMONIQUE")
        print(f"{'='*60}")
        print(f"  Echantillons: {len(self.logs)}")
        print(f"\n  Signatures 7D (moyennes):")
        dims = ["phi", "alpha", "creativite", "factuel", "code", "raisonnement", "abstraction"]
        for i, (dim, mean, std) in enumerate(zip(dims, signatures.mean(0), signatures.std(0))):
            print(f"    {dim}: {mean:.4f} +/- {std:.4f}")
        
        print(f"\n  Resonance:")
        print(f"    Moyenne: {resonances.mean():.4f}")
        print(f"    Min: {resonances.min():.4f}")
        print(f"    Max: {resonances.max():.4f}")
        print(f"    Std: {resonances.std():.4f}")
        
        print(f"\n  Latence:")
        print(f"    Moyenne: {latencies.mean():.1f} ms")
        print(f"    Min: {latencies.min():.1f} ms")
        print(f"    Max: {latencies.max():.1f} ms")
        
        # Top prompts par resonance
        sorted_logs = sorted(self.logs, key=lambda x: x["resonance"], reverse=True)
        print(f"\n  Top 5 prompts (meilleure resonance):")
        for i, e in enumerate(sorted_logs[:5]):
            print(f"    {i+1}. Resonance: {e['resonance']:.4f} | {e['prompt'][:60]}...")
        
        return {
            "num_samples": len(self.logs),
            "signatures_mean": signatures.mean(0).tolist(),
            "signatures_std": signatures.std(0).tolist(),
            "resonance_mean": float(resonances.mean()),
            "latency_mean": float(latencies.mean()),
        }


# ---------------------------------------------------------------------------
# Entraineur d'adaptateur harmonique
# ---------------------------------------------------------------------------
class HarmonicAdapterTrainer:
    """Entraine l'adaptateur harmonique a partir du dataset."""
    
    def __init__(self, dataset_path: str = "harmonic_logs/harmonic_dataset.json"):
        with open(dataset_path, "r", encoding="utf-8") as f:
            self.dataset = json.load(f)
        print(f"[OK] Dataset charge: {len(self.dataset)} echantillons")
        
        # Preparer les donnees
        self.prompts = [e["prompt"] for e in self.dataset]
        self.signatures = np.array([e["signatures"] for e in self.dataset])
        self.resonances = np.array([e["resonance"] for e in self.dataset])
        
        # Normaliser les signatures
        self.sig_mean = self.signatures.mean(0)
        self.sig_std = self.signatures.std(0).clip(1e-8)
        self.signatures_norm = (self.signatures - self.sig_mean) / self.sig_std
    
    def extract_features(self, text: str) -> np.ndarray:
        """Extrait des features simples du texte."""
        words = text.split()
        word_lens = [len(w) for w in words]
        
        features = np.zeros(12, dtype=np.float32)
        features[0] = len(words)  # Nombre de mots
        features[1] = len(text)   # Longueur totale
        features[2] = np.mean(word_lens) if word_lens else 0  # Longueur moyenne
        features[3] = np.std(word_lens) if len(word_lens) > 1 else 0  # Ecart-type
        features[4] = len(set(w.lower() for w in words)) / max(len(words), 1)  # Diversite
        features[5] = sum(1 for w in words if any(c.isdigit() for c in w)) / max(len(words), 1)  # Ratio chiffres
        features[6] = sum(1 for w in words if w[0].isupper() if w) / max(len(words), 1)  # Majuscules
        features[7] = text.count("?") / max(len(words), 1)  # Questions
        features[8] = text.count("!") / max(len(words), 1)  # Exclamations
        features[9] = text.count(",") / max(len(words), 1)  # Virgules
        features[10] = text.count(".") / max(len(words), 1)  # Points
        features[11] = sum(1 for w in words if len(w) > 8) / max(len(words), 1)  # Mots longs
        
        return features
    
    def train_linear_model(self):
        """Entraine un modele lineaire simple pour predire les signatures."""
        from sklearn.linear_model import Ridge
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import mean_squared_error, r2_score
        
        # Extraire les features
        X = np.array([self.extract_features(p) for p in self.prompts])
        y = self.signatures_norm
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Entrainer un modele par dimension
        models = []
        scores = []
        
        print(f"\n{'='*60}")
        print(f"ENTRAINEMENT DU MODELE PREDICTIF")
        print(f"{'='*60}")
        
        dims = ["phi", "alpha", "creativite", "factuel", "code", "raisonnement", "abstraction"]
        
        for i, dim in enumerate(dims):
            model = Ridge(alpha=1.0)
            model.fit(X_train, y_train[:, i])
            
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test[:, i], y_pred)
            r2 = r2_score(y_test[:, i], y_pred)
            
            models.append(model)
            scores.append({"dim": dim, "mse": mse, "r2": r2})
            
            print(f"  {dim}: MSE={mse:.6f}, R2={r2:.4f}")
        
        # Score global
        y_pred_all = np.array([m.predict(X_test) for m in models]).T
        global_r2 = r2_score(y_test, y_pred_all)
        print(f"\n  Score global R2: {global_r2:.4f}")
        
        self.models = models
        return models, scores
    
    def predict_signatures(self, prompt: str) -> np.ndarray:
        """Predire les signatures optimales pour un prompt."""
        if not hasattr(self, 'models'):
            print("[ERREUR] Modele non entraine")
            return np.zeros(7)
        
        features = self.extract_features(prompt).reshape(1, -1)
        sig_norm = np.array([m.predict(features)[0] for m in self.models])
        sig = sig_norm * self.sig_std + self.sig_mean
        return sig.clip(0, 1)
    
    def save_model(self, path: str = "harmonic_logs/adapter_model.npz"):
        """Sauvegarde le modele entraine."""
        if not hasattr(self, 'models'):
            print("[ERREUR] Modele non entraine")
            return
        
        np.savez(path,
                 sig_mean=self.sig_mean,
                 sig_std=self.sig_std,
                 coefs=np.array([m.coef_ for m in self.models]),
                 intercepts=np.array([m.intercept_ for m in self.models]))
        print(f"\n[OK] Modele sauvegarde: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Dataset et entrainement adaptateur harmonique")
    parser.add_argument("--collect", action="store_true", help="Collecter les logs")
    parser.add_argument("--train", action="store_true", help="Entrainer le modele")
    parser.add_argument("--eval", action="store_true", help="Evaluer le dataset")
    parser.add_argument("--samples", type=int, default=30, help="Nombre d'echantillons")
    parser.add_argument("--server", type=str, default="http://localhost:8080", help="URL du serveur")
    
    args = parser.parse_args()
    
    collector = HarmonicLogCollector()
    
    if args.collect:
        print(f"Collecte de {args.samples} echantillons depuis {args.server}...")
        collector.collect_from_server(args.server, args.samples)
        collector.save_dataset()
        collector.analyze_dataset()
    
    if args.eval:
        collector.load_dataset()
        collector.analyze_dataset()
    
    if args.train:
        trainer = HarmonicAdapterTrainer()
        trainer.train_linear_model()
        trainer.save_model()
        
        # Demo
        print(f"\n{'='*60}")
        print(f"DEMO - Prediction de signatures")
        print(f"{'='*60}")
        test_prompts = [
            "Ecris un code Python pour trier une liste",
            "Explique la theorie de la relativite",
            "Ecris un poeme sur la lune",
            "Calcule l'integrale de x^2 de 0 a 1",
        ]
        for p in test_prompts:
            sig = trainer.predict_signatures(p)
            print(f"\n  Prompt: {p[:50]}...")
            print(f"  Signatures predites: {[f'{s:.3f}' for s in sig]}")
    
    if not any([args.collect, args.train, args.eval]):
        parser.print_help()


if __name__ == "__main__":
    main()
