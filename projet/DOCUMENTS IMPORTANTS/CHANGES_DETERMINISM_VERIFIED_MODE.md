# RÃ©sumÃ© des modifications (dÃ©terminisme + â€œmode vÃ©rifiÃ©â€ anti-hallucination)
Date: 2026-05-14

## Objectif
Mettre en place une diffÃ©renciation â€œmÃªme prompt â‡’ mÃªme sortieâ€ (dÃ©terminisme) et une politique â€œzÃ©ro hallucinationâ€ crÃ©dible via:
- verrouillage greedy (tempÃ©rature forcÃ©e Ã  0 cÃ´tÃ© serveur),
- cache dÃ©terministe (prompt+params â‡’ rÃ©ponse identique),
- mode vÃ©rifiÃ© (abstention structurÃ©e si pas de sources, citations si sources),
- mÃ©triques reproductibles (response_id + policy + cache_hitâ€¦).

## Fichiers modifiÃ©s
- [lm_arena_test_final.py](file:///f:/SAAS%20-%20Copie/lm_arena_test_final.py)
- [deepseek_api_real_final.py](file:///f:/SAAS%20-%20Copie/deepseek_api_real_final.py)
- [deepseek_api_deepseek_backend.py](file:///f:/SAAS%20-%20Copie/deepseek_api_deepseek_backend.py)
- [DEEPSEEK_V4_HARMONIC_FINAL.py](file:///f:/SAAS%20-%20Copie/HCV_Project/SAAS%20-%20Copie/HCV-PRO-PROJECT/DEEPSEEK_V4_HARMONIC_FINAL.py)

## 1) Client de test LM Arena
Fichier: [lm_arena_test_final.py](file:///f:/SAAS%20-%20Copie/lm_arena_test_final.py)
- Passage de `temperature: 0.7` Ã  `temperature: 0.0` dans `test_generate`, pour aligner les tests sur un dÃ©codage greedy.

## 2) API â€œRealâ€ (FastAPI) â€” verrou dÃ©terministe + mode vÃ©rifiÃ© + mÃ©triques
Fichier: [deepseek_api_real_final.py](file:///f:/SAAS%20-%20Copie/deepseek_api_real_final.py)

### DÃ©terminisme
- Valeur par dÃ©faut `temperature: 0.0` dans le modÃ¨le de requÃªte.
- Verrou serveur optionnel:
  - si `DETERMINISTIC_LOCK=true`, la tempÃ©rature est forcÃ©e Ã  `0.0` mÃªme si le client envoie autre chose.
- Cache dÃ©terministe LRU en mÃ©moire:
  - clÃ©: hash de `(mode, max_tokens, verified_mode, sources_hash, prompt)`,
  - taille contrÃ´lÃ©e par `DETERMINISTIC_CACHE_MAX_ENTRIES` (dÃ©faut 2048).
- Stabilisation du JSON retournÃ©:
  - `processing_time` est renvoyÃ© Ã  `0.0` quand le verrou dÃ©terministe est actif (sinon il varie Ã  chaque appel).

### Mode vÃ©rifiÃ© (anti-hallucination crÃ©dible)
- Ajout des champs optionnels de requÃªte:
  - `verified_mode` (bool),
  - `sources` (liste de chaÃ®nes: extraits, URLs, rÃ©fÃ©rences).
- Extraction de sources depuis le prompt (formats supportÃ©s):
  - lignes `SOURCE: ...`, `URL: ...`,
  - bloc `SOURCES:` â€¦ `END_SOURCES`.
- Politique:
  - si `verified_mode=true` et que la question semble â€œfactuelle externeâ€ et quâ€™aucune source nâ€™est fournie â‡’ abstention structurÃ©e,
  - si sources fournies â‡’ rÃ©ponse â€œcitations/quoteâ€ dÃ©terministe (pas de gÃ©nÃ©ration libre basÃ©e sur des faits non sourcÃ©s).

### MÃ©triques reproductibles
- Ajout dans la rÃ©ponse:
  - `response_id` (sha256 stable basÃ© sur prompt+params+sources+version),
  - `verified_mode`,
  - `citations` (liste structurÃ©e quand sources prÃ©sentes),
  - `metrics` (policy, cache_hit, deterministic_lock, sources_count, etc.).

## 3) API â€œDeepSeek backendâ€ â€” verrou dÃ©terministe + mode vÃ©rifiÃ© + citations
Fichier: [deepseek_api_deepseek_backend.py](file:///f:/SAAS%20-%20Copie/deepseek_api_deepseek_backend.py)

### DÃ©terminisme
- Valeur par dÃ©faut `temperature: 0.0` dans le modÃ¨le de requÃªte.
- Verrou serveur optionnel:
  - si `DETERMINISTIC_LOCK=true`, la tempÃ©rature est forcÃ©e Ã  `0.0`.
- Cache dÃ©terministe LRU en mÃ©moire, contrÃ´lÃ© par `DETERMINISTIC_CACHE_MAX_ENTRIES`.

### Mode vÃ©rifiÃ© (avec vrai backend)
- Ajout:
  - `verified_mode`, `sources` en entrÃ©e,
  - `response_id`, `citations`, `metrics` en sortie.
- Politique:
  - si `verified_mode=true` et pas de sources â‡’ abstention structurÃ©e,
  - si sources fournies â‡’ appel backend avec un message systÃ¨me qui impose:
    - rÃ©pondre uniquement Ã  partir des sources,
    - citer avec `[S1]`, `[S2]`, etc.,
    - sinon rÃ©pondre `ABSTAIN`.
  - si le modÃ¨le ne cite pas correctement â‡’ abstention structurÃ©e.

## 4) Service â€œDeepSeek Harmonic V2â€ (DEEPSEEK_V4_HARMONIC_FINAL.py)
Fichier: [DEEPSEEK_V4_HARMONIC_FINAL.py](file:///f:/SAAS%20-%20Copie/HCV_Project/SAAS%20-%20Copie/HCV-PRO-PROJECT/DEEPSEEK_V4_HARMONIC_FINAL.py)
- Ajout dâ€™un chemin â€œmode vÃ©rifiÃ©â€ au niveau de `/generate` avec:
  - `verified_mode`, `sources` en entrÃ©e,
  - `response_id`, `citations`, `metrics` en sortie,
  - cache dÃ©terministe tenant compte des sources et du mode.
- Comportement:
  - en mode vÃ©rifiÃ©: abstention si pas de sources sur questions factuelles, quote/citations si sources prÃ©sentes,
  - sinon: comportement existant (agrÃ©gation â€œharmonicâ€).

## Variables dâ€™environnement utilisÃ©es
- `DETERMINISTIC_LOCK` (dÃ©faut `true`): force `temperature=0` cÃ´tÃ© serveur.
- `DETERMINISTIC_CACHE_MAX_ENTRIES` (dÃ©faut `2048`): taille du cache dÃ©terministe.
- `VERIFIED_MODE_DEFAULT` (dÃ©faut `false`): active le mode vÃ©rifiÃ© par dÃ©faut si `true`.

## DÃ©ploiement AWS observÃ© (important)
Sur lâ€™instance actuelle (IP publique vue: `__EC2_IP__`), le service systemd actif dÃ©tectÃ© est:
- `deepseek-api.service` (pas `deepseek-harmonic-v2`),
- il exÃ©cute `/opt/deepseek/api.py`,
- lâ€™utilisateur SSH fonctionnel avec la clÃ© `deepseek_ec2` est `ec2-user` (pas `ubuntu`).

## SÃ©curitÃ© (point dâ€™attention)
Un fichier dâ€™environnement systemd a Ã©tÃ© observÃ© sur lâ€™instance:
- `/etc/deepseek-api.env` (chargÃ© par `deepseek-api.service`)
Il contient une variable `BACKEND_API_KEY`.
- Ne pas partager / committer cette clÃ©.
- Recommandation: rotation de clÃ© + permissions IAM minimales + accÃ¨s SSH restreint (SG 22).

