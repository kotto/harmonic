#!/usr/bin/env python3
"""
HCS French AI Processor - Traitement IA spécialisé français
Reconnaissance vocale, génération musicale, et traitement du langage français
"""

import torch
import torchaudio
import numpy as np
import librosa
import soundfile as sf
from typing import Dict, List, Optional, Tuple
import logging
import re
from pathlib import Path

# Import IA multilingues
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper non disponible")

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2Seq
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers non disponible")

logger = logging.getLogger(__name__)

class FrenchAIProcessor:
    """
    Processeur IA spécialisé pour le traitement du français
    Reconnaissance vocale, génération musicale, et analyse sémantique
    """
    
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.sample_rate = 48000  # Taux standard pour reconnaissance
        
        # Configuration française
        self.french_config = {
            'language': 'fr',
            'accent': 'france',
            'vocabulary_size': 50000,  # Vocabulaire français riche
            'phonetic_model': True,  # Modèle phonétique français
        }
        
        # Initialisation des modèles
        self.whisper_model = None
        self.music_generator = None
        self.text_processor = None
        
        self.load_french_models()
        
        logger.info(f"French AI Processor initialisé: device={device}, français={self.french_config['language']}")
    
    def load_french_models(self):
        """Charge les modèles IA spécialisés français"""
        
        # 1. Whisper pour reconnaissance vocale française
        if WHISPER_AVAILABLE:
            try:
                self.whisper_model = whisper.load_model("base").to(self.device)
                logger.info("✅ Whisper modèle français chargé")
            except Exception as e:
                logger.error(f"❌ Erreur chargement Whisper: {e}")
                self.whisper_model = None
        
        # 2. Générateur musical avec support français
        if TRANSFORMERS_AVAILABLE:
            try:
                # Modèle de génération musicale multilingue
                self.music_generator = pipeline(
                    "text-to-audio",
                    model="facebook/musicgen-small",
                    device=self.device
                )
                logger.info("✅ MusicGen multilingue chargé")
            except Exception as e:
                logger.error(f"❌ Erreur chargement MusicGen: {e}")
                self.music_generator = None
        
        # 3. Processeur de texte français
        try:
            self.text_processor = pipeline(
                "text2text-generation",
                model="dbmdz/bert-base-french-cased-squad",
                device=self.device
            )
            logger.info("✅ BERT français chargé")
        except Exception as e:
            logger.error(f"❌ Erreur chargement BERT: {e}")
            self.text_processor = None
    
    def transcribe_french_audio(self, audio_path: str) -> Dict:
        """
        Transcrit l'audio français avec Whisper
        """
        if self.whisper_model is None:
            return {"error": "Whisper non disponible"}
        
        try:
            logger.info(f"🎤 Transcription audio français: {audio_path}")
            
            # Transcription avec Whisper
            result = self.whisper_model.transcribe(
                audio_path,
                language="fr",
                task="transcribe",
                fp16=False
            )
            
            # Post-traitement pour le français
            processed_text = self.post_process_french_text(result["text"])
            
            # Analyse sémantique française
            semantic_analysis = self.analyze_french_semantics(processed_text)
            
            transcription_result = {
                "original_text": result["text"],
                "processed_text": processed_text,
                "language": "fr",
                "confidence": result.get("avg_logprob", 0.0),
                "semantic_analysis": semantic_analysis,
                "french_features": self.extract_french_features(processed_text),
                "duration": result.get("duration", 0.0)
            }
            
            logger.info(f"✅ Transcription française complétée: {len(processed_text)} caractères")
            
            return transcription_result
            
        except Exception as e:
            logger.error(f"❌ Erreur transcription française: {e}")
            return {"error": str(e)}
    
    def generate_french_music_description(self, description: str, style: str = "pop") -> Dict:
        """
        Génère une description musicale optimisée pour les modèles IA
        """
        try:
            logger.info(f"🎵 Génération description française: {style}")
            
            # Enrichissement de la description en français
            enhanced_description = self.enhance_french_description(description, style)
            
            # Génération de variations pour l'IA
            variations = self.generate_french_variations(enhanced_description, style)
            
            # Analyse musicale française
            musical_analysis = self.analyze_french_musical_elements(enhanced_description)
            
            generation_config = {
                "original_description": description,
                "enhanced_description": enhanced_description,
                "variations": variations,
                "style": style,
                "musical_analysis": musical_analysis,
                "french_cultural_context": self.get_french_cultural_context(style),
                "recommended_instruments": self.get_french_instruments(style),
                "tempo_suggestions": self.get_french_tempo_suggestions(style)
            }
            
            logger.info(f"✅ Description française enrichie: {len(enhanced_description)} caractères")
            
            return generation_config
            
        except Exception as e:
            logger.error(f"❌ Erreur génération description française: {e}")
            return {"error": str(e)}
    
    def post_process_french_text(self, text: str) -> str:
        """
        Post-traite le texte transcrit pour le français
        """
        # Correction des erreurs courantes de transcription
        corrections = {
            "é": "e",
            "è": "e", 
            "ê": "e",
            "à": "a",
            "â": "a",
            "ä": "a",
            "ô": "o",
            "ö": "o",
            "ù": "u",
            "û": "u",
            "ç": "c"
        }
        
        # Normalisation des accents (optionnel)
        processed = text.lower()
        
        # Ajout de la ponctuation française
        processed = self.add_french_punctuation(processed)
        
        # Correction des contractions françaises
        processed = self.fix_french_contractions(processed)
        
        return processed
    
    def add_french_punctuation(self, text: str) -> str:
        """Ajoute la ponctuation française appropriée"""
        # Ajout des guillemets français « »
        text = re.sub(r'"([^"]*)"', r'« \1 »', text)
        
        # Gestion des points et virgules
        text = re.sub(r'\b(oui|non|peut-être|bien sûr)\b', lambda m: m.group(0) + ',', text, flags=re.IGNORECASE)
        
        # Ajout des points finaux
        if text and text[-1] not in '.!?':
            text += '.'
        
        return text
    
    def fix_french_contractions(self, text: str) -> str:
        """Corrige les contractions françaises courantes"""
        contractions = {
            "j ai": "j'ai",
            "tu as": "t'as",
            "il a": "il a",
            "elle a": "elle a",
            "nous avons": "nous avons",
            "vous avez": "vous avez",
            "ils ont": "ils ont",
            "elles ont": "elles ont",
            "qu est": "qu'est",
            "d abord": "d'abord",
            "aujourd hui": "aujourd'hui",
            "presque": "presqu'"
        }
        
        for contraction, correction in contractions.items():
            text = text.replace(contraction, correction)
        
        return text
    
    def enhance_french_description(self, description: str, style: str) -> str:
        """Enrichit la description avec des éléments français"""
        
        # Mots-clés français par style
        french_keywords = {
            "pop": ["entraînant", "accrocheur", "rythmé", "populaire", "français"],
            "jazz": "improvisé", "sophistiqué", "swing", "blue note", "parisien"],
            "classical": "élégant", "orchestral", "harmonieux", "classique", "français"],
            "electronic": "synthétique", "numérique", "futuriste", "électronique", "français"],
            "cinema": "épique", "dramatique", "cinématographique", "orchestral", "français"]
        }
        
        # Enrichissement sémantique
        enhanced = description.lower()
        
        # Ajout de mots-clés français
        if style in french_keywords:
            keywords = french_keywords[style]
            for keyword in keywords:
                if keyword not in enhanced:
                    enhanced += f", {keyword}"
        
        # Ajout de contextes culturels français
        cultural_contexts = [
            "ambiance française", "style parisien", "chanson française",
            "musique francophone", "culture française"
        ]
        
        for context in cultural_contexts:
            if any(word in enhanced for word in ["musique", "chanson", "style"]):
                enhanced += f", {context}"
        
        return enhanced
    
    def generate_french_variations(self, description: str, style: str) -> List[str]:
        """Génère des variations de description en français"""
        variations = [description]
        
        # Variations stylistiques françaises
        if style == "pop":
            variations.extend([
                f"chanson pop française {description}",
                f"tube français {description}",
                f"hit radio français {description}",
                f"musique pop d'ici {description}"
            ])
        elif style == "jazz":
            variations.extend([
                f"jazz français {description}",
                f"manouche française {description}",
                f"swing parisien {description}",
                f"jazz d'ici {description}"
            ])
        elif style == "classical":
            variations.extend([
                f"musique classique française {description}",
                f"orchestre français {description}",
                f"composition française {description}",
                f"œuvre classique française {description}"
            ])
        
        return variations
    
    def analyze_french_semantics(self, text: str) -> Dict:
        """Analyse sémantique du texte français"""
        
        # Détection de thèmes français
        french_themes = {
            "amour": ["amour", "cœur", "tendre", "romantique", "passion"],
            "nature": ["forêt", "mer", "montagne", "ciel", "jardin", "fleur"],
            "ville": ["paris", "marseille", "lyon", "ville", "rue", "café"],
            "émotions": ["joie", "tristesse", "colère", "peur", "espoir", "rêve"],
            "culture": ["france", "français", "liberté", "égalité", "république"]
        }
        
        detected_themes = []
        for theme, keywords in french_themes.items():
            if any(keyword in text.lower() for keyword in keywords):
                detected_themes.append(theme)
        
        # Analyse des sentiments français
        french_sentiments = {
            "positif": ["joie", "amour", "bonheur", "espoir", "rêve", "liberté"],
            "négatif": ["tristesse", "peur", "colère", "mort", "guerre", "perte"],
            "neutre": ["penser", "voir", "entendre", "parler", "marcher"]
        }
        
        detected_sentiment = "neutre"
        for sentiment, keywords in french_sentiments.items():
            if any(keyword in text.lower() for keyword in keywords):
                detected_sentiment = sentiment
                break
        
        return {
            "detected_themes": detected_themes,
            "sentiment": detected_sentiment,
            "french_cultural_elements": self.extract_french_cultural_elements(text),
            "language_confidence": 0.95 if any(word in text.lower() for word in ["français", "france", "paris"]) else 0.7
        }
    
    def extract_french_cultural_elements(self, text: str) -> List[str]:
        """Extrait les éléments culturels français"""
        cultural_elements = []
        
        french_references = [
            "paris", "france", "français", "eiffel", "louvre", "sacré-cœur",
            "marseillaise", "bastille", "révolution", "liberté", "égalité",
            "fromage", "vin", "baguette", "croissant", "café", "bistrot",
            "métro", "rue", "boulevard", "champs-élysées"
        ]
        
        for reference in french_references:
            if reference in text.lower():
                cultural_elements.append(reference)
        
        return cultural_elements
    
    def analyze_french_musical_elements(self, description: str) -> Dict:
        """Analyse les éléments musicaux français"""
        
        # Instruments typiquement français
        french_instruments = {
            "accordéon": ["accordéon", "harmonica", "guitare française"],
            "bois": ["violon", "flûte", "hautbois", "clarinette", "saxophone"],
            "cuivres": ["trompette", "cor", "trombone", "tuba"],
            "cordes": ["violoncelle", "contrebasse", "harpe", "mandoline"],
            "percussion": ["batterie", "cajon", "tambourin", "darbouka"]
        }
        
        # Styles musicaux français
        french_styles = {
            "chanson française": ["variété", "pop française", "chanson"],
            "musique traditionnelle": ["folk", "traditionnel", "régional"],
            "musique classique": ["orchestre", "symphonie", "opéra"],
            "électronique française": ["techno française", "house français", "electro"]
        }
        
        detected_instruments = []
        detected_styles = []
        
        # Détection des instruments
        for category, instruments in french_instruments.items():
            if any(instrument in description.lower() for instrument in instruments):
                detected_instruments.extend(instruments)
        
        # Détection des styles
        for style, keywords in french_styles.items():
            if any(keyword in description.lower() for keyword in keywords):
                detected_styles.append(style)
        
        return {
            "detected_instruments": list(set(detected_instruments)),
            "detected_styles": list(set(detected_styles)),
            "french_musical_context": self.get_french_musical_context(description),
            "recommended_tempo": self.get_french_tempo_from_style(detected_styles)
        }
    
    def get_french_cultural_context(self, style: str) -> Dict:
        """Retourne le contexte culturel français selon le style"""
        
        contexts = {
            "pop": {
                "era": "contemporain",
                "region": "francophone",
                "influences": ["variété française", "chanson française"],
                "cultural_references": ["radio française", "charts français"]
            },
            "jazz": {
                "era": "1930-1960",
                "region": "parisienne",
                "influences": ["swing parisien", "manouche"],
                "cultural_references": ["le chat qui pèle", "cave de jazz"]
            },
            "classical": {
                "era": "baroque à moderne",
                "region": "européenne",
                "influences": ["opéra français", "orchestre symphonique"],
                "cultural_references": ["opéra garnier", "conservatoire"]
            },
            "electronic": {
                "era": "1980 à aujourd'hui",
                "region": "mondiale",
                "influences": ["techno française", "house parisien"],
                "cultural_references": ["rave", "festival électronique"]
            }
        }
        
        return contexts.get(style, contexts["pop"])
    
    def get_french_instruments(self, style: str) -> List[str]:
        """Retourne les instruments français recommandés"""
        
        instrument_recommendations = {
            "pop": ["guitare", "basse", "batterie", "synthétiseur", "piano"],
            "jazz": ["saxophone", "trompette", "piano", "contrebasse", "batterie"],
            "classical": ["violon", "alto", "violoncelle", "flûte", "hautbois", "harpe"],
            "electronic": ["synthétiseur", "machine à écrire", "sampler", "boite à rythmes"]
        }
        
        return instrument_recommendations.get(style, instrument_recommendations["pop"])
    
    def get_french_tempo_suggestions(self, style: str) -> List[int]:
        """Retourne les tempos recommandés pour le style français"""
        
        tempo_suggestions = {
            "pop": [120, 128, 135],      # Tempos pop français
            "jazz": [80, 120, 140],        # Tempos jazz français
            "classical": [60, 80, 100],       # Tempos classiques
            "electronic": [128, 140, 160]      # Tempos électroniques
        }
        
        return tempo_suggestions.get(style, tempo_suggestions["pop"])
    
    def get_french_musical_context(self, description: str) -> str:
        """Détermine le contexte musical français"""
        
        if any(word in description.lower() for word in ["danse", "fête", "soirée"]):
            return "musique de fête/danse"
        elif any(word in description.lower() for word in ["amour", "cœur", "romantique"]):
            return "musique romantique"
        elif any(word in description.lower() for word in ["paris", "café", "rue"]):
            return "musique urbaine parisienne"
        elif any(word in description.lower() for word in ["nature", "forêt", "campagne"]):
            return "musique traditionnelle française"
        else:
            return "musique française contemporaine"
    
    def get_french_tempo_from_style(self, styles: List[str]) -> int:
        """Détermine le tempo français selon les styles détectés"""
        
        if "jazz" in styles:
            return 120  # Tempo jazz français typique
        elif "classical" in styles:
            return 80   # Tempo classique français
        elif "électronique" in styles:
            return 140  # Tempo électronique français
        else:
            return 128  # Tempo pop français par défaut
    
    def process_french_audio_command(self, command: str, audio_data: np.ndarray) -> Dict:
        """
        Traite les commandes vocales françaises
        """
        try:
            # Transcription de la commande
            transcription = self.transcribe_french_audio_from_array(audio_data)
            
            if "error" in transcription:
                return {"error": "Transcription échouée"}
            
            command_text = transcription["processed_text"].lower()
            
            # Analyse de la commande française
            command_analysis = self.analyze_french_command(command_text)
            
            return {
                "command": command_text,
                "transcription": transcription,
                "analysis": command_analysis,
                "french_language_detected": True,
                "confidence": transcription.get("confidence", 0.0)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur commande française: {e}")
            return {"error": str(e)}
    
    def transcribe_french_audio_from_array(self, audio_data: np.ndarray) -> Dict:
        """Transcrit l'audio français depuis un tableau numpy"""
        if self.whisper_model is None:
            return {"error": "Whisper non disponible"}
        
        try:
            # Sauvegarde temporaire
            temp_path = "temp_french_audio.wav"
            sf.write(temp_path, audio_data.T, self.sample_rate)
            
            # Transcription
            result = self.transcribe_french_audio(temp_path)
            
            # Nettoyage
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur transcription française depuis array: {e}")
            return {"error": str(e)}
    
    def analyze_french_command(self, command: str) -> Dict:
        """Analyse les commandes françaises"""
        
        # Commandes musicales françaises
        french_commands = {
            "générer": ["génère", "crée", "produis", "fais"],
            "jouer": ["joue", "lance", "démarre", "mets"],
            "arrêter": ["arrête", "stop", "pause", "coupe"],
            "sauvegarder": ["sauvegarde", "enregistre", "exporte"],
            "changer": ["change", "modifie", "ajuste", "transforme"],
            "augmenter": ["augmente", "plus fort", "monte le volume"],
            "diminuer": ["diminue", "moins fort", "baisse le volume"]
        }
        
        detected_command = None
        confidence = 0.0
        
        for command_type, keywords in french_commands.items():
            for keyword in keywords:
                if keyword in command:
                    detected_command = command_type
                    confidence = 0.9
                    break
            if detected_command:
                break
        
        return {
            "detected_command": detected_command,
            "confidence": confidence,
            "command_type": detected_command,
            "french_command": True,
            "keywords_found": [kw for kw in french_commands.get(detected_command, []) if kw in command]
        }

# Test du processeur IA français
if __name__ == "__main__":
    print("🇫🇷 French AI Processor Test")
    print("=" * 50)
    
    # Initialisation
    french_ai = FrenchAIProcessor()
    
    try:
        # Test de transcription française
        print("🎤 Test transcription française...")
        
        # Test avec une phrase française
        test_audio_path = "test_french_audio.wav"  # À créer avec un audio français
        
        if os.path.exists(test_audio_path):
            result = french_ai.transcribe_french_audio(test_audio_path)
            print(f"✅ Transcription: {result.get('processed_text', 'N/A')}")
            print(f"   Confiance: {result.get('confidence', 0.0):.2f}")
            print(f"   Éléments français: {result.get('french_features', [])}")
        
        # Test de génération musicale française
        print("\n🎵 Test génération musicale française...")
        description = "musique pop française entraînante avec guitare et batterie"
        music_config = french_ai.generate_french_music_description(description, "pop")
        
        print(f"✅ Description enrichie: {music_config.get('enhanced_description', 'N/A')}")
        print(f"   Variations: {len(music_config.get('variations', []))}")
        print(f"   Instruments français: {music_config.get('recommended_instruments', [])}")
        print(f"   Tempo suggéré: {music_config.get('tempo_suggestions', [])}")
        
        # Test d'analyse sémantique
        print("\n🧠 Test analyse sémantique française...")
        semantic_result = french_ai.analyze_french_semantics("j'aime la musique française et paris")
        print(f"✅ Thèmes détectés: {semantic_result.get('detected_themes', [])}")
        print(f"   Sentiment: {semantic_result.get('sentiment', 'N/A')}")
        print(f"   Éléments culturels: {semantic_result.get('french_cultural_elements', [])}")
        
    except Exception as e:
        print(f"❌ Erreur test IA français: {e}")
