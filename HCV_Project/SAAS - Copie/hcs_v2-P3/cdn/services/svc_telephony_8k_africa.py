"""
HCS Telephony 8K - Module Afrique
==================================
Super-app africaine avec:
- Transfert d'argent instantané (0.5% frais)
- Tontine digitale (1% frais)
- Télémédecine (consultation $5-$20)

Port: 9020 (partagé)
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

from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ============================================================================
# MODELS
# ============================================================================

class PaymentMethod(str, Enum):
    MPESA = "mpesa"
    AIRTEL_MONEY = "airtel_money"
    ORANGE_MONEY = "orange_money"
    VODAFONE_CASH = "vodafone_cash"
    CRYPTO = "crypto"
    BANK = "bank"

class TontineFrequency(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"

class MedicalSpecialty(str, Enum):
    GENERAL_PRACTITIONER = "general_practitioner"
    CARDIOLOGIST = "cardiologist"
    PEDIATRICIAN = "pediatrician"
    GYNECOLOGIST = "gynecologist"
    DERMATOLOGIST = "dermatologist"
    PHARMACIST = "pharmacist"

@dataclass
class AfricaPayment:
    """Modèle de paiement africain"""
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    method: PaymentMethod = PaymentMethod.MPESA
    status: str = "completed"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    fee_usd: float = 0.0
    recipient_country: str = ""
    confirmation_code: str = field(default_factory=lambda: f"{uuid.uuid4().hex[:8].upper()}")

@dataclass
class Tontine:
    """Modèle de tontine digitale"""
    tontine_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    members: List[str] = field(default_factory=list)
    contribution_amount: float = 0.0
    currency: str = "USD"
    frequency: TontineFrequency = TontineFrequency.MONTHLY
    cycle_duration_months: int = 12
    rotation_type: str = "random"  # ou "sequential"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    total_pot: float = 0.0
    next_distribution: str = ""
    next_recipient: str = ""
    insurance: bool = True
    insurance_coverage: float = 0.0
    fee_monthly: float = 0.0
    transactions: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class MedicalAppointment:
    """Modèle de consultation médicale"""
    appointment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    doctor_id: str = ""
    specialty: MedicalSpecialty = MedicalSpecialty.GENERAL_PRACTITIONER
    language: str = "fr"
    scheduled_time: str = ""
    status: str = "scheduled"  # scheduled, completed, cancelled
    cost: float = 10.0
    currency: str = "USD"
    symptoms: str = ""
    diagnosis: str = ""
    prescription: str = ""
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class Doctor:
    """Modèle de médecin"""
    doctor_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    specialty: MedicalSpecialty = MedicalSpecialty.GENERAL_PRACTITIONER
    country: str = ""
    language: str = "fr"
    verified: bool = False
    rating: float = 4.5
    consultations: int = 0
    cost_per_consultation: float = 10.0
    availability: str = "9am-5pm"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============================================================================
# STORAGE (In-Memory pour démo)
# ============================================================================

payments_db: Dict[str, AfricaPayment] = {}
tontines_db: Dict[str, Tontine] = {}
appointments_db: Dict[str, MedicalAppointment] = {}
doctors_db: Dict[str, Doctor] = {}
medical_records_db: Dict[str, List[Dict[str, Any]]] = {}

# ============================================================================
# APP
# ============================================================================

app = FastAPI(title="HCS Telephony 8K Africa", version="1.0.0")

# ============================================================================
# ENDPOINTS - TRANSFERT D'ARGENT AFRICAIN
# ============================================================================

@app.post("/payment/send-africa")
async def send_payment_africa(request: Request):
    """
    Envoie de l'argent en Afrique avec frais réduits (0.5%)
    
    Body:
    {
        "sender_id": "user_alice",
        "recipient_id": "user_bob",
        "amount": 100.00,
        "currency": "USD",
        "recipient_country": "Senegal",
        "method": "mpesa",
        "note": "Remboursement"
    }
    """
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    amount = body.get("amount", 0.0)
    fee = amount * 0.005  # 0.5% frais
    
    payment = AfricaPayment(
        sender_id=body.get("sender_id", ""),
        recipient_id=body.get("recipient_id", ""),
        amount=amount,
        currency=body.get("currency", "USD"),
        method=PaymentMethod(body.get("method", "mpesa")),
        recipient_country=body.get("recipient_country", ""),
        fee_usd=fee,
    )
    
    payments_db[payment.transaction_id] = payment
    
    return JSONResponse({
        "status": "completed",
        "transaction_id": payment.transaction_id,
        "amount": amount,
        "fee_usd": fee,
        "recipient_received": amount - fee,
        "confirmation_code": payment.confirmation_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/payment/history-africa")
async def get_payment_history_africa(user_id: str = Query("")):
    """Historique des paiements africains"""
    user_payments = [
        p for p in payments_db.values()
        if p.sender_id == user_id or p.recipient_id == user_id
    ]
    
    return JSONResponse({
        "user_id": user_id,
        "transactions": [asdict(p) for p in user_payments[-50:]],
        "total": len(user_payments),
        "total_sent": sum(p.amount for p in user_payments if p.sender_id == user_id),
        "total_received": sum(p.amount for p in user_payments if p.recipient_id == user_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/payment/rates")
async def get_exchange_rates():
    """Taux de change africains"""
    return JSONResponse({
        "rates": {
            "USD": 1.0,
            "EUR": 0.92,
            "GBP": 0.79,
            "XOF": 600.0,  # Franc CFA Ouest
            "XAF": 600.0,  # Franc CFA Est
            "KES": 130.0,  # Shilling kényan
            "NGN": 410.0,  # Naira nigérian
            "ZAR": 18.5,   # Rand sud-africain
            "GHS": 12.5,   # Cedi ghanéen
            "BTC": 0.000025,  # Bitcoin
            "ETH": 0.00055,   # Ethereum
            "USDC": 1.0,      # USD Coin
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENDPOINTS - TONTINE DIGITALE
# ============================================================================

@app.post("/tontine/create")
async def create_tontine(request: Request):
    """Crée une tontine digitale"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    members = body.get("members", [])
    contribution = body.get("contribution_amount", 0.0)
    
    tontine = Tontine(
        name=body.get("name", ""),
        members=members,
        contribution_amount=contribution,
        currency=body.get("currency", "USD"),
        frequency=TontineFrequency(body.get("frequency", "monthly")),
        cycle_duration_months=body.get("cycle_duration_months", 12),
        rotation_type=body.get("rotation_type", "random"),
        insurance=body.get("insurance", True),
        total_pot=contribution * len(members),
        insurance_coverage=contribution * len(members),
        fee_monthly=contribution * len(members) * 0.01,  # 1%
    )
    
    # Calculer prochaine distribution
    tontine.next_distribution = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    tontine.next_recipient = members[0] if members else ""
    
    tontines_db[tontine.tontine_id] = tontine
    
    return JSONResponse({
        "status": "created",
        "tontine": asdict(tontine),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/tontine/{tontine_id}/contribute")
async def contribute_to_tontine(tontine_id: str, request: Request):
    """Contribue à une tontine"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    if tontine_id not in tontines_db:
        raise HTTPException(404, "Tontine not found")
    
    tontine = tontines_db[tontine_id]
    user_id = body.get("user_id", "")
    amount = body.get("amount", tontine.contribution_amount)
    
    if user_id not in tontine.members:
        raise HTTPException(400, "User not member of tontine")
    
    transaction = {
        "date": datetime.now(timezone.utc).isoformat(),
        "contributor": user_id,
        "amount": amount,
        "status": "confirmed",
        "hash": uuid.uuid4().hex[:16],
    }
    
    tontine.transactions.append(transaction)
    tontine.total_pot += amount
    
    return JSONResponse({
        "tontine_id": tontine_id,
        "transaction": transaction,
        "total_pot": tontine.total_pot,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/tontine/{tontine_id}/history")
async def get_tontine_history(tontine_id: str):
    """Historique d'une tontine"""
    if tontine_id not in tontines_db:
        raise HTTPException(404, "Tontine not found")
    
    tontine = tontines_db[tontine_id]
    
    return JSONResponse({
        "tontine_id": tontine_id,
        "name": tontine.name,
        "members": len(tontine.members),
        "total_pot": tontine.total_pot,
        "transactions": tontine.transactions,
        "next_distribution": tontine.next_distribution,
        "next_recipient": tontine.next_recipient,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/tontine/{tontine_id}/claim")
async def claim_tontine_distribution(tontine_id: str, request: Request):
    """Réclame la distribution de tontine"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    if tontine_id not in tontines_db:
        raise HTTPException(404, "Tontine not found")
    
    tontine = tontines_db[tontine_id]
    user_id = body.get("user_id", "")
    
    if user_id != tontine.next_recipient:
        raise HTTPException(400, "Not eligible for distribution")
    
    amount = tontine.total_pot - tontine.fee_monthly
    
    return JSONResponse({
        "tontine_id": tontine_id,
        "recipient": user_id,
        "amount": amount,
        "fee": tontine.fee_monthly,
        "insurance_coverage": tontine.insurance_coverage,
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENDPOINTS - TÉLÉMÉDECINE
# ============================================================================

@app.post("/telemedicine/appointment/book")
async def book_appointment(request: Request):
    """Réserve une consultation médicale"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    appointment = MedicalAppointment(
        user_id=body.get("user_id", ""),
        specialty=MedicalSpecialty(body.get("specialty", "general_practitioner")),
        language=body.get("language", "fr"),
        scheduled_time=body.get("preferred_time", ""),
        symptoms=body.get("symptoms", ""),
        cost=body.get("cost", 10.0),
    )
    
    # Assigner un médecin (simulation)
    available_doctors = [d for d in doctors_db.values() if d.specialty == appointment.specialty]
    if available_doctors:
        appointment.doctor_id = available_doctors[0].doctor_id
    
    appointments_db[appointment.appointment_id] = appointment
    
    return JSONResponse({
        "status": "booked",
        "appointment": asdict(appointment),
        "video_link": f"https://hcs.call/{appointment.appointment_id}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/telemedicine/appointment/{appointment_id}/start")
async def start_consultation(appointment_id: str, request: Request):
    """Démarre une consultation"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    if appointment_id not in appointments_db:
        raise HTTPException(404, "Appointment not found")
    
    appointment = appointments_db[appointment_id]
    appointment.status = "in_progress"
    
    return JSONResponse({
        "session_id": f"session_{uuid.uuid4().hex[:8]}",
        "appointment_id": appointment_id,
        "video_resolution": "8K",
        "audio_quality": "192kHz",
        "encryption": "AES-256-GCM",
        "recording": True,
        "duration_minutes": 30,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/telemedicine/prescription/create")
async def create_prescription(request: Request):
    """Crée une prescription"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    appointment_id = body.get("appointment_id", "")
    
    if appointment_id not in appointments_db:
        raise HTTPException(404, "Appointment not found")
    
    appointment = appointments_db[appointment_id]
    appointment.prescription = json.dumps(body.get("medications", []))
    appointment.notes = body.get("notes", "")
    appointment.status = "completed"
    
    # Enregistrer dans dossier médical
    if appointment.user_id not in medical_records_db:
        medical_records_db[appointment.user_id] = []
    
    record = {
        "date": datetime.now(timezone.utc).isoformat(),
        "doctor": appointment.doctor_id,
        "diagnosis": appointment.diagnosis,
        "prescription": appointment.prescription,
        "notes": appointment.notes,
    }
    
    medical_records_db[appointment.user_id].append(record)
    
    return JSONResponse({
        "status": "created",
        "prescription_id": f"rx_{uuid.uuid4().hex[:8]}",
        "appointment_id": appointment_id,
        "medications": body.get("medications", []),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/telemedicine/medical-record")
async def get_medical_record(user_id: str = Query("")):
    """Récupère le dossier médical"""
    records = medical_records_db.get(user_id, [])
    
    return JSONResponse({
        "user_id": user_id,
        "records": records,
        "total": len(records),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/telemedicine/doctors")
async def list_doctors(specialty: str = Query("general_practitioner"), language: str = Query("fr")):
    """Liste les médecins disponibles"""
    doctors = [
        d for d in doctors_db.values()
        if d.specialty.value == specialty and language in d.language
    ]
    
    return JSONResponse({
        "specialty": specialty,
        "language": language,
        "doctors": [asdict(d) for d in doctors],
        "total": len(doctors),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/telemedicine/doctor/register")
async def register_doctor(request: Request):
    """Enregistre un médecin"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    doctor = Doctor(
        name=body.get("name", ""),
        specialty=MedicalSpecialty(body.get("specialty", "general_practitioner")),
        country=body.get("country", ""),
        language=body.get("language", "fr"),
        verified=False,  # À vérifier manuellement
        cost_per_consultation=body.get("cost_per_consultation", 10.0),
    )
    
    doctors_db[doctor.doctor_id] = doctor
    
    return JSONResponse({
        "status": "registered",
        "doctor": asdict(doctor),
        "verification_required": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENDPOINTS - SUPER-APP AFRICAINE
# ============================================================================

@app.get("/africa/dashboard")
async def get_africa_dashboard(user_id: str = Query("")):
    """Dashboard super-app africaine"""
    
    # Statistiques utilisateur
    user_payments = [p for p in payments_db.values() if p.sender_id == user_id or p.recipient_id == user_id]
    user_tontines = [t for t in tontines_db.values() if user_id in t.members]
    user_appointments = [a for a in appointments_db.values() if a.user_id == user_id]
    
    return JSONResponse({
        "user_id": user_id,
        "dashboard": {
            "payments": {
                "total_sent": sum(p.amount for p in user_payments if p.sender_id == user_id),
                "total_received": sum(p.amount for p in user_payments if p.recipient_id == user_id),
                "transactions": len(user_payments),
                "fees_saved": sum(p.fee_usd for p in user_payments) * 5,  # vs 5% frais normaux
            },
            "tontines": {
                "active": len(user_tontines),
                "total_pot": sum(t.total_pot for t in user_tontines),
                "next_distribution": user_tontines[0].next_distribution if user_tontines else None,
            },
            "health": {
                "consultations": len(user_appointments),
                "medical_records": len(medical_records_db.get(user_id, [])),
                "last_consultation": user_appointments[-1].created_at if user_appointments else None,
            },
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/africa/stats")
async def get_africa_stats():
    """Statistiques globales Afrique"""
    return JSONResponse({
        "platform": "HCS Telephony 8K Africa",
        "stats": {
            "total_users": len(set(p.sender_id for p in payments_db.values())),
            "total_payments": len(payments_db),
            "total_volume": sum(p.amount for p in payments_db.values()),
            "total_fees_saved": sum(p.fee_usd for p in payments_db.values()) * 5,
            "active_tontines": len(tontines_db),
            "tontine_members": sum(len(t.members) for t in tontines_db.values()),
            "consultations": len(appointments_db),
            "doctors": len(doctors_db),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENTREE PRINCIPALE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    
    # Ajouter quelques médecins de démo
    demo_doctors = [
        Doctor(name="Dr. Diallo", specialty=MedicalSpecialty.GENERAL_PRACTITIONER, country="Senegal", language="fr"),
        Doctor(name="Dr. Okonkwo", specialty=MedicalSpecialty.PEDIATRICIAN, country="Nigeria", language="en"),
        Doctor(name="Dr. Mensah", specialty=MedicalSpecialty.CARDIOLOGIST, country="Ghana", language="en"),
    ]
    for doc in demo_doctors:
        doctors_db[doc.doctor_id] = doc
    
    uvicorn.run(app, host="0.0.0.0", port=9020, access_log=False)

