# Système d'Authentification API Avancé - Harmonic AI
# Protection contre Reverse Engineering et Attaques

import hmac
import hashlib
import secrets
import time
import base64
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
import redis
import boto3
from botocore.exceptions import ClientError
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

class AdvancedAPIAuthSystem:
    """Système d'authentification API avancé avec protection multi-couches"""
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        # Configuration Redis pour rate limiting et cache
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        
        # AWS Secrets Manager pour stockage sécurisé
        self.secrets_client = boto3.client('secretsmanager')
        
        # Configuration sécurité
        self.api_key_length = 32
        self.secret_key_length = 64
        self.token_expiry_hours = 24
        self.max_requests_per_minute = 1000
        
        # Clé de chiffrement pour données sensibles
        self.encryption_key = self._generate_encryption_key()
        
        # Cache pour performances
        self.key_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Monitoring
        self.request_log = []
        self.security_events = []
        
    def _generate_encryption_key(self) -> bytes:
        """Générer une clé de chiffrement sécurisée"""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(b"harmonic-ai-master-key"))
        return key
    
    def encrypt_data(self, data: str) -> str:
        """Chiffrer des données sensibles"""
        fernet = Fernet(self.encryption_key)
        encrypted = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Déchiffrer des données"""
        fernet = Fernet(self.encryption_key)
        decoded = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted = fernet.decrypt(decoded)
        return decrypted.decode()
    
    def generate_api_key_pair(self, tier: str, customer_id: str, 
                             metadata: Optional[Dict] = None) -> Dict:
        """
        Générer une paire de clés API sécurisée
        
        Args:
            tier: Package (starter/pro/enterprise)
            customer_id: Identifiant unique client
            metadata: Données supplémentaires optionnelles
            
        Returns:
            Dict avec clés et metadata
        """
        # Générer clés cryptographiquement sécurisées
        api_key = secrets.token_urlsafe(self.api_key_length)
        secret_key = secrets.token_urlsafe(self.secret_key_length)
        
        # Créer un identifiant unique pour la clé
        key_id = f"harmonic-ai-{customer_id}-{int(time.time())}"
        
        # Préparer les données à stocker
        key_data = {
            'api_key': api_key,
            'secret_key': secret_key,  # Stocké chiffré
            'tier': tier,
            'customer_id': customer_id,
            'key_id': key_id,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=365)).isoformat(),
            'is_active': True,
            'request_count': 0,
            'last_used': None,
            'metadata': metadata or {}
        }
        
        try:
            # Stocker dans AWS Secrets Manager
            secret_name = f"harmonic-ai/{customer_id}/api-keys/{key_id}"
            
            # Chiffrer la secret_key avant stockage
            encrypted_secret = self.encrypt_data(secret_key)
            
            secret_value = {
                'api_key': api_key,
                'secret_key_encrypted': encrypted_secret,
                'tier': tier,
                'key_id': key_id,
                'created_at': key_data['created_at'],
                'expires_at': key_data['expires_at']
            }
            
            self.secrets_client.create_secret(
                Name=secret_name,
                SecretString=json.dumps(secret_value),
                Description=f"API Key for Harmonic AI customer {customer_id}",
                Tags=[
                    {'Key': 'Project', 'Value': 'Harmonic-AI'},
                    {'Key': 'Tier', 'Value': tier},
                    {'Key': 'Customer', 'Value': customer_id},
                    {'Key': 'Environment', 'Value': 'Production'}
                ]
            )
            
            # Stocker metadata dans Redis pour performances
            redis_key = f"api_key:{api_key}"
            metadata_for_redis = {
                'tier': tier,
                'customer_id': customer_id,
                'key_id': key_id,
                'created_at': key_data['created_at'],
                'is_active': '1',
                'request_count': '0'
            }
            
            self.redis_client.hset(redis_key, mapping=metadata_for_redis)
            self.redis_client.expire(redis_key, 3600)  # 1 heure TTL
            
            # Mettre en cache localement
            self.key_cache[api_key] = {
                'tier': tier,
                'customer_id': customer_id,
                'is_active': True,
                'cached_at': time.time()
            }
            
            # Log l'événement
            self._log_security_event(
                event_type="API_KEY_GENERATED",
                details=f"Generated API key for customer {customer_id}, tier {tier}",
                severity="INFO"
            )
            
            return {
                'api_key': api_key,
                'secret_key': secret_key,  # À transmettre une seule fois au client
                'key_id': key_id,
                'tier': tier,
                'customer_id': customer_id,
                'created_at': key_data['created_at'],
                'expires_at': key_data['expires_at'],
                'warning': 'Store the secret_key securely. It will not be shown again.'
            }
            
        except Exception as e:
            self._log_security_event(
                event_type="API_KEY_GENERATION_FAILED",
                details=f"Failed to generate API key: {str(e)}",
                severity="ERROR"
            )
            raise
    
    def verify_request(self, api_key: str, signature: str, 
                      timestamp: str, payload: str, 
                      nonce: Optional[str] = None) -> Tuple[bool, Dict]:
        """
        Vérifier une requête API avec protection avancée
        
        Args:
            api_key: Clé API publique
            signature: Signature HMAC de la requête
            timestamp: Timestamp de la requête (ISO format)
            payload: Données de la requête (JSON string)
            nonce: Valeur unique pour prévenir replay attacks
            
        Returns:
            Tuple (is_valid, metadata)
        """
        start_time = time.time()
        
        try:
            # 1. Vérifier format de base
            if not all([api_key, signature, timestamp, payload]):
                self._log_security_event(
                    event_type="INVALID_REQUEST_FORMAT",
                    details="Missing required authentication fields",
                    severity="WARNING"
                )
                return False, {'error': 'Missing authentication fields'}
            
            # 2. Vérifier timestamp (prévention replay attacks)
            try:
                request_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                now = datetime.utcnow()
                time_diff = abs((now - request_time).total_seconds())
                
                if time_diff > 300:  # 5 minutes de tolérance
                    self._log_security_event(
                        event_type="EXPIRED_TIMESTAMP",
                        details=f"Timestamp expired: {time_diff} seconds difference",
                        severity="WARNING"
                    )
                    return False, {'error': 'Timestamp expired'}
                    
            except ValueError:
                self._log_security_event(
                    event_type="INVALID_TIMESTAMP",
                    details=f"Invalid timestamp format: {timestamp}",
                    severity="WARNING"
                )
                return False, {'error': 'Invalid timestamp format'}
            
            # 3. Vérifier nonce pour replay protection
            if nonce:
                nonce_key = f"nonce:{api_key}:{nonce}"
                if self.redis_client.exists(nonce_key):
                    self._log_security_event(
                        event_type="REPLAY_ATTACK_DETECTED",
                        details=f"Replay attack detected with nonce: {nonce}",
                        severity="HIGH"
                    )
                    return False, {'error': 'Replay attack detected'}
                
                # Stocker le nonce pour 10 minutes
                self.redis_client.setex(nonce_key, 600, 'used')
            
            # 4. Vérifier rate limiting
            if not self._check_rate_limit(api_key):
                self._log_security_event(
                    event_type="RATE_LIMIT_EXCEEDED",
                    details=f"Rate limit exceeded for API key: {api_key}",
                    severity="HIGH"
                )
                return False, {'error': 'Rate limit exceeded'}
            
            # 5. Vérifier clé API dans cache local
            cached_data = self.key_cache.get(api_key)
            if cached_data and (time.time() - cached_data.get('cached_at', 0)) < self.cache_ttl:
                if not cached_data.get('is_active', False):
                    self._log_security_event(
                        event_type="INACTIVE_API_KEY",
                        details=f"Inactive API key used: {api_key}",
                        severity="WARNING"
                    )
                    return False, {'error': 'API key inactive'}
                
                tier = cached_data['tier']
                customer_id = cached_data['customer_id']
                
            else:
                # 6. Vérifier dans Redis
                redis_key = f"api_key:{api_key}"
                redis_data = self.redis_client.hgetall(redis_key)
                
                if redis_data:
                    if redis_data.get('is_active') != '1':
                        self._log_security_event(
                            event_type="INACTIVE_API_KEY",
                            details=f"Inactive API key used: {api_key}",
                            severity="WARNING"
                        )
                        return False, {'error': 'API key inactive'}
                    
                    tier = redis_data['tier']
                    customer_id = redis_data['customer_id']
                    
                    # Mettre en cache local
                    self.key_cache[api_key] = {
                        'tier': tier,
                        'customer_id': customer_id,
                        'is_active': True,
                        'cached_at': time.time()
                    }
                    
                else:
                    # 7. Vérifier dans AWS Secrets Manager (dernier recours)
                    try:
                        # Chercher le secret correspondant à cette clé API
                        # Note: Cette opération est coûteuse, donc à utiliser avec parcimonie
                        secret_name = self._find_secret_for_api_key(api_key)
                        if not secret_name:
                            self._log_security_event(
                                event_type="INVALID_API_KEY",
                                details=f"Invalid API key: {api_key}",
                                severity="HIGH"
                            )
                            return False, {'error': 'Invalid API key'}
                        
                        # Récupérer le secret
                        secret_response = self.secrets_client.get_secret_value(
                            SecretId=secret_name
                        )
                        secret_data = json.loads(secret_response['SecretString'])
                        
                        # Déchiffrer la secret_key
                        encrypted_secret = secret_data['secret_key_encrypted']
                        secret_key = self.decrypt_data(encrypted_secret)
                        
                        tier = secret_data['tier']
                        customer_id = secret_data.get('customer_id', 'unknown')
                        key_id = secret_data['key_id']
                        
                        # Mettre en cache Redis pour futures requêtes
                        metadata_for_redis = {
                            'tier': tier,
                            'customer_id': customer_id,
                            'key_id': key_id,
                            'is_active': '1',
                            'request_count': '0'
                        }
                        self.redis_client.hset(redis_key, mapping=metadata_for_redis)
                        self.redis_client.expire(redis_key, 3600)
                        
                        # Mettre en cache local
                        self.key_cache[api_key] = {
                            'tier': tier,
                            'customer_id': customer_id,
                            'is_active': True,
                            'cached_at': time.time()
                        }
                        
                    except ClientError:
                        self._log_security_event(
                            event_type="INVALID_API_KEY",
                            details=f"Invalid API key: {api_key}",
                            severity="HIGH"
                        )
                        return False, {'error': 'Invalid API key'}
            
            # 8. Récupérer la secret_key pour vérification signature
            secret_key = self._get_secret_key(api_key, customer_id)
            if not secret_key:
                self._log_security_event(
                    event_type="SECRET_KEY_NOT_FOUND",
                    details=f"Secret key not found for API key: {api_key}",
                    severity="HIGH"
                )
                return False, {'error': 'Secret key not found'}
            
            # 9. Vérifier signature HMAC
            message = f"{timestamp}:{payload}"
            if nonce:
                message = f"{nonce}:{message}"
            
            expected_signature = self._calculate_hmac(secret_key, message)
            
            if not hmac.compare_digest(signature, expected_signature):
                self._log_security_event(
                    event_type="INVALID_SIGNATURE",
                    details=f"Invalid signature for API key: {api_key}",
                    severity="HIGH"
                )
                return False, {'error': 'Invalid signature'}
            
            # 10. Mettre à jour les statistiques
            self._update_request_stats(api_key, customer_id)
            
            # 11. Calculer temps de traitement
            processing_time = time.time() - start_time
            
            # Log la requête réussie
            self._log_request(
                api_key=api_key,
                customer_id=customer_id,
                tier=tier,
                processing_time=processing_time,
                success=True
            )
            
            return True, {
                'customer_id': customer_id,
                'tier': tier,
                'processing_time': processing_time,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self._log_security_event(
                event_type="AUTHENTICATION_ERROR",
                details=f"Authentication error: {str(e)}",
                severity="ERROR"
            )
            return False, {'error': 'Internal authentication error'}
    
    def _find_secret_for_api_key(self, api_key: str) -> Optional[str]:
        """Trouver le nom du secret correspondant à une clé API"""
        # Cette méthode est simplifiée - en production, vous auriez
        # une table de correspondance ou un index
        try:
            # Lister tous les secrets avec un filtre
            response = self.secrets_client.list_secrets(
                Filters=[
                    {
                        'Key': 'tag-key',
                        'Values': ['Project']
                    },
                    {
                        'Key': 'tag-value',
                        'Values': ['Harmonic-AI']
                    }
                ]
            )
            
            for secret in response['SecretList']:
                secret_name = secret['Name']
                if api_key in secret_name:
                    return secret_name
                    
        except ClientError:
            pass
        
        return None
    
    def _get_secret_key(self, api_key: str, customer_id: str) -> Optional[str]:
        """Récupérer la secret_key pour une clé API donnée"""
        try:
            # Construire le nom du secret
            secret_name = f"harmonic-ai/{customer_id}/api-keys/*"
            
            # Chercher le secret correspondant
            # Note: En production, vous auriez un meilleur système de recherche
            response = self.secrets_client.list_secrets(
                Filters=[
                    {
                        'Key': 'name',
                        'Values': [f"harmonic-ai/{customer_id}/api-keys/"]
                    }
                ]
            )
            
            for secret in response['SecretList']:
                # Récupérer le secret
                secret_response = self.secrets_client.get_secret_value(
                    SecretId=secret['Name']
                )
                secret_data = json.loads(secret_response['SecretString'])
                
                if secret_data.get('api_key') == api_key:
                    # Déchiffrer la secret_key
                    encrypted_secret = secret_data['secret_key_encrypted']
                    return self.decrypt_data(encrypted_secret)
                    
        except (ClientError, KeyError):
            pass
        
        return None
    
    def _calculate_hmac(self, secret_key: str, message: str) -> str:
        """Calculer HMAC-SHA256"""
        return hmac.new(
            secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _check_rate_limit(self, api_key: str) -> bool:
        """Vérifier rate limiting"""
        key = f"rate_limit:{api_key}:{int(time.time() // 60)}"
        
        # Incrémenter le compteur
        current_count = self.redis_client.incr(key)
        
        # Définir expiration (2 minutes pour éviter les problèmes d'horloge)
        if current_count == 1:
            self.redis_client.expire(key, 120)
        
        # Vérifier limite
        tier = self._get_tier_for_api_key(api_key)
        limits = {
            'starter': 100,
            'pro': 1000,
            'enterprise': 10000
        }
        
        limit = limits.get(tier, 100)
        return current_count <= limit
    
    def _get_tier_for_api_key(self, api_key: str) -> str:
        """Obtenir le tier pour une clé API"""
        cached = self.key_cache.get(api_key)
        if cached:
            return cached.get('tier', 'starter')
        
        redis_key = f"api_key:{api_key}"
        tier = self.redis_client.hget(redis_key, 'tier')
        return tier.decode() if tier else 'starter'
    
    def _update_request_stats(self, api_key: str, customer_id: str):
        """Mettre à jour les statistiques de requêtes"""
        # Mettre à jour Redis
        redis_key = f"api_key:{api_key}"
        self.redis_client.hincrby(redis_key, 'request_count', 1)
        self.redis_client.hset(redis_key, 'last_used', datetime.utcnow().isoformat())
        
        # Mettre à jour cache local
        if api_key in self.key_cache:
            self.key_cache[api_key]['last_used'] = time.time()
    
    def _log_request(self, api_key: str, customer_id: str, tier: str,
                    processing_time: float, success: bool):
        """Logger une requête"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'api_key': api_key[:8] + '...',  # Masquer partie de la clé
            'customer_id': customer_id,
            'tier': tier,
            'processing_time': processing_time,
            'success': success,
            'type': 'API_REQUEST'
        }
        
        self.request_log.append(log_entry)
        
        # Garder seulement les 1000 dernières entrées
        if len(self.request_log) > 1000:
            self.request_log = self.request_log[-1000:]
    
    def _log_security_event(self, event_type: str, details: str, severity: str):
        """Logger un événement de sécurité"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'details': details,
            'severity': severity,
            'type': 'SECURITY_EVENT'
        }
        
        self.security_events.append(event)
        
        # Garder seulement les 500 derniers événements
        if len(self.security_events) > 500:
            self.security_events = self.security_events[-500:]
        
        # Log vers CloudWatch ou système centralisé
        print(f"[SECURITY] {severity}: {event_type} - {details}")
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Révoquer une clé API"""
        try:
            # Désactiver dans Redis
            redis_key = f"api_key:{api_key}"
            self.redis_client.hset(redis_key, 'is_active', '0')
            self.redis_client.hset(redis_key, 'revoked_at', datetime.utcnow().isoformat())
            
            # Supprimer du cache local
            if api_key in self.key_cache:
                del self.key_cache[api_key]
            
            # Marquer comme révoqué dans Secrets Manager
            # (En production, vous auriez une meilleure méthode)
            
            self._log_security_event(
                event_type="API_KEY_REVOKED",
                details=f"API key revoked: {api_key[:8]}...",
                severity="INFO"
            )
            
            return True
            
        except Exception as e:
            self._log_security_event(
                event_type="API_KEY_REVOCATION_FAILED",
                details=f"Failed to revoke API key: {str(e)}",
                severity="ERROR"
            )
            return False
    
    def get_key_metrics(self, api_key: str) -> Optional[Dict]:
        """Obtenir les métriques d'utilisation d'une clé API"""
        redis_key = f"api_key:{api_key}"
        data = self.redis_client.hgetall(redis_key)
        
        if not data:
            return None
        
        return {
            'api_key': api_key[:8] + '...',
            'customer_id': data.get('customer_id', 'unknown'),
            'tier': data.get('tier', 'unknown'),
            'request_count': int(data.get('request_count', 0)),
            'last_used': data.get('last_used', 'never'),
            'is_active': data.get('is_active', '0') == '1',
            'created_at': data.get('created_at', 'unknown')
        }
    
    def get_security_report(self, hours: int = 24) -> Dict:
        """Générer un rapport de sécurité"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        recent_events = [
            event for event in self.security_events
            if datetime.fromisoformat(event['timestamp']) > cutoff
        ]
        
        recent_requests = [
            req for req in self.request_log
            if datetime.fromisoformat(req['timestamp']) > cutoff
        ]
        
        # Analyser les événements
        event_counts = {}
        for event in recent_events:
            event_type = event['event_type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Analyser les requêtes
        success_count = sum(1 for req in recent_requests if req['success'])
        total_requests = len(recent_requests)
        success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'report_period_hours': hours,
            'total_security_events': len(recent_events),
            'total_api_requests': total_requests,
            'api_success_rate': success_rate,
            'event_breakdown': event_counts,
            'top_events': sorted(event_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'recent_high_severity': [
                event for event in recent_events 
                if event['severity'] in ['HIGH', 'CRITICAL']
            ][:10]
        }


# Middleware FastAPI pour intégration
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

security = HTTPBearer()
auth_system = AdvancedAPIAuthSystem()

app = FastAPI(title="Harmonic AI API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def authenticate_api_request(request: Request) -> Dict:
    """Middleware d'authentification pour FastAPI"""
    
    # Récupérer headers
    api_key = request.headers.get('X-API-Key')
    signature = request.headers.get('X-Signature')
    timestamp = request.headers.get('X-Timestamp')
    nonce = request.headers.get('X-Nonce')
    
    if not api_key:
        # Essayer avec Bearer token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            api_key = auth_header[7:]
    
    # Récupérer body
    body = await request.body()
    payload_hash = hashlib.sha256(body).hexdigest() if body else ""
    
    # Vérifier authentification
    is_valid, metadata = auth_system.verify_request(
        api_key=api_key,
        signature=signature,
        timestamp=timestamp,
        payload=payload_hash,
        nonce=nonce
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail=metadata.get('error', 'Authentication failed')
        )
    
    # Ajouter metadata à la requête
    request.state.auth_metadata = metadata
    
    return metadata

# Routes API
@app.get("/")
async def root():
    return {
        "service": "Harmonic AI API",
        "version": "1.0.0",
        "status": "operational",
        "description": "Deterministic AI with guaranteed verification",
        "endpoints": {
            "health": "/health",
            "generate": "/generate",
            "metrics": "/metrics",
            "security": "/security/report"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Harmonic AI API",
        "version": "1.0.0"
    }

@app.post("/generate")
async def generate_text(request: Request, auth_data: Dict = Depends(authenticate_api_request)):
    """Endpoint principal pour génération de texte"""
    
    try:
        # Récupérer les données de la requête
        data = await request.json()
        prompt = data.get('prompt', '')
        parameters = data.get('parameters', {})
        
        # Validation
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Appeler le moteur d'IA (simplifié pour l'exemple)
        # En production, vous appelleriez votre modèle Harmonic AI
        
        # Simuler un traitement
        import random
        response_text = f"Response to: {prompt[:50]}..."
        processing_time = random.uniform(0.5, 2.0)
        
        # Générer un response_id unique
        response_id = hashlib.sha256(
            f"{prompt}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()
        
        return {
            "response": response_text,
            "response_id": response_id,
            "processing_time": processing_time,
            "timestamp": datetime.utcnow().isoformat(),
            "customer_id": auth_data.get('customer_id'),
            "tier": auth_data.get('tier'),
            "verified": True,
            "citations": [
                {
                    "source": "internal_knowledge_base",
                    "confidence": 0.95,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }
        
    except Exception as e:
        auth_system._log_security_event(
            event_type="API_GENERATE_ERROR",
            details=f"Generate endpoint error: {str(e)}",
            severity="ERROR"
        )
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/metrics")
async def get_metrics(api_key: str):
    """Obtenir les métriques d'une clé API"""
    metrics = auth_system.get_key_metrics(api_key)
    
    if not metrics:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return metrics

@app.get("/security/report")
async def get_security_report(hours: int = 24):
    """Obtenir un rapport de sécurité"""
    report = auth_system.get_security_report(hours)
    return report

@app.post("/admin/generate-key")
async def admin_generate_key(
    tier: str,
    customer_id: str,
    metadata: Optional[str] = None,
    admin_token: str = Depends(security)
):
    """Endpoint admin pour générer des clés API"""
    
    # Vérifier token admin (simplifié)
    if admin_token.credentials != "harmonic-admin-secret-token":
        raise HTTPException(status_code=403, detail="Invalid admin token")
    
    # Parser metadata
    metadata_dict = json.loads(metadata) if metadata else None
    
    # Générer la clé
    result = auth_system.generate_api_key_pair(
        tier=tier,
        customer_id=customer_id,
        metadata=metadata_dict
    )
    
    return result

@app.post("/admin/revoke-key")
async def admin_revoke_key(
    api_key: str,
    admin_token: HTTPAuthorizationCredentials = Depends(security)
):
    """Endpoint admin pour révoquer des clés API"""
    
    if admin_token.credentials != "harmonic-admin-secret-token":
        raise HTTPException(status_code=403, detail="Invalid admin token")
    
    success = auth_system.revoke_api_key(api_key)
    
    return {
        "success": success,
        "api_key": api_key[:8] + '...',
        "timestamp": datetime.utcnow().isoformat()
    }


# Client example
class HarmonicAIClient:
    """Client pour interagir avec l'API Harmonic AI"""
    
    def __init__(self, api_key: str, secret_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.nonce_counter = 0
        
    def _generate_nonce(self) -> str:
        """Générer une valeur unique pour chaque requête"""
        self.nonce_counter += 1
        timestamp = int(time.time() * 1000)
        return f"{timestamp}-{self.nonce_counter}-{secrets.token_hex(4)}"
    
    def _sign_request(self, timestamp: str, payload: str, nonce: Optional[str] = None) -> str:
        """Signer une requête"""
        message = f"{timestamp}:{payload}"
        if nonce:
            message = f"{nonce}:{message}"
        
        return hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def generate_text(self, prompt: str, parameters: Optional[Dict] = None) -> Dict:
        """Générer du texte via l'API"""
        import requests
        
        # Préparer les données
        payload_data = {
            'prompt': prompt,
            'parameters': parameters or {}
        }
        payload = json.dumps(payload_data)
        payload_hash = hashlib.sha256(payload.encode()).hexdigest()
        
        # Générer nonce et timestamp
        nonce = self._generate_nonce()
        timestamp = datetime.utcnow().isoformat()
        
        # Signer la requête
        signature = self._sign_request(timestamp, payload_hash, nonce)
        
        # Headers
        headers = {
            'X-API-Key': self.api_key,
            'X-Signature': signature,
            'X-Timestamp': timestamp,
            'X-Nonce': nonce,
            'Content-Type': 'application/json'
        }
        
        # Envoyer la requête
        response = requests.post(
            f"{self.base_url}/generate",
            data=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API error: {response.status_code} - {response.text}")


# Exemple d'utilisation
if __name__ == "__main__":
    print("=== Harmonic AI Advanced Auth System ===")
    
    # Initialiser le système
    auth = AdvancedAPIAuthSystem()
    
    # Générer une clé API
    print("\n1. Génération d'une clé API...")
    key_pair = auth.generate_api_key_pair(
        tier="pro",
        customer_id="customer-123",
        metadata={"company": "Example Corp", "contact": "john@example.com"}
    )
    
    print(f"API Key: {key_pair['api_key'][:16]}...")
    print(f"Tier: {key_pair['tier']}")
    print(f"Customer ID: {key_pair['customer_id']}")
    
    # Simuler une requête
    print("\n2. Simulation d'une requête API...")
    
    # Données de test
    test_payload = json.dumps({
        "prompt": "Explain the benefits of deterministic AI",
        "parameters": {"max_tokens": 500}
    })
    test_payload_hash = hashlib.sha256(test_payload.encode()).hexdigest()
    test_timestamp = datetime.utcnow().isoformat()
    test_nonce = secrets.token_hex(8)
    
    # Calculer signature
    test_signature = auth._calculate_hmac(
        key_pair['secret_key'],
        f"{test_nonce}:{test_timestamp}:{test_payload_hash}"
    )
    
    # Vérifier la requête
    is_valid, metadata = auth.verify_request(
        api_key=key_pair['api_key'],
        signature=test_signature,
        timestamp=test_timestamp,
        payload=test_payload_hash,
        nonce=test_nonce
    )
    
    print(f"Requête valide: {is_valid}")
    if is_valid:
        print(f"Customer ID: {metadata.get('customer_id')}")
        print(f"Tier: {metadata.get('tier')}")
    
    # Obtenir un rapport de sécurité
    print("\n3. Rapport de sécurité (24h)...")
    report = auth.get_security_report(hours=24)
    print(f"Événements de sécurité: {report['total_security_events']}")
    print(f"Requêtes API: {report['total_api_requests']}")
    print(f"Taux de succès: {report['api_success_rate']:.2f}%")
    
    print("\n=== Configuration terminée ===")