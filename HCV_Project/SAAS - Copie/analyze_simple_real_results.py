#!/usr/bin/env python3
"""
📊 ANALYSE DES RÉSULTATS SIMPLES RÉELS
Analyse approfondie des résultats de traitement batch simple RÉEL
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import matplotlib.pyplot as plt

def analyze_simple_real_results():
    """Analyse complète des résultats simples RÉELS"""
    
    print("📊 ANALYSE DES RÉSULTATS SIMPLES RÉELS")
    print("=" * 60)
    
    # Lecture du rapport simple RÉEL
    report_file = Path("simple_real_batch_report.json")
    if not report_file.exists():
        print("❌ Rapport simple RÉEL non trouvé")
        return
    
    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    # Analyse du résumé simple RÉEL
    summary = report['simple_real_summary']
    print(f"📋 RÉSUMÉ SIMPLE RÉEL:")
    print(f"   📅 Date: {summary['timestamp']}")
    print(f"   🌊 Mode: {summary['mode']}")
    print(f"   🏢 Domaines: {summary['successful_domains']}/{summary['total_domains']}")
    print(f"   📁 Fichiers: {summary['processed_files']}/{summary['total_files']}")
    print(f"   📊 Taux de traitement: {summary['processing_rate']:.1%}")
    print(f"   💾 Taille totale: {summary['total_size']:,} bytes")
    print(f"   🎵 Score harmonique moyen: {summary['avg_harmonic_score']:.3f}")
    print(f"   📋 Taux de succès: {summary['success_rate']:.1%}")
    
    # Analyse par domaine simple RÉEL
    print(f"\n📊 ANALYSE PAR DOMAINE SIMPLE RÉEL:")
    print("-" * 50)
    
    domain_results = report['domain_results']
    
    # Création d'un DataFrame simple RÉEL
    domain_data = []
    for domain_name, result in domain_results.items():
        domain_data.append({
            'Domaine': domain_name,
            'Succès': result['success'],
            'Fichiers': result['processed_files'],
            'Taille (KB)': result['total_size'] / 1024,
            'Score Harmonique': result['harmonic_score'],
            'Temps (s)': result['processing_time']
        })
    
    df = pd.DataFrame(domain_data)
    
    # Tri par score harmonique simple RÉEL
    df_sorted = df.sort_values('Score Harmonique', ascending=False)
    
    print(df_sorted.to_string(index=False, float_format='%.3f'))
    
    # Analyse des métriques simples RÉELLES
    print(f"\n📈 MÉTRIQUES DÉTAILLÉES SIMPLES RÉELLES:")
    print("-" * 40)
    
    # Statistiques des scores harmoniques simples RÉELS
    harmonic_scores = df['Score Harmonique']
    print(f"🎵 Scores Harmoniques Simples RÉELS:")
    print(f"   Moyenne: {harmonic_scores.mean():.3f}")
    print(f"   Médiane: {harmonic_scores.median():.3f}")
    print(f"   Écart-type: {harmonic_scores.std():.3f}")
    print(f"   Min: {harmonic_scores.min():.3f}")
    print(f"   Max: {harmonic_scores.max():.3f}")
    
    # Analyse de la taille simple RÉELLE
    file_sizes = df['Taille (KB)']
    print(f"\n💾 Taille des Fichiers Simples RÉELS:")
    print(f"   Moyenne: {file_sizes.mean():.1f} KB")
    print(f"   Médiane: {file_sizes.median():.1f} KB")
    print(f"   Total: {file_sizes.sum():.1f} KB")
    
    # Performance simple RÉELLE par domaine
    print(f"\n🏆 CLASSEMENT DES DOMAINES SIMPLES RÉELS:")
    print("-" * 40)
    
    for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
        status = "✅" if row['Succès'] else "❌"
        print(f"   {i}. {row['Domaine']} - {status}")
        print(f"      Score: {row['Score Harmonique']:.3f}")
        print(f"      Fichiers: {row['Fichiers']}")
        print(f"      Taille: {row['Taille (KB)']:.1f} KB")
    
    # Analyse de la qualité simple RÉELLE
    print(f"\n🔍 ANALYSE DE LA QUALITÉ SIMPLE RÉELLE:")
    print("-" * 40)
    
    # Domaines avec score > 0.4 simple RÉEL
    high_score_domains = df[df['Score Harmonique'] > 0.4]
    print(f"📊 Domaines avec score > 0.4: {len(high_score_domains)}")
    if len(high_score_domains) > 0:
        print(f"   {', '.join(high_score_domains['Domaine'].tolist())}")
    
    # Domaines avec score < 0.35 simple RÉEL
    low_score_domains = df[df['Score Harmonique'] < 0.35]
    print(f"⚠️ Domaines avec score < 0.35: {len(low_score_domains)}")
    if len(low_score_domains) > 0:
        print(f"   {', '.join(low_score_domains['Domaine'].tolist())}")
    
    # Recommandations simples RÉELLES
    print(f"\n💡 RECOMMANDATIONS SIMPLES RÉELLES:")
    print("-" * 30)
    
    if harmonic_scores.mean() < 0.4:
        print("📈 Améliorer globalement les scores harmoniques simples RÉELS")
        print("   - Ajouter plus de contenu structuré")
        print("   - Optimiser les poids harmoniques simples")
    
    if len(low_score_domains) > 0:
        print(f"🔧 Améliorer les domaines: {', '.join(low_score_domains['Domaine'].tolist())}")
        print("   - Enrichir le contenu")
        print("   - Réviser la structure simple")
    
    if harmonic_scores.std() > 0.05:
        print("⚖️ Standardiser les scores simples entre domaines")
        print("   - Harmoniser les poids simples")
        print("   - Unifier les formats simples")
    
    # Sauvegarde de l'analyse simple RÉELLE
    analysis_results = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'global_summary': summary,
        'domain_analysis': df_sorted.to_dict('records'),
        'statistics': {
            'harmonic_score_mean': float(harmonic_scores.mean()),
            'harmonic_score_median': float(harmonic_scores.median()),
            'harmonic_score_std': float(harmonic_scores.std()),
            'total_size_kb': float(file_sizes.sum()),
            'high_score_domains': len(high_score_domains),
            'low_score_domains': len(low_score_domains)
        },
        'recommendations': [
            "Améliorer les scores harmoniques simples globaux",
            "Standardiser les formats simples entre domaines",
            "Enrichir le contenu des domaines faibles simples"
        ],
        'real_mode': True,
        'simple_version': True
    }
    
    analysis_file = "simple_real_analysis_results.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Analyse simple RÉELLE sauvegardée: {analysis_file}")
    
    return analysis_results

def analyze_detailed_domain_simple_real(domain_name: str):
    """Analyse détaillée simple RÉELLE d'un domaine spécifique"""
    
    print(f"\n🔍 ANALYSE DÉTAILLÉE SIMPLE RÉELLE - DOMAINE: {domain_name.upper()}")
    print("=" * 70)
    
    # Lecture des fichiers simples RÉELS du domaine
    domain_dir = Path("simple_real_output") / domain_name
    if not domain_dir.exists():
        print(f"❌ Répertoire du domaine {domain_name} non trouvé")
        return
    
    # Lecture du manifeste simple RÉEL
    manifest_file = domain_dir / f"{domain_name}_simple_manifest.json"
    if manifest_file.exists():
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        print(f"📋 MANIFESTE SIMPLE RÉEL DU DOMAINE:")
        print(f"   Mode: {manifest.get('mode', 'N/A')}")
        print(f"   Version simple: {manifest.get('simple_version', 'N/A')}")
        print(f"   Fichiers: {manifest['total_items']}")
        print(f"   Date: {manifest['processing_date']}")
    
    # Lecture des métadonnées simples RÉELLES
    metadata_file = domain_dir / f"{domain_name}_simple_real.csv"
    if metadata_file.exists():
        df = pd.read_csv(metadata_file)
        
        print(f"\n📊 MÉTADONNÉES DÉTAILLÉES SIMPLES RÉELLES:")
        print(f"   Fichiers: {len(df)}")
        
        # Analyse des scores harmoniques simples RÉELS
        if 'harmonic_score' in df.columns:
            scores = df['harmonic_score']
            print(f"   Score harmonique moyen: {scores.mean():.3f}")
            print(f"   Score harmonique max: {scores.max():.3f}")
            print(f"   Score harmonique min: {scores.min():.3f}")
            
            # Meilleurs fichiers simples RÉELS
            best_files = df.nlargest(3, 'harmonic_score')
            print(f"\n🏆 MEILLEURS FICHIERS SIMPLES RÉELS:")
            for _, row in best_files.iterrows():
                print(f"   📄 {row['file_name']}: {row['harmonic_score']:.3f}")
        
        # Analyse des tailles simples RÉELLES
        if 'file_size' in df.columns:
            sizes = df['file_size']
            print(f"\n💾 ANALYSE DES TAILLES SIMPLES RÉELLES:")
            print(f"   Taille moyenne: {sizes.mean():.0f} bytes")
            print(f"   Taille totale: {sizes.sum():.0f} bytes")
            print(f"   Plus grand: {sizes.max():.0f} bytes")
            print(f"   Plus petit: {sizes.min():.0f} bytes")
        
        # Analyse des longueurs de contenu simples RÉELLES
        if 'content_length' in df.columns:
            lengths = df['content_length']
            print(f"\n📏 ANALYSE DES LONGUEURS SIMPLES RÉELLES:")
            print(f"   Longueur moyenne: {lengths.mean():.0f} chars")
            print(f"   Longueur totale: {lengths.sum():.0f} chars")
            print(f"   Plus long: {lengths.max():.0f} chars")
            print(f"   Plus court: {lengths.min():.0f} chars")

def create_simple_real_visualization():
    """Crée des visualisations simples RÉELLES des résultats"""
    
    print(f"\n📊 CRÉATION DES VISUALISATIONS SIMPLES RÉELLES")
    print("=" * 50)
    
    # Lecture des résultats simples RÉELS
    report_file = Path("simple_real_batch_report.json")
    if not report_file.exists():
        print("❌ Rapport simple RÉEL non trouvé")
        return
    
    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    domain_results = report['domain_results']
    
    # Préparation des données simples RÉELLES
    domains = []
    harmonic_scores = []
    file_counts = []
    sizes = []
    
    for domain_name, result in domain_results.items():
        domains.append(domain_name)
        harmonic_scores.append(result['harmonic_score'])
        file_counts.append(result['processed_files'])
        sizes.append(result['total_size'] / 1024)  # KB
    
    # Création des graphiques simples RÉELS
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Graphique 1: Scores harmoniques simples RÉELS
    ax1.bar(domains, harmonic_scores, color='lightblue', alpha=0.7)
    ax1.set_title('Scores Harmoniques Simples RÉELS par Domaine')
    ax1.set_ylabel('Score Harmonique Simple RÉEL')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # Graphique 2: Nombre de fichiers simples RÉELS
    ax2.bar(domains, file_counts, color='lightgreen', alpha=0.7)
    ax2.set_title('Nombre de Fichiers Simples RÉELS par Domaine')
    ax2.set_ylabel('Nombre de Fichiers Simple RÉEL')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)
    
    # Graphique 3: Taille des domaines simples RÉELS
    ax3.bar(domains, sizes, color='orange', alpha=0.7)
    ax3.set_title('Taille des Domaines Simples RÉELS (KB)')
    ax3.set_ylabel('Taille Simple RÉEL (KB)')
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(True, alpha=0.3)
    
    # Graphique 4: Scatter plot simple RÉEL
    ax4.scatter(harmonic_scores, sizes, alpha=0.7, s=100, c='red')
    ax4.set_xlabel('Score Harmonique Simple RÉEL')
    ax4.set_ylabel('Taille Simple RÉEL (KB)')
    ax4.set_title('Relation Score Harmonique Simple RÉEL vs Taille')
    ax4.grid(True, alpha=0.3)
    
    # Ajout des labels sur le scatter plot simple RÉEL
    for i, domain in enumerate(domains):
        ax4.annotate(domain, (harmonic_scores[i], sizes[i]), 
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    plt.tight_layout()
    
    # Sauvegarde du graphique simple RÉEL
    chart_file = "simple_real_results_visualization.png"
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"📊 Visualisation simple RÉELLE sauvegardée: {chart_file}")
    return chart_file

def main():
    """Fonction principale simple RÉELLE"""
    
    # Analyse globale simple RÉELLE
    analysis_results = analyze_simple_real_results()
    
    # Analyse détaillée des meilleurs domaines simples RÉELS
    report_file = Path("simple_real_batch_report.json")
    if report_file.exists():
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        domain_results = report['domain_results']
        
        # Top 3 domaines simples RÉELS par score harmonique
        sorted_domains = sorted(domain_results.items(), 
                            key=lambda x: x[1]['harmonic_score'], 
                            reverse=True)
        
        print(f"\n🏆 ANALYSE DÉTAILLÉE DES TOP 3 DOMAINES SIMPLES RÉELS:")
        for i, (domain_name, result) in enumerate(sorted_domains[:3], 1):
            analyze_detailed_domain_simple_real(domain_name)
    
    # Création des visualisations simples RÉELLES
    try:
        create_simple_real_visualization()
    except Exception as e:
        print(f"⚠️ Erreur création visualisation simple RÉELLE: {str(e)}")
    
    print(f"\n🌊 Analyse batch simple RÉEL terminée!")

if __name__ == "__main__":
    main()
