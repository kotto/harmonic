#!/usr/bin/env python3
"""
HCV PRO - Harmonic Marketplace
================================
Marketplace d'applications pour le Téléphone Harmonique

Plateforme complète :
- Apps tierces utilisant le SDK
- Validation et certification
- Distribution automatique
- Monétisation intégrée
- Reviews et ratings
- Analytics pour développeurs

Écosystème complet :
- SDK pour développeurs
- Marketplace pour distribution
- Analytics pour monitoring
- Support technique
- Documentation complète
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from harmonic_sdk import HarmonicApp, SDKVersion, get_harmonic_sdk

class AppCategory(Enum):
    """Catégories d'applications Harmonic"""
    PRODUCTIVITY = "productivity"
    ENTERTAINMENT = "entertainment"
    EDUCATION = "education"
    HEALTH = "health"
    FINANCE = "finance"
    SOCIAL = "social"
    CREATIVITY = "creativity"
    UTILITIES = "utilities"
    BUSINESS = "business"
    LIFESTYLE = "lifestyle"

class AppStatus(Enum):
    """Statuts des applications"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class MonetizationType(Enum):
    """Types de monétisation"""
    FREE = "free"
    PREMIUM = "premium"
    FREEMIUM = "freemium"
    SUBSCRIPTION = "subscription"
    ONE_TIME = "one_time"

@dataclass
class MarketplaceApp:
    """Application dans le Marketplace"""
    app_id: str
    name: str
    version: str
    developer: str
    description: str
    category: AppCategory
    status: AppStatus
    monetization: MonetizationType
    price: float
    download_url: str
    icon_url: str
    screenshots: List[str]
    features: List[str]
    permissions: List[str]
    sdk_version: SDKVersion
    file_size_mb: float
    created_at: float
    updated_at: float
    downloads: int
    rating: float
    reviews_count: int
    verified: bool

@dataclass
class AppReview:
    """Review d'application"""
    review_id: str
    app_id: str
    user_id: str
    rating: int  # 1-5
    title: str
    content: str
    created_at: float
    helpful_count: int
    verified_purchase: bool

@dataclass
class DeveloperAccount:
    """Compte développeur"""
    developer_id: str
    name: str
    email: str
    company: Optional[str]
    website: Optional[str]
    verified: bool
    created_at: float
    total_apps: int
    total_downloads: int
    total_revenue: float
    api_key: str

class HarmonicMarketplace:
    """
    Marketplace du Téléphone Harmonique
    
    Fonctionnalités :
    - Publication d'applications
    - Validation et certification
    - Distribution automatique
    - Monétisation intégrée
    - Reviews et ratings
    - Analytics pour développeurs
    - Support technique
    
    Avantages pour développeurs :
    - Accès à millions d'utilisateurs
    - SDK Harmonique intégré
    - Analytics détaillées
    - Monétisation flexible
    - Support prioritaire
    - Certification de qualité
    """
    
    def __init__(self):
        self.apps: Dict[str, MarketplaceApp] = {}
        self.reviews: Dict[str, List[AppReview]] = {}
        self.developers: Dict[str, DeveloperAccount] = {}
        self.downloads: Dict[str, List[Dict[str, Any]]] = {}
        
        # Statistiques du marketplace
        self.stats = {
            'total_apps': 0,
            'published_apps': 0,
            'total_downloads': 0,
            'total_revenue': 0.0,
            'active_developers': 0,
            'average_rating': 0.0
        }
        
        # Categories disponibles
        self.categories = list(AppCategory)
        
        print("🏪 Harmonic Marketplace initialisé")
        print(f"📱 Categories : {len(self.categories)}")
        print(f"👨‍💻 Développeurs : {len(self.developers)}")
        print(f"📦 Applications : {len(self.apps)}")
    
    def register_developer(self, name: str, email: str, 
                          company: str = None, 
                          website: str = None) -> str:
        """
        Enregistre un nouveau développeur
        
        Args:
            name: Nom du développeur
            email: Email du développeur
            company: Entreprise (optionnel)
            website: Site web (optionnel)
            
        Returns:
            ID du développeur
        """
        
        developer_id = str(uuid.uuid4())[:12]
        api_key = hashlib.sha256(f"{developer_id}_{time.time()}".encode()).hexdigest()[:32]
        
        developer = DeveloperAccount(
            developer_id=developer_id,
            name=name,
            email=email,
            company=company,
            website=website,
            verified=False,
            created_at=time.time(),
            total_apps=0,
            total_downloads=0,
            total_revenue=0.0,
            api_key=api_key
        )
        
        self.developers[developer_id] = developer
        self.stats['active_developers'] = len(self.developers)
        
        print(f"👨‍💻 Développeur enregistré : {name}")
        print(f"   📧 Email : {email}")
        print(f"   🔑 API Key : {api_key}")
        print(f"   🆔 Developer ID : {developer_id}")
        
        return developer_id
    
    def submit_app(self, developer_id: str, 
                   name: str, 
                   version: str,
                   description: str,
                   category: AppCategory,
                   monetization: MonetizationType,
                   price: float,
                   features: List[str],
                   permissions: List[str],
                   file_path: str,
                   icon_url: str = None,
                   screenshots: List[str] = None) -> str:
        """
        Soumet une nouvelle application
        
        Args:
            developer_id: ID du développeur
            name: Nom de l'application
            version: Version de l'application
            description: Description
            category: Catégorie
            monetization: Type de monétisation
            price: Prix
            features: Liste des fonctionnalités
            permissions: Permissions requises
            file_path: Chemin du fichier
            icon_url: URL de l'icône
            screenshots: URLs des screenshots
            
        Returns:
            ID de l'application
        """
        
        if developer_id not in self.developers:
            raise ValueError("Développeur non enregistré")
        
        app_id = str(uuid.uuid4())[:12]
        
        # Simuler la taille du fichier
        file_size_mb = len(file_path) * 0.001  # Simulation
        
        app = MarketplaceApp(
            app_id=app_id,
            name=name,
            version=version,
            developer=self.developers[developer_id].name,
            description=description,
            category=category,
            status=AppStatus.PENDING_REVIEW,
            monetization=monetization,
            price=price,
            download_url=file_path,
            icon_url=icon_url or f"https://icons.harmonic.com/{app_id}.png",
            screenshots=screenshots or [],
            features=features,
            permissions=permissions,
            sdk_version=SDKVersion.V1_0,
            file_size_mb=file_size_mb,
            created_at=time.time(),
            updated_at=time.time(),
            downloads=0,
            rating=0.0,
            reviews_count=0,
            verified=False
        )
        
        self.apps[app_id] = app
        self.stats['total_apps'] = len(self.apps)
        
        # Mettre à jour les stats du développeur
        self.developers[developer_id].total_apps += 1
        
        print(f"📦 Application soumise : {name}")
        print(f"   🆔 App ID : {app_id}")
        print(f"   📂 Catégorie : {category.value}")
        print(f"   💰 Prix : ${price}")
        print(f"   📊 Statut : {app.status.value}")
        
        return app_id
    
    def review_app(self, app_id: str, approved: bool, 
                   review_notes: str = "") -> bool:
        """
        Approuve ou rejette une application
        
        Args:
            app_id: ID de l'application
            approved: True si approuvé
            review_notes: Notes de review
            
        Returns:
            True si succès
        """
        
        if app_id not in self.apps:
            return False
        
        app = self.apps[app_id]
        
        if approved:
            app.status = AppStatus.APPROVED
            app.verified = True
            print(f"✅ Application approuvée : {app.name}")
        else:
            app.status = AppStatus.REJECTED
            print(f"❌ Application rejetée : {app.name}")
        
        app.updated_at = time.time()
        
        return True
    
    def publish_app(self, app_id: str) -> bool:
        """
        Publie une application approuvée
        
        Args:
            app_id: ID de l'application
            
        Returns:
            True si succès
        """
        
        if app_id not in self.apps:
            return False
        
        app = self.apps[app_id]
        
        if app.status != AppStatus.APPROVED:
            return False
        
        app.status = AppStatus.PUBLISHED
        app.updated_at = time.time()
        
        self.stats['published_apps'] = len([a for a in self.apps.values() if a.status == AppStatus.PUBLISHED])
        
        print(f"🚀 Application publiée : {app.name}")
        print(f"   📱 Disponible dans le Marketplace")
        
        return True
    
    def search_apps(self, query: str = "", 
                   category: AppCategory = None,
                   min_rating: float = 0.0,
                   max_price: float = None,
                   monetization: MonetizationType = None) -> List[MarketplaceApp]:
        """
        Recherche des applications
        
        Args:
            query: Recherche textuelle
            category: Catégorie filtrée
            min_rating: Rating minimum
            max_price: Prix maximum
            monetization: Type de monétisation
            
        Returns:
            Liste des applications correspondantes
        """
        
        results = []
        
        for app in self.apps.values():
            # Filtrer par statut publié uniquement
            if app.status != AppStatus.PUBLISHED:
                continue
            
            # Filtrer par recherche textuelle
            if query and query.lower() not in app.name.lower() and query.lower() not in app.description.lower():
                continue
            
            # Filtrer par catégorie
            if category and app.category != category:
                continue
            
            # Filtrer par rating
            if app.rating < min_rating:
                continue
            
            # Filtrer par prix
            if max_price is not None and app.price > max_price:
                continue
            
            # Filtrer par monétisation
            if monetization and app.monetization != monetization:
                continue
            
            results.append(app)
        
        # Trier par rating (décroissant) puis par downloads
        results.sort(key=lambda x: (x.rating, x.downloads), reverse=True)
        
        return results
    
    def get_app_details(self, app_id: str) -> Optional[Dict[str, Any]]:
        """
        Retourne les détails complets d'une application
        
        Args:
            app_id: ID de l'application
            
        Returns:
            Détails de l'application ou None
        """
        
        if app_id not in self.apps:
            return None
        
        app = self.apps[app_id]
        
        # Récupérer les reviews
        app_reviews = self.reviews.get(app_id, [])
        
        details = {
            'app': asdict(app),
            'reviews': [asdict(review) for review in app_reviews],
            'similar_apps': self._get_similar_apps(app_id),
            'developer_info': {
                'name': app.developer,
                'total_apps': len([a for a in self.apps.values() if a.developer == app.developer]),
                'verified': app.verified
            }
        }
        
        return details
    
    def _get_similar_apps(self, app_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retourne des applications similaires"""
        
        if app_id not in self.apps:
            return []
        
        current_app = self.apps[app_id]
        similar = []
        
        for app in self.apps.values():
            if app.app_id == app_id or app.status != AppStatus.PUBLISHED:
                continue
            
            # Calculer la similarité
            similarity = 0
            
            # Même catégorie
            if app.category == current_app.category:
                similarity += 0.3
            
            # Même développeur
            if app.developer == current_app.developer:
                similarity += 0.2
            
            # Features similaires
            common_features = set(app.features) & set(current_app.features)
            if common_features:
                similarity += 0.1 * len(common_features)
            
            # Prix similaire
            if abs(app.price - current_app.price) < 5.0:
                similarity += 0.1
            
            if similarity > 0:
                similar.append({
                    'app_id': app.app_id,
                    'name': app.name,
                    'category': app.category.value,
                    'rating': app.rating,
                    'price': app.price,
                    'similarity': similarity
                })
        
        # Trier par similarité et limiter
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        return similar[:limit]
    
    def download_app(self, app_id: str, user_id: str) -> Dict[str, Any]:
        """
        Simule le téléchargement d'une application
        
        Args:
            app_id: ID de l'application
            user_id: ID de l'utilisateur
            
        Returns:
            Résultat du téléchargement
        """
        
        if app_id not in self.apps:
            return {'success': False, 'error': 'Application non trouvée'}
        
        app = self.apps[app_id]
        
        if app.status != AppStatus.PUBLISHED:
            return {'success': False, 'error': 'Application non publiée'}
        
        # Enregistrer le téléchargement
        download_record = {
            'user_id': user_id,
            'app_id': app_id,
            'timestamp': time.time(),
            'price': app.price,
            'monetization': app.monetization.value
        }
        
        if app_id not in self.downloads:
            self.downloads[app_id] = []
        
        self.downloads[app_id].append(download_record)
        
        # Mettre à jour les stats
        app.downloads += 1
        self.stats['total_downloads'] += 1
        
        # Mettre à jour les revenus du développeur
        developer_id = self._get_developer_id_by_app(app_id)
        if developer_id:
            self.developers[developer_id].total_downloads += 1
            self.developers[developer_id].total_revenue += app.price
            self.stats['total_revenue'] += app.price
        
        print(f"📱 Application téléchargée : {app.name}")
        print(f"   👤 Par : {user_id}")
        print(f"   💰 Prix : ${app.price}")
        print(f"   📊 Total téléchargements : {app.downloads}")
        
        return {
            'success': True,
            'app_id': app_id,
            'download_url': app.download_url,
            'file_size_mb': app.file_size_mb,
            'version': app.version
        }
    
    def _get_developer_id_by_app(self, app_id: str) -> Optional[str]:
        """Retourne l'ID du développeur pour une application"""
        
        if app_id not in self.apps:
            return None
        
        app_name = self.apps[app_id].developer
        
        for dev_id, developer in self.developers.items():
            if developer.name == app_name:
                return dev_id
        
        return None
    
    def add_review(self, app_id: str, user_id: str, 
                   rating: int, title: str, content: str) -> str:
        """
        Ajoute une review pour une application
        
        Args:
            app_id: ID de l'application
            user_id: ID de l'utilisateur
            rating: Rating (1-5)
            title: Titre de la review
            content: Contenu de la review
            
        Returns:
            ID de la review
        """
        
        if app_id not in self.apps:
            raise ValueError("Application non trouvée")
        
        if rating < 1 or rating > 5:
            raise ValueError("Rating doit être entre 1 et 5")
        
        review_id = str(uuid.uuid4())[:12]
        
        review = AppReview(
            review_id=review_id,
            app_id=app_id,
            user_id=user_id,
            rating=rating,
            title=title,
            content=content,
            created_at=time.time(),
            helpful_count=0,
            verified_purchase=True
        )
        
        if app_id not in self.reviews:
            self.reviews[app_id] = []
        
        self.reviews[app_id].append(review)
        
        # Mettre à jour le rating de l'application
        self._update_app_rating(app_id)
        
        print(f"⭐ Review ajoutée pour : {self.apps[app_id].name}")
        print(f"   🌟 Rating : {rating}/5")
        print(f"   📝 Titre : {title}")
        
        return review_id
    
    def _update_app_rating(self, app_id: str):
        """Met à jour le rating moyen d'une application"""
        
        if app_id not in self.reviews:
            return
        
        reviews = self.reviews[app_id]
        if not reviews:
            return
        
        total_rating = sum(review.rating for review in reviews)
        avg_rating = total_rating / len(reviews)
        
        self.apps[app_id].rating = avg_rating
        self.apps[app_id].reviews_count = len(reviews)
        
        # Mettre à jour le rating moyen du marketplace
        all_ratings = [app.rating for app in self.apps.values() if app.rating > 0]
        if all_ratings:
            self.stats['average_rating'] = sum(all_ratings) / len(all_ratings)
    
    def get_trending_apps(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retourne les applications tendance"""
        
        # Calculer le score de tendance
        trending = []
        
        for app in self.apps.values():
            if app.status != AppStatus.PUBLISHED:
                continue
            
            # Score basé sur les téléchargements récents (simulation)
            recent_downloads = len([d for d in self.downloads.get(app.app_id, []) 
                                  if time.time() - d['timestamp'] < 7 * 24 * 3600])  # 7 jours
            
            trend_score = recent_downloads * 0.5 + app.rating * 0.3 + app.downloads * 0.2
            
            trending.append({
                'app_id': app.app_id,
                'name': app.name,
                'category': app.category.value,
                'rating': app.rating,
                'downloads': app.downloads,
                'recent_downloads': recent_downloads,
                'trend_score': trend_score
            })
        
        # Trier par score de tendance
        trending.sort(key=lambda x: x['trend_score'], reverse=True)
        
        return trending[:limit]
    
    def get_developer_analytics(self, developer_id: str) -> Dict[str, Any]:
        """Retourne les analytics pour un développeur"""
        
        if developer_id not in self.developers:
            return {}
        
        developer = self.developers[developer_id]
        
        # Applications du développeur
        dev_apps = [app for app in self.apps.values() if app.developer == developer.name]
        
        # Téléchargements par application
        downloads_by_app = {}
        revenue_by_app = {}
        
        for app in dev_apps:
            downloads_by_app[app.app_id] = app.downloads
            revenue_by_app[app.app_id] = app.downloads * app.price
        
        # Reviews par application
        reviews_by_app = {}
        for app in dev_apps:
            app_reviews = self.reviews.get(app.app_id, [])
            if app_reviews:
                avg_rating = sum(review.rating for review in app_reviews) / len(app_reviews)
                reviews_by_app[app.app_id] = {
                    'count': len(app_reviews),
                    'average_rating': avg_rating
                }
        
        analytics = {
            'developer_info': asdict(developer),
            'apps_summary': {
                'total_apps': len(dev_apps),
                'published_apps': len([a for a in dev_apps if a.status == AppStatus.PUBLISHED]),
                'total_downloads': developer.total_downloads,
                'total_revenue': developer.total_revenue
            },
            'apps_performance': {
                'downloads_by_app': downloads_by_app,
                'revenue_by_app': revenue_by_app,
                'reviews_by_app': reviews_by_app
            },
            'marketplace_position': {
                'rank_by_downloads': self._get_developer_rank(developer_id, 'downloads'),
                'rank_by_revenue': self._get_developer_rank(developer_id, 'revenue'),
                'rank_by_apps': self._get_developer_rank(developer_id, 'apps')
            }
        }
        
        return analytics
    
    def _get_developer_rank(self, developer_id: str, metric: str) -> int:
        """Calcule le rang d'un développeur selon une métrique"""
        
        if developer_id not in self.developers:
            return 0
        
        developers_by_metric = []
        
        for dev_id, dev in self.developers.items():
            if metric == 'downloads':
                value = dev.total_downloads
            elif metric == 'revenue':
                value = dev.total_revenue
            elif metric == 'apps':
                value = dev.total_apps
            else:
                value = 0
            
            developers_by_metric.append((dev_id, value))
        
        # Trier par métrique (décroissant)
        developers_by_metric.sort(key=lambda x: x[1], reverse=True)
        
        # Trouver le rang
        for rank, (dev_id, _) in enumerate(developers_by_metric, 1):
            if dev_id == developer_id:
                return rank
        
        return 0
    
    def get_marketplace_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques complètes du marketplace"""
        
        # Apps par catégorie
        apps_by_category = {}
        for category in AppCategory:
            count = len([app for app in self.apps.values() 
                        if app.category == category and app.status == AppStatus.PUBLISHED])
            apps_by_category[category.value] = count
        
        # Apps par monétisation
        apps_by_monetization = {}
        for monetization in MonetizationType:
            count = len([app for app in self.apps.values() 
                        if app.monetization == monetization and app.status == AppStatus.PUBLISHED])
            apps_by_monetization[monetization.value] = count
        
        # Revenue par mois (simulation)
        monthly_revenue = []
        for i in range(12):
            month_revenue = self.stats['total_revenue'] * (i + 1) / 12  # Simulation
            monthly_revenue.append(month_revenue)
        
        stats = {
            'overview': self.stats,
            'apps_by_category': apps_by_category,
            'apps_by_monetization': apps_by_monetization,
            'top_categories': sorted(apps_by_category.items(), key=lambda x: x[1], reverse=True)[:5],
            'monthly_revenue': monthly_revenue,
            'trending_apps': self.get_trending_apps(5),
            'top_developers': self._get_top_developers(5)
        }
        
        return stats
    
    def _get_top_developers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Retourne les meilleurs développeurs"""
        
        developers = []
        
        for dev_id, developer in self.developers.items():
            developers.append({
                'developer_id': dev_id,
                'name': developer.name,
                'total_apps': developer.total_apps,
                'total_downloads': developer.total_downloads,
                'total_revenue': developer.total_revenue,
                'verified': developer.verified
            })
        
        # Trier par revenue (décroissant)
        developers.sort(key=lambda x: x['total_revenue'], reverse=True)
        
        return developers[:limit]

# Singleton global
_marketplace_instance = None

def get_harmonic_marketplace() -> HarmonicMarketplace:
    """Récupère l'instance du Marketplace"""
    global _marketplace_instance
    if _marketplace_instance is None:
        _marketplace_instance = HarmonicMarketplace()
    return _marketplace_instance

if __name__ == "__main__":
    print("🏪 HCV PRO - Harmonic Marketplace")
    print("📱 Marketplace d'applications pour le Téléphone Harmonique")
    print("👨‍💻 Platforme pour développeurs")
    print("💰 Monétisation intégrée")
    print()
    
    # Initialiser le marketplace
    marketplace = get_harmonic_marketplace()
    
    # Enregistrer des développeurs
    print("👨‍💻 Enregistrement des développeurs...")
    
    dev1_id = marketplace.register_developer(
        "Harmonic Studios",
        "dev@harmonicstudios.com",
        company="Harmonic Studios Inc.",
        website="https://harmonicstudios.com"
    )
    
    dev2_id = marketplace.register_developer(
        "Creative Apps",
        "contact@creativeapps.com",
        company="Creative Apps Ltd"
    )
    
    # Soumettre des applications
    print("\n📦 Soumission des applications...")
    
    app1_id = marketplace.submit_app(
        developer_id=dev1_id,
        name="Harmonic Notes",
        version="1.0.0",
        description="Application de notes avec IA personnelle intégrée",
        category=AppCategory.PRODUCTIVITY,
        monetization=MonetizationType.FREEMIUM,
        price=0.0,
        features=["IA Personnelle", "Compression Harmonique", "Synchronisation", "Voice Notes"],
        permissions=["storage", "microphone", "network"],
        file_path="/apps/harmonic_notes.apk",
        icon_url="https://icons.harmonic.com/harmonic_notes.png"
    )
    
    app2_id = marketplace.submit_app(
        developer_id=dev2_id,
        name="Harmonic Camera",
        version="2.1.0",
        description="Appareil photo avec compression 300x plus rapide",
        category=AppCategory.CREATIVITY,
        monetization=MonetizationType.PREMIUM,
        price=4.99,
        features=["Compression Harmonique", "Filtres IA", "Édition avancée", "Cloud Sync"],
        permissions=["camera", "storage", "network"],
        file_path="/apps/harmonic_camera.apk"
    )
    
    # Approuver et publier les applications
    print("\n✅ Validation et publication...")
    
    marketplace.review_app(app1_id, True, "Application de qualité, SDK bien intégré")
    marketplace.publish_app(app1_id)
    
    marketplace.review_app(app2_id, True, "Performance exceptionnelle, interface harmonique")
    marketplace.publish_app(app2_id)
    
    # Rechercher des applications
    print("\n🔍 Recherche d'applications...")
    
    productivity_apps = marketplace.search_apps(category=AppCategory.PRODUCTIVITY)
    print(f"📱 Apps Productivité : {len(productivity_apps)}")
    
    free_apps = marketplace.search_apps(monetization=MonetizationType.FREE)
    print(f"🆓 Apps Gratuites : {len(free_apps)}")
    
    # Simuler des téléchargements
    print("\n📱 Téléchargements simulés...")
    
    marketplace.download_app(app1_id, "user123")
    marketplace.download_app(app1_id, "user456")
    marketplace.download_app(app2_id, "user789")
    
    # Ajouter des reviews
    print("\n⭐ Ajout de reviews...")
    
    marketplace.add_review(app1_id, "user123", 5, "Incroyable !", "Meilleure app de notes jamais utilisée")
    marketplace.add_review(app1_id, "user456", 4, "Très bonne", "Interface fluide, IA très utile")
    marketplace.add_review(app2_id, "user789", 5, "Exceptionnel !", "Compression ultra-rapide, photos parfaites")
    
    # Analytics développeur
    print("\n📊 Analytics développeur...")
    
    dev_analytics = marketplace.get_developer_analytics(dev1_id)
    print(f"👨‍💻 {dev_analytics['developer_info']['name']}:")
    print(f"   📦 Apps : {dev_analytics['apps_summary']['total_apps']}")
    print(f"   📱 Téléchargements : {dev_analytics['apps_summary']['total_downloads']}")
    print(f"   💰 Revenue : ${dev_analytics['apps_summary']['total_revenue']:.2f}")
    
    # Stats marketplace
    print("\n📈 Statistiques Marketplace...")
    
    stats = marketplace.get_marketplace_stats()
    print(f"   📦 Total apps : {stats['overview']['total_apps']}")
    print(f"   🚀 Apps publiées : {stats['overview']['published_apps']}")
    print(f"   📱 Total téléchargements : {stats['overview']['total_downloads']}")
    print(f"   💰 Total revenue : ${stats['overview']['total_revenue']:.2f}")
    print(f"   👨‍💽 Développeurs actifs : {stats['overview']['active_developers']}")
    print(f"   ⭐ Rating moyen : {stats['overview']['average_rating']:.2f}/5")
    
    # Apps tendance
    print("\n🔥 Apps tendance...")
    
    trending = marketplace.get_trending_apps(3)
    for i, app in enumerate(trending, 1):
        print(f"   {i}. {app['name']} - Score: {app['trend_score']:.1f}")
    
    print("\n🏆 Harmonic Marketplace : Écosystème complet opérationnel !")
