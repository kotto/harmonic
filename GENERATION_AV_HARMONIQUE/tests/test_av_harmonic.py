#!/usr/bin/env python3
"""
Tests de validation du moteur de génération AV harmonique.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from engine.harmonic_av_core import (
    HarmonicAVGenerator, HarmonicPromptAnalyzer,
    PHI, ALPHA, PHI_INV, mittag_leffler, compute_resonance,
    RESONANCE_HIGH, RESONANCE_MEDIUM, RESONANCE_LOW
)


def test_analyzer():
    """Test de l'analyseur de prompts enrichi AV."""
    print("\n1️⃣ Test : Analyseur de prompts enrichi AV")
    analyzer = HarmonicPromptAnalyzer()
    
    tests = [
        ("Un coucher de soleil sur l'océan calme", 'nature', 'calme'),
        ("Une ville dynamique la nuit", 'urbain', 'dynamique'),
        ("Un rêve abstrait et coloré", 'abstrait', 'neutre'),
        ("Calculez 15% de 340", 'neutre', 'neutre'),
    ]
    
    passed = 0
    for prompt, expected_scene, expected_mood in tests:
        result = analyzer.analyze(prompt)
        scene_ok = result['scene_type'] == expected_scene
        mood_ok = result['mood'] == expected_mood if expected_mood != 'neutre' else True
        
        if scene_ok and mood_ok and len(result['signature_7d']) == 7:
            passed += 1
            status = '✅'
        else:
            status = '❌'
        
        print(f"  {status} {prompt[:40]:40s} → "
              f"scène={result['scene_type']:8s} "
              f"humeur={result['mood']:10s} "
              f"mvt={result['motion_level']:.2f}")
    
    print(f"  → {passed}/{len(tests)} tests passés")
    return passed == len(tests)


def test_audio_generation():
    """Test de la génération audio."""
    print("\n2️⃣ Test : Génération audio")
    gen = HarmonicAVGenerator()
    analyzer = HarmonicPromptAnalyzer()
    
    analysis = analyzer.analyze("Un bruit de vagues douces")
    audio = gen.generate_audio(analysis, duration=2.0, sample_rate=44100)
    
    checks = []
    checks.append(len(audio['samples']) == 2 * 44100)  # 2 secondes
    checks.append(abs(max(audio['samples'])) > 0.001)    # Non nul
    checks.append(abs(min(audio['samples'])) < 1.0)      # Normalisé
    checks.append(audio['sample_rate'] == 44100)
    
    for i, c in enumerate(checks):
        print(f"  {'✅' if c else '❌'} Check {i+1}")
    
    all_ok = all(checks)
    print(f"  → {'✅ Passé' if all_ok else '❌ Échoué'}")
    return all_ok


def test_video_generation():
    """Test de la génération vidéo."""
    print("\n3️⃣ Test : Génération vidéo")
    gen = HarmonicAVGenerator()
    analyzer = HarmonicPromptAnalyzer()
    
    analysis = analyzer.analyze("Un paysage de montagne")
    video = gen.generate_video(analysis, duration=2.0, fps=10, resolution=(32, 18))
    
    checks = []
    checks.append(len(video['frames']) == 20)  # 2s × 10fps
    checks.append(len(video['frames'][0]) == 18)  # height
    checks.append(len(video['frames'][0][0]) == 32)  # width
    checks.append(video['resonance'] > 0)
    
    # Vérifier que les couleurs sont valides (0-255)
    r, g, b = video['frames'][0][0][0]
    checks.append(0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255)
    
    for i, c in enumerate(checks):
        print(f"  {'✅' if c else '❌'} Check {i+1}")
    
    all_ok = all(checks)
    print(f"  → {'✅ Passé' if all_ok else '❌ Échoué'}")
    return all_ok


def test_av_sync():
    """Test de la synchronisation AV."""
    print("\n4️⃣ Test : Synchronisation AV")
    gen = HarmonicAVGenerator()
    analyzer = HarmonicPromptAnalyzer()
    
    analysis = analyzer.analyze("Une scène calme et paisible")
    audio = gen.generate_audio(analysis, duration=1.0, sample_rate=22050)
    video = gen.generate_video(analysis, duration=1.0, fps=10, resolution=(32, 18))
    
    sync = gen.compute_av_sync(audio, video)
    
    print(f"  Qualité de sync : {sync:.2%}")
    ok = sync > 0.3  # Au moins 30% de sync
    print(f"  → {'✅ Passé' if ok else '❌ Échoué'} (seuil > 30%)")
    return ok


def test_pipeline_complete():
    """Test du pipeline complet."""
    print("\n5️⃣ Test : Pipeline complet")
    gen = HarmonicAVGenerator()
    
    result = gen.generate_from_prompt(
        prompt="Test rapide",
        duration_seconds=1.0,
        fps=5,
        sample_rate=11025,
        resolution=(16, 9)
    )
    
    checks = []
    checks.append(len(result.audio_samples) > 0)
    checks.append(len(result.video_frames) > 0)
    checks.append(result.resonance_audio > 0)
    checks.append(result.resonance_video > 0)
    checks.append(result.processing_time_ms > 0)
    checks.append(len(result.scene_type) > 0)
    
    for i, c in enumerate(checks):
        print(f"  {'✅' if c else '❌'} Check {i+1}")
    
    all_ok = all(checks)
    print(f"  → {'✅ Passé' if all_ok else '❌ Échoué'}")
    return all_ok


def run_all_tests():
    """Exécute tous les tests."""
    print("=" * 60)
    print("TESTS DU MOTEUR AV HARMONIQUE v1.0")
    print("=" * 60)
    
    tests = [
        ("Analyseur de prompts", test_analyzer()),
        ("Génération audio", test_audio_generation()),
        ("Génération vidéo", test_video_generation()),
        ("Sync AV", test_av_sync()),
        ("Pipeline complet", test_pipeline_complete()),
    ]
    
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in tests if ok)
    total = len(tests)
    print(f"RÉSULTAT : {passed}/{total} tests passés")
    
    for name, ok in tests:
        print(f"  {'✅' if ok else '❌'} {name}")
    
    print("=" * 60)
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)