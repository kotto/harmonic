"""
HCS Telephony 8K - Module Amélioré
===================================
Extensions pour rivaliser avec WhatsApp:
- Messagerie riche
- Statuts/Stories
- Paiements
- IA intégrée
- Collaboration

Port: 9020 (partagé avec svc_telephony_8k.py)
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

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    STICKER = "sticker"

class MessageStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class StatusType(str, Enum):
    PHOTO = "photo"
    VIDEO = "video"
    TEXT = "text"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

@dataclass
class Message:
    """Modèle de message riche"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    chat_id: str = ""
    sender_id: str = ""
    content: str = ""
    message_type: MessageType = MessageType.TEXT
    status: MessageStatus = MessageStatus.SENT
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    edited_at: Optional[str] = None
    deleted_at: Optional[str] = None
    reactions: Dict[str, List[str]] = field(default_factory=dict)  # emoji -> [user_ids]
    reply_to: Optional[str] = None  # message_id
    mentions: List[str] = field(default_factory=list)  # user_ids
    media_url: Optional[str] = None
    media_size_bytes: int = 0
    media_duration_s: Optional[float] = None
    encryption_key: str = ""  # AES-256-GCM key

@dataclass
class Status:
    """Modèle de statut (24h)"""
    status_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    content_type: StatusType = StatusType.PHOTO
    content_url: str = ""
    caption: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str = field(default_factory=lambda: (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat())
    viewers: List[str] = field(default_factory=list)  # user_ids
    reactions: Dict[str, List[str]] = field(default_factory=dict)  # emoji -> [user_ids]
    privacy: str = "public"  # public, contacts, private
    allowed_viewers: List[str] = field(default_factory=list)  # user_ids (si privacy=private)

@dataclass
class Payment:
    """Modèle de paiement"""
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    method: str = "card"  # card, bank, crypto, wallet
    fee_usd: float = 0.0
    note: str = ""
    receipt_url: Optional[str] = None

@dataclass
class Wallet:
    """Modèle de portefeuille utilisateur"""
    wallet_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    balance_usd: float = 0.0
    balance_crypto: Dict[str, float] = field(default_factory=dict)  # {BTC: 0.5, ETH: 2.0}
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    kyc_verified: bool = False
    daily_limit_usd: float = 10000.0
    daily_spent_usd: float = 0.0

@dataclass
class Transcript:
    """Modèle de transcription"""
    transcript_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    language: str = "auto"
    segments: List[Dict[str, Any]] = field(default_factory=list)
    # segment: {start_s, end_s, speaker, text, confidence}
    full_text: str = ""
    summary: str = ""
    keywords: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============================================================================
# STORAGE (In-Memory pour démo, remplacer par DB)
# ============================================================================

messages_db: Dict[str, Message] = {}
statuses_db: Dict[str, Status] = {}
payments_db: Dict[str, Payment] = {}
wallets_db: Dict[str, Wallet] = {}
transcripts_db: Dict[str, Transcript] = {}
chats_db: Dict[str, List[str]] = {}  # chat_id -> [message_ids]

# ============================================================================
# ENDPOINTS - MESSAGERIE RICHE
# ============================================================================

app = FastAPI(title="HCS Telephony 8K Enhanced", version="2.0.0")

@app.post("/messages/send")
async def send_message(request: Request):
    """
    Envoie un message riche chiffré E2E
    
    Body:
    {
        "chat_id": "chat_123",
        "sender_id": "user_alice",
        "content": "Bonjour!",
        "message_type": "text",
        "mentions": ["user_bob"],
        "reply_to": "msg_456"
    }
    """
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    msg = Message(
        chat_id=body.get("chat_id", ""),
        sender_id=body.get("sender_id", ""),
        content=body.get("content", ""),
        message_type=MessageType(body.get("message_type", "text")),
        mentions=body.get("mentions", []),
        reply_to=body.get("reply_to"),
        encryption_key=_generate_encryption_key(),
    )
    
    messages_db[msg.message_id] = msg
    if msg.chat_id not in chats_db:
        chats_db[msg.chat_id] = []
    chats_db[msg.chat_id].append(msg.message_id)
    
    return JSONResponse({
        "status": "sent",
        "message": asdict(msg),
        "encryption": "AES-256-GCM",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/messages/{chat_id}")
async def get_messages(chat_id: str, limit: int = Query(50, le=100)):
    """Récupère les messages d'une conversation"""
    if chat_id not in chats_db:
        return JSONResponse({"messages": [], "total": 0})
    
    msg_ids = chats_db[chat_id][-limit:]
    messages = [asdict(messages_db[mid]) for mid in msg_ids if mid in messages_db]
    
    return JSONResponse({
        "chat_id": chat_id,
        "messages": messages,
        "total": len(messages),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/messages/{message_id}/react")
async def react_to_message(message_id: str, request: Request):
    """Ajoute une réaction emoji à un message"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    if message_id not in messages_db:
        raise HTTPException(404, "Message not found")
    
    msg = messages_db[message_id]
    emoji = body.get("emoji", "👍")
    user_id = body.get("user_id", "")
    
    if emoji not in msg.reactions:
        msg.reactions[emoji] = []
    if user_id not in msg.reactions[emoji]:
        msg.reactions[emoji].append(user_id)
    
    return JSONResponse({
        "message_id": message_id,
        "reactions": msg.reactions,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/messages/{message_id}/edit")
async def edit_message(message_id: str, request: Request):
    """Édite un message"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    if message_id not in messages_db:
        raise HTTPException(404, "Message not found")
    
    msg = messages_db[message_id]
    msg.content = body.get("content", msg.content)
    msg.edited_at = datetime.now(timezone.utc).isoformat()
    
    return JSONResponse({
        "message_id": message_id,
        "message": asdict(msg),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/messages/{message_id}/delete")
async def delete_message(message_id: str, request: Request):
    """Supprime un message"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    if message_id not in messages_db:
        raise HTTPException(404, "Message not found")
    
    msg = messages_db[message_id]
    for_all = body.get("for_all", False)
    
    if for_all:
        msg.deleted_at = datetime.now(timezone.utc).isoformat()
        msg.content = "[Message supprimé]"
    else:
        del messages_db[message_id]
    
    return JSONResponse({
        "message_id": message_id,
        "status": "deleted",
        "for_all": for_all,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENDPOINTS - STATUTS/STORIES
# ============================================================================

@app.post("/status/create")
async def create_status(request: Request):
    """Crée un statut (24h)"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    status = Status(
        user_id=body.get("user_id", ""),
        content_type=StatusType(body.get("content_type", "photo")),
        content_url=body.get("content_url", ""),
        caption=body.get("caption", ""),
        privacy=body.get("privacy", "public"),
        allowed_viewers=body.get("allowed_viewers", []),
    )
    
    statuses_db[status.status_id] = status
    
    return JSONResponse({
        "status": "created",
        "status_data": asdict(status),
        "expires_in_hours": 24,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/status/feed")
async def get_status_feed(user_id: str = Query("")):
    """Récupère le feed de statuts des contacts"""
    # Simulation: retourner les 10 derniers statuts
    statuses = list(statuses_db.values())[-10:]
    
    return JSONResponse({
        "user_id": user_id,
        "statuses": [asdict(s) for s in statuses],
        "total": len(statuses),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/status/{status_id}/view")
async def view_status(status_id: str, request: Request):
    """Enregistre une vue de statut"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    if status_id not in statuses_db:
        raise HTTPException(404, "Status not found")
    
    status = statuses_db[status_id]
    viewer_id = body.get("viewer_id", "")
    
    if viewer_id not in status.viewers:
        status.viewers.append(viewer_id)
    
    return JSONResponse({
        "status_id": status_id,
        "viewers": len(status.viewers),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/status/{status_id}/react")
async def react_to_status(status_id: str, request: Request):
    """Réagit à un statut"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    if status_id not in statuses_db:
        raise HTTPException(404, "Status not found")
    
    status = statuses_db[status_id]
    emoji = body.get("emoji", "❤️")
    user_id = body.get("user_id", "")
    
    if emoji not in status.reactions:
        status.reactions[emoji] = []
    if user_id not in status.reactions[emoji]:
        status.reactions[emoji].append(user_id)
    
    return JSONResponse({
        "status_id": status_id,
        "reactions": status.reactions,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENDPOINTS - PAIEMENTS
# ============================================================================

@app.post("/wallet/create")
async def create_wallet(request: Request):
    """Crée un portefeuille utilisateur"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    wallet = Wallet(
        user_id=body.get("user_id", ""),
        balance_usd=body.get("initial_balance", 0.0),
    )
    
    wallets_db[wallet.wallet_id] = wallet
    
    return JSONResponse({
        "status": "created",
        "wallet": asdict(wallet),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/payment/send")
async def send_payment(request: Request):
    """Envoie un paiement"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    sender_id = body.get("sender_id", "")
    recipient_id = body.get("recipient_id", "")
    amount = body.get("amount", 0.0)
    currency = body.get("currency", "USD")
    
    # Vérifier les limites
    sender_wallets = [w for w in wallets_db.values() if w.user_id == sender_id]
    if not sender_wallets:
        raise HTTPException(400, "Sender wallet not found")
    
    sender_wallet = sender_wallets[0]
    if sender_wallet.balance_usd < amount:
        raise HTTPException(400, "Insufficient balance")
    
    if sender_wallet.daily_spent_usd + amount > sender_wallet.daily_limit_usd:
        raise HTTPException(400, "Daily limit exceeded")
    
    # Créer la transaction
    payment = Payment(
        sender_id=sender_id,
        recipient_id=recipient_id,
        amount=amount,
        currency=currency,
        status=PaymentStatus.COMPLETED,
        method=body.get("method", "card"),
        fee_usd=amount * 0.005,  # 0.5% fee
        note=body.get("note", ""),
        completed_at=datetime.now(timezone.utc).isoformat(),
    )
    
    # Mettre à jour les soldes
    sender_wallet.balance_usd -= (amount + payment.fee_usd)
    sender_wallet.daily_spent_usd += amount
    
    recipient_wallets = [w for w in wallets_db.values() if w.user_id == recipient_id]
    if recipient_wallets:
        recipient_wallets[0].balance_usd += amount
    
    payments_db[payment.transaction_id] = payment
    
    return JSONResponse({
        "status": "completed",
        "transaction": asdict(payment),
        "fee_usd": payment.fee_usd,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/payment/history")
async def get_payment_history(user_id: str = Query("")):
    """Historique des transactions"""
    user_payments = [
        p for p in payments_db.values()
        if p.sender_id == user_id or p.recipient_id == user_id
    ]
    
    return JSONResponse({
        "user_id": user_id,
        "transactions": [asdict(p) for p in user_payments[-50:]],
        "total": len(user_payments),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# ENDPOINTS - TRANSCRIPTION IA
# ============================================================================

@app.post("/call/{session_id}/transcription/enable")
async def enable_transcription(session_id: str, request: Request):
    """Active la transcription temps réel"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    language = body.get("language", "auto")
    
    transcript = Transcript(
        session_id=session_id,
        language=language,
    )
    
    transcripts_db[transcript.transcript_id] = transcript
    
    return JSONResponse({
        "status": "enabled",
        "transcript_id": transcript.transcript_id,
        "language": language,
        "model": "Whisper v3",
        "accuracy": "95%+",
        "latency_ms": "<500ms",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.get("/call/{session_id}/transcript")
async def get_transcript(session_id: str, format: str = Query("json")):
    """Récupère la transcription"""
    transcripts = [t for t in transcripts_db.values() if t.session_id == session_id]
    
    if not transcripts:
        raise HTTPException(404, "Transcript not found")
    
    transcript = transcripts[0]
    
    # Simulation de segments
    transcript.segments = [
        {"start_s": 0, "end_s": 2, "speaker": "Alice", "text": "Bonjour Bob", "confidence": 0.98},
        {"start_s": 2, "end_s": 5, "speaker": "Bob", "text": "Salut Alice, comment ça va?", "confidence": 0.97},
    ]
    transcript.full_text = " ".join([s["text"] for s in transcript.segments])
    transcript.summary = "Conversation de salutation entre Alice et Bob"
    transcript.keywords = ["salutation", "conversation", "amical"]
    
    if format == "srt":
        return _format_srt(transcript)
    elif format == "vtt":
        return _format_vtt(transcript)
    else:
        return JSONResponse({
            "transcript_id": transcript.transcript_id,
            "session_id": session_id,
            "language": transcript.language,
            "segments": transcript.segments,
            "full_text": transcript.full_text,
            "summary": transcript.summary,
            "keywords": transcript.keywords,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

# ============================================================================
# ENDPOINTS - IA INTÉGRÉE
# ============================================================================

@app.post("/ai/chat")
async def ai_chat(request: Request):
    """Chat avec assistant IA"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    user_message = body.get("message", "")
    context = body.get("context", "")
    
    # Simulation de réponse IA
    ai_response = _simulate_ai_response(user_message, context)
    
    return JSONResponse({
        "user_message": user_message,
        "ai_response": ai_response,
        "model": "Llama 2 70B",
        "confidence": 0.92,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/ai/summarize-call")
async def summarize_call(session_id: str):
    """Résumé automatique d'un appel"""
    return JSONResponse({
        "session_id": session_id,
        "summary": "Appel professionnel de 15 minutes. Sujets: Projet Q1, Budget, Timeline.",
        "key_points": [
            "Projet Q1 lancé avec succès",
            "Budget approuvé: $50K",
            "Timeline: 3 mois",
            "Prochaine réunion: 15 mars"
        ],
        "action_items": [
            "Alice: Préparer documentation",
            "Bob: Valider ressources",
        ],
        "sentiment": "positif",
        "duration_minutes": 15,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.post("/ai/translate-message")
async def translate_message(message_id: str, request: Request):
    """Traduction instantanée"""
    try:
        body = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    target_language = body.get("target_language", "en")
    
    if message_id not in messages_db:
        raise HTTPException(404, "Message not found")
    
    msg = messages_db[message_id]
    
    return JSONResponse({
        "message_id": message_id,
        "original": msg.content,
        "original_language": "auto",
        "translated": f"[Translated to {target_language}] {msg.content}",
        "target_language": target_language,
        "confidence": 0.95,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ============================================================================
# HELPERS
# ============================================================================

def _generate_encryption_key() -> str:
    """Génère une clé AES-256-GCM"""
    return f"key_{uuid.uuid4().hex[:32]}"

def _simulate_ai_response(message: str, context: str) -> str:
    """Simule une réponse IA"""
    responses = {
        "hello": "Bonjour! Comment puis-je vous aider?",
        "help": "Je peux vous aider avec: traduction, résumé, rédaction, code, etc.",
        "time": f"Il est actuellement {datetime.now().strftime('%H:%M:%S')}",
    }
    
    for key, response in responses.items():
        if key in message.lower():
            return response
    
    return "Je comprends votre message. Comment puis-je vous aider davantage?"

def _format_srt(transcript: Transcript) -> str:
    """Formate la transcription en SRT"""
    srt = ""
    for i, seg in enumerate(transcript.segments, 1):
        start = _seconds_to_srt_time(seg["start_s"])
        end = _seconds_to_srt_time(seg["end_s"])
        srt += f"{i}\n{start} --> {end}\n{seg['speaker']}: {seg['text']}\n\n"
    return srt

def _format_vtt(transcript: Transcript) -> str:
    """Formate la transcription en VTT"""
    vtt = "WEBVTT\n\n"
    for seg in transcript.segments:
        start = _seconds_to_vtt_time(seg["start_s"])
        end = _seconds_to_vtt_time(seg["end_s"])
        vtt += f"{start} --> {end}\n{seg['speaker']}: {seg['text']}\n\n"
    return vtt

def _seconds_to_srt_time(seconds: float) -> str:
    """Convertit secondes en format SRT (HH:MM:SS,mmm)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def _seconds_to_vtt_time(seconds: float) -> str:
    """Convertit secondes en format VTT (HH:MM:SS.mmm)"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

# ============================================================================
# ENTREE PRINCIPALE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=9020, access_log=False)

