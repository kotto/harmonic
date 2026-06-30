"""
Harmonic AI v1.0 — Intelligence ondulatoire unifiée
=====================================================
Une seule classe. Toutes les capacités.

Usage:
  from harmonic_ai import HarmonicAI
  
  ai = HarmonicAI()
  
  # Raisonnement
  ai.ask("explique la lumiere")
  ai.reason("pourquoi le coeur pompe le sang")
  
  # Créativité
  ai.create(n=5)
  ai.metaphor()
  ai.haiku()
  ai.surreal()
  
  # Apprentissage
  ai.learn("Marie Curie a decouvert le radium", "PHYSIQUE_FOND")
  ai.ingest("chemin/vers/corpus/")
  
  # Persistance
  ai.save("mon_modele.hai")
  ai.load("mon_modele.hai")
  
  # Stats
  print(ai.stats)
"""

import os, sys, json, time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np

# Chemin du module
_MODULE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_MODULE_DIR))

from harmonic_model import HarmonicModel, build_waves, KNOWLEDGE_BASE
from reasoning_engine import ReasoningEngine
from style_engine import StyleEngine


class HarmonicAI:
    """
    Intelligence Artificielle Harmonique — Interface unifiée.
    
    Capacités :
      - ask()      : réponse factuelle
      - reason()   : chaîne de raisonnement
      - create()   : connexions créatives entre domaines
      - metaphor() : métaphores poétiques
      - haiku()    : poésie japonaise
      - surreal()  : images surréalistes
      - learn()    : apprentissage de nouveaux faits
      - ingest()   : ingestion massive depuis un corpus
      - save()     : persistance complète
      - load()     : restauration complète
    """
    
    def __init__(self, use_memory: bool = True):
        self.model = HarmonicModel(use_memory=use_memory)
        self.engine = ReasoningEngine(self.model)
        self._load_extended_kb()
    
    def _load_extended_kb(self):
        """Charge la base étendue si disponible."""
        kb_path = _MODULE_DIR.parent / "data" / "bootstrapper_output" / "knowledge_base.npz"
        if kb_path.exists():
            try:
                data = np.load(str(kb_path), allow_pickle=True)
                ingested = list(data['facts'])
                added = 0
                for s, r, o, sec in ingested:
                    if (s, r, o, sec) not in self.model.knowledge_base:
                        self.model.knowledge_base.append((s, r, o, sec))
                        added += 1
                if added > 0:
                    self.model.kx, self.model.ky, self.model.w2i = build_waves(
                        self.model.knowledge_base
                    )
            except Exception:
                pass
    
    # ═══════════════════════════════════════════════════════════════════
    # RAISONNEMENT
    # ═══════════════════════════════════════════════════════════════════
    
    def ask(self, question: str) -> str:
        """Réponse factuelle — utilise le meilleur chemin de raisonnement."""
        try:
            return self.engine.reason(question, max_depth=1)
        except Exception:
            return self.model.ask(question)
    
    def reason(self, question: str) -> str:
        """Chaîne de raisonnement avec style élégant."""
        return self.engine.reason(question)
    
    # ═══════════════════════════════════════════════════════════════════
    # CRÉATIVITÉ
    # ═══════════════════════════════════════════════════════════════════
    
    def create(self, n: int = 5) -> List[str]:
        """Connexions créatives entre domaines."""
        return self.engine.create(n_ideas=n)
    
    def create_ondulatoire(self, concept_a: str = None, concept_b: str = None, n: int = 3) -> List[str]:
        """
        Créativité ondulatoire profonde — superposition + sondage mémoire.
        
        Superpose les ondes de deux concepts, sonde l'hologramme,
        et fait ÉMERGER les ponts créatifs du substrat ondulatoire.
        """
        return self.engine.create_ondulatoire(concept_a, concept_b, n_idees=n)
    
    def metaphor(self, n: int = 5) -> List[str]:
        """Métaphores poétiques par interférence."""
        return self.engine.metaphor(n_metaphores=n)
    
    def haiku(self) -> str:
        """Haïku généré par résonance."""
        return self.engine.haiku()
    
    def surreal(self, n: int = 4) -> List[str]:
        """Images surréalistes par interférence faible."""
        return self.engine.surreal(n_images=n)
    
    # ═══════════════════════════════════════════════════════════════════
    # APPRENTISSAGE
    # ═══════════════════════════════════════════════════════════════════
    
    def learn(self, sujet: str, relation: str = None, objet: str = None,
              secteur: str = "GENERAL"):
        """
        Apprend un nouveau fait.
        
        Forme simple : ai.learn("Marie Curie a decouvert le radium", "PHYSIQUE_FOND")
        Forme complète : ai.learn("lumiere", "est", "onde electromagnetique", "PHYSIQUE_FOND")
        """
        if relation is None:
            # Forme simple : extraire automatiquement
            from bootstrapper import extract_triples_simple
            triples = extract_triples_simple(sujet)
            for s, r, o, sec in triples:
                self.model.learn(s, r, o, sec)
        else:
            self.model.learn(sujet, relation, objet, secteur)
    
    def ingest(self, corpus_dir: str, max_files: int = None):
        """
        Ingestion massive depuis un répertoire de textes.
        Utilise DeepSeek pour l'extraction de triplets.
        """
        from bootstrapper import HarmonicBootstrapper
        boot = HarmonicBootstrapper()
        n = boot.ingest_corpus(corpus_dir, max_files=max_files or 50)
        # Mettre à jour le modèle avec les nouveaux faits
        for s, r, o, sec in boot.model.knowledge_base:
            if (s, r, o, sec) not in self.model.knowledge_base:
                self.model.knowledge_base.append((s, r, o, sec))
        self.model.kx, self.model.ky, self.model.w2i = build_waves(
            self.model.knowledge_base
        )
        return n
    
    # ═══════════════════════════════════════════════════════════════════
    # PERSISTANCE
    # ═══════════════════════════════════════════════════════════════════
    
    def save(self, path: str):
        """Sauvegarde complète du modèle."""
        data = {
            'knowledge_base': self.model.knowledge_base,
            'kx': self.model.kx.tolist() if hasattr(self.model.kx, 'tolist') else self.model.kx,
            'ky': self.model.ky.tolist() if hasattr(self.model.ky, 'tolist') else self.model.ky,
            'word_to_id': self.model.w2i,
            'memoire_H_real': self.model.memoire.H.real.tolist() if self.model.memoire else [],
            'memoire_H_imag': self.model.memoire.H.imag.tolist() if self.model.memoire else [],
            'n_experiences': self.model.memoire.n_experiences if self.model.memoire else 0,
        }
        np.savez(path, **data)
    
    def load(self, path: str):
        """Charge un modèle sauvegardé."""
        data = np.load(path, allow_pickle=True)
        self.model.knowledge_base = list(data['knowledge_base'])
        self.model.kx = np.array(data['kx'])
        self.model.ky = np.array(data['ky'])
        self.model.w2i = dict(data['word_to_id'].item())
        if self.model.memoire and 'memoire_H_real' in data:
            H = np.array(data['memoire_H_real']) + 1j * np.array(data['memoire_H_imag'])
            self.model.memoire.H = H
            self.model.memoire.n_experiences = int(data['n_experiences'])
    
    # ═══════════════════════════════════════════════════════════════════
    # STATS
    # ═══════════════════════════════════════════════════════════════════
    
    @property
    def stats(self) -> dict:
        return {
            'faits': len(self.model.knowledge_base),
            'vocabulaire': len(self.model.w2i),
            'experiences': self.model.experience_count,
            'energie': round(self.model.memoire.energie, 0) if self.model.memoire and hasattr(self.model.memoire, 'energie') else 0,
        }


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Harmonic AI")
    parser.add_argument('question', nargs='?', help='Question to ask')
    parser.add_argument('--reason', action='store_true', help='Use reasoning mode')
    parser.add_argument('--create', type=int, default=0, help='Generate N creative connections')
    parser.add_argument('--metaphor', type=int, default=0, help='Generate N metaphors')
    parser.add_argument('--haiku', action='store_true', help='Generate a haiku')
    parser.add_argument('--surreal', type=int, default=0, help='Generate N surreal images')
    parser.add_argument('--stats', action='store_true', help='Show stats')
    parser.add_argument('--learn', type=str, help='Learn a fact (text or S|R|O|SEC)')
    parser.add_argument('--save', type=str, help='Save model to path')
    parser.add_argument('--load', type=str, help='Load model from path')
    args = parser.parse_args()
    
    ai = HarmonicAI()
    
    if args.load:
        ai.load(args.load)
        print(f"Model loaded from {args.load}")
    
    if args.learn:
        parts = args.learn.split('|')
        if len(parts) >= 4:
            ai.learn(parts[0], parts[1], parts[2], parts[3])
        else:
            ai.learn(args.learn)
        print(f"Learned: {args.learn[:80]}")
    
    if args.stats:
        print(f"Stats: {ai.stats}")
    
    if args.question:
        if args.reason:
            print(ai.reason(args.question))
        else:
            print(ai.ask(args.question))
    
    if args.create:
        for i, idea in enumerate(ai.create(args.create)):
            print(f"{i+1}. {idea}\n")
    
    if args.metaphor:
        for m in ai.metaphor(args.metaphor):
            print(f"  ✨ {m}")
    
    if args.haiku:
        print(ai.haiku())
    
    if args.surreal:
        for s in ai.surreal(args.surreal):
            print(f"  🎨 {s}")
    
    if args.save:
        ai.save(args.save)
        print(f"Model saved to {args.save}")


if __name__ == '__main__':
    main()
