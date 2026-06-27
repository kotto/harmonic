import os
import json
import smtplib
import sqlite3
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import secrets
import hashlib

class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class SupportTicket:
    """Ticket de support Harmonic AI"""
    id: str
    user_id: str
    user_email: str
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: str
    created_at: str
    updated_at: str
    assigned_to: Optional[str] = None
    resolution: Optional[str] = None
    
    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = TicketStatus(self.status)
        if isinstance(self.priority, str):
            self.priority = TicketPriority(self.priority)
    
    @property
    def is_open(self) -> bool:
        return self.status in [TicketStatus.OPEN, TicketStatus.IN_PROGRESS]
    
    @property
    def age_days(self) -> float:
        created = datetime.fromisoformat(self.created_at)
        now = datetime.now()
        return (now - created).total_seconds() / 86400

@dataclass
class SupportMessage:
    """Message dans un ticket de support"""
    id: str
    ticket_id: str
    sender_type: str  # 'user', 'support', 'system'
    sender_email: str
    content: str
    created_at: str
    attachments: Optional[List[str]] = None

@dataclass
class KnowledgeBaseArticle:
    """Article de la base de connaissances"""
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    views: int = 0
    helpful_count: int = 0
    not_helpful_count: int = 0
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at

class HarmonicAISupportSystem:
    """Système de support client pour Harmonic AI SaaS"""
    
    def __init__(self, db_path: str = "harmonic_ai_support.db"):
        self.db_path = db_path
        self._init_db()
        
        # Configuration email
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'smtp_username': os.getenv('SMTP_USERNAME', ''),
            'smtp_password': os.getenv('SMTP_PASSWORD', ''),
            'from_email': os.getenv('FROM_EMAIL', 'support@harmonica.ai'),
            'support_team_email': os.getenv('SUPPORT_TEAM_EMAIL', 'support@harmonica.ai')
        }
        
        # Catégories de support
        self.categories = {
            'billing': 'Facturation et paiements',
            'technical': 'Problèmes techniques',
            'api': 'API et intégration',
            'account': 'Compte et sécurité',
            'feature': 'Fonctionnalités et utilisation',
            'other': 'Autre'
        }
    
    def _init_db(self):
        """Initialiser la base de données de support"""
        with self._get_connection() as conn:
            # Table tickets
            conn.execute('''
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    user_email TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    category TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    assigned_to TEXT,
                    resolution TEXT
                )
            ''')
            
            # Table messages
            conn.execute('''
                CREATE TABLE IF NOT EXISTS support_messages (
                    id TEXT PRIMARY KEY,
                    ticket_id TEXT NOT NULL,
                    sender_type TEXT NOT NULL,
                    sender_email TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    attachments TEXT,
                    FOREIGN KEY (ticket_id) REFERENCES support_tickets (id)
                )
            ''')
            
            # Table base de connaissances
            conn.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    views INTEGER DEFAULT 0,
                    helpful_count INTEGER DEFAULT 0,
                    not_helpful_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Table FAQ
            conn.execute('''
                CREATE TABLE IF NOT EXISTS faq (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    category TEXT NOT NULL,
                    views INTEGER DEFAULT 0,
                    helpful_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            ''')
    
    def _get_connection(self):
        """Contexte pour la connexion DB"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def create_ticket(self, user_id: str, user_email: str, subject: str, 
                     description: str, category: str, priority: TicketPriority = TicketPriority.MEDIUM) -> Tuple[bool, Optional[SupportTicket]]:
        """Créer un nouveau ticket de support"""
        if category not in self.categories:
            category = 'other'
        
        ticket_id = f"TKT-{secrets.token_hex(6).upper()}"
        now = datetime.now().isoformat()
        
        ticket = SupportTicket(
            id=ticket_id,
            user_id=user_id,
            user_email=user_email,
            subject=subject,
            description=description,
            status=TicketStatus.OPEN,
            priority=priority,
            category=category,
            created_at=now,
            updated_at=now
        )
        
        with self._get_connection() as conn:
            try:
                conn.execute('''
                    INSERT INTO support_tickets 
                    (id, user_id, user_email, subject, description, status, priority, category, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ticket.id, ticket.user_id, ticket.user_email, ticket.subject,
                    ticket.description, ticket.status.value, ticket.priority.value,
                    ticket.category, ticket.created_at, ticket.updated_at
                ))
                
                # Envoyer email de confirmation
                self._send_ticket_created_email(ticket)
                
                # Notifier l'équipe support
                self._notify_support_team(ticket)
                
                return True, ticket
                
            except sqlite3.Error as e:
                print(f"❌ Erreur création ticket: {e}")
                return False, None
    
    def add_message(self, ticket_id: str, sender_type: str, sender_email: str, 
                   content: str, attachments: Optional[List[str]] = None) -> Tuple[bool, Optional[SupportMessage]]:
        """Ajouter un message à un ticket"""
        # Vérifier que le ticket existe
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return False, None
        
        message_id = f"MSG-{secrets.token_hex(6).upper()}"
        now = datetime.now().isoformat()
        
        message = SupportMessage(
            id=message_id,
            ticket_id=ticket_id,
            sender_type=sender_type,
            sender_email=sender_email,
            content=content,
            created_at=now,
            attachments=attachments
        )
        
        with self._get_connection() as conn:
            try:
                # Ajouter le message
                attachments_json = json.dumps(attachments) if attachments else None
                
                conn.execute('''
                    INSERT INTO support_messages 
                    (id, ticket_id, sender_type, sender_email, content, created_at, attachments)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    message.id, message.ticket_id, message.sender_type,
                    message.sender_email, message.content, message.created_at,
                    attachments_json
                ))
                
                # Mettre à jour la date de modification du ticket
                conn.execute('''
                    UPDATE support_tickets 
                    SET updated_at = ? 
                    WHERE id = ?
                ''', (now, ticket_id))
                
                # Envoyer notification par email
                if sender_type == 'user':
                    self._notify_support_new_message(ticket, message)
                elif sender_type == 'support':
                    self._notify_user_new_message(ticket, message)
                
                return True, message
                
            except sqlite3.Error as e:
                print(f"❌ Erreur ajout message: {e}")
                return False, None
    
    def update_ticket_status(self, ticket_id: str, status: TicketStatus, 
                           assigned_to: Optional[str] = None, resolution: Optional[str] = None) -> bool:
        """Mettre à jour le statut d'un ticket"""
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            try:
                # Mettre à jour le ticket
                update_fields = ['status = ?', 'updated_at = ?']
                params = [status.value, now]
                
                if assigned_to:
                    update_fields.append('assigned_to = ?')
                    params.append(assigned_to)
                
                if resolution:
                    update_fields.append('resolution = ?')
                    params.append(resolution)
                
                params.append(ticket_id)
                
                query = f'''
                    UPDATE support_tickets 
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                '''
                
                conn.execute(query, params)
                
                # Ajouter un message système
                status_message = f"Ticket mis à jour: {status.value}"
                if resolution:
                    status_message += f"\nRésolution: {resolution}"
                
                self.add_message(
                    ticket_id=ticket_id,
                    sender_type='system',
                    sender_email='system@harmonica.ai',
                    content=status_message
                )
                
                # Notifier l'utilisateur si le ticket est résolu
                if status == TicketStatus.RESOLVED:
                    ticket = self.get_ticket(ticket_id)
                    if ticket:
                        self._send_ticket_resolved_email(ticket, resolution)
                
                return True
                
            except sqlite3.Error as e:
                print(f"❌ Erreur mise à jour ticket: {e}")
                return False
    
    def get_ticket(self, ticket_id: str) -> Optional[SupportTicket]:
        """Obtenir un ticket par ID"""
        with self._get_connection() as conn:
            cursor = conn.execute('SELECT * FROM support_tickets WHERE id = ?', (ticket_id,))
            row = cursor.fetchone()
            
            if row:
                return SupportTicket(**dict(row))
        
        return None
    
    def get_user_tickets(self, user_id: str, limit: int = 50, offset: int = 0) -> List[SupportTicket]:
        """Obtenir les tickets d'un utilisateur"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM support_tickets 
                WHERE user_id = ? 
                ORDER BY updated_at DESC 
                LIMIT ? OFFSET ?
            ''', (user_id, limit, offset))
            
            return [SupportTicket(**dict(row)) for row in cursor.fetchall()]
    
    def get_ticket_messages(self, ticket_id: str) -> List[SupportMessage]:
        """Obtenir les messages d'un ticket"""
        with self._get_connection() as conn:
            cursor = conn.execute('''
                SELECT * FROM support_messages 
                WHERE ticket_id = ? 
                ORDER BY created_at ASC
            ''', (ticket_id,))
            
            rows = cursor.fetchall()
            messages = []
            
            for row in rows:
                data = dict(row)
                if data.get('attachments'):
                    data['attachments'] = json.loads(data['attachments'])
                messages.append(SupportMessage(**data))
            
            return messages
    
    def search_knowledge_base(self, query: str, category: Optional[str] = None, 
                             limit: int = 10) -> List[KnowledgeBaseArticle]:
        """Rechercher dans la base de connaissances"""
        with self._get_connection() as conn:
            search_terms = query.lower().split()
            
            # Construction de la requête
            where_clauses = []
            params = []
            
            for term in search_terms:
                where_clauses.append('(title LIKE ? OR content LIKE ? OR tags LIKE ?)')
                params.extend([f'%{term}%', f'%{term}%', f'%{term}%'])
            
            if category:
                where_clauses.append('category = ?')
                params.append(category)
            
            where_sql = ' AND '.join(where_clauses) if where_clauses else '1=1'
            
            cursor = conn.execute(f'''
                SELECT * FROM knowledge_base 
                WHERE {where_sql}
                ORDER BY views DESC, helpful_count DESC
                LIMIT ?
            ''', params + [limit])
            
            rows = cursor.fetchall()
            articles = []
            
            for row in rows:
                data = dict(row)
                data['tags'] = json.loads(data['tags']) if data.get('tags') else []
                articles.append(KnowledgeBaseArticle(**data))
            
            return articles
    
    def create_knowledge_base_article(self, title: str, content: str, 
                                    category: str, tags: List[str]) -> Tuple[bool, Optional[KnowledgeBaseArticle]]:
        """Créer un article dans la base de connaissances"""
        article_id = f"KB-{secrets.token_hex(6).upper()}"
        now = datetime.now().isoformat()
        
        article = KnowledgeBaseArticle(
            id=article_id,
            title=title,
            content=content,
            category=category,
            tags=tags,
            created_at=now,
            updated_at=now
        )
        
        with self._get_connection() as conn:
            try:
                tags_json = json.dumps(tags)
                
                conn.execute('''
                    INSERT INTO knowledge_base 
                    (id, title, content, category, tags, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article.id, article.title, article.content,
                    article.category, tags_json, article.created_at,
                    article.updated_at
                ))
                
                return True, article
                
            except sqlite3.Error as e:
                print(f"❌ Erreur création article KB: {e}")
                return False, None
    
    def get_support_stats(self, days: int = 30) -> Dict:
        """Obtenir les statistiques de support"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._get_connection() as conn:
            # Tickets ouverts
            cursor = conn.execute('''
                SELECT COUNT(*) as open_tickets 
                FROM support_tickets 
                WHERE status IN (?, ?) AND created_at >= ?
            ''', (TicketStatus.OPEN.value, TicketStatus.IN_PROGRESS.value, start_date))
            open_tickets = cursor.fetchone()['open_tickets']
            
            # Tickets résolus
            cursor = conn.execute('''
                SELECT COUNT(*) as resolved_tickets 
                FROM support_tickets 
                WHERE status = ? AND created_at >= ?
            ''', (TicketStatus.RESOLVED.value, start_date))
            resolved_tickets = cursor.fetchone()['resolved_tickets']
            
            # Temps moyen de résolution
            cursor = conn.execute('''
                SELECT AVG(
                    (julianday(updated_at) - julianday(created_at)) * 86400
                ) as avg_resolution_seconds
                FROM support_tickets 
                WHERE status = ? AND created_at >= ?
            ''', (TicketStatus.RESOLVED.value, start_date))
            avg_resolution = cursor.fetchone()['avg_resolution_seconds'] or 0
            
            # Répartition par catégorie
            cursor = conn.execute('''
                SELECT category, COUNT(*) as count 
                FROM support_tickets 
                WHERE created_at >= ?
                GROUP BY category
            ''', (start_date,))
            category_distribution = {row['category']: row['count'] for row in cursor.fetchall()}
            
            # Répartition par priorité
            cursor = conn.execute('''
                SELECT priority, COUNT(*) as count 
                FROM support_tickets 
                WHERE created_at >= ?
                GROUP BY priority
            ''', (start_date,))
            priority_distribution = {row['priority']: row['count'] for row in cursor.fetchall()}
            
            return {
                'period_days': days,
                'open_tickets': open_tickets,
                'resolved_tickets': resolved_tickets,
                'avg_resolution_hours': round(avg_resolution / 3600, 1),
                'category_distribution': category_distribution,
                'priority_distribution': priority_distribution,
                'timestamp': datetime.now().isoformat()
            }
    
    def _send_ticket_created_email(self, ticket: SupportTicket):
        """Envoyer un email de confirmation de création de ticket"""
        subject = f"Ticket #{ticket.id} créé: {ticket.subject}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #10b981;">Harmonic AI Support</h1>
                </div>
                
                <h2>Votre ticket a été créé</h2>
                <p>Bonjour,</p>
                <p>Votre ticket de support a été créé avec succès. Voici les détails :</p>
                
                <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Ticket ID:</strong> {ticket.id}</p>
                    <p><strong>Sujet:</strong> {ticket.subject}</p>
                    <p><strong>Catégorie:</strong> {self.categories.get(ticket.category, ticket.category)}</p>
                    <p><strong>Priorité:</strong> {ticket.priority.value}</p>
                    <p><strong>Date de création:</strong> {ticket.created_at[:19]}</p>
                </div>
                
                <h3>Description :</h3>
                <div style="background: #f1f5f9; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <p>{ticket.description}</p>
                </div>
                
                <p>Notre équipe support examinera votre ticket et vous répondra dans les plus brefs délais.</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p style="font-size: 14px; color: #64748b;">
                        Vous pouvez consulter l'état de votre ticket à tout moment depuis votre dashboard Harmonic AI.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self._send_email(ticket.user_email, subject, html_content)
    
    def _send_ticket_resolved_email(self, ticket: SupportTicket, resolution: Optional[str]):
        """Envoyer un email de résolution de ticket"""
        subject = f"Ticket #{ticket.id} résolu: {ticket.subject}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #10b981;">Harmonic AI Support</h1>
                </div>
                
                <h2>Votre ticket a été résolu</h2>
                <p>Bonjour,</p>
                <p>Votre ticket de support a été marqué comme résolu. Voici les détails :</p>
                
                <div style="background: #f8fafc; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Ticket ID:</strong> {ticket.id}</p>
                    <p><strong>Sujet:</strong> {ticket.subject}</p>
                    <p><strong>Statut:</strong> Résolu</p>
                    <p><strong>Date de résolution:</strong> {datetime.now().isoformat()[:19]}</p>
                </div>
                
                <h3>Résolution :</h3>
                <div style="background: #f1f5f9; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <p>{resolution or 'Le problème a été résolu par notre équipe support.'}</p>
                </div>
                
                <p>Si vous avez d'autres questions ou si le problème persiste, n'hésitez pas à répondre à cet email pour rouvrir le ticket.</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p style="font-size: 14px; color: #64748b;">
                        Merci d'utiliser Harmonic AI !
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self._send_email(ticket.user_email, subject, html_content)
    
    def _notify_support_team(self, ticket: SupportTicket):
        """Notifier l'équipe support d'un nouveau ticket"""
        subject = f"🚨 Nouveau ticket #{ticket.id}: {ticket.subject}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #ef4444;">Nouveau Ticket Support</h1>
                </div>
                
                <h2>Ticket #{ticket.id}</h2>
                
                <div style="background: #fef2f2; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Utilisateur:</strong> {ticket.user_email}</p>
                    <p><strong>Sujet:</strong> {ticket.subject}</p>
                    <p><strong>Catégorie:</strong> {self.categories.get(ticket.category, ticket.category)}</p>
                    <p><strong>Priorité:</strong> {ticket.priority.value}</p>
                    <p><strong>Date de création:</strong> {ticket.created_at[:19]}</p>
                </div>
                
                <h3>Description :</h3>
                <div style="background: #f1f5f9; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <p>{ticket.description}</p>
                </div>
                
                <div style="margin-top: 30px; text-align: center;">
                    <a href="http://localhost:5000/admin/ticket/{ticket.id}" 
                       style="background: #ef4444; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 8px; font-weight: bold;">
                       Voir le ticket
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        
        self._send_email(self.email_config['support_team_email'], subject, html_content)
    
    def _notify_support_new_message(self, ticket: SupportTicket, message: SupportMessage):
        """Notifier l'équipe support d'un nouveau message utilisateur"""
        subject = f"💬 Nouveau message sur ticket #{ticket.id}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #3b82f6;">Nouveau Message</h1>
                </div>
                
                <h2>Ticket #{ticket.id}: {ticket.subject}</h2>
                
                <div style="background: #eff6ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>De:</strong> {message.sender_email}</p>
                    <p><strong>Date:</strong> {message.created_at[:19]}</p>
                </div>
                
                <h3>Message :</h3>
                <div style="background: #f1f5f9; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <p>{message.content}</p>
                </div>
                
                <div style="margin-top: 30px; text-align: center;">
                    <a href="http://localhost:5000/admin/ticket/{ticket.id}" 
                       style="background: #3b82f6; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 8px; font-weight: bold;">
                       Répondre
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        
        self._send_email(self.email_config['support_team_email'], subject, html_content)
    
    def _notify_user_new_message(self, ticket: SupportTicket, message: SupportMessage):
        """Notifier l'utilisateur d'un nouveau message support"""
        subject = f"💬 Réponse sur votre ticket #{ticket.id}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1 style="color: #10b981;">Harmonic AI Support</h1>
                </div>
                
                <h2>Réponse à votre ticket #{ticket.id}</h2>
                
                <div style="background: #f0fdf4; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>De:</strong> Équipe Support Harmonic AI</p>
                    <p><strong>Date:</strong> {message.created_at[:19]}</p>
                </div>
                
                <h3>Message :</h3>
                <div style="background: #f1f5f9; padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <p>{message.content}</p>
                </div>
                
                <p>Vous pouvez répondre à cet email pour continuer la conversation.</p>
                
                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p style="font-size: 14px; color: #64748b;">
                        Merci d'utiliser Harmonic AI !
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        self._send_email(ticket.user_email, subject, html_content)
    
    def _send_email(self, to_email: str, subject: str, html_content: str):
        """Envoyer un email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_config['from_email']
            msg['To'] = to_email
            
            # Partie HTML
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Connexion SMTP
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['smtp_username'], self.email_config['smtp_password'])
            
            # Envoi
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email envoyé à {to_email}")
            
        except Exception as e:
            print(f"❌ Erreur envoi email à {to_email}: {e}")


# Interface web pour le support
from flask import Flask, request, jsonify, render_template_string
import functools

app = Flask(__name__)
support_system = HarmonicAISupportSystem()

# Templates HTML
SUPPORT_PORTAL_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Harmonic AI Support</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #f8fafc; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid #334155; }
        .logo { display: flex; align-items: center; gap: 12px; font-size: 24px; font-weight: bold; }
        .logo-icon { color: #10b981; font-size: 28px; }
        .btn { background: #10b981; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 500; text-decoration: none; display: inline-block; }
        .btn:hover { background: #0ea271; }
        .btn-outline { background: transparent; border: 2px solid #10b981; color: #10b981; }
        .btn-outline:hover { background: #10b981; color: white; }
        .tabs { display: flex; gap: 10px; margin-bottom: 30px; border-bottom: 1px solid #334155; }
        .tab { padding: 12px 24px; cursor: pointer; border-bottom: 3px solid transparent; }
        .tab.active { border-bottom-color: #10b981; color: #10b981; }
        .ticket-list { background: #1e293b; border-radius: 12px; overflow: hidden; }
        .ticket-item { padding: 20px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }
        .ticket-item:hover { background: #1e293b; }
        .ticket-id { font-weight: bold; color: #10b981; }
        .ticket-subject { font-size: 18px; margin: 5px 0; }
        .ticket-meta { color: #94a3b8; font-size: 14px; }
        .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .status-open { background: #3b82f6; color: white; }
        .status-in-progress { background: #f59e0b; color: white; }
        .status-resolved { background: #10b981; color: white; }
        .priority-badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        .priority-low { background: #6b7280; color: white; }
        .priority-medium { background: #3b82f6; color: white; }
        .priority-high { background: #ef4444; color: white; }
        .priority-critical { background: #7c2d12; color: white; }
        .new-ticket-form { background: #1e293b; padding: 30px; border-radius: 12px; margin-top: 40px; }
        .form-group { margin-bottom: 20px; }
        .form-label { display: block; margin-bottom: 8px; font-weight: 500; }
        .form-input, .form-select, .form-textarea { width: 100%; padding: 12px; background: #0f172a; border: 1px solid #334155; border-radius: 8px; color: #f8fafc; font-size: 16px; }
        .form-textarea { min-height: 150px; resize: vertical; }
        .knowledge-base { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 40px; }
        .kb-article { background: #1e293b; padding: 20px; border-radius: 12px; border: 1px solid #334155; }
        .kb-title { font-size: 18px; font-weight: 600; margin-bottom: 10px; color: #10b981; }
        .kb-category { display: inline-block; background: #334155; color: #94a3b8; padding: 4px 12px; border-radius: 20px; font-size: 12px; margin-bottom: 15px; }
        .kb-content { color: #cbd5e1; line-height: 1.6; }
        .kb-tags { margin-top: 15px; }
        .kb-tag { display: inline-block; background: #1e40af; color: #93c5fd; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-right: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">
                <span class="logo-icon">φ</span>
                <span>Harmonic AI Support</span>
            </div>
            <div>
                <a href="/" class="btn">Dashboard</a>
                <a href="/support/new" class="btn btn-outline">Nouveau ticket</a>
            </div>
        </div>
        
        <div class="tabs">
            <div class="tab active" onclick="showTab('tickets