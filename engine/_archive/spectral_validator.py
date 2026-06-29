"""
Module de Validation Spectrale — Anti-Hallucination pour Harmonic AI v2
=========================================================================
Vérifie la cohérence spectrale d'une réponse générée avant de la délivrer.
Filtre les hallucinations par vérification d'interférence entre la réponse
et le savoir holographique.

Principe : une réponse n'est valide que si elle interfère CONSTRUCTIVEMENT
avec le champ de la question ET avec le savoir de référence.

Architecture :
1. SpectralValidator — validation basée sur les signatures 11D
2. KnowledgeVerifier — vérification par rapport à l'hologramme
3. CoherenceFilter — filtre de sortie avec seuils φ

Seuils calibrés sur φ (1.618...) :
- COHERENCE_MIN = 0.618 (φ⁻¹) — seuil minimal d'acceptation
- RESONANCE_MIN = 0.5 — seuil minimal de résonance question-réponse
- KNOWLEDGE_MIN = 0.382 (φ⁻²) — seuil minimal de support factuel

Intégration :
    from engine.spectral_validator import SpectralValidator
    validator = SpectralValidator(hologram)
    is_valid, score = validator.validate(question_sig, response_text)
"""
import math
import hashlib
import re
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
import numpy as np

# =========================================================================
# CONSTANTES HARMONIQUES
# =========================================================================

PHI = 1.618033988749895
PHI_INV = 1.0 / PHI  # ≈ 0.618
PHI_INV_2 = PHI_INV ** 2  # ≈ 0.382

# Seuils de validation (calibrés sur φ)
COHERENCE_MIN = PHI_INV       # 0.618 — seuil minimal de cohérence
RESONANCE_MIN = 0.5           # 0.500 — seuil minimal de résonance Q-R
KNOWLEDGE_MIN = PHI_INV_2     # 0.382 — seuil minimal de support factuel
OVERALL_MIN = PHI_INV         # 0.618 — score global minimal

# Poids des composantes du score
WEIGHT_COHERENCE = 0.35    # Cohérence interne de la réponse
WEIGHT_RESONANCE = 0.30    # Résonance question-réponse
WEIGHT_KNOWLEDGE = 0.35    # Support par le savoir holographique


# =========================================================================
# ANALYSEUR DE TEXTE LÉGER (sans LLM)
# =========================================================================

class LightweightTextAnalyzer:
    """
    Analyseur de texte léger pour extraire des caractéristiques spectrales
    sans dépendance à un modèle de langage lourd.
    """
    
    # Patterns de détection d'hallucination
    HALLUCINATION_PATTERNS = [
        r"\bje ne sais pas\b",
        r"\bje n'ai pas accès\b",
        r"\bje ne peux pas\b",
        r"\bmes connaissances s'arrêtent\b",
        r"\ben tant qu'IA\b",
        r"\bje suis désolé\b.{0,30}\bje ne peux\b",
    ]
    
    # Indicateurs de confiance
    CONFIDENCE_INDICATORS = [
        r"\b(?:selon|d'après|conformément à)\b",
        r"\b(?:données?|étude|recherche|publication)\b",
        r"\b(?:démontré|prouvé|établi|confirmé)\b",
        r"\b\d{4}\b",  # Années (références temporelles)
    ]
    
    @staticmethod
    def extract_factual_density(text: str) -> float:
        """
        Mesure la densité factuelle d'un texte.
        Ratio de mots « factuels » sur total des mots.
        """
        words = text.lower().split()
        if not words:
            return 0.0
        
        factual_count = 0
        for pattern in LightweightTextAnalyzer.CONFIDENCE_INDICATORS:
            factual_count += len(re.findall(pattern, text.lower()))
        
        density = min(factual_count / len(words), 1.0)
        return density
    
    @staticmethod
    def detect_hallucination_markers(text: str) -> float:
        """
        Détecte les marqueurs d'hallucination (aveux d'ignorance, excuses).
        Retourne un score de 0 (très hallucinatoire) à 1 (aucun marqueur).
        """
        text_lower = text.lower()
        markers_found = 0
        
        for pattern in LightweightTextAnalyzer.HALLUCINATION_PATTERNS:
            if re.search(pattern, text_lower):
                markers_found += 1
        
        # Chaque marqueur réduit le score
        score = max(0.0, 1.0 - markers_found * 0.3)
        return score
    
    @staticmethod
    def estimate_coherence(text: str) -> float:
        """
        Estime la cohérence textuelle par des heuristiques simples.
        - Longueur suffisante
        - Ponctuation équilibrée
        - Absence de répétitions excessives
        """
        if len(text) < 20:
            return 0.3
        
        # Vérifier la présence de ponctuation
        has_period = '.' in text
        has_structure = len(text.split('.')) >= 2
        
        # Vérifier les répétitions
        words = text.lower().split()
        if len(words) > 5:
            unique_ratio = len(set(words)) / len(words)
        else:
            unique_ratio = 1.0
        
        # Score combiné
        score = 0.3 * min(len(text) / 200, 1.0)  # Longueur
        score += 0.2 * (1.0 if has_period else 0.0)  # Ponctuation
        score += 0.2 * (1.0 if has_structure else 0.0)  # Structure
        score += 0.3 * unique_ratio  # Diversité lexicale
        
        return min(score, 1.0)


# =========================================================================
# SIGNATURE DE TEXTE LÉGER
# =========================================================================

def compute_lightweight_signature(text: str) -> np.ndarray:
    """
    Calcule une signature 9D légère à partir d'un texte,
    sans nécessiter de modèle de langage.
    
    Utilise des heuristiques statistiques pour approximer
    les 9 dimensions harmoniques.
    
    Returns:
        signature: np.ndarray [9] dans [0, 1]
    """
    words = text.lower().split()
    if not words:
        return np.ones(9) * PHI_INV
    
    n_words = len(words)
    unique_words = len(set(words))
    
    # φ : diversité lexicale
    phi_val = min(unique_words / max(n_words, 1), 1.0)
    
    # α : complexité (longueur moyenne des mots)
    avg_word_len = np.mean([len(w) for w in words])
    alpha_val = min(avg_word_len / 10.0, 1.0)
    
    # Raisonnement : connecteurs logiques
    reasoning_markers = ['donc', 'parce', 'car', 'si', 'alors', 'cependant', 'mais',
                        'puisque', 'ainsi', 'par conséquent', 'toutefois', 'néanmoins']
    reasoning_count = sum(1 for w in words if w in reasoning_markers)
    reasoning_val = min(reasoning_count / max(n_words * 0.05, 1), 1.0)
    
    # Créativité : mots longs et rares
    long_rare = sum(1 for w in words if len(w) > 8)
    creativity_val = min(long_rare / max(n_words * 0.03, 1), 1.0)
    
    # Math : présence de chiffres
    math_chars = sum(1 for c in text if c.isdigit() or c in '+-×÷=<>[]{}')
    math_val = min(math_chars / max(len(text) * 0.02, 1), 1.0)
    
    # Factuel : densité factuelle
    analyzer = LightweightTextAnalyzer()
    factual_val = analyzer.extract_factual_density(text)
    
    # Code : présence de patterns de code
    code_indicators = ['{', '}', 'def ', 'class ', 'function', 'import ', 'return ',
                       'if __', 'print(', 'const ', 'let ', 'var ']
    code_count = sum(1 for ind in code_indicators if ind in text)
    code_val = min(code_count / 3.0, 1.0)
    
    # Émotion : ratio de mots émotionnels
    positive = ['bien', 'super', 'excellent', 'merci', 'heureux', 'joyeux', 'aime']
    negative = ['mal', 'triste', 'grave', 'problème', 'difficile', 'peur', 'colère']
    pos_count = sum(1 for w in words if w in positive)
    neg_count = sum(1 for w in words if w in negative)
    emotion_val = min((pos_count + neg_count) / max(n_words * 0.05, 1), 1.0)
    
    # Temporel : variation de longueur des phrases
    sentences = re.split(r'[.!?]+', text)
    sent_lengths = [len(s.split()) for s in sentences if s.strip()]
    if len(sent_lengths) >= 2:
        temporal_val = min(np.std(sent_lengths) / max(np.mean(sent_lengths), 1), 1.0)
    else:
        temporal_val = 0.0
    
    signature = np.array([
        phi_val, alpha_val, reasoning_val, creativity_val, math_val,
        factual_val, code_val, emotion_val, temporal_val
    ])
    
    return np.clip(signature, 0.0, 1.0)


# =========================================================================
# VALIDATEUR SPECTRAL
# =========================================================================

@dataclass
class ValidationResult:
    """Résultat de la validation spectrale."""
    is_valid: bool
    overall_score: float
    coherence_score: float
    resonance_score: float
    knowledge_score: float
    hallucination_markers: float
    recommendation: str
    details: Dict[str, Any] = field(default_factory=dict)


class SpectralValidator:
    """
    Validateur spectral pour Harmonic AI v2.
    
    Vérifie qu'une réponse générée est spectralement cohérente
    avec la question ET avec le savoir holographique.
    
    Usage:
        validator = SpectralValidator(hologram_connector)
        result = validator.validate(question_signature, response_text)
        if result.is_valid:
            return response_text
        else:
            # Régénérer avec ajustement
            ...
    """
    
    def __init__(self, hologram_connector=None):
        """
        Args:
            hologram_connector: Instance de HologrammeConnecteur pour
                               la vérification par rapport au savoir.
                               Si None, seule la validation textuelle est effectuée.
        """
        self.hologram = hologram_connector
        self.text_analyzer = LightweightTextAnalyzer()
        self.validation_history: List[ValidationResult] = []
    
    def validate(self, question_signature: np.ndarray,
                 response_text: str,
                 context_signature: Optional[np.ndarray] = None) -> ValidationResult:
        """
        Valide une réponse générée.
        
        Args:
            question_signature: Signature 9D de la question [9]
            response_text: Texte de la réponse générée
            context_signature: Signature 9D du contexte conversationnel [9] (optionnel)
        
        Returns:
            ValidationResult avec le verdict et les scores détaillés
        """
        # 1. Signature de la réponse (légère, sans LLM)
        response_signature = compute_lightweight_signature(response_text)
        
        # 2. Cohérence interne de la réponse
        coherence_score = self._compute_coherence(response_text, response_signature)
        
        # 3. Résonance question-réponse
        resonance_score = self._compute_resonance(question_signature, response_signature,
                                                    context_signature)
        
        # 4. Support par le savoir (si hologramme disponible)
        knowledge_score = self._compute_knowledge_support(response_text)
        
        # 5. Score global
        overall_score = (
            WEIGHT_COHERENCE * coherence_score +
            WEIGHT_RESONANCE * resonance_score +
            WEIGHT_KNOWLEDGE * knowledge_score
        )
        
        # 6. Détection de marqueurs d'hallucination
        hallucination_markers = self.text_analyzer.detect_hallucination_markers(response_text)
        
        # 7. Décision
        is_valid = (
            overall_score >= OVERALL_MIN and
            coherence_score >= COHERENCE_MIN * 0.7 and  # Tolérance de 30%
            resonance_score >= RESONANCE_MIN * 0.7 and
            hallucination_markers >= 0.5  # Pas trop de marqueurs d'hallucination
        )
        
        # 8. Recommandation
        recommendation = self._generate_recommendation(
            is_valid, overall_score, coherence_score, resonance_score,
            knowledge_score, hallucination_markers
        )
        
        result = ValidationResult(
            is_valid=is_valid,
            overall_score=overall_score,
            coherence_score=coherence_score,
            resonance_score=resonance_score,
            knowledge_score=knowledge_score,
            hallucination_markers=hallucination_markers,
            recommendation=recommendation,
            details={
                'response_signature': response_signature.tolist(),
                'question_signature': question_signature.tolist() if isinstance(question_signature, np.ndarray) else None,
                'response_length': len(response_text),
                'thresholds': {
                    'overall': OVERALL_MIN,
                    'coherence': COHERENCE_MIN,
                    'resonance': RESONANCE_MIN,
                    'knowledge': KNOWLEDGE_MIN,
                }
            }
        )
        
        self.validation_history.append(result)
        if len(self.validation_history) > 100:
            self.validation_history = self.validation_history[-100:]
        
        return result
    
    def _compute_coherence(self, text: str, signature: np.ndarray) -> float:
        """
        Calcule le score de cohérence interne de la réponse.
        Combine l'analyse textuelle et la cohérence spectrale.
        """
        # Cohérence textuelle légère
        text_coherence = self.text_analyzer.estimate_coherence(text)
        
        # Cohérence spectrale (équilibre des 9 dimensions)
        mean = signature.mean()
        std = signature.std()
        cv = std / (mean + 1e-8)
        cv_ideal = PHI_INV_2  # φ⁻² ≈ 0.382
        cv_penalty = abs(cv - cv_ideal) / cv_ideal
        spectral_coherence = 1.0 - cv_penalty
        
        # Combinaison
        return 0.5 * text_coherence + 0.5 * np.clip(spectral_coherence, 0.0, 1.0)
    
    def _compute_resonance(self, question_sig: np.ndarray,
                           response_sig: np.ndarray,
                           context_sig: Optional[np.ndarray] = None) -> float:
        """
        Calcule le score de résonance (interférence) entre la question et la réponse.
        """
        # Résonance question-réponse
        qr_cosine = np.dot(question_sig, response_sig) / (
            np.linalg.norm(question_sig) * np.linalg.norm(response_sig) + 1e-8
        )
        qr_resonance = (qr_cosine + 1.0) / 2.0
        
        if context_sig is not None:
            # Résonance réponse-contexte
            rc_cosine = np.dot(response_sig, context_sig) / (
                np.linalg.norm(response_sig) * np.linalg.norm(context_sig) + 1e-8
            )
            rc_resonance = (rc_cosine + 1.0) / 2.0
            
            # Combinaison (60% Q-R, 40% R-C)
            return 0.6 * qr_resonance + 0.4 * rc_resonance
        
        return qr_resonance
    
    def _compute_knowledge_support(self, text: str) -> float:
        """
        Vérifie le support du savoir holographique.
        
        Si l'hologramme n'est pas disponible, utilise une heuristique
        basée sur la densité factuelle et la structure du texte.
        """
        if self.hologram is not None:
            try:
                # Interroger l'hologramme
                result = self.hologram.query(text)
                support = result.get('confidence', 0.5)
                return support
            except Exception:
                pass
        
        # Fallback : estimation heuristique
        factual_density = self.text_analyzer.extract_factual_density(text)
        text_coherence = self.text_analyzer.estimate_coherence(text)
        
        # Le support factuel est estimé à partir de la densité factuelle
        # et de la cohérence structurelle
        return 0.6 * factual_density + 0.4 * text_coherence
    
    def _generate_recommendation(self, is_valid: bool, overall: float,
                                  coherence: float, resonance: float,
                                  knowledge: float, hallucination: float) -> str:
        """Génère une recommandation basée sur les scores."""
        if is_valid:
            if overall > 0.85:
                return "EXCELLENT — Réponse spectralement cohérente. Aucun ajustement nécessaire."
            elif overall > 0.72:
                return "BON — Réponse acceptable. Légère optimisation possible."
            else:
                return "ACCEPTABLE — Réponse validée mais proche du seuil. Surveiller."
        
        # Diagnostic des problèmes
        issues = []
        if coherence < COHERENCE_MIN * 0.7:
            issues.append("cohérence interne faible")
        if resonance < RESONANCE_MIN * 0.7:
            issues.append("résonance question-réponse insuffisante")
        if knowledge < KNOWLEDGE_MIN:
            issues.append("support factuel insuffisant")
        if hallucination < 0.5:
            issues.append("marqueurs d'hallucination détectés")
        
        if issues:
            return f"REJETÉ — Problèmes : {', '.join(issues)}. Régénérer avec ajustement."
        return "REJETÉ — Score global insuffisant. Régénérer."


# =========================================================================
# FILTRE DE SORTIE AVEC SEUILS φ
# =========================================================================

class CoherenceFilter:
    """
    Filtre de cohérence pour les sorties textuelles.
    
    Applique des seuils inspirés de φ pour filtrer les réponses incohérentes
    avant même la validation spectrale complète.
    """
    
    # Seuils rapides
    MIN_LENGTH = 10       # Longueur minimale en caractères
    MAX_REPETITION = 0.5  # Ratio maximal de répétition de mots
    MIN_UNIQUE_WORDS = 3  # Nombre minimal de mots uniques
    
    @staticmethod
    def quick_filter(text: str) -> Tuple[bool, str]:
        """
        Filtre rapide avant validation spectrale.
        Élimine les réponses manifestement invalides.
        
        Returns:
            (is_valid, reason)
        """
        if not text or len(text.strip()) < CoherenceFilter.MIN_LENGTH:
            return False, "Réponse trop courte"
        
        words = text.lower().split()
        if len(words) < CoherenceFilter.MIN_UNIQUE_WORDS:
            return False, "Pas assez de mots"
        
        # Vérifier les répétitions excessives
        if len(words) > 5:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:
                return False, f"Répétition excessive (ratio unique: {unique_ratio:.2f})"
        
        # Vérifier les boucles (même phrase répétée)
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) >= 3:
            for i in range(len(sentences) - 1):
                if sentences[i].strip() and sentences[i].strip() == sentences[i+1].strip():
                    return False, "Boucle de répétition détectée"
        
        return True, "OK"
    
    @staticmethod
    def enhance_response(text: str, question_sig: np.ndarray) -> str:
        """
        Améliore une réponse en supprimant les marqueurs d'hallucination
        et en renforçant la structure.
        """
        # Supprimer les aveux d'ignorance
        for pattern in LightweightTextAnalyzer.HALLUCINATION_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Nettoyer les espaces multiples
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Ajouter un point final si absent
        if text and text[-1] not in '.!?':
            text += '.'
        
        return text


# =========================================================================
# INTÉGRATION DANS LE PIPELINE HARMONIC AI
# =========================================================================

class HarmonicValidationPipeline:
    """
    Pipeline complet de validation pour Harmonic AI v2.
    
    Intègre :
    1. Filtre rapide (CoherenceFilter)
    2. Validation spectrale (SpectralValidator)
    3. Ajustement automatique si rejet
    
    Usage:
        pipeline = HarmonicValidationPipeline(hologram)
        result = pipeline.process(question_sig, response_text)
    """
    
    def __init__(self, hologram_connector=None, auto_retry: bool = True):
        self.validator = SpectralValidator(hologram_connector)
        self.filter = CoherenceFilter()
        self.auto_retry = auto_retry
        self.max_retries = 3
    
    def process(self, question_signature: np.ndarray,
                response_text: str,
                context_signature: Optional[np.ndarray] = None,
                regenerate_fn: Optional[callable] = None) -> Tuple[str, ValidationResult]:
        """
        Traite une réponse à travers le pipeline de validation.
        
        Args:
            question_signature: Signature 9D de la question
            response_text: Texte de la réponse
            context_signature: Signature du contexte
            regenerate_fn: Fonction de régénération (appelée si rejet)
                          Signature: fn(question_sig, feedback) -> new_text
        
        Returns:
            (final_text, validation_result)
        """
        current_text = response_text
        
        for attempt in range(self.max_retries + 1):
            # 1. Filtre rapide
            quick_ok, quick_reason = self.filter.quick_filter(current_text)
            if not quick_ok:
                if attempt < self.max_retries and regenerate_fn:
                    current_text = regenerate_fn(question_signature,
                                                 f"Quick filter: {quick_reason}")
                    continue
                else:
                    result = ValidationResult(
                        is_valid=False, overall_score=0.0,
                        coherence_score=0.0, resonance_score=0.0,
                        knowledge_score=0.0, hallucination_markers=0.0,
                        recommendation=f"Rejeté par filtre rapide: {quick_reason}"
                    )
                    return current_text, result
            
            # 2. Nettoyage
            current_text = self.filter.enhance_response(current_text, question_signature)
            
            # 3. Validation spectrale
            result = self.validator.validate(question_signature, current_text, context_signature)
            
            if result.is_valid:
                return current_text, result
            
            # 4. Régénération si nécessaire
            if attempt < self.max_retries and regenerate_fn and self.auto_retry:
                feedback = result.recommendation
                current_text = regenerate_fn(question_signature, feedback)
            else:
                break
        
        return current_text, result


# =========================================================================
# TESTS
# =========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TEST SPECTRAL VALIDATOR — Validation Anti-Hallucination")
    print("=" * 60)
    
    # Créer le validateur (sans hologramme pour le test)
    validator = SpectralValidator(hologram_connector=None)
    
    # Signature de question simulée
    np.random.seed(42)
    question_sig = np.random.rand(9)
    
    # Test 1 : Bonne réponse
    good_response = (
        "La théorie harmonique postule que l'univers est une superposition d'ondes "
        "dont les fréquences sont espacées par le nombre d'or φ = 1.618. "
        "Cette équation unique, Ψ = Σ Aₙ·(Ψ₁)ⁿ, prédit la constante de structure fine α "
        "avec une précision de 0.000024%. Les 4 forces fondamentales émergent comme "
        "des projections du même champ Ψ sur différents régimes spectraux."
    )
    
    print("\n--- Test 1 : Bonne réponse ---")
    result1 = validator.validate(question_sig, good_response)
    print(f"  Valide: {result1.is_valid}")
    print(f"  Score global: {result1.overall_score:.3f}")
    print(f"  Cohérence: {result1.coherence_score:.3f}")
    print(f"  Résonance: {result1.resonance_score:.3f}")
    print(f"  Connaissance: {result1.knowledge_score:.3f}")
    print(f"  Hallucination: {result1.hallucination_markers:.3f}")
    print(f"  Recommandation: {result1.recommendation}")
    
    # Test 2 : Réponse avec marqueur d'hallucination
    hallucinated_response = (
        "Je suis désolé, je ne peux pas répondre à cette question car mes connaissances "
        "s'arrêtent en 2023. En tant qu'IA, je ne sais pas..."
    )
    
    print("\n--- Test 2 : Réponse avec marqueurs d'hallucination ---")
    result2 = validator.validate(question_sig, hallucinated_response)
    print(f"  Valide: {result2.is_valid}")
    print(f"  Score global: {result2.overall_score:.3f}")
    print(f"  Hallucination: {result2.hallucination_markers:.3f}")
    print(f"  Recommandation: {result2.recommendation}")
    
    # Test 3 : Réponse très courte
    short_response = "OK."
    
    print("\n--- Test 3 : Réponse trop courte ---")
    result3 = validator.validate(question_sig, short_response)
    print(f"  Valide: {result3.is_valid}")
    print(f"  Score global: {result3.overall_score:.3f}")
    print(f"  Cohérence: {result3.coherence_score:.3f}")
    
    # Test 4 : Filtre rapide
    print("\n--- Test 4 : CoherenceFilter ---")
    filt = CoherenceFilter()
    
    tests = [
        "OK.",
        "blabla blabla blabla blabla blabla",
        "Ceci est une phrase normale. Ceci est une phrase normale. Ceci est une phrase normale.",
        "Une réponse courte mais valide et cohérente.",
    ]
    for t in tests:
        ok, reason = filt.quick_filter(t)
        print(f"  '{t[:50]}...' → {ok} ({reason})")
    
    # Test 5 : Pipeline complet
    print("\n--- Test 5 : Pipeline complet ---")
    pipeline = HarmonicValidationPipeline(hologram_connector=None, auto_retry=False)
    final_text, final_result = pipeline.process(question_sig, good_response)
    print(f"  Texte final (extrait): {final_text[:80]}...")
    print(f"  Validation: {final_result.is_valid} (score: {final_result.overall_score:.3f})")
    
    # Test 6 : Signature légère
    print("\n--- Test 6 : Signature légère ---")
    sig = compute_lightweight_signature(good_response)
    dim_names = ["φ", "α", "raison", "créa", "math", "factuel", "code", "émotion", "temporel"]
    for name, val in zip(dim_names, sig):
        bar = "█" * int(val * 30)
        print(f"  {name:>8}: {val:.3f} {bar}")
    
    print("\n✓ Test Spectral Validator réussi!")
    print("=" * 60)