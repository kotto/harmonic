"""
HCS Medical Units Service
=========================
Système d'unités médicales familiales pour frais médicaux en Afrique

Port: 9022
"""

import os
import sys
import json
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Query, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ============================================================================
# MODELS
# ============================================================================

class MedicalUnitType(str, Enum):
    EMERGENCY = "emergency"
    CHRONIC = "chronic"
    PREVENTION = "prevention"

class MedicalUnitStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    INSUFFICIENT = "insufficient"

class ProofType(str, Enum):
    PRESCRIPTION = "prescription"
    HOSPITAL_BILL = "hospital_bill"
    LAB_RESULT = "lab_result"
    PHARMACY_RECEIPT = "pharmacy_receipt"

@dataclass
class MedicalUnit:
    """Unité médicale familiale"""
    unit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    initiator_id: str = ""
    beneficiary_id: str = ""
    type: MedicalUnitType = MedicalUnitType.EMERGENCY
    amount: float = 0.0
    currency: str = "USD"
    reason: str = ""
    medical_proof_url: str = ""
    hospital: str = ""
    duration_days: int = 7
    frequency: str = "once"  # once, monthly, annual
    family_members: List[str] = field(default_factory=list)
    contributions: Dict[str, float] = field(default_factory=dict)
    total_collected: float = 0.0
    status: MedicalUnitStatus = MedicalUnitStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    deadline: str = ""
    transferred_at: Optional[str] = None
    insurance_coverage: float = 0.0
    fee_percent: float = 0.5
    notes: str = ""

@dataclass
class MedicalProof:
    """Preuve médicale"""
    proof_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    unit_id: str = ""
    proof_type: ProofType = ProofType.PRESCRIPTION
    file_url: str = ""
    doctor_name: str = ""
    hospital: str = ""
    date: str = ""
    amount: float = 0.0
    verified: bool = False
    ocr_text: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class MedicalRecord:
    """Dossier médical"""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    unit_id: str = ""
    date: str = ""
    type: str = ""
    reason: str = ""
    amount: float = 0.0
    hospital: str = ""
    doctor: str = ""
    diagnosis: str = ""
    treatment: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class FamilyGroup:
    """Groupe familial"""
    group_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    members: List[str] = field(default_factory=list)
    admin_id: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_units: int = 0
    total_collected: float = 0.0

# ============================================================================
# STORAGE (In-Memory pour démo)
# ============================================================================

medical_units_db: Dict[str, MedicalUnit] = {}
medical_proofs_db: Dict[str, MedicalProof] = {}
medical_records_db: Dict[str, List[MedicalRecord]] = {}
family_groups_db: Dict[str, FamilyGroup] = {}

# ============================================================================
# APP
# ============================================================================

app = FastAPI(title="HCS Medical Units Service", version="1.0.0")

# ============================================================================
# ENDPOINTS - UNITÉS MÉDICALES
# ============================================================================

@app.post("/medical-units/create")
async def create_medical_unit(request: Request):
    """Crée une unité médicale"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    unit = MedicalUnit(
        initiator_id=body.get("initiator_id", ""),
        beneficiary_id=body.get("beneficiary_id", ""),
        type=MedicalUnitType(body.get("type", "emergency")),
        amount=body.get("amount", 0.0),
        currency=body.get("currency", "USD"),
        reason=body.get("reason", ""),
        hospital=body.get("hospital", ""),
        duration_days=body.get("duration_days", 7),
        frequency=body.get("frequency", "once"),
        family_members=body.get("family_members", []),
    )
    
    # Calculer deadline
    if unit.type == MedicalUnitType.EMERGENCY:
        unit.deadline = (datetime.now(timezone.utc) + timedelta(days=unit.duration_days)).isoformat()
        unit.fee_percent = 1.0
    else:
        unit.deadline = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        unit.fee_percent = 0.5
    
    medical_units_db[unit.unit_id] = unit
    
    return JSONResponse({
        "status": "created",
        "unit": asdict(unit),
        "notifications_sent": len(unit.family_members),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/medical-units/{unit_id}/contribute")
async def contribute_to_unit(unit_id: str, request: Request):
    """Contribue à une unité médicale"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    if unit_id not in medical_units_db:
        raise HTTPException(404, "Medical unit not found")
    
    unit = medical_units_db[unit_id]
    contributor_id = body.get("contributor_id", "")
    amount = body.get("amount", 0.0)
    
    if contributor_id not in unit.family_members:
        raise HTTPException(400, "Contributor not in family group")
    
    # Enregistrer contribution
    unit.contributions[contributor_id] = amount
    unit.total_collected += amount
    
    # Vérifier si montant atteint
    if unit.total_collected >= unit.amount:
        unit.status = MedicalUnitStatus.COMPLETED
    
    return JSONResponse({
        "unit_id": unit_id,
        "contributor": contributor_id,
        "amount": amount,
        "total_collected": unit.total_collected,
        "target": unit.amount,
        "progress_percent": round((unit.total_collected / unit.amount) * 100, 1),
        "status": unit.status.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/medical-units/{unit_id}/transfer")
async def transfer_medical_unit(unit_id: str, request: Request):
    """Transfère les fonds au bénéficiaire"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    if unit_id not in medical_units_db:
        raise HTTPException(404, "Medical unit not found")
    
    unit = medical_units_db[unit_id]
    
    # Calculer frais
    fee = unit.total_collected * (unit.fee_percent / 100)
    amount_to_transfer = unit.total_collected - fee
    
    # Vérifier assurance
    if unit.total_collected < unit.amount:
        insurance_coverage = unit.amount - unit.total_collected
        unit.insurance_coverage = insurance_coverage
        amount_to_transfer = unit.amount - fee
    
    unit.transferred_at = datetime.now(timezone.utc).isoformat()
    unit.status = MedicalUnitStatus.COMPLETED
    
    return JSONResponse({
        "unit_id": unit_id,
        "beneficiary": unit.beneficiary_id,
        "total_collected": unit.total_collected,
        "fee_usd": fee,
        "insurance_coverage": unit.insurance_coverage,
        "amount_transferred": amount_to_transfer,
        "status": "transferred",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/medical-units/{unit_id}")
async def get_medical_unit(unit_id: str):
    """Récupère les détails d'une unité médicale"""
    if unit_id not in medical_units_db:
        raise HTTPException(404, "Medical unit not found")
    
    unit = medical_units_db[unit_id]
    
    return JSONResponse({
        "unit": asdict(unit),
        "progress": {
            "collected": unit.total_collected,
            "target": unit.amount,
            "percent": round((unit.total_collected / unit.amount) * 100, 1),
            "contributors": len(unit.contributions),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/medical-units/user/{user_id}")
async def get_user_medical_units(user_id: str):
    """Récupère les unités médicales d'un utilisateur"""
    
    # Unités créées par l'utilisateur
    created = [u for u in medical_units_db.values() if u.initiator_id == user_id]
    
    # Unités où l'utilisateur est bénéficiaire
    beneficiary = [u for u in medical_units_db.values() if u.beneficiary_id == user_id]
    
    # Unités où l'utilisateur a contribué
    contributed = [u for u in medical_units_db.values() if user_id in u.contributions]
    
    return JSONResponse({
        "user_id": user_id,
        "created": [asdict(u) for u in created],
        "beneficiary": [asdict(u) for u in beneficiary],
        "contributed": [asdict(u) for u in contributed],
        "total_created": len(created),
        "total_beneficiary": len(beneficiary),
        "total_contributed": len(contributed),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENDPOINTS - PREUVE MÉDICALE
# ============================================================================

@app.post("/medical-units/{unit_id}/upload-proof")
async def upload_medical_proof(unit_id: str, request: Request):
    """Upload une preuve médicale"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    if unit_id not in medical_units_db:
        raise HTTPException(404, "Medical unit not found")
    
    proof = MedicalProof(
        unit_id=unit_id,
        proof_type=ProofType(body.get("proof_type", "prescription")),
        file_url=body.get("file_url", ""),
        doctor_name=body.get("doctor_name", ""),
        hospital=body.get("hospital", ""),
        date=body.get("date", ""),
        amount=body.get("amount", 0.0),
    )
    
    # Simulation OCR
    proof.ocr_text = f"Ordonnance du Dr. {proof.doctor_name} - {proof.hospital} - {proof.date} - Montant: ${proof.amount}"
    proof.verified = True
    
    medical_proofs_db[proof.proof_id] = proof
    
    # Mettre à jour unité médicale
    unit = medical_units_db[unit_id]
    unit.medical_proof_url = proof.file_url
    
    return JSONResponse({
        "proof_id": proof.proof_id,
        "unit_id": unit_id,
        "proof_type": proof.proof_type.value,
        "verified": proof.verified,
        "ocr_text": proof.ocr_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/medical-units/{unit_id}/proof")
async def get_medical_proof(unit_id: str):
    """Récupère la preuve médicale d'une unité"""
    proofs = [p for p in medical_proofs_db.values() if p.unit_id == unit_id]
    
    if not proofs:
        raise HTTPException(404, "No proof found")
    
    proof = proofs[0]
    
    return JSONResponse({
        "proof": asdict(proof),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENDPOINTS - DOSSIER MÉDICAL
# ============================================================================

@app.get("/medical-records/{user_id}")
async def get_medical_records(user_id: str):
    """Récupère le dossier médical d'un utilisateur"""
    records = medical_records_db.get(user_id, [])
    
    return JSONResponse({
        "user_id": user_id,
        "records": [asdict(r) for r in records],
        "total": len(records),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/medical-records/create")
async def create_medical_record(request: Request):
    """Crée un enregistrement médical"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    user_id = body.get("user_id", "")
    
    record = MedicalRecord(
        user_id=user_id,
        unit_id=body.get("unit_id", ""),
        date=body.get("date", datetime.now(timezone.utc).isoformat()),
        type=body.get("type", ""),
        reason=body.get("reason", ""),
        amount=body.get("amount", 0.0),
        hospital=body.get("hospital", ""),
        doctor=body.get("doctor", ""),
        diagnosis=body.get("diagnosis", ""),
        treatment=body.get("treatment", ""),
    )
    
    if user_id not in medical_records_db:
        medical_records_db[user_id] = []
    
    medical_records_db[user_id].append(record)
    
    return JSONResponse({
        "record_id": record.record_id,
        "user_id": user_id,
        "status": "created",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENDPOINTS - GROUPES FAMILIAUX
# ============================================================================

@app.post("/family-groups/create")
async def create_family_group(request: Request):
    """Crée un groupe familial"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    group = FamilyGroup(
        name=body.get("name", ""),
        members=body.get("members", []),
        admin_id=body.get("admin_id", ""),
    )
    
    family_groups_db[group.group_id] = group
    
    return JSONResponse({
        "group_id": group.group_id,
        "group": asdict(group),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/family-groups/{group_id}")
async def get_family_group(group_id: str):
    """Récupère les détails d'un groupe familial"""
    if group_id not in family_groups_db:
        raise HTTPException(404, "Family group not found")
    
    group = family_groups_db[group_id]
    
    # Statistiques
    units = [u for u in medical_units_db.values() if group_id in u.family_members]
    
    return JSONResponse({
        "group": asdict(group),
        "statistics": {
            "total_units": len(units),
            "total_collected": sum(u.total_collected for u in units),
            "active_units": len([u for u in units if u.status == MedicalUnitStatus.ACTIVE]),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENDPOINTS - DASHBOARD
# ============================================================================

@app.get("/medical-units/dashboard/{user_id}")
async def get_medical_dashboard(user_id: str):
    """Dashboard unités médicales"""
    
    # Unités créées
    created = [u for u in medical_units_db.values() if u.initiator_id == user_id]
    
    # Unités où bénéficiaire
    beneficiary = [u for u in medical_units_db.values() if u.beneficiary_id == user_id]
    
    # Unités où contributeur
    contributed = [u for u in medical_units_db.values() if user_id in u.contributions]
    
    # Dossier médical
    records = medical_records_db.get(user_id, [])
    
    return JSONResponse({
        "user_id": user_id,
        "dashboard": {
            "created_units": {
                "total": len(created),
                "active": len([u for u in created if u.status == MedicalUnitStatus.ACTIVE]),
                "completed": len([u for u in created if u.status == MedicalUnitStatus.COMPLETED]),
                "total_amount": sum(u.amount for u in created),
            },
            "beneficiary_units": {
                "total": len(beneficiary),
                "active": len([u for u in beneficiary if u.status == MedicalUnitStatus.ACTIVE]),
                "completed": len([u for u in beneficiary if u.status == MedicalUnitStatus.COMPLETED]),
                "total_received": sum(u.total_collected for u in beneficiary),
            },
            "contributions": {
                "total": len(contributed),
                "total_amount": sum(u.contributions.get(user_id, 0) for u in contributed),
                "average_contribution": round(sum(u.contributions.get(user_id, 0) for u in contributed) / max(len(contributed), 1), 2),
            },
            "medical_records": {
                "total": len(records),
                "last_record": records[-1].date if records else None,
            },
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/medical-units/stats")
async def get_medical_stats():
    """Statistiques globales"""
    return JSONResponse({
        "platform": "HCS Medical Units",
        "stats": {
            "total_units": len(medical_units_db),
            "total_collected": sum(u.total_collected for u in medical_units_db.values()),
            "total_amount_requested": sum(u.amount for u in medical_units_db.values()),
            "active_units": len([u for u in medical_units_db.values() if u.status == MedicalUnitStatus.ACTIVE]),
            "completed_units": len([u for u in medical_units_db.values() if u.status == MedicalUnitStatus.COMPLETED]),
            "emergency_units": len([u for u in medical_units_db.values() if u.type == MedicalUnitType.EMERGENCY]),
            "chronic_units": len([u for u in medical_units_db.values() if u.type == MedicalUnitType.CHRONIC]),
            "prevention_units": len([u for u in medical_units_db.values() if u.type == MedicalUnitType.PREVENTION]),
            "total_families": len(family_groups_db),
            "total_medical_records": sum(len(r) for r in medical_records_db.values()),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENTREE PRINCIPALE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=9022, access_log=False)

