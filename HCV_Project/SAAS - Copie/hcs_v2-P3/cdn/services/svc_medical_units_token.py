"""
HCS Medical Units Token Service
================================
Système d'unités médicales comme tokens de valeur

Port: 9023
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

class ConversionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class MedicalUnit:
    """Unité médicale (token)"""
    unit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    initiator_id: str = ""
    beneficiary_id: str = ""
    type: MedicalUnitType = MedicalUnitType.EMERGENCY
    amount_um: float = 0.0  # Montant en UM (tokens)
    value_usd: float = 0.0  # Valeur équivalente en USD
    reason: str = ""
    medical_proof_url: str = ""
    hospital: str = ""
    duration_days: int = 7
    frequency: str = "once"
    family_members: List[str] = field(default_factory=list)
    contributions_um: Dict[str, float] = field(default_factory=dict)
    total_collected_um: float = 0.0
    status: MedicalUnitStatus = MedicalUnitStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    deadline: str = ""
    transferred_at: Optional[str] = None
    insurance_coverage_um: float = 0.0
    fee_percent: float = 1.0
    notes: str = ""

@dataclass
class MedicalUnitWallet:
    """Portefeuille d'unités médicales"""
    wallet_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    balance_um: float = 0.0  # Solde en UM
    value_usd: float = 0.0  # Valeur équivalente en USD
    transactions: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class MedicalUnitConversion:
    """Conversion UM → Argent réel (pour prestataires)"""
    conversion_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider_id: str = ""
    amount_um: float = 0.0  # Montant en UM
    value_usd: float = 0.0  # Valeur en USD
    fee_percent: float = 1.5
    fee_usd: float = 0.0
    amount_to_transfer: float = 0.0
    currency: str = "USD"
    amount_local: float = 0.0
    status: ConversionStatus = ConversionStatus.PENDING
    bank_account: str = ""
    payment_method: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

@dataclass
class Provider:
    """Prestataire partenaire (hôpital, pharmacie, etc)"""
    provider_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    provider_type: str = ""  # hospital, clinic, pharmacy, lab, dental
    country: str = ""
    city: str = ""
    phone: str = ""
    email: str = ""
    bank_account: str = ""
    payment_method: str = ""  # bank_transfer, mpesa, airtel, orange
    accepted_um: bool = True
    conversion_fee_percent: float = 1.5
    verified: bool = False
    um_wallet_id: str = ""
    balance_um: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============================================================================
# STORAGE (In-Memory pour démo)
# ============================================================================

medical_units_db: Dict[str, MedicalUnit] = {}
wallets_db: Dict[str, MedicalUnitWallet] = {}
conversions_db: Dict[str, MedicalUnitConversion] = {}
providers_db: Dict[str, Provider] = {}

# Taux de change (mis à jour quotidiennement)
EXCHANGE_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "XOF": 600.0,  # Franc CFA Ouest
    "XAF": 600.0,  # Franc CFA Est
    "KES": 130.0,  # Shilling kényan
    "NGN": 410.0,  # Naira nigérian
    "ZAR": 18.5,   # Rand sud-africain
    "GHS": 12.5,   # Cedi ghanéen
}

# Valeur de base: 1 UM = $10 USD
UM_VALUE_USD = 10.0

# ============================================================================
# APP
# ============================================================================

app = FastAPI(title="HCS Medical Units Token Service", version="1.0.0")

# ============================================================================
# ENDPOINTS - UNITÉS MÉDICALES (TOKENS)
# ============================================================================

@app.post("/medical-units/create")
async def create_medical_unit(request: Request):
    """Crée une unité médicale (tokens)"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    amount_um = body.get("amount_um", 0.0)
    value_usd = amount_um * UM_VALUE_USD
    
    unit = MedicalUnit(
        initiator_id=body.get("initiator_id", ""),
        beneficiary_id=body.get("beneficiary_id", ""),
        type=MedicalUnitType(body.get("type", "emergency")),
        amount_um=amount_um,
        value_usd=value_usd,
        reason=body.get("reason", ""),
        hospital=body.get("hospital", ""),
        duration_days=body.get("duration_days", 7),
        frequency=body.get("frequency", "once"),
        family_members=body.get("family_members", []),
    )
    
    # Calculer deadline et frais
    if unit.type == MedicalUnitType.EMERGENCY:
        unit.deadline = (datetime.now(timezone.utc) + timedelta(days=unit.duration_days)).isoformat()
        unit.fee_percent = 2.0
    else:
        unit.deadline = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        unit.fee_percent = 1.0
    
    medical_units_db[unit.unit_id] = unit
    
    return JSONResponse({
        "status": "created",
        "unit_id": unit.unit_id,
        "amount_um": unit.amount_um,
        "value_usd": unit.value_usd,
        "type": unit.type.value,
        "deadline": unit.deadline,
        "notifications_sent": len(unit.family_members),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/medical-units/{unit_id}/contribute")
async def contribute_to_unit(unit_id: str, request: Request):
    """Contribue à une unité médicale (en UM)"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    if unit_id not in medical_units_db:
        raise HTTPException(404, "Medical unit not found")
    
    unit = medical_units_db[unit_id]
    contributor_id = body.get("contributor_id", "")
    amount_um = body.get("amount_um", 0.0)
    
    if contributor_id not in unit.family_members:
        raise HTTPException(400, "Contributor not in family group")
    
    # Enregistrer contribution en UM
    unit.contributions_um[contributor_id] = amount_um
    unit.total_collected_um += amount_um
    
    # Vérifier si montant atteint
    if unit.total_collected_um >= unit.amount_um:
        unit.status = MedicalUnitStatus.COMPLETED
    
    return JSONResponse({
        "unit_id": unit_id,
        "contributor": contributor_id,
        "amount_um": amount_um,
        "value_usd": amount_um * UM_VALUE_USD,
        "total_collected_um": unit.total_collected_um,
        "target_um": unit.amount_um,
        "progress_percent": round((unit.total_collected_um / unit.amount_um) * 100, 1),
        "status": unit.status.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/medical-units/{unit_id}/transfer")
async def transfer_medical_unit(unit_id: str, request: Request):
    """Transfère les UM au bénéficiaire"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    if unit_id not in medical_units_db:
        raise HTTPException(404, "Medical unit not found")
    
    unit = medical_units_db[unit_id]
    beneficiary_id = unit.beneficiary_id
    
    # Créer/mettre à jour portefeuille bénéficiaire
    if beneficiary_id not in wallets_db:
        wallet = MedicalUnitWallet(user_id=beneficiary_id)
        wallets_db[wallet.wallet_id] = wallet
    else:
        wallet = list(w for w in wallets_db.values() if w.user_id == beneficiary_id)[0]
    
    # Ajouter UM au portefeuille
    wallet.balance_um += unit.total_collected_um
    wallet.value_usd = wallet.balance_um * UM_VALUE_USD
    
    # Enregistrer transaction
    wallet.transactions.append({
        "date": datetime.now(timezone.utc).isoformat(),
        "type": "received",
        "unit_id": unit_id,
        "amount_um": unit.total_collected_um,
        "value_usd": unit.total_collected_um * UM_VALUE_USD,
        "reason": unit.reason,
    })
    
    unit.transferred_at = datetime.now(timezone.utc).isoformat()
    unit.status = MedicalUnitStatus.COMPLETED
    
    return JSONResponse({
        "unit_id": unit_id,
        "beneficiary": beneficiary_id,
        "total_collected_um": unit.total_collected_um,
        "value_usd": unit.total_collected_um * UM_VALUE_USD,
        "status": "transferred",
        "beneficiary_wallet": {
            "balance_um": wallet.balance_um,
            "value_usd": wallet.value_usd,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/medical-units/{unit_id}")
async def get_medical_unit(unit_id: str):
    """Récupère les détails d'une unité médicale"""
    if unit_id not in medical_units_db:
        raise HTTPException(404, "Medical unit not found")
    
    unit = medical_units_db[unit_id]
    
    return JSONResponse({
        "unit_id": unit_id,
        "amount_um": unit.amount_um,
        "value_usd": unit.value_usd,
        "collected_um": unit.total_collected_um,
        "collected_usd": unit.total_collected_um * UM_VALUE_USD,
        "progress_percent": round((unit.total_collected_um / unit.amount_um) * 100, 1),
        "contributors": len(unit.contributions_um),
        "status": unit.status.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENDPOINTS - PORTEFEUILLE D'UNITÉS MÉDICALES
# ============================================================================

@app.get("/wallet/{user_id}")
async def get_wallet(user_id: str):
    """Récupère le portefeuille d'UM d'un utilisateur"""
    user_wallets = [w for w in wallets_db.values() if w.user_id == user_id]
    
    if not user_wallets:
        return JSONResponse({
            "user_id": user_id,
            "balance_um": 0.0,
            "value_usd": 0.0,
            "transactions": [],
        })
    
    wallet = user_wallets[0]
    
    return JSONResponse({
        "user_id": user_id,
        "balance_um": wallet.balance_um,
        "value_usd": wallet.value_usd,
        "transactions": wallet.transactions[-20:],  # Dernières 20 transactions
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/wallet/{user_id}/use-units")
async def use_medical_units(user_id: str, request: Request):
    """Utilise des UM pour payer chez un prestataire"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    user_wallets = [w for w in wallets_db.values() if w.user_id == user_id]
    if not user_wallets:
        raise HTTPException(404, "Wallet not found")
    
    wallet = user_wallets[0]
    provider_id = body.get("provider_id", "")
    amount_um = body.get("amount_um", 0.0)
    
    if provider_id not in providers_db:
        raise HTTPException(404, "Provider not found")
    
    if wallet.balance_um < amount_um:
        raise HTTPException(400, "Insufficient UM balance")
    
    provider = providers_db[provider_id]
    
    # Déduire UM du portefeuille utilisateur
    wallet.balance_um -= amount_um
    wallet.value_usd = wallet.balance_um * UM_VALUE_USD
    
    # Ajouter UM au portefeuille prestataire
    provider.balance_um += amount_um
    
    # Enregistrer transaction
    wallet.transactions.append({
        "date": datetime.now(timezone.utc).isoformat(),
        "type": "spent",
        "provider_id": provider_id,
        "provider_name": provider.name,
        "amount_um": amount_um,
        "value_usd": amount_um * UM_VALUE_USD,
    })
    
    return JSONResponse({
        "status": "success",
        "user_id": user_id,
        "provider": provider.name,
        "amount_um": amount_um,
        "value_usd": amount_um * UM_VALUE_USD,
        "remaining_balance_um": wallet.balance_um,
        "remaining_value_usd": wallet.value_usd,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENDPOINTS - PRESTATAIRES PARTENAIRES
# ============================================================================

@app.post("/providers/register")
async def register_provider(request: Request):
    """Enregistre un prestataire partenaire"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    provider = Provider(
        name=body.get("provider_name", ""),
        provider_type=body.get("provider_type", ""),
        country=body.get("country", ""),
        city=body.get("city", ""),
        phone=body.get("phone", ""),
        email=body.get("email", ""),
        bank_account=body.get("bank_account", ""),
        payment_method=body.get("payment_method", "bank_transfer"),
        conversion_fee_percent=body.get("conversion_fee_percent", 1.5),
    )
    
    providers_db[provider.provider_id] = provider
    
    return JSONResponse({
        "provider_id": provider.provider_id,
        "status": "registered",
        "verified": False,
        "um_wallet_balance": 0.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/providers/{provider_id}")
async def get_provider(provider_id: str):
    """Récupère les détails d'un prestataire"""
    if provider_id not in providers_db:
        raise HTTPException(404, "Provider not found")
    
    provider = providers_db[provider_id]
    
    return JSONResponse({
        "provider_id": provider_id,
        "name": provider.name,
        "type": provider.provider_type,
        "country": provider.country,
        "city": provider.city,
        "verified": provider.verified,
        "balance_um": provider.balance_um,
        "value_usd": provider.balance_um * UM_VALUE_USD,
        "conversion_fee_percent": provider.conversion_fee_percent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENDPOINTS - CONVERSION UM → ARGENT RÉEL
# ============================================================================

@app.post("/providers/{provider_id}/convert-um")
async def convert_um_to_cash(provider_id: str, request: Request):
    """Convertit UM en argent réel (pour prestataire)"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    if provider_id not in providers_db:
        raise HTTPException(404, "Provider not found")
    
    provider = providers_db[provider_id]
    amount_um = body.get("amount_um", 0.0)
    currency = body.get("currency", "USD")
    
    if provider.balance_um < amount_um:
        raise HTTPException(400, "Insufficient UM balance")
    
    # Calculer montants
    value_usd = amount_um * UM_VALUE_USD
    fee_usd = value_usd * (provider.conversion_fee_percent / 100)
    amount_to_transfer = value_usd - fee_usd
    
    # Convertir en devise locale
    exchange_rate = EXCHANGE_RATES.get(currency, 1.0)
    amount_local = amount_to_transfer * exchange_rate
    
    # Créer conversion
    conversion = MedicalUnitConversion(
        provider_id=provider_id,
        amount_um=amount_um,
        value_usd=value_usd,
        fee_percent=provider.conversion_fee_percent,
        fee_usd=fee_usd,
        amount_to_transfer=amount_to_transfer,
        currency=currency,
        amount_local=amount_local,
        bank_account=provider.bank_account,
        payment_method=provider.payment_method,
    )
    
    conversions_db[conversion.conversion_id] = conversion
    
    # Déduire UM du portefeuille prestataire
    provider.balance_um -= amount_um
    
    return JSONResponse({
        "conversion_id": conversion.conversion_id,
        "status": "pending",
        "amount_um": amount_um,
        "value_usd": value_usd,
        "fee_usd": fee_usd,
        "amount_to_transfer": amount_to_transfer,
        "currency": currency,
        "amount_local": amount_local,
        "exchange_rate": exchange_rate,
        "payment_method": provider.payment_method,
        "estimated_arrival": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/conversions/{conversion_id}")
async def get_conversion(conversion_id: str):
    """Récupère le statut d'une conversion"""
    if conversion_id not in conversions_db:
        raise HTTPException(404, "Conversion not found")
    
    conversion = conversions_db[conversion_id]
    
    return JSONResponse({
        "conversion_id": conversion_id,
        "status": conversion.status.value,
        "amount_um": conversion.amount_um,
        "value_usd": conversion.value_usd,
        "fee_usd": conversion.fee_usd,
        "amount_to_transfer": conversion.amount_to_transfer,
        "currency": conversion.currency,
        "amount_local": conversion.amount_local,
        "payment_method": conversion.payment_method,
        "created_at": conversion.created_at,
        "completed_at": conversion.completed_at,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENDPOINTS - TAUX DE CHANGE
# ============================================================================

@app.get("/exchange-rates")
async def get_exchange_rates():
    """Récupère les taux de change actuels"""
    return JSONResponse({
        "um_value_usd": UM_VALUE_USD,
        "rates": EXCHANGE_RATES,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENDPOINTS - STATISTIQUES
# ============================================================================

@app.get("/stats")
async def get_stats():
    """Statistiques globales"""
    total_um_created = sum(u.amount_um for u in medical_units_db.values())
    total_um_collected = sum(u.total_collected_um for u in medical_units_db.values())
    total_um_converted = sum(c.amount_um for c in conversions_db.values() if c.status == ConversionStatus.COMPLETED)
    
    return JSONResponse({
        "platform": "HCS Medical Units Token",
        "stats": {
            "total_units": len(medical_units_db),
            "total_um_created": total_um_created,
            "total_um_value_usd": total_um_created * UM_VALUE_USD,
            "total_um_collected": total_um_collected,
            "total_um_converted": total_um_converted,
            "active_units": len([u for u in medical_units_db.values() if u.status == MedicalUnitStatus.ACTIVE]),
            "completed_units": len([u for u in medical_units_db.values() if u.status == MedicalUnitStatus.COMPLETED]),
            "total_providers": len(providers_db),
            "total_wallets": len(wallets_db),
            "total_conversions": len(conversions_db),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENTREE PRINCIPALE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=9023, access_log=False)

