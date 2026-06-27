#!/usr/bin/env python3
"""
Performance Tracker
Suivi des performances de recompression H.264 → HCV16
"""

import json
import time
import os
from typing import Dict, List, Optional
from datetime import datetime

class PerformanceTracker:
    """Tracker de performance pour recompression H.264 → HCV16"""
    
    def __init__(self, log_file: str = "performance_log.json"):
        self.log_file = log_file
        self.session_data = []
        self.session_start = time.time()
        
    def record_compression(self, input_file: str, original_size: int, 
                          compressed_size: int, ratio: float, strategy: str,
                          processing_time: float, analysis_results: Dict):
        """Enregistrement d'une compression"""
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'input_file': os.path.basename(input_file),
            'file_info': analysis_results.get('file_info', {}),
            'original_size_mb': original_size / (1024 * 1024),
            'compressed_size_mb': compressed_size / (1024 * 1024),
            'compression_ratio': ratio,
            'savings_percent': ((ratio - 1) * 100) if ratio > 1 else 0,
            'strategy_used': strategy,
            'processing_time_sec': processing_time,
            'analysis_summary': {
                'blocking_artifacts': analysis_results['blocking_artifacts']['level'],
                'motion_residuals': analysis_results['motion_residuals']['level'],
                'quantization_noise': analysis_results['quantization_noise']['level'],
                'temporal_stability': analysis_results['temporal_patterns']['temporal_stability'],
                'opportunity_level': analysis_results['hcv16_opportunities']['opportunity_level']
            },
            'performance_metrics': {
                'mb_per_second': (original_size / (1024 * 1024)) / processing_time if processing_time > 0 else 0,
                'frames_per_second': analysis_results['frames_analyzed'] / processing_time if processing_time > 0 else 0
            }
        }
        
        self.session_data.append(record)
        self._save_to_log()
        
        print(f"📊 Performance enregistrée: {ratio:.3f}× en {processing_time:.1f}s")
    
    def _save_to_log(self):
        """Sauvegarde dans fichier log"""
        try:
            # Chargement données existantes
            existing_data = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    existing_data = json.load(f)
            
            # Ajout nouvelles données
            existing_data.extend(self.session_data)
            
            # Sauvegarde
            with open(self.log_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️  Erreur sauvegarde log: {e}")
    
    def generate_session_report(self) -> str:
        """Génération rapport de session"""
        if not self.session_data:
            return "Aucune compression dans cette session"
        
        # Calculs statistiques
        ratios = [r['compression_ratio'] for r in self.session_data]
        processing_times = [r['processing_time_sec'] for r in self.session_data]
        savings = [r['savings_percent'] for r in self.session_data]
        
        avg_ratio = sum(ratios) / len(ratios)
        avg_savings = sum(savings) / len(savings)
        avg_time = sum(processing_times) / len(processing_times)
        total_original = sum(r['original_size_mb'] for r in self.session_data)
        total_compressed = sum(r['compressed_size_mb'] for r in self.session_data)
        
        # Comptage stratégies
        strategies = {}
        for record in self.session_data:
            strategy = record['strategy_used']
            strategies[strategy] = strategies.get(strategy, 0) + 1
        
        # Comptage niveaux d'opportunité
        opportunities = {}
        for record in self.session_data:
            level = record['analysis_summary']['opportunity_level']
            opportunities[level] = opportunities.get(level, 0) + 1
        
        report = f"""
📊 RAPPORT SESSION RECOMPRESSION H.264 → HCV16
{'='*60}

🎯 RÉSULTATS GLOBAUX:
   Fichiers traités: {len(self.session_data)}
   Ratio moyen: {avg_ratio:.3f}×
   Économie moyenne: {avg_savings:.1f}%
   Temps moyen: {avg_time:.1f}s/fichier
   
💾 VOLUMES:
   Total original: {total_original:.1f} MB
   Total compressé: {total_compressed:.1f} MB
   Économie totale: {total_original - total_compressed:.1f} MB
   
🔧 STRATÉGIES UTILISÉES:
"""
        
        for strategy, count in strategies.items():
            percentage = (count / len(self.session_data)) * 100
            report += f"   {strategy}: {count} fichiers ({percentage:.1f}%)\n"
        
        report += f"""
🎯 NIVEAUX D'OPPORTUNITÉ:
"""
        
        for level, count in opportunities.items():
            percentage = (count / len(self.session_data)) * 100
            report += f"   {level}: {count} fichiers ({percentage:.1f}%)\n"
        
        # Top performers
        best_ratio = max(self.session_data, key=lambda x: x['compression_ratio'])
        worst_ratio = min(self.session_data, key=lambda x: x['compression_ratio'])
        
        report += f"""
🏆 PERFORMANCES:
   Meilleur ratio: {best_ratio['compression_ratio']:.3f}× ({best_ratio['input_file']})
   Ratio le plus faible: {worst_ratio['compression_ratio']:.3f}× ({worst_ratio['input_file']})
   
⚡ VITESSE:
   Débit moyen: {sum(r['performance_metrics']['mb_per_second'] for r in self.session_data) / len(self.session_data):.1f} MB/s
   FPS moyen: {sum(r['performance_metrics']['frames_per_second'] for r in self.session_data) / len(self.session_data):.1f} fps
"""
        
        return report
    
    def get_statistics(self) -> Dict:
        """Statistiques détaillées"""
        if not self.session_data:
            return {}
        
        ratios = [r['compression_ratio'] for r in self.session_data]
        
        return {
            'count': len(self.session_data),
            'avg_ratio': sum(ratios) / len(ratios),
            'min_ratio': min(ratios),
            'max_ratio': max(ratios),
            'success_rate': len([r for r in ratios if r >= 1.02]) / len(ratios),
            'excellent_rate': len([r for r in ratios if r >= 1.15]) / len(ratios),
            'total_savings_mb': sum(r['original_size_mb'] - r['compressed_size_mb'] for r in self.session_data)
        }
    
    def export_detailed_report(self, output_file: str = "detailed_performance_report.json"):
        """Export rapport détaillé"""
        report_data = {
            'session_info': {
                'start_time': datetime.fromtimestamp(self.session_start).isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_minutes': (time.time() - self.session_start) / 60
            },
            'statistics': self.get_statistics(),
            'detailed_results': self.session_data
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"📄 Rapport détaillé exporté: {output_file}")
        return output_file