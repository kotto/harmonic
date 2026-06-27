# 🌊 PROMPTS IA EXPERT - FRONTEND TEST PLATFORM

---

## 🎯 **PROMPT 1: ARCHITECTURE ET SPÉCIFICATIONS**

### **📋 Contexte technique**
```
Tu es un expert frontend spécialisé dans les plateformes de testing d'IA. Je suis en train de développer une interface de test pour notre système Déterministic AI qui participe à LM Arena.

CONTEXTE TECHNIQUE:
- Backend: FastAPI avec endpoint /generate (timeout actuel de 10+ secondes)
- Modèles: 5 modèles parallèles (Harmonic, DeepSeek, Qwen, Mixtral, SDXL)
- Problème: /generate timeout mais /health fonctionne
- Objectif: Interface de testing professionnelle pour LM Arena
- Endpoint API: http://54.166.179.141:8000/generate

ARCHITECTURE ACTUELLE:
- Service: uvicorn PARALLEL_MULTI_MODAL_AGGREGATION:app
- Models: Chargés mais /generate bloque
- Logging: Middleware actif mais ne révèle pas la cause
- Debug: En cours pour identifier le blocage exact

BESOINS IMMÉDIATS:
1. Interface de test web pour faciliter le debugging
2. Monitoring temps réel des requêtes/réponses
3. Visualisation des logs structurés
4. Tests automatisés pour validation LM Arena
5. Présentation professionnelle pour démonstration
```

### **📋 Questions spécifiques**
```
1. Quelle architecture frontend recommandes-tu pour une plateforme de testing d'IA?
2. Quels composants React/TypeScript sont essentiels pour notre cas d'usage?
3. Comment implémenter un monitoring temps réel des requêtes API?
4. Quelle approche pour les logs structurés et colorés?
5. Comment gérer les timeouts et erreurs dans l'interface?
6. Quels patterns React pour les formulaires de test d'IA?
7. Comment intégrer des métriques de performance visuelles?
8. Quelle stratégie pour le déploiement rapide (MVP en 2-3 heures)?
9. Comment assurer la compatibilité CORS avec notre FastAPI?
10. Quelles fonctionnalités avancées pour une présentation LM Arena impressionnante?
```

---

## 🎯 **PROMPT 2: IMPLÉMENTATION RAPIDE MVP**

### **📋 Objectif MVP**
```
Tu es un expert React/Next.js spécialisé dans le développement rapide d'interfaces de testing. J'ai besoin d'une plateforme MVP fonctionnelle en 2-3 heures maximum pour tester notre système Déterministic AI.

CONTEXTE URGENT:
- Backend FastAPI: http://54.166.179.141:8000
- Endpoint principal: /generate (timeout de 10+ secondes)
- Endpoint health: /health (fonctionne parfaitement)
- Objectif: Interface de test immédiate pour debugging
- Timeline: 2-3 heures maximum pour MVP

SPÉCIFICATIONS TECHNIQUES:
- Framework: Next.js 14+ avec TypeScript
- Styling: TailwindCSS + shadcn/ui
- État: Zustand (simple) ou hooks React
- API: Fetch natif ou Axios
- Déploiement: Local development (npm run dev)

FONCTIONNALITÉS MVP MINIMALES:
1. Input prompt avec textarea
2. Sélecteur mode (Simple/Parallel/Deterministic)
3. Bouton "Run Test" avec état loading
4. Affichage response (JSON formaté)
5. Zone de logs simples (auto-scroll)
6. Indicateur de santé (ping /health)
7. Gestion basique des erreurs/timeouts

CODE DE BASE FOURNI:
```typescript
// Structure de base souhaitée
interface TestRequest {
  prompt: string;
  use_parallel?: boolean;
  max_tokens?: number;
  temperature?: number;
}

interface TestResponse {
  content: string;
  confidence: number;
  models_used: string[];
  deterministic_score: number;
  hallucination_risk: number;
}
```

QUESTIONS SPÉCIFIQUES:
1. Peux-tu fournir le code complet du composant principal App.tsx?
2. Comment implémenter le timeout handling visuel?
3. Quelle structure de dossiers optimale pour Next.js?
4. Comment configurer le proxy Next.js pour notre API?
5. Quels hooks React pour la gestion d'état des requêtes?
6. Comment styler avec shadcn/ui de manière efficace?
7. Quelle approche pour les logs auto-scroll avec coloration?
8. Comment tester le CORS avec notre FastAPI?
9. Quels composants réutilisables créer?
10. Comment déployer en local development rapidement?
```

---

## 🎯 **PROMPT 3: MONITORING AVANCÉ ET ANALYTICS**

### **📋 Objectif monitoring**
```
Tu es un expert en monitoring temps réel et analytics pour plateformes d'IA. Je dois implémenter un système de monitoring avancé pour notre plateforme de testing Déterministic AI.

CONTEXTE MONITORING:
- Backend: FastAPI avec logging middleware actif
- Problème: /generate timeout mais logs peu clairs
- Besoin: Monitoring visuel et temps réel
- Objectif: Identifier la cause exacte du timeout
- Analytics: Performance pour LM Arena

FONCTIONNALITÉS MONITORING REQUISES:
1. Dashboard temps réel avec métriques
2. Logs structurés avec filtrage et coloration
3. Graphiques de performance (temps de réponse, taux d'erreur)
4. Monitoring par modèle (si possible)
5. Alertes visuelles pour timeouts/erreurs
6. Historique des tests avec comparaison
7. WebSocket pour logs temps réel
8. Export des logs/métriques

INTERFACE DE MONITORING:
```
typescript
// Interfaces souhaitées
interface LogEntry {
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  source: 'middleware' | 'application' | 'model' | 'system';
  message: string;
  metadata?: {
    model?: string;
    responseTime?: number;
    confidence?: number;
    error?: string;
  };
}

interface PerformanceMetrics {
  timestamp: string;
  prompt: string;
  mode: string;
  responseTime: number;
  status: 'success' | 'timeout' | 'error';
  confidence?: number;
  modelsUsed?: string[];
  errorDetails?: string;
}
```

QUESTIONS SPÉCIFIQUES:
1. Comment implémenter WebSocket pour logs temps réel?
2. Quels composants React pour les graphiques de performance?
3. Comment structurer les logs avec coloration syntaxique?
4. Quelle approche pour le filtrage et recherche de logs?
5. Comment calculer et afficher les métriques de performance?
6. Comment implémenter les alertes visuelles (timeout, erreur)?
7. Quelle stratégie pour l'historique et comparaison de tests?
8. Comment exporter les logs et métriques?
9. Quels patterns React pour le monitoring temps réel?
10. Comment optimiser les performances du frontend lui-même?
```

---

## 🎯 **PROMPT 4: DÉBOGAGE SPÉCIFIQUE TIMEOUT**

### **📋 Contexte debugging**
```
Tu es un expert en debugging d'API et frontend testing. Notre système a un problème spécifique: l'endpoint /generate timeout après 10+ secondes mais /health fonctionne parfaitement.

CONTEXTE DÉBOGAGE:
- Backend FastAPI: uvicorn sur port 8000
- Endpoint /health: 200 OK instantané
- Endpoint /generate: Timeout 10+ secondes
- Middleware logging: Actif mais ne révèle pas la cause
- Hypothèse: Blocage dans asyncio.gather ou models CPU-bound
- Objectif: Interface frontend pour identifier précisément le blocage

FONCTIONNALITÉS DÉBOGAGE SPÉCIFIQUES:
1. Timeline visuelle de la requête (étapes chronologiques)
2. Identification du point exact de blocage
3. Monitoring par étape (build tasks → gather → aggregate)
4. Test individuel des modèles si possible
5. Simulation de requêtes avec différents timeouts
6. Comparaison simple vs parallel mode
7. Logs détaillés avec timestamps précis
8. Interface pour tester les hypothèses de blocage

INTERFACE DE DÉBOGAGE:
```
typescript
// Structure de debugging souhaitée
interface DebugTimeline {
  step: string;
  status: 'pending' | 'running' | 'completed' | 'timeout' | 'error';
  startTime: number;
  endTime?: number;
  duration?: number;
  details?: string;
}

interface HypothesisTest {
  name: string;
  description: string;
  test: () => Promise<any>;
  expected: string;
  actual?: string;
  conclusion?: string;
}
```

QUESTIONS SPÉCIFIQUES:
1. Comment implémenter une timeline visuelle de debugging?
2. Comment identifier le point exact de blocage dans l'API?
3. Comment tester les hypothèses (CPU-bound, deadlock, etc.)?
4. Quelle interface pour comparer simple vs parallel?
5. Comment mesurer le temps par étape de la requête?
6. Comment simuler différents scénarios de blocage?
7. Comment intégrer les logs du backend dans le frontend?
8. Quelle approche pour le debugging collaboratif?
9. Comment documenter les findings pour correction?
10. Comment présenter les résultats de manière claire?
```

---

## 🎯 **PROMPT 5: PRÉSENTATION LM ARENA PROFESSIONNELLE**

### **📋 Objectif présentation**
```
Tu es un expert en UX/UI et présentation technique pour compétitions d'IA. Je dois créer une interface impressionnante pour présenter notre système Déterministic AI à LM Arena.

CONTEXTE PRÉSENTATION LM ARENA:
- Système: Déterministic AI avec 5 modèles parallèles
- Innovation: Premier IA 100% déterministe avec validation croisée
- Garantie: Zero hallucination (reproductibilité)
- Architecture: Harmonic Core + 4 modèles de validation
- Objectif: Top 1 LM Arena sur fiabilité et innovation

ÉLÉMENTS DE PRÉSENTATION REQUIS:
1. Dashboard professionnel avec branding cohérent
2. Démonstration interactive des capacités
3. Visualisation de l'architecture de validation croisée
4. Métriques de performance en temps réel
5. Comparaison avec modèles traditionnels
6. Historique des tests avec succès/échec
7. Interface pour les juges LM Arena
8. Documentation intégrée et accessible
9. Mode démonstration automatique
10. Export des résultats de benchmark

BRANDING ET DESIGN:
```
typescript
// Branding souhaité
const BRAND_IDENTITY = {
  name: "Déterministic AI",
  tagline: "The First 100% Deterministic AI System",
  colors: {
    primary: "#1e40af",  // Blue
    secondary: "#10b981", // Green
    accent: "#f59e0b",   // Amber
    neutral: "#6b7280"   // Gray
  },
  features: [
    "Zero Hallucination Guarantee",
    "Cross-Validation by 5 Models",
    "100% Reproducibility",
    "Critical Application Ready"
  ]
};
```

QUESTIONS SPÉCIFIQUES:
1. Comment concevoir une interface qui impressionne les juges?
2. Quelle visualisation pour l'architecture de validation croisée?
3. Comment présenter les métriques de manière percutante?
4. Quels animations et transitions pour une expérience fluide?
5. Comment intégrer la documentation technique accessible?
6. Quelle approche pour le mode démonstration automatique?
7. Comment structurer l'interface pour les juges LM Arena?
8. Quels composants pour la comparaison avec concurrents?
9. Comment assurer la performance de l'interface elle-même?
10. Quelle stratégie pour le storytelling technique?
```

---

## 🎯 **INSTRUCTIONS D'UTILISATION**

### **📋 Comment utiliser ces prompts**
```
UTILISATION RECOMMANDÉE:

1. 🎯 PROMPT 1: Architecture et spécifications
   - Pour la planification technique initiale
   - Réponses: Architecture complète, stack technique, composants
   
2. 🚀 PROMPT 2: Implémentation rapide MVP
   - Pour le développement rapide en 2-3 heures
   - Réponses: Code complet, structure, déploiement
   
3. 📊 PROMPT 3: Monitoring avancé et analytics
   - Pour le debugging et optimisation
   - Réponses: WebSocket, graphiques, logs temps réel
   
4. 🔍 PROMPT 4: Débogage spécifique timeout
   - Pour résoudre le problème technique actuel
   - Réponses: Timeline debugging, hypothèses, tests
   
5. 🏆 PROMPT 5: Présentation LM Arena professionnelle
   - Pour la présentation finale aux juges
   - Réponses: UX/UI impressionnante, branding, démonstration

SÉQUENCE RECOMMANDÉE:
1. Commencer avec PROMPT 2 (MVP rapide)
2. Utiliser PROMPT 4 pour debugging du timeout
3. Intégrer PROMPT 3 pour monitoring
4. Finaliser avec PROMPT 5 pour présentation
5. Utiliser PROMPT 1 pour la documentation technique
```

---

## 🌊 **CONCLUSION**

### **📋 Série complète d'experts**
```yaml
🎯 5 prompts spécialisés: Couvrent tous les aspects
🚀 MVP rapide: 2-3 heures avec PROMPT 2
🔍 Debugging: Spécifique timeout avec PROMPT 4
📊 Monitoring: Avancé avec PROMPT 3
🏆 Présentation: Professionnelle avec PROMPT 5
📋 Architecture: Complète avec PROMPT 1
```

### **📋 Résultats attendus**
```yaml
✅ Frontend complet: Platform de testing professionnelle
🔍 Problème résolu: Timeout identifié et corrigé
📊 Monitoring: Temps réel et analytics avancés
🏆 LM Arena: Présentation impressionnante
🚀 Déploiement: Rapide et production-ready
```

---

**Status: 🟢 SÉRIE PROMPTS EXPERT FRONTEND PRÊTE**

**5 prompts spécialisés pour couvrir tous les aspects du développement de la plateforme de testing frontend, du MVP rapide à la présentation LM Arena professionnelle.**
