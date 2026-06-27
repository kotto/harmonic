#!/usr/bin/env python3
"""
Subscription Service - Monetization & Billing
==============================================
Service pour la gestion des abonnements, quotas et facturation
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import uuid

from app.core.config import settings
from app.models.user import User
from app.models.subscription import Subscription, SubscriptionTier, SubscriptionStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.usage import UsageMetrics
from app.schemas.subscription import SubscriptionTier, PlanDefinition, UsageMetrics as UsageMetricsSchema
from app.services.stripe_service import StripeService

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# SUBSCRIPTION PLANS
# ----------------------------------------------------------------------------

class SubscriptionService:
    """Service de gestion des abonnements"""
    
    # Plans d'abonnement disponibles
    PLANS = {
        SubscriptionTier.FREE: PlanDefinition(
            tier=SubscriptionTier.FREE,
            name="Free",
            price_monthly=0.0,
            price_yearly=0.0,
            features=[
                "10 minutes audio/month",
                "5 minutes video/month", 
                "100 API calls/month",
                "Watermark on results",
                "Basic support"
            ],
            limits={
                "audio_minutes": 10,
                "video_minutes": 5,
                "api_calls": 100,
                "max_file_size_mb": 50,
                "concurrent_jobs": 1
            }
        ),
        SubscriptionTier.PRO: PlanDefinition(
            tier=SubscriptionTier.PRO,
            name="Pro",
            price_monthly=49.0,
            price_yearly=490.0,  # 2 months free
            features=[
                "100 minutes audio/month",
                "50 minutes video/month",
                "1000 API calls/month",
                "No watermark",
                "Priority processing",
                "Advanced audio profiles",
                "Email support"
            ],
            limits={
                "audio_minutes": 100,
                "video_minutes": 50,
                "api_calls": 1000,
                "max_file_size_mb": 200,
                "concurrent_jobs": 3
            }
        ),
        SubscriptionTier.ENTERPRISE: PlanDefinition(
            tier=SubscriptionTier.ENTERPRISE,
            name="Enterprise",
            price_monthly=499.0,
            price_yearly=4990.0,  # 2 months free
            features=[
                "Unlimited audio processing",
                "Unlimited video processing",
                "10,000 API calls/month",
                "Custom processing profiles",
                "Dedicated support",
                "SLA 99.9%",
                "White-label solutions",
                "API access"
            ],
            limits={
                "audio_minutes": float('inf'),
                "video_minutes": float('inf'),
                "api_calls": 10000,
                "max_file_size_mb": 1000,
                "concurrent_jobs": 10
            }
        )
    }
    
    @staticmethod
    def get_available_plans() -> List[PlanDefinition]:
        """
        Récupérer tous les plans d'abonnement disponibles
        
        Returns:
            Liste des plans
        """
        return list(SubscriptionService.PLANS.values())
    
    @staticmethod
    def get_plan_by_tier(tier: SubscriptionTier) -> Optional[PlanDefinition]:
        """
        Récupérer un plan spécifique par tier
        
        Args:
            tier: Niveau d'abonnement
            
        Returns:
            Plan d'abonnement ou None
        """
        return SubscriptionService.PLANS.get(tier)
    
    # ------------------------------------------------------------------------
    # SUBSCRIPTION MANAGEMENT
    # ------------------------------------------------------------------------
    
    @staticmethod
    def get_user_subscription(db: Session, user_id: str) -> Optional[Subscription]:
        """
        Récupérer l'abonnement d'un utilisateur
        
        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            
        Returns:
            Abonnement ou None
        """
        return db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(Subscription.created_at.desc()).first()
    
    @staticmethod
    def create_subscription(
        db: Session,
        user_id: str,
        tier: SubscriptionTier,
        payment_method_id: Optional[str] = None,
        coupon_code: Optional[str] = None
    ) -> Subscription:
        """
        Créer un nouvel abonnement
        
        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            tier: Niveau d'abonnement
            payment_method_id: ID de la méthode de paiement Stripe
            coupon_code: Code promo
            
        Returns:
            Abonnement créé
            
        Raises:
            HTTPException: Si la création échoue
        """
        try:
            # Récupérer l'utilisateur
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Vérifier si l'utilisateur a déjà un abonnement actif
            existing_subscription = SubscriptionService.get_user_subscription(db, user_id)
            if existing_subscription and existing_subscription.status == SubscriptionStatus.ACTIVE:
                raise ValueError("User already has an active subscription")
            
            # Créer le customer Stripe si nécessaire
            if not user.stripe_customer_id:
                customer = StripeService.create_customer(
                    email=user.email,
                    name=user.username
                )
                user.stripe_customer_id = customer.id
                db.commit()
            
            # Créer l'abonnement Stripe pour les plans payants
            stripe_subscription_id = None
            if tier != SubscriptionTier.FREE:
                stripe_subscription = StripeService.create_subscription(
                    customer_id=user.stripe_customer_id,
                    price_id=SubscriptionService._get_stripe_price_id(tier),
                    payment_method_id=payment_method_id,
                    coupon_code=coupon_code
                )
                stripe_subscription_id = stripe_subscription.id
            
            # Calculer les dates de période
            now = datetime.utcnow()
            period_start = now
            period_end = now + timedelta(days=30)  # 30 jours pour le mois
            
            # Créer l'abonnement dans la base
            subscription = Subscription(
                id=str(uuid.uuid4()),
                user_id=user_id,
                tier=tier,
                status=SubscriptionStatus.ACTIVE,
                current_period_start=period_start,
                current_period_end=period_end,
                cancel_at_period_end=False,
                stripe_subscription_id=stripe_subscription_id,
                created_at=now,
                updated_at=now
            )
            
            db.add(subscription)
            db.commit()
            
            # Créer la première facture
            if tier != SubscriptionTier.FREE:
                SubscriptionService._create_invoice(
                    db=db,
                    user_id=user_id,
                    subscription_id=subscription.id,
                    amount=SubscriptionService.PLANS[tier].price_monthly,
                    stripe_subscription_id=stripe_subscription_id
                )
            
            logger.info(f"Subscription created for user {user_id}: {subscription.id}")
            return subscription
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create subscription for user {user_id}: {str(e)}")
            raise
    
    @staticmethod
    def update_subscription(
        db: Session,
        user_id: str,
        new_tier: SubscriptionTier,
        payment_method_id: Optional[str] = None,
        prorate: bool = True
    ) -> Subscription:
        """
        Mettre à jour un abonnement existant
        
        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            new_tier: Nouveau niveau d'abonnement
            payment_method_id: Nouvelle méthode de paiement
            prorate: Appliquer le prorata
            
        Returns:
            Abonnement mis à jour
        """
        try:
            # Récupérer l'abonnement actuel
            subscription = SubscriptionService.get_user_subscription(db, user_id)
            if not subscription:
                raise ValueError("No subscription found for user")
            
            # Si le tier est le même, juste mettre à jour la méthode de paiement
            if subscription.tier == new_tier and payment_method_id:
                StripeService.update_payment_method(
                    customer_id=subscription.stripe_customer_id,
                    payment_method_id=payment_method_id
                )
                subscription.updated_at = datetime.utcnow()
                db.commit()
                return subscription
            
            # Mettre à jour l'abonnement Stripe pour les plans payants
            if subscription.tier != SubscriptionTier.FREE and new_tier != SubscriptionTier.FREE:
                # Mise à jour de l'abonnement existant
                updated_subscription = StripeService.update_subscription(
                    subscription_id=subscription.stripe_subscription_id,
                    new_price_id=SubscriptionService._get_stripe_price_id(new_tier),
                    prorate=prorate
                )
                
                subscription.stripe_subscription_id = updated_subscription.id
                subscription.tier = new_tier
                subscription.updated_at = datetime.utcnow()
                db.commit()
                
                # Créer une nouvelle facture
                SubscriptionService._create_invoice(
                    db=db,
                    user_id=user_id,
                    subscription_id=subscription.id,
                    amount=SubscriptionService.PLANS[new_tier].price_monthly,
                    stripe_subscription_id=updated_subscription.id
                )
                
            elif subscription.tier == SubscriptionTier.FREE and new_tier != SubscriptionTier.FREE:
                # Passage de Free à payant
                user = db.query(User).filter(User.id == user_id).first()
                
                stripe_subscription = StripeService.create_subscription(
                    customer_id=user.stripe_customer_id,
                    price_id=SubscriptionService._get_stripe_price_id(new_tier),
                    payment_method_id=payment_method_id
                )
                
                subscription.tier = new_tier
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.stripe_subscription_id = stripe_subscription.id
                subscription.current_period_start = datetime.utcnow()
                subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
                subscription.updated_at = datetime.utcnow()
                db.commit()
                
                # Créer la première facture
                SubscriptionService._create_invoice(
                    db=db,
                    user_id=user_id,
                    subscription_id=subscription.id,
                    amount=SubscriptionService.PLANS[new_tier].price_monthly,
                    stripe_subscription_id=stripe_subscription.id
                )
                
            elif subscription.tier != SubscriptionTier.FREE and new_tier == SubscriptionTier.FREE:
                # Passage de payant à Free
                StripeService.cancel_subscription(subscription.stripe_subscription_id)
                
                subscription.tier = new_tier
                subscription.status = SubscriptionStatus.CANCELED
                subscription.cancel_at_period_end = True
                subscription.updated_at = datetime.utcnow()
                db.commit()
            
            logger.info(f"Subscription updated for user {user_id}: {subscription.id}")
            return subscription
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update subscription for user {user_id}: {str(e)}")
            raise
    
    @staticmethod
    def cancel_subscription(db: Session, user_id: str) -> Subscription:
        """
        Annuler un abonnement
        
        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            
        Returns:
            Abonnement annulé
        """
        try:
            # Récupérer l'abonnement
            subscription = SubscriptionService.get_user_subscription(db, user_id)
            if not subscription:
                raise ValueError("No subscription found for user")
            
            # Annuler l'abonnement Stripe pour les plans payants
            if subscription.tier != SubscriptionTier.FREE and subscription.stripe_subscription_id:
                StripeService.cancel_subscription(subscription.stripe_subscription_id)
            
            # Mettre à jour l'abonnement
            subscription.status = SubscriptionStatus.CANCELED
            subscription.cancel_at_period_end = True
            subscription.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Subscription canceled for user {user_id}: {subscription.id}")
            return subscription
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cancel subscription for user {user_id}: {str(e)}")
            raise
    
    # ------------------------------------------------------------------------
    # USAGE & QUOTAS
    # ------------------------------------------------------------------------
    
    @staticmethod
    def calculate_usage(db: Session, user_id: str) -> UsageMetricsSchema:
        """
        Calculer l'utilisation de l'utilisateur
        
        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            
        Returns:
            Métriques d'utilisation
        """
        try:
            # Récupérer l'abonnement
            subscription = SubscriptionService.get_user_subscription(db, user_id)
            if not subscription:
                # Retourner des métriques par défaut
                return UsageMetricsSchema(
                    user_id=user_id,
                    subscription_tier=SubscriptionTier.FREE,
                    audio_minutes_used=0.0,
                    audio_minutes_limit=10.0,
                    video_minutes_used=0.0,
                    video_minutes_limit=5.0,
                    api_calls_used=0,
                    api_calls_limit=100,
                    usage_percentage=0.0,
                    remaining_days=30
                )
            
            # Récupérer les métriques d'utilisation du mois en cours
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            usage = db.query(UsageMetrics).filter(
                UsageMetrics.user_id == user_id,
                UsageMetrics.date >= month_start
            ).first()
            
            if not usage:
                # Créer des métriques par défaut
                usage = UsageMetrics(
                    user_id=user_id,
                    date=now,
                    audio_minutes=0.0,
                    video_minutes=0.0,
                    api_calls=0,
                    total_cost=0.0
                )
                db.add(usage)
                db.commit()
            
            # Récupérer les limites du plan
            plan = SubscriptionService.PLANS[subscription.tier]
            limits = plan.limits
            
            # Calculer les pourcentages d'utilisation
            audio_percentage = (usage.audio_minutes / limits["audio_minutes"]) * 100 if limits["audio_minutes"] > 0 else 0
            video_percentage = (usage.video_minutes / limits["video_minutes"]) * 100 if limits["video_minutes"] > 0 else 0
            api_percentage = (usage.api_calls / limits["api_calls"]) * 100 if limits["api_calls"] > 0 else 0
            
            # Calculer le pourcentage global
            total_percentage = (audio_percentage + video_percentage + api_percentage) / 3
            
            # Calculer les jours restants
            if subscription.current_period_end:
                remaining_days = (subscription.current_period_end - now).days
            else:
                remaining_days = 30
            
            return UsageMetricsSchema(
                user_id=user_id,
                subscription_tier=subscription.tier,
                audio_minutes_used=usage.audio_minutes,
                audio_minutes_limit=limits["audio_minutes"],
                video_minutes_used=usage.video_minutes,
                video_minutes_limit=limits["video_minutes"],
                api_calls_used=usage.api_calls,
                api_calls_limit=limits["api_calls"],
                usage_percentage=total_percentage,
                remaining_days=remaining_days
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate usage for user {user_id}: {str(e)}")
            raise
    
    @staticmethod
    def check_quota(
        db: Session,
        user_id: str,
        service_type: str,
        amount: float
    ) -> Tuple[bool, Optional[str]]:
        """
        Vérifier si l'utilisateur a assez de quota
        
        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            service_type: Type de service (audio/video/api)
            amount: Quantité à utiliser
            
        Returns:
            Tuple (has_quota, error_message)
        """
        try:
            # Récupérer l'abonnement
            subscription = SubscriptionService.get_user_subscription(db, user_id)
            if not subscription:
                return False, "No subscription found"
            
            # Récupérer les limites du plan
            plan = SubscriptionService.PLANS[subscription.tier]
            limits = plan.limits
            
            # Récupérer l'utilisation actuelle
            usage = SubscriptionService.calculate_usage(db, user_id)
            
            # Vérifier les quotas selon le type de service
            if service_type == "audio":
                if usage.audio_minutes_used + amount > limits["audio_minutes"]:
                    return False, f"Audio quota exceeded. Used: {usage.audio_minutes_used}/{limits['audio_minutes']} minutes"
            
            elif service_type == "video":
                if usage.video_minutes_used + amount > limits["video_minutes"]:
                    return False, f"Video quota exceeded. Used: {usage.video_minutes_used}/{limits['video_minutes']} minutes"
            
            elif service_type == "api":
                if usage.api_calls_used + amount > limits["api_calls"]:
                    return False, f"API quota exceeded. Used: {usage.api_calls_used}/{limits['api_calls']} calls"
            
            else:
                return False, f"Unknown service type: {service_type}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Failed to check quota for user {user_id}: {str(e)}")
            return False, f"Quota check error: {str(e)}"
    
    @staticmethod
    def update_usage(
        db: Session,
        user_id: str,
        service_type: str,
        amount: float,
        cost: float = 0.0
    ) -> bool:
        """
        Mettre à jour l'utilisation de l'utilisateur
        
        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            service_type: Type de service (audio/video/api)
            amount: Quantité utilisée
            cost: Coût associé
            
        Returns:
            Succès de la mise à jour
        """
        try:
            # Récupérer les métriques du jour
            now = datetime.utcnow()
            today = now.date()
            
            usage = db.query(UsageMetrics).filter(
                UsageMetrics.user_id == user_id,
                UsageMetrics.date == today
            ).first()
            
            if not usage:
                # Créer de nouvelles métriques
                usage = UsageMetrics(
                    user_id=user_id,
                    date=now,
                    audio_minutes=0.0,
                    video_minutes=0.0,
                    api_calls=0,
                    total_cost=0.0
                )
                db.add(usage)
            
            # Mettre à jour selon le type de service
            if service_type == "audio":
                usage.audio_minutes += amount
            elif service_type == "video":
                usage.video_minutes += amount
            elif service_type == "api":
                usage.api_calls += int(amount)
            else:
                return False
            
            # Mettre à jour le coût total
            usage.total_cost += cost
            usage.updated_at = now
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update usage for user {user_id}: {str(e)}")
            return False
    
    # ------------------------------------------------------------------------
    # INVOICE MANAGEMENT
    # ------------------------------------------------------------------------
    
    @staticmethod
    def get_user_invoices(db: Session, user_id: str) -> List[Invoice]:
        """
        Récupérer les factures d'un utilisateur
        
        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            
        Returns:
            Liste des factures
        """
        return db.query(Invoice).filter(
            Invoice.user_id == user_id
        ).order_by(Invoice.created_at.desc()).all()
    
    @staticmethod
    def get_invoice(db: Session, invoice_id: str, user_id: str) -> Optional[Invoice]:
        """
        Récupérer une facture spécifique
        
        Args:
            db: Session de base de données
            invoice_id: ID de la facture
            user_id: ID de l'utilisateur
            
        Returns:
            Facture ou None
        """
        return db.query(Invoice).filter(
            Invoice.id == invoice_id,
            Invoice.user_id == user_id
        ).first()
    
    @staticmethod
    def _create_invoice(
        db: Session,
        user_id: str,
        subscription_id: str,
        amount: float,
        stripe_subscription_id: Optional[str] = None
    ) -> Invoice:
        """
        Créer une facture
        
        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            subscription_id: ID de l'abonnement
            amount: Montant
            stripe_subscription_id: ID de l'abonnement Stripe
            
        Returns:
            Facture créée
        """
        try:
            now = datetime.utcnow()
            
            invoice = Invoice(
                id=str(uuid.uuid4()),
                user_id=user_id,
                subscription_id=subscription_id,
                amount=amount,
                currency="eur",
                status=InvoiceStatus.OPEN,
                period_start=now,
                period_end=now + timedelta(days=30),
                stripe_subscription_id=stripe_subscription_id,
                created_at=now,
                updated_at=now
            )
            
            db.add(invoice)
            db.commit()
            
            logger.info(f"Invoice created for user {user_id}: {invoice.id}")
            return invoice
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create invoice for user {user_id}: {str(e)}")
            raise
    
    # ------------------------------------------------------------------------
    # UTILITY FUNCTIONS
    # ------------------------------------------------------------------------
    
    @staticmethod
    def _get_stripe_price_id(tier: SubscriptionTier) -> str:
        """
        Récupérer l'ID de prix Stripe pour un tier
        
        Args:
            tier: Niveau d'abonnement
            
        Returns:
            ID de prix Stripe
        """
        # IDs Stripe pour les différents plans
        # À remplacer par les IDs réels de votre compte Stripe
        price_ids = {
            SubscriptionTier.PRO: "price_pro_monthly",
            SubscriptionTier.ENTERPRISE: "price_enterprise_monthly"
        }
        
        return price_ids.get(tier, "")
    
    @staticmethod
    def get_quota_status(db: Session, user_id: str) -> Dict[str, Any]:
        """
        Récupérer le statut des quotas de l'utilisateur
        
        Args:
            db: Session de base de données
            user_id: ID de l'utilisateur
            
        Returns:
            Statut des quotas
        """
        try:
            # Récupérer l'utilisation
            usage = SubscriptionService.calculate_usage(db, user_id)
            
            # Récupérer l'abonnement
            subscription = SubscriptionService.get_user_subscription(db, user_id)
            
            # Calculer les statuts
            audio_status = {
                "used": usage.audio_minutes_used,
                "limit": usage.audio_minutes_limit,
                "remaining": usage.audio_minutes_limit - usage.audio_minutes_used,
                "percentage": (usage.audio_minutes_used / usage.audio_minutes_limit) * 100 if usage.audio_minutes_limit > 0 else 0,
                "status": "ok" if usage.audio_minutes_used < usage.audio_minutes_limit else "exceeded"
            }
            
            video_status = {
                "used": usage.video_minutes_used,
                "limit": usage.video_minutes_limit,
                "remaining": usage.video_minutes_limit - usage.video_minutes_used,
                "percentage": (usage.video_minutes_used / usage.video_minutes_limit) * 100 if usage.video_minutes_limit > 0 else 0,
                "status": "ok" if usage.video_minutes_used < usage.video_minutes_limit else "exceeded"
            }
            
            api_status = {
                "used": usage.api_calls_used,
                "limit": usage.api_calls_limit,
                "remaining": usage.api_calls_limit - usage.api_calls_used,
                "percentage": (usage.api_calls_used / usage.api_calls_limit) * 100 if usage.api_calls_limit > 0 else 0,
                "status": "ok" if usage.api_calls_used < usage.api_calls_limit else "exceeded"
            }
            
            return {
                "subscription": {
                    "tier": subscription.tier if subscription else SubscriptionTier.FREE,
                    "status": subscription.status if subscription else SubscriptionStatus.INACTIVE,
                    "period_end": subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None
                },
                "quotas": {
                    "audio": audio_status,
                    "video": video_status,
                    "api": api_status
                },
                "overall": {
                    "usage_percentage": usage.usage_percentage,
                    "remaining_days": usage.remaining_days,
                    "status": "ok" if usage.usage_percentage < 100 else "exceeded"
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get quota status for user {user_id}: {str(e)}")
            raise