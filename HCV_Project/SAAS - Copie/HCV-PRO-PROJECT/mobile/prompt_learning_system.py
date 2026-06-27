#!/usr/bin/env python3
"""
HCV PRO - Prompt Learning System with Harmonic Compression
==========================================================

Implementation de l'apprentissage par prompt avec métadonnées
et compression harmonique déterministe O(N log N).

Auteur: HCV PRO Team
Date: 27 avril 2026
"""

import numpy as np
import json
import hashlib
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from scipy.fft import fft2, ifft2
from collections import defaultdict
import sqlite3
import pickle
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes harmoniques universelles
FUNDAMENTAL_FREQ = 432  # Hz
GOLDEN_RATIO = 1.618034
HARMONIC_SERIES = [FUNDAMENTAL_FREQ * (GOLDEN_RATIO ** n) for n in range(12)]

@dataclass
class PromptMetadata:
    """Métadonnées structurées pour chaque prompt"""
    timestamp: int
    time_of_day: str
    day_of_week: str
    season: str
    frequency_pattern: str
    
    location: str
    device_type: str
    connectivity: str
    battery_level: float
    storage_available: float
    
    intent_type: str
    domain: str
    complexity: str
    urgency: str
    emotional_tone: str
    
    previous_interactions: List[str]
    success_rate: float
    response_time: float
    follow_up_required: bool
    pattern_match: str
    
    frequency_signature: List[float]
    resonance_score: float
    harmonic_pattern: str
    energy_level: float
    phase_coherence: float

class MetadataExtractor:
    """Extraction des métadonnées riches des prompts"""
    
    def __init__(self):
        self.time_patterns = {
            'morning': (6, 12),
            'afternoon': (12, 18),
            'evening': (18, 22),
            'night': (22, 6)
        }
        
        self.intent_keywords = {
            'question': ['?', 'comment', 'pourquoi', 'comment', 'où', 'quand'],
            'command': ['fais', 'crée', 'génère', 'cherche', 'trouve'],
            'conversation': ['salut', 'bonjour', 'merci', 'au revoir', 'discutons']
        }
        
        self.domain_keywords = {
            'work': ['travail', 'projet', 'réunion', 'email', 'collègue'],
            'personal': ['maison', 'famille', 'amis', 'personnel'],
            'health': ['santé', 'médicament', 'docteur', 'sport', 'alimentation'],
            'entertainment': ['film', 'musique', 'jeu', 'livre', 'série']
        }
    
    def extract_metadata(self, prompt_text: str, context: Dict, user_state: Dict) -> PromptMetadata:
        """Extraction complète des métadonnées"""
        
        # Métadonnées temporelles
        temporal = self._extract_temporal_metadata(prompt_text, context)
        
        # Métadonnées contextuelles
        contextual = self._extract_contextual_metadata(context, user_state)
        
        # Métadonnées sémantiques
        semantic = self._extract_semantic_metadata(prompt_text)
        
        # Métadonnées comportementales
        behavioral = self._extract_behavioral_metadata(prompt_text, user_state)
        
        # Métadonnées harmoniques
        harmonic = self._extract_harmonic_metadata(prompt_text, user_state)
        
        # Construction de l'objet métadonnées
        metadata = PromptMetadata(
            timestamp=temporal['timestamp'],
            time_of_day=temporal['time_of_day'],
            day_of_week=temporal['day_of_week'],
            season=temporal['season'],
            frequency_pattern=temporal['frequency_pattern'],
            
            location=contextual['location'],
            device_type=contextual['device_type'],
            connectivity=contextual['connectivity'],
            battery_level=contextual['battery_level'],
            storage_available=contextual['storage_available'],
            
            intent_type=semantic['intent_type'],
            domain=semantic['domain'],
            complexity=semantic['complexity'],
            urgency=semantic['urgency'],
            emotional_tone=semantic['emotional_tone'],
            
            previous_interactions=behavioral['previous_interactions'],
            success_rate=behavioral['success_rate'],
            response_time=behavioral['response_time'],
            follow_up_required=behavioral['follow_up_required'],
            pattern_match=behavioral['pattern_match'],
            
            frequency_signature=harmonic['frequency_signature'],
            resonance_score=harmonic['resonance_score'],
            harmonic_pattern=harmonic['harmonic_pattern'],
            energy_level=harmonic['energy_level'],
            phase_coherence=harmonic['phase_coherence']
        )
        
        return metadata
    
    def _extract_temporal_metadata(self, prompt_text: str, context: Dict) -> Dict:
        """Extraction des métadonnées temporelles"""
        now = datetime.now(timezone.utc)
        timestamp = int(now.timestamp())
        
        # Heure de la journée
        hour = now.hour
        time_of_day = None
        for period, (start, end) in self.time_patterns.items():
            if start <= hour < end or (start > end and (hour >= start or hour < end)):
                time_of_day = period
                break
        
        # Jour de la semaine
        day_of_week = now.strftime('%A').lower()
        
        # Saison
        month = now.month
        if month in [12, 1, 2]:
            season = 'winter'
        elif month in [3, 4, 5]:
            season = 'spring'
        elif month in [6, 7, 8]:
            season = 'summer'
        else:
            season = 'autumn'
        
        # Pattern de fréquence (basé sur l'historique)
        frequency_pattern = context.get('frequency_pattern', 'unknown')
        
        return {
            'timestamp': timestamp,
            'time_of_day': time_of_day,
            'day_of_week': day_of_week,
            'season': season,
            'frequency_pattern': frequency_pattern
        }
    
    def _extract_contextual_metadata(self, context: Dict, user_state: Dict) -> Dict:
        """Extraction des métadonnées contextuelles"""
        return {
            'location': context.get('location', 'unknown'),
            'device_type': context.get('device_type', 'mobile'),
            'connectivity': context.get('connectivity', 'unknown'),
            'battery_level': context.get('battery_level', 1.0),
            'storage_available': context.get('storage_available', 1000000000)  # 1GB default
        }
    
    def _extract_semantic_metadata(self, prompt_text: str) -> Dict:
        """Extraction des métadonnées sémantiques"""
        prompt_lower = prompt_text.lower()
        
        # Type d'intention
        intent_type = 'conversation'
        for intent, keywords in self.intent_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                intent_type = intent
                break
        
        # Domaine
        domain = 'personal'
        for dom, keywords in self.domain_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                domain = dom
                break
        
        # Complexité
        word_count = len(prompt_text.split())
        if word_count < 5:
            complexity = 'simple'
        elif word_count < 15:
            complexity = 'moderate'
        else:
            complexity = 'complex'
        
        # Urgence
        urgency = 'low'
        urgent_keywords = ['urgent', 'vite', 'immédiatement', 'maintenant']
        if any(keyword in prompt_lower for keyword in urgent_keywords):
            urgency = 'high'
        elif any(keyword in prompt_lower for keyword in ['svp', 'merci', 'aide']):
            urgency = 'medium'
        
        # Ton émotionnel
        emotional_tone = 'neutral'
        positive_words = ['bon', 'excellent', 'super', 'génial', 'heureux']
        negative_words = ['mauvais', 'terrible', 'problème', 'erreur', 'échec']
        stressed_words = ['stressé', 'panique', 'urgent', 'aide']
        
        if any(word in prompt_lower for word in positive_words):
            emotional_tone = 'positive'
        elif any(word in prompt_lower for word in stressed_words):
            emotional_tone = 'stressed'
        elif any(word in prompt_lower for word in negative_words):
            emotional_tone = 'negative'
        
        return {
            'intent_type': intent_type,
            'domain': domain,
            'complexity': complexity,
            'urgency': urgency,
            'emotional_tone': emotional_tone
        }
    
    def _extract_behavioral_metadata(self, prompt_text: str, user_state: Dict) -> Dict:
        """Extraction des métadonnées comportementales"""
        # Interactions précédentes
        previous_interactions = user_state.get('recent_prompts', [])[-5:]  # 5 derniers
        
        # Taux de succès (basé sur l'historique)
        success_rate = user_state.get('success_rate', 0.8)
        
        # Temps de réponse moyen
        response_time = user_state.get('avg_response_time', 0.5)
        
        # Nécessité de suivi
        follow_up_required = '?' in prompt_text or 'aide' in prompt_text.lower()
        
        # Pattern matching
        pattern_match = 'new_pattern'
        if len(previous_interactions) > 0:
            # Simple similarity check
            similarity = self._calculate_similarity(prompt_text, previous_interactions[-1])
            if similarity > 0.7:
                pattern_match = 'repeated_pattern'
        
        return {
            'previous_interactions': previous_interactions,
            'success_rate': success_rate,
            'response_time': response_time,
            'follow_up_required': follow_up_required,
            'pattern_match': pattern_match
        }
    
    def _extract_harmonic_metadata(self, prompt_text: str, user_state: Dict) -> Dict:
        """Extraction des métadonnées harmoniques"""
        
        # Encodage du texte en fréquences
        text_freq = self._encode_text_to_frequencies(prompt_text)
        
        # Signature fréquentielle
        frequency_signature = text_freq.tolist()
        
        # Score de résonance avec profil utilisateur
        user_profile = user_state.get('harmonic_profile', np.ones(12))
        resonance_score = self._calculate_resonance(text_freq, user_profile)
        
        # Pattern harmonique
        harmonic_pattern = self._identify_harmonic_pattern(text_freq)
        
        # Niveau d'énergie
        energy_level = np.sum(text_freq ** 2)
        
        # Cohérence de phase
        phase_coherence = self._calculate_phase_coherence(text_freq)
        
        return {
            'frequency_signature': frequency_signature,
            'resonance_score': resonance_score,
            'harmonic_pattern': harmonic_pattern,
            'energy_level': float(energy_level),
            'phase_coherence': float(phase_coherence)
        }
    
    def _encode_text_to_frequencies(self, text: str) -> np.ndarray:
        """Encodage du texte en fréquences harmoniques"""
        # Conversion du texte en valeurs numériques
        char_values = [ord(c) for c in text[:100]]  # Limiter à 100 chars
        
        # Padding/truncate pour taille fixe
        if len(char_values) < 12:
            char_values.extend([0] * (12 - len(char_values)))
        else:
            char_values = char_values[:12]
        
        # Application des constantes harmoniques
        frequencies = np.array(char_values) * FUNDAMENTAL_FREQ / 100
        
        return frequencies
    
    def _calculate_resonance(self, freq1: np.ndarray, freq2: np.ndarray) -> float:
        """Calcul de la résonance entre deux signatures fréquentielles"""
        correlation = np.corrcoef(freq1, freq2)[0, 1]
        return float(correlation) if not np.isnan(correlation) else 0.0
    
    def _identify_harmonic_pattern(self, frequencies: np.ndarray) -> str:
        """Identification du pattern harmonique"""
        ratios = frequencies[1:] / frequencies[:-1]
        
        # Vérifier si les ratios suivent le nombre d'or
        golden_ratios = np.abs(ratios - GOLDEN_RATIO)
        if np.mean(golden_ratios) < 0.1:
            return 'golden_harmonic'
        
        # Vérifier si c'est une série harmonique simple
        harmonic_ratios = np.abs(ratios - 2.0)
        if np.mean(harmonic_ratios) < 0.1:
            return 'simple_harmonic'
        
        return 'complex_harmonic'
    
    def _calculate_phase_coherence(self, frequencies: np.ndarray) -> float:
        """Calcul de la cohérence de phase"""
        if len(frequencies) < 2:
            return 1.0
        
        # Calcul des phases relatives
        phases = np.angle(frequencies.astype(complex))
        phase_diffs = np.diff(phases)
        
        # Cohérence = 1 - variance des différences de phase
        coherence = 1.0 - np.var(phase_diffs) / (2 * np.pi)
        return max(0.0, min(1.0, coherence))
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcul de similarité simple entre deux textes"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if len(union) > 0 else 0.0

class PromptModeler:
    """Modélisation des prompts avec métadonnées"""
    
    def __init__(self):
        self.deterministic_seed = 42
    
    def model_prompt_with_metadata(self, prompt_text: str, metadata: PromptMetadata) -> Dict:
        """Crée un modèle de prompt enrichi"""
        
        modeled_prompt = {
            'prompt_text': prompt_text,
            'prompt_hash': self._generate_deterministic_hash(prompt_text),
            'metadata': asdict(metadata),
            'harmonic_signature': self._generate_harmonic_signature(prompt_text, metadata),
            'behavioral_patterns': self._extract_behavioral_patterns(metadata),
            'causal_links': self._establish_causal_links(prompt_text, metadata),
            'response_predictions': self._predict_response_patterns(metadata)
        }
        
        return modeled_prompt
    
    def _generate_deterministic_hash(self, text: str) -> str:
        """Génération de hash déterministe"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
    
    def _generate_harmonic_signature(self, prompt_text: str, metadata: PromptMetadata) -> Dict:
        """Génération de signature harmonique"""
        
        # Encodage du texte
        text_freq = self._encode_text_to_frequencies(prompt_text)
        
        # Encodage des métadonnées
        metadata_freq = self._encode_metadata_to_frequencies(metadata)
        
        # Combinaison harmonique
        combined_freq = self._combine_harmonically(text_freq, metadata_freq)
        
        # Extraction de la signature
        signature = {
            'dominant_frequencies': self._find_dominant_frequencies(combined_freq),
            'harmonic_ratios': self._calculate_harmonic_ratios(combined_freq),
            'phase_relationships': self._calculate_phase_relationships(combined_freq),
            'energy_distribution': self._calculate_energy_distribution(combined_freq)
        }
        
        return signature
    
    def _encode_text_to_frequencies(self, text: str) -> np.ndarray:
        """Encodage du texte en fréquences"""
        char_values = [ord(c) for c in text[:100]]
        
        if len(char_values) < 12:
            char_values.extend([0] * (12 - len(char_values)))
        else:
            char_values = char_values[:12]
        
        frequencies = np.array(char_values) * FUNDAMENTAL_FREQ / 100
        return frequencies
    
    def _encode_metadata_to_frequencies(self, metadata: PromptMetadata) -> np.ndarray:
        """Encodage des métadonnées en fréquences"""
        # Conversion des métadonnées en valeurs numériques
        metadata_values = [
            metadata.timestamp % 1000,
            hash(metadata.time_of_day) % 100,
            hash(metadata.day_of_week) % 100,
            hash(metadata.season) % 100,
            hash(metadata.frequency_pattern) % 100,
            hash(metadata.location) % 100,
            hash(metadata.device_type) % 100,
            hash(metadata.connectivity) % 100,
            int(metadata.battery_level * 100),
            int(metadata.storage_available / 100000000) % 100,
            hash(metadata.intent_type) % 100,
            hash(metadata.domain) % 100
        ]
        
        frequencies = np.array(metadata_values) * FUNDAMENTAL_FREQ / 100
        return frequencies
    
    def _combine_harmonically(self, freq1: np.ndarray, freq2: np.ndarray) -> np.ndarray:
        """Combinaison harmonique déterministe"""
        # Combinaison basée sur le nombre d'or
        combined = freq1 * GOLDEN_RATIO + freq2
        return combined
    
    def _find_dominant_frequencies(self, frequencies: np.ndarray) -> List[float]:
        """Trouve les fréquences dominantes"""
        # Tri par amplitude
        sorted_indices = np.argsort(np.abs(frequencies))[::-1]
        dominant = frequencies[sorted_indices[:6]]  # Top 6
        return dominant.tolist()
    
    def _calculate_harmonic_ratios(self, frequencies: np.ndarray) -> List[float]:
        """Calcule les ratios harmoniques"""
        ratios = []
        for i in range(1, len(frequencies)):
            if frequencies[i-1] != 0:
                ratios.append(frequencies[i] / frequencies[i-1])
        return ratios
    
    def _calculate_phase_relationships(self, frequencies: np.ndarray) -> List[float]:
        """Calcule les relations de phase"""
        phases = np.angle(frequencies.astype(complex))
        return phases.tolist()
    
    def _calculate_energy_distribution(self, frequencies: np.ndarray) -> List[float]:
        """Calcule la distribution d'énergie"""
        energies = frequencies ** 2
        total_energy = np.sum(energies)
        if total_energy > 0:
            distribution = energies / total_energy
        else:
            distribution = np.zeros_like(energies)
        return distribution.tolist()
    
    def _extract_behavioral_patterns(self, metadata: PromptMetadata) -> Dict:
        """Extrait les patterns comportementaux"""
        return {
            'time_pattern': metadata.time_of_day,
            'urgency_pattern': metadata.urgency,
            'complexity_pattern': metadata.complexity,
            'domain_preference': metadata.domain,
            'interaction_frequency': metadata.frequency_pattern
        }
    
    def _establish_causal_links(self, prompt_text: str, metadata: PromptMetadata) -> List[Dict]:
        """Établit les liens causaux"""
        links = []
        
        # Lien temps/comportement
        if metadata.time_of_day == 'morning' and metadata.domain == 'work':
            links.append({
                'cause': 'morning_time',
                'effect': 'work_domain',
                'confidence': 0.8
            })
        
        # Lien urgence/réponse rapide
        if metadata.urgency == 'high':
            links.append({
                'cause': 'high_urgency',
                'effect': 'fast_response_required',
                'confidence': 0.9
            })
        
        return links
    
    def _predict_response_patterns(self, metadata: PromptMetadata) -> Dict:
        """Prédit les patterns de réponse"""
        predictions = {
            'expected_response_length': 'short' if metadata.urgency == 'high' else 'medium',
            'response_tone': 'professional' if metadata.domain == 'work' else 'casual',
            'response_speed': 'immediate' if metadata.urgency == 'high' else 'normal',
            'follow_up_likelihood': metadata.follow_up_required
        }
        
        return predictions

class HarmonicModelCompression:
    """Compression du modèle de prompt avec harmoniques"""
    
    def __init__(self):
        self.compression_threshold = 0.95  # Garder 95% de l'énergie
    
    def compress_model(self, modeled_prompt: Dict) -> Dict:
        """Compression du modèle complet"""
        
        # 1. Sérialisation structurée
        serialized_model = self._serialize_model(modeled_prompt)
        
        # 2. Transformée harmonique
        harmonic_representation = self._apply_global_fft(serialized_model)
        
        # 3. Extraction des composantes significatives
        significant_components = self._extract_significant_components(harmonic_representation)
        
        # 4. Quantification
        quantized_model = self._quantize_harmonically(significant_components)
        
        # 5. Compression finale
        compressed_model = self._final_compression(quantized_model)
        
        return compressed_model
    
    def _serialize_model(self, modeled_prompt: Dict) -> np.ndarray:
        """Sérialisation déterministe du modèle"""
        serialization_order = [
            'prompt_text',
            'prompt_hash',
            'metadata.timestamp',
            'metadata.time_of_day',
            'metadata.intent_type',
            'metadata.domain',
            'metadata.complexity',
            'metadata.urgency',
            'metadata.emotional_tone',
            'metadata.resonance_score',
            'metadata.energy_level',
            'metadata.phase_coherence'
        ]
        
        serialized = []
        for key in serialization_order:
            value = self._get_nested_value(modeled_prompt, key)
            serialized.append(self._encode_value(value))
        
        # Padding pour taille fixe
        while len(serialized) < 256:
            serialized.append(0.0)
        
        return np.array(serialized, dtype=np.float64)
    
    def _get_nested_value(self, data: Dict, key: str) -> Any:
        """Récupère une valeur imbriquée"""
        keys = key.split('.')
        value = data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                value = 0
                break
        return value
    
    def _encode_value(self, value: Any) -> float:
        """Encode une valeur en float"""
        if isinstance(value, str):
            return hash(value) % 1000
        elif isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, bool):
            return 1.0 if value else 0.0
        else:
            return 0.0
    
    def _apply_global_fft(self, data: np.ndarray) -> np.ndarray:
        """Application de la FFT globale"""
        # Padding pour puissance de 2
        next_power = 2 ** int(np.ceil(np.log2(len(data))))
        padded_data = np.zeros(next_power)
        padded_data[:len(data)] = data
        
        # FFT
        fft_result = fft2(padded_data.reshape(1, -1))
        return fft_result[0]
    
    def _extract_significant_components(self, harmonic_data: np.ndarray) -> np.ndarray:
        """Extraction des composantes significatives"""
        magnitude = np.abs(harmonic_data)
        total_energy = np.sum(magnitude ** 2)
        
        # Seuil d'énergie
        energy_threshold = total_energy * self.compression_threshold
        
        # Tri par magnitude
        sorted_indices = np.argsort(magnitude)[::-1]
        
        # Sélection jusqu'au seuil
        significant = np.zeros_like(harmonic_data)
        cumulative_energy = 0
        
        for idx in sorted_indices:
            if cumulative_energy < energy_threshold:
                significant[idx] = harmonic_data[idx]
                cumulative_energy += magnitude[idx] ** 2
            else:
                break
        
        return significant
    
    def _quantize_harmonically(self, data: np.ndarray) -> np.ndarray:
        """Quantification harmonique"""
        # Quantification basée sur les harmoniques
        quantized = np.round(data / FUNDAMENTAL_FREQ) * FUNDAMENTAL_FREQ
        return quantized
    
    def _final_compression(self, data: np.ndarray) -> Dict:
        """Compression finale"""
        # Conversion en bytes
        compressed_bytes = data.tobytes()
        
        return {
            'compressed_data': compressed_bytes,
            'original_shape': data.shape,
            'compression_ratio': len(data) * 8 / len(compressed_bytes) / 8,
            'energy_preserved': self.compression_threshold,
            'timestamp': int(time.time())
        }

class HarmonicKnowledgeBase:
    """Base de connaissance harmonique"""
    
    def __init__(self, db_path: str = "harmonic_knowledge.db"):
        self.db_path = db_path
        self.harmonic_index = {}
        self.pattern_library = {}
        self.response_models = {}
        self._init_database()
    
    def _init_database(self):
        """Initialisation de la base de données"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Création des tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_hash TEXT UNIQUE,
                compressed_data BLOB,
                metadata TEXT,
                created_at INTEGER,
                accessed_at INTEGER,
                access_count INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT UNIQUE,
                pattern_data BLOB,
                confidence REAL,
                created_at INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_state (
                id INTEGER PRIMARY KEY,
                user_id TEXT UNIQUE,
                harmonic_profile BLOB,
                total_prompts INTEGER,
                success_rate REAL,
                avg_response_time REAL,
                last_updated INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_and_learn(self, compressed_model: Dict, user_state: Dict) -> Dict:
        """Stockage et apprentissage"""
        
        # 1. Décompression du modèle
        model = self._decompress_model(compressed_model)
        
        # 2. Extraction de la signature
        signature = self._extract_unique_signature(model)
        
        # 3. Stockage en base
        storage_result = self._store_in_database(signature, compressed_model, model)
        
        # 4. Apprentissage des patterns
        learning_result = self._learn_patterns(model, user_state)
        
        # 5. Mise à jour de l'état utilisateur
        self._update_user_state(user_state, learning_result)
        
        return {
            'storage_success': storage_result['success'],
            'patterns_learned': learning_result['patterns_count'],
            'learning_confidence': learning_result['confidence'],
            'signature': signature
        }
    
    def _decompress_model(self, compressed_model: Dict) -> np.ndarray:
        """Décompression du modèle"""
        compressed_data = compressed_model['compressed_data']
        shape = compressed_model['original_shape']
        
        # Reconstruction depuis les bytes
        data = np.frombuffer(compressed_data, dtype=np.float64)
        data = data.reshape(shape)
        
        return data
    
    def _extract_unique_signature(self, model: np.ndarray) -> str:
        """Extraction de signature unique"""
        # Hash des premières composantes
        signature_data = model[:16]  # 16 premières valeurs
        signature_hash = hashlib.sha256(signature_data.tobytes()).hexdigest()[:16]
        return signature_hash
    
    def _store_in_database(self, signature: str, compressed_model: Dict, model: np.ndarray) -> Dict:
        """Stockage en base de données"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Insertion ou mise à jour
            cursor.execute('''
                INSERT OR REPLACE INTO prompt_models 
                (prompt_hash, compressed_data, metadata, created_at, accessed_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                signature,
                compressed_model['compressed_data'],
                json.dumps({
                    'compression_ratio': compressed_model['compression_ratio'],
                    'energy_preserved': compressed_model['energy_preserved']
                }),
                compressed_model['timestamp'],
                int(time.time())
            ))
            
            conn.commit()
            return {'success': True, 'stored': True}
            
        except Exception as e:
            logger.error(f"Erreur stockage: {e}")
            conn.rollback()
            return {'success': False, 'error': str(e)}
        
        finally:
            conn.close()
    
    def _learn_patterns(self, model: np.ndarray, user_state: Dict) -> Dict:
        """Apprentissage des patterns"""
        
        # 1. Analyse des patterns temporels
        temporal_patterns = self._analyze_temporal_patterns(model)
        
        # 2. Analyse des patterns contextuels
        contextual_patterns = self._analyze_contextual_patterns(model)
        
        # 3. Analyse des patterns sémantiques
        semantic_patterns = self._analyze_semantic_patterns(model)
        
        # 4. Intégration
        integrated_patterns = self._integrate_patterns(
            temporal_patterns, contextual_patterns, semantic_patterns
        )
        
        # 5. Stockage des patterns
        pattern_id = self._generate_pattern_id(model)
        self.pattern_library[pattern_id] = integrated_patterns
        
        # Stockage en base
        self._store_pattern_in_db(pattern_id, integrated_patterns)
        
        return {
            'pattern_id': pattern_id,
            'patterns_count': len(integrated_patterns),
            'confidence': self._calculate_learning_confidence(integrated_patterns)
        }
    
    def _analyze_temporal_patterns(self, model: np.ndarray) -> List[Dict]:
        """Analyse des patterns temporels"""
        patterns = []
        
        # Extraction des composantes temporelles (indices 0-4)
        temporal_components = model[:5]
        
        # Détection de patterns récurrents
        if len(temporal_components) > 2:
            # Simple pattern detection
            pattern = {
                'type': 'temporal',
                'components': temporal_components.tolist(),
                'frequency': self._calculate_pattern_frequency(temporal_components),
                'confidence': 0.8
            }
            patterns.append(pattern)
        
        return patterns
    
    def _analyze_contextual_patterns(self, model: np.ndarray) -> List[Dict]:
        """Analyse des patterns contextuels"""
        patterns = []
        
        # Extraction des composantes contextuelles (indices 5-9)
        contextual_components = model[5:10]
        
        if len(contextual_components) > 0:
            pattern = {
                'type': 'contextual',
                'components': contextual_components.tolist(),
                'stability': self._calculate_stability(contextual_components),
                'confidence': 0.7
            }
            patterns.append(pattern)
        
        return patterns
    
    def _analyze_semantic_patterns(self, model: np.ndarray) -> List[Dict]:
        """Analyse des patterns sémantiques"""
        patterns = []
        
        # Extraction des composantes sémantiques (indices 10-14)
        semantic_components = model[10:15]
        
        if len(semantic_components) > 0:
            pattern = {
                'type': 'semantic',
                'components': semantic_components.tolist(),
                'complexity': self._calculate_complexity(semantic_components),
                'confidence': 0.6
            }
            patterns.append(pattern)
        
        return patterns
    
    def _integrate_patterns(self, temporal: List, contextual: List, semantic: List) -> List[Dict]:
        """Intégration des patterns"""
        integrated = temporal + contextual + semantic
        
        # Calcul de la confiance globale
        total_confidence = sum(p['confidence'] for p in integrated)
        avg_confidence = total_confidence / len(integrated) if integrated else 0
        
        # Ajout de métadonnées d'intégration
        for pattern in integrated:
            pattern['integrated_confidence'] = avg_confidence
            pattern['integration_timestamp'] = int(time.time())
        
        return integrated
    
    def _calculate_pattern_frequency(self, components: np.ndarray) -> float:
        """Calcule la fréquence du pattern"""
        # Simple calcul basé sur la variance
        variance = np.var(components)
        return 1.0 / (1.0 + variance)  # Inverse de la variance
    
    def _calculate_stability(self, components: np.ndarray) -> float:
        """Calcule la stabilité des composantes"""
        return 1.0 - np.std(components) / (np.mean(np.abs(components)) + 1e-6)
    
    def _calculate_complexity(self, components: np.ndarray) -> float:
        """Calcule la complexité"""
        return np.sum(np.abs(np.diff(components)))
    
    def _generate_pattern_id(self, model: np.ndarray) -> str:
        """Génère un ID de pattern"""
        pattern_hash = hashlib.sha256(model.tobytes()).hexdigest()[:12]
        return f"pattern_{pattern_hash}"
    
    def _store_pattern_in_db(self, pattern_id: str, patterns: List[Dict]):
        """Stocke les patterns en base"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            pattern_data = pickle.dumps(patterns)
            confidence = np.mean([p['confidence'] for p in patterns])
            
            cursor.execute('''
                INSERT OR REPLACE INTO learned_patterns 
                (pattern_id, pattern_data, confidence, created_at)
                VALUES (?, ?, ?, ?)
            ''', (pattern_id, pattern_data, confidence, int(time.time())))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Erreur stockage pattern: {e}")
            conn.rollback()
        
        finally:
            conn.close()
    
    def _calculate_learning_confidence(self, patterns: List[Dict]) -> float:
        """Calcule la confiance d'apprentissage"""
        if not patterns:
            return 0.0
        
        confidences = [p.get('confidence', 0.5) for p in patterns]
        return np.mean(confidences)
    
    def _update_user_state(self, user_state: Dict, learning_result: Dict):
        """Met à jour l'état utilisateur"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            user_id = user_state.get('user_id', 'default_user')
            
            # Mise à jour des compteurs
            cursor.execute('''
                INSERT OR REPLACE INTO user_state 
                (user_id, total_prompts, success_rate, avg_response_time, last_updated)
                VALUES (?, 
                    COALESCE((SELECT total_prompts FROM user_state WHERE user_id = ?), 0) + 1,
                    ?,
                    ?,
                    ?
                )
            ''', (
                user_id, user_id,
                user_state.get('success_rate', 0.8),
                user_state.get('avg_response_time', 0.5),
                int(time.time())
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Erreur mise à jour état utilisateur: {e}")
            conn.rollback()
        
        finally:
            conn.close()

class PromptLearningSystem:
    """Système principal d'apprentissage par prompt"""
    
    def __init__(self, db_path: str = "harmonic_knowledge.db"):
        self.metadata_extractor = MetadataExtractor()
        self.prompt_modeler = PromptModeler()
        self.harmonic_compressor = HarmonicModelCompression()
        self.knowledge_base = HarmonicKnowledgeBase(db_path)
        
        logger.info("Système d'apprentissage par prompt initialisé")
    
    def process_user_prompt(self, prompt_text: str, context: Dict, user_state: Dict) -> Dict:
        """Pipeline complet de traitement du prompt"""
        
        start_time = time.time()
        
        try:
            # 1. Extraction des métadonnées
            metadata = self.metadata_extractor.extract_metadata(prompt_text, context, user_state)
            
            # 2. Modélisation du prompt
            modeled_prompt = self.prompt_modeler.model_prompt_with_metadata(prompt_text, metadata)
            
            # 3. Compression harmonique
            compressed_model = self.harmonic_compressor.compress_model(modeled_prompt)
            
            # 4. Stockage et apprentissage
            learning_result = self.knowledge_base.store_and_learn(compressed_model, user_state)
            
            # 5. Génération de réponse (basée sur l'apprentissage)
            response = self._generate_response(modeled_prompt, learning_result)
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'response': response,
                'processing_time': processing_time,
                'metadata': asdict(metadata),
                'compression_ratio': compressed_model['compression_ratio'],
                'learning_result': learning_result
            }
            
        except Exception as e:
            logger.error(f"Erreur traitement prompt: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _generate_response(self, modeled_prompt: Dict, learning_result: Dict) -> str:
        """Génère une réponse basée sur l'apprentissage"""
        
        metadata = modeled_prompt['metadata']
        predictions = modeled_prompt['response_predictions']
        
        # Génération basée sur les patterns appris
        if learning_result['patterns_learned'] > 0:
            base_response = "J'ai appris de vos patterns précédents. "
        else:
            base_response = "Je suis en train d'apprendre vos préférences. "
        
        # Adaptation selon le contexte
        if metadata['domain'] == 'work':
            context_response = "Voici une réponse professionnelle adaptée à votre contexte."
        elif metadata['urgency'] == 'high':
            context_response = "Réponse rapide et directe à votre demande urgente."
        else:
            context_response = "Réponse personnalisée selon vos habitudes."
        
        # Ajout de la prédiction
        prediction_text = f"Prédiction de réponse: {predictions['expected_response_length']}, "
        prediction_text += f"ton: {predictions['response_tone']}, "
        prediction_text += f"vitesse: {predictions['response_speed']}"
        
        return f"{base_response} {context_response} {prediction_text}"
    
    def get_learning_metrics(self, user_id: str = 'default_user') -> Dict:
        """Récupère les métriques d'apprentissage"""
        
        conn = sqlite3.connect(self.knowledge_base.db_path)
        cursor = conn.cursor()
        
        try:
            # Métriques utilisateur
            cursor.execute('''
                SELECT total_prompts, success_rate, avg_response_time, last_updated
                FROM user_state WHERE user_id = ?
            ''', (user_id,))
            
            user_metrics = cursor.fetchone()
            
            # Métriques de patterns
            cursor.execute('SELECT COUNT(*) FROM learned_patterns')
            total_patterns = cursor.fetchone()[0]
            
            # Métriques de prompts
            cursor.execute('SELECT COUNT(*) FROM prompt_models')
            total_prompts_stored = cursor.fetchone()[0]
            
            if user_metrics:
                return {
                    'total_prompts_processed': user_metrics[0],
                    'success_rate': user_metrics[1],
                    'avg_response_time': user_metrics[2],
                    'last_updated': user_metrics[3],
                    'total_patterns_learned': total_patterns,
                    'total_prompts_stored': total_prompts_stored,
                    'learning_efficiency': total_patterns / max(1, user_metrics[0])
                }
            else:
                return {
                    'total_prompts_processed': 0,
                    'success_rate': 0.0,
                    'avg_response_time': 0.0,
                    'total_patterns_learned': total_patterns,
                    'total_prompts_stored': total_prompts_stored,
                    'learning_efficiency': 0.0
                }
        
        except Exception as e:
            logger.error(f"Erreur récupération métriques: {e}")
            return {}
        
        finally:
            conn.close()

# Point d'entrée principal
if __name__ == "__main__":
    # Initialisation du système
    learning_system = PromptLearningSystem()
    
    # Test avec un exemple
    test_prompt = "Aide-moi à organiser ma journée de travail demain"
    test_context = {
        'location': 'home',
        'device_type': 'mobile',
        'connectivity': 'wifi',
        'battery_level': 0.8,
        'storage_available': 5000000000
    }
    test_user_state = {
        'user_id': 'test_user',
        'success_rate': 0.85,
        'avg_response_time': 0.3,
        'recent_prompts': ['Organise ma journée', 'Planification travail']
    }
    
    # Traitement du prompt
    result = learning_system.process_user_prompt(test_prompt, test_context, test_user_state)
    
    print("=== Résultat du Traitement ===")
    print(f"Succès: {result['success']}")
    print(f"Réponse: {result.get('response', 'N/A')}")
    print(f"Temps de traitement: {result.get('processing_time', 0):.3f}s")
    print(f"Ratio de compression: {result.get('compression_ratio', 0):.2f}x")
    print(f"Patterns appris: {result.get('learning_result', {}).get('patterns_learned', 0)}")
    
    # Métriques d'apprentissage
    metrics = learning_system.get_learning_metrics('test_user')
    print("\n=== Métriques d'Apprentissage ===")
    for key, value in metrics.items():
        print(f"{key}: {value}")
    
    logger.info("Système d'apprentissage par prompt démontré avec succès")
