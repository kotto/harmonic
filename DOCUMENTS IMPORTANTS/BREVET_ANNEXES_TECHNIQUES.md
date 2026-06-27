# ANNEXES TECHNIQUES DU BREVET
## Système et procédé pour la génération déterministe et auditable de réponses par IA

---

## ANNEXE D : DESSINS TECHNIQUES DÉTAILLÉS

### FIGURE D1 : Diagramme de séquence complet
```
┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Client  │     │   API       │     │  Cache      │     │  Backend    │
│         │     │  FastAPI    │     │  LRU        │     │   IA        │
└────┬────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
     │                 │                   │                   │
     │ 1. POST /generate                  │                   │
     │─────────────────>                  │                   │
     │                 │                   │                   │
     │                 │ 2. Vérif. temp.   │                   │
     │                 │    (force 0.0)    │                   │
     │                 │<──────────────────│                   │
     │                 │                   │                   │
     │                 │ 3. Calcul clé cache│                   │
     │                 │    SHA256(params) │                   │
     │                 │<──────────────────│                   │
     │                 │                   │                   │
     │                 │ 4. Check cache    │                   │
     │                 │──────────────────>│                   │
     │                 │                   │                   │
     │                 │    5. Cache hit?  │                   │
     │                 │<──────────────────│                   │
     │                 │                   │                   │
     │                 │ 6. Mode vérifié?  │                   │
     │                 │<──────────────────│                   │
     │                 │                   │                   │
     │                 │ 7. Détection      │                   │
     │                 │    question fact. │                   │
     │                 │<──────────────────│                   │
     │                 │                   │                   │
     │                 │ 8. Génération     │                   │
     │                 │    réponse        │                   │
     │                 │──────────────────────────────────────>│
     │                 │                   │                   │
     │                 │    9. Retour      │                   │
     │                 │<──────────────────────────────────────│
     │                 │                   │                   │
     │                 │10. Calcul Response_ID│                   │
     │                 │<──────────────────│                   │
     │                 │                   │                   │
     │                 │11. Mise en cache  │                   │
     │                 │──────────────────>│                   │
     │                 │                   │                   │
     │ 12. Réponse     │                   │                   │
     │<────────────────│                   │                   │
     │                 │                   │                   │
```

### FIGURE D2 : Structure de données du cache
```
Structure CacheEntry:
┌─────────────────────────────────────────────┐
│ Clé: SHA256(concaténation des paramètres)   │
│ • Mode: "default"                           │
│ • Max_tokens: 1000                          │
│ • Verified_mode: 1                          │
│ • Sources_hash: SHA256("source1\nsource2")  │
│ • Prompt: "Calcul IMC..."                   │
├─────────────────────────────────────────────┤
│ Valeur: JSON réponse                        │
│ • content: "L'IMC est de 25..."             │
│ • response_id: "sha256:abc123..."           │
│ • verified_mode: true                       │
│ • citations: [{"id":"S1","source":"..."}]   │
│ • metrics: {                                │
│     "deterministic_lock": true,             │
│     "cache_hit": false,                     │
│     "sources_count": 2,                     │
│     "processing_time": 0.0                  │
│   }                                         │
└─────────────────────────────────────────────┘

Gestion LRU:
┌─────┬─────┬─────┬─────┬─────┐
│ E1  │ E2  │ E3  │ E4  │ E5  │  ← Ordre d'accès
└─────┴─────┴─────┴─────┴─────┘
     ↑                 ↑
  Most Recent     Least Recent
```

### FIGURE D3 : Algorithme de détection de questions factuelles
```
Fonction: _needs_external_facts(prompt)
Entrée: prompt (chaîne de caractères)
Sortie: booléen (vrai si question factuelle)

Étapes:
1. Convertir prompt en minuscules → prompt_lower
2. Liste indicateurs = [
   "quel est", "combien", "quand", "où", "qui",
   "pourquoi", "comment", "statistiques", "données",
   "chiffres", "taux", "pourcentage", "nombre de",
   "date de", "valeur de", "montant", "coût"
   ]
3. Pour chaque indicateur dans liste:
   Si indicateur dans prompt_lower:
      Retourner VRAI
4. Liste mots-clés factuels = [
   "2025", "2026", "euros", "dollars", "pourcent",
   "millions", "milliards", "kg", "m", "cm"
   ]
5. Pour chaque mot-clé dans liste:
   Si mot-clé dans prompt_lower:
      Retourner VRAI
6. Retourner FAUX
```

### FIGURE D4 : Format de réponse standardisé
```
{
  "content": "Le patient présente un IMC de 25.0 [S1], ce qui correspond à une catégorie surpoids selon les standards de l'OMS.",
  "confidence": 0.95,
  "processing_time": 0.0,
  "version": "2.0.0-real",
  "response_id": "sha256:8f3a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7",
  "verified_mode": true,
  "citations": [
    {
      "id": "S1",
      "source": "IMC (Indice de Masse Corporelle) = poids(kg) / taille(m)^2. Catégories: <18.5 maigreur; 18.5–24.9 normal; 25–29.9 surpoids; ≥30 obésité."
    }
  ],
  "metrics": {
    "deterministic_lock": true,
    "cache_hit": false,
    "sources_count": 1,
    "policy_applied": "citations_required",
    "abstention_reason": null,
    "response_length": 125,
    "timestamp": "2026-05-15T14:30:45Z"
  }
}
```

---

## ANNEXE E : ALGORITHMES DÉTAILLÉS

### ALGORITHME E1 : Génération déterministe avec cache
```
Fonction: generate_deterministic_response(request)
Entrée: GenerationRequest {prompt, max_tokens, temperature, verified_mode, sources}
Sortie: GenerationResponse

Étapes:
1. // Vérification déterminisme
   SI _DETERMINISTIC_LOCK = VRAI:
      temperature_effective = 0.0
   SINON:
      temperature_effective = request.temperature OU 0.0

2. // Calcul clé cache
   sources_list = request.sources OU liste_vide
   sources_hash = SHA256(concaténation(sources_list, "\n"))
   payload_parts = [
      "default",                    // mode
      str(request.max_tokens),
      str(int(request.verified_mode OU FAUX)),
      sources_hash,
      request.prompt
   ]
   cache_key = SHA256(concaténation(payload_parts, "\n"))

3. // Vérification cache
   cached_response = _cache_get(cache_key)
   SI cached_response ≠ NULL:
      cached_response.metrics.cache_hit = VRAI
      RETOURNER cached_response

4. // Traitement mode vérifié
   SI request.verified_mode = VRAI:
      SI _needs_external_facts(request.prompt):
         SI sources_list = liste_vide:
            content = _build_abstention(request.prompt, "sources_manquantes")
            citations = liste_vide
         SINON:
            content = _build_verified_response(request.prompt, sources_list)
            citations = _extract_citations(content)
      SINON:
         content = _generate_normal_response(request.prompt)
         citations = liste_vide
   SINON:
      content = _generate_normal_response(request.prompt)
      citations = liste_vide

5. // Calcul Response_ID
   response_id = _compute_response_id(
      request.prompt,
      request.max_tokens,
      "default",
      request.verified_mode OU FAUX,
      sources_list,
      "2.0.0"
   )

6. // Construction réponse
   response = GenerationResponse(
      content = content,
      confidence = _compute_confidence(content, sources_list),
      processing_time = 0.0,  // stabilisé pour déterminisme
      version = "2.0.0-real",
      response_id = response_id,
      verified_mode = request.verified_mode OU FAUX,
      citations = citations,
      metrics = {
         "deterministic_lock": _DETERMINISTIC_LOCK,
         "cache_hit": FAUX,
         "sources_count": len(sources_list),
         "policy_applied": _get_policy_applied(request),
         "abstention_reason": _get_abstention_reason(si applicable),
         "response_length": len(content),
         "timestamp": timestamp_ISO8601()
      }
   )

7. // Mise en cache
   _cache_put(cache_key, response)

8. RETOURNER response
```

### ALGORITHME E2 : Extraction et validation des citations
```
Fonction: _extract_and_validate_citations(content, sources_list)
Entrée: content (texte réponse), sources_list (liste sources)
Sortie: liste citations validées

Étapes:
1. citations_found = liste_vide
2. // Recherche marqueurs [SX] dans content
   pattern = r'\[S(\d+)\]'
   matches = trouver_tous(pattern, content)
   
3. POUR CHAQUE match dans matches:
      citation_id = "S" + match.groupe(1)
      // Vérifier que l'ID correspond à une source existante
      SI citation_id est numérique ET int(citation_id[1:]) ≤ len(sources_list):
         source_index = int(citation_id[1:]) - 1  // indices 0-based
         source_text = sources_list[source_index]
         citation = {
            "id": citation_id,
            "source": source_text[:200] + "..." SI len(source_text) > 200
         }
         AJOUTER citation à citations_found
   
4. // Vérifier que toutes les sources sont citées si mode strict
   SI mode_strict = VRAI:
      POUR i = 1 À len(sources_list):
         citation_id_attendu = "S" + str(i)
         SI citation_id_attendu non trouvé dans content:
            // Générer avertissement dans métriques
            metrics.citation_warnings += 1
   
5. RETOURNER citations_found
```

### ALGORITHME E3 : Benchmark de validation
```
Fonction: run_validation_benchmark(api_url, dataset_path)
Entrée: api_url (URL API), dataset_path (chemin dataset JSON)
Sortie: rapport_benchmark JSON

Étapes:
1. CHARGER dataset depuis dataset_path
2. résultats = dictionnaire_vide
3. métriques_globales = {
      "total_cases": 0,
      "passed_cases": 0,
      "determinism_score": 0.0,
      "abstention_score": 0.0,
      "citation_score": 0.0,
      "latency_avg": 0.0
   }
   
4. POUR CHAQUE case dans dataset.cases:
      métriques_globales.total_cases += 1
      case_results = liste_vide
      
      // Test de déterminisme (3 répétitions)
      POUR i = 1 À 3:
         réponse = appeler_api(api_url, case)
         AJOUTER réponse à case_results
      
      // Calcul métriques case
      déterminisme = vérifier_response_id_identique(case_results)
      abstention = vérifier_abstention_correcte(case, case_results[0])
      citations = vérifier_citations_correctes(case, case_results[0])
      latence = calculer_latence_moyenne(case_results)
      
      // Évaluation
      SI déterminisme ET abstention ET citations:
         métriques_globales.passed_cases += 1
         statut = "PASSED"
      SINON:
         statut = "FAILED"
      
      // Stockage résultats case
      résultats[case.id] = {
         "status": statut,
         "determinism": déterminisme,
         "abstention": abstention,
         "citations": citations,
         "avg_latency": latence,
         "responses": case_results
      }
   
5. // Calcul métriques globales
   métriques_globales.determinism_score = 
      (nombre_cases_déterministes / total_cases) * 100
   métriques_globales.abstention_score = 
      (nombre_cases_abstention_correcte / total_cases) * 100
   métriques_globales.citation_score = 
      (nombre_cases_citations_correctes / total_cases) * 100
   métriques_globales.overall_score = 
      (passed_cases / total_cases) * 100
   
6. // Construction rapport
   rapport = {
      "timestamp": timestamp_ISO8601(),
      "api_url": api_url,
      "dataset_version": dataset.version,
      "global_metrics": métriques_globales,
      "case_results": résultats,
      "summary": {
         "total_cases": métriques_globales.total_cases,
         "passed_cases": métriques_globales.passed_cases,
         "overall_score": métriques_globales.overall_score,
         "recommendation": générer_recommandation(métriques_globales)
      }
   }
   
7. RETOURNER rapport
```

---

## ANNEXE F : IMPLÉMENTATIONS CONCRÈTES

### FICHIER F1 : Configuration système complète
```python
# config_deterministic.py
"""
Configuration du système déterministe
"""

import os
from typing import Dict, Any

class DeterministicConfig:
    """Configuration pour le système déterministe"""
    
    def __init__(self):
        # Paramètres de déterminisme
        self.deterministic_lock = self._get_bool_env("DETERMINISTIC_LOCK", True)
        self.cache_max_entries = self._get_int_env("DETERMINISTIC_CACHE_MAX_ENTRIES", 2048)
        self.cache_ttl_seconds = self._get_int_env("CACHE_TTL_SECONDS", 3600)
        
        # Paramètres mode vérifié
        self.verified_mode_default = self._get_bool_env("VERIFIED_MODE_DEFAULT", False)
        self.require_citations = self._get_bool_env("REQUIRE_CITATIONS", True)
        self.min_sources_for_facts = self._get_int_env("MIN_SOURCES_FOR_FACTS", 1)
        
        # Paramètres auditabilité
        self.enable_response_id = self._get_bool_env("ENABLE_RESPONSE_ID", True)
        self.response_id_version = os.getenv("RESPONSE_ID_VERSION", "2.0.0")
        self.enable_detailed_metrics = self._get_bool_env("ENABLE_DETAILED_METRICS", True)
        
        # Paramètres performance
        self.max_retries = self._get_int_env("MAX_RETRIES", 3)
        self.timeout_seconds = self._get_int_env("TIMEOUT_SECONDS", 30)
        self.rate_limit_per_minute = self._get_int_env("RATE_LIMIT_PER_MINUTE", 60)
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Récupère une variable d'environnement booléenne"""
        value = os.getenv(key, "").strip().lower()
        if value in ("true", "1", "yes", "on"):
            return True
        elif value in ("false", "0", "no", "off"):
            return False
        return default
    
    def _get_int_env(self, key: str, default: int) -> int:
        """Récupère une variable d'environnement entière"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit la configuration en dictionnaire"""
        return {
            "deterministic_lock": self.deterministic_lock,
            "cache_max_entries": self.cache_max_entries,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "verified_mode_default": self.verified_mode_default,
            "require_citations": self.require_citations,
            "min_sources_for_facts": self.min_sources_for_facts,
            "enable_response_id": self.enable_response_id,
            "response_id_version": self.response_id_version,
            "enable_detailed_metrics": self.enable_detailed_metrics,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "rate_limit_per_minute": self.rate_limit_per_minute
        }
```

### FICHIER F2 : Module de cache avancé
```python
# deterministic_cache.py
"""
Cache déterministe LRU avec TTL et statistiques
"""

import time
import hashlib
from typing import Dict, Any, Optional, Tuple
from collections import OrderedDict
from threading import Lock

class DeterministicCache:
    """Cache déterministe avec métriques"""
    
    def __init__(self, max_entries: int = 2048, ttl_seconds: int = 3600):
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_entries": 0
        }
        self.lock = Lock()
    
    def make_key(self, params: Dict[str, Any]) -> str:
        """Crée une clé de cache déterministe"""
        # Normalisation des paramètres
        normalized = {
            "prompt": str(params.get("prompt", "")),
            "max_tokens": int(params.get("max_tokens", 1000)),
            "temperature": float(params.get("temperature", 0.0)),
            "verified_mode": bool(params.get("verified_mode", False)),
            "sources": sorted(params.get("sources", [])),
            "mode": str(params.get("mode", "default")),
            "version": str(params.get("version", "1.0.0"))
        }
        
        # Sérialisation JSON canonique
        import json
        serialized = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
        
        # Hachage SHA256
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()
    
    def get(self, key: str) -> Optional[Tuple[Any, float]]:
        """Récupère une entrée du cache"""
        with self.lock:
            if key not in self.cache:
                self.stats["misses"] += 1
                return None
            
            value, timestamp = self.cache[key]
            
            # Vérification TTL
            if time.time() - timestamp > self.ttl_seconds:
                del self.cache[key]
                self.stats["evictions"] += 1
                self.stats["misses"] += 1
                return None
            
            # Mise à jour LRU
            self.cache.move_to_end(key)
            self.stats["hits"] += 1
            return value
    
    def put(self, key: str, value: Any) -> None:
        """Ajoute une entrée au cache"""
        with self.lock:
            # Éviction si nécessaire
            if len(self.cache) >= self.max_entries and key not in self.cache:
                self.cache.popitem(last=False)
                self.stats["evictions"] += 1
            
            # Ajout avec timestamp
            self.cache[key] = (value, time.time())
            self.stats["total_entries"] = len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        with self.lock:
            total = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
            
            return {
                **self.stats,
                "hit_rate_percent": hit_rate,
                "current_size": len(self.cache),
                "max_size": self.max_entries,
                "ttl_seconds": self.ttl_seconds
            }
    
    def clear(self) -> None:
        """Vide le cache"""
        with self.lock:
            self.cache.clear()
            self.stats["evictions"] += len(self.cache)
```

### FICHIER F3 : Validateur de citations
```python
# citation_validator.py
"""
Validation des citations dans les réponses IA
"""

import re
from typing import List, Dict, Any, Tuple

class CitationValidator:
    """Valide les citations dans les réponses"""
    
    def __init__(self):
        self.citation_pattern = re.compile(r'\[S(\d+)\]')
        self.source_patterns = [
            re.compile(r'source\s*:\s*(.+)', re.IGNORECASE),
            re.compile(r'url\s*:\s*(.+)', re.IGNORECASE),
            re.compile(r'ref\s*:\s*(.+)', re.IGNORECASE),
            re.compile(r'\[(\d+)\]\s*(.+)')
        ]
    
    def extract_citations(self, text: str) -> List[str]:
        """Extrait les identifiants de citations du texte"""
        matches = self.citation_pattern.findall(text)
        return [f"S{match}" for match in matches]
    
    def validate_citation_coverage(self, 
                                 text: str, 
                                 sources: List[str],
                                 strict_mode: bool = True) -> Dict[str, Any]:
        """Valide la couverture des citations"""
        citation_ids = self.extract_citations(text)
        unique_citations = set(citation_ids)
        
        # Vérification que toutes les citations référencent des sources existantes
        valid_citations = []
        invalid_citations = []
        
        for citation in unique_citations:
            try:
                # Extraction du numéro (S1 → 1)
                num = int(citation[1:])
                if 1 <= num <= len(sources):
                    valid_citations.append(citation)
                else:
                    invalid_citations.append(citation)
            except ValueError:
                invalid_citations.append(citation)
        
        # Calcul métriques
        total_sources = len(sources)
        cited_sources = len(valid_citations)
        coverage_rate = (cited_sources / total_sources * 100) if total_sources > 0 else 0
        
        # Vérification mode strict
        if strict_mode and total_sources > 0 and cited_sources < total_sources:
            missing_sources = [
                f"S{i+1}" for i in range(total_sources) 
                if f"S{i+1}" not in valid_citations
            ]
        else:
            missing_sources = []
        
        return {
            "total_sources": total_sources,
            "cited_sources": cited_sources,
            "coverage_rate_percent": coverage_rate,
            "valid_citations": valid_citations,
            "invalid_citations": invalid_citations,
            "missing_sources": missing_sources,
            "strict_mode": strict_mode,
            "validation_passed": len(invalid_citations) == 0 and 
                              (not strict_mode or cited_sources == total_sources)
        }
    
    def generate_citation_report(self, 
                               text: str, 
                               sources: List[str]) -> Dict[str, Any]:
        """Génère un rapport détaillé sur les citations"""
        validation = self.validate_citation_coverage(text, sources)
        
        # Analyse sémantique des citations
        citation_contexts = []
        for citation in validation["valid_citations"]:
            # Trouver le contexte autour de la citation
            pattern = re.compile(rf'([^\.\n]*?\[{citation}\][^\.\n]*\.?)')
            contexts = pattern.findall(text)
            citation_contexts.extend(contexts)
        
        return {
            **validation,
            "citation_contexts": citation_contexts,
            "text_length": len(text),
            "citation_density": len(validation["valid_citations"]) / max(1, len(text.split())),
            "recommendations": self._generate_recommendations(validation)
        }
    
    def _generate_recommendations(self, validation: Dict[str, Any]) -> List[str]:
        """Génère des recommandations basées sur la validation"""
        recommendations = []
        
        if validation["invalid_citations"]:
            recommendations.append(
                f"Corriger les citations invalides: {', '.join(validation['invalid_citations'])}"
            )
        
        if validation["missing_sources"]:
            recommendations.append(
                f"Ajouter des citations pour les sources: {', '.join(validation['missing_sources'])}"
            )
        
        if validation["coverage_rate_percent"] < 80:
            recommendations.append(
                f"Améliorer la couverture des citations (actuellement {validation['coverage_rate_percent']:.1f}%)"
            )
        
        return recommendations
```

---

## ANNEXE G : MÉTRIQUES ET STANDARDS

### TABLEAU G1 : Métriques de performance standardisées
| Métrique | Description | Cible | Méthode de calcul |
|----------|-------------|-------|-------------------|
| **Stabilité Response_ID** | Pourcentage de réponses identiques sur répétitions | 100% | `(réponses_identiques / total_répétitions) × 100` |
| **Taux d'abstention utile** | Pourcentage d'abstentions correctes sur questions sans sources | >95% | `(abstentions_correctes / questions_sans_sources) × 100` |
| **Couverture citations** | Pourcentage de sources correctement citées | 100% | `(sources_citées / total_sources) × 100` |
| **Latence moyenne** | Temps moyen de génération de réponse | <2s | `Σ(temps_réponse) / nombre_réponses` |
| **Cache hit rate** | Pourcentage de réponses servies depuis le cache | >80% | `(hits_cache / total_requêtes) × 100` |
| **Précision factuelle** | Pourcentage d'affirmations vérifiables | >99% | `(affirmations_vérifiées / total_affirmations) × 100` |

### TABLEAU G2 : Standards sectoriels d'application
| Secteur | Standards applicables | Exigences de citation | Taux hallucination cible |
|---------|----------------------|----------------------|-------------------------|
| **Santé** | HAS, OMS, guidelines médicaux | Références obligatoires aux guidelines | <0.1% |
| **Finance** | MIFID II, GDPR, réglementations bancaires | Citations des articles réglementaires | <0.01% |
| **Juridique** | Codes juridiques, jurisprudence | Références aux articles de loi | <0.05% |
| **Industrie** | ISO, CE, normes techniques | Citations des normes applicables | <0.1% |
| **Recherche** | Standards académiques, peer-review | Références bibliographiques complètes | <0.5% |

### FORMULAIRE G3 : Rapport de validation standard
```json
{
  "validation_report": {
    "metadata": {
      "report_id": "VR-20260515-001",
      "timestamp": "2026-05-15T14:30:45Z",
      "validator": "DeepSeek Deterministic Validator v2.0",
      "api_version": "2.0.0-real"
    },
    "test_configuration": {
      "dataset": "verified_mode_benchmark_v1",
      "test_cases": 10,
      "repeats_per_case": 3,
      "timeout_per_request": 30
    },
    "performance_metrics": {
      "determinism": {
        "score": 100.0,
        "passed_cases": 10,
        "total_cases": 10,
        "details": "Tous les response_id identiques sur 3 répétitions"
      },
      "abstention": {
        "score": 100.0,
        "correct_abstentions": 3,
        "total_abstention_cases": 3,
        "details": "Abstentions structurées correctes sur toutes les questions sans sources"
      },
      "citations": {
        "score": 100.0,
        "sources_covered": 15,
        "total_sources": 15,
        "details": "Toutes les sources correctement citées avec [SX]"
      },
      "latency": {
        "average_ms": 1250,
        "p95_ms": 1800,
        "p99_ms": 2200,
        "details": "Latence conforme aux exigences (<2s)"
      }
    },
    "compliance_assessment": {
      "sector_standards": {
        "healthcare": "CONFORME - Références HAS/OMS",
        "finance": "CONFORME - Citations réglementaires",
        "legal": "CONFORME - Références juridiques",
        "industry": "CONFORME - Normes techniques"
      },
      "overall_compliance": "FULLY_COMPLIANT",
      "certification_ready": true
    },
    "recommendations": [
      "Maintenir la configuration de déterminisme actuelle",
      "Documenter les procédures de validation pour audit externe",
      "Étendre le dataset de test avec des cas edge-cases"
    ],
    "attestation": {
      "validator_signature": "sha256:abc123...",
      "validation_date": "2026-05-15",
      "next_validation_due": "2026-08-15"
    }
  }
}
```

---

**Fin des annexes techniques**