# Phase 3: Vital Ka Integration Guide

## Overview
This document describes how to integrate the HWAT-Med inference API into the 4 Vital Ka applications:
- **Patient App** — Symptom checker, medication reminders, health education
- **Médecin App** — Clinical decision support, prescription aid, referral guidance
- **Pharmacien App** — Drug interaction checking, dispensing guidance, substitution
- **Solidarité App** — Community health worker triage, telemedicine coordination

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Vital Ka Apps  │────▶│  KA_PLATFORM    │────▶│  HWAT-Med API   │
│  (Frontend)     │     │  .callAI()      │     │  (FastAPI)      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │                         │
                              ▼                         ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  localStorage   │     │  GPU Inference  │
                        │  + BroadcastCh  │     │  (A100/H100)    │
                        └─────────────────┘     └─────────────────┘
```

## API Endpoints

### 1. POST /diagnose — Differential Diagnosis
**Used by:** Patient App (symptom checker), Médecin App (clinical decision support), Solidarité App (triage)

**Request:**
```json
{
  "symptoms": ["fièvre", "toux sèche", "fatigue"],
  "patient_age": 45,
  "patient_sex": "M",
  "history": ["hypertension", "diabète type 2"],
  "max_diagnoses": 5
}
```

**Response:**
```json
{
  "diagnoses": [
    {"text": "COVID-19: 65% - Fièvre, toux sèche, fatigue", "icd10": "U07.1"},
    {"text": "Grippe saisonnière: 20% - Fièvre, toux, myalgies", "icd10": "J11.1"},
    {"text": "Pneumonie bactérienne: 10% - Fièvre, toux productive", "icd10": "J18.9"}
  ],
  "confidence": 0.75,
  "disclaimer": "Avertissement: Ceci est une assistance IA, pas un avis médical."
}
```

### 2. POST /prescribe — Prescription Suggestion
**Used by:** Médecin App (prescription aid), Pharmacien App (validation)

**Request:**
```json
{
  "diagnosis": "Pneumonie communautaire",
  "patient_age": 65,
  "patient_weight": 70,
  "allergies": ["pénicilline"],
  "current_meds": ["metformine", "amlodipine"],
  "guidelines": "WHO"
}
```

**Response:**
```json
{
  "medications": [
    {
      "drug": "Amoxicilline + Acide clavulanique",
      "dose": "1g/125mg",
      "route": "PO",
      "frequency": "3 fois/jour",
      "duration": "7 jours",
      "notes": "Alternative à pénicilline"
    },
    {
      "drug": "Paracétamol",
      "dose": "1g",
      "route": "PO",
      "frequency": "4 fois/jour si fièvre >38.5°C",
      "duration": "Selon besoin"
    }
  ],
  "warnings": ["Vérifier fonction rénale", "Surveiller diarrhée"],
  "monitoring": ["Température J1-3", "CRP J3", "Rx thorax si pas d'amélioration J3"]
}
```

### 3. POST /interactions — Drug Interaction Check
**Used by:** Pharmacien App (dispensing), Médecin App (prescription review)

**Request:**
```json
{
  "medications": ["warfarine", "amoxicilline", "ibuprofène"],
  "patient_factors": {"age": 72, "renal_function": "normal", "hepatic_function": "normal"}
}
```

**Response:**
```json
{
  "interactions": [
    {
      "pair": ["warfarine", "amoxicilline"],
      "severity": "major",
      "mechanism": "Augmentation INR par inhibition flore intestinale",
      "action": "Surveiller INR à J3 et J7, ajuster dose warfarine"
    },
    {
      "pair": ["warfarine", "ibuprofène"],
      "severity": "major",
      "mechanism": "Risque hémorragique additif (antiplaquettaire + anticoagulant)",
      "action": "Éviter association, préférer paracétamol"
    }
  ],
  "severity": "major",
  "recommendations": ["Remplacer ibuprofène par paracétamol", "INR contrôle rapproché"]
}
```

### 4. POST /explain — Medical Explanation
**Used by:** Patient App (health education), Solidarité App (community education)

**Request:**
```json
{
  "topic": "diabète type 2",
  "audience": "patient",
  "language": "fr",
  "max_length": 300
}
```

**Response:**
```json
{
  "explanation": "Le diabète type 2 est une maladie où le corps n'utilise pas bien l'insuline... [explication simple]",
  "sources": ["Vital Ka Medical Knowledge Base", "OMS Guidelines"],
  "reading_level": "Patient"
}
```

### 5. POST /hologram/query — Holographic Memory Query
**Used by:** Médecin App (rare case lookup), Pharmacien App (specialty knowledge), Research

**Request:**
```json
{
  "domain": "infectious_disease",
  "query": "Traitement paludisme sévère enfant Afrique subsaharienne",
  "top_k": 3
}
```

**Response:**
```json
{
  "results": [
    {
      "content": "Artesunate IV 2.4 mg/kg à H0, H12, H24 puis q24h...",
      "score": 0.92,
      "source": "WHO Guidelines 2023"
    },
    {
      "content": "Alternative: Quinine IV si artesunate indisponible...",
      "score": 0.85,
      "source": "MSF Clinical Guidelines"
    }
  ],
  "domain": "infectious_disease"
}
```

## Frontend Integration

### KA_PLATFORM.callAI() Helper

Add to each app's JavaScript:

```javascript
// ka_ai_bridge.js - Shared across all 4 apps
class KAAIBridge {
  constructor(baseUrl = 'https://api.vital-ka.org/ai') {
    this.baseUrl = baseUrl;
    this.cache = new Map();
  }
  
  async callAI(endpoint, payload, options = {}) {
    const cacheKey = `${endpoint}:${JSON.stringify(payload)}`;
    
    // Check cache (5 min TTL)
    if (options.useCache !== false && this.cache.has(cacheKey)) {
      const { data, timestamp } = this.cache.get(cacheKey);
      if (Date.now() - timestamp < 5 * 60 * 1000) return data;
    }
    
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`
        },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        throw new Error(`API ${response.status}: ${await response.text()}`);
      }
      
      const data = await response.json();
      
      // Cache successful responses
      if (options.useCache !== false) {
        this.cache.set(cacheKey, { data, timestamp: Date.now() });
      }
      
      return data;
    } catch (error) {
      console.error(`KA AI Error (${endpoint}):`, error);
      
      // Fallback to local knowledge base
      if (options.fallback !== false) {
        return this.localFallback(endpoint, payload);
      }
      throw error;
    }
  }
  
  // Convenience methods
  async diagnose(symptoms, patientInfo = {}) {
    return this.callAI('/diagnose', { symptoms, ...patientInfo });
  }
  
  async prescribe(diagnosis, patientInfo) {
    return this.callAI('/prescribe', { diagnosis, ...patientInfo });
  }
  
  async checkInteractions(medications, patientFactors = {}) {
    return this.callAI('/interactions', { medications, patient_factors: patientFactors });
  }
  
  async explain(topic, audience = 'patient', language = 'fr') {
    return this.callAI('/explain', { topic, audience, language });
  }
  
  async queryHologram(domain, query, topK = 5) {
    return this.callAI('/hologram/query', { domain, query, top_k: topK });
  }
  
  getAuthToken() {
    // Get from localStorage or auth context
    return localStorage.getItem('ka_auth_token') || '';
  }
  
  localFallback(endpoint, payload) {
    // Offline fallback using local knowledge base
    return { 
      offline: true, 
      message: 'Mode hors ligne - fonctionnalité limitée',
      data: null 
    };
  }
}

// Global instance
window.KA_PLATFORM = window.KA_PLATFORM || {};
window.KA_PLATFORM.ai = new KAAIBridge();
```

### App-Specific Usage

#### Patient App (ka_patient.js)
```javascript
// Symptom checker
async function checkSymptoms(symptoms) {
  const result = await KA_PLATFORM.ai.diagnose(symptoms, {
    patient_age: currentUser.age,
    patient_sex: currentUser.sex,
    history: currentUser.medicalHistory
  });
  
  displayDiagnoses(result.diagnoses);
  showDisclaimer(result.disclaimer);
}

// Medication explanation
async function explainMedication(drugName) {
  const result = await KA_PLATFORM.ai.explain(drugName, 'patient', currentUser.language);
  showExplanationModal(result.explanation);
}
```

#### Médecin App (ka_medecin.js)
```javascript
// Clinical decision support
async function getDiagnosisSupport(symptoms, patient) {
  const result = await KA_PLATFORM.ai.diagnose(symptoms, {
    patient_age: patient.age,
    patient_sex: patient.sex,
    history: patient.history,
    max_diagnoses: 10
  });
  
  // Show with confidence scores
  renderDiagnosisPanel(result.diagnoses);
}

// Prescription aid
async function suggestPrescription(diagnosis, patient) {
  const result = await KA_PLATFORM.ai.prescribe(diagnosis, {
    patient_age: patient.age,
    patient_weight: patient.weight,
    allergies: patient.allergies,
    current_meds: patient.currentMeds
  });
  
  // Pre-fill prescription form
  populatePrescriptionForm(result.medications);
  showWarnings(result.warnings);
}

// Real-time interaction check while prescribing
async function checkPrescriptionInteractions(newMeds, patient) {
  const allMeds = [...patient.currentMeds, ...newMeds];
  const result = await KA_PLATFORM.ai.checkInteractions(allMeds, {
    age: patient.age,
    renal_function: patient.renalFunction
  });
  
  if (result.severity === 'major' || result.severity === 'contraindicated') {
    showAlert('Interaction majeure détectée', result.recommendations);
  }
}
```

#### Pharmacien App (ka_pharmacien.js)
```javascript
// Dispensing validation
async function validateDispensing(prescription, patient) {
  const meds = prescription.medications.map(m => m.drug);
  const result = await KA_PLATFORM.ai.checkInteractions(meds, {
    age: patient.age,
    renal_function: patient.renalFunction,
    hepatic_function: patient.hepaticFunction
  });
  
  if (result.severity !== 'none') {
    showInteractionWarning(result);
    return false; // Block dispensing
  }
  return true; // Allow dispensing
}

// Substitution suggestion
async function suggestSubstitution(unavailableDrug, patient) {
  const result = await KA_PLATFORM.ai.explain(
    `Alternative à ${unavailableDrug} pour ${patient.diagnosis}`,
    'clinician',
    'fr'
  );
  showSubstitutionOptions(result.explanation);
}
```

#### Solidarité App (ka_solidarite.js)
```javascript
// Community health worker triage
async function triagePatient(symptoms, patient) {
  const result = await KA_PLATFORM.ai.diagnose(symptoms, {
    patient_age: patient.age,
    patient_sex: patient.sex,
    max_diagnoses: 3
  });
  
  // Determine urgency
  const urgent = result.diagnoses.some(d => 
    d.text.toLowerCase().includes('urgence') || 
    d.text.toLowerCase().includes('critique')
  );
  
  if (urgent) {
    triggerEmergencyReferral(patient, result.diagnoses);
  }
  
  return { diagnoses: result.diagnoses, urgent };
}

// Health education for community
async function getHealthEducation(topic, language = 'wo') {
  const result = await KA_PLATFORM.ai.explain(topic, 'patient', language);
  playAudioExplanation(result.explanation); // TTS for low literacy
}
```

## Deployment

### Production Checklist

1. **GPU Infrastructure**
   - A100 80GB or H100 for 125M model
   - Minimum 2 replicas for HA
   - Auto-scaling based on request queue

2. **API Gateway**
   - Rate limiting: 100 req/min per user
   - Authentication: JWT tokens
   - Request validation & sanitization

3. **Monitoring**
   - Latency p50/p95/p99
   - Error rates by endpoint
   - GPU utilization
   - Token usage/costs

4. **Security**
   - HTTPS only
   - Input sanitization (prevent prompt injection)
   - Audit logging for medical queries
   - Data residency (African servers)

5. **Offline Support**
   - Service workers for frontend
   - Local knowledge base cache
   - Sync when online

### Environment Variables
```bash
# inference_server.py
MODEL_PATH=/models/hwat_med_125m/model_final.pt
TOKENIZER_PATH=/models/tokenizer_medical_50k/tokenizer.json
DEVICE=cuda
MAX_BATCH_SIZE=8
LOG_LEVEL=INFO

# Frontend apps
VITE_AI_API_URL=https://api.vital-ka.org/ai
VITE_AI_TIMEOUT=30000
```

## Testing

### Unit Tests
```bash
# Test each endpoint
pytest tests/test_inference_api.py -v

# Load testing
locust -f tests/load_test.py --host=https://api.vital-ka.org/ai
```

### Integration Tests
```bash
# Test app integration
npm run test:e2e -- --spec="ai-integration"
```

## Rollout Plan

| Week | Milestone |
|------|-----------|
| 1 | Deploy inference server to staging, unit tests |
| 2 | Integrate Patient App (diagnose, explain) |
| 3 | Integrate Médecin App (diagnose, prescribe, interactions) |
| 4 | Integrate Pharmacien App (interactions, substitution) |
| 5 | Integrate Solidarité App (triage, education) |
| 6 | Load testing, security audit, production deploy |

## Support

- **Documentation:** https://docs.vital-ka.org/ai-api
- **Status:** https://status.vital-ka.org
- **Support:** ai-support@vital-ka.org
- **Emergency:** +221-XX-XX-XX-XX (Senegal)