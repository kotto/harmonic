import os
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import sqlite3
from contextlib import contextmanager

@dataclass
class User:
    """Utilisateur Harmonic AI"""
    id: str
    email: str
    tier: str  # 'starter', 'pro', 'enterprise'
    api_key: str
    monthly_tokens: int
    tokens_used: int = 0
    created_at: str = None
    last_login: str = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    @property
    def tokens_remaining(self) -> int:
        return max(0, self.monthly_tokens - self.tokens_used)
    
    @property
    def usage_percentage(self) -> float:
        if self.monthly_tokens == 0:
            return 0.0
        return (self.tokens_used / self.monthly_tokens) * 100

@dataclass
class APIRequest:
    """Requête API enregistrée"""
    id: str
    user_id: str
    endpoint: str
    prompt_hash: str
    tokens_used: int
    response_id: str
    timestamp: str
    duration_ms: int
    
    @classmethod
    def from_request(cls, user_id: str, endpoint: str, prompt: str, tokens_used: int, response_id: str, duration_ms: int):
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        return cls(
            id=secrets.token_hex(8),
            user_id=user_id,
            endpoint=endpoint,
            prompt_hash=prompt_hash,
            tokens_used=tokens_used,
            response_id=response_id,
            timestamp=datetime.now().isoformat(),
            duration_ms=duration_ms
        )

class HarmonicAIDashboard:
    """Dashboard MVP pour Harmonic AI SaaS"""
    
    def __init__(self, db_path: str = "harmonic_ai.db"):
        self.db_path = db_path
        self._init_db()
        
        # Configuration des tiers
        self.tiers_config = {
            'starter': {
                'monthly_tokens': 10000,
                'features': ['mode_verifie_basique', 'citations_obligatoires', 'support_email'],
                'price': 99
            },
            'pro': {
                'monthly_tokens': 100000,
                'features': ['mode_verifie_complet', 'citations_avancees', 'support_prioritaire', 'dashboard_analytics'],
                'price': 499
            },
            'enterprise': {
                'monthly_tokens': 1000000,
                'features': ['determinisme_garanti', 'audit_trail', 'support_24_7', 'sla_99_9', 'api_dediee'],
                'price': 2499
            }
        }
    
    @contextmanager
    def _get_connection(self):
        """Contexte pour la connexion DB"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialiser la base de données"""
        with self._get_connection() as conn:
            # Table utilisateurs
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    tier TEXT NOT NULL,
                    api_key TEXT UNIQUE NOT NULL,
                    monthly_tokens INTEGER NOT NULL,
                    tokens_used INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    last_login TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Table requêtes API
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_requests (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    tokens_used INTEGER NOT NULL,
                    response_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Table facturation
            conn.execute('''
                CREATE TABLE IF NOT EXISTS billing (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    stripe_customer_id TEXT,
                    stripe_subscription_id TEXT,
                    amount INTEGER NOT NULL,
                    currency TEXT DEFAULT 'usd',
                    status TEXT NOT NULL,
                    invoice_url TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
    
    def create_user(self, email: str, tier: str = 'starter') -> Tuple[bool, Optional[User]]:
        """Créer un nouvel utilisateur"""
        if tier not in self.tiers_config:
            return False, None
        
        # Générer une clé API sécurisée
        api_key = f"hk_{secrets.token_hex(16)}"
        user_id = hashlib.sha256(f"{email}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        user = User(
            id=user_id,
            email=email,
            tier=tier,
            api_key=api_key,
            monthly_tokens=self.tiers_config[tier]['monthly_tokens']
        )
        
        with self._get_connection() as conn:
            try:
                conn.execute('''
                    INSERT INTO users (id, email, tier, api_key, monthly_tokens, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user.id, user.email, user.tier, user.api_key, user.monthly_tokens, user.created_at))
                
                return True, user
                
            except sqlite3.IntegrityError:
                return False, None
    
    def authenticate_user(self, api_key: str) -> Optional[User]:
        """Authentifier un utilisateur par clé API"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM users 
                WHERE api_key = ? AND is_active = 1
            ''', (api_key,))
            
            row = cursor.fetchone()
            if row:
                # Mettre à jour last_login
                conn.execute('''
                    UPDATE users SET last_login = ? WHERE id = ?
                ''', (datetime.now().isoformat(), row['id']))
                
                return User(**dict(row))
        
        return None
    
    def log_api_request(self, request: APIRequest) -> bool:
        """Enregistrer une requête API"""
        with self._get_connection() as conn:
            try:
                # Ajouter la requête
                conn.execute('''
                    INSERT INTO api_requests 
                    (id, user_id, endpoint, prompt_hash, tokens_used, response_id, timestamp, duration_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    request.id, request.user_id, request.endpoint, 
                    request.prompt_hash, request.tokens_used, request.response_id,
                    request.timestamp, request.duration_ms
                ))
                
                # Mettre à jour le compteur de tokens
                conn.execute('''
                    UPDATE users 
                    SET tokens_used = tokens_used + ? 
                    WHERE id = ?
                ''', (request.tokens_used, request.user_id))
                
                return True
                
            except sqlite3.Error:
                return False
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Obtenir les statistiques d'un utilisateur"""
        with self._get_connection() as conn:
            # Informations utilisateur
            cursor = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user_row = cursor.fetchone()
            
            if not user_row:
                return {}
            
            user = User(**dict(user_row))
            
            # Statistiques des 30 derniers jours
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            
            cursor = conn.execute('''
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(tokens_used) as total_tokens,
                    AVG(duration_ms) as avg_duration
                FROM api_requests 
                WHERE user_id = ? AND timestamp >= ?
            ''', (user_id, thirty_days_ago))
            
            stats_row = cursor.fetchone()
            
            # Requêtes récentes
            cursor = conn.execute('''
                SELECT * FROM api_requests 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 10
            ''', (user_id,))
            
            recent_requests = [dict(row) for row in cursor.fetchall()]
            
            return {
                'user': asdict(user),
                'stats': dict(stats_row) if stats_row else {},
                'recent_requests': recent_requests,
                'tier_config': self.tiers_config[user.tier]
            }
    
    def check_rate_limit(self, user_id: str, tokens_needed: int) -> Tuple[bool, str]:
        """Vérifier les limites de taux et de tokens"""
        with self._get_connection() as conn:
            # Vérifier les tokens restants
            cursor = conn.execute('''
                SELECT monthly_tokens, tokens_used FROM users WHERE id = ?
            ''', (user_id,))
            
            row = cursor.fetchone()
            if not row:
                return False, "Utilisateur non trouvé"
            
            monthly_tokens = row['monthly_tokens']
            tokens_used = row['tokens_used']
            
            if tokens_used + tokens_needed > monthly_tokens:
                return False, f"Limite de tokens dépassée ({tokens_used}/{monthly_tokens})"
            
            # Vérifier le rate limit (max 10 requêtes/minute)
            one_minute_ago = (datetime.now() - timedelta(minutes=1)).isoformat()
            
            cursor = conn.execute('''
                SELECT COUNT(*) as request_count 
                FROM api_requests 
                WHERE user_id = ? AND timestamp >= ?
            ''', (user_id, one_minute_ago))
            
            request_count = cursor.fetchone()['request_count']
            
            if request_count >= 10:
                return False, "Rate limit dépassé (10 req/min)"
            
            return True, "OK"
    
    def generate_api_key(self, user_id: str) -> Optional[str]:
        """Générer une nouvelle clé API pour un utilisateur"""
        new_api_key = f"hk_{secrets.token_hex(16)}"
        
        with self._get_connection() as conn:
            try:
                conn.execute('''
                    UPDATE users SET api_key = ? WHERE id = ?
                ''', (new_api_key, user_id))
                
                return new_api_key
                
            except sqlite3.Error:
                return None
    
    def upgrade_tier(self, user_id: str, new_tier: str) -> Tuple[bool, str]:
        """Mettre à niveau le tier d'un utilisateur"""
        if new_tier not in self.tiers_config:
            return False, "Tier invalide"
        
        with self._get_connection() as conn:
            try:
                conn.execute('''
                    UPDATE users 
                    SET tier = ?, monthly_tokens = ?
                    WHERE id = ?
                ''', (
                    new_tier, 
                    self.tiers_config[new_tier]['monthly_tokens'],
                    user_id
                ))
                
                return True, f"Tier mis à jour vers {new_tier}"
                
            except sqlite3.Error as e:
                return False, str(e)
    
    def get_admin_stats(self) -> Dict:
        """Obtenir les statistiques admin"""
        with self._get_connection() as conn:
            # Total utilisateurs
            cursor = conn.execute('SELECT COUNT(*) as total_users FROM users')
            total_users = cursor.fetchone()['total_users']
            
            # Utilisateurs actifs
            cursor = conn.execute('SELECT COUNT(*) as active_users FROM users WHERE is_active = 1')
            active_users = cursor.fetchone()['active_users']
            
            # Répartition par tier
            cursor = conn.execute('''
                SELECT tier, COUNT(*) as count 
                FROM users 
                GROUP BY tier
            ''')
            tier_distribution = {row['tier']: row['count'] for row in cursor.fetchall()}
            
            # Requêtes totales
            cursor = conn.execute('SELECT COUNT(*) as total_requests FROM api_requests')
            total_requests = cursor.fetchone()['total_requests']
            
            # Tokens utilisés total
            cursor = conn.execute('SELECT SUM(tokens_used) as total_tokens FROM api_requests')
            total_tokens = cursor.fetchone()['total_tokens'] or 0
            
            # Requêtes récentes (24h)
            twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).isoformat()
            cursor = conn.execute('''
                SELECT COUNT(*) as recent_requests 
                FROM api_requests 
                WHERE timestamp >= ?
            ''', (twenty_four_hours_ago,))
            recent_requests = cursor.fetchone()['recent_requests']
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'tier_distribution': tier_distribution,
                'total_requests': total_requests,
                'total_tokens': total_tokens,
                'recent_requests_24h': recent_requests,
                'timestamp': datetime.now().isoformat()
            }


# Interface web simple avec Flask
from flask import Flask, request, jsonify, render_template_string
import functools

app = Flask(__name__)
dashboard = HarmonicAIDashboard()

# Template HTML pour le dashboard
DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Harmonic AI Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid #334155; }
        .logo { display: flex; align-items: center; gap: 12px; font-size: 24px; font-weight: bold; }
        .logo-icon { color: #10b981; font-size: 28px; }
        .user-info { display: flex; align-items: center; gap: 16px; }
        .btn { background: #10b981; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 500; }
        .btn:hover { background: #0ea271; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .stat-card { background: #1e293b; padding: 24px; border-radius: 12px; border-left: 4px solid #10b981; }
        .stat-title { color: #94a3b8; font-size: 14px; margin-bottom: 8px; }
        .stat-value { font-size: 32px; font-weight: bold; }
        .usage-bar { height: 8px; background: #334155; border-radius: 4px; margin-top: 12px; overflow: hidden; }
        .usage-fill { height: 100%; background: #10b981; border-radius: 4px; }
        .requests-table { background: #1e293b; border-radius: 12px; overflow: hidden; }
        .table-header { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; padding: 16px 24px; background: #0f172a; font-weight: 600; }
        .table-row { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; padding: 16px 24px; border-bottom: 1px solid #334155; }
        .table-row:hover { background: #1e293b; }
        .api-key-section { background: #1e293b; padding: 24px; border-radius: 12px; margin-top: 40px; }
        .api-key { font-family: monospace; background: #0f172a; padding: 12px; border-radius: 8px; margin: 12px 0; }
        .tier-badge { background: #10b981; color: white; padding: 4px 12px; border-radius: 20px; font-size: 14px; font-weight: 500; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <span class="logo-icon">φ</span>
                <span>Harmonic AI Dashboard</span>
            </div>
            <div class="user-info">
                <span class="tier-badge">{{ user.tier|upper }}</span>
                <span>{{ user.email }}</span>
                <button class="btn" onclick="generateNewKey()">Nouvelle clé API</button>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">Tokens utilisés</div>
                <div class="stat-value">{{ user.tokens_used|intcomma }}</div>
                <div class="usage-bar">
                    <div class="usage-fill" style="width: {{ user.usage_percentage }}%"></div>
                </div>
                <div class="stat-title">{{ user.usage_percentage|round(1) }}% de {{ user.monthly_tokens|intcomma }} tokens/mois</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">Tokens restants</div>
                <div class="stat-value">{{ user.tokens_remaining|intcomma }}</div>
                <div class="stat-title">Valable jusqu'au {{ next_reset_date }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">Requêtes totales</div>
                <div class="stat-value">{{ stats.total_requests or 0 }}</div>
                <div class="stat-title">30 derniers jours</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">Temps moyen</div>
                <div class="stat-value">{{ (stats.avg_duration or 0)|round }}ms</div>
                <div class="stat-title">Par requête</div>
            </div>
        </div>
        
        <div class="api-key-section">
            <h3>Votre clé API</h3>
            <div class="api-key">{{ user.api_key }}</div>
            <p style="color: #94a3b8; margin-top: 8px;">
                Utilisez cette clé pour authentifier vos requêtes à l'API Harmonic AI.
                Gardez-la secrète !
            </p>
        </div>
        
        {% if recent_requests %}
        <div style="margin-top: 40px;">
            <h3 style="margin-bottom: 20px;">Dernières requêtes</h3>
            <div class="requests-table">
                <div class="table-header">
                    <div>Date</div>
                    <div>Endpoint</div>
                    <div>Tokens</div>
                    <div>Durée</div>
                </div>
                {% for req in recent_requests %}
                <div class="table-row">
                    <div>{{ req.timestamp[:19] }}</div>
                    <div>{{ req.endpoint }}</div>
                    <div>{{ req.tokens_used }}</div>
                    <div>{{ req.duration_ms }}ms</div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
    </div>
    
    <script>
        function generateNewKey() {
            if (confirm('Générer une nouvelle clé API ? L\'ancienne sera invalidée.')) {
                fetch('/api/generate-key', {
                    method: 'POST',
                    headers: {
                        'Authorization': 'Bearer {{ user.api_key }}',
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Nouvelle clé API générée !');
                        location.reload();
                    } else {
                        alert('Erreur: ' + data.error);
                    }
                });
            }
        }
        
        // Formatage des nombres
        function intcomma(x) {
            return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
        }
    </script>
</body>
</html>
'''

def require_auth(f):
    """Décorateur pour l'authentification API"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
        user = dashboard.authenticate_user(api_key)
        
        if not user:
            return jsonify({'error': 'Authentification requise'}), 401
        
        return f(user, *args, **kwargs)
    return decorated

@app.route('/')
@require_auth
def dashboard_home(user):
    """Page principale du dashboard"""
    stats = dashboard.get_user_stats(user.id)
    
    # Calculer la date de réinitialisation (prochain 1er du mois)
    today = datetime.now()
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    
    # Template filters
    def intcomma(value):
        return f"{value:,}"
    
    def round_filter(value, digits=0):
        return round(value, digits)
    
    return render_template_string(
        DASHBOARD_TEMPLATE,
        user=stats['user'],
        stats=stats['stats'],
        recent_requests=stats['recent_requests'],
        next_reset_date=next_month.strftime('%d/%m/%Y'),
        intcomma=intcomma,
        round=round_filter
    )

@app.route('/api/stats', methods=['GET'])
@require_auth
def api_stats(user):
    """API: Obtenir les statistiques"""
    stats = dashboard.get_user_stats(user.id)
    return jsonify(stats)

@app.route('/api/generate-key', methods=['POST'])
@require_auth
def api_generate_key(user):
    """API: Générer une nouvelle clé API"""
    new_key = dashboard.generate_api_key(user.id)
    if new_key:
        return jsonify({'success': True, 'api_key': new_key})
    else:
        return jsonify({'success': False, 'error': 'Erreur de génération'}), 500

@app.route('/api/upgrade', methods=['POST'])
@require_auth
def api_upgrade(user):
    """API: Mettre à niveau le tier"""
    data = request.get_json()
    new_tier = data.get('tier')
    
    if not new_tier:
        return jsonify({'success': False, 'error': 'Tier non spécifié'}), 400
    
    success, message = dashboard.upgrade_tier(user.id, new_tier)
    return jsonify({'success': success, 'message': message})

@app.route('/admin/stats', methods=['GET'])
def admin_stats():
    """API Admin: Statistiques globales"""
    # Vérifier une clé admin (simplifiée)
    admin_key = request.headers.get('X-Admin-Key')
    if admin_key != os.getenv('ADMIN_KEY', 'admin123'):
        return jsonify({'error': 'Accès non autorisé'}), 403
    
    stats = dashboard.get_admin_stats()
    return jsonify(stats)

if __name__ == "__main__":
    print("HARMONIC AI DASHBOARD MVP")
    print("=" * 50)
    print("URL: http://localhost:5000")
    print("Pour créer un utilisateur de test:")
    print("  python -c \"from dashboard_mvp import HarmonicAIDashboard; d = HarmonicAIDashboard(); success, user = d.create_user('test@example.com', 'pro'); print(f'API Key: {user.api_key}' if success else 'Erreur')\"")
    print("=" * 50)
    
    # Créer un utilisateur de test si la DB est vide
    with dashboard._get_connection() as conn:
        cursor = conn.execute('SELECT COUNT(*) as count FROM users')
        if cursor.fetchone()['count'] == 0:
            success, test_user = dashboard.create_user('demo@harmonica.ai', 'pro')
            if success:
                print(f"UTILISATEUR DE TEST CREE: demo@harmonica.ai")
                print(f"CLE API: {test_user.api_key}")
    
    app.run(debug=True, port=5000)