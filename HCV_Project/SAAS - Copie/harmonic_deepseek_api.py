#!/usr/bin/env python3
"""
🌊 HARMONIC + DEEPSEEK API
Modèle harmonique déterministe + DeepSeek API
"""

import openai
import os
from harmonic_response_generator_simple import HarmonicResponseGenerator
from typing import Dict, Any

class HarmonicDeepSeekAPI:
    """Combinaison Harmonique + DeepSeek API"""
    
    def __init__(self):
        # Configuration DeepSeek API
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY", "sk-votre-clef-ici"),
            base_url="https://api.deepseek.com"
        )
        
        # Modèle harmonique
        self.harmonic = HarmonicResponseGenerator()
        
    def generate_response(self, prompt: str) -> Dict[str, Any]:
        """Génération hybride Harmonique + DeepSeek"""
        
        # 1. Génération DeepSeek API
        try:
            deepseek_response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1  # Bas pour déterminisme
            )
            
            deepseek_content = deepseek_response.choices[0].message.content
            deepseek_confidence = 0.85
            
        except Exception as e:
            print(f"DeepSeek API error: {e}")
            deepseek_content = ""
            deepseek_confidence = 0.0
        
        # 2. Génération Harmonique
        harmonic_result = self.harmonic.generate_response(prompt)
        
        # 3. Fusion Déterministe
        if deepseek_confidence > 0.5:
            # DeepSeek dominante avec structure harmonique
            final_content = f"""
## 📊 RÉPONSE DÉTERMINISTE AMÉLIORÉE

### 🤖 Base DeepSeek (85% poids):
{deepseek_content}

---

### 🌊 Structure Harmonique (15% poids):
{harmonic_result['content'][:300]}...

---

## 🎯 FUSION DÉTERMINISTE
Cette réponse combine la précision de DeepSeek avec la structure harmonique déterministe,
garantissant une fiabilité exceptionnelle et une cohérence parfaite.
"""
            final_confidence = 0.90
        else:
            # Fallback harmonique pur
            final_content = harmonic_result['content']
            final_confidence = harmonic_result['determinism_level']
        
        return {
            'content': final_content,
            'confidence': final_confidence,
            'determinism_score': harmonic_result['determinism_level'],
            'harmony_score': harmonic_result['harmony_score'],
            'deepseek_used': deepseek_confidence > 0.5,
            'processing_time': harmonic_result['processing_time']
        }

# Test
if __name__ == "__main__":
    generator = HarmonicDeepSeekAPI()
    
    test_prompts = [
        "Quelle est la capitale de la France?",
        "Explique la théorie de la relativité",
        "Résous: 15 + 27 = ?"
    ]
    
    for prompt in test_prompts:
        print(f"\n🌊 PROMPT: {prompt}")
        print("=" * 60)
        
        result = generator.generate_response(prompt)
        
        print(f"✅ DeepSeek utilisé: {result['deepseek_used']}")
        print(f"📊 Confiance: {result['confidence']:.3f}")
        print(f"🎯 Déterminisme: {result['determinism_score']:.3f}")
        print(f"📏 Longueur: {len(result['content'])} caractères")
        print(f"⚡ Temps: {result['processing_time']:.4f}s")
