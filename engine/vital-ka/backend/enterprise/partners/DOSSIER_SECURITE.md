# 🔐 KA Enterprise — Dossier de sécurité (audit hébergeur / partenaire)

Réponses structurées au questionnaire d'audit d'un hébergeur ou d'un
acheteur entreprise. Version 1.0 — KA Enterprise v4.

---

## 1 · Architecture et hébergement

**Où tourne KA Enterprise ?**
Sur le VPS du CLIENT (Ubuntu 22.04+, Docker). L'hébergeur fournit
l'infrastructure ; les données applicatives sont sur le volume persistant
du VPS client (`~/ka-enterprise-data`). Aucune donnée client n'est hébergée
chez l'éditeur.

**Dépendances d'exécution** : Python 3.11, Flask, NumPy, openpyxl,
python-docx. **Aucun GPU, aucun appel LLM externe** — l'inférence est
ondulatoire, locale et déterministe (CPU seul). Aucune donnée ne transite
par un service tiers (pas de cloud IA, pas de télémétrie).

**Ports exposés** : 8767 (HTTPS en production via reverse proxy Caddy/nginx
recommandé). SSH 22 pour l'administration.

## 2 · Données et chiffrement

| Question | Réponse |
|---|---|
| Chiffrement au repos | **AES-256-CBC** — hologrammes et faits chiffrés (module HologramEncryption) |
| Chiffrement en transit | TLS 1.2+ (terminaison reverse proxy) ; API authentifiée par clé |
| Quelles données sont stockées ? | Textes ingérés (documents du client), vecteurs ψ, journal d'audit, clés API |
| Où ? | Volume persistant du VPS client — **jamais chez l'éditeur** |
| Sauvegarde | `tar` du volume (`~/ka-enterprise-data`) — guide fourni, cron proposé |
| Effacement | Suppression du tenant / du volume = effacement complet (RGPD : droit à l'oubli garanti par le client) |

## 3 · Authentification et contrôle d'accès

- **SSO** : jetons Bearer (intégration SAML/OIDC côté hébergeur possible).
- **Clés API** : une par tenant, hachées en stock, révocables.
- **RBAC** : 5 rôles (admin, manager, user, auditor, readonly) — permissions
  par ressource (`tenant:*`, `department:*`, `hologram:*`, `audit:*`, `user:*`).
- **Rate limiting** par tenant (100 req/min par défaut, configurable).
- **Étanchéité inter-départements** : chaque département (hologramme) est
  isolé par un offset de phase ; une question posée à un département ne peut
  pas puiser le savoir d'un autre. Vérifié par `verify_seal` (test
  d'étanchéité exposé en API).

## 4 · Journalisation et audit

- **Audit trail obligatoire** : chaque requête API (méthode, chemin, tenant,
  utilisateur, horodatage, confiance, réponse hashée SHA256).
- Journal d'audit conservé dans le volume du client (exportable).
- Réponse `response_id` (SHA256) traçable de bout en bout.

## 5 · Intégrité des réponses (anti-hallucination)

- **Gate de résonance** : une réponse n'est servie que si la résonance
  (score ψ + overlap lexical) dépasse un seuil ; sinon **refus calibré**
  (« Je ne trouve pas cette information »).
- Chaque réponse porte : confiance, sources citées, incertitude admise.
- **Déterministe** : mêmes données + même question = même réponse
  (aucun modèle stochastique). Auditabilité totale.

## 6 · Vulnérabilités et durcissement

- Dépendances minimales et connues (Flask, NumPy, openpyxl, python-docx) ;
  aucune librairie LLM embarquée.
- Entrées validées : parsing JSON strict, taille limitée des ingests,
  échappement HTML systématique dans l'interface.
- Conteneur : exécution non-root recommandée, image `python:3.11-slim`.
- Mises à jour : image reconstruite à chaque version ; `deploy_vps.sh`
  remplace le conteneur en conservant les données.

## 7 · Conformité

- **RGPD** : le client est responsable du traitement (il héberge), l'éditeur
  n'accède à aucune donnée — DPA simplifié.
- **Souveraineté** : localisation choisie par le client (datacenter de son
  hébergeur), aucune sortie de l'UE par défaut.
- Aucun transfert vers des services IA tiers (pas de traitement externe).

## 8 · Reprise d'activité

- Sauvegarde du volume → restauration = recréer le conteneur + remonter le
  volume (procédure documentée dans README_DEPLOIEMENT_VPS.md).
- Redémarrage automatique du conteneur (`restart: unless-stopped`).
- Healthcheck Docker exposé (`/api/enterprise/info`).

---

*Contact sécurité : contact@ka-enterprise.fr — réponse sous 48 h.*
