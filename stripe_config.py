import stripe
import os
from typing import Dict, List, Optional
from datetime import datetime

class StripeSaaSConfig:
    """Configuration Stripe pour Harmonic AI SaaS"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('STRIPE_SECRET_KEY')
        stripe.api_key = self.api_key
        
        # Produits SaaS Harmonic AI
        self.products = {
            'starter': {
                'name': 'Harmonic AI Starter',
                'description': '10K tokens/mois, Mode vérifié basique, Support email',
                'price': 99,  # USD
                'features': [
                    '10,000 tokens par mois',
                    'Mode vérifié basique',
                    'Citations obligatoires',
                    'Support email',
                    'API REST',
                    'Documentation complète'
                ]
            },
            'pro': {
                'name': 'Harmonic AI Pro',
                'description': '100K tokens/mois, Mode vérifié complet, Citations avancées, Support prioritaire',
                'price': 499,  # USD
                'features': [
                    '100,000 tokens par mois',
                    'Mode vérifié complet',
                    'Citations avancées avec sources',
                    'Support prioritaire',
                    'API REST + WebSocket',
                    'Dashboard analytics',
                    'Export des données',
                    'Intégration webhook'
                ]
            },
            'enterprise': {
                'name': 'Harmonic AI Enterprise',
                'description': '1M tokens/mois, Déterminisme garanti, Audit trail complet, Support 24/7, SLA 99.9%',
                'price': 2499,  # USD
                'features': [
                    '1,000,000 tokens par mois',
                    'Déterminisme garanti (même prompt = même réponse)',
                    'Audit trail complet',
                    'Support 24/7',
                    'SLA 99.9%',
                    'API dédiée',
                    'Custom integration',
                    'Onboarding personnalisé',
                    'Accès aux logs détaillés',
                    'Contrat de service'
                ]
            }
        }
    
    def create_products(self) -> Dict[str, str]:
        """Créer les produits Stripe pour Harmonic AI"""
        product_ids = {}
        
        for tier, details in self.products.items():
            try:
                # Créer le produit
                product = stripe.Product.create(
                    name=details['name'],
                    description=details['description'],
                    metadata={
                        'tier': tier,
                        'features': ','.join(details['features']),
                        'created_at': datetime.now().isoformat()
                    }
                )
                
                # Créer le prix
                price = stripe.Price.create(
                    product=product.id,
                    unit_amount=details['price'] * 100,  # en cents
                    currency='usd',
                    recurring={'interval': 'month'},
                    metadata={'tier': tier}
                )
                
                product_ids[tier] = {
                    'product_id': product.id,
                    'price_id': price.id
                }
                
                print(f"✅ Produit créé: {details['name']} (${details['price']}/mois)")
                print(f"   Product ID: {product.id}")
                print(f"   Price ID: {price.id}")
                
            except stripe.error.StripeError as e:
                print(f"❌ Erreur création produit {tier}: {e}")
        
        return product_ids
    
    def create_checkout_session(self, price_id: str, customer_email: str, success_url: str, cancel_url: str) -> Dict:
        """Créer une session de checkout Stripe"""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                customer_email=customer_email,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'service': 'harmonic_ai',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            return {
                'session_id': session.id,
                'url': session.url,
                'status': 'created'
            }
            
        except stripe.error.StripeError as e:
            return {
                'error': str(e),
                'status': 'failed'
            }
    
    def handle_webhook(self, payload: bytes, sig_header: str, webhook_secret: str) -> Dict:
        """Gérer les webhooks Stripe"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            event_type = event['type']
            data = event['data']['object']
            
            # Gérer différents types d'événements
            handlers = {
                'checkout.session.completed': self._handle_checkout_completed,
                'customer.subscription.created': self._handle_subscription_created,
                'customer.subscription.updated': self._handle_subscription_updated,
                'customer.subscription.deleted': self._handle_subscription_deleted,
                'invoice.payment_succeeded': self._handle_payment_succeeded,
                'invoice.payment_failed': self._handle_payment_failed
            }
            
            if event_type in handlers:
                return handlers[event_type](data)
            else:
                return {'status': 'ignored', 'event_type': event_type}
                
        except ValueError as e:
            return {'error': 'Invalid payload', 'status': 'error'}
        except stripe.error.SignatureVerificationError as e:
            return {'error': 'Invalid signature', 'status': 'error'}
    
    def _handle_checkout_completed(self, data: Dict) -> Dict:
        """Gérer checkout complété"""
        customer_email = data.get('customer_email', '')
        subscription_id = data.get('subscription', '')
        
        print(f"🎉 Nouveau client: {customer_email}")
        print(f"   Subscription ID: {subscription_id}")
        
        # Ici: créer l'utilisateur dans votre base de données
        # générer une clé API, envoyer l'email de bienvenue
        
        return {
            'status': 'processed',
            'action': 'create_user',
            'customer_email': customer_email,
            'subscription_id': subscription_id
        }
    
    def _handle_subscription_created(self, data: Dict) -> Dict:
        """Gérer création d'abonnement"""
        customer_id = data.get('customer', '')
        subscription_id = data.get('id', '')
        
        print(f"📝 Abonnement créé: {subscription_id}")
        print(f"   Customer ID: {customer_id}")
        
        return {
            'status': 'processed',
            'action': 'activate_subscription',
            'subscription_id': subscription_id
        }
    
    def _handle_payment_succeeded(self, data: Dict) -> Dict:
        """Gérer paiement réussi"""
        subscription_id = data.get('subscription', '')
        amount_paid = data.get('amount_paid', 0) / 100  # convertir en dollars
        
        print(f"💰 Paiement réussi: ${amount_paid}")
        print(f"   Subscription ID: {subscription_id}")
        
        return {
            'status': 'processed',
            'action': 'payment_success',
            'amount': amount_paid,
            'subscription_id': subscription_id
        }


# Configuration pour développement
if __name__ == "__main__":
    # Pour tester, utilisez une clé de test Stripe
    # export STRIPE_SECRET_KEY=sk_test_...
    
    config = StripeSaaSConfig()
    
    print("=" * 60)
    print("CONFIGURATION STRIPE HARMONIC AI")
    print("=" * 60)
    
    # Afficher les produits configurés
    for tier, details in config.products.items():
        print(f"\n📦 {details['name']} - ${details['price']}/mois")
        print(f"   {details['description']}")
        print("   Fonctionnalités:")
        for feature in details['features']:
            print(f"     • {feature}")
    
    print("\n" + "=" * 60)
    print("Pour créer les produits sur Stripe:")
    print("1. Créez un compte Stripe: https://dashboard.stripe.com/register")
    print("2. Récupérez votre clé API secrète")
    print("3. Exécutez: python stripe_config.py --create-products")
    print("=" * 60)