#!/usr/bin/env python3
"""
📊 ANALYSE DES RÉSULTATS BATCH
Analyse approfondie des résultats de traitement batch
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import matplotlib.pyplot as plt

def analyze_batch_results():
    """Analyse complète des résultats batch"""
    
    print("📊 ANALYSE DES RÉSULTATS BATCH")
    print("=" * 50)
    
    # Lecture du rapport global
    report_file = Path("batch_processing_global_report.json")
    if not report_file.exists():
        print("❌ Rapport batch non trouvé")
        return
    
    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    # Analyse du résumé
    summary = report['processing_summary']
    print(f"📋 RÉSUMÉ GLOBAL:")
    print(f"   📅 Date: {summary['timestamp']}")
    print(f"   🏢 Domaines: {summary['successful_domains']}/{summary['total_domains']}")
    print(f"   📁 Fichiers: {summary['processed_files']}/{summary['total_files']}")
    print(f"   📊 Taux de traitement: {summary['processing_rate']:.1%}")
    print(f"   💾 Taille totale: {summary['total_size']:,} bytes")
    print(f"   🎵 Score harmonique moyen: {summary['avg_harmonic_score']:.3f}")
    
    # Analyse par domaine
    print(f"\n📊 ANALYSE PAR DOMAINE:")
    print("-" * 40)
    
    domain_results = report['domain_results']
    
    # Création d'un DataFrame pour l'analyse
    domain_data = []
    for domain_name, result in domain_results.items():
        domain_data.append({
            'Domaine': domain_name,
            'Succès': result['success'],
            'Fichiers': result['processed_files'],
            'Taille (KB)': result['total_size'] / 1024,
            'Score Harmonique': result['harmonic_score'],
            'Temps (s)': result['processing_time'],
            'Validation': result['validation_accuracy']
        })
    
    df = pd.DataFrame(domain_data)
    
    # Tri par score harmonique
    df_sorted = df.sort_values('Score Harmonique', ascending=False)
    
    print(df_sorted.to_string(index=False, float_format='%.3f'))
    
    # Analyse des métriques
    print(f"\n📈 MÉTRIQUES DÉTAILLÉES:")
    print("-" * 30)
    
    # Statistiques des scores harmoniques
    harmonic_scores = df['Score Harmonique']
    print(f"🎵 Scores Harmoniques:")
    print(f"   Moyenne: {harmonic_scores.mean():.3f}")
    print(f"   Médiane: {harmonic_scores.median():.3f}")
    print(f"   Écart-type: {harmonic_scores.std():.3f}")
    print(f"   Min: {harmonic_scores.min():.3f}")
    print(f"   Max: {harmonic_scores.max():.3f}")
    
    # Analyse de la taille
    file_sizes = df['Taille (KB)']
    print(f"\n💾 Taille des Fichiers:")
    print(f"   Moyenne: {file_sizes.mean():.1f} KB")
    print(f"   Médiane: {file_sizes.median():.1f} KB")
    print(f"   Total: {file_sizes.sum():.1f} KB")
    
    # Performance par domaine
    print(f"\n🏆 CLASSEMENT DES DOMAINES:")
    print("-" * 30)
    
    # Classement par score harmonique
    for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
        status = "✅" if row['Succès'] else "❌"
        print(f"   {i}. {row['Domaine']} - {status}")
        print(f"      Score: {row['Score Harmonique']:.3f}")
        print(f"      Fichiers: {row['Fichiers']}")
        print(f"      Taille: {row['Taille (KB)']:.1f} KB")
    
    # Analyse de la qualité
    print(f"\n🔍 ANALYSE DE LA QUALITÉ:")
    print("-" * 30)
    
    # Domaines avec score > 0.5
    high_score_domains = df[df['Score Harmonique'] > 0.5]
    print(f"📊 Domaines avec score > 0.5: {len(high_score_domains)}")
    if len(high_score_domains) > 0:
        print(f"   {', '.join(high_score_domains['Domaine'].tolist())}")
    
    # Domaines avec score < 0.3
    low_score_domains = df[df['Score Harmonique'] < 0.3]
    print(f"⚠️ Domaines avec score < 0.3: {len(low_score_domains)}")
    if len(low_score_domains) > 0:
        print(f"   {', '.join(low_score_domains['Domaine'].tolist())}")
    
    # Recommandations
    print(f"\n💡 RECOMMANDATIONS:")
    print("-" * 20)
    
    if harmonic_scores.mean() < 0.4:
        print("📈 Améliorer globalement les scores harmoniques")
        print("   - Ajouter plus de contenu structuré")
        print("   - Optimiser les poids harmoniques")
    
    if len(low_score_domains) > 0:
        print(f"🔧 Améliorer les domaines: {', '.join(low_score_domains['Domaine'].tolist())}")
        print("   - Enrichir le contenu")
        print("   - Réviser la structure")
    
    if harmonic_scores.std() > 0.1:
        print("⚖️ Standardiser les scores entre domaines")
        print("   - Harmoniser les poids")
        print("   - Unifier les formats")
    
    # Sauvegarde de l'analyse
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
            "Améliorer les scores harmoniques globaux",
            "Standardiser les formats entre domaines",
            "Enrichir le contenu des domaines faibles"
        ]
    }
    
    analysis_file = "batch_analysis_results.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Analyse sauvegardée: {analysis_file}")
    
    return analysis_results

def analyze_domain_details(domain_name: str):
    """Analyse détaillée d'un domaine spécifique"""
    
    print(f"\n🔍 ANALYSE DÉTAILLÉE - DOMAINE: {domain_name.upper()}")
    print("=" * 60)
    
    # Lecture des fichiers du domaine
    domain_dir = Path("batch_output") / domain_name
    if not domain_dir.exists():
        print(f"❌ Répertoire du domaine {domain_name} non trouvé")
        return
    
    # Lecture du manifeste
    manifest_file = domain_dir / f"{domain_name}_manifest.json"
    if manifest_file.exists():
        with open(manifest_file, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        print(f"📋 MANIFESTE DU DOMAINE:")
        print(f"   Type: {manifest['domain_type']}")
        print(f"   Description: {manifest['config']['description']}")
        print(f"   Tags: {', '.join(manifest['config']['tags'])}")
        print(f"   Version: {manifest['version']}")
        print(f"   Fichiers: {manifest['total_items']}")
    
    # Lecture des métadonnées
    metadata_file = domain_dir / f"{domain_name}_metadata.csv"
    if metadata_file.exists():
        df = pd.read_csv(metadata_file)
        
        print(f"\n📊 MÉTADONNÉES DÉTAILLÉES:")
        print(f"   Fichiers: {len(df)}")
        
        # Analyse des scores harmoniques
        if 'harmonic_score' in df.columns:
            scores = df['harmonic_score']
            print(f"   Score harmonique moyen: {scores.mean():.3f}")
            print(f"   Score harmonique max: {scores.max():.3f}")
            print(f"   Score harmonique min: {scores.min():.3f}")
            
            # Meilleurs fichiers
            best_files = df.nlargest(3, 'harmonic_score')
            print(f"\n🏆 MEILLEURS FICHIERS:")
            for _, row in best_files.iterrows():
                print(f"   📄 {row['file_name']}: {row['harmonic_score']:.3f}")
        
        # Analyse des tailles
        if 'file_size' in df.columns:
            sizes = df['file_size']
            print(f"\n💾 ANALYSE DES TAILLES:")
            print(f"   Taille moyenne: {sizes.mean():.0f} bytes")
            print(f"   Taille totale: {sizes.sum():.0f} bytes")
            print(f"   Plus grand: {sizes.max():.0f} bytes")
            print(f"   Plus petit: {sizes.min():.0f} bytes")

def create_visualization():
    """Crée des visualisations des résultats"""
    
    print(f"\n📊 CRÉATION DES VISUALISATIONS")
    print("=" * 40)
    
    # Lecture des résultats
    report_file = Path("batch_processing_global_report.json")
    if not report_file.exists():
        print("❌ Rapport batch non trouvé")
        return
    
    with open(report_file, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    domain_results = report['domain_results']
    
    # Préparation des données
    domains = []
    harmonic_scores = []
    file_counts = []
    sizes = []
    
    for domain_name, result in domain_results.items():
        domains.append(domain_name)
        harmonic_scores.append(result['harmonic_score'])
        file_counts.append(result['processed_files'])
        sizes.append(result['total_size'] / 1024)  # KB
    
    # Création des graphiques
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Graphique 1: Scores harmoniques
    ax1.bar(domains, harmonic_scores, color='skyblue', alpha=0.7)
    ax1.set_title('Scores Harmoniques par Domaine')
    ax1.set_ylabel('Score Harmonique')
    ax1.tick_params(axis='x', rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # Graphique 2: Nombre de fichiers
    ax2.bar(domains, file_counts, color='lightgreen', alpha=0.7)
    ax2.set_title('Nombre de Fichiers par Domaine')
    ax2.set_ylabel('Nombre de Fichiers')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)
    
    # Graphique 3: Taille des domaines
    ax3.bar(domains, sizes, color='orange', alpha=0.7)
    ax3.set_title('Taille des Domaines (KB)')
    ax3.set_ylabel('Taille (KB)')
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(True, alpha=0.3)
    
    # Graphique 4: Scatter plot
    ax4.scatter(harmonic_scores, sizes, alpha=0.7, s=100, c='red')
    ax4.set_xlabel('Score Harmonique')
    ax4.set_ylabel('Taille (KB)')
    ax4.set_title('Relation Score Harmonique vs Taille')
    ax4.grid(True, alpha=0.3)
    
    # Ajout des labels sur le scatter plot
    for i, domain in enumerate(domains):
        ax4.annotate(domain, (harmonic_scores[i], sizes[i]), 
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    plt.tight_layout()
    
    # Sauvegarde du graphique
    chart_file = "batch_results_visualization.png"
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"📊 Visualisation sauvegardée: {chart_file}")
    return chart_file

def main():
    """Fonction principale"""
    
    # Analyse globale
    analysis_results = analyze_batch_results()
    
    # Analyse détaillée des meilleurs domaines
    report_file = Path("batch_processing_global_report.json")
    if report_file.exists():
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        domain_results = report['domain_results']
        
        # Top 3 domaines par score harmonique
        sorted_domains = sorted(domain_results.items(), 
                            key=lambda x: x[1]['harmonic_score'], 
                            reverse=True)
        
        print(f"\n🏆 ANALYSE DÉTAILLÉE DES TOP 3 DOMAINES:")
        for i, (domain_name, result) in enumerate(sorted_domains[:3], 1):
            analyze_domain_details(domain_name)
    
    # Création des visualisations
    try:
        create_visualization()
    except Exception as e:
        print(f"⚠️ Erreur création visualisation: {str(e)}")
    
    print(f"\n🌊 Analyse batch terminée!")

if __name__ == "__main__":
    main()
