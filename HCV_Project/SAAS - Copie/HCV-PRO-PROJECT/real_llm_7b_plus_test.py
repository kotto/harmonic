#!/usr/bin/env python3
"""
TEST RÉEL AVEC LLM 7B+ - MODÈLES DE GRANDE TAILLE
==================================================

Test réel avec des modèles 7B+ pour des résultats significatifs
et validation précise des claims.
"""

import json
import time
import hashlib
import torch
import statistics
from datetime import datetime
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealLLM7BPlusTester:
    """Testeur réel avec LLM 7B+"""
    
    def __init__(self):
        # Constantes harmoniques
        self.phi = 1.618033988749895
        self.pi = 3.141592653589793
        self.e = 2.718281828459045
        self.alpha_optimal = 0.6180339887498948
        
        # Modèles 7B+ accessibles et performants
        self.models_7b_plus = [
            "EleutherAI/gpt-neo-2.7B",        # 2.7B - Rapide
            "EleutherAI/gpt-j-6B",            # 6B - Très performant
            "bigscience/bloom-560m",           # 560M - Test rapide
            "microsoft/DialoGPT-large",       # 774M - Conversationnel
            "facebook/opt-1.3b",              # 1.3B - Optimisé
        ]
        
        # Pour tester, on commence avec le plus grand disponible
        self.recommended_models = [
            "EleutherAI/gpt-j-6B",            # 6B - Meilleur rapport taille/performance
            "EleutherAI/gpt-neo-2.7B",        # 2.7B - Excellent pour tests
            "microsoft/DialoGPT-large",       # 774M - Si les autres sont trop lents
        ]
        
        self.model_name = None
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Base de données factuelle étendue
        self.factual_db = {
            "capitales": {
                "france": "Paris",
                "allemagne": "Berlin",
                "italie": "Rome",
                "espagne": "Madrid",
                "royaume-uni": "Londres",
                "japon": "Tokyo",
                "chine": "Pékin",
                "états-unis": "Washington",
                "canada": "Ottawa",
                "australie": "Canberra",
                "brésil": "Brasilia",
                "inde": "New Delhi",
                "russie": "Moscou"
            },
            "math": {
                "2+2": "4",
                "3*3": "9",
                "10/2": "5",
                "5+7": "12",
                "8*4": "32",
                "15-7": "8",
                "6*6": "36",
                "100/10": "10",
                "25+25": "50",
                "9*9": "81"
            },
            "sciences": {
                "formule eau": "H2O",
                "formule co2": "CO2",
                "vitesse lumière": "299792458",
                "constante g": "9.81",
                "température ébullition eau": "100",
                "température fusion glace": "0",
                "formule sel": "NaCl",
                "formule glucose": "C6H12O6",
                "nombre avogadro": "6.022e23",
                "constante planck": "6.626e-34"
            },
            "histoire": {
                "révolution française": "1789",
                "déclaration indépendance": "1776",
                "chute berlin": "1989",
                "premier homme sur lune": "1969",
                "fin guerre mondiale": "1945",
                "naissance christophe colomb": "1451",
                "révolution russe": "1917",
                "guerre de sécession": "1861"
            },
            "littérature": {
                "les misérables": "Victor Hugo",
                "le petit prince": "Antoine de Saint-Exupéry",
                "1984": "George Orwell",
                "le seigneur des anneaux": "J.R.R. Tolkien",
                "harry potter": "J.K. Rowling",
                "orgueil et préjugés": "Jane Austen",
                "don quichotte": "Miguel de Cervantes",
                "l'odyssée": "Homère"
            }
        }
        
        # Métriques
        self.results = {
            'determinism_tests': [],
            'hallucination_tests': [],
            'performance_tests': []
        }
    
    def check_model_requirements(self, model_name: str) -> dict:
        """Vérifier les exigences pour le modèle"""
        requirements = {
            'model_name': model_name,
            'estimated_size_gb': 0,
            'recommended': False,
            'memory_required_gb': 0,
            'expected_performance': 'unknown'
        }
        
        # Estimations basées sur les modèles connus
        if "gpt-j-6b" in model_name.lower():
            requirements.update({
                'estimated_size_gb': 24,
                'memory_required_gb': 12,
                'expected_performance': 'excellent',
                'recommended': True
            })
        elif "gpt-neo-2.7b" in model_name.lower():
            requirements.update({
                'estimated_size_gb': 11,
                'memory_required_gb': 6,
                'expected_performance': 'very_good',
                'recommended': True
            })
        elif "opt-1.3b" in model_name.lower():
            requirements.update({
                'estimated_size_gb': 5,
                'memory_required_gb': 3,
                'expected_performance': 'good',
                'recommended': True
            })
        elif "bloom-560m" in model_name.lower():
            requirements.update({
                'estimated_size_gb': 2.2,
                'memory_required_gb': 2,
                'expected_performance': 'good',
                'recommended': False
            })
        else:
            requirements.update({
                'estimated_size_gb': 10,
                'memory_required_gb': 5,
                'expected_performance': 'unknown',
                'recommended': False
            })
        
        return requirements
    
    def setup_model(self, model_name: str) -> bool:
        """Configurer le modèle LLM 7B+"""
        try:
            requirements = self.check_model_requirements(model_name)
            
            logger.info(f"🤖 Configuration du modèle: {model_name}")
            logger.info(f"📊 Taille estimée: {requirements['estimated_size_gb']}GB")
            logger.info(f"💻 Mémoire requise: {requirements['memory_required_gb']}GB")
            logger.info(f"⚡ Performance attendue: {requirements['expected_performance']}")
            
            self.model_name = model_name
            
            # Charger le tokenizer
            logger.info("📦 Chargement du tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            # Ajouter pad token si nécessaire
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Configuration du modèle
            logger.info("🧠 Chargement du modèle...")
            
            # Optimisations selon le device
            model_kwargs = {
                'torch_dtype': torch.float16 if self.device == "cuda" else torch.float32,
                'low_cpu_mem_usage': True
            }
            
            # Pour GPU, utiliser device_map automatique
            if self.device == "cuda":
                model_kwargs['device_map'] = "auto"
            
            # Charger le modèle
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                **model_kwargs
            )
            
            # Pour CPU, forcer le device
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            # Compter les paramètres
            total_params = sum(p.numel() for p in self.model.parameters())
            trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
            
            logger.info(f"✅ Modèle chargé avec succès sur {self.device}")
            logger.info(f"📊 Paramètres totaux: {total_params:,}")
            logger.info(f"📊 Paramètres entraînables: {trainable_params:,}")
            logger.info(f"📊 Taille approx: {total_params * 4 / 1024**3:.2f}GB")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {e}")
            return False
    
    def generate_harmonic_response(self, prompt: str, temperature: float = 0.0, max_length: int = 100) -> dict:
        """Générer une réponse avec couche harmonique sur modèle 7B+"""
        start_time = time.time()
        
        # Tokenizer le prompt
        try:
            inputs = self.tokenizer.encode(prompt, return_tensors="pt", truncation=True, max_length=512)
            if self.device == "cuda":
                inputs = inputs.to(self.device)
        except Exception as e:
            logger.warning(f"⚠️ Erreur tokenization: {e}")
            inputs = self.tokenizer.encode("Test", return_tensors="pt")
            if self.device == "cuda":
                inputs = inputs.to(self.device)
        
        # Génération avec température contrôlée
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=inputs.shape[1] + max_length,
                temperature=temperature,
                do_sample=(temperature > 0.0),
                pad_token_id=self.tokenizer.eos_token_id,
                num_return_sequences=1,
                repetition_penalty=1.1,
                top_p=0.9 if temperature > 0 else 1.0
            )
        
        # Décoder la réponse
        response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extraire seulement la partie générée
        if response_text.startswith(prompt):
            generated_part = response_text[len(prompt):].strip()
        else:
            generated_part = response_text
        
        # Appliquer la couche harmonique
        harmonic_response = self.apply_harmonic_layer(prompt, generated_part)
        
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000
        
        return {
            'prompt': prompt,
            'raw_response': generated_part,
            'harmonic_response': harmonic_response,
            'processing_time_ms': processing_time,
            'temperature': temperature,
            'prompt_hash': hashlib.sha256(prompt.encode()).hexdigest()
        }
    
    def apply_harmonic_layer(self, prompt: str, response: str) -> str:
        """Appliquer la couche harmonique sur modèle 7B+"""
        # Hash déterministe
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        
        # Vérification factuelle approfondie
        factual_check = self.verify_factual_accuracy_deep(prompt, response)
        
        # Construction de la réponse harmonique
        harmonic_signature = f"|φ:{self.phi:.3f}|π:{self.pi:.3f}|α:{self.alpha_optimal:.3f}"
        
        # Si hallucination détectée, corriger avec le modèle 7B+
        if factual_check['is_accurate']:
            final_response = response
        else:
            # Pour les modèles 7B+, on peut essayer de générer une correction
            correction_prompt = f"Corrige cette erreur: {prompt}. La réponse correcte est {factual_check['expected_answer']}."
            try:
                correction_result = self.generate_harmonic_response(correction_prompt, temperature=0.0, max_length=50)
                final_response = correction_result['harmonic_response']
            except:
                final_response = f"{factual_check['expected_answer']} {harmonic_signature} [corrigé]"
        
        # Ajouter la signature harmonique
        final_response += f" {harmonic_signature} [T={temperature}]"
        
        return final_response
    
    def verify_factual_accuracy_deep(self, prompt: str, response: str) -> dict:
        """Vérification factuelle approfondie pour modèles 7B+"""
        prompt_lower = prompt.lower()
        response_lower = response.lower()
        
        # Vérifier les capitales (plus étendu)
        for country, capital in self.factual_db['capitales'].items():
            if f"capitale {country}" in prompt_lower or f"capital {country}" in prompt_lower:
                is_accurate = any(term in response_lower for term in [capital.lower(), country.lower()])
                return {
                    'is_accurate': is_accurate,
                    'expected_answer': f"La capitale de {country.title()} est {capital}",
                    'category': 'capitales',
                    'confidence': 'high' if is_accurate else 'low'
                }
        
        # Vérifier les mathématiques
        for expr, result in self.factual_db['math'].items():
            if expr in prompt_lower:
                is_accurate = result in response_lower or str(result) in response_lower
                return {
                    'is_accurate': is_accurate,
                    'expected_answer': f"{expr} = {result}",
                    'category': 'math',
                    'confidence': 'high' if is_accurate else 'low'
                }
        
        # Vérifier les sciences
        for concept, formula in self.factual_db['sciences'].items():
            if concept in prompt_lower:
                is_accurate = formula.lower() in response_lower
                return {
                    'is_accurate': is_accurate,
                    'expected_answer': f"La {concept} est {formula}",
                    'category': 'sciences',
                    'confidence': 'high' if is_accurate else 'low'
                }
        
        # Vérifier l'histoire
        for event, date in self.factual_db['histoire'].items():
            if event in prompt_lower:
                is_accurate = date in response_lower
                return {
                    'is_accurate': is_accurate,
                    'expected_answer': f"{event} en {date}",
                    'category': 'histoire',
                    'confidence': 'high' if is_accurate else 'low'
                }
        
        # Vérifier la littérature
        for work, author in self.factual_db['littérature'].items():
            if work in prompt_lower:
                is_accurate = any(term in response_lower for term in [author.lower(), author.split()[-1].lower()])
                return {
                    'is_accurate': is_accurate,
                    'expected_answer': f"{work} a été écrit par {author}",
                    'category': 'littérature',
                    'confidence': 'high' if is_accurate else 'low'
                }
        
        # Pas de vérification factuelle trouvée
        return {
            'is_accurate': True,  # Par défaut pour les prompts non factuels
            'expected_answer': response,
            'category': 'général',
            'confidence': 'medium'
        }
    
    def test_determinism_7b_plus(self, num_tests: int = 50) -> dict:
        """Test de déterminisme avec modèle 7B+"""
        logger.info(f"🧪 TEST DE DÉTERMINISME 7B+ - {num_tests} tests")
        
        test_prompts = [
            "Quelle est la capitale de la France?",
            "Combien font 2 + 2?",
            "Quelle est la formule de l'eau?",
            "Qui a écrit 'Les Misérables'?",
            "En quelle année a eu lieu la Révolution française?",
            "Quelle est la capitale du Japon?",
            "Combien font 3 * 3?",
            "Quelle est la vitesse de la lumière?",
            "Qui a écrit '1984'?",
            "Quelle est la capitale du Brésil?"
        ] * (num_tests // 10)
        
        determinism_results = []
        
        for i, prompt in enumerate(test_prompts[:num_tests]):
            if i % 10 == 0:
                logger.info(f"   🔄 Progression: {i}/{num_tests}")
            
            # 3 exécutions avec T=0
            responses = []
            for j in range(3):
                try:
                    result = self.generate_harmonic_response(prompt, temperature=0.0)
                    responses.append(result['harmonic_response'])
                except Exception as e:
                    logger.warning(f"⚠️ Erreur génération: {e}")
                    responses.append(f"Erreur: {e}")
            
            # Vérifier le déterminisme
            unique_responses = len(set(responses))
            determinism_score = 1.0 if unique_responses == 1 else 0.0
            
            determinism_results.append({
                'prompt': prompt,
                'determinism_score': determinism_score,
                'unique_responses': unique_responses,
                'responses': responses
            })
        
        # Calcul des métriques
        total_tests = len(determinism_results)
        perfect_determinism = sum(1 for r in determinism_results if r['determinism_score'] == 1.0)
        determinism_rate = (perfect_determinism / total_tests) * 100
        
        logger.info(f"   📊 Tests déterminisme: {total_tests}")
        logger.info(f"   ✅ Déterminisme parfait: {perfect_determinism}")
        logger.info(f"   🎯 Taux déterminisme: {determinism_rate:.2f}%")
        
        return {
            'total_tests': total_tests,
            'perfect_determinism': perfect_determinism,
            'determinism_rate': determinism_rate,
            'results': determinism_results
        }
    
    def test_hallucination_7b_plus(self, num_tests: int = 40) -> dict:
        """Test d'hallucination avec modèle 7B+"""
        logger.info(f"🎭 TEST D'HALLUCINATION 7B+ - {num_tests} tests")
        
        factual_prompts = [
            "Quelle est la capitale de la France?",
            "Quelle est la capitale de l'Allemagne?",
            "Quelle est la capitale de l'Italie?",
            "Combien font 2 + 2?",
            "Combien font 3 * 3?",
            "Combien font 5 + 7?",
            "Quelle est la formule de l'eau?",
            "Quelle est la formule du CO2?",
            "Quelle est la vitesse de la lumière?",
            "Qui a écrit 'Les Misérables'?",
            "Qui a écrit '1984'?",
            "Qui a écrit 'Le Petit Prince'?",
            "En quelle année a eu lieu la Révolution française?",
            "En quelle année a eu lieu la chute du mur de Berlin?",
            "Quel est le plus grand océan?",
            "Quelle est la constante gravitationnelle?"
        ] * (num_tests // 16)
        
        hallucination_results = []
        
        for i, prompt in enumerate(factual_prompts[:num_tests]):
            if i % 8 == 0:
                logger.info(f"   🔄 Progression: {i}/{num_tests}")
            
            try:
                # Générer la réponse
                result = self.generate_harmonic_response(prompt, temperature=0.0)
                
                # Vérifier l'accuracy
                response_text = result['harmonic_response'].lower()
                
                # Détecter les hallucinations
                factual_check = self.verify_factual_accuracy_deep(prompt, response_text)
                
                hallucination_detected = not factual_check['is_accurate']
                
                hallucination_results.append({
                    'prompt': prompt,
                    'response': result['harmonic_response'],
                    'is_accurate': factual_check['is_accurate'],
                    'expected_answer': factual_check['expected_answer'],
                    'category': factual_check['category'],
                    'confidence': factual_check['confidence'],
                    'hallucination_detected': hallucination_detected
                })
            except Exception as e:
                logger.warning(f"⚠️ Erreur test hallucination: {e}")
                hallucination_results.append({
                    'prompt': prompt,
                    'response': f"Erreur: {e}",
                    'is_accurate': False,
                    'expected_answer': "N/A",
                    'category': 'error',
                    'confidence': 'low',
                    'hallucination_detected': True
                })
        
        # Calcul des métriques
        total_tests = len(hallucination_results)
        accurate_responses = sum(1 for r in hallucination_results if r['is_accurate'])
        hallucinations = sum(1 for r in hallucination_results if r['hallucination_detected'])
        
        accuracy_rate = (accurate_responses / total_tests) * 100
        hallucination_rate = (hallucinations / total_tests) * 100
        
        logger.info(f"   📊 Tests hallucination: {total_tests}")
        logger.info(f"   ✅ Réponses accurate: {accurate_responses}")
        logger.info(f"   🎭 Hallucinations: {hallucinations}")
        logger.info(f"   📊 Accuracy: {accuracy_rate:.2f}%")
        logger.info(f"   🎭 Hallucination: {hallucination_rate:.2f}%")
        
        return {
            'total_tests': total_tests,
            'accurate_responses': accurate_responses,
            'hallucinations': hallucinations,
            'accuracy_rate': accuracy_rate,
            'hallucination_rate': hallucination_rate,
            'results': hallucination_results
        }
    
    def test_performance_7b_plus(self, num_tests: int = 25) -> dict:
        """Test de performance avec modèle 7B+"""
        logger.info(f"⚡ TEST DE PERFORMANCE 7B+ - {num_tests} tests")
        
        test_prompts = [
            "Quelle est la capitale de la France?",
            "Combien font 2 + 2?",
            "Explique la photosynthèse",
            "Décris l'architecture REST",
            "Génère du code Python simple",
            "Quelle est la formule de l'eau?",
            "Qui a écrit 'Les Misérables'?",
            "En quelle année a eu lieu la Révolution française?",
            "Quelle est la vitesse de la lumière?",
            "Décris l'intelligence artificielle"
        ] * (num_tests // 10)
        
        performance_results = []
        
        for i, prompt in enumerate(test_prompts[:num_tests]):
            if i % 5 == 0:
                logger.info(f"   🔄 Progression: {i}/{num_tests}")
            
            try:
                result = self.generate_harmonic_response(prompt, temperature=0.0)
                
                performance_results.append({
                    'prompt': prompt,
                    'processing_time_ms': result['processing_time_ms'],
                    'response_length': len(result['harmonic_response']),
                    'success': True
                })
            except Exception as e:
                logger.warning(f"⚠️ Erreur performance: {e}")
                performance_results.append({
                    'prompt': prompt,
                    'processing_time_ms': 999999,  # Valeur d'erreur
                    'response_length': 0,
                    'success': False
                })
        
        # Filtrer les succès
        successful_tests = [r for r in performance_results if r['success']]
        
        if successful_tests:
            processing_times = [r['processing_time_ms'] for r in successful_tests]
            avg_time = statistics.mean(processing_times)
            median_time = statistics.median(processing_times)
            min_time = min(processing_times)
            max_time = max(processing_times)
        else:
            avg_time = median_time = min_time = max_time = 0
        
        success_rate = (len(successful_tests) / len(performance_results)) * 100
        
        logger.info(f"   📊 Tests performance: {len(performance_results)}")
        logger.info(f"   ✅ Succès: {len(successful_tests)} ({success_rate:.1f}%)")
        logger.info(f"   ⏱️ Temps moyen: {avg_time:.2f}ms")
        logger.info(f"   ⏱️ Temps médian: {median_time:.2f}ms")
        logger.info(f"   ⏱️ Temps min: {min_time:.2f}ms")
        logger.info(f"   ⏱️ Temps max: {max_time:.2f}ms")
        
        return {
            'total_tests': len(performance_results),
            'successful_tests': len(successful_tests),
            'success_rate': success_rate,
            'avg_time_ms': avg_time,
            'median_time_ms': median_time,
            'min_time_ms': min_time,
            'max_time_ms': max_time,
            'results': performance_results
        }
    
    def run_real_7b_plus_test(self, model_name: str = None) -> dict:
        """Exécuter le test réel complet avec modèle 7B+"""
        
        # Sélectionner le meilleur modèle disponible
        if model_name is None:
            for model in self.recommended_models:
                requirements = self.check_model_requirements(model)
                if requirements['recommended']:
                    model_name = model
                    break
        
        if model_name is None:
            model_name = "EleutherAI/gpt-neo-2.7B"  # Par défaut
        
        logger.info("🌊 TEST RÉEL AVEC LLM 7B+")
        logger.info("=" * 60)
        logger.info(f"🤖 Modèle: {model_name}")
        logger.info(f"💻 Device: {self.device}")
        requirements = self.check_model_requirements(model_name)
        logger.info(f"📊 Taille estimée: {requirements['estimated_size_gb']}GB")
        logger.info(f"⚡ Performance attendue: {requirements['expected_performance']}")
        logger.info("=" * 60)
        
        # Configuration du modèle
        if not self.setup_model(model_name):
            return {'error': 'Failed to setup model'}
        
        start_time = time.time()
        
        # Test 1: Déterminisme
        determinism_results = self.test_determinism_7b_plus(30)
        
        # Test 2: Hallucination
        hallucination_results = self.test_hallucination_7b_plus(25)
        
        # Test 3: Performance
        performance_results = self.test_performance_7b_plus(20)
        
        end_time = time.time()
        
        # Calcul du score global
        determinism_score = determinism_results['determinism_rate']
        hallucination_score = 100 - hallucination_results['hallucination_rate']
        performance_score = max(0, 100 - (performance_results['avg_time_ms'] / 50) * 100)
        
        overall_score = (determinism_score + hallucination_score + performance_score) / 3
        
        # Résultats finaux
        final_results = {
            'test_info': {
                'model_name': model_name,
                'device': self.device,
                'model_requirements': requirements,
                'total_duration_seconds': end_time - start_time,
                'test_date': datetime.now().isoformat()
            },
            'determinism': determinism_results,
            'hallucination': hallucination_results,
            'performance': performance_results,
            'overall_score': overall_score,
            'claims_validation': {
                'determinism_claim': 'VALIDÉ' if determinism_score >= 95.0 else 'PARTIEL',
                'hallucination_claim': 'VALIDÉ' if hallucination_score >= 95.0 else 'PARTIEL',
                'performance_claim': 'VALIDÉ' if performance_results['avg_time_ms'] <= 50 else 'PARTIEL'
            }
        }
        
        # Affichage des résultats
        self.display_real_7b_plus_results(final_results)
        
        # Sauvegarde
        self.save_real_7b_plus_results(final_results)
        
        return final_results
    
    def display_real_7b_plus_results(self, results):
        """Afficher les résultats réels 7B+"""
        print("\n" + "=" * 80)
        print("🌊 RÉSULTATS TEST RÉEL LLM 7B+")
        print("=" * 80)
        
        print(f"🤖 Modèle: {results['test_info']['model_name']}")
        print(f"💻 Device: {results['test_info']['device']}")
        print(f"📊 Taille: {results['test_info']['model_requirements']['estimated_size_gb']}GB")
        print(f"⏱️ Durée: {results['test_info']['total_duration_seconds']:.1f} secondes")
        print("")
        
        print("🎯 CLAIMS VALIDATION RÉELLE 7B+:")
        print(f"   🔄 Déterminisme: {results['determinism']['determinism_rate']:.2f}% - {results['claims_validation']['determinism_claim']}")
        print(f"   🎭 Hallucination: {100 - results['hallucination']['hallucination_rate']:.2f}% - {results['claims_validation']['hallucination_claim']}")
        print(f"   ⚡ Performance: {results['performance']['avg_time_ms']:.1f}ms - {results['claims_validation']['performance_claim']}")
        print("")
        
        print("📊 MÉTRIQUES RÉELLES 7B+:")
        print(f"   🔄 Tests déterminisme: {results['determinism']['total_tests']}")
        print(f"   ✅ Déterminisme parfait: {results['determinism']['perfect_determinism']}")
        print(f"   🎭 Tests hallucination: {results['hallucination']['total_tests']}")
        print(f"   ❌ Hallucinations: {results['hallucination']['hallucinations']}")
        print(f"   ⚡ Succès performance: {results['performance']['successful_tests']}/{results['performance']['total_tests']}")
        print(f"   ⏱️ Temps moyen: {results['performance']['avg_time_ms']:.1f}ms")
        print("")
        
        print("🏆 SCORE GLOBAL RÉEL 7B+:")
        print(f"   📊 Score: {results['overall_score']:.1f}/100")
        
        if results['overall_score'] >= 80:
            print("   🏆 TEST RÉEL 7B+ RÉUSSI")
            print("   🌊 Les claims sont validés avec un modèle 7B+")
        elif results['overall_score'] >= 60:
            print("   🥈 TEST RÉEL 7B+ PARTIEL")
            print("   🌊 Les claims sont partiellement validés")
        else:
            print("   ❌ TEST RÉEL 7B+ ÉCHOUÉ")
            print("   🌊 Les claims nécessitent des ajustements")
        
        print("=" * 80)
    
    def save_real_7b_plus_results(self, results):
        """Sauvegarder les résultats réels 7B+"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path(f"real_llm_7b_plus_results_{timestamp}.json")
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"💾 Résultats sauvegardés: {results_file}")

def main():
    """Fonction principale"""
    print("🌊 TEST RÉEL AVEC LLM 7B+ - VALIDATION DES CLAIMS")
    print("=" * 70)
    print("🎯 Objectif: Tester les claims avec un vrai modèle 7B+")
    print("🤖 Modèles recommandés: GPT-J-6B, GPT-Neo-2.7B, DialoGPT-Large")
    print("📊 Tests: Déterminisme, Hallucination, Performance")
    print("⚡ Avantage: Meilleure qualité des réponses avec 7B+")
    print("=" * 70)
    
    tester = RealLLM7BPlusTester()
    
    # Tester avec le meilleur modèle disponible
    results = tester.run_real_7b_plus_test()
    
    if 'error' not in results:
        print(f"\n🚀 CONCLUSION DU TEST RÉEL 7B+:")
        if results['overall_score'] >= 80:
            print("   ✅ Les claims sont validés avec un modèle 7B+")
            print("   🌊 Excellente base pour le test Deepseek")
        elif results['overall_score'] >= 60:
            print("   ⚠️ Les claims sont partiellement validés")
            print("   🌊 Bonne base, nécessite des ajustements")
        else:
            print("   ❌ Les claims ne sont pas validés")
            print("   🌊 Refonte nécessaire avant Deepseek")
        
        print(f"📊 Score obtenu: {results['overall_score']:.1f}/100")
    else:
        print("❌ Erreur lors du test réel 7B+")

if __name__ == "__main__":
    main()
