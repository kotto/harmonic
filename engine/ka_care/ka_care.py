"""
KA CARE — Serveur de Santé Harmonique pour Zones Sous-Équipées
================================================================

Backend Flask autonome. Dépendances minimales.
Fonctionne sur Raspberry Pi, vieux laptop, ou téléphone Android (via Pydroid).
Optimisé pour fonctionnement OFFLINE.

Endpoints :
  GET  /api/health              — État du serveur
  POST /api/screen/pneumonia    — Dépistage pneumonie (OMS/IMCI)
  POST /api/screen/dehydration  — Évaluation déshydratation (OMS)
  POST /api/screen/fever        — Détection syndrome fébrile
  POST /api/screen/anemia       — Dépistage anémie
  POST /api/screen/newborn      — Signes danger nouveau-né
  POST /api/assess              — Évaluation communautaire complète
  POST /api/indicators          — Indicateurs harmoniques depuis PPG

Usage :
  python ka_care.py
  → http://localhost:8700

Auteur : Kotto Alain — Juillet 2026
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import math

# Importer le moteur de santé
from care_engine import (
    pneumonia_screener,
    dehydration_assessor,
    febrile_screener,
    anemia_screener,
    newborn_danger_screener,
    community_health_assessment,
    PHI, PI, E, S2, S3, S5,
)

app = Flask(__name__, static_folder='.')
CORS(app)

# ─── ROUTES STATIQUES ───

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(os.path.join('.', path)):
        return send_from_directory('.', path)
    return send_from_directory('.', 'index.html')


# ─── API ───

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'app': 'KA CARE',
        'version': '1.0.0',
        'constants': {
            'phi': PHI, 'pi': PI, 'e': E,
            'sqrt2': S2, 'sqrt3': S3, 'sqrt5': S5,
        },
        'tools': [
            'pneumonia', 'dehydration', 'fever',
            'anemia', 'newborn', 'assess'
        ],
        'offline': True,
    })


@app.route('/api/screen/pneumonia', methods=['POST'])
def screen_pneumonia():
    """Dépistage pneumonie (OMS/IMCI)."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        result = pneumonia_screener(
            age_months=data.get('age_months', 36),
            respiratory_rate=data.get('respiratory_rate'),
            heart_rate=data.get('heart_rate'),
            chest_indrawing=data.get('chest_indrawing', False),
            grunting=data.get('grunting', False),
            oxygen_saturation=data.get('oxygen_saturation'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/screen/dehydration', methods=['POST'])
def screen_dehydration():
    """Évaluation déshydratation (OMS)."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        result = dehydration_assessor(
            age_months=data.get('age_months', 24),
            skin_pinch_seconds=data.get('skin_pinch_seconds'),
            sunken_eyes=data.get('sunken_eyes', False),
            drinks_eagerly=data.get('drinks_eagerly', False),
            unable_to_drink=data.get('unable_to_drink', False),
            heart_rate=data.get('heart_rate'),
            respiratory_rate=data.get('respiratory_rate'),
            capillary_refill_seconds=data.get('capillary_refill_seconds'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/screen/fever', methods=['POST'])
def screen_fever():
    """Détection syndrome fébrile harmonique."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        result = febrile_screener(
            heart_rate=data.get('heart_rate'),
            respiratory_rate=data.get('respiratory_rate'),
            hrv_sdnn=data.get('hrv_sdnn'),
            ppg_amplitude=data.get('ppg_amplitude'),
            reported_fever=data.get('reported_fever', False),
            age_years=data.get('age_years', 5),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/screen/anemia', methods=['POST'])
def screen_anemia():
    """Dépistage anémie."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        result = anemia_screener(
            palmar_pallor=data.get('palmar_pallor', False),
            conjunctival_pallor=data.get('conjunctival_pallor', False),
            heart_rate=data.get('heart_rate'),
            respiratory_rate=data.get('respiratory_rate'),
            fatigue_reported=data.get('fatigue_reported', False),
            hrv_sdnn=data.get('hrv_sdnn'),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/screen/newborn', methods=['POST'])
def screen_newborn():
    """Signes de danger nouveau-né (OMS)."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        result = newborn_danger_screener(
            age_days=data.get('age_days', 3),
            heart_rate=data.get('heart_rate'),
            respiratory_rate=data.get('respiratory_rate'),
            temperature_feels=data.get('temperature_feels', 'normal'),
            feeding_well=data.get('feeding_well', True),
            moving_well=data.get('moving_well', True),
            umbilical_redness=data.get('umbilical_redness', False),
            convulsions=data.get('convulsions', False),
            jaundice_palms=data.get('jaundice_palms', False),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/assess', methods=['POST'])
def assess():
    """Évaluation communautaire complète (tous les outils)."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        result = community_health_assessment(
            age_months=data.get('age_months', 36),
            heart_rate=data.get('heart_rate'),
            respiratory_rate=data.get('respiratory_rate'),
            hrv_sdnn=data.get('hrv_sdnn'),
            ppg_amplitude=data.get('ppg_amplitude'),
            chest_indrawing=data.get('chest_indrawing', False),
            skin_pinch_seconds=data.get('skin_pinch_seconds'),
            sunken_eyes=data.get('sunken_eyes', False),
            palmar_pallor=data.get('palmar_pallor', False),
            reported_fever=data.get('reported_fever', False),
            feeding_well=data.get('feeding_well', True),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/indicators', methods=['POST'])
def indicators():
    """
    Calcul des indicateurs harmoniques à partir d'un signal PPG brut.
    
    Body : {
        "ppg_samples": [{"t": 0, "v": 128.5}, {"t": 33, "v": 129.1}, ...]
    }
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        samples = data.get('ppg_samples', [])
        
        if len(samples) < 90:
            return jsonify({'error': 'Au moins 90 échantillons requis (~3 secondes)'}), 400
        
        # Extraire le signal
        signal = [s['v'] for s in samples]
        n = len(signal)
        mean = sum(signal) / n
        std = math.sqrt(sum((x - mean)**2 for x in signal) / n)
        normalized = [(x - mean) / std if std > 0 else 0 for x in signal]
        
        # Détection de pics
        filtered = [normalized[i] - normalized[i-2] for i in range(2, n)]
        peaks = []
        for i in range(2, len(filtered) - 1):
            if (filtered[i] > filtered[i-1] and filtered[i] > filtered[i+1] 
                and filtered[i] > 0.3):
                peaks.append(i + 2)
        
        # Intervalles RR
        rr = []
        for i in range(1, len(peaks)):
            dt = samples[peaks[i]]['t'] - samples[peaks[i-1]]['t']
            if 300 < dt < 2000:
                rr.append(dt)
        
        result = {}
        
        # BPM
        if len(rr) >= 2:
            sorted_rr = sorted(rr)
            med_rr = sorted_rr[len(sorted_rr)//2]
            result['bpm'] = round(60000 / med_rr)
        
        # HRV SDNN
        if len(rr) >= 4:
            rr_mean = sum(rr) / len(rr)
            result['hrv_sdnn'] = round(math.sqrt(
                sum((x - rr_mean)**2 for x in rr) / len(rr)))
        
        # HRV RMSSD
        if len(rr) >= 4:
            sum_sq = sum((rr[i] - rr[i-1])**2 for i in range(1, len(rr)))
            result['hrv_rmssd'] = round(math.sqrt(sum_sq / (len(rr) - 1)))
        
        # Cohérence φ
        if 'bpm' in result and 'hrv_sdnn' in result:
            cv = result['hrv_sdnn'] / (60000 / result['bpm'])
            target = 1 / (PHI * PHI)
            result['coherence_phi'] = round(
                max(0, min(100, 100 * (1 - abs(cv - target) / target))))
        
        # Fréquence respiratoire (modulation d'amplitude)
        if len(peaks) >= 6:
            amplitudes = [samples[p]['v'] for p in peaks]
            amp_f = [amplitudes[i] - amplitudes[i-2] for i in range(2, len(amplitudes))]
            resp_peaks = 0
            for i in range(2, len(amp_f) - 1):
                if (amp_f[i] > amp_f[i-1] and amp_f[i] > amp_f[i+1] 
                    and amp_f[i] > 0.2):
                    resp_peaks += 1
            duration = (samples[-1]['t'] - samples[0]['t']) / 1000
            if duration > 5 and resp_peaks >= 2:
                result['respiratory_rate'] = round(resp_peaks * 60 / duration)
        
        # Score de vitalité
        vitality_score = 0
        vitality_count = 0
        if 'coherence_phi' in result:
            vitality_score += result['coherence_phi']
            vitality_count += 1
        if 'bpm' in result:
            vitality_score += max(0, 100 - abs(result['bpm'] - 64) * 3)
            vitality_count += 1
        if 'hrv_rmssd' in result:
            vitality_score += min(100, result['hrv_rmssd'] * 3)
            vitality_count += 1
        if 'respiratory_rate' in result:
            if 12 <= result['respiratory_rate'] <= 18:
                vitality_score += 100
            else:
                vitality_score += max(0, 100 - abs(result['respiratory_rate'] - 15) * 8)
            vitality_count += 1
        if vitality_count > 0:
            result['vitality_score'] = round(vitality_score / vitality_count)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ─── GESTION DES PATIENTS ───

import uuid
import time
from pathlib import Path

PATIENTS_DIR = Path(__file__).resolve().parent / 'patients'
PATIENTS_DIR.mkdir(exist_ok=True)


def _patient_path(patient_id=None):
    """Retourne le chemin du fichier patient."""
    return PATIENTS_DIR / f'{patient_id}.json' if patient_id else None


def _load_patient(patient_id):
    """Charge un dossier patient."""
    path = _patient_path(patient_id)
    if not path or not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_patient(patient_id, data):
    """Sauvegarde un dossier patient."""
    path = _patient_path(patient_id)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@app.route('/api/patient/create', methods=['POST'])
def patient_create():
    """
    Crée un dossier patient.
    
    Body : {
        "nom": "Dupont",
        "prenom": "Marie",
        "age": 5,
        "age_unite": "ans",  // "mois" ou "ans"
        "sexe": "F",
        "village": "Bamako",
        "notes": ""
    }
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        if not data.get('nom') or not data.get('prenom'):
            return jsonify({'error': 'Nom et prénom requis'}), 400
        
        patient_id = str(uuid.uuid4())[:8]
        patient = {
            'id': patient_id,
            'nom': data['nom'].strip(),
            'prenom': data['prenom'].strip(),
            'age': data.get('age', 0),
            'age_unite': data.get('age_unite', 'ans'),
            'sexe': data.get('sexe', ''),
            'village': data.get('village', ''),
            'notes': data.get('notes', ''),
            'created_at': time.strftime('%Y-%m-%d %H:%M'),
            'updated_at': time.strftime('%Y-%m-%d %H:%M'),
            'screenings': [],
        }
        _save_patient(patient_id, patient)
        return jsonify({'status': 'ok', 'patient': patient})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patient/list', methods=['GET'])
def patient_list():
    """Liste tous les patients."""
    try:
        patients = []
        for f in sorted(PATIENTS_DIR.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True):
            with open(f, 'r', encoding='utf-8') as fp:
                p = json.load(fp)
            # Résumé léger pour la liste
            last = p['screenings'][-1] if p['screenings'] else None
            patients.append({
                'id': p['id'],
                'nom': p['nom'],
                'prenom': p['prenom'],
                'age': p['age'],
                'age_unite': p['age_unite'],
                'sexe': p['sexe'],
                'village': p['village'],
                'nb_screenings': len(p['screenings']),
                'last_screening': last['date'] if last else None,
                'last_result': last.get('classification', last.get('score_harmonique', '—')) if last else '—',
                'created_at': p['created_at'],
            })
        return jsonify({'patients': patients, 'total': len(patients)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patient/<patient_id>', methods=['GET'])
def patient_get(patient_id):
    """Récupère le dossier complet d'un patient."""
    try:
        patient = _load_patient(patient_id)
        if not patient:
            return jsonify({'error': 'Patient introuvable'}), 404
        return jsonify({'patient': patient})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patient/<patient_id>/screening', methods=['POST'])
def patient_add_screening(patient_id):
    """
    Ajoute un résultat de dépistage au dossier patient.
    
    Body : {
        "type": "pneumonia",  // ou dehydration, fever, anemia, newborn, assess
        "result": { ... }      // le résultat complet de l'outil de dépistage
    }
    """
    try:
        patient = _load_patient(patient_id)
        if not patient:
            return jsonify({'error': 'Patient introuvable'}), 404
        
        data = request.get_json(force=True, silent=True) or {}
        screening_type = data.get('type', 'unknown')
        result = data.get('result', {})
        
        screening = {
            'date': time.strftime('%Y-%m-%d %H:%M'),
            'type': screening_type,
            'result': result,
            'classification': result.get('classification', result.get('niveau_urgence', '—')),
            'action': result.get('action', result.get('recommandation', '—')),
        }
        
        patient['screenings'].append(screening)
        patient['updated_at'] = time.strftime('%Y-%m-%d %H:%M')
        _save_patient(patient_id, patient)
        
        return jsonify({
            'status': 'ok',
            'patient_id': patient_id,
            'nb_screenings': len(patient['screenings']),
            'screening': screening,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/patient/<patient_id>/delete', methods=['DELETE', 'POST'])
def patient_delete(patient_id):
    """Supprime un dossier patient."""
    try:
        path = _patient_path(patient_id)
        if not path or not path.exists():
            return jsonify({'error': 'Patient introuvable'}), 404
        path.unlink()
        return jsonify({'status': 'ok', 'deleted': patient_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─── DÉMARRAGE ───

if __name__ == '__main__':
    port = int(os.environ.get('KA_CARE_PORT', 8700))
    print("=" * 55)
    print("  🫀  KA CARE — Santé Harmonique Communautaire")
    print("=" * 55)
    print(f"  Serveur : http://localhost:{port}")
    print(f"  API     : http://localhost:{port}/api/health")
    print(f"  Outils  : pneumonie | déshydratation | fièvre")
    print(f"            anémie | nouveau-né | évaluation complète")
    print()
    print(f"  Constantes : φ={PHI:.4f} π={PI:.4f} e={E:.4f}")
    print(f"               √2={S2:.4f} √3={S3:.4f} √5={S5:.4f}")
    print()
    print("  ⚠ AIDE AU DÉPISTAGE — pas un dispositif médical certifié")
    print("=" * 55)
    app.run(host='0.0.0.0', port=port, debug=False)
