"""
KA Server — Hugging Face Specializer
=====================================
Crée des hologrammes à la volée en utilisant les APIs Hugging Face :
- 🤗 Datasets API : trouve des datasets pertinents pour le domaine
- 🤗 Inference API : génère des triplets de connaissance (optionnel)

DNS note : api-inference.huggingface.co peut ne pas résoudre sur tous les réseaux.
Le specializer fonctionne au minimum avec l'API Datasets.

Utilisation :
    POST /api/specialize  { "domain": "biologie marine", "mode": "huggingface" }
"""

import logging
import re
import json
import requests
from typing import Optional, List, Dict, Any
from urllib.parse import quote

log = logging.getLogger(__name__)

HF_DATASETS_API = "https://huggingface.co/api/datasets"
HF_INFERENCE_API = "https://api-inference.huggingface.co/models"

# Modèles pour génération de faits (si inference API dispo)
HF_MODELS = [
    "google/flan-t5-base",
    "google/flan-t5-small",
    "HuggingFaceH4/zephyr-7b-beta",
]

_dataset_cache = {}
_inference_api_available = None  # None = pas encore testé


def _check_inference_api() -> bool:
    """Vérifie si l'Inference API est accessible (DNS + connectivité)."""
    global _inference_api_available
    if _inference_api_available is not None:
        return _inference_api_available
    
    try:
        # Test rapide DNS + connexion
        resp = requests.head("https://api-inference.huggingface.co", timeout=5, allow_redirects=True)
        _inference_api_available = resp.status_code < 500
        if _inference_api_available:
            log.info("✅ HF Inference API accessible")
        else:
            log.warning("⚠️ HF Inference API status: %s", resp.status_code)
    except Exception as e:
        log.warning("⚠️ HF Inference API non accessible: %s", str(e).split(':')[0])
        _inference_api_available = False
    
    return _inference_api_available


def _translate_domain(domain: str) -> List[str]:
    """Liste des termes de recherche (FR + EN)."""
    translations = {
        # Sciences
        'biologie': 'biology', 'biologie marine': 'marine biology',
        'physique': 'physics', 'chimie': 'chemistry',
        'médecine': 'medicine', 'santé': 'health',
        'cardiologie': 'cardiology', 'neurologie': 'neurology',
        'génétique': 'genetics', 'biologie moléculaire': 'molecular biology',
        'écologie': 'ecology', 'environnement': 'environment',
        'astronomie': 'astronomy', 'astrophysique': 'astrophysics',
        'géologie': 'geology', 'océanographie': 'oceanography',
        'botanique': 'botany', 'zoologie': 'zoology',
        # Tech
        'programmation': 'programming', 'python': 'python',
        'javascript': 'javascript', 'machine learning': 'machine learning',
        'intelligence artificielle': 'artificial intelligence',
        'deep learning': 'deep learning',
        'réseaux': 'networking', 'cybersécurité': 'cybersecurity',
        'blockchain': 'blockchain',
        # Sciences sociales
        'économie': 'economics', 'droit': 'law',
        'psychologie': 'psychology', 'sociologie': 'sociology',
        'philosophie': 'philosophy', 'histoire': 'history',
        'linguistique': 'linguistics',
    }
    
    domain_lower = domain.lower().strip()
    terms = [domain_lower]
    
    # Traduction directe
    if domain_lower in translations:
        terms.append(translations[domain_lower])
    
    # Mots-clés individuels
    for word in domain_lower.split():
        if word in translations:
            terms.append(translations[word])
    
    # Version sans accents
    import unicodedata
    ascii_domain = unicodedata.normalize('NFKD', domain_lower).encode('ascii', 'ignore').decode('ascii').strip()
    if ascii_domain != domain_lower and ascii_domain:
        terms.append(ascii_domain)
    
    return list(set(terms))


def _search_hf_datasets(domain: str, max_results: int = 5) -> List[Dict]:
    """Interroge l'API Datasets de HF en FR et EN."""
    cache_key = domain.lower().strip()
    if cache_key in _dataset_cache:
        return _dataset_cache[cache_key]

    search_terms = _translate_domain(domain)
    all_datasets = []
    seen_ids = set()

    for term in search_terms:
        if len(seen_ids) >= max_results * 2:  # assez de candidats
            break
        try:
            url = f"{HF_DATASETS_API}?search={quote(term)}&sort=downloads&direction=-1"
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                continue

            results = resp.json()
            if not isinstance(results, list):
                results = results.get('data', [])

            for ds in results:
                ds_id = ds.get('id', ds.get('name', ''))
                if ds_id and ds_id not in seen_ids:
                    seen_ids.add(ds_id)
                    all_datasets.append(ds)

        except Exception as e:
            log.warning(f"Search error for '{term}': {e}")

    log.info(f"📦 HF Datasets: {len(all_datasets)} trouvés pour '{domain}' "
             f"(termes: {search_terms})")

    # Enrichir les meilleurs datasets avec leur description
    enriched = []
    for ds in all_datasets[:max_results]:
        ds_id = ds.get('id', '')
        downloads = ds.get('downloads', 0)
        description = ds.get('description', '') or ds.get('cardData', {}).get('description', '')
        tags = ds.get('tags', []) or ds.get('cardData', {}).get('tags', [])
        likes = ds.get('likes', 0)

        # Récupérer les détails si description manquante
        if not description and ds_id:
            try:
                detail = requests.get(f"{HF_DATASETS_API}/{quote(ds_id)}", timeout=10).json()
                description = detail.get('description', '') or detail.get('cardData', {}).get('description', '')
                tags = detail.get('tags', []) or []
            except Exception:
                pass

        enriched.append({
            'id': ds_id,
            'description': (description or '')[:500],
            'downloads': downloads or 0,
            'tags': tags[:10],
            'likes': likes or 0,
            'url': f"https://huggingface.co/datasets/{ds_id}" if ds_id else '',
        })

    _dataset_cache[cache_key] = enriched
    return enriched


def _dataset_to_facts(datasets: List[Dict]) -> List[tuple]:
    """Convertit les datasets en faits de connaissance riches."""
    facts = []
    for ds in datasets:
        ds_id = ds.get('id', '').lower().replace(' ', '_')
        
        # Fait : source disponible
        if ds.get('url'):
            facts.append((ds_id, 'est_disponible_sur', ds['url'], 'huggingface', 0.95))
        
        # Fait : description (phrase-clé)
        if ds.get('description'):
            desc = ds['description'].replace('\n', ' ').strip()
            # Extraire les phrases informatives
            sentences = [s.strip() for s in re.split(r'[.!?\n]+', desc) if len(s.strip()) > 20]
            for s in sentences[:3]:
                facts.append((ds_id, 'concerne', s[:300], 'huggingface', 0.8))
        
        # Fait : tags
        for tag in ds.get('tags', [])[:5]:
            if tag and not tag.startswith('_'):  # ignorer tags techniques
                facts.append((ds_id, 'est_taggé', tag, 'huggingface', 0.7))
        
        # Fait : métrique d'utilité
        if ds.get('downloads', 0) > 100:
            facts.append((ds_id, 'a_plus_de', '100_downloads', 'huggingface', 0.9))
    
    return facts


def _infer_facts(domain: str) -> List[tuple]:
    """Génère des triplets via Inference API (si accessible)."""
    if not _check_inference_api():
        log.info("⏭️ Inference API non accessible, skip")
        return []

    facts = []
    english_domain = _translate_domain(domain)[-1]  # dernier terme = EN

    for model in HF_MODELS:
        if facts:
            break
        try:
            prompt = (
                f"Generate 10 factual statements about \"{english_domain}\". "
                "Each on its own line, format: (subject | predicate | object | confidence 0-1)\n"
                f"Example: ({english_domain.replace(' ','_')} | is_a | scientific_field | 0.95)\n"
            )
            resp = requests.post(
                f"{HF_INFERENCE_API}/{model}",
                json={"inputs": prompt, "parameters": {"max_new_tokens": 500, "temperature": 0.3}},
                timeout=30,
            )
            if resp.status_code != 200:
                continue

            text = resp.json()
            if isinstance(text, list) and text:
                if isinstance(text[0], dict) and 'generated_text' in text[0]:
                    text = text[0]['generated_text']
                elif isinstance(text[0], str):
                    text = text[0]
            text = str(text)

            for line in text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                match = re.match(r'\(([^|]+)\|([^|]+)\|([^|]+)(?:\|([^)]+))?\)', line)
                if match:
                    subj = match.group(1).strip()
                    pred = match.group(2).strip()
                    obj = match.group(3).strip()
                    try:
                        conf = min(float(match.group(4).strip()), 1.0) if match.group(4) else 0.8
                    except ValueError:
                        conf = 0.8
                    if subj and pred and obj:
                        facts.append((subj, pred, obj, 'huggingface', conf))

            if facts:
                log.info(f"🤖 {model}: {len(facts)} faits inférés")

        except Exception as e:
            log.debug(f"Inference {model} error: {e}")
            continue

    return facts


def _build_domain_facts(domain: str, datasets: List[Dict]) -> List[tuple]:
    """
    Construit un ensemble riche de faits à partir des datasets trouvés.
    Combine métadonnées + contenu textuel pour créer un hologramme utile.
    """
    domain_clean = domain.lower().replace(' ', '_')
    facts = []

    # Si des datasets ont été trouvés
    if datasets:
        facts.append((domain_clean, 'a_des_ressources_sur', 'Hugging_Face', 'huggingface', 0.95))
        facts.append((domain_clean, 'nombre_datasets_disponibles', str(len(datasets)), 'huggingface', 0.9))
        facts.extend(_dataset_to_facts(datasets))
        
        # Générer des faits de synthèse à partir des descriptions
        all_tags = []
        all_descriptions = []
        for ds in datasets:
            if ds.get('tags'):
                all_tags.extend(ds['tags'])
            if ds.get('description'):
                all_descriptions.append(ds['description'])
        
        # Tags les plus fréquents
        from collections import Counter
        if all_tags:
            top_tags = [t for t, _ in Counter(all_tags).most_common(5) if t and not t.startswith('_')]
            for tag in top_tags[:3]:
                facts.append((domain_clean, 'concepts_liés', tag, 'huggingface', 0.7))
        
        # Phrases-clés des descriptions
        if all_descriptions:
            combined = ' '.join(all_descriptions)
            sentences = [s.strip() for s in re.split(r'[.!?\n]+', combined) if len(s.strip()) > 30]
            for s in sentences[:3]:
                facts.append((domain_clean, 'connaissance_extraite', s[:300], 'huggingface', 0.7))
        
        # Dataset le plus populaire
        best_ds = max(datasets, key=lambda d: d.get('downloads', 0))
        if best_ds.get('id'):
            facts.append((domain_clean, 'dataset_plus_utilisé', best_ds['id'], 'huggingface', 0.85))
    
    # Faits génériques utiles
    english = _translate_domain(domain)[-1] if len(_translate_domain(domain)) > 1 else domain
    facts.extend([
        (domain_clean, 'domaine', english, 'huggingface', 0.9),
        (domain_clean, 'recherche_disponible_sur', 'Hugging_Face', 'huggingface', 0.8),
    ])
    
    return facts


def specialize_with_huggingface(domain: str) -> Dict[str, Any]:
    """
    Spécialisation complète via Hugging Face.
    
    Pipeline :
    1. Recherche datasets HF (FR + EN)
    2. Enrichissement avec descriptions
    3. Optionnel : Inference API pour faits supplémentaires
    4. Construction du bundle de faits
    
    Args:
        domain: Domaine à spécialiser (ex: 'biologie marine', 'python')
    
    Returns:
        Dict avec faits, sources, statistiques
    """
    log.info(f"🧠 HF Specialize: '{domain}'")
    
    # 1. Datasets
    datasets = _search_hf_datasets(domain)
    
    # 2. Construire les faits
    facts = _build_domain_facts(domain, datasets)
    
    # 3. Inference API (si dispo)
    try:
        inferred = _infer_facts(domain)
        facts.extend(inferred)
    except Exception as e:
        log.debug(f"Inference optionnelle échouée: {e}")
    
    # 4. Sources
    sources = [ds['url'] for ds in datasets if ds.get('url')]
    if not sources:
        english_term = _translate_domain(domain)[-1]
        sources.append(f"https://huggingface.co/datasets?search={quote(english_term)}")
    
    # 5. Stats
    datasets_count = len(datasets)
    total_facts = len(facts)
    has_datasets = datasets_count > 0
    has_inference = bool([f for f in facts if f[3] == 'huggingface'])
    
    msg = (
        f"Hologramme '{domain}' créé avec {total_facts} faits"
        f" ({datasets_count} datasets HF"
        + (", + inference IA" if has_inference else "")
        + ")"
    )
    
    result = {
        'success': True,
        'domain': domain,
        'facts': facts,
        'sources': sources,
        'fact_count': total_facts,
        'datasets_found': datasets_count,
        'method': 'huggingface',
        'source_name': 'Hugging Face',
        'hologram_id': domain.lower().replace(' ', '_'),
        'message': msg,
    }
    
    log.info(f"✅ HF Specialize '{domain}': {total_facts} faits, {datasets_count} datasets")
    return result