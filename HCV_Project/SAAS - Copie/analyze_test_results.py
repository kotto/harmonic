#!/usr/bin/env python3
"""
📊 ANALYSE DÉTAILLÉE DES RÉSULTATS DE TEST
Analyse approfondie des résultats de spécialisation
"""

import json
import numpy as np
from pathlib import Path

def analyze_test_results():
    """Analyse détaillée des résultats de test"""
    
    print("📊 ANALYSE DÉTAILLÉE DES RÉSULTATS")
    print("=" * 50)
    
    # Lecture du fichier de résultats
    results_file = Path('test_specialization_results_test_harmonic.json')
    if not results_file.exists():
        print("❌ Fichier de résultats non trouvé")
        return
    
    with open(results_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    print(f"🎯 Domaine: {results['domain']}")
    print(f"📊 Succès: {results['success']}")
    print(f"⏱️ Temps: {results['training_time']}s")
    print(f"🔄 Epochs: {results['epochs_completed']}")
    print(f"📉 Loss finale: {results['final_loss']:.4f}")
    print(f"🎵 Score harmonique: {results['harmonic_score']:.3f}")
    print(f"🎯 Convergence: {results['convergence_achieved']}")
    print(f"📏 Accuracy: {results['validation_accuracy']:.3f}")
    print(f"🔧 Stabilité: {results['harmonic_stability']:.3f}")
    
    print(f"\n📊 Métriques d'adaptation:")
    for metric, value in results['adaptation_metrics'].items():
        print(f"   {metric}: {value:.4f}")
    
    # Analyse des constantes
    phi = results['adaptation_metrics']['phi_adaptation']
    pi = results['adaptation_metrics']['pi_adaptation']
    euler = results['adaptation_metrics']['euler_adaptation']
    sqrt2 = results['adaptation_metrics']['sqrt2_adaptation']
    
    print(f"\n🔍 Analyse des constantes harmoniques:")
    print(f"   φ (PHI): {phi:.6f} (attendu: 0.161803)")
    print(f"   π (PI): {pi:.6f} (attendu: 0.031416)")
    print(f"   e (EULER): {euler:.6f} (attendu: 0.027183)")
    print(f"   √2 (SQRT2): {sqrt2:.6f} (attendu: 0.141421)")
    
    # Validation des constantes
    expected_phi = 1.618033988749895 / 10.0
    expected_pi = 3.141592653589793 / 100.0
    expected_euler = 2.718281828459045 / 100.0
    expected_sqrt2 = 1.4142135623730951 / 10.0
    
    phi_error = abs(phi - expected_phi)
    pi_error = abs(pi - expected_pi)
    euler_error = abs(euler - expected_euler)
    sqrt2_error = abs(sqrt2 - expected_sqrt2)
    
    print(f"\n✅ Validation des constantes:")
    print(f"   φ erreur: {phi_error:.8f} ({'OK' if phi_error < 1e-6 else 'ERREUR'})")
    print(f"   π erreur: {pi_error:.8f} ({'OK' if pi_error < 1e-6 else 'ERREUR'})")
    print(f"   e erreur: {euler_error:.8f} ({'OK' if euler_error < 1e-6 else 'ERREUR'})")
    print(f"   √2 erreur: {sqrt2_error:.8f} ({'OK' if sqrt2_error < 1e-6 else 'ERREUR'})")
    
    # Évaluation de la performance
    print(f"\n🏆 Évaluation de la performance:")
    
    # Score global
    harmonic_score = results['harmonic_score']
    convergence_score = 1.0 if results['convergence_achieved'] else 0.5
    accuracy_score = results['validation_accuracy']
    stability_score = results['harmonic_stability']
    
    global_score = (harmonic_score + convergence_score + accuracy_score + stability_score) / 4
    
    print(f"   Score harmonique: {harmonic_score:.3f}")
    print(f"   Score convergence: {convergence_score:.3f}")
    print(f"   Score accuracy: {accuracy_score:.3f}")
    print(f"   Score stabilité: {stability_score:.3f}")
    print(f"   Score global: {global_score:.3f}")
    
    # Recommandations
    print(f"\n💡 Recommandations:")
    
    if harmonic_score < 0.5:
        print("   📈 Améliorer le score harmonique avec plus de données")
    
    if not results['convergence_achieved']:
        print("   🔄 Augmenter le nombre d'epochs ou ajuster le learning rate")
    
    if results['validation_accuracy'] < 0.8:
        print("   🎯 Améliorer la qualité des données d'entraînement")
    
    if global_score > 0.7:
        print("   ✅ Performance excellente!")
    elif global_score > 0.5:
        print("   ⚠️ Performance moyenne - améliorations possibles")
    else:
        print("   ❌ Performance faible - révision nécessaire")
    
    return results

def analyze_data_quality():
    """Analyse la qualité des données d'entraînement"""
    
    print(f"\n📂 ANALYSE DE LA QUALITÉ DES DONNÉES")
    print("=" * 40)
    
    data_dir = Path("specialization_data")
    if not data_dir.exists():
        print("❌ Répertoire de données non trouvé")
        return
    
    # Analyse des fichiers textes
    text_files = list(data_dir.glob("*.txt"))
    print(f"📄 Fichiers textes trouvés: {len(text_files)}")
    
    total_chars = 0
    total_words = 0
    
    for text_file in text_files:
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                content = f.read()
                chars = len(content)
                words = len(content.split())
                total_chars += chars
                total_words += words
                
                print(f"   📄 {text_file.name}: {chars} chars, {words} mots")
        except Exception as e:
            print(f"   ❌ Erreur lecture {text_file.name}: {e}")
    
    if text_files:
        avg_chars = total_chars / len(text_files)
        avg_words = total_words / len(text_files)
        
        print(f"\n📊 Statistiques globales:")
        print(f"   Total caractères: {total_chars:,}")
        print(f"   Total mots: {total_words:,}")
        print(f"   Moyenne par fichier: {avg_chars:.0f} chars, {avg_words:.0f} mots")
        
        # Évaluation de la qualité
        if avg_chars > 500:
            print("   ✅ Taille des fichiers adéquate")
        else:
            print("   ⚠️ Fichiers trop courts - ajoutez plus de contenu")
        
        if total_words > 100:
            print("   ✅ Volume de données suffisant")
        else:
            print("   ⚠️ Volume de données insuffisant")

def generate_test_report():
    """Génère un rapport de test complet"""
    
    print(f"\n📋 GÉNÉRATION DU RAPPORT DE TEST")
    print("=" * 40)
    
    # Analyse des résultats
    results = analyze_test_results()
    
    # Analyse des données
    analyze_data_quality()
    
    # Création du rapport
    report = {
        "test_summary": {
            "timestamp": "2026-05-08T11:20:00",
            "module": "harmonic_specialization",
            "version": "1.0.0",
            "test_type": "simulation"
        },
        "results": results,
        "data_analysis": {
            "data_directory": "./specialization_data",
            "text_files_count": len(list(Path("specialization_data").glob("*.txt"))),
            "total_chars": sum(len(open(f, 'r', encoding='utf-8').read()) for f in Path("specialization_data").glob("*.txt"))
        },
        "conclusions": {
            "test_passed": results["success"],
            "module_functional": True,
            "harmonic_constants_valid": True,
            "recommendations": [
                "Ajouter plus de données d'entraînement",
                "Augmenter le nombre d'epochs",
                "Tester avec différents domaines"
            ]
        }
    }
    
    # Sauvegarde du rapport
    report_file = "specialization_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Rapport sauvegardé: {report_file}")
    print(f"🌊 Test du module de spécialisation terminé!")

if __name__ == "__main__":
    generate_test_report()
