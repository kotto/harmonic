"""Service d'envoi d'emails pour Harmonic AI SaaS"""
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Service d'envoi d'emails (mode développement)"""
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Envoyer un email (simulé en développement)"""
        logger.info(f"[EMAIL SIMULÉ] To: {to_email}")
        logger.info(f"[EMAIL SIMULÉ] Subject: {subject}")
        logger.info(f"[EMAIL SIMULÉ] Body: {body[:200]}...")
        return True
    
    @staticmethod
    def send_welcome_email(email: str, username: str) -> bool:
        """Envoyer un email de bienvenue"""
        subject = "Welcome to Harmonic AI!"
        body = f"""
        Welcome {username}!
        
        Thank you for joining Harmonic AI. Your account has been created successfully.
        
        Get started with our powerful AI services:
        - Audio Processing
        - Video Processing
        - Text Analysis
        - And more...
        
        Best regards,
        The Harmonic AI Team
        """
        return EmailService.send_email(email, subject, body)
    
    @staticmethod
    def send_password_reset_email(email: str, reset_token: str) -> bool:
        """Envoyer un email de réinitialisation de mot de passe"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        subject = "Password Reset - Harmonic AI"
        body = f"""
        You have requested a password reset.
        
        Click the link below to reset your password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you did not request this, please ignore this email.
        
        Best regards,
        The Harmonic AI Team
        """
        return EmailService.send_email(email, subject, body)
    
    @staticmethod
    def send_subscription_confirmation(email: str, plan: str) -> bool:
        """Envoyer une confirmation d'abonnement"""
        subject = f"Subscription Confirmed - {plan.title()} Plan"
        body = f"""
        Your {plan.title()} subscription has been activated!
        
        You now have access to all features included in your plan.
        
        Thank you for choosing Harmonic AI!
        
        Best regards,
        The Harmonic AI Team
        """
        return EmailService.send_email(email, subject, body)
