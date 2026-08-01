"""
🏥 HWAT-Med Inference Server — Phase 3 Vital Ka Integration
===========================================================
FastAPI server for medical AI inference with HWAT-Med-125M.

API Endpoints:
  POST /diagnose      — Differential diagnosis from symptoms
  POST /prescribe     — Prescription suggestion with dosing
  POST /interactions  — Drug interaction checking
  POST /explain       — Medical explanation / patient education
  POST /hologram/query — Holographic memory query
  GET  /health        — Health check
  GET  /model/info    — Model information

Usage:
  python inference_server.py --model checkpoints/hwat_med_125m/model_final.pt
  
  Or with uvicorn:
  uvicorn inference_server:app --host 0.0.0.0 --port 8000
"""

import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import torch
import torch.nn.functional as F
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from tokenizers import Tokenizer

# Add engine to path
ENGINE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ENGINE_DIR))

from train_hwat_kaggle import HWATMed, phase_attention_fast, mlp_fast, layernorm_amp_fast

# Hologrammes médicaux (routeur spectral, prêt sans GPU)
from hologram_router import HologramRouter

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model state
model: Optional[HWATMed] = None
tokenizer: Optional[Tokenizer] = None
hologram_router: Optional['HologramRouter'] = None
device: torch.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model_config: Dict[str, Any] = {}


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS (API Contracts)
# ═══════════════════════════════════════════════════════════════════════════════

class DiagnoseRequest(BaseModel):
    symptoms: List[str] = Field(..., description="List of patient symptoms")
    patient_age: Optional[int] = Field(None, description="Patient age in years")
    patient_sex: Optional[str] = Field(None, description="Patient sex (M/F)")
    history: Optional[List[str]] = Field(None, description="Medical history")
    max_diagnoses: int = Field(5, description="Maximum number of diagnoses to return")

class DiagnoseResponse(BaseModel):
    diagnoses: List[Dict[str, Any]] = Field(..., description="Ranked differential diagnoses")
    confidence: float = Field(..., description="Overall confidence score")
    disclaimer: str = Field(default="This is AI assistance, not medical advice. Consult a healthcare professional.")

class PrescribeRequest(BaseModel):
    diagnosis: str = Field(..., description="Confirmed diagnosis")
    patient_age: int = Field(..., description="Patient age")
    patient_weight: Optional[float] = Field(None, description="Patient weight in kg")
    allergies: Optional[List[str]] = Field(None, description="Known allergies")
    current_meds: Optional[List[str]] = Field(None, description="Current medications")
    guidelines: Optional[str] = Field("WHO", description="Guideline source (WHO, local, etc.)")

class PrescribeResponse(BaseModel):
    medications: List[Dict[str, Any]] = Field(..., description="Prescribed medications with dosing")
    warnings: List[str] = Field(default_factory=list, description="Safety warnings")
    monitoring: List[str] = Field(default_factory=list, description="Required monitoring")

class InteractionsRequest(BaseModel):
    medications: List[str] = Field(..., description="List of medications to check")
    patient_factors: Optional[Dict[str, Any]] = Field(None, description="Age, renal/hepatic function, etc.")

class InteractionsResponse(BaseModel):
    interactions: List[Dict[str, Any]] = Field(..., description="Identified drug interactions")
    severity: str = Field(..., description="Overall severity (none/minor/moderate/major/contraindicated)")
    recommendations: List[str] = Field(..., description="Clinical recommendations")

class ExplainRequest(BaseModel):
    topic: str = Field(..., description="Medical topic to explain")
    audience: str = Field("patient", description="Target audience (patient, student, clinician)")
    language: str = Field("fr", description="Language code (fr, en, wo, bm, etc.)")
    max_length: int = Field(500, description="Maximum response length in tokens")

class ExplainResponse(BaseModel):
    explanation: str = Field(..., description="Generated explanation")
    sources: List[str] = Field(default_factory=list, description="Reference sources")
    reading_level: str = Field(..., description="Estimated reading level")

class HologramQueryRequest(BaseModel):
    domain: str = Field(..., description="Medical domain (infectious, cardiology, pediatrics, etc.)")
    query: str = Field(..., description="Natural language query")
    top_k: int = Field(5, description="Number of results")

class HologramQueryResponse(BaseModel):
    results: List[Dict[str, Any]] = Field(..., description="Retrieved holographic memories")
    domain: str = Field(..., description="Queried domain")

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str
    model_params: Optional[int] = None
    
    model_config = {'protected_namespaces': ()}

class ModelInfoResponse(BaseModel):
    name: str
    version: str
    architecture: str
    parameters: int
    vocab_size: int
    max_seq_len: int
    medical_specialties: List[str]
    training_data: str


# ═══════════════════════════════════════════════════════════════════════════════
# MODEL LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_model(model_path: str, config_override: Dict = None):
    """Load HWAT-Med model from checkpoint."""
    global model, tokenizer, model_config
    
    logger.info(f"Loading model from {model_path}")
    ckpt = torch.load(model_path, map_location=device, weights_only=False)
    
    # Extract config
    model_config = ckpt.get('config', {})
    if config_override:
        model_config.update(config_override)
    
    # Default config for 125M
    default_config = {
        'vocab_size': 50000,
        'dim': 1024,
        'n_layers': 12,
        'n_heads': 16,
        'max_seq_len': 512,
        'hidden_mult': 4,
        'use_float32': True,
        'lora_rank': 32,
        'lora_alpha': 32.0,
    }
    for k, v in default_config.items():
        model_config.setdefault(k, v)
    
    # Create model
    model = HWATMed(**model_config).to(device)
    
    # Load weights
    state_dict = ckpt.get('model_state_dict', ckpt)
    model_dict = model.state_dict()
    
    matched = 0
    for k, v in state_dict.items():
        if k in model_dict and v.shape == model_dict[k].shape:
            model_dict[k].copy_(v)
            matched += 1
    
    logger.info(f"Loaded {matched}/{len(model_dict)} parameters")
    
    # Load tokenizer
    tokenizer_path = model_config.get('tokenizer_path', 'tokenizer_medical_50k/tokenizer.json')
    tokenizer = Tokenizer.from_file(str(ENGINE_DIR / tokenizer_path))
    
    model.eval()
    logger.info(f"Model loaded on {device}")


# ═══════════════════════════════════════════════════════════════════════════════
# INFERENCE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_text(prompt: str, max_new_tokens: int = 256, temperature: float = 0.7, 
                  top_p: float = 0.9, stop_tokens: List[int] = None) -> str:
    """Generate text from prompt using the model."""
    if model is None or tokenizer is None:
        raise RuntimeError("Model not loaded")
    
    # Encode prompt
    encoded = tokenizer.encode(prompt)
    input_ids = torch.tensor(encoded.ids, dtype=torch.long, device=device)
    
    # Generate
    generated = input_ids.clone()
    
    with torch.no_grad():
        for _ in range(max_new_tokens):
            # Forward pass
            logits = model(generated)  # [L, V]
            next_logits = logits[-1] / temperature
            
            # Top-p sampling
            probs = F.softmax(next_logits, dim=-1)
            sorted_probs, sorted_indices = torch.sort(probs, descending=True)
            cumsum_probs = torch.cumsum(sorted_probs, dim=-1)
            sorted_indices_to_remove = cumsum_probs > top_p
            sorted_indices_to_remove[1:] = sorted_indices_to_remove[:-1].clone()
            sorted_indices_to_remove[0] = False
            indices_to_remove = sorted_indices_to_remove.scatter(0, sorted_indices, sorted_indices_to_remove)
            probs[indices_to_remove] = 0
            probs = probs / probs.sum()
            
            # Sample
            next_token = torch.multinomial(probs, 1).item()
            
            if stop_tokens and next_token in stop_tokens:
                break
            
            generated = torch.cat([generated, torch.tensor([next_token], device=device)])
            
            # Max length check
            if len(generated) >= model_config.get('max_seq_len', 512):
                break
    
    # Decode only new tokens
    new_tokens = generated[len(input_ids):].tolist()
    return tokenizer.decode(new_tokens)


def build_diagnose_prompt(request: DiagnoseRequest) -> str:
    """Build structured prompt for diagnosis."""
    parts = ["<diagnose>"]
    parts.append(f"Symptômes: {', '.join(request.symptoms)}")
    if request.patient_age:
        parts.append(f"Âge: {request.patient_age} ans")
    if request.patient_sex:
        parts.append(f"Sexe: {request.patient_sex}")
    if request.history:
        parts.append(f"Antécédents: {', '.join(request.history)}")
    parts.append(f"Donner jusqu'à {request.max_diagnoses} diagnostics différentiels avec probabilités.")
    parts.append("</diagnose>")
    return "\n".join(parts)


def build_prescribe_prompt(request: PrescribeRequest) -> str:
    """Build structured prompt for prescription."""
    parts = ["<prescribe>"]
    parts.append(f"Diagnostic: {request.diagnosis}")
    parts.append(f"Âge: {request.patient_age} ans")
    if request.patient_weight:
        parts.append(f"Poids: {request.patient_weight} kg")
    if request.allergies:
        parts.append(f"Allergies: {', '.join(request.allergies)}")
    if request.current_meds:
        parts.append(f"Traitement actuel: {', '.join(request.current_meds)}")
    parts.append(f"Guidelines: {request.guidelines}")
    parts.append("Prescrire médicaments avec posologie, durée, surveillance.")
    parts.append("</prescribe>")
    return "\n".join(parts)


def build_interactions_prompt(request: InteractionsRequest) -> str:
    """Build prompt for drug interactions."""
    parts = ["<interactions>"]
    parts.append(f"Médicaments: {', '.join(request.medications)}")
    if request.patient_factors:
        for k, v in request.patient_factors.items():
            parts.append(f"{k}: {v}")
    parts.append("Analyser interactions, sévérité, recommandations.")
    parts.append("</interactions>")
    return "\n".join(parts)


def build_explain_prompt(request: ExplainRequest) -> str:
    """Build prompt for medical explanation."""
    parts = ["<explain>"]
    parts.append(f"Sujet: {request.topic}")
    parts.append(f"Public: {request.audience}")
    parts.append(f"Langue: {request.language}")
    parts.append(f"Longueur max: {request.max_length} tokens")
    parts.append("Expliquer clairement, sans jargon si patient.")
    parts.append("</explain>")
    return "\n".join(parts)


def build_hologram_prompt(request: HologramQueryRequest) -> str:
    """Build prompt for holographic memory query."""
    parts = ["<hologram>"]
    parts.append(f"Domaine: {request.domain}")
    parts.append(f"Requête: {request.query}")
    parts.append(f"Top {request.top_k} résultats.")
    parts.append("</hologram>")
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    global hologram_router

    # 1. Hologrammes médicaux (toujours disponibles — zéro GPU)
    holograms_dir = ENGINE_DIR / "data" / "medical_holograms"
    if holograms_dir.exists():
        try:
            hologram_router = HologramRouter(holograms_dir=str(holograms_dir))
            logger.info(f"Hologrammes médicaux chargés : "
                        f"{len(hologram_router.list_domains())} domaines")
        except Exception as e:
            logger.error(f"Échec chargement hologrammes: {e}")

    # 2. Modèle 125M (si checkpoint disponible)
    model_path = Path("checkpoints/hwat_med_125m/model_final.pt")
    if not model_path.exists():
        # Try to find any checkpoint
        for p in Path("checkpoints").rglob("*.pt"):
            if "hwat" in p.name.lower() and "med" in p.name.lower():
                model_path = p
                break

    if model_path.exists():
        try:
            load_model(str(model_path))
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
    else:
        logger.warning("No model checkpoint found - serving holograms only")

    yield

    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="HWAT-Med Inference API",
    description="Medical AI inference for Vital Ka ecosystem",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if (model is not None or hologram_router is not None) else "degraded",
        model_loaded=model is not None,
        device=str(device),
        model_params=sum(p.numel() for p in model.parameters()) if model else None,
    )


@app.get("/model/info", response_model=ModelInfoResponse)
async def model_info():
    """Model information."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    specialties = [
        "infectious_disease", "cardiology", "pulmonology", "neurology",
        "pediatrics", "obstetrics_gynecology", "psychiatry", "dermatology",
        "endocrinology", "gastroenterology", "nephrology", "hematology_oncology"
    ]
    
    return ModelInfoResponse(
        name="HWAT-Med-125M",
        version="1.0.0",
        architecture="Harmonic Wavelet Attention Transformer",
        parameters=sum(p.numel() for p in model.parameters()),
        vocab_size=model_config.get('vocab_size', 50000),
        max_seq_len=model_config.get('max_seq_len', 512),
        medical_specialties=specialties,
        training_data="Vital Ka medical corpus (63.7M chars, 132k segments)",
    )


@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(request: DiagnoseRequest):
    """Differential diagnosis from symptoms."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    prompt = build_diagnose_prompt(request)
    response_text = generate_text(prompt, max_new_tokens=256, temperature=0.3)
    
    # Parse response (simplified - in production use structured output)
    diagnoses = []
    for line in response_text.strip().split('\n'):
        if line.strip() and ('%' in line or 'probabilité' in line.lower() or 'diagnostic' in line.lower()):
            diagnoses.append({"text": line.strip()})
    
    if not diagnoses:
        diagnoses = [{"text": response_text[:500]}]
    
    return DiagnoseResponse(
        diagnoses=diagnoses[:request.max_diagnoses],
        confidence=0.75,  # Placeholder
        disclaimer="Avertissement: Ceci est une assistance IA, pas un avis médical. Consultez un professionnel de santé."
    )


@app.post("/prescribe", response_model=PrescribeResponse)
async def prescribe(request: PrescribeRequest):
    """Prescription suggestion with dosing."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    prompt = build_prescribe_prompt(request)
    response_text = generate_text(prompt, max_new_tokens=300, temperature=0.2)
    
    # Parse medications (simplified)
    medications = []
    for line in response_text.strip().split('\n'):
        if line.strip() and any(kw in line.lower() for kw in ['mg', 'ml', 'fois', 'jour', 'semaine', 'comprim', 'gélul']):
            medications.append({"text": line.strip()})
    
    if not medications:
        medications = [{"text": response_text[:500]}]
    
    return PrescribeResponse(
        medications=medications,
        warnings=["Vérifier allergies", "Ajuster selon fonction rénale/hépatique"],
        monitoring=["Évolution clinique", "Effets indésirables"]
    )


@app.post("/interactions", response_model=InteractionsResponse)
async def interactions(request: InteractionsRequest):
    """Drug interaction checking."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    prompt = build_interactions_prompt(request)
    response_text = generate_text(prompt, max_new_tokens=300, temperature=0.2)
    
    # Determine severity from response
    severity = "none"
    text_lower = response_text.lower()
    if "contre-indiqué" in text_lower or "contre-indique" in text_lower:
        severity = "contraindicated"
    elif "majeur" in text_lower or "grave" in text_lower:
        severity = "major"
    elif "modéré" in text_lower or "modere" in text_lower:
        severity = "moderate"
    elif "mineur" in text_lower or "léger" in text_lower:
        severity = "minor"
    
    interactions_list = []
    for line in response_text.strip().split('\n'):
        if line.strip():
            interactions_list.append({"description": line.strip()})
    
    return InteractionsResponse(
        interactions=interactions_list or [{"description": response_text[:500]}],
        severity=severity,
        recommendations=["Surveiller le patient", "Considérer alternative si possible"]
    )


@app.post("/explain", response_model=ExplainResponse)
async def explain(request: ExplainRequest):
    """Medical explanation / patient education."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    prompt = build_explain_prompt(request)
    response_text = generate_text(prompt, max_new_tokens=request.max_length, temperature=0.5)
    
    return ExplainResponse(
        explanation=response_text.strip(),
        sources=["Vital Ka Medical Knowledge Base", "WHO Guidelines"],
        reading_level="Patient" if request.audience == "patient" else "Professional"
    )


@app.post("/hologram/query", response_model=HologramQueryResponse)
async def hologram_query(request: HologramQueryRequest):
    """Query holographic memory (routeur spectral médical)."""
    # Le routeur fonctionne sans GPU — toujours disponible
    if hologram_router is None:
        raise HTTPException(status_code=503, detail="Hologrammes non chargés")

    # Requête = domaine + requête fusionnés (le routeur gère le routing)
    query_text = request.query
    if request.domain and request.domain != "auto":
        query_text = f"{request.domain} {request.query}"

    # Routage vers les meilleurs domaines (sélection du domaine)
    routes = hologram_router.route(query_text, top_k=3)
    results = []
    seen = set()
    best_score = 0.0

    for domain, confidence in routes:
        # Retrieval des faits les plus pertinents du domaine
        # (score normalisé [0,1] par retrieve_facts — le routage
        #  sélectionne le domaine, le score vient du retrieval)
        facts = hologram_router.retrieve_facts(domain, query_text, top_k=request.top_k)
        for f in facts:
            key = f"{f['sujet']}|{f['relation']}|{f['objet']}"
            if key in seen:
                continue
            seen.add(key)
            score = f.get('score', 0.5)
            best_score = max(best_score, score)
            results.append({
                "content": f.get('phrase') or f"{f['sujet']} {f['relation']} {f['objet']}",
                "sujet": f['sujet'],
                "relation": f['relation'],
                "objet": f['objet'],
                "secteur": domain,
                "score": score,
            })

    # Si le domaine demandé n'est pas dans le top des routes, compléter
    if request.domain and request.domain != "auto":
        dom_upper = request.domain.upper()
        if dom_upper not in [d for d, _ in routes]:
            direct_facts = hologram_router.retrieve_facts(
                dom_upper, request.query, top_k=request.top_k)
            for f in direct_facts:
                key = f"{f['sujet']}|{f['relation']}|{f['objet']}"
                if key in seen:
                    continue
                seen.add(key)
                score = f.get('score', 0.5)
                best_score = max(best_score, score)
                results.append({
                    "content": f.get('phrase') or f"{f['sujet']} {f['relation']} {f['objet']}",
                    "sujet": f['sujet'],
                    "relation": f['relation'],
                    "objet": f['objet'],
                    "secteur": dom_upper,
                    "score": score,
                })

    # ⚠️ SEUIL DE CONFIANCE : en médical, mieux vaut "je ne sais pas"
    # que renvoyer un faux résultat (hallucination par défaut).
    MIN_SCORE = 0.15
    if best_score < MIN_SCORE:
        return HologramQueryResponse(
            results=[{
                "content": "Aucune correspondance fiable trouvée pour cette requête. "
                           "Cette question ne relève pas des connaissances médicales Vital Ka "
                           "ou manque de précision. Consultez un professionnel de santé.",
                "sujet": "",
                "relation": "",
                "objet": "hors domaine",
                "secteur": routes[0][0] if routes else "INCONNU",
                "score": 0.0,
            }],
            domain=routes[0][0] if routes else "INCONNU"
        )

    return HologramQueryResponse(
        results=results[:request.top_k * 2] or [{
            "content": "Aucun fait trouvé pour cette requête",
            "sujet": "",
            "relation": "",
            "objet": "",
            "secteur": routes[0][0] if routes else "INCONNU",
            "score": 0.0,
        }],
        domain=routes[0][0] if routes else (request.domain or 'auto')
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    # Allow model path as argument
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="checkpoints/hwat_med_125m/model_final.pt")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    
    # Pre-load model
    if Path(args.model).exists():
        load_model(args.model)
    
    uvicorn.run(app, host=args.host, port=args.port)