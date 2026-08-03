# 🏢 FICHE PRODUIT — KA Enterprise

## En une phrase
> L'IA de vos données privées : elle ne répond que sur ce que vous lui avez
> donné, elle vous le dit quand elle ne sait pas, et elle vous livre vos
> données en Excel et en documents.

## Les trois promesses

1. **Ancrée** — chaque réponse est issue de VOS documents ingérés, avec
   confiance affichée et sources citées. Jamais de contenu inventé.
2. **Souveraine** — tout tourne sur votre VPS, vos données ne quittent
   jamais votre infrastructure. Chiffrement AES-256 au repos, audit trail,
   RBAC, étanchéité par département.
3. **Calibrée** — quand la résonance est insuffisante, l'IA REFUSE et vous
   le dit (« Je ne trouve pas cette information ») — au lieu d'inventer.
   Et elle s'enrichit automatiquement de vos questions (auto-apprentissage).

## Ce qu'elle fait

| Besoin | Exemple | Résultat |
|---|---|---|
| Répondre sur vos données | « combien de clients actifs ? » | Comptage + sources |
| Analyser | « chiffre d'affaires total ? » | Total, moyenne, min, max |
| Lister | « liste des factures en retard » | Tableau + filtre automatique |
| Livrer | « exporte les clients » | Excel (.xlsx) : feuille Données + Résumé |
| Rédiger | « email aux clients en retard » | Texte structuré, français corrigé, .docx |
| Synthétiser | « résume le département » | Prose connectée + provenance |
| S'intégrer | assistants, IDE, n8n | Agents MCP (15 outils, 5 rôles) |
| Apprendre | questions sans réponse | Enrichissement automatique en arrière-plan |

## Comparatif — l'argument décisif

| | **KA Enterprise** | LLM généralistes (ChatGPT…) | Copilot + documents |
|---|---|---|---|
| Réponse hors de vos données | **Refus calibré** | Réponse plausible — souvent fausse | Réponse mélangée au web |
| Données | **Restent chez vous (VPS)** | Partent chez le fournisseur | Partent chez le fournisseur |
| Sources citées | ✓ (confiance + sources) | rarement | non |
| Coût | **Forfait 49 €/mois, 0 GPU** | par token / par utilisateur | par utilisateur |
| Inférence | CPU seul, déterministe | GPU, coûteux | GPU |
| Étanchéité interne | ✓ par département | non | non |
| Livrables Excel/documents | ✓ natifs | via plugins | limité |
| Auto-apprentissage sur vos questions | ✓ | non | non |

## Objections → réponses

| Objection | Réponse |
|---|---|
| « ChatGPT fait pareil » | « Posez-lui une question hors de vos documents : il inventera. Nous, nous refusons. Lequel pour votre conformité ? » |
| « On a déjà Copilot » | « Vos données partent chez Microsoft et ses réponses mélangent vos docs au web. Ici : rien ne sort de votre VPS, et chaque réponse est sourcée. » |
| « L'IA ne connaît pas notre métier » | « Elle connaît ce que VOUS lui donnez — votre savoir, pas le web. » |
| « La qualité des réponses ? » | « Essayez : posez vos vraies questions sur vos vrais documents, en démo, maintenant. » |
| « Trop cher » | « Moins cher qu'un abonnement par utilisateur chez les autres, et votre marge ne dépend pas du volume de questions. » |
| « On a déjà un outil » | « Connectez-le via MCP : votre assistant existant interroge vos hologrammes. » |

## Spécifications techniques

- **0 LLM, 0 GPU** : encodage ondulatoire (ψ), attention de phase (HWAT),
  correcteur français déterministe — reproductible, auditable.
- **Gate anti-hallucination** : résonance > seuil pour répondre, sinon refus
  calibré + chaînon D (complétion en arrière-plan).
- **VPS requis** : Ubuntu 22.04+, 2 vCPU / 4 Go RAM, 20 Go — installation
  en 2 minutes (`deploy_vps.sh`), Docker.
- **Sécurité** : SSO + clés API, RBAC (5 rôles), AES-256 au repos, audit
  SHA256 horodaté, rate limiting, étanchéité inter-départements.
- **Intégrations** : API REST documentée (OpenAPI), MCP (stdio + HTTP),
  Excel/CSV/DOCX/TXT.
- **Onboarding** : décrivez votre environnement → hologrammes créés avec
  contenu initial → posez vos questions immédiatement.
