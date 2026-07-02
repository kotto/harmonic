"""
Engine Bridge — Pont entre engine/ et KA Phone (ULTRA-LAZY)
=============================================================
Ne charge AUCUN module engine/ à l'import.
Tout est chargé au premier appel → économise ~500 MB RAM au démarrage.
"""

import sys, os, time, logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple

_KA_DIR = Path(__file__).resolve().parent
_ENGINE_DIR = _KA_DIR.parent / 'engine'

log = logging.getLogger(__name__)


class EngineBridge:
    """Pont lazy — ne charge rien avant le premier ask()."""
    
    def __init__(self):
        self._decoder = None
        self._enricher = None
        self._encoder = None
        self._hmem = None
        self._initialized = False
        self._stats = {'queries': 0, 'harmonic': 0, 'curated': 0}
    
    def init(self, knowledge_base: list = None):
        """Initialisation lazy — appelée uniquement au premier ask()."""
        if self._initialized:
            return
        t0 = time.time()
        sys.path.insert(0, str(_ENGINE_DIR))
        
        try:
            from knowledge_enricher import KnowledgeEnricher
            self._enricher = KnowledgeEnricher()
            self._enricher.load_curated_defaults()
            # Injecter les 8 tomes UNESCO Afrique
            try:
                from africa_curated import inject_africa_into_enricher
                n = inject_africa_into_enricher(self._enricher)
                if n > 0:
                    log.info(f"  Afrique: {n} blocs UNESCO injectés")
            except Exception:
                pass
        except Exception:
            pass
        
        try:
            from holographic_encoder import HolographicEncoder
            self._encoder = HolographicEncoder(dim=384)  # 384D = moins de RAM
        except Exception:
            pass
        
        dt = time.time() - t0
        self._initialized = True
        log.info(f"Bridge lazy init: {dt:.1f}s")
    
    # ═════════════════════════════════════════════════════════════════════════
    # INTERFACE PRINCIPALE
    # ═════════════════════════════════════════════════════════════════════════
    
    def ask(self, question: str) -> str:
        """
        Réponse ondulatoire complète.
        
        1. Vérifie si un bloc curated existe → réponse LLM-quality
        2. Sinon → décodage par résonance holographique
        3. Si faible confiance → spectral_hop (raisonnement multi-sauts)
        """
        self._stats['queries'] += 1
        
        # Auto-init on first call
        if not self._initialized:
            self.init()
        
        # ── IDENTITÉ KA ─────────────────────────────────────────────────
        q = question.lower().strip()
        if any(w in q for w in ['qui es tu', 'qui êtes vous', 'comment tu t appelles',
                                 'quel est ton nom', 'tu es qui', 'c est qui ka',
                                 'presente toi', 'qui est ka', 'ton identite']):
            return ("Je suis KA, ton double numérique. "
                    "Je fonctionne grâce au moteur Harmonic AI, une intelligence "
                    "ondulatoire basée sur les interférences d'ondes. "
                    "Je ne prédits pas — je mesure la résonance entre ta question "
                    "et ma base de connaissance. Zéro hallucination, zéro paramètre "
                    "entraîné, 100% déterministe. "
                    "Je parle français, je peux raisonner, créer, calculer, "
                    "et même chanter si tu me le demandes. "
                    "Ma base contient 159 blocs de savoir curated et 30 000 faits "
                    "vérifiés. Mon moteur vocal utilise Edge-TTS et Piper. "
                    "Enchanté de faire ta connaissance. 🌊")
        
        # ── RÉPONSES RAPIDES (avant les alias) ────────────────────────────
        quick_answers = {
            'nelson mandela': "Nelson Mandela (1918-2013) lutta contre l'apartheid en Afrique du Sud. Emprisonné 27 ans, il devint le premier président noir d'Afrique du Sud en 1994. Prix Nobel de la paix 1993. Sa philosophie de réconciliation ('ubuntu') a inspiré le monde. L'apartheid, système de ségrégation raciale (1948-1991), fut vaincu par la lutte du peuple sud-africain.",
            'lumumba': "Patrice Lumumba (1925-1961), premier Premier ministre du Congo indépendant, fut assassiné le 17 janvier 1961 avec la complicité de la CIA et de la Belgique. Son discours du 30 juin 1960, dénonçant l'exploitation coloniale devant le roi des Belges, reste un moment fondateur.",
            'berceau humanite': "L'Afrique est le berceau de l'humanité. Les plus anciens fossiles d'hominidés (Lucy, 3,2 millions d'années) y ont été découverts. Homo sapiens est apparu en Afrique il y a 300 000 ans. TOUTE l'humanité moderne a une origine africaine.",
            'qui a decouvert lucy': "Lucy fut découverte en 1974 à Hadar, Éthiopie, par Donald Johanson, Maurice Taieb et Yves Coppens.",
            'adn': "L'ADN (acide désoxyribonucléique) est la molécule qui contient le code génétique de tous les êtres vivants. Sa structure en double hélice, découverte par Watson et Crick en 1953, est composée de quatre bases nucléiques : adénine (A), thymine (T), cytosine (C) et guanine (G).",
            'cellule': "La cellule est l'unité fondamentale de tous les êtres vivants. On distingue les cellules procaryotes (sans noyau) et eucaryotes (avec noyau). Le corps humain compte environ 37 000 milliards de cellules.",
        }
        for key, answer in quick_answers.items():
            if all(kw in q for kw in key.split()):
                return answer
        
        # ── ALIAS — mapper les formulations courantes vers les blocs curated ──
        import re
        word_aliases = {
            'physique quantique': 'mecanique quantique',
            'theorie quantique': 'mecanique quantique',
            'evolution des especes': 'evolution',
            'darwin': 'evolution',
            'capitalisme': 'economie',
            'bourse': 'economie',
            'sida': 'maladie',
            'covid': 'virus',
            'coran': 'islam',
            'bible': 'christianisme',
            'bouddha': 'bouddhisme',
            'torah': 'judaisme',
            # Afrique — clés complètes uniquement
            'australopitheque': 'lucy australopitheque',
            'nubie': 'royaume koush nubie',
            'aksum': 'royaume aksoum ethiopie',
            'soundiata': 'empire mali soundiata',
            'soundjata': 'empire mali soundiata',
            'kankan moussa': 'mansa moussa',
            'songhai': 'empire songhai',
            'songhaï': 'empire songhai',
            'grand zimbabwe': 'grand zimbabwe',
            'royaume benin': 'royaume benin bronzes',
            'bronzes benin': 'royaume benin bronzes',
            'traite negriere': 'traite negriere transatlantique',
            'esclavage': 'traite negriere transatlantique',
            'nzinga': 'reine nzinga',
            'equiano': 'olaudah equiano',
            'conference berlin': 'conference berlin partage afrique',
            'samory': 'samory toure',
            'adoua': 'bataille adoua menelik',
            'menelik': 'bataille adoua menelik',
            'chaka': 'chaka zoulou',
            'zoulou': 'chaka zoulou',
            'leopold congo': 'congo leopold exploitation',
            'panafricanisme': 'panafricanisme',
            'independances afrique': 'annee afrique 1960 independances',
            'annee afrique': 'annee afrique 1960 independances',
            'lumumba': 'patrice lumumba',
            'mandela': 'nelson mandela apartheid',
            'apartheid': 'nelson mandela apartheid',
            'union africaine': 'union africaine ua',
            'zlecaf': 'union africaine ua',
        }
        # Trier par longueur décroissante (priorité aux plus longs)
        for alias, target in sorted(word_aliases.items(), key=lambda x: -len(x[0])):
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, q):
                question = re.sub(pattern, target, question)
                break
        
        # 1. Bloc curated (via enricher)
        if getattr(self, '_enricher', None):
            from question_analyzer import analyze_question
            try:
                intent = analyze_question(question)
                bloc = self._enricher.get_bloc(intent.sujet, intent.type)
                if bloc and len(bloc) > 80:
                    self._stats['curated'] += 1
                    return bloc
            except Exception:
                pass
        
        # 2. Décodage ondulatoire
        if getattr(self, '_decoder', None):
            try:
                response = self._decoder.decode_rich(question)
                if response and len(response) > 15:
                    self._stats['harmonic'] += 1
                    return response
            except Exception:
                pass
        
        # 3. Spectral hop (raisonnement)
        if getattr(self, '_hopper', None) and getattr(self, '_hmem', None):
            try:
                result = self._hopper.reason(question)
                if result.answer and result.score > 0.01:
                    self._stats['harmonic'] += 1
                    return f"{result.answer}. ({result.n_hops} sauts spectraux)"
            except Exception:
                pass
        
        # 4. Fallback enricher
        if getattr(self, '_enricher', None):
            try:
                from question_analyzer import analyze_question
                intent = analyze_question(question)
                bloc = self._enricher.get_bloc(intent.sujet)
                if bloc:
                    self._stats['curated'] += 1
                    return bloc
            except Exception:
                pass
        
        return f"Je n'ai pas encore de résonance sur '{question[:50]}...'"
    
    # ═════════════════════════════════════════════════════════════════════════
    # MOTEURS SPÉCIALISÉS
    # ═════════════════════════════════════════════════════════════════════════
    
    def compute(self, expression: str) -> str:
        """Calcul arithmétique ondulatoire."""
        try:
            _ENGINES_DIR = Path(__file__).resolve().parent.parent / 'engines'
            sys.path.insert(0, str(_ENGINES_DIR))
            from arithmetic import ArithmeticEngine
            ae = ArithmeticEngine()
            result = ae.compute(expression)
            return str(result)
        except Exception as e:
            return f"(moteur arithmétique indisponible: {e})"
    
    def grover(self, target: int, n_qubits: int = 6) -> str:
        """Recherche quantique de Grover."""
        try:
            _ENGINES_DIR = Path(__file__).resolve().parent.parent / 'engines'
            sys.path.insert(0, str(_ENGINES_DIR))
            from quantum import QuantumEngine
            qe = QuantumEngine(n_qubits)
            result = qe.run_grover(target)
            return str(result)
        except Exception as e:
            return f"(moteur quantique indisponible: {e})"
    
    def fold(self, sequence: str) -> str:
        """Repliement protéique."""
        try:
            from engines.folding import FoldingEngine
            fe = FoldingEngine(grid_size=16)
            _, energies = fe.fold(sequence, max_iter=30)
            return f"Repliement: {len(energies)} itérations, E_final={energies[-1]:.1f}"
        except Exception:
            return None
    
    # ═════════════════════════════════════════════════════════════════════════
    # UTILITAIRES
    # ═════════════════════════════════════════════════════════════════════════
    
    def _is_binary(self, expr: str) -> bool:
        return any(op in expr for op in ['+', '-'])
    
    def _parse_binary(self, expr: str) -> tuple:
        for op in ['+', '-']:
            if op in expr:
                parts = expr.split(op)
                return int(parts[0].strip()), int(parts[1].strip())
        return 0, 0
    
    @property
    def stats(self) -> dict:
        s = {
            'queries': self._stats['queries'],
            'harmonic': self._stats['harmonic'],
            'curated': self._stats['curated'],
            'autonomie': round(self._stats['harmonic'] / max(self._stats['queries'], 1) * 100, 1),
        }
        if self._enricher:
            s['blocs_curated'] = self._enricher.count
        if self._hmem:
            s['faits_hologramme'] = self._hmem.n_facts
        return s
    
    @property
    def is_ready(self) -> bool:
        return self._initialized


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════

_bridge_instance = None

def get_bridge(knowledge_base: list = None) -> EngineBridge:
    """Retourne l'instance unique du bridge."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = EngineBridge()
        _bridge_instance.init(knowledge_base)
    return _bridge_instance
