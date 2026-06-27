#!/usr/bin/env python3
"""
Subscription Endpoints - Monetization & Billing
================================================
Endpoints pour la gestion des abonnements et la monétisation
- Plans d'abonnement
- Paiements Stripe
- Facturation
- Gestion des quotas
"""

import logging
import stripe
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionTier, SubscriptionStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.schemas.subscription import (
    SubscriptionPlan,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    PaymentIntentResponse,
    UsageMetrics
)
from app.schemas.invoice import InvoiceResponse
from app.services.subscription_service import SubscriptionService
from app.services.stripe_service import StripeService

router = APIRouter()
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# SUBSCRIPTION PLANS
# ----------------------------------------------------------------------------

@router.get("/plans", response_model=List[SubscriptionPlan])
async def get_subscription_plans() -> Any:
    """
    Récupérer tous les plans d'abonnement disponibles
    
    Returns:
        Liste des plans d'abonnement
    """
    try:
        plans = SubscriptionService.get_available_plans()
        return plans
        
    except Exception as e:
        logger.error(f"Failed to get subscription plans: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscription plans: {str(e)}"
        )

@router.get("/plans/{tier}", response_model=SubscriptionPlan)
async def get_subscription_plan(tier: SubscriptionTier) -> Any:
    """
    Récupérer un plan d'abonnement spécifique
    
    Args:
        tier: Niveau d'abonnement
        
    Returns:
        Plan d'abonnement
    """
    try:
        plan = SubscriptionService.get_plan_by_tier(tier)
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription plan {tier} not found"
            )
        
        return plan
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get subscription plan {tier}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscription plan: {str(e)}"
        )

# ----------------------------------------------------------------------------
# SUBSCRIPTION MANAGEMENT
# ----------------------------------------------------------------------------

@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Récupérer l'abonnement actuel de l'utilisateur
    
    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Abonnement actuel
    """
    try:
        subscription = SubscriptionService.get_user_subscription(db, current_user.id)
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No subscription found for user"
            )
        
        # Calculer l'utilisation
        usage = SubscriptionService.calculate_usage(db, current_user.id)
        
        response = SubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            tier=subscription.tier,
            status=subscription.status,
            current_period_start=subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            cancel_at_period_end=subscription.cancel_at_period_end,
            created_at=subscription.created_at.isoformat() if subscription.created_at else None,
            updated_at=subscription.updated_at.isoformat() if subscription.updated_at else None,
            usage=usage
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get current subscription for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscription: {str(e)}"
        )

@router.post("/create", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Créer un nouvel abonnement
    
    Args:
        subscription_data: Données de l'abonnement
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Abonnement créé
    """
    try:
        logger.info(f"Creating subscription for user {current_user.id}, tier: {subscription_data.tier}")
        
        # Vérifier si l'utilisateur a déjà un abonnement actif
        existing_subscription = SubscriptionService.get_user_subscription(db, current_user.id)
        
        if existing_subscription and existing_subscription.status == SubscriptionStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active subscription"
            )
        
        # Créer l'abonnement
        subscription = SubscriptionService.create_subscription(
            db=db,
            user_id=current_user.id,
            tier=subscription_data.tier,
            payment_method_id=subscription_data.payment_method_id,
            coupon_code=subscription_data.coupon_code
        )
        
        # Calculer l'utilisation
        usage = SubscriptionService.calculate_usage(db, current_user.id)
        
        response = SubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            tier=subscription.tier,
            status=subscription.status,
            current_period_start=subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            cancel_at_period_end=subscription.cancel_at_period_end,
            created_at=subscription.created_at.isoformat() if subscription.created_at else None,
            updated_at=subscription.updated_at.isoformat() if subscription.updated_at else None,
            usage=usage
        )
        
        logger.info(f"Subscription created successfully for user {current_user.id}: {subscription.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create subscription for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subscription: {str(e)}"
        )

@router.put("/update", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_data: SubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Mettre à jour l'abonnement actuel
    
    Args:
        subscription_data: Données de mise à jour
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Abonnement mis à jour
    """
    try:
        logger.info(f"Updating subscription for user {current_user.id}, new tier: {subscription_data.tier}")
        
        # Mettre à jour l'abonnement
        subscription = SubscriptionService.update_subscription(
            db=db,
            user_id=current_user.id,
            new_tier=subscription_data.tier,
            payment_method_id=subscription_data.payment_method_id,
            prorate=subscription_data.prorate
        )
        
        # Calculer l'utilisation
        usage = SubscriptionService.calculate_usage(db, current_user.id)
        
        response = SubscriptionResponse(
            id=subscription.id,
            user_id=subscription.user_id,
            tier=subscription.tier,
            status=subscription.status,
            current_period_start=subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            cancel_at_period_end=subscription.cancel_at_period_end,
            created_at=subscription.created_at.isoformat() if subscription.created_at else None,
            updated_at=subscription.updated_at.isoformat() if subscription.updated_at else None,
            usage=usage
        )
        
        logger.info(f"Subscription updated successfully for user {current_user.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update subscription for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subscription: {str(e)}"
        )

@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Annuler l'abonnement actuel
    
    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Confirmation d'annulation
    """
    try:
        logger.info(f"Canceling subscription for user {current_user.id}")
        
        # Annuler l'abonnement
        subscription = SubscriptionService.cancel_subscription(db, current_user.id)
        
        return {
            "success": True,
            "message": "Subscription canceled successfully",
            "subscription_id": subscription.id,
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel subscription for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}"
        )

# ----------------------------------------------------------------------------
# PAYMENT & BILLING
# ----------------------------------------------------------------------------

@router.post("/payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    amount: int,
    currency: str = "eur",
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Créer un PaymentIntent Stripe
    
    Args:
        amount: Montant en centimes
        currency: Devise (par défaut: eur)
        current_user: Utilisateur authentifié
        
    Returns:
        PaymentIntent créé
    """
    try:
        logger.info(f"Creating payment intent for user {current_user.id}, amount: {amount/100:.2f} {currency}")
        
        # Créer le PaymentIntent
        payment_intent = StripeService.create_payment_intent(
            amount=amount,
            currency=currency,
            customer_id=current_user.stripe_customer_id,
            metadata={
                "user_id": current_user.id,
                "service": "harmonic_ai_saas"
            }
        )
        
        response = PaymentIntentResponse(
            client_secret=payment_intent.client_secret,
            amount=payment_intent.amount,
            currency=payment_intent.currency,
            status=payment_intent.status,
            created=payment_intent.created,
            id=payment_intent.id
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to create payment intent for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment intent: {str(e)}"
        )

@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_user_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Récupérer les factures de l'utilisateur
    
    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Liste des factures
    """
    try:
        invoices = SubscriptionService.get_user_invoices(db, current_user.id)
        
        invoice_responses = []
        for invoice in invoices:
            invoice_responses.append(InvoiceResponse(
                id=invoice.id,
                user_id=invoice.user_id,
                amount=invoice.amount,
                currency=invoice.currency,
                status=invoice.status,
                stripe_invoice_id=invoice.stripe_invoice_id,
                period_start=invoice.period_start.isoformat() if invoice.period_start else None,
                period_end=invoice.period_end.isoformat() if invoice.period_end else None,
                paid_at=invoice.paid_at.isoformat() if invoice.paid_at else None,
                created_at=invoice.created_at.isoformat() if invoice.created_at else None
            ))
        
        return invoice_responses
        
    except Exception as e:
        logger.error(f"Failed to get invoices for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get invoices: {str(e)}"
        )

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Récupérer une facture spécifique
    
    Args:
        invoice_id: ID de la facture
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Facture
    """
    try:
        invoice = SubscriptionService.get_invoice(db, invoice_id, current_user.id)
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        response = InvoiceResponse(
            id=invoice.id,
            user_id=invoice.user_id,
            amount=invoice.amount,
            currency=invoice.currency,
            status=invoice.status,
            stripe_invoice_id=invoice.stripe_invoice_id,
            period_start=invoice.period_start.isoformat() if invoice.period_start else None,
            period_end=invoice.period_end.isoformat() if invoice.period_end else None,
            paid_at=invoice.paid_at.isoformat() if invoice.paid_at else None,
            created_at=invoice.created_at.isoformat() if invoice.created_at else None
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get invoice {invoice_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get invoice: {str(e)}"
        )

# ----------------------------------------------------------------------------
# USAGE & QUOTAS
# ----------------------------------------------------------------------------

@router.get("/usage", response_model=UsageMetrics)
async def get_usage_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Récupérer les métriques d'utilisation de l'utilisateur
    
    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Métriques d'utilisation
    """
    try:
        usage = SubscriptionService.calculate_usage(db, current_user.id)
        
        return usage
        
    except Exception as e:
        logger.error(f"Failed to get usage metrics for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage metrics: {str(e)}"
        )

@router.get("/quota")
async def get_quota_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Récupérer le statut des quotas de l'utilisateur
    
    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        Statut des quotas
    """
    try:
        quota_status = SubscriptionService.get_quota_status(db, current_user.id)
        
        return {
            "success": True,
            "quota_status": quota_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get quota status for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quota status: {str(e)}"
        )

# ----------------------------------------------------------------------------
# STRIPE WEBHOOK
# ----------------------------------------------------------------------------

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
) -> Any:
    """
    Webhook Stripe pour les événements de paiement
    
    Args:
        request: Requête HTTP
        db: Session de base de données
        
    Returns:
        Confirmation de réception
    """
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        # Vérifier la signature
        event = StripeService.verify_webhook_signature(payload, sig_header)
        
        # Traiter l'événement
        result = StripeService.handle_webhook_event(event, db)
        
        return {
            "success": True,
            "event_type": event.type,
            "event_id": event.id,
            "processed": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook error: {str(e)}"
        )