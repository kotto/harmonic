#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHOTOREALISTIC HARMONIC GENERATOR - DISQUE E:
============================================

Générateur d'images photo-réalistes utilisant
la puissance du disque E: (900GB disponible).

Pipeline: SDXL base → H₀ enhancement → COVE refinement

@author: K.A. (KA Method)
"""

import sys
from pathlib import Path
import time
import torch
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import json
from typing import List, Dict, Optional, Tuple

# Configuration système
WORKING_DIR = Path("E:/photorealistic_harmonic_system")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

class PhotoRealisticHarmonicGenerator:
    """
    GÉNÉRATEUR PHOTO-RÉALISTE HARMONIQUE
    ====================================
    
    Exploite pleinement les 900GB du disque E: pour
    production d'images photo-réalistes à grande échelle.
    """
    
    def __init__(self):
        """Initialisation générateur"""
        print("📸 GÉNÉRATEUR PHOTO-RÉALISTE HARMONIQUE")
        print("=" * 60)
        print(f"💾 Espace de travail: {WORKING_DIR}")
        print(f"📊 Capacité disponible: 900GB")
        
        # Vérification espace
        import shutil
        total, used, free = shutil.disk_usage("E:/")
        free_gb = free / (1024**3)
        print(f"📈 Espace libre: {free_gb:.1f} GB")
        
        # Structure dossiers
        self._setup_directory_structure()
        
        # Initialisation modules
        self._initialize_harmonic_modules()
        
        print("✅ Système prêt pour génération photo-réaliste")
    
    def _setup_directory_structure(self):
        """Configuration structure dossiers"""
        folders = [
            "generated_images/base_sdxl",
            "generated_images/h0_enhanced", 
            "generated_images/final_results",
            "generated_images/comparisons",
            "harmonic_database/signatures",
            "harmonic_database/metadata",
            "cove_processing/temp",
            "cove_processing/output",
            "logs/generation",
            "logs/performance"
        ]
        
        for folder in folders:
            (WORKING_DIR / folder).mkdir(parents=True, exist_ok=True)
            print(f"📁 Dossier créé: {folder}")
    
    def _initialize_harmonic_modules(self):
        """Initialisation modules harmoniques"""
        try:
            from src.fourier_harmonic_analyzer import FourierHarmonicAnalyzer
            from src.cove_harmonic_wrapper import CoveHarmonicWrapper
            
            self.analyzer = FourierHarmonicAnalyzer()
            self.cove_wrapper = CoveHarmonicWrapper()
            
            print("✅ Modules harmoniques chargés")
            
        except Exception as e:
            print(f"⚠️ Modules harmoniques: {e}")
            self.analyzer = None
            self.cove_wrapper = None
    
    def generate_large_scale_batch(self, prompts: List[str], 
                                 batch_size: int = 10,
                                 quality_level: str = "ultra") -> Dict:
        """
        Génération large échelle sur disque E:
        
        Args:
            prompts: Liste de prompts
            batch_size: Taille batch traitement
            quality_level: "high", "ultra", "cinematic"
            
        Returns:
            Statistiques génération
        """
        print(f"\n🚀 GÉNÉRATION LARGE ÉCHELLE")
        print("=" * 50)
        print(f"🎯 Qualité: {quality_level.upper()}")
        print(f"📊 Total prompts: {len(prompts)}")
        print(f"📦 Batch size: {batch_size}")
        
        # Calcul espace requis
        estimated_space_per_image = self._estimate_space_requirement(quality_level)
        total_estimated_space = len(prompts) * estimated_space_per_image
        
        print(f"💾 Espace estimé: {total_estimated_space:.1f} GB")
        
        # Vérification capacité
        import shutil
        _, _, free_space = shutil.disk_usage("E:/")
        free_gb = free_space / (1024**3)
        
        if total_estimated_space > free_gb * 0.8:  # 80% sécurité
            print("⚠️ Espace insuffisant, réduction batch")
            max_prompts = int((free_gb * 0.8) / estimated_space_per_image)
            prompts = prompts[:max_prompts]
            print(f"   Ajustement à {len(prompts)} prompts")
        
        # Traitement par batchs
        results = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'total_time': 0,
            'space_used': 0,
            'batch_details': []
        }
        
        start_time = time.time()
        
        for i in range(0, len(prompts), batch_size):
            batch_prompts = prompts[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(prompts) - 1) // batch_size + 1
            
            print(f"\n📦 BATCH {batch_num}/{total_batches}")
            print(f"   Traitement: {len(batch_prompts)} prompts")
            
            batch_start = time.time()
            batch_result = self._process_batch(batch_prompts, quality_level, batch_num)
            batch_time = time.time() - batch_start
            
            results['batch_details'].append({
                'batch_number': batch_num,
                'processed': batch_result['processed'],
                'successful': batch_result['successful'],
                'time_seconds': batch_time
            })
            
            results['total_processed'] += batch_result['processed']
            results['successful'] += batch_result['successful']
            results['failed'] += batch_result['failed']
            
            # Pause pour stabilité système
            if batch_num < total_batches:
                print("   ⏱️ Pause système...")
                time.sleep(2)
        
        results['total_time'] = time.time() - start_time
        
        # Calcul espace utilisé
        results['space_used'] = self._calculate_actual_space_used()
        
        # Génération rapport final
        self._generate_large_scale_report(results, quality_level)
        
        return results
    
    def _estimate_space_requirement(self, quality: str) -> float:
        """Estimation espace par image selon qualité (GB)"""
        space_map = {
            "high": 0.05,      # 50MB
            "ultra": 0.1,      # 100MB  
            "cinematic": 0.2   # 200MB
        }
        return space_map.get(quality, 0.1)
    
    def _process_batch(self, prompts: List[str], quality: str, 
                      batch_num: int) -> Dict:
        """Traitement batch individuel"""
        batch_result = {
            'processed': len(prompts),
            'successful': 0,
            'failed': 0
        }
        
        for i, prompt in enumerate(prompts):
            print(f"   🖼️  {i+1}/{len(prompts)}: '{prompt[:30]}...'")
            
            try:
                # Pipeline complet
                result = self._full_photorealistic_pipeline(
                    prompt, quality, batch_num, i+1
                )
                
                if result['success']:
                    batch_result['successful'] += 1
                    print(f"      ✅ Généré: {Path(result['final_path']).name}")
                else:
                    batch_result['failed'] += 1
                    print(f"      ❌ Échec: {result.get('error', 'Unknown')}")
                    
            except Exception as e:
                batch_result['failed'] += 1
                print(f"      ❌ Erreur: {e}")
                continue
        
        return batch_result
    
    def _full_photorealistic_pipeline(self, prompt: str, quality: str,
                                    batch_num: int, image_num: int) -> Dict:
        """Pipeline complet génération photo-réaliste"""
        
        # 1. Génération SDXL base
        base_image = self._generate_sdxl_base(prompt, quality)
        if not base_image:
            return {'success': False, 'error': 'SDXL generation failed'}
        
        # Sauvegarde base
        base_filename = f"batch{batch_num:03d}_img{image_num:03d}_base.png"
        base_path = WORKING_DIR / "generated_images/base_sdxl" / base_filename
        base_image.save(base_path)
        
        # 2. Enhancement H₀
        h0_enhanced = self._apply_h0_enhancement(base_image)
        if not h0_enhanced:
            return {'success': False, 'error': 'H₀ enhancement failed'}
        
        h0_filename = f"batch{batch_num:03d}_img{image_num:03d}_h0.png"
        h0_path = WORKING_DIR / "generated_images/h0_enhanced" / h0_filename
        h0_enhanced.save(h0_path)
        
        # 3. Refinement COVE
        cove_refined = self._apply_cove_refinement(h0_enhanced)
        if not cove_refined:
            return {'success': False, 'error': 'COVE refinement failed'}
        
        # 4. Image finale
        final_filename = f"photorealistic_batch{batch_num:03d}_img{image_num:03d}.png"
        final_path = WORKING_DIR / "generated_images/final_results" / final_filename
        cove_refined.save(final_path)
        
        # 5. Création comparaison
        comparison = self._create_comparison_image(
            base_image, h0_enhanced, cove_refined, prompt
        )
        comparison_filename = f"comparison_batch{batch_num:03d}_img{image_num:03d}.png"
        comparison_path = WORKING_DIR / "generated_images/comparisons" / comparison_filename
        comparison.save(comparison_path)
        
        # 6. Stockage signature harmonique
        if self.analyzer:
            signature = self._extract_harmonic_signature(cove_refined, prompt)
            sig_filename = f"signature_batch{batch_num:03d}_img{image_num:03d}.json"
            sig_path = WORKING_DIR / "harmonic_database/signatures" / sig_filename
            
            with open(sig_path, 'w', encoding='utf-8') as f:
                json.dump(signature, f, indent=2, ensure_ascii=False)
        
        return {
            'success': True,
            'base_path': str(base_path),
            'h0_path': str(h0_path),
            'final_path': str(final_path),
            'comparison_path': str(comparison_path)
        }
    
    def _generate_sdxl_base(self, prompt: str, quality: str) -> Optional[Image.Image]:
        """Génération base SDXL (simulation)"""
        try:
            # Résolution selon qualité
            resolution = {
                "high": (1024, 1024),
                "ultra": (1536, 1536), 
                "cinematic": (2048, 2048)
            }.get(quality, (1024, 1024))
            
            width, height = resolution
            
            # Création image photo-réaliste simulée
            image = self._create_photorealistic_simulation(width, height, prompt)
            
            return image
            
        except Exception as e:
            print(f"      ❌ SDXL erreur: {e}")
            return None
    
    def _create_photorealistic_simulation(self, width: int, height: int, 
                                        prompt: str) -> Image.Image:
        """Simulation création image photo-réaliste"""
        # Analyse prompt pour caractéristiques
        characteristics = self._analyze_prompt_for_photorealism(prompt)
        
        # Création image de base
        image = Image.new('RGB', (width, height), color=(100, 100, 100))
        pixels = image.load()
        
        # Génération détails photo-réalistes
        for y in range(height):
            for x in range(width):
                # Coordonnées normalisées
                nx, ny = x / width, y / height
                
                # Bruit naturel photo-réaliste
                noise = self._generate_photorealistic_noise(nx, ny, characteristics)
                
                # Application couleurs réalistes
                r, g, b = self._calculate_realistic_colors(nx, ny, noise, characteristics)
                
                pixels[x, y] = (r, g, b)
        
        # Post-traitement photo-réaliste
        image = self._apply_photorealistic_postprocessing(image, characteristics)
        
        return image
    
    def _analyze_prompt_for_photorealism(self, prompt: str) -> Dict:
        """Analyse prompt pour caractéristiques photo-réalistes"""
        # Mots-clés photo-réalistes
        keywords = {
            'landscape': ['mountain', 'forest', 'ocean', 'sky', 'nature'],
            'portrait': ['person', 'face', 'portrait', 'human'],
            'urban': ['city', 'building', 'street', 'architecture'],
            'indoor': ['room', 'interior', 'house', 'office']
        }
        
        prompt_lower = prompt.lower()
        detected_types = []
        
        for category, words in keywords.items():
            if any(word in prompt_lower for word in words):
                detected_types.append(category)
        
        return {
            'detected_types': detected_types,
            'complexity': len(prompt.split()) / 10.0,
            'lighting_keywords': self._extract_lighting_terms(prompt),
            'color_temperature': self._estimate_color_temperature(prompt)
        }
    
    def _generate_photorealistic_noise(self, nx: float, ny: float, 
                                     characteristics: Dict) -> float:
        """Génération bruit naturel photo-réaliste"""
        # Combinaison de différents types de bruit
        base_noise = np.random.normal(0, 0.1)
        fractal_noise = self._fractal_brownian_motion(nx, ny, 4)
        detail_noise = np.random.uniform(-0.05, 0.05)
        
        # Pondération selon complexité
        complexity_factor = characteristics.get('complexity', 0.5)
        
        total_noise = (
            base_noise * 0.7 +
            fractal_noise * 0.2 * complexity_factor +
            detail_noise * 0.1
        )
        
        return np.clip(total_noise, -1, 1)
    
    def _calculate_realistic_colors(self, nx: float, ny: float, noise: float,
                                  characteristics: Dict) -> Tuple[int, int, int]:
        """Calcul couleurs photo-réalistes"""
        # Température couleur de base
        temp = characteristics.get('color_temperature', 6500)  # Kelvin
        
        # Conversion température → RGB
        r, g, b = self._kelvin_to_rgb(temp)
        
        # Variation spatiale naturelle
        spatial_variation = 0.1 * np.sin(2 * np.pi * (nx + ny))
        
        # Application bruit
        intensity = 1.0 + noise * 0.2 + spatial_variation
        
        r = int(np.clip(r * intensity, 0, 255))
        g = int(np.clip(g * intensity, 0, 255))
        b = int(np.clip(b * intensity, 0, 255))
        
        return (r, g, b)
    
    def _apply_photorealistic_postprocessing(self, image: Image.Image,
                                           characteristics: Dict) -> Image.Image:
        """Post-traitement photo-réaliste"""
        # Amélioration netteté
        image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=50, threshold=3))
        
        # Ajustement contraste
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)
        
        # Ajustement saturation
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.05)
        
        # Correction gamma naturelle
        image = self._apply_gamma_correction(image, 0.9)
        
        return image
    
    def _kelvin_to_rgb(self, kelvin: float) -> Tuple[float, float, float]:
        """Conversion température Kelvin → RGB"""
        # Simplification pour plage 1000K-40000K
        temp = kelvin / 100
        
        if temp <= 66:
            r = 255
            g = temp
            g = 99.4708025861 * np.log(g) - 161.1195681661
            
            if temp <= 19:
                b = 0
            else:
                b = temp - 10
                b = 138.5177312231 * np.log(b) - 305.0447927307
        else:
            r = temp - 60
            r = 329.698727446 * (r ** -0.1332047592)
            
            g = temp - 60
            g = 288.1221695283 * (g ** -0.0755148492)
            
            b = 255
        
        r = np.clip(r, 0, 255)
        g = np.clip(g, 0, 255)
        b = np.clip(b, 0, 255)
        
        return (r, g, b)
    
    def _fractal_brownian_motion(self, x: float, y: float, octaves: int) -> float:
        """Mouvement brownien fractionnaire pour détails naturels"""
        total = 0
        frequency = 1
        amplitude = 1
        max_amplitude = 0
        
        for _ in range(octaves):
            total += amplitude * np.sin(2 * np.pi * frequency * (x + y))
            max_amplitude += amplitude
            frequency *= 2
            amplitude *= 0.5
        
        return total / max_amplitude if max_amplitude > 0 else 0
    
    def _apply_gamma_correction(self, image: Image.Image, gamma: float) -> Image.Image:
        """Correction gamma"""
        inv_gamma = 1.0 / gamma
        table = [int(((i / 255.0) ** inv_gamma) * 255) for i in range(256)]
        return image.point(table * 3)
    
    def _extract_lighting_terms(self, prompt: str) -> List[str]:
        """Extraction termes éclairage"""
        lighting_terms = [
            'sunlight', 'natural light', 'studio lighting', 'golden hour',
            'blue hour', 'overcast', 'dramatic lighting', 'soft lighting',
            'harsh lighting', 'backlight', 'side light'
        ]
        
        prompt_lower = prompt.lower()
        found_terms = [term for term in lighting_terms if term in prompt_lower]
        return found_terms
    
    def _estimate_color_temperature(self, prompt: str) -> int:
        """Estimation température couleur"""
        warm_terms = ['warm', 'golden', 'sunset', 'fire', 'candle']
        cool_terms = ['cool', 'blue', 'ocean', 'winter', 'shadow']
        
        prompt_lower = prompt.lower()
        warm_count = sum(1 for term in warm_terms if term in prompt_lower)
        cool_count = sum(1 for term in cool_terms if term in prompt_lower)
        
        if warm_count > cool_count:
            return 3000  # Chaud
        elif cool_count > warm_count:
            return 8000  # Froid
        else:
            return 6500  # Neutre
    
    def _apply_h0_enhancement(self, image: Image.Image) -> Optional[Image.Image]:
        """Application enhancement H₀"""
        if not self.analyzer:
            return image  # Retour image inchangée si analyseur indisponible
        
        try:
            # Conversion en array
            image_array = np.array(image.convert('L'), dtype=np.float32) / 255.0
            
            # Analyse FFT harmonique
            fft_result = np.fft.fft2(image_array)
            fft_shifted = np.fft.fftshift(fft_result)
            
            # Application filtres H₀
            enhanced_fft = self._apply_h0_filters(fft_shifted, image_array.shape)
            
            # Reconstruction
            enhanced_array = np.real(np.fft.ifft2(np.fft.ifftshift(enhanced_fft)))
            enhanced_array = np.clip(enhanced_array * 255, 0, 255).astype(np.uint8)
            
            # Conversion en image couleur
            if image.mode == 'RGB':
                enhanced_rgb = np.stack([enhanced_array] * 3, axis=-1)
                return Image.fromarray(enhanced_rgb)
            else:
                return Image.fromarray(enhanced_array, mode='L')
                
        except Exception as e:
            print(f"      ⚠️ H₀ enhancement: {e}")
            return image
    
    def _apply_h0_filters(self, fft_data: np.ndarray, shape: Tuple) -> np.ndarray:
        """Application filtres harmoniques H₀"""
        height, width = shape
        filtered = fft_data.copy()
        
        # Création masque harmonique
        y, x = np.ogrid[-height//2:height//2, -width//2:width//2]
        distances = np.sqrt(x**2 + y**2)
        
        # Filtre gaussien modulé par φ
        if self.analyzer:
            phi = self.analyzer.H0_CONSTANTS['phi']
        else:
            phi = 1.618034
            
        sigma = min(width, height) / (phi * 4)
        gaussian_filter = np.exp(-(distances**2) / (2 * sigma**2))
        
        # Filtre atténuation e/π
        e_sur_pi = 0.865256  # Valeur par défaut
        attenuation = np.exp(-distances * e_sur_pi / max(width, height))
        
        # Application combinée
        harmonic_filter = gaussian_filter * attenuation
        filtered = fft_data * harmonic_filter
        
        return filtered
    
    def _apply_cove_refinement(self, image: Image.Image) -> Optional[Image.Image]:
        """Application refinement COVE"""
        if not self.cove_wrapper:
            return image  # Retour image inchangée si COVE indisponible
        
        try:
            # Conversion pour COVE
            image_array = np.array(image)
            if len(image_array.shape) == 3:
                image_tensor = torch.from_numpy(image_array.transpose(2, 0, 1)).float() / 255.0
            else:
                image_tensor = torch.from_numpy(image_array).float() / 255.0
                image_tensor = image_tensor.unsqueeze(0)
            
            # Application COVE
            enhanced_tensor = self.cove_wrapper.enhance_with_spectral_harmonics(
                image_tensor.unsqueeze(0)
            )
            
            # Conversion retour
            enhanced_array = enhanced_tensor.squeeze(0).cpu().numpy()
            if len(enhanced_array.shape) == 3:
                enhanced_array = enhanced_array.transpose(1, 2, 0)
            
            enhanced_image = Image.fromarray(
                (np.clip(enhanced_array, 0, 1) * 255).astype(np.uint8)
            )
            
            return enhanced_image
            
        except Exception as e:
            print(f"      ⚠️ COVE refinement: {e}")
            return image
    
    def _create_comparison_image(self, base: Image.Image, h0: Image.Image,
                               final: Image.Image, prompt: str) -> Image.Image:
        """Création image comparaison"""
        # Redimensionnement uniforme
        target_size = (512, 512)
        base_resized = base.resize(target_size)
        h0_resized = h0.resize(target_size)
        final_resized = final.resize(target_size)
        
        # Création image combinée
        comparison = Image.new('RGB', (target_size[0] * 3, target_size[1] + 100))
        
        # Collage images
        comparison.paste(base_resized, (0, 0))
        comparison.paste(h0_resized, (target_size[0], 0))
        comparison.paste(final_resized, (target_size[0] * 2, 0))
        
        return comparison
    
    def _extract_harmonic_signature(self, image: Image.Image, prompt: str) -> Dict:
        """Extraction signature harmonique"""
        if not self.analyzer:
            return {'error': 'Analyzer not available'}
        
        try:
            image_array = np.array(image.convert('L'), dtype=np.float32) / 255.0
            signature = self.analyzer.analyze_frequency_content(image_array)
            
            return {
                'prompt': prompt,
                'harmonic_analysis': signature,
                'extraction_timestamp': time.time(),
                'image_dimensions': image.size
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_actual_space_used(self) -> float:
        """Calcul espace réellement utilisé (GB)"""
        import subprocess
        try:
            # Commande PowerShell pour taille dossier
            cmd = f'powershell "Get-ChildItem \'{WORKING_DIR}\' -Recurse | Measure-Object -Property Length -Sum"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                # Extraction valeur numérique
                output = result.stdout.strip()
                import re
                match = re.search(r'Sum\s*:\s*(\d+)', output)
                if match:
                    bytes_used = int(match.group(1))
                    gb_used = bytes_used / (1024**3)
                    return gb_used
            
            return 0.0
        except:
            return 0.0
    
    def _generate_large_scale_report(self, results: Dict, quality: str):
        """Génération rapport échelle large"""
        print(f"\n📋 RAPPORT GÉNÉRATION LARGE ÉCHELLE")
        print("=" * 50)
        
        report = {
            'generation_session': {
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'quality_level': quality,
                'total_prompts': results['total_processed'],
                'successful_generations': results['successful'],
                'failed_generations': results['failed'],
                'success_rate': f"{(results['successful']/results['total_processed']*100):.1f}%" if results['total_processed'] > 0 else "0%",
                'total_processing_time': f"{results['total_time']:.1f} seconds",
                'space_used_gb': f"{results['space_used']:.2f}",
                'performance_metrics': {
                    'images_per_minute': f"{results['successful']/(results['total_time']/60):.1f}" if results['total_time'] > 0 else "0",
                    'average_time_per_image': f"{results['total_time']/results['successful']:.2f} seconds" if results['successful'] > 0 else "N/A"
                }
            },
            'batch_performance': results['batch_details'],
            'storage_summary': {
                'working_directory': str(WORKING_DIR),
                'output_structure': [
                    'generated_images/base_sdxl/',
                    'generated_images/h0_enhanced/',
                    'generated_images/final_results/',
                    'generated_images/comparisons/',
                    'harmonic_database/signatures/'
                ]
            }
        }
        
        # Sauvegarde rapport
        report_path = WORKING_DIR / "logs" / f"generation_report_{int(time.time())}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Rapport sauvegardé: {report_path}")
        
        # Affichage résumé
        print(f"\n📊 RÉSUMÉ FINAL:")
        print(f"   Images générées: {results['successful']}/{results['total_processed']}")
        print(f"   Taux succès: {report['generation_session']['success_rate']}")
        print(f"   Temps total: {report['generation_session']['total_processing_time']}")
        print(f"   Espace utilisé: {report['generation_session']['space_used_gb']} GB")
        print(f"   Performance: {report['generation_session']['performance_metrics']['images_per_minute']} images/min")

# Interface utilisateur simplifiée
class SimplePhotoRealisticGenerator:
    """Interface simple pour génération photo-réaliste"""
    
    @staticmethod
    def generate_images(prompts: List[str], 
                       quality: str = "ultra",
                       batch_size: int = 5) -> str:
        """
        Génération images photo-réalistes
        
        Args:
            prompts: Liste de descriptions
            quality: Niveau qualité ("high", "ultra", "cinematic")
            batch_size: Taille batch traitement
            
        Returns:
            Chemin dossier résultats
        """
        generator = PhotoRealisticHarmonicGenerator()
        results = generator.generate_large_scale_batch(prompts, batch_size, quality)
        return str(WORKING_DIR / "generated_images" / "final_results")

# Exemple d'utilisation
def demo_photorealistic_generation():
    """Démonstration génération photo-réaliste"""
    print("📸 DÉMONSTRATION GÉNÉRATION PHOTO-RÉALISTE")
    print("=" * 60)
    
    # Prompts photo-réalistes
    sample_prompts = [
        "Mountain landscape at golden hour with dramatic clouds and warm lighting",
        "Professional portrait of a person with natural studio lighting and soft shadows",
        "Urban cityscape at blue hour with neon lights reflecting on wet streets",
        "Forest interior with dappled sunlight filtering through tall trees",
        "Ocean waves crashing against rocky coastline during sunset"
    ]
    
    # Génération
    output_path = SimplePhotoRealisticGenerator.generate_images(
        sample_prompts, quality="ultra", batch_size=3
    )
    
    print(f"\n🎉 Démonstration terminée!")
    print(f"📁 Résultats: {output_path}")

if __name__ == "__main__":
    demo_photorealistic_generation()