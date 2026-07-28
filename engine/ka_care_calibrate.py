"""
KA Care — Pipeline de Calibration Clinique
===========================================
Transforme les scores de résonance harmonique en indicateurs
cliniquement valides : courbes ROC, sensibilité, spécificité,
VPP, VPN, seuils optimaux (Youden).

Méthodologie :
  1. Dataset de cas patients (symptômes + diagnostic confirmé)
  2. Pour chaque pathologie, calculer les scores de résonance
  3. Faire varier le seuil de décision
  4. Mesurer TP, FP, TN, FN à chaque seuil
  5. Tracer la courbe ROC → AUC
  6. Déterminer le seuil optimal (indice de Youden)
  7. Calibrer les poids des features par régression logistique

Usage:
    python ka_care_calibrate.py                    # Exécuter la calibration
    python ka_care_calibrate.py --report           # Générer le rapport complet
    python ka_care_calibrate.py --optimize-weights # Optimiser les poids
"""

import sys, os, json, math
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ka_care import KACare, encode, resonance, MEDICAL_FEATURES


# ═══════════════════════════════════════════════════════════════════
# DATASET SYNTHÉTIQUE DE VALIDATION
# ═══════════════════════════════════════════════════════════════════

# Format: (symptomes, diagnostic_confirme)
# Basé sur des présentations cliniques typiques (OMS, CDC, HAS)
VALIDATION_CASES = [
    # ── COVID-19 ──
    ("fievre, toux seche, fatigue, anosmie, agueusie, courbatures", "COVID-19"),
    ("fievre, toux seche, fatigue, essoufflement, anosmie", "COVID-19"),
    ("fievre elevee, toux seche, fatigue intense, perte d odorat", "COVID-19"),
    ("toux seche, fatigue, maux de tete, anosmie", "COVID-19"),
    ("fievre, toux seche, courbatures, fatigue, diarrhee", "COVID-19"),
    
    # ── Grippe ──
    ("fievre, toux grasse, courbatures, maux de tete, fatigue, frissons", "Grippe_saisonnière"),
    ("fievre elevee, courbatures, maux de tete, fatigue intense, frissons", "Grippe_saisonnière"),
    ("fievre, mal de gorge, toux grasse, courbatures", "Grippe_saisonnière"),
    ("frissons, fievre, courbatures, fatigue, toux", "Grippe_saisonnière"),
    ("maux de tete, fievre, frissons, douleurs musculaires, toux", "Grippe_saisonnière"),
    
    # ── Infarctus ──
    ("douleur thoracique, essoufflement, sueurs froides, nausees, douleur bras gauche", "Infarctus_du_myocarde"),
    ("douleur thoracique intense, oppression, sueurs, angoisse, palpitations", "Infarctus_du_myocarde"),
    ("douleur thoracique, essoufflement brutal, malaise, sueurs froides", "Infarctus_du_myocarde"),
    ("douleur bras gauche, oppression thoracique, nausees, angoisse", "Infarctus_du_myocarde"),
    ("palpitations, douleur thoracique, essoufflement, sueurs", "Infarctus_du_myocarde"),
    
    # ── Rhume ──
    ("nez bouche, eternuements, mal de gorge leger, ecoulement nasal", "Rhume"),
    ("nez bouche, eternuements, fatigue legere, mal de gorge", "Rhume"),
    ("ecoulement nasal, eternuements, toux legere", "Rhume"),
    ("nez bouche, mal de gorge leger, fatigue", "Rhume"),
    ("eternuements, nez bouche, toux legere, mal de gorge", "Rhume"),
    
    # ── Paludisme ──
    ("fievre cyclique, frissons, sueurs, maux de tete, nausees, fatigue intense", "Paludisme_simple"),
    ("fievre, frissons, sueurs, maux de tete, douleurs musculaires", "Paludisme_simple"),
    ("fievre elevee, frissons intenses, sueurs profuses, cephalees", "Paludisme_simple"),
    ("fievre, frissons, nausees, fatigue extreme, douleurs musculaires", "Paludisme_simple"),
    ("fievre cyclique, sueurs nocturnes, cephalees, nausees", "Paludisme_simple"),
    
    # ── Dengue ──
    ("fievre elevee, maux de tete intenses, douleurs retro orbitaires, douleurs articulaires, eruption cutanee", "Dengue"),
    ("fievre, douleurs articulaires, eruption cutanee, maux de tete, nausees", "Dengue"),
    ("fievre elevee, douleurs musculaires, eruption, cephalees intenses", "Dengue"),
    ("fievre, douleurs articulaires, maux de tete, fatigue, eruption", "Dengue"),
    ("eruption cutanee, fievre, douleurs retro orbitaires, nausees", "Dengue"),
    
    # ── Gastro ──
    ("diarrhee, vomissements, nausees, douleurs abdominales, fievre moderee", "Gastro_entérite"),
    ("vomissements, diarrhee, crampes abdominales, nausees", "Gastro_entérite"),
    ("diarrhee aqueuse, vomissements, douleurs abdominales, fatigue", "Gastro_entérite"),
    ("nausees, vomissements, diarrhee, fievre legere", "Gastro_entérite"),
    ("douleurs abdominales, diarrhee, nausees, perte appetit", "Gastro_entérite"),
    
    # ── Méningite ──
    ("fievre elevee, maux de tete violents, raideur nuque, photophobie, vomissements", "Méningite"),
    ("fievre, cephalees intenses, raideur nuque, confusion, photophobie", "Méningite"),
    ("maux de tete violents, fievre, raideur nuque, vomissements", "Méningite"),
    ("photophobie, cephalees, fievre, raideur nuque, confusion", "Méningite"),
    ("fievre elevee, raideur nuque, maux de tete, vomissements, taches rouges", "Méningite"),
    
    # ── Asthme ──
    ("essoufflement, sifflement respiratoire, toux seche, oppression thoracique", "Crise_dasthme"),
    ("difficulte respirer, sifflement, oppression, toux", "Crise_dasthme"),
    ("essoufflement, respiration sifflante, oppression thoracique", "Crise_dasthme"),
    ("toux seche nocturne, essoufflement, sifflement", "Crise_dasthme"),
    ("oppression thoracique, difficulte parler, essoufflement, sifflement", "Crise_dasthme"),
]


# ═══════════════════════════════════════════════════════════════════
# MÉTRIQUES DE CALIBRATION
# ═══════════════════════════════════════════════════════════════════

@dataclass
class DiseaseMetrics:
    """Métriques cliniques pour une pathologie."""
    name: str
    auc: float = 0.0           # Area Under ROC Curve
    optimal_threshold: float = 0.5
    sensitivity: float = 0.0   # Rappel / TPR
    specificity: float = 0.0   # TNR
    ppv: float = 0.0           # Valeur Prédictive Positive
    npv: float = 0.0           # Valeur Prédictive Négative
    f1_score: float = 0.0
    n_cases: int = 0           # Nombre de cas positifs dans le dataset
    thresholds: List[float] = field(default_factory=list)
    tpr_list: List[float] = field(default_factory=list)
    fpr_list: List[float] = field(default_factory=list)


class ClinicalCalibrator:
    """Pipeline de calibration clinique des scores de résonance."""
    
    def __init__(self):
        self.care = KACare()
        self.metrics: Dict[str, DiseaseMetrics] = {}
    
    def calibrate(self, cases: List[Tuple[str, str]] = None) -> Dict[str, DiseaseMetrics]:
        """Exécute la calibration complète sur le dataset.
        
        Returns:
            Dict[maldie_name -> DiseaseMetrics]
        """
        if cases is None:
            cases = VALIDATION_CASES
        
        # 1. Calculer les scores pour tous les cas
        all_scores = []
        for symptoms, true_diagnosis in cases:
            scores = self._compute_scores(symptoms)
            all_scores.append((symptoms, true_diagnosis, scores))
        
        # 2. Pour chaque maladie, calculer les métriques ROC
        diseases = set(true_diag for _, true_diag, _ in all_scores)
        
        for disease in sorted(diseases):
            metrics = self._compute_roc(disease, all_scores)
            self.metrics[disease] = metrics
        
        return self.metrics
    
    def _compute_scores(self, symptoms: str) -> Dict[str, float]:
        """Calcule les scores de résonance pour tous les symptômes."""
        psi_patient = encode(symptoms)
        scores = {}
        for name, data in self.care._maladies.items():
            scores[name] = float(resonance(psi_patient, data["psi"]))
        return scores
    
    def _compute_roc(
        self, disease: str, all_scores: List[Tuple]
    ) -> DiseaseMetrics:
        """Calcule la courbe ROC pour une maladie donnée."""
        
        # Collecter les scores et labels
        y_true = []
        y_score = []
        
        for _, true_diag, scores in all_scores:
            y_true.append(1.0 if true_diag == disease else 0.0)
            y_score.append(scores.get(disease, 0.0))
        
        y_true = np.array(y_true)
        y_score = np.array(y_score)
        
        n_positive = int(np.sum(y_true))
        n_negative = len(y_true) - n_positive
        
        if n_positive == 0:
            return DiseaseMetrics(name=disease, n_cases=0)
        
        # Trier par score décroissant
        sorted_idx = np.argsort(y_score)[::-1]
        y_true_sorted = y_true[sorted_idx]
        y_score_sorted = y_score[sorted_idx]
        
        # Calculer TPR et FPR à chaque seuil
        thresholds = []
        tpr_list = []
        fpr_list = []
        
        tp = 0; fp = 0
        for i in range(len(y_true_sorted)):
            if y_true_sorted[i] == 1:
                tp += 1
            else:
                fp += 1
            
            tpr = tp / n_positive if n_positive > 0 else 0
            fpr = fp / n_negative if n_negative > 0 else 0
            
            thresholds.append(float(y_score_sorted[i]))
            tpr_list.append(tpr)
            fpr_list.append(fpr)
        
        # AUC par la méthode des trapèzes
        auc = 0.0
        for i in range(1, len(fpr_list)):
            auc += (fpr_list[i] - fpr_list[i-1]) * (tpr_list[i] + tpr_list[i-1]) / 2
        auc = abs(auc)
        
        # Seuil optimal : indice de Youden = TPR - FPR
        youden = np.array(tpr_list) - np.array(fpr_list)
        optimal_idx = int(np.argmax(youden))
        optimal_threshold = thresholds[optimal_idx]
        
        # Métriques au seuil optimal
        tp_opt = sum(1 for i in range(len(y_true)) 
                     if y_true[i] == 1 and y_score[i] >= optimal_threshold)
        fp_opt = sum(1 for i in range(len(y_true)) 
                     if y_true[i] == 0 and y_score[i] >= optimal_threshold)
        tn_opt = sum(1 for i in range(len(y_true)) 
                     if y_true[i] == 0 and y_score[i] < optimal_threshold)
        fn_opt = sum(1 for i in range(len(y_true)) 
                     if y_true[i] == 1 and y_score[i] < optimal_threshold)
        
        sensitivity = tp_opt / n_positive if n_positive > 0 else 0
        specificity = tn_opt / n_negative if n_negative > 0 else 0
        ppv = tp_opt / (tp_opt + fp_opt) if (tp_opt + fp_opt) > 0 else 0
        npv = tn_opt / (tn_opt + fn_opt) if (tn_opt + fn_opt) > 0 else 0
        f1 = 2 * sensitivity * ppv / (sensitivity + ppv) if (sensitivity + ppv) > 0 else 0
        
        return DiseaseMetrics(
            name=disease,
            auc=round(auc, 4),
            optimal_threshold=round(optimal_threshold, 4),
            sensitivity=round(sensitivity, 4),
            specificity=round(specificity, 4),
            ppv=round(ppv, 4),
            npv=round(npv, 4),
            f1_score=round(f1, 4),
            n_cases=n_positive,
            thresholds=thresholds,
            tpr_list=tpr_list,
            fpr_list=fpr_list,
        )
    
    def report(self) -> str:
        """Génère un rapport de calibration complet."""
        if not self.metrics:
            self.calibrate()
        
        lines = []
        lines.append("=" * 70)
        lines.append("RAPPORT DE CALIBRATION CLINIQUE — KA Care")
        lines.append("=" * 70)
        lines.append(f"Dataset : {len(VALIDATION_CASES)} cas, {len(self.metrics)} pathologies")
        lines.append(f"Méthode : Courbes ROC, seuil optimal par indice de Youden")
        lines.append("")
        lines.append(f"{'Pathologie':30s} {'AUC':>6s} {'Seuil':>6s} {'Sens':>6s} {'Spec':>6s} {'VPP':>6s} {'VPN':>6s} {'F1':>6s} {'n':>4s}")
        lines.append("-" * 70)
        
        for name in sorted(self.metrics.keys()):
            m = self.metrics[name]
            lines.append(
                f"{name[:28]:30s} {m.auc:6.3f} {m.optimal_threshold:6.3f} "
                f"{m.sensitivity:6.3f} {m.specificity:6.3f} {m.ppv:6.3f} "
                f"{m.npv:6.3f} {m.f1_score:6.3f} {m.n_cases:4d}"
            )
        
        lines.append("-" * 70)
        
        # Résumé
        avg_auc = np.mean([m.auc for m in self.metrics.values() if m.n_cases > 0])
        lines.append(f"\nAUC moyen : {avg_auc:.3f}")
        
        # Interprétation clinique
        lines.append("\n📋 INTERPRÉTATION CLINIQUE")
        lines.append("-" * 70)
        for name in sorted(self.metrics.keys()):
            m = self.metrics[name]
            if m.n_cases == 0:
                continue
            interpretation = self._interpret_metrics(m)
            lines.append(f"\n{name}:")
            lines.append(f"  AUC = {m.auc:.3f} → {interpretation['auc']}")
            lines.append(f"  Seuil optimal = {m.optimal_threshold:.3f}")
            lines.append(f"  Sensibilité = {m.sensitivity:.1%} → {interpretation['sens']}")
            lines.append(f"  Spécificité = {m.specificity:.1%} → {interpretation['spec']}")
            lines.append(f"  VPP = {m.ppv:.1%} → {interpretation['ppv']}")
            lines.append(f"  F1 = {m.f1_score:.3f}")
        
        return "\n".join(lines)
    
    def _interpret_metrics(self, m: DiseaseMetrics) -> dict:
        """Interprétation qualitative des métriques."""
        return {
            "auc": (
                "Excellent (≥0.9)" if m.auc >= 0.9 else
                "Bon (0.8-0.9)" if m.auc >= 0.8 else
                "Acceptable (0.7-0.8)" if m.auc >= 0.7 else
                "Faible (<0.7) — nécessite calibration"
            ),
            "sens": (
                "Détecte presque tous les cas" if m.sensitivity >= 0.9 else
                "Bonne détection" if m.sensitivity >= 0.8 else
                "Détection modérée" if m.sensitivity >= 0.7 else
                "Beaucoup de faux négatifs"
            ),
            "spec": (
                "Très peu de fausses alertes" if m.specificity >= 0.9 else
                "Peu de fausses alertes" if m.specificity >= 0.8 else
                "Fausses alertes modérées" if m.specificity >= 0.7 else
                "Beaucoup de faux positifs"
            ),
            "ppv": (
                "Diagnostic très fiable quand positif" if m.ppv >= 0.9 else
                "Diagnostic fiable" if m.ppv >= 0.8 else
                "Diagnostic à confirmer" if m.ppv >= 0.7 else
                "Score élevé ne garantit pas le diagnostic"
            ),
        }


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--report", action="store_true", help="Générer le rapport complet")
    p.add_argument("--optimize-weights", action="store_true", help="Optimiser les poids des features")
    args = p.parse_args()
    
    calibrator = ClinicalCalibrator()
    metrics = calibrator.calibrate()
    
    if args.report or not args.optimize_weights:
        print(calibrator.report())
    
    if args.optimize_weights:
        print("\n🔧 OPTIMISATION DES POIDS — À IMPLÉMENTER")
        print("   Méthode : régression logistique par pathologie")
        print("   Objectif : maximiser l'AUC en ajustant les poids des features")
        print("   Données nécessaires : 100+ cas confirmés par pathologie")
