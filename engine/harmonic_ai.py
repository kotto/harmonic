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
    
    def __init__(self, use_memory: bool = True, enable_bootstrapper: bool = True):
        self.model = HarmonicModel(use_memory=use_memory)
        self.engine = ReasoningEngine(self.model)
        self._load_extended_kb()
        
        # Bootstrapper pour le sevrage progressif du LLM
        self.bootstrapper = None
        if enable_bootstrapper:
            from bootstrapper import HarmonicBootstrapper
            self.bootstrapper = HarmonicBootstrapper(model=self.model)
        
        # Mémoire conversationnelle multi-tours
        import importlib.util, sys
        spec = importlib.util.spec_from_file_location(
            "conversation_memory",
            str(_MODULE_DIR / "memory" / "conversation.py")
        )
        conv_module = importlib.util.module_from_spec(spec)
        sys.modules["conversation_memory"] = conv_module
        spec.loader.exec_module(conv_module)
        self.conversation = conv_module.ConversationMemory(max_messages=50)
    
    def _confidence_score(self, response: str, question: str) -> float:
        """
        Évalue la confiance dans une réponse (0 = pas confiance, 1 = confiance totale).
        
        Stratégie : vérifier que la réponse apporte de l'information NOUVELLE,
        pas juste un echo de la question via les templates.
        """
        if not response or len(response) < 20:
            return 0.0
        low_phrases = ['je ne connais pas', 'je ne trouve pas', 'pas de resonance',
                       'connais pas assez', 'ne comprends pas', 'pas assez de connaissances']
        if any(p in response.lower() for p in low_phrases):
            return 0.0
        
        # Extraire le SUJET NET de la question (sans les mots-outils)
        stopwords = {'le', 'la', 'les', 'de', 'des', 'du', 'un', 'une', 'et', 'est', 'a',
                     'que', 'qui', 'quoi', 'dans', 'sur', 'pour', 'avec', 'par', 'en',
                     'the', 'a', 'an', 'is', 'are', 'of', 'in', 'on', 'at', 'to',
                     'what', 'who', 'how', 'why', 'when', 'where', 'which',
                     'invente', 'cree', 'decouvert', 'fonctionne', 'explique', 'trouve',
                     'fait', 'dit', 'donne', 'utilise', 'appelle', 'signifie',
                     'comment', 'pourquoi', 'quand', 'ou', 'combien', 'est-ce'}
        q_words = set(w.strip('.,!?;:()[]{}') for w in question.lower().split()
                     if len(w) > 2 and w not in stopwords)
        
        if not q_words:
            return 0.4
        
        # Identifier les MOTS-CLÉS de la question (les plus longs, les plus spécifiques)
        key_words = sorted(q_words, key=len, reverse=True)[:3]  # top 3 mots les plus longs
        
        # Vérifier que les MOTS-CLÉS n'apparaissent PAS comme simples échos
        # (si un mot-clé apparaît suivi d'un verbe générique → echo du template)
        echo_score = 0
        for kw in key_words:
            # Chercher le mot-clé dans la réponse
            pos = response.lower().find(kw)
            if pos >= 0:
                # Vérifier le contexte : est-ce un echo ?
                context = response.lower()[max(0,pos-20):pos+len(kw)+30]
                echo_patterns = ['éclaire ' + kw, 'comprendre ' + kw, 'cerner ' + kw,
                                'phénomène de ' + kw, 'concept de ' + kw]
                if any(p in context for p in echo_patterns):
                    echo_score += 1  # c'est un echo, pas une vraie réponse
        
        # Si tous les mots-clés sont des échos → très faible confiance
        if len(key_words) > 0 and echo_score >= len(key_words):
            return 0.1
        
        # Si la plupart sont des échos → faible
        if len(key_words) > 0 and echo_score / len(key_words) >= 0.5:
            return 0.2
        
        # Vérifier aussi la présence RÉELLE des mots-clés dans la réponse
        r_words = set(w.strip('.,!?;:()[]{}') for w in response.lower().split() if len(w) > 2)
        key_overlap = set(key_words) & r_words
        key_ratio = len(key_overlap) / len(key_words) if key_words else 1.0
        
        # Si aucun mot-clé n'apparaît → très faible
        if key_ratio == 0:
            return 0.15
        
        # Si peu de mots-clés apparaissent → faible
        if key_ratio < 0.3:
            return 0.25
        
        # Sinon, confiance basée sur la longueur et couverture
        base = 0.35 + key_ratio * 0.3 + min(0.25, len(response) / 400)
        return min(1.0, base)
    
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
        """Réponse factuelle avec mémoire conversationnelle et fallback LLM."""
        # Enrichir la question avec le contexte de conversation
        enriched = self._enrich_with_context(question)
        
        # Essayer le moteur harmonique d'abord (raisonnement multi-sauts)
        try:
            response = self.engine.reason(enriched, max_depth=2)
        except Exception:
            response = self.model.ask(enriched)
        
        # Si confiance faible et bootstrapper disponible → fallback LLM
        if self.bootstrapper is not None:
            confidence = self._confidence_score(response, enriched)
            if confidence < 0.35:
                try:
                    llm_text = self.bootstrapper._llm_fallback(enriched)
                    if llm_text:
                        response = llm_text
                        # Apprendre de la réponse LLM
                        from bootstrapper import extract_triples_simple
                        triples = extract_triples_simple(llm_text)
                        for s, r, o, sec in triples:
                            self.model.knowledge_base.append((s, r, o, sec))
                        if triples:
                            self.model.rebuild_waves()
                            # Mettre à jour l'engine avec le nouveau modèle
                            self.engine = ReasoningEngine(self.model)
                except Exception:
                    pass
        
        # Enregistrer dans la mémoire conversationnelle
        self.conversation.add("user", question)
        self.conversation.add("assistant", response)
        
        # Correction orthographique finale
        try:
            from style_engine import _fix_accents
            response = _fix_accents(response)
        except ImportError:
            pass
        
        return response
    
    def _enrich_with_context(self, question: str) -> str:
        """
        Enrichit une question avec le sujet de la conversation.
        Pour les questions courtes (follow-up), ajoute le sujet précédent.
        """
        recent = self.conversation.messages[-6:] if self.conversation.messages else []
        if not recent:
            return question
        
        # Si la question est courte (follow-up probable)
        q_words = question.lower().split()
        if len(q_words) <= 6:
            # Trouver la dernière question USER (le sujet principal)
            last_user_q = None
            for msg in reversed(recent):
                if msg.role == "user":
                    last_user_q = msg.content
                    break
            
            if last_user_q:
                # Extraire les mots-clés de la DERNIÈRE QUESTION (pas de la réponse)
                stopwords = {'le', 'la', 'les', 'de', 'des', 'du', 'un', 'une', 'et', 'est', 'a',
                           'que', 'qui', 'quoi', 'dans', 'sur', 'pour', 'avec', 'par', 'en',
                           'the', 'of', 'in', 'on', 'at', 'to', 'is', 'are', 'comment',
                           'pourquoi', 'quand', 'quelle', 'quel', 'quels', 'quelles',
                           'explique', 'parle', 'decris', 'definis'}
                sujet_words = [w.strip('.,!?;:') for w in last_user_q.lower().split()
                             if len(w) > 2 and w not in stopwords]
                if sujet_words:
                    context = ' '.join(sujet_words[:4])
                    return f"{question} (a propos de: {context})"
        
        return question
    
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
        s = {
            'faits': len(self.model.knowledge_base),
            'vocabulaire': len(self.model.w2i),
            'experiences': self.model.experience_count,
            'energie': round(self.model.memoire.energie, 0) if self.model.memoire and hasattr(self.model.memoire, 'energie') else 0,
        }
        if self.bootstrapper:
            s['autonomie'] = round(self.bootstrapper.autonomie * 100, 1)
            s['llm_calls'] = self.bootstrapper._llm_calls
        return s


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
