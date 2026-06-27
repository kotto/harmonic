"""Service Stripe pour les paiements - Version simplifiée pour développement"""
from typing import Optional, Dict, Any
from app.schemas.subscription import SubscriptionTier

class StripeService:
    """Service Stripe simplifié pour le développement"""
    
    @staticmethod
    async def create_checkout_session(
        plan: SubscriptionTier,
        user_id: int,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """Crée une session de checkout simulée"""
        return {
            "id": f"cs_test_{user_id}_{plan.value}",
            "url": success_url,
            "status": "complete"
        }
    
    @staticmethod
    async def create_portal_session(
        user_id: int,
        return_url: str
    ) -> Dict[str, Any]:
        """Crée une session de portail client simulée"""
        return {
            "id": f"ps_test_{user_id}",
            "url": return_url,
            "status": "active"
        }
    
    @staticmethod
    async def cancel_subscription(subscription_id: str) -> bool:
        """Annule un abonnement simulé"""
        return True
    
    @staticmethod
    async def get_subscription_status(subscription_id: str) -> Optional[str]:
        """Récupère le statut d'un abonnement simulé"""
        return "active"
    
    @staticmethod
    async def handle_webhook(payload: bytes, signature: str) -> Optional[Dict[str, Any]]:
        """Gère un webhook Stripe simulé"""
        return {"type": "checkout.session.completed", "status": "complete"}
