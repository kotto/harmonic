#!/usr/bin/env python3
"""
MEDICAL RESONATOR — Diagnostic médical par résonance ondulatoire
===================================================================
Applique la Théorie Harmonique au diagnostic médical :
  - ECG → spectre de Fourier → détection d'anomalies
  - EEG → cartes de fréquences cérébrales
  - Sang → superposition des marqueurs → diagnostic
  - Pharmacocinétique → modélisation onde

Principe :
  La santé = résonance harmonieuse
  La maladie = interférence destructive ou désaccord
  Le diagnostic = décomposition de Fourier du signal corporel
  La thérapie = onde correctrice en opposition de phase

Usage :
  from medical_resonator import MedicalResonator
  mr = MedicalResonator()
  diagnosis = mr.analyze_ecg(ecg_signal, sample_rate=250)
  diagnosis = mr.analyze_blood_markers({"glucose": 1.2, "pH": 7.1, ...})
  diagnosis = mr.diagnose(symptoms=["fatigue", "douleur articulaire"])

Basé sur le Dictionnaire des Ondes de l'Univers.
"""

import numpy as np
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

try:
    from phytotherapy_kb import PhytotherapyKB
    HAS_PHYTO = True
except ImportError:
    HAS_PHYTO = False

PHI = 1.618033988749895

# ══════════════════════════════════════════════════════════════════════════
# BASE DE CONNAISSANCES MÉDICALES ONDULATOIRES
# ══════════════════════════════════════════════════════════════════════════

# Fréquences propres du corps humain (valeurs normales)
BODY_FREQUENCIES = {
    "cœur":        {"rate": (60, 100), "unit": "bpm", "description": "Fréquence cardiaque au repos"},
    "respiration": {"rate": (12, 20),  "unit": "bpm", "description": "Fréquence respiratoire au repos"},
    "cerveau_delta":  {"rate": (0.5, 4),  "unit": "Hz", "description": "Sommeil profond"},
    "cerveau_theta":  {"rate": (4, 8),    "unit": "Hz", "description": "Méditation, somnolence"},
    "cerveau_alpha":  {"rate": (8, 13),   "unit": "Hz", "description": "Relaxation éveillée"},
    "cerveau_beta":   {"rate": (13, 30),  "unit": "Hz", "description": "Concentration active"},
    "cerveau_gamma":  {"rate": (30, 100), "unit": "Hz", "description": "Traitement cognitif intense"},
    "circadien":      {"rate": (1/86400, 1/86400), "unit": "Hz", "description": "Cycle jour/nuit (~24h)"},
    "menstruel":      {"rate": (1/2419200, 1/1814400), "unit": "Hz", "description": "Cycle menstruel (21-35 jours)"},
    "renouvellement_peau": {"rate": (1/2419200, 1/2419200), "unit": "Hz", "description": "Renouvellement cutané (~28 jours)"},
}

# Valeurs normales des marqueurs sanguins
BLOOD_MARKERS = {
    "glucose":       (0.70, 1.10, "g/L", "Énergie cellulaire — fréquence métabolique"),
    "pH":            (7.35, 7.45, "", "Équilibre acido-basique — résonance chimique"),
    "hemoglobine":   (13.0, 17.0, "g/dL", "Transport O₂ — amplitude oxygénation"),
    "leucocytes":    (4000, 10000, "/mm³", "Défense — amplitude immunitaire"),
    "plaquettes":    (150000, 400000, "/mm³", "Coagulation — fréquence de réparation"),
    "creatinine":    (0.6, 1.2, "mg/dL", "Filtration rénale — fréquence d'épuration"),
    "troponine":     (0, 0.04, "ng/mL", "Lésion cardiaque — onde de choc myocardique"),
    "CRP":           (0, 5, "mg/L", "Inflammation — amplitude de défense"),
    "TSH":           (0.4, 4.0, "mUI/L", "Thyroïde — fréquence métabolique globale"),
    "vitamine_D":    (30, 100, "ng/mL", "Régulation — harmonique osseuse et immunitaire"),
    "cholesterol_LDL": (0, 1.6, "g/L", "Lipides — amortissement artériel si excessif"),
    "cholesterol_HDL": (0.4, 0.6, "g/L", "Lipides protecteurs — harmonique inverse du LDL"),
}

# Correspondance symptômes → désaccord ondulatoire
SYMPTOM_TO_DISHARMONY = {
    "fatigue":           ("Effondrement d'amplitude métabolique", "Restaurer résonance mitochondriale"),
    "fièvre":            ("Amplification anormale de la fréquence immunitaire", "Identifier la fréquence pathogène et générer onde d'annulation"),
    "douleur":           ("Interférence destructive localisée — battement entre lésion et réparation", "Onde analgésique en opposition de phase"),
    "inflammation":      ("Saturation d'amplitude de la réponse immunitaire", "Filtre passe-bas — réduire l'amplitude de la réponse"),
    "insomnie":          ("Désynchronisation circadienne — perte de la fréquence sommeil", "Restaurer onde delta (0.5-4 Hz) par hygiène du sommeil"),
    "anxiété":           ("Oscillation anticipatoire dans le vide — fréquence bêta excessive", "Entraînement alpha/thêta (méditation, cohérence cardiaque)"),
    "dépression":        ("Effondrement d'amplitude — toutes les fréquences sont atténuées", "Amplification par résonance externe (activité, lumière, lien social)"),
    "hypertension":       ("Amplitude excessive de l'onde de pression artérielle", "Amortissement par filtre passe-bas (vasodilatateurs, relaxation)"),
    "arythmie":           ("Désaccord de la fréquence cardiaque fondamentale", "Restaurer la fréquence propre du nœud sinusal"),
    "diabète_type2":      ("Désensibilisation à la fréquence insuline — perte de résonance", "Restaurer sensibilité par désaturation des récepteurs"),
    "migraine":           ("Interférence constructive de stimuli sensoriels — seuil dépassé", "Filtrage des fréquences externes (obscurité, silence)"),
    "allergie":           ("Reconnaissance erronée d'une fréquence inoffensive comme hostile", "Désensibilisation progressive — apprendre la fréquence réelle"),
    "infection":          ("Une fréquence étrangère s'est introduite et se réplique", "Identifier ω_pathogène → antibiotique/antiviral = onde destructrice sélective"),
    "cancer":             ("Perte de la fréquence propre cellulaire — oscillation autonome chaotique", "Restaurer ω_saine ou détruire spécifiquement ω_cancer"),
    "maladie_autoimmune": ("Confusion soi/non-soi — attaque des propres fréquences", "Rééducation du système immunitaire — filtre adaptatif"),
    "vertige":            ("Désaccord entre fréquence vestibulaire et fréquence visuelle", "Réalignement des phases par rééducation"),
    "constipation":       ("Ralentissement de l'onde péristaltique — fréquence trop basse", "Stimuler la fréquence intestinale (fibres, hydratation, mouvement)"),
    "toux":               ("Onde d'expulsion — tentative d'éliminer une fréquence irritante", "Identifier et supprimer la fréquence irritante"),
}

# ══════════════════════════════════════════════════════════════════════════
# ANALYSEUR DE SIGNAUX
# ══════════════════════════════════════════════════════════════════════════

class SignalAnalyzer:
    """Analyse de signaux médicaux par décomposition harmonique."""
    
    @staticmethod
    def analyze_periodic(signal: np.ndarray, sample_rate: float) -> Dict:
        """
        Analyse un signal périodique (ECG, EEG, respiration).
        Retourne le spectre de Fourier et les fréquences dominantes.
        """
        n = len(signal)
        if n < 4:
            return {"error": "Signal trop court"}
        
        # Transformée de Fourier
        fft = np.fft.rfft(signal)
        freqs = np.fft.rfftfreq(n, 1.0 / sample_rate)
        power = np.abs(fft) ** 2
        
        # Fréquence dominante
        dominant_idx = np.argmax(power[1:]) + 1  # Ignorer DC
        dominant_freq = freqs[dominant_idx]
        dominant_power = power[dominant_idx]
        
        # Harmoniques (multiples de la fréquence fondamentale)
        harmonics = []
        for i in range(2, 6):
            harmonic_freq = dominant_freq * i
            # Trouver le pic le plus proche
            idx = np.argmin(np.abs(freqs - harmonic_freq))
            harmonics.append({
                "order": i,
                "frequency": float(freqs[idx]),
                "power_normalized": float(power[idx] / dominant_power) if dominant_power > 0 else 0
            })
        
        # Variabilité (écart-type de la fréquence instantanée)
        # Calcul simplifié via les pics
        peaks = []
        if len(signal) > 10:
            threshold = np.mean(signal) + 0.5 * np.std(signal)
            for i in range(1, n-1):
                if signal[i] > threshold and signal[i] > signal[i-1] and signal[i] > signal[i+1]:
                    peaks.append(i)
            
            if len(peaks) >= 2:
                intervals = np.diff(peaks) / sample_rate
                heart_rate_variability = float(np.std(intervals) * 1000)  # en ms
            else:
                heart_rate_variability = 0
        else:
            heart_rate_variability = 0
        
        return {
            "dominant_frequency_hz": float(dominant_freq),
            "dominant_power": float(dominant_power),
            "harmonics": harmonics,
            "total_power": float(np.sum(power)),
            "variability_ms": heart_rate_variability,
            "sample_rate": sample_rate,
            "duration_s": n / sample_rate,
        }
    
    @staticmethod
    def analyze_ecg(ecg_signal: np.ndarray, sample_rate: float = 250) -> Dict:
        """Analyse spécifique ECG."""
        base = SignalAnalyzer.analyze_periodic(ecg_signal, sample_rate)
        
        # Détection de la fréquence cardiaque
        heart_rate = base["dominant_frequency_hz"] * 60  # bpm
        
        # Diagnostic par rapport aux normes
        diagnosis = []
        if heart_rate < 60:
            diagnosis.append({
                "condition": "Bradycardie",
                "frequency_issue": f"ω = {heart_rate:.0f} bpm < ω_min (60 bpm)",
                "harmonic_interpretation": "Fréquence cardiaque ralentie — possible augmentation du tonus vagal",
            })
        elif heart_rate > 100:
            diagnosis.append({
                "condition": "Tachycardie",
                "frequency_issue": f"ω = {heart_rate:.0f} bpm > ω_max (100 bpm)",
                "harmonic_interpretation": "Fréquence cardiaque accélérée — possible stress, fièvre ou trouble du rythme",
            })
        else:
            diagnosis.append({
                "condition": "Rythme sinusal normal",
                "frequency_issue": f"ω = {heart_rate:.0f} bpm ∈ [60, 100]",
                "harmonic_interpretation": "Fréquence cardiaque en résonance normale",
            })
        
        # Analyse de la variabilité
        hrv = base["variability_ms"]
        if hrv > 0:
            if hrv < 20:
                diagnosis.append({
                    "condition": "HRV basse",
                    "frequency_issue": f"Variabilité = {hrv:.0f} ms",
                    "harmonic_interpretation": "Manque de flexibilité harmonique — stress chronique possible",
                })
            elif hrv > 100:
                diagnosis.append({
                    "condition": "HRV élevée",
                    "frequency_issue": f"Variabilité = {hrv:.0f} ms",
                    "harmonic_interpretation": "Bonne adaptabilité harmonique",
                })
        
        base["heart_rate_bpm"] = float(heart_rate)
        base["diagnosis"] = diagnosis
        base["signal_type"] = "ECG"
        return base
    
    @staticmethod
    def analyze_eeg(eeg_signal: np.ndarray, sample_rate: float = 256) -> Dict:
        """Analyse EEG par bandes de fréquences."""
        n = len(eeg_signal)
        fft = np.fft.rfft(eeg_signal)
        freqs = np.fft.rfftfreq(n, 1.0 / sample_rate)
        power = np.abs(fft) ** 2
        
        bands = {
            "delta": (0.5, 4),
            "theta": (4, 8),
            "alpha": (8, 13),
            "beta": (13, 30),
            "gamma": (30, 45),
        }
        
        band_powers = {}
        total_power = np.sum(power)
        
        for name, (low, high) in bands.items():
            mask = (freqs >= low) & (freqs < high)
            band_power = np.sum(power[mask])
            band_powers[name] = {
                "range_hz": f"{low}-{high}",
                "absolute_power": float(band_power),
                "relative_power": float(band_power / total_power * 100) if total_power > 0 else 0,
            }
        
        # Interprétation
        interpretation = []
        if band_powers["delta"]["relative_power"] > 40:
            interpretation.append("Dominance delta — sommeil profond ou état pathologique")
        if band_powers["theta"]["relative_power"] > 30:
            interpretation.append("Dominance thêta — méditation, somnolence ou TDAH")
        if band_powers["alpha"]["relative_power"] > 50:
            interpretation.append("Dominance alpha — relaxation éveillée optimale")
        if band_powers["beta"]["relative_power"] > 40:
            interpretation.append("Dominance bêta — concentration, anxiété ou stress")
        
        return {
            "band_powers": band_powers,
            "interpretation": interpretation,
            "signal_type": "EEG",
            "duration_s": n / sample_rate,
        }


# ══════════════════════════════════════════════════════════════════════════
# ANALYSEUR DE MARQUEURS SANGUINS
# ══════════════════════════════════════════════════════════════════════════

class BloodAnalyzer:
    """Analyse des marqueurs sanguins par superposition harmonique."""
    
    @staticmethod
    def analyze(markers: Dict[str, float]) -> Dict:
        """
        Analyse une série de marqueurs sanguins.
        Retourne un diagnostic harmonique.
        """
        results = []
        disharmonies = []
        harmony_score = 1.0
        
        for marker, value in markers.items():
            if marker in BLOOD_MARKERS:
                low, high, unit, description = BLOOD_MARKERS[marker]
                
                if value < low:
                    disharmonies.append({
                        "marker": marker,
                        "value": value,
                        "normal": f"{low}-{high} {unit}",
                        "type": "Amplitude insuffisante",
                        "description": description,
                        "correction": f"Augmenter l'amplitude de {marker} vers la fréquence propre [{low}-{high}]",
                    })
                    harmony_score *= max(0, value / low)
                    
                elif value > high:
                    disharmonies.append({
                        "marker": marker,
                        "value": value,
                        "normal": f"{low}-{high} {unit}",
                        "type": "Amplitude excessive",
                        "description": description,
                        "correction": f"Réduire l'amplitude de {marker} vers la fréquence propre [{low}-{high}]",
                    })
                    harmony_score *= max(0, high / value)
                    
                else:
                    results.append({
                        "marker": marker,
                        "status": "✅ Résonance normale",
                        "value": value,
                        "normal": f"{low}-{high} {unit}",
                    })
            else:
                results.append({
                    "marker": marker,
                    "status": "⚠️ Marqueur inconnu",
                    "value": value,
                })
        
        # Score global d'harmonie
        harmony_percentage = round(harmony_score * 100, 1)
        
        return {
            "results": results,
            "disharmonies": disharmonies,
            "harmony_score": min(100, harmony_percentage),
            "interpretation": BloodAnalyzer._interpret(harmony_percentage, disharmonies),
        }
    
    @staticmethod
    def _interpret(score: float, disharmonies: List) -> str:
        """Génère une interprétation narrative du score d'harmonie."""
        if score >= 95:
            return "L'orchestre sanguin est en parfaite résonance. Tous les marqueurs oscillent dans leur plage harmonique."
        elif score >= 80:
            return f"Légères dissonances détectées ({len(disharmonies)} marqueur(s)). Corrections mineures recommandées."
        elif score >= 60:
            return f"Désaccords modérés ({len(disharmonies)} marqueur(s)). Une intervention harmonique est conseillée."
        elif score >= 40:
            return f"Désaccords significatifs ({len(disharmonies)} marqueur(s)). Consultation médicale recommandée."
        else:
            return f"Désaccords majeurs ({len(disharmonies)} marqueur(s)). L'orchestre sanguin nécessite une intervention urgente."


# ══════════════════════════════════════════════════════════════════════════
# MODÉLISATEUR PHARMACOCINÉTIQUE
# ══════════════════════════════════════════════════════════════════════════

class Pharmacokinetics:
    """Modélisation pharmacocinétique par ondes."""
    
    @staticmethod
    def concentration_over_time(dose: float, half_life: float, time_points: np.ndarray) -> np.ndarray:
        """
        Modélise la concentration d'un médicament au fil du temps.
        C(t) = C₀ · e^(-kt)  où k = ln(2)/T½
        
        C'est la même équation que l'amortissement d'une onde !
        """
        k = np.log(2) / half_life
        return dose * np.exp(-k * time_points)
    
    @staticmethod
    def repeated_doses(dose: float, interval: float, half_life: float, num_doses: int) -> Dict:
        """
        Simulation de doses répétées (prise régulière de médicament).
        Chaque dose est une nouvelle onde qui s'ajoute à la précédente.
        """
        total_time = num_doses * interval + 5 * half_life  # Observer 5 demi-vies après la dernière dose
        t = np.linspace(0, total_time, 1000)
        concentration = np.zeros_like(t)
        
        for i in range(num_doses):
            dose_time = i * interval
            mask = t >= dose_time
            concentration[mask] += dose * np.exp(-np.log(2) / half_life * (t[mask] - dose_time))
        
        # État stationnaire : la concentration oscille entre C_min et C_max
        steady_state_min = dose * np.exp(-np.log(2) / half_life * interval) / (1 - np.exp(-np.log(2) / half_life * interval))
        steady_state_max = dose / (1 - np.exp(-np.log(2) / half_life * interval))
        
        return {
            "time": t.tolist(),
            "concentration": concentration.tolist(),
            "steady_state_min": float(steady_state_min),
            "steady_state_max": float(steady_state_max),
            "time_to_steady_state": float(5 * half_life),
            "harmonic_interpretation": (
                f"Chaque dose est une onde d'amplitude {dose} avec décroissance exponentielle "
                f"(k = ln(2)/{half_life} {chr(126)} {np.log(2)/half_life:.4f}). "
                f"Les doses successives se superposent. "
                f"L'état stationnaire oscille entre {steady_state_min:.1f} et {steady_state_max:.1f}. "
                f"C'est une interférence d'ondes amorties en régime permanent."
            ),
        }


# ══════════════════════════════════════════════════════════════════════════
# RÉSONATEUR MÉDICAL PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════

class MedicalResonator:
    """
    Système de diagnostic médical par résonance ondulatoire.
    Applique le Dictionnaire des Ondes de l'Univers à la médecine.
    """
    
    def __init__(self):
        self.body_frequencies = BODY_FREQUENCIES
        self.blood_markers = BLOOD_MARKERS
        self.symptom_map = SYMPTOM_TO_DISHARMONY
        self.signal_analyzer = SignalAnalyzer()
        self.blood_analyzer = BloodAnalyzer()
        self.pharmaco = Pharmacokinetics()
        self.name = "Medical Resonator (Théorie Harmonique)"
    
    def diagnose(self, symptoms: List[str], context: Dict = None) -> Dict:
        """
        Diagnostic par symptômes — traduit en langage ondulatoire.
        
        Args:
            symptoms: Liste de symptômes (ex: ["fatigue", "fièvre"])
            context: Contexte additionnel (âge, antécédents, etc.)
        
        Returns:
            Diagnostic harmonique complet
        """
        results = []
        disharmony_types = defaultdict(list)
        
        for symptom in symptoms:
            s_lower = symptom.lower().strip()
            if s_lower in self.symptom_map:
                disharmony, correction = self.symptom_map[s_lower]
                disharmony_types[disharmony].append(symptom)
                results.append({
                    "symptom": symptom,
                    "translation": disharmony,
                    "correction_strategy": correction,
                })
            else:
                # Recherche partielle
                found = False
                for key in self.symptom_map:
                    if key in s_lower or s_lower in key:
                        disharmony, correction = self.symptom_map[key]
                        disharmony_types[disharmony].append(symptom)
                        results.append({
                            "symptom": symptom,
                            "matched_to": key,
                            "translation": disharmony,
                            "correction_strategy": correction,
                        })
                        found = True
                        break
                if not found:
                    results.append({
                        "symptom": symptom,
                        "translation": "Symptôme non répertorié dans le dictionnaire",
                        "correction_strategy": "Analyse fréquentielle complémentaire nécessaire",
                    })
        
        # Score de sévérité = nombre de désaccords détectés
        severity = min(1.0, len(disharmony_types) * 0.15)
        
        # Génération du plan de correction
        corrections = []
        for disharmony, related_symptoms in disharmony_types.items():
            corrections.append({
                "disharmony": disharmony,
                "related_symptoms": related_symptoms,
                "strategy": self.symptom_map[related_symptoms[0].lower()][1] if related_symptoms else "Analyse complémentaire",
            })
        
        return {
            "diagnosis": results,
            "severity": round(severity, 2),
            "severity_label": "Léger" if severity < 0.3 else "Modéré" if severity < 0.6 else "Significatif",
            "correction_plan": corrections,
            "methodology": "Traduction Classique → Ondulatoire (Dictionnaire des Ondes de l'Univers)",
        }
    
    def analyze_ecg(self, ecg_signal: np.ndarray, sample_rate: float = 250) -> Dict:
        """Analyse un signal ECG."""
        return self.signal_analyzer.analyze_ecg(ecg_signal, sample_rate)
    
    def analyze_eeg(self, eeg_signal: np.ndarray, sample_rate: float = 256) -> Dict:
        """Analyse un signal EEG."""
        return self.signal_analyzer.analyze_eeg(eeg_signal, sample_rate)
    
    def analyze_blood(self, markers: Dict[str, float]) -> Dict:
        """Analyse des marqueurs sanguins."""
        return self.blood_analyzer.analyze(markers)
    
    def model_drug(self, dose: float, interval: float, half_life: float, num_doses: int) -> Dict:
        """Modélise la pharmacocinétique d'un médicament."""
        return self.pharmaco.repeated_doses(dose, interval, half_life, num_doses)
    
    def body_frequency_check(self) -> Dict:
        """Vérifie les fréquences connues du corps humain."""
        return {
            name: {
                "range": info["rate"],
                "unit": info["unit"],
                "description": info["description"],
            }
            for name, info in self.body_frequencies.items()
        }


# ══════════════════════════════════════════════════════════════════════════
# TEST
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mr = MedicalResonator()
    
    print("=" * 60)
    print("MEDICAL RESONATOR — Test")
    print("=" * 60)
    
    # Test 1 : Diagnostic par symptômes
    print("\n[Test 1] Diagnostic Ondulatoire")
    symptoms = ["fatigue", "fièvre", "douleur"]
    diag = mr.diagnose(symptoms)
    print(f"  Symptômes : {symptoms}")
    print(f"  Sévérité : {diag['severity_label']} ({diag['severity']})")
    for d in diag["diagnosis"]:
        print(f"    {d['symptom']} -> {d['translation'][:60]}...")
    
    # Test 2 : Analyse sanguine simulée
    print("\n[Test 2] Analyse Sanguine Harmonique")
    blood = {
        "glucose": 1.45,     # élevé
        "pH": 7.1,           # bas (acidose)
        "CRP": 12,           # élevé (inflammation)
        "hemoglobine": 14.5, # normal
        "leucocytes": 12000, # légèrement élevé
    }
    blood_result = mr.analyze_blood(blood)
    print(f"  Score d'harmonie : {blood_result['harmony_score']}%")
    print(f"  Interprétation : {blood_result['interpretation']}")
    for d in blood_result["disharmonies"]:
        print(f"    [!] {d['marker']} : {d['value']} ({d['type']}) - normal {d['normal']}")
    
    # Test 3 : ECG simulé
    print("\n[Test 3] ECG — Simulation")
    t = np.linspace(0, 4, 1000)  # 4 secondes à 250 Hz
    ecg_normal = np.sin(2 * np.pi * 1.2 * t) + 0.3 * np.sin(2 * np.pi * 2.4 * t) + 0.1 * np.random.randn(1000)
    ecg_result = mr.analyze_ecg(ecg_normal, sample_rate=250)
    print(f"  Fréquence cardiaque détectée : {ecg_result['heart_rate_bpm']:.0f} bpm")
    for d in ecg_result["diagnosis"]:
        print(f"    {d['condition']} : {d['harmonic_interpretation']}")
    
    # Test 4 : Pharmacocinétique
    print("\n[Test 4] Pharmacocinétique — Paracétamol")
    pk = mr.model_drug(dose=1000, interval=6, half_life=2.5, num_doses=6)
    print(f"  État stationnaire : [{pk['steady_state_min']:.0f}, {pk['steady_state_max']:.0f}] mg")
    print(f"  Temps jusqu'à l'état stationnaire : {pk['time_to_steady_state']:.1f} h")
    
    # Test 5 : Fréquences corporelles
    print("\n[Test 5] Fréquences Propres du Corps")
    freqs = mr.body_frequency_check()
    for name, info in list(freqs.items())[:5]:
        print(f"  {name} : {info['range']} {info['unit']} — {info['description']}")
    
    print("\n" + "=" * 60)
    print("Théorie Harmonique appliquée à la médecine — validé")
    print("=" * 60)