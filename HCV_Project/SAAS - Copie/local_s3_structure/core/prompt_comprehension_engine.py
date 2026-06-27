#!/usr/bin/env python3
"""
🧠 PROMPT COMPREHENSION ENGINE - SYSTÈME INTELLIGENT AVANCÉ
Compréhension profonde et contextuelle des prompts avec principes harmoniques
Version: 1.0.0 - INTELLIGENCE CONTEXTUELLE
"""

import numpy as np
import math
import re
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Imports harmoniques
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from foundation.harmonic_foundation import FOUNDATION
from core.harmonic_resonance_engine_fixed import ENGINE

# Constantes harmoniques
PHI = (1 + math.sqrt(5)) / 2
PI = math.pi
EULER = math.e

@dataclass
class PromptAnalysis:
    """Analyse complète d'un prompt"""
    original_prompt: str
    normalized_prompt: str
    intent: str
    entities: List[str]
    concepts: List[str]
    context: Dict[str, Any]
    semantic_vector: np.ndarray
    harmonic_score: float
    confidence: float
    complexity_level: str
    domain: str
    language: str
    timestamp: float

@dataclass
class ComprehensionResult:
    """Résultat de compréhension du prompt"""
    analysis: PromptAnalysis
    interpretation: str
    suggested_actions: List[str]
    clarifications_needed: List[str]
    confidence_score: float
    processing_time: float
    harmonic_validation: bool

class PromptComprehensionEngine:
    """Moteur intelligent de compréhension de prompts"""
    
    def __init__(self):
        """Initialisation du moteur de compréhension"""
        
        print("🧠 INITIALISATION PROMPT COMPREHENSION ENGINE")
        print("=" * 60)
        
        # Composants harmoniques
        self.foundation = FOUNDATION
        self.engine = ENGINE
        
        # Configuration du système
        self.config = {
            "max_prompt_length": 10000,
            "semantic_threshold": 0.7,
            "harmonic_threshold": 0.6,
            "context_window": 5,  # prompts précédents
            "language_detection": True,
            "entity_extraction": True,
            "intent_classification": True
        }
        
        # Dictionnaires sémantiques
        self.intent_patterns = self._initialize_intent_patterns()
        self.entity_patterns = self._initialize_entity_patterns()
        self.concept_vectors = self._initialize_concept_vectors()
        
        # Contexte historique
        self.context_history = []
        self.user_profiles = {}
        
        # Analyseurs spécialisés
        self.semantic_analyzer = SemanticAnalyzer(self)
        self.context_manager = ContextManager(self)
        self.intent_detector = IntentDetector(self)
        self.prompt_validator = PromptValidator(self)
        
        print("✅ Moteur de compréhension initialisé")
        print("✅ Analyseurs spécialisés chargés")
        print("✅ Contexte historique prêt")
        print("=" * 60)
    
    def _initialize_intent_patterns(self) -> Dict[str, List[str]]:
        """Initialise les patterns d'intention"""
        
        return {
            "question": [
                "comment", "pourquoi", "comment", "où", "quand", "quel", "quelle",
                "what", "how", "why", "where", "when", "which", "?"
            ],
            "request": [
                "peux-tu", "pourrais-tu", "s'il te plaît", "aide-moi",
                "can you", "could you", "please", "help me", "je veux", "je souhaite"
            ],
            "creation": [
                "crée", "génère", "développe", "construis", "fabrique",
                "create", "generate", "develop", "build", "make"
            ],
            "analysis": [
                "analyse", "étudie", "examine", "évalue", "compare",
                "analyze", "study", "examine", "evaluate", "compare"
            ],
            "explanation": [
                "explique", "décrit", "détaille", "montre", "démontre",
                "explain", "describe", "detail", "show", "demonstrate"
            ],
            "optimization": [
                "optimise", "améliore", "améliore", "fais mieux",
                "optimize", "improve", "enhance", "make better"
            ],
            "transformation": [
                "transforme", "convertis", "change", "modifie", "adapte",
                "transform", "convert", "change", "modify", "adapt"
            ]
        }
    
    def _initialize_entity_patterns(self) -> Dict[str, List[str]]:
        """Initialise les patterns d'entités"""
        
        return {
            "person": [
                "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
                "i", "you", "he", "she", "we", "they", "user", "person"
            ],
            "time": [
                "aujourd'hui", "demain", "hier", "maintenant", "bientôt",
                "today", "tomorrow", "yesterday", "now", "soon", "heure", "minute"
            ],
            "location": [
                "ici", "là", "où", "ici", "là-bas", "ici", "là",
                "here", "there", "where", "location", "place", "address"
            ],
            "quantity": [
                "beaucoup", "peu", "plus", "moins", "tous", "aucun",
                "many", "few", "more", "less", "all", "none", "number", "count"
            ],
            "technology": [
                "ordinateur", "programme", "algorithme", "code", "données",
                "computer", "program", "algorithm", "code", "data", "software", "hardware"
            ],
            "mathematics": [
                "mathématique", "calcul", "équation", "nombre", "formule",
                "mathematics", "calculation", "equation", "number", "formula"
            ],
            "science": [
                "science", "recherche", "expérience", "théorie", "hypothèse",
                "science", "research", "experiment", "theory", "hypothesis"
            ]
        }
    
    def _initialize_concept_vectors(self) -> Dict[str, np.ndarray]:
        """Initialise les vecteurs conceptuels harmoniques"""
        
        vectors = {}
        
        # Concepts fondamentaux basés sur les constantes harmoniques
        fundamental_concepts = [
            "harmony", "balance", "proportion", "golden_ratio",
            "mathematics", "logic", "reasoning", "analysis",
            "creation", "transformation", "optimization", "efficiency"
        ]
        
        for concept in fundamental_concepts:
            # Génération de vecteur harmonique basé sur le concept
            vector = self._generate_harmonic_vector(concept)
            vectors[concept] = vector
        
        return vectors
    
    def _generate_harmonic_vector(self, concept: str) -> np.ndarray:
        """Génère un vecteur harmonique pour un concept"""
        
        # Hash du concept pour déterminisme
        concept_hash = hash(concept) % 1000
        
        # Génération de vecteur 64D basé sur les constantes harmoniques
        vector = np.zeros(64)
        
        for i in range(64):
            # Application des constantes harmoniques
            if i % 4 == 0:
                vector[i] = PHI * math.sin(concept_hash * (i + 1))
            elif i % 4 == 1:
                vector[i] = PI * math.cos(concept_hash * (i + 1))
            elif i % 4 == 2:
                vector[i] = EULER * math.sin(concept_hash * (i + 1) + PI/4)
            else:
                vector[i] = math.sqrt(2) * math.cos(concept_hash * (i + 1) + PI/3)
        
        # Normalisation
        vector = vector / np.linalg.norm(vector)
        
        return vector
    
    def comprehend_prompt(self, prompt: str, user_id: str = None) -> ComprehensionResult:
        """
        Compréhension complète d'un prompt
        
        Args:
            prompt: Le prompt à analyser
            user_id: Identifiant utilisateur (optionnel)
            
        Returns:
            Résultat de compréhension complet
        """
        
        start_time = time.time()
        
        print(f"🧠 Compréhension du prompt: {prompt[:50]}...")
        
        # Étape 1: Normalisation du prompt
        normalized_prompt = self._normalize_prompt(prompt)
        
        # Étape 2: Analyse sémantique
        semantic_analysis = self.semantic_analyzer.analyze(normalized_prompt)
        
        # Étape 3: Détection d'intention
        intent = self.intent_detector.detect_intent(normalized_prompt)
        
        # Étape 4: Extraction d'entités
        entities = self._extract_entities(normalized_prompt)
        
        # Étape 5: Extraction de concepts
        concepts = self._extract_concepts(normalized_prompt)
        
        # Étape 6: Gestion contextuelle
        context = self.context_manager.get_context(prompt, user_id)
        
        # Étape 7: Vectorisation sémantique
        semantic_vector = self._vectorize_semantically(normalized_prompt, concepts)
        
        # Étape 8: Calcul du score harmonique
        harmonic_score = self._calculate_harmonic_score(normalized_prompt, intent, concepts)
        
        # Étape 9: Classification de complexité
        complexity_level = self._classify_complexity(normalized_prompt, concepts)
        
        # Étape 10: Détection de domaine
        domain = self._detect_domain(normalized_prompt, concepts)
        
        # Étape 11: Détection de langue
        language = self._detect_language(normalized_prompt)
        
        # Création de l'analyse
        analysis = PromptAnalysis(
            original_prompt=prompt,
            normalized_prompt=normalized_prompt,
            intent=intent,
            entities=entities,
            concepts=concepts,
            context=context,
            semantic_vector=semantic_vector,
            harmonic_score=harmonic_score,
            confidence=semantic_analysis['confidence'],
            complexity_level=complexity_level,
            domain=domain,
            language=language,
            timestamp=time.time()
        )
        
        # Étape 12: Interprétation du prompt
        interpretation = self._interpret_prompt(analysis)
        
        # Étape 13: Suggestion d'actions
        suggested_actions = self._suggest_actions(analysis)
        
        # Étape 14: Détection de clarifications
        clarifications_needed = self._detect_clarifications(analysis)
        
        # Étape 15: Validation harmonique
        harmonic_validation = self.prompt_validator.validate_harmonic(analysis)
        
        # Étape 16: Mise à jour du contexte
        self.context_manager.update_context(analysis, user_id)
        
        processing_time = time.time() - start_time
        
        # Calcul du score de confiance global
        confidence_score = self._calculate_global_confidence(analysis, harmonic_validation)
        
        result = ComprehensionResult(
            analysis=analysis,
            interpretation=interpretation,
            suggested_actions=suggested_actions,
            clarifications_needed=clarifications_needed,
            confidence_score=confidence_score,
            processing_time=processing_time,
            harmonic_validation=harmonic_validation
        )
        
        print(f"✅ Compréhension terminée en {processing_time:.3f}s")
        print(f"🎯 Intention: {intent}")
        print(f"🌊 Score harmonique: {harmonic_score:.3f}")
        print(f"💪 Confiance: {confidence_score:.3f}")
        
        return result
    
    def _normalize_prompt(self, prompt: str) -> str:
        """Normalise le prompt pour analyse"""
        
        # Nettoyage de base
        normalized = prompt.strip().lower()
        
        # Suppression des caractères spéciaux excessifs
        normalized = re.sub(r'[^\w\s\?\!\.\,\;\:]', ' ', normalized)
        
        # Normalisation des espaces
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Conservation de la ponctuation importante
        normalized = re.sub(r'\s*([?.!])', r'\1', normalized)
        
        return normalized
    
    def _extract_entities(self, prompt: str) -> List[str]:
        """Extrait les entités du prompt"""
        
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                if pattern in prompt:
                    entities.append(f"{entity_type}:{pattern}")
        
        return list(set(entities))
    
    def _extract_concepts(self, prompt: str) -> List[str]:
        """Extrait les concepts du prompt"""
        
        concepts = []
        
        # Recherche dans les vecteurs conceptuels
        for concept, vector in self.concept_vectors.items():
            if concept in prompt or concept.replace('_', ' ') in prompt:
                concepts.append(concept)
        
        # Concepts basés sur les mots-clés
        concept_keywords = {
            "logic": ["logique", "raisonnement", "déduction", "logic", "reasoning"],
            "mathematics": ["math", "calcul", "nombre", "équation", "math", "calculation"],
            "creativity": ["créatif", "innovation", "idée", "creative", "innovation"],
            "analysis": ["analyse", "étude", "examen", "analyze", "study"],
            "optimization": ["optimisation", "amélioration", "efficacité", "optimize", "improve"]
        }
        
        for concept, keywords in concept_keywords.items():
            for keyword in keywords:
                if keyword in prompt:
                    concepts.append(concept)
                    break
        
        return list(set(concepts))
    
    def _vectorize_semantically(self, prompt: str, concepts: List[str]) -> np.ndarray:
        """Vectorise sémantiquement le prompt"""
        
        # Vectorisation de base basée sur les concepts
        vector = np.zeros(64)
        
        for concept in concepts:
            if concept in self.concept_vectors:
                vector += self.concept_vectors[concept]
        
        # Ajout de composante harmonique du prompt
        prompt_vector = self._generate_harmonic_vector(prompt)
        vector = 0.7 * vector + 0.3 * prompt_vector
        
        # Normalisation
        if np.linalg.norm(vector) > 0:
            vector = vector / np.linalg.norm(vector)
        
        return vector
    
    def _calculate_harmonic_score(self, prompt: str, intent: str, concepts: List[str]) -> float:
        """Calcule le score harmonique du prompt"""
        
        score = 0.0
        
        # Score basé sur les concepts harmoniques
        harmonic_concepts = ["harmony", "balance", "proportion", "golden_ratio"]
        for concept in harmonic_concepts:
            if concept in concepts:
                score += 0.2
        
        # Score basé sur l'intention
        harmonic_intents = ["analysis", "explanation", "creation"]
        if intent in harmonic_intents:
            score += 0.2
        
        # Score basé sur la structure du prompt
        if len(prompt.split()) > 5:  # Prompt suffisamment détaillé
            score += 0.2
        
        # Score basé sur la clarté
        if any(punct in prompt for punct in ['?', '.', '!']):
            score += 0.2
        
        # Score basé sur la cohérence
        coherence_score = self._calculate_coherence(prompt)
        score += coherence_score * 0.2
        
        return min(1.0, score)
    
    def _calculate_coherence(self, prompt: str) -> float:
        """Calcule la cohérence du prompt"""
        
        # Analyse simple de cohérence basée sur les mots
        words = prompt.split()
        
        if len(words) < 3:
            return 0.5
        
        # Cohérence basée sur la répétition et la structure
        unique_words = set(words)
        repetition_ratio = len(unique_words) / len(words)
        
        # Cohérence basée sur la structure grammaticale simple
        has_question = '?' in prompt
        has_statement = '.' in prompt
        has_exclamation = '!' in prompt
        
        structure_score = 0.0
        if has_question or has_statement:
            structure_score += 0.5
        if has_exclamation:
            structure_score += 0.3
        
        return (repetition_ratio + structure_score) / 2
    
    def _classify_complexity(self, prompt: str, concepts: List[str]) -> str:
        """Classifie la complexité du prompt"""
        
        # Métriques de complexité
        word_count = len(prompt.split())
        concept_count = len(concepts)
        has_subquestions = prompt.count('?') > 1
        has_multiple_requests = len(re.findall(r'\b(peux|pourrais|s\'il|can|could|please)\b', prompt)) > 1
        
        # Classification
        if word_count <= 5 and concept_count <= 1:
            return "simple"
        elif word_count <= 15 and concept_count <= 3 and not has_subquestions:
            return "medium"
        elif word_count <= 30 and concept_count <= 5:
            return "complex"
        else:
            return "very_complex"
    
    def _detect_domain(self, prompt: str, concepts: List[str]) -> str:
        """Détecte le domaine principal du prompt"""
        
        domain_scores = {
            "mathematics": 0,
            "technology": 0,
            "science": 0,
            "general": 0
        }
        
        # Score basé sur les concepts
        math_concepts = ["mathematics", "logic", "calculation", "equation"]
        tech_concepts = ["technology", "computer", "program", "algorithm", "code"]
        science_concepts = ["science", "research", "experiment", "theory"]
        
        for concept in concepts:
            if concept in math_concepts:
                domain_scores["mathematics"] += 1
            elif concept in tech_concepts:
                domain_scores["technology"] += 1
            elif concept in science_concepts:
                domain_scores["science"] += 1
            else:
                domain_scores["general"] += 1
        
        # Score basé sur les mots-clés
        math_keywords = ["calcul", "équation", "nombre", "formule", "calculation", "equation"]
        tech_keywords = ["ordinateur", "programme", "code", "algorithme", "computer", "program"]
        science_keywords = ["science", "recherche", "expérience", "théorie", "research", "experiment"]
        
        for keyword in math_keywords:
            if keyword in prompt:
                domain_scores["mathematics"] += 0.5
        
        for keyword in tech_keywords:
            if keyword in prompt:
                domain_scores["technology"] += 0.5
        
        for keyword in science_keywords:
            if keyword in prompt:
                domain_scores["science"] += 0.5
        
        # Détermination du domaine principal
        max_domain = max(domain_scores, key=domain_scores.get)
        
        if domain_scores[max_domain] == 0:
            return "general"
        
        return max_domain
    
    def _detect_language(self, prompt: str) -> str:
        """Détecte la langue du prompt"""
        
        # Mots-clés par langue
        french_keywords = ["le", "la", "les", "de", "du", "des", "et", "est", "dans", "pour"]
        english_keywords = ["the", "and", "is", "in", "for", "of", "to", "with", "on", "at"]
        
        french_score = sum(1 for word in french_keywords if word in prompt.lower())
        english_score = sum(1 for word in english_keywords if word in prompt.lower())
        
        if french_score > english_score:
            return "french"
        elif english_score > french_score:
            return "english"
        else:
            return "unknown"
    
    def _interpret_prompt(self, analysis: PromptAnalysis) -> str:
        """Interprète le prompt de manière intelligible"""
        
        interpretation = f"Intent: {analysis.intent} dans le domaine {analysis.domain} "
        
        if analysis.concepts:
            interpretation += f"avec les concepts: {', '.join(analysis.concepts)}. "
        
        if analysis.entities:
            interpretation += f"Entités détectées: {', '.join(analysis.entities)}. "
        
        if analysis.complexity_level == "simple":
            interpretation += "Prompt simple et direct."
        elif analysis.complexity_level == "medium":
            interpretation += "Prompt de complexité moyenne."
        elif analysis.complexity_level == "complex":
            interpretation += "Prompt complexe nécessitant une analyse approfondie."
        else:
            interpretation += "Prompt très complexe avec plusieurs sous-requêtes."
        
        if analysis.harmonic_score > 0.7:
            interpretation += " Alignement harmonique élevé."
        
        return interpretation.strip()
    
    def _suggest_actions(self, analysis: PromptAnalysis) -> List[str]:
        """Suggère des actions basées sur l'analyse"""
        
        actions = []
        
        # Actions basées sur l'intention
        if analysis.intent == "question":
            actions.append("Fournir une réponse directe et précise")
        elif analysis.intent == "request":
            actions.append("Exécuter la demande spécifique")
        elif analysis.intent == "creation":
            actions.append("Générer ou créer le contenu demandé")
        elif analysis.intent == "analysis":
            actions.append("Analyser en détail le sujet")
        elif analysis.intent == "explanation":
            actions.append("Expliquer clairement les concepts")
        elif analysis.intent == "optimization":
            actions.append("Optimiser ou améliorer l'élément mentionné")
        elif analysis.intent == "transformation":
            actions.append("Transformer ou convertir selon les spécifications")
        
        # Actions basées sur la complexité
        if analysis.complexity_level in ["complex", "very_complex"]:
            actions.append("Décomposer en sous-tâches plus simples")
            actions.append("Demander des clarifications si nécessaire")
        
        # Actions basées sur le domaine
        if analysis.domain == "mathematics":
            actions.append("Utiliser des exemples concrets et des formules")
        elif analysis.domain == "technology":
            actions.append("Fournir des exemples de code ou des instructions techniques")
        elif analysis.domain == "science":
            actions.append("Inclure des références scientifiques et des preuves")
        
        return actions
    
    def _detect_clarifications(self, analysis: PromptAnalysis) -> List[str]:
        """Détecte les clarifications nécessaires"""
        
        clarifications = []
        
        # Clarifications basées sur l'ambiguïté
        if analysis.confidence < 0.7:
            clarifications.append("Le prompt semble ambigu, pourriez-vous préciser?")
        
        # Clarifications basées sur la complexité
        if analysis.complexity_level == "very_complex":
            clarifications.append("Le prompt contient plusieurs requêtes, laquelle prioriser?")
        
        # Clarifications basées sur les entités manquantes
        if analysis.intent == "request" and not analysis.entities:
            clarifications.append("Quelle est l'entité spécifique concernée?")
        
        # Clarifications basées sur le contexte
        if not analysis.context and analysis.complexity_level != "simple":
            clarifications.append("Pouvez-vous fournir plus de contexte?")
        
        return clarifications
    
    def _calculate_global_confidence(self, analysis: PromptAnalysis, harmonic_validation: bool) -> float:
        """Calcule le score de confiance global"""
        
        confidence = analysis.confidence
        
        # Ajustement basé sur le score harmonique
        confidence = 0.7 * confidence + 0.3 * analysis.harmonic_score
        
        # Ajustement basé sur la validation harmonique
        if harmonic_validation:
            confidence *= 1.1
        else:
            confidence *= 0.9
        
        # Ajustement basé sur la complexité
        if analysis.complexity_level == "simple":
            confidence *= 1.05
        elif analysis.complexity_level == "very_complex":
            confidence *= 0.95
        
        return min(1.0, confidence)

# Classes spécialisées
class SemanticAnalyzer:
    """Analyseur sémantique spécialisé"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def analyze(self, prompt: str) -> Dict[str, Any]:
        """Analyse sémantique du prompt"""
        
        # Analyse de structure
        structure = self._analyze_structure(prompt)
        
        # Analyse de sentiment (basique)
        sentiment = self._analyze_sentiment(prompt)
        
        # Analyse de clarté
        clarity = self._analyze_clarity(prompt)
        
        # Calcul de confiance
        confidence = (structure['score'] + sentiment['score'] + clarity['score']) / 3
        
        return {
            'structure': structure,
            'sentiment': sentiment,
            'clarity': clarity,
            'confidence': confidence
        }
    
    def _analyze_structure(self, prompt: str) -> Dict[str, Any]:
        """Analyse la structure du prompt"""
        
        sentences = re.split(r'[.!?]+', prompt)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return {
            'sentence_count': len(sentences),
            'avg_sentence_length': sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0,
            'has_question': '?' in prompt,
            'has_exclamation': '!' in prompt,
            'score': min(1.0, len(sentences) / 5)  # Score basé sur le nombre de phrases
        }
    
    def _analyze_sentiment(self, prompt: str) -> Dict[str, Any]:
        """Analyse le sentiment du prompt"""
        
        positive_words = ["bon", "bien", "excellent", "super", "génial", "good", "great", "excellent"]
        negative_words = ["mauvais", "mal", "terrible", "horrible", "bad", "terrible", "horrible"]
        
        positive_count = sum(1 for word in positive_words if word in prompt.lower())
        negative_count = sum(1 for word in negative_words if word in prompt.lower())
        
        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        score = 0.5  # Neutre par défaut
        if positive_count > 0 or negative_count > 0:
            score = (positive_count - negative_count) / (positive_count + negative_count)
            score = (score + 1) / 2  # Normalisation entre 0 et 1
        
        return {
            'sentiment': sentiment,
            'positive_words': positive_count,
            'negative_words': negative_count,
            'score': score
        }
    
    def _analyze_clarity(self, prompt: str) -> Dict[str, Any]:
        """Analyse la clarté du prompt"""
        
        # Métriques de clarté
        words = prompt.split()
        unique_words = set(words)
        
        # Ratio de mots uniques
        uniqueness_ratio = len(unique_words) / len(words) if words else 0
        
        # Présence de ponctuation
        has_punctuation = any(punct in prompt for punct in ['?', '.', '!'])
        
        # Longueur appropriée
        appropriate_length = 10 <= len(words) <= 50
        
        # Score de clarté
        score = 0.0
        if uniqueness_ratio > 0.5:
            score += 0.3
        if has_punctuation:
            score += 0.3
        if appropriate_length:
            score += 0.4
        
        return {
            'uniqueness_ratio': uniqueness_ratio,
            'has_punctuation': has_punctuation,
            'appropriate_length': appropriate_length,
            'score': score
        }

class ContextManager:
    """Gestionnaire de contexte spécialisé"""
    
    def __init__(self, engine):
        self.engine = engine
        self.context_history = []
        self.max_history = 10
    
    def get_context(self, prompt: str, user_id: str = None) -> Dict[str, Any]:
        """Obtient le contexte pour le prompt"""
        
        context = {
            'previous_prompts': self.context_history[-5:],
            'user_profile': self._get_user_profile(user_id),
            'session_info': self._get_session_info(),
            'relevant_history': self._get_relevant_history(prompt)
        }
        
        return context
    
    def update_context(self, analysis: PromptAnalysis, user_id: str = None):
        """Met à jour le contexte"""
        
        # Ajout à l'historique
        self.context_history.append({
            'prompt': analysis.original_prompt,
            'intent': analysis.intent,
            'domain': analysis.domain,
            'timestamp': analysis.timestamp
        })
        
        # Limitation de l'historique
        if len(self.context_history) > self.max_history:
            self.context_history = self.context_history[-self.max_history:]
        
        # Mise à jour du profil utilisateur
        self._update_user_profile(user_id, analysis)
    
    def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Obtient le profil utilisateur"""
        
        if not user_id:
            return {}
        
        return self.engine.user_profiles.get(user_id, {
            'preferred_domains': [],
            'interaction_count': 0,
            'last_interaction': None
        })
    
    def _update_user_profile(self, user_id: str, analysis: PromptAnalysis):
        """Met à jour le profil utilisateur"""
        
        if not user_id:
            return
        
        if user_id not in self.engine.user_profiles:
            self.engine.user_profiles[user_id] = {
                'preferred_domains': [],
                'interaction_count': 0,
                'last_interaction': None
            }
        
        profile = self.engine.user_profiles[user_id]
        
        # Mise à jour des domaines préférés
        if analysis.domain not in profile['preferred_domains']:
            profile['preferred_domains'].append(analysis.domain)
        
        # Mise à jour du compteur d'interactions
        profile['interaction_count'] += 1
        profile['last_interaction'] = analysis.timestamp
    
    def _get_session_info(self) -> Dict[str, Any]:
        """Obtient les informations de session"""
        
        return {
            'session_start': time.time() - len(self.context_history) * 60,  # Estimation
            'prompt_count': len(self.context_history),
            'average_complexity': self._calculate_average_complexity()
        }
    
    def _get_relevant_history(self, prompt: str) -> List[Dict[str, Any]]:
        """Obtient l'historique pertinent pour le prompt"""
        
        # Simple implémentation: retourne les 3 prompts les plus récents
        return self.context_history[-3:] if self.context_history else []
    
    def _calculate_average_complexity(self) -> str:
        """Calcule la complexité moyenne"""
        
        if not self.context_history:
            return "unknown"
        
        complexities = []
        for entry in self.context_history:
            # Simplification: basé sur la longueur du prompt
            if len(entry['prompt'].split()) < 10:
                complexities.append("simple")
            elif len(entry['prompt'].split()) < 20:
                complexities.append("medium")
            else:
                complexities.append("complex")
        
        # Mode de la complexité
        from collections import Counter
        return Counter(complexities).most_common(1)[0][0]

class IntentDetector:
    """Détecteur d'intention spécialisé"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def detect_intent(self, prompt: str) -> str:
        """Détecte l'intention principale du prompt"""
        
        scores = {}
        
        # Calcul des scores pour chaque intention
        for intent, patterns in self.engine.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in prompt:
                    score += 1
            scores[intent] = score
        
        # Détermination de l'intention principale
        if not scores or max(scores.values()) == 0:
            return "unknown"
        
        return max(scores, key=scores.get)

class PromptValidator:
    """Validateur de prompts spécialisé"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def validate_harmonic(self, analysis: PromptAnalysis) -> bool:
        """Valide l'harmonie du prompt"""
        
        # Validation basée sur le score harmonique
        if analysis.harmonic_score < self.engine.config["harmonic_threshold"]:
            return False
        
        # Validation basée sur la cohérence
        if analysis.confidence < 0.5:
            return False
        
        # Validation basée sur la structure
        if len(analysis.normalized_prompt.split()) < 3:
            return False
        
        return True

# Fonction de démonstration
def demonstrate_prompt_comprehension():
    """Démonstration du système de compréhension de prompts"""
    
    print("🧠 DÉMONSTRATION PROMPT COMPREHENSION ENGINE")
    print("=" * 60)
    
    engine = PromptComprehensionEngine()
    
    # Prompts de test
    test_prompts = [
        "Comment puis-je optimiser un algorithme de tri?",
        "Peux-tu m'expliquer le concept du nombre d'or en mathématiques?",
        "Crée un programme Python qui calcule la suite de Fibonacci",
        "Analyse les performances de ce code et suggère des améliorations",
        "Quelle est la différence entre l'apprentissage supervisé et non supervisé?"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n📝 Test {i}: {prompt}")
        print("-" * 50)
        
        result = engine.comprehend_prompt(prompt, user_id="demo_user")
        
        print(f"🎯 Intention: {result.analysis.intent}")
        print(f"📊 Domaine: {result.analysis.domain}")
        print(f"🧠 Complexité: {result.analysis.complexity_level}")
        print(f"🌊 Score harmonique: {result.analysis.harmonic_score:.3f}")
        print(f"💪 Confiance: {result.confidence_score:.3f}")
        print(f"⏱️ Temps: {result.processing_time:.3f}s")
        print(f"✅ Validation: {result.harmonic_validation}")
        
        if result.suggested_actions:
            print(f"🚀 Actions suggérées: {', '.join(result.suggested_actions[:2])}")
        
        if result.clarifications_needed:
            print(f"❓ Clarifications: {', '.join(result.clarifications_needed)}")
    
    print(f"\n🏆 DÉMONSTRATION TERMINÉE")
    print(f"✅ Système de compréhension intelligent démontré")
    print(f"🌊 Approche harmonique unique")
    print(f"🧠 Analyse multi-niveaux complète")
    print(f"🎯 Précision contextuelle avancée")

if __name__ == "__main__":
    demonstrate_prompt_comprehension()
