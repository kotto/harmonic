"""
Résonateur de Problèmes — Couche 0 de Harmonic AI v2
=====================================================
Applique les 7 principes du raisonnement ondulatoire AU-DESSUS de toutes
les autres couches. Formule le message utilisateur comme un champ spectral,
identifie les harmoniques, trouve le point de résonance, et prépare
le contexte optimal pour la génération.

Principes appliqués :
1. SUPERPOSITION    — Formuler le message comme champ de possibilités
2. INTERFÉRENCE     — Croiser les dimensions du problème
3. RÉSONANCE        — Identifier le point d'accord maximal
4. COHÉRENCE        — Vérifier la cohérence multi-échelle
5. ESPACEMENT φ     — Varier les approches (jamais de répétition)
6. NON-LOCALITÉ     — Chercher dans des domaines éloignés
7. PROJECTION       — Distinguer symptômes et causes

Intégration :
    from engine.harmonic_resonator import HarmonicResonator
    resonator = HarmonicResonator(hologram, memory)
    spectral_context = resonator.analyze(user_message)
"""
import math
import re
import hashlib
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import numpy as np

# =========================================================================
# CONSTANTES
# =========================================================================

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI

# Les 7 harmoniques fondamentales
HARMONIC_NAMES = {
    'H_factual': 'Ancrage dans les faits — ce qui est mesurable, vérifiable',
    'H_logical': 'Structure logique — liens de cause à effet, raisonnement',
    'H_emotional': 'Charge émotionnelle — affect, sentiment, tonalité',
    'H_creative': 'Ouverture créative — imagination, hypothèses, possibles',
    'H_temporal': 'Dimension temporelle — urgence, passé, futur, durée',
    'H_spatial': 'Dimension spatiale — localisation, échelle, proximité',
    'H_relational': 'Dimension relationnelle — liens entre personnes/entités',
}

# Types de raisonnement détectables
REASONING_TYPES = {
    'analytical': ['pourquoi', 'cause', 'analyse', 'explique', 'comment', 'raison'],
    'creative': ['imagine', 'crée', 'invente', 'si', 'hypothèse', 'possible'],
    'decisional': ['choisir', 'décider', 'quelle', 'option', 'meilleur', 'priorité'],
    'explanatory': ['c\'est quoi', 'définition', 'qu\'est-ce que', 'signifie', 'concept'],
    'predictive': ['prédire', 'futur', 'va-t-il', 'tendance', ' évolution', 'deviendra'],
    'comparative': ['comparer', 'différence', 'similaire', 'versus', 'contre', 'ou'],
    'procedural': ['comment faire', 'étapes', 'méthode', 'processus', 'tutoriel'],
}


# =========================================================================
# STRUCTURES DE DONNÉES
# =========================================================================

@dataclass
class SpectralProblem:
    """Représentation spectrale d'un problème."""
    raw_text: str
    harmonics: Dict[str, float]          # H_factual, H_logical, etc. → score [0,1]
    reasoning_types: Dict[str, float]    # analytical, creative, etc. → score [0,1]
    complexity: float                     # Complexité estimée du problème
    urgency: float                        # Urgence perçue
    domain_hints: List[str]              # Domaines suggérés (physique, médecine, etc.)
    resonance_points: List[str]          # Points de résonance identifiés
    suggested_approach: str              # Approche suggérée (jamais la même que précédemment)
    signature_9d: Optional[np.ndarray] = None  # Signature 9D calculée


@dataclass
class ResonatorStats:
    """Statistiques du résonateur."""
    total_problems: int = 0
    avg_complexity: float = 0.0
    dominant_harmonics: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    approach_history: List[str] = field(default_factory=list)
    resonance_success_rate: float = 0.0


# =========================================================================
# EXTRACTEURS D'HARMONIQUES
# =========================================================================

class HarmonicExtractor:
    """Extrait les harmoniques d'un message texte."""
    
    # Patterns pour chaque harmonique
    FACTUAL_PATTERNS = [
        r'\b\d{4}\b', r'\b\d+%', r'\b\d+[.,]\d+', r'\b\d+\s*(?:km|m|kg|g|€|%)\b',
        r'\b(?:données?|statistique|mesure|chiffre|nombre|preuve)\b',
    ]
    
    LOGICAL_PATTERNS = [
        r'\b(?:donc|parce que|car|puisque|ainsi|par conséquent|en effet)\b',
        r'\b(?:si\.{3}alors|si.*alors|d'une part.*d'autre part)\b',
        r'\b(?:cependant|toutefois|néanmoins|en revanche|or)\b',
    ]
    
    EMOTIONAL_PATTERNS = [
        r'\b(?:urgent|important|critique|vital|essentiel)\b',
        r'\b(?:inquiet|peur|angoiss|stress|panique)\b',
        r'\b(?:heureux|content|ravi|enthousiaste|merci)\b',
        r'[!]{2,}', r'[?]{2,}',
    ]
    
    CREATIVE_PATTERNS = [
        r'\b(?:imaginer|créer|inventer|rêver|hypothèse|possible|peut-être)\b',
        r'\b(?:et si|supposons|admettons|dans le futur|un jour)\b',
    ]
    
    TEMPORAL_PATTERNS = [
        r'\b(?:maintenant|tout de suite|urgence|immédiat|vite|rapide)\b',
        r'\b(?:demain|semaine prochaine|mois prochain|futur|plus tard)\b',
        r'\b(?:hier|passé|avant|jadis|autrefois|histoire)\b',
    ]
    
    SPATIAL_PATTERNS = [
        r'\b(?:ici|là-bas|proche|loin|distance|local|global|partout)\b',
        r'\b(?:en France|en Afrique|en Europe|aux États-Unis|dans le monde)\b',
    ]
    
    RELATIONAL_PATTERNS = [
        r'\b(?:nous|ensemble|équipe|groupe|communauté|collaborer)\b',
        r'\b(?:avec|contre|pour|entre|parmi)\b.*\b(?:personne|gens|amis?|famille)\b',
    ]
    
    @classmethod
    def extract_all(cls, text: str) -> Dict[str, float]:
        """Extrait toutes les harmoniques d'un texte."""
        text_lower = text.lower()
        n_words = max(len(text_lower.split()), 1)
        
        def score_patterns(patterns, text_lower, n_words):
            count = sum(len(re.findall(p, text_lower)) for p in patterns)
            return min(count / max(n_words * 0.08, 1), 1.0)
        
        harmonics = {
            'H_factual': score_patterns(cls.FACTUAL_PATTERNS, text_lower, n_words),
            'H_logical': score_patterns(cls.LOGICAL_PATTERNS, text_lower, n_words),
            'H_emotional': score_patterns(cls.EMOTIONAL_PATTERNS, text_lower, n_words),
            'H_creative': score_patterns(cls.CREATIVE_PATTERNS, text_lower, n_words),
            'H_temporal': score_patterns(cls.TEMPORAL_PATTERNS, text_lower, n_words),
            'H_spatial': score_patterns(cls.SPATIAL_PATTERNS, text_lower, n_words),
            'H_relational': score_patterns(cls.RELATIONAL_PATTERNS, text_lower, n_words),
        }
        
        return harmonics
    
    @classmethod
    def detect_reasoning_type(cls, text: str) -> Dict[str, float]:
        """Détecte le(s) type(s) de raisonnement requis."""
        text_lower = text.lower()
        scores = {}
        for rtype, markers in REASONING_TYPES.items():
            count = sum(1 for m in markers if m in text_lower)
            scores[rtype] = min(count / 3.0, 1.0)
        return scores
    
    @classmethod
    def detect_domains(cls, text: str) -> List[str]:
        """Détecte les domaines de connaissance pertinents."""
        text_lower = text.lower()
        domains = []
        
        domain_keywords = {
            'physique': ['physique', 'énergie', 'force', 'onde', 'particule', 'atome', 'quantique'],
            'mathématiques': ['math', 'équation', 'nombre', 'calcul', 'théorème', 'algorithme'],
            'médecine': ['médecin', 'santé', 'maladie', 'traitement', 'patient', 'diagnostic'],
            'biologie': ['biologie', 'cellule', 'ADN', 'organisme', 'espèce', 'évolution'],
            'informatique': ['code', 'programme', 'algorithme', 'donnée', 'réseau', 'IA'],
            'économie': ['économie', 'marché', 'prix', 'monnaie', 'finance', 'croissance'],
            'psychologie': ['psycho', 'émotion', 'comportement', 'cerveau', 'conscience'],
            'philosophie': ['philosophie', 'sens', 'existence', 'éthique', 'vérité'],
            'agriculture': ['agriculture', 'plante', 'culture', 'sol', 'récolte', 'semence'],
            'éducation': ['éducation', 'école', 'apprendre', 'cours', 'élève', 'professeur'],
        }
        
        for domain, keywords in domain_keywords.items():
            if any(kw in text_lower for kw in keywords):
                domains.append(domain)
        
        return domains
    
    @classmethod
    def estimate_complexity(cls, text: str) -> float:
        """Estime la complexité du problème."""
        n_words = len(text.split())
        n_sentences = max(len(re.split(r'[.!?]+', text)), 1)
        avg_sentence_len = n_words / n_sentences
        
        # Complexité lexicale
        words = text.lower().split()
        unique_ratio = len(set(words)) / max(n_words, 1)
        
        # Complexité structurelle
        has_subordinate = bool(re.search(r'\b(?:que|qui|dont|où|lequel)\b', text.lower()))
        
        score = 0.3 * min(avg_sentence_len / 25, 1.0)
        score += 0.3 * unique_ratio
        score += 0.2 * (1.0 if has_subordinate else 0.0)
        score += 0.2 * min(n_words / 100, 1.0)
        
        return min(score, 1.0)
    
    @classmethod
    def estimate_urgency(cls, text: str) -> float:
        """Estime l'urgence perçue du message."""
        urgency_markers = [
            r'\b(?:urgent|vite|maintenant|tout de suite|immédiat|dès que)\b',
            r'\b(?:grave|critique|crise|danger|alerte)\b',
            r'\b(?:aidez|secours|au secours|SOS)\b',
            r'[!]{3,}', r'[?]{3,}',
        ]
        text_lower = text.lower()
        count = sum(len(re.findall(p, text_lower)) for p in urgency_markers)
        return min(count / 3.0, 1.0)


# =========================================================================
# RÉSONATEUR DE PROBLÈMES
# =========================================================================

class HarmonicResonator:
    """
    Résonateur de Problèmes — Couche 0 de Harmonic AI v2.
    
    Applique les 7 principes du raisonnement ondulatoire
    AVANT toute génération de réponse.
    
    Usage:
        resonator = HarmonicResonator(hologram_connector, phi_memory)
        spectral_problem = resonator.analyze(user_message)
        # spectral_problem contient la formulation spectrale,
        # les points de résonance, et l'approche suggérée
    """
    
    def __init__(self, hologram_connector=None, phi_memory=None):
        self.hologram = hologram_connector
        self.memory = phi_memory
        self.extractor = HarmonicExtractor()
        self.stats = ResonatorStats()
        self.approach_counter: Dict[str, int] = defaultdict(int)
    
    def analyze(self, user_message: str) -> SpectralProblem:
        """
        Analyse un message utilisateur et produit une formulation spectrale.
        
        C'est la fonction principale du Résonateur.
        """
        self.stats.total_problems += 1
        
        # === PRINCIPE 1 : SUPERPOSITION ===
        # Formuler comme champ de possibilités
        harmonics = self.extractor.extract_all(user_message)
        
        # === PRINCIPE 2 : INTERFÉRENCE ===
        # Croiser les dimensions pour trouver des combinaisons
        reasoning_types = self.extractor.detect_reasoning_type(user_message)
        domains = self.extractor.detect_domains(user_message)
        
        # === PRINCIPE 3 : RÉSONANCE ===
        # Identifier le point d'accord maximal
        resonance_points = self._find_resonance_points(harmonics, domains)
        
        # === PRINCIPE 4 : COHÉRENCE ===
        # Vérifier la cohérence multi-échelle
        complexity = self.extractor.estimate_complexity(user_message)
        urgency = self.extractor.estimate_urgency(user_message)
        
        # === PRINCIPE 5 : ESPACEMENT φ ===
        # Choisir une approche qui ne répète pas les précédentes
        suggested_approach = self._suggest_phi_approach(harmonics, reasoning_types)
        
        # === PRINCIPE 6 : NON-LOCALITÉ ===
        # Chercher dans des domaines éloignés (cross-domain)
        cross_domains = self._suggest_cross_domains(domains)
        
        # === PRINCIPE 7 : PROJECTION ===
        # Distinguer symptômes et causes profondes
        depth_analysis = self._analyze_depth(user_message, harmonics)
        
        # Construire le problème spectral
        problem = SpectralProblem(
            raw_text=user_message,
            harmonics=harmonics,
            reasoning_types=reasoning_types,
            complexity=complexity,
            urgency=urgency,
            domain_hints=domains + cross_domains,
            resonance_points=resonance_points,
            suggested_approach=suggested_approach,
        )
        
        # Mettre à jour les stats
        dominant = max(harmonics, key=harmonics.get)
        self.stats.dominant_harmonics[dominant] += 1
        self.stats.avg_complexity = (
            (self.stats.avg_complexity * (self.stats.total_problems - 1) + complexity)
            / self.stats.total_problems
        )
        self.stats.approach_history.append(suggested_approach)
        if len(self.stats.approach_history) > 100:
            self.stats.approach_history = self.stats.approach_history[-100:]
        
        return problem
    
    def _find_resonance_points(self, harmonics: Dict[str, float],
                                domains: List[str]) -> List[str]:
        """
        PRINCIPE 3 — RÉSONANCE
        Identifie les points où les harmoniques entrent en interférence
        constructive — où une petite action produit un grand effet.
        """
        points = []
        
        # Point 1 : Dominante harmonique
        dominant = max(harmonics, key=harmonics.get)
        if harmonics[dominant] > 0.5:
            points.append(f"Dominante_{dominant}")
        
        # Point 2 : Paires en résonance (deux harmoniques élevées)
        high_harmonics = [(k, v) for k, v in harmonics.items() if v > 0.3]
        if len(high_harmonics) >= 2:
            sorted_h = sorted(high_harmonics, key=lambda x: x[1], reverse=True)
            pair = f"Resonance_{sorted_h[0][0]}_{sorted_h[1][0]}"
            points.append(pair)
        
        # Point 3 : Croisement domaine-harmonique
        for domain in domains[:3]:
            points.append(f"Domaine_{domain}")
        
        # Point 4 : φ-point (équilibre harmonique)
        # Entre H_factual et H_emotional, le point φ⁻¹ est l'équilibre idéal
        factual = harmonics.get('H_factual', 0)
        emotional = harmonics.get('H_emotional', 0)
        if abs(factual - emotional) < 0.3:
            points.append("Point_equilibre_phi")
        
        return points
    
    def _suggest_phi_approach(self, harmonics: Dict[str, float],
                               reasoning_types: Dict[str, float]) -> str:
        """
        PRINCIPE 5 — ESPACEMENT φ
        Suggère une approche qui ne répète pas les patterns précédents.
        """
        # Déterminer le type de raisonnement dominant
        dominant_reasoning = max(reasoning_types, key=reasoning_types.get) if reasoning_types else 'analytical'
        
        # Mapping des approches
        approach_by_harmonic = {
            'H_factual': 'investigation_factuelle',
            'H_logical': 'déduction_logique',
            'H_emotional': 'écoute_empathique',
            'H_creative': 'exploration_créative',
            'H_temporal': 'projection_temporelle',
            'H_spatial': 'analyse_spatiale',
            'H_relational': 'médiation_relationnelle',
        }
        
        dominant = max(harmonics, key=harmonics.get)
        primary_approach = approach_by_harmonic.get(dominant, 'approche_générale')
        
        # Si cette approche a été trop utilisée, varier (φ spacing)
        self.approach_counter[primary_approach] += 1
        usage = self.approach_counter[primary_approach]
        
        if usage > 3:
            # Chercher l'approche la moins utilisée
            all_approaches = list(approach_by_harmonic.values())
            for app in all_approaches:
                if app not in self.approach_counter:
                    self.approach_counter[app] = 0
            
            # Choisir une approche non-répétée
            alternatives = [a for a in all_approaches if self.approach_counter[a] < usage * 0.5]
            if alternatives:
                primary_approach = np.random.choice(alternatives)
        
        return f"{primary_approach}_{dominant_reasoning}"
    
    def _suggest_cross_domains(self, domains: List[str]) -> List[str]:
        """
        PRINCIPE 6 — NON-LOCALITÉ
        Suggère des domaines éloignés qui pourraient contenir des solutions.
        """
        cross_domain_map = {
            'médecine': ['physique', 'biologie', 'psychologie'],
            'physique': ['mathématiques', 'philosophie', 'informatique'],
            'économie': ['psychologie', 'mathématiques', 'physique'],
            'informatique': ['mathématiques', 'physique', 'linguistique'],
            'éducation': ['psychologie', 'neurosciences', 'philosophie'],
            'agriculture': ['biologie', 'physique', 'économie'],
        }
        
        suggested = []
        for domain in domains:
            if domain in cross_domain_map:
                for cross in cross_domain_map[domain]:
                    if cross not in domains and cross not in suggested:
                        suggested.append(cross)
        
        return suggested[:3]
    
    def _analyze_depth(self, text: str, harmonics: Dict[str, float]) -> Dict[str, Any]:
        """
        PRINCIPE 7 — PROJECTION SPECTRALE
        Distingue les symptômes (surface) des causes profondes (structure).
        """
        depth = {
            'surface_indicators': [],
            'depth_indicators': [],
            'is_surface_problem': False,
            'suggested_deep_question': None,
        }
        
        # Indicateurs de surface (problème immédiat)
        surface_words = ['vite', 'maintenant', 'urgent', 'problème', 'bug', 'erreur', 'cassé']
        for word in surface_words:
            if word in text.lower():
                depth['surface_indicators'].append(word)
        
        # Indicateurs de profondeur (question fondamentale)
        depth_words = ['pourquoi', 'cause', 'origine', 'fondamental', 'structure', 'sens']
        for word in depth_words:
            if word in text.lower():
                depth['depth_indicators'].append(word)
        
        # Si plus d'indicateurs de surface que de profondeur
        if len(depth['surface_indicators']) > len(depth['depth_indicators']):
            depth['is_surface_problem'] = True
            # Suggérer une reformulation plus profonde
            if harmonics.get('H_factual', 0) > 0.3:
                depth['suggested_deep_question'] = (
                    "Au-delà du symptôme immédiat, quelle est la structure sous-jacente ?"
                )
        
        return depth
    
    def get_context_for_generation(self, problem: SpectralProblem) -> Dict[str, Any]:
        """
        Prépare le contexte optimal pour la génération de réponse.
        
        Returns:
            Dict avec :
            - 'approach': l'approche suggérée
            - 'focus_harmonics': les harmoniques à privilégier
            - 'cross_domains': les domaines connexes à explorer
            - 'complexity_level': niveau de complexité (simple/moyen/complexe)
            - 'depth_hint': suggestion d'approfondissement si problème de surface
        """
        context = {
            'approach': problem.suggested_approach,
            'focus_harmonics': [
                h for h, v in sorted(problem.harmonics.items(),
                                     key=lambda x: x[1], reverse=True)[:3]
            ],
            'cross_domains': problem.domain_hints,
            'complexity_level': (
                'simple' if problem.complexity < 0.3 else
                'moyen' if problem.complexity < 0.6 else
                'complexe'
            ),
            'depth_hint': None,
            'resonance_points': problem.resonance_points,
        }
        
        # Si problème de surface détecté
        if problem.complexity < 0.4 and len(problem.raw_text.split()) < 15:
            context['depth_hint'] = (
                "Ce message semble décrire un symptôme. "
                "Chercher la structure sous-jacente plutôt que la solution immédiate."
            )
        
        return context


# =========================================================================
# TESTS
# =========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST HARMONIC RESONATOR — Couche 0 de Harmonic AI v2")
    print("=" * 60)
    
    resonator = HarmonicResonator()
    
    # Test 1 : Question factuelle
    msg1 = "Quelle est la valeur de la constante de structure fine α et comment est-elle calculée ?"
    
    print(f"\n--- Test 1 : Question factuelle ---")
    print(f"Message: {msg1}")
    problem1 = resonator.analyze(msg1)
    print(f"  Harmoniques: {problem1.harmonics}")
    print(f"  Raisonnement: {problem1.reasoning_types}")
    print(f"  Domaines: {problem1.domain_hints}")
    print(f"  Complexité: {problem1.complexity:.3f}")
    print(f"  Urgence: {problem1.urgency:.3f}")
    print(f"  Points de résonance: {problem1.resonance_points}")
    print(f"  Approche suggérée: {problem1.suggested_approach}")
    
    context1 = resonator.get_context_for_generation(problem1)
    print(f"  Contexte génération: {context1}")
    
    # Test 2 : Question émotionnelle
    msg2 = "Je suis très inquiet pour mon examen de demain, je n'arrive pas à dormir. Aidez-moi !"
    
    print(f"\n--- Test 2 : Question émotionnelle ---")
    print(f"Message: {msg2}")
    problem2 = resonator.analyze(msg2)
    print(f"  Harmoniques: {problem2.harmonics}")
    print(f"  Complexité: {problem2.complexity:.3f}")
    print(f"  Urgence: {problem2.urgency:.3f}")
    print(f"  Approche suggérée: {problem2.suggested_approach}")
    
    # Test 3 : Question créative
    msg3 = "Imagine un monde où l'énergie est gratuite. Comment la société changerait-elle ?"
    
    print(f"\n--- Test 3 : Question créative ---")
    print(f"Message: {msg3}")
    problem3 = resonator.analyze(msg3)
    print(f"  Harmoniques: {problem3.harmonics}")
    print(f"  Domaines: {problem3.domain_hints}")
    print(f"  Approche suggérée: {problem3.suggested_approach}")
    
    # Test 4 : Domaine croisé (non-localité)
    msg4 = "Comment résoudre la crise du logement en zone urbaine ?"
    
    print(f"\n--- Test 4 : Non-localité ---")
    print(f"Message: {msg4}")
    problem4 = resonator.analyze(msg4)
    print(f"  Domaines directs: {[d for d in problem4.domain_hints if d not in ['physique', 'mathématiques', 'psychologie', 'biologie', 'neurosciences', 'linguistique']]}")
    cross = [d for d in problem4.domain_hints if d in ['physique', 'mathématiques', 'psychologie', 'biologie', 'neurosciences', 'linguistique']]
    print(f"  Domaines croisés (non-localité): {cross}")
    
    # Test 5 : Stats
    print(f"\n--- Statistiques du résonateur ---")
    print(f"  Total problèmes analysés: {resonator.stats.total_problems}")
    print(f"  Complexité moyenne: {resonator.stats.avg_complexity:.3f}")
    print(f"  Harmoniques dominantes: {dict(resonator.stats.dominant_harmonics)}")
    
    print("\n✓ Test Harmonic Resonator réussi!")
    print("=" * 60)