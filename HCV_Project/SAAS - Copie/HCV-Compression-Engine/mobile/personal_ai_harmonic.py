#!/usr/bin/env python3
"""
HCV PRO - IA Personnelle Harmonique
===================================
IA Personnelle qui apprend de votre quotidien

Concept Obsidian-like :
- Base de connaissances personnelle
- Connexions automatiques
- Apprentissage continu
- Contexte personnel profond

Basé sur la Physique Harmonique :
- Représentation déterministe
- Connexions harmoniques
- Mémoire personnelle optimisée
"""

import numpy as np
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import hashlib
from collections import defaultdict

@dataclass
class PersonalKnowledge:
    """Élément de connaissance personnelle"""
    id: str
    content: str
    context: str
    timestamp: datetime
    importance: float  # 0.0 - 1.0
    connections: List[str]  # IDs connectés
    tags: List[str]
    embedding: Optional[np.ndarray] = None

@dataclass
class PersonalContext:
    """Contexte personnel de l'utilisateur"""
    current_task: str
    recent_activities: List[str]
    preferences: Dict[str, Any]
    patterns: Dict[str, Any]
    knowledge_graph: Dict[str, List[str]]

class HarmonicPersonalAI:
    """
    IA Personnelle basée sur la Physique Harmonique
    
    Principes :
    - Représentation déterministe des connaissances
    - Connexions harmoniques entre concepts
    - Apprentissage personnel continu
    - Mémoire optimisée par transformée harmonique
    
    Différence vs IA géantes :
    - Local vs Cloud
    - Personnelle vs Générique  
    - Déterministe vs Probabiliste
    - Optimisée vs Lourde
    """
    
    def __init__(self, user_id: str, storage_path: Optional[Path] = None):
        self.user_id = user_id
        self.storage_path = storage_path or Path(f"personal_ai_{user_id}")
        self.storage_path.mkdir(exist_ok=True)
        
        # Base de connaissances personnelle
        self.knowledge_base: Dict[str, PersonalKnowledge] = {}
        
        # Contexte personnel
        self.context = PersonalContext(
            current_task="",
            recent_activities=[],
            preferences={},
            patterns={},
            knowledge_graph=defaultdict(list)
        )
        
        # Métriques personnelles
        self.metrics = {
            'total_knowledge_items': 0,
            'connections_made': 0,
            'learning_rate': 0.0,
            'personalization_score': 0.0,
            'memory_efficiency': 0.0
        }
        
        # Charger les données existantes
        self._load_personal_data()
        
        print(f"🧠 IA Personnelle Harmonique initialisée pour {user_id}")
        print(f"📁 Stockage : {self.storage_path}")
        print(f"📚 Connaissances chargées : {len(self.knowledge_base)}")
    
    def add_knowledge(self, content: str, context: str = "", tags: List[str] = None, importance: float = 0.5) -> str:
        """
        Ajoute une connaissance personnelle
        
        Args:
            content: Contenu de la connaissance
            context: Contexte d'acquisition
            tags: Étiquettes personnelles
            importance: Importance personnelle (0.0-1.0)
            
        Returns:
            ID de la connaissance ajoutée
        """
        
        # Générer un ID unique
        knowledge_id = hashlib.md5(f"{content}_{context}_{time.time()}".encode()).hexdigest()[:12]
        
        # Créer l'objet connaissance
        knowledge = PersonalKnowledge(
            id=knowledge_id,
            content=content,
            context=context,
            timestamp=datetime.now(),
            importance=importance,
            connections=[],
            tags=tags or [],
            embedding=self._create_harmonic_embedding(content)
        )
        
        # Ajouter à la base
        self.knowledge_base[knowledge_id] = knowledge
        
        # Mettre à jour le contexte
        self._update_context_from_knowledge(knowledge)
        
        # Trouver les connexions automatiques
        self._find_harmonic_connections(knowledge_id)
        
        # Sauvegarder
        self._save_personal_data()
        
        # Mettre à jour les métriques
        self.metrics['total_knowledge_items'] = len(self.knowledge_base)
        
        print(f"💡 Connaissance ajoutée : {content[:50]}...")
        print(f"🔗 Connexions trouvées : {len(knowledge.connections)}")
        
        return knowledge_id
    
    def _create_harmonic_embedding(self, content: str) -> np.ndarray:
        """
        Crée un embedding harmonique déterministe
        
        Basé sur la Physique Harmonique :
        - Représentation mathématique exacte
        - Pas de hasard, pas de probabilités
        - Reproductible
        """
        
        # Convertir le contenu en vecteur numérique
        content_bytes = content.encode('utf-8')
        
        # Taille fixe pour l'embedding
        embedding_size = 64
        embedding = np.zeros(embedding_size)
        
        # Remplir avec des valeurs déterministes basées sur le contenu
        for i, byte_val in enumerate(content_bytes[:embedding_size]):
            # Fonction harmonique déterministe
            embedding[i] = np.sin(byte_val * np.pi / 256) * np.cos(i * np.pi / embedding_size)
        
        # Normaliser
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
    
    def _find_harmonic_connections(self, knowledge_id: str):
        """
        Trouve les connexions harmoniques entre connaissances
        
        Principe : Similarité harmonique des embeddings
        """
        
        if knowledge_id not in self.knowledge_base:
            return
        
        current_knowledge = self.knowledge_base[knowledge_id]
        current_embedding = current_knowledge.embedding
        
        if current_embedding is None:
            return
        
        # Calculer la similarité harmonique avec les connaissances existantes
        similarities = []
        
        for other_id, other_knowledge in self.knowledge_base.items():
            if other_id == knowledge_id or other_knowledge.embedding is None:
                continue
            
            # Similarité cosinus (déterministe)
            similarity = np.dot(current_embedding, other_knowledge.embedding)
            similarities.append((other_id, similarity))
        
        # Trier par similarité
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Connecter aux plus similaires (seuil harmonique)
        connection_threshold = 0.7
        for other_id, similarity in similarities:
            if similarity > connection_threshold:
                # Ajouter la connexion bidirectionnelle
                current_knowledge.connections.append(other_id)
                self.knowledge_base[other_id].connections.append(knowledge_id)
                
                # Mettre à jour le graphe de connaissances
                self.context.knowledge_graph[knowledge_id].append(other_id)
                self.context.knowledge_graph[other_id].append(knowledge_id)
        
        self.metrics['connections_made'] = sum(len(k.connections) for k in self.knowledge_base.values()) // 2
    
    def _update_context_from_knowledge(self, knowledge: PersonalKnowledge):
        """Met à jour le contexte personnel à partir d'une nouvelle connaissance"""
        
        # Ajouter aux activités récentes
        self.context.recent_activities.append(f"Appris: {knowledge.content[:50]}...")
        if len(self.context.recent_activities) > 10:
            self.context.recent_activities.pop(0)
        
        # Mettre à jour les préférences
        for tag in knowledge.tags:
            if tag not in self.context.preferences:
                self.context.preferences[tag] = 0
            self.context.preferences[tag] += knowledge.importance
        
        # Détecter les patterns
        self._detect_personal_patterns()
    
    def _detect_personal_patterns(self):
        """Détecte les patterns personnels d'apprentissage"""
        
        # Pattern temporel : quand apprend-on le plus ?
        hour_counts = defaultdict(int)
        for knowledge in self.knowledge_base.values():
            # Gérer le cas où timestamp est une chaîne
            if isinstance(knowledge.timestamp, str):
                try:
                    # Parser la date ISO
                    dt = datetime.fromisoformat(knowledge.timestamp)
                    hour = dt.hour
                except:
                    continue
            else:
                hour = knowledge.timestamp.hour
            hour_counts[hour] += 1
        
        if hour_counts:
            best_hour = max(hour_counts, key=hour_counts.get)
            self.context.patterns['best_learning_hour'] = best_hour
        
        # Pattern thématique : quels sujets ?
        tag_counts = defaultdict(int)
        for knowledge in self.knowledge_base.values():
            for tag in knowledge.tags:
                tag_counts[tag] += 1
        
        if tag_counts:
            top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            self.context.patterns['top_interests'] = [tag for tag, _ in top_tags]
    
    def query_personal_ai(self, query: str, context: str = "") -> Dict[str, Any]:
        """
        Interroge l'IA personnelle
        
        Args:
            query: Question ou demande
            context: Contexte additionnel
            
        Returns:
            Réponse personnalisée avec connaissances pertinentes
        """
        
        print(f"🤔 Question personnelle : {query}")
        
        # Créer l'embedding de la question
        query_embedding = self._create_harmonic_embedding(query + " " + context)
        
        # Trouver les connaissances pertinentes
        relevant_knowledge = self._find_relevant_knowledge(query_embedding)
        
        # Générer une réponse personnalisée
        response = self._generate_personalized_response(query, relevant_knowledge, context)
        
        # Mettre à jour le contexte
        self.context.current_task = query
        
        # Sauvegarder l'interaction
        self.add_knowledge(
            content=f"Q: {query}",
            context=f"Query at {datetime.now().isoformat()}",
            tags=["query", "interaction"],
            importance=0.3
        )
        
        return response
    
    def _find_relevant_knowledge(self, query_embedding: np.ndarray, max_results: int = 5) -> List[PersonalKnowledge]:
        """Trouve les connaissances les plus pertinentes pour la question"""
        
        similarities = []
        
        for knowledge in self.knowledge_base.values():
            if knowledge.embedding is None:
                continue
            
            similarity = np.dot(query_embedding, knowledge.embedding)
            similarities.append((knowledge, similarity))
        
        # Trier par similarité
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Retourner les plus pertinentes
        return [k for k, _ in similarities[:max_results]]
    
    def _generate_personalized_response(self, query: str, relevant_knowledge: List[PersonalKnowledge], context: str) -> Dict[str, Any]:
        """Génère une réponse personnalisée basée sur les connaissances pertinentes"""
        
        response = {
            'query': query,
            'context': context,
            'personal_insights': [],
            'relevant_knowledge': [],
            'personal_connections': [],
            'suggestions': [],
            'confidence': 0.0,
            'timestamp': datetime.now().isoformat()
        }
        
        # Analyser les connaissances pertinentes
        for knowledge in relevant_knowledge:
            response['relevant_knowledge'].append({
                'content': knowledge.content,
                'context': knowledge.context,
                'importance': knowledge.importance,
                'timestamp': knowledge.timestamp.isoformat(),
                'tags': knowledge.tags
            })
        
        # Générer des insights personnels
        if relevant_knowledge:
            # Insight basé sur l'importance moyenne
            avg_importance = np.mean([k.importance for k in relevant_knowledge])
            response['personal_insights'].append(
                f"Basé sur votre expérience, ce sujet a une importance personnelle de {avg_importance:.2f}/1.0"
            )
            
            # Insight basé sur les connexions
            total_connections = sum(len(k.connections) for k in relevant_knowledge)
            if total_connections > 0:
                response['personal_insights'].append(
                    f"Ce sujet est connecté à {total_connections} autres connaissances personnelles"
                )
        
        # Suggestions basées sur les patterns personnels
        if 'best_learning_hour' in self.context.patterns:
            best_hour = self.context.patterns['best_learning_hour']
            response['suggestions'].append(
                f"Vous apprenez le mieux vers {best_hour}h, considérez explorer ce sujet à ce moment"
            )
        
        if 'top_interests' in self.context.patterns:
            top_interests = self.context.patterns['top_interests']
            response['suggestions'].append(
                f"Vos intérêts principaux : {', '.join(top_interests[:3])}"
            )
        
        # Calculer la confiance
        if relevant_knowledge:
            response['confidence'] = min(1.0, len(relevant_knowledge) / 5.0)
        
        return response
    
    def get_personal_summary(self) -> Dict[str, Any]:
        """Retourne un résumé de l'IA personnelle"""
        
        total_knowledge = len(self.knowledge_base)
        total_connections = sum(len(k.connections) for k in self.knowledge_base.values()) // 2
        
        # Calculer les métriques personnelles
        avg_importance = np.mean([k.importance for k in self.knowledge_base.values()]) if self.knowledge_base else 0
        connection_density = total_connections / max(1, total_knowledge * (total_knowledge - 1) / 2)
        
        summary = {
            'user_id': self.user_id,
            'knowledge_metrics': {
                'total_items': total_knowledge,
                'total_connections': total_connections,
                'avg_importance': avg_importance,
                'connection_density': connection_density,
                'top_tags': self._get_top_tags()
            },
            'personal_patterns': self.context.patterns,
            'current_context': {
                'current_task': self.context.current_task,
                'recent_activities': self.context.recent_activities[-5:],
                'preferences': dict(list(self.context.preferences.items())[:10])
            },
            'ai_metrics': {
                'personalization_score': min(1.0, total_knowledge / 100),  # Normalisé
                'learning_rate': self._calculate_learning_rate(),
                'memory_efficiency': self._calculate_memory_efficiency()
            }
        }
        
        return summary
    
    def _get_top_tags(self, limit: int = 10) -> List[Tuple[str, float]]:
        """Retourne les tags les plus utilisés"""
        
        tag_counts = defaultdict(int)
        tag_importance = defaultdict(float)
        
        for knowledge in self.knowledge_base.values():
            for tag in knowledge.tags:
                tag_counts[tag] += 1
                tag_importance[tag] += knowledge.importance
        
        # Calculer le score combiné
        tag_scores = []
        for tag in tag_counts:
            score = tag_counts[tag] * 0.5 + tag_importance[tag] * 0.5
            tag_scores.append((tag, score))
        
        tag_scores.sort(key=lambda x: x[1], reverse=True)
        return tag_scores[:limit]
    
    def _calculate_learning_rate(self) -> float:
        """Calcule le taux d'apprentissage personnel"""
        
        if len(self.knowledge_base) < 2:
            return 0.0
        
        # Trier par timestamp
        sorted_knowledge = sorted(self.knowledge_base.values(), key=lambda k: k.timestamp)
        
        # Calculer l'accélération d'apprentissage
        recent_count = len([k for k in sorted_knowledge if k.timestamp > datetime.now() - timedelta(days=7)])
        older_count = len([k for k in sorted_knowledge if k.timestamp <= datetime.now() - timedelta(days=7)])
        
        if older_count == 0:
            return 1.0
        
        learning_rate = recent_count / older_count
        return min(2.0, learning_rate)  # Capper à 2x
    
    def _calculate_memory_efficiency(self) -> float:
        """Calcule l'efficacité de la mémoire personnelle"""
        
        if not self.knowledge_base:
            return 0.0
        
        # Efficacité basée sur la densité de connexions
        total_possible_connections = len(self.knowledge_base) * (len(self.knowledge_base) - 1) / 2
        actual_connections = sum(len(k.connections) for k in self.knowledge_base.values()) // 2
        
        if total_possible_connections == 0:
            return 1.0
        
        efficiency = actual_connections / total_possible_connections
        return efficiency
    
    def _load_personal_data(self):
        """Charge les données personnelles depuis le stockage"""
        
        try:
            # Charger la base de connaissances
            knowledge_file = self.storage_path / "knowledge_base.json"
            if knowledge_file.exists():
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    knowledge_data = json.load(f)
                
                for item_data in knowledge_data:
                    knowledge = PersonalKnowledge(**item_data)
                    # Recréer l'embedding
                    knowledge.embedding = self._create_harmonic_embedding(knowledge.content)
                    self.knowledge_base[knowledge.id] = knowledge
            
            # Charger le contexte
            context_file = self.storage_path / "context.json"
            if context_file.exists():
                with open(context_file, 'r', encoding='utf-8') as f:
                    context_data = json.load(f)
                
                # Recréer les objets
                self.context = PersonalContext(**context_data)
                self.context.knowledge_graph = defaultdict(list, context_data.get('knowledge_graph', {}))
            
            print(f"✅ Données personnelles chargées : {len(self.knowledge_base)} connaissances")
            
        except Exception as e:
            print(f"⚠️ Erreur chargement données : {e}")
    
    def _save_personal_data(self):
        """Sauvegarde les données personnelles"""
        
        try:
            # Sauvegarder la base de connaissances (sans les embeddings)
            knowledge_data = []
            for knowledge in self.knowledge_base.values():
                knowledge_dict = asdict(knowledge)
                knowledge_dict['embedding'] = None  # Ne pas sauvegarder l'embedding
                knowledge_dict['timestamp'] = knowledge.timestamp.isoformat()
                knowledge_data.append(knowledge_dict)
            
            knowledge_file = self.storage_path / "knowledge_base.json"
            with open(knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(knowledge_data, f, indent=2, ensure_ascii=False)
            
            # Sauvegarder le contexte
            context_file = self.storage_path / "context.json"
            context_dict = asdict(self.context)
            context_dict['knowledge_graph'] = dict(self.context.knowledge_graph)
            with open(context_file, 'w', encoding='utf-8') as f:
                json.dump(context_dict, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde données : {e}")

# Singleton global pour l'utilisateur
_personal_ai_instances = {}

def get_personal_ai(user_id: str, storage_path: Optional[Path] = None) -> HarmonicPersonalAI:
    """Récupère ou crée l'IA personnelle pour un utilisateur"""
    if user_id not in _personal_ai_instances:
        _personal_ai_instances[user_id] = HarmonicPersonalAI(user_id, storage_path)
    return _personal_ai_instances[user_id]

if __name__ == "__main__":
    print("🧠 HCV PRO - IA Personnelle Harmonique")
    print("📚 Apprend de votre quotidien")
    print("🔗 Crée des connexions personnelles")
    print("🎯 S'adapte à vos besoins")
    print()
    
    # Démonstration
    ai = get_personal_ai("demo_user")
    
    # Ajouter des connaissances personnelles
    print("💭 Ajout de connaissances personnelles...")
    
    ai.add_knowledge(
        content="J'aime travailler sur HCV PRO le matin",
        context="Travail quotidien",
        tags=["hcv-pro", "matin", "préférence"],
        importance=0.8
    )
    
    ai.add_knowledge(
        content="Les réunions Zoom me fatiguent après 2 heures",
        context="Expérience professionnelle",
        tags=["zoom", "réunions", "fatigue"],
        importance=0.6
    )
    
    ai.add_knowledge(
        content="Je préfère le café au thé le matin",
        context="Préférences personnelles",
        tags=["café", "thé", "matin"],
        importance=0.4
    )
    
    # Interroger l'IA personnelle
    print("\n🤔 Interrogation de l'IA personnelle...")
    
    response = ai.query_personal_ai("Qu'est-ce que je préfère le matin ?", "contexte de travail")
    
    print(f"\n📝 Réponse personnalisée :")
    print(f"   💡 Insights : {response['personal_insights']}")
    print(f"   🔗 Connaissances pertinentes : {len(response['relevant_knowledge'])}")
    print(f"   💡 Suggestions : {response['suggestions']}")
    print(f"   🎯 Confiance : {response['confidence']:.2f}")
    
    # Résumé personnel
    print("\n📊 Résumé de l'IA personnelle :")
    summary = ai.get_personal_summary()
    
    print(f"   📚 Connaissances : {summary['knowledge_metrics']['total_items']}")
    print(f"   🔗 Connexions : {summary['knowledge_metrics']['total_connections']}")
    print(f"   📈 Score de personnalisation : {summary['ai_metrics']['personalization_score']:.2f}")
    print(f"   🧠 Taux d'apprentissage : {summary['ai_metrics']['learning_rate']:.2f}")
    
    print("\n🏆 IA Personnelle Harmonique : Votre intelligence augmentée !")
