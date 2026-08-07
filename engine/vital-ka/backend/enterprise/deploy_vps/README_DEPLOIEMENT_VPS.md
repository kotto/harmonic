# 📦 KA Enterprise — Guide de déploiement sur votre VPS

KA Enterprise est une **IA d'entreprise harmonique** : votre environnement
(secteur, activités, métiers) est décrit une fois, et le système crée les
**hologrammes** (départements de savoir) correspondants, chacun capable de
répondre **sans hallucination** (gate de résonance), en **CPU uniquement**.

Ce guide installe l'application sur votre propre VPS : **vos données, vos
hologrammes et vos clés restent chez vous**.

---

## 1 · Prérequis

| Ressource | Minimum | Confort |
|---|---|---|
| VPS | Ubuntu 22.04+ | Debian 12 |
| CPU | 2 vCPU | 4 vCPU |
| RAM | 4 Go | 8 Go |
| Stockage | 20 Go | 50 Go |
| GPU | **Aucun** (CPU pur) | — |

Connexion SSH au VPS :

```bash
ssh root@VOTRE_VPS
```

## 2 · Installation de Docker

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # puis reconnectez-vous (exit + ssh)
```

Vérifier : `docker --version`

## 3 · Copie du dossier de déploiement

Depuis votre machine locale (là où se trouve le code KA Enterprise) :

```bash
scp -r vital-ka/backend/enterprise/deploy_vps root@VOTRE_VPS:/opt/ka-enterprise
```

## 4 · Installation (2 minutes)

```bash
cd /opt/ka-enterprise
bash deploy_vps.sh
```

Le script :
1. construit l'image Docker (`python:3.11-slim`, numpy + flask) ;
2. démarre le conteneur sur le port **8767** ;
3. monte le volume persistant `~/ka-enterprise-data`.

**Alternative avec docker compose :**

```bash
docker compose -f deploy_vps/docker-compose.yml up -d --build
```

## 5 · Ouverture du port

```bash
sudo ufw allow 8767/tcp
```

## 6 · Utilisation

| Page | URL |
|---|---|
| 🌱 Portail onboarding (créer son environnement) | `http://VOTRE_VPS:8767/onboard` |
| 📊 Dashboard admin (avec clé API) | `http://VOTRE_VPS:8767/admin` |
| 📖 Documentation API | `http://VOTRE_VPS:8767/docs` |

**Premier onboarding :**

1. Nom de l'entreprise, secteur, email administrateur ;
2. **Description de l'environnement** (ex. *« clinique privée avec pharmacie
   et laboratoires d'analyses »*) ;
3. KA Enterprise détecte les domaines et **propose les hologrammes** —
   décochez ce qui ne vous concerne pas ;
4. Création : chaque hologramme reçoit un **seed initial** (Wikipedia si le
   réseau est disponible, sinon corpus hors-ligne) — il répond **dès la
   création**, avant même l'ingestion de vos documents ;
5. Une **clé API** est affichée : collez-la dans le dashboard admin
   (champ « API Key » en haut à droite) pour administrer votre tenant.

## 7 · Enrichir avec vos documents

Dans le dashboard admin, onglet **Ingestion** : collez un texte ou déposez
un fichier (PDF, DOCX, XLSX, CSV) dans le département cible. Chaque
ingestion est versionnée, auditée et chiffrée (AES-256 au repos).

## 7bis · Vos données privées → Excel & documents (livrables)

L'IA répond à **toute question sur vos données privées** et les **formate
en livrables** (onglet « 📊 Données & Docs » du dashboard) :

| Vous demandez… | Elle produit |
|---|---|
| « liste des clients » | Tableau Excel (.xlsx) : en-têtes, filtre automatique, colonnes |
| « chiffre d'affaires total » | Feuille **Résumé** avec indicateurs (total, moyenne, min, max, comptage) |
| « combien de factures en attente ? » | Comptage + lignes filtrées |
| « prépare un email sur la situation des clients » | **Email** rédigé (objet, corps, politesse) — .docx ou .txt |
| « rédige un rapport sur les ventes » | **Rapport** structuré (intro, éléments, conclusion) |
| « fais le compte-rendu de la réunion » | **Compte-rendu** (points, décisions, prochaines étapes) |

Tout est généré à partir de **vos seules données** (jamais d'hallucination,
gate de résonance), en français corrigé, **0 LLM / 0 GPU**.

## 7ter · Agents spécialisés MCP (assistants, IDE, automatisations)

KA Enterprise expose ses hologrammes au **Model Context Protocol** :
vos assistants (Claude Desktop, Cursor, n8n…) peuvent appeler les
compétences de votre IA — Q&A privée, tableaux Excel, textes rédigés,
conformité, onboarding — via 5 agents spécialisés (Data, Rédaction,
Conformité, Onboarding, Support) qui **concourent** sur chaque question.

- Point d'entrée HTTP : `POST http://VOTRE_VPS:8767/mcp` (clé API du tenant)
- Transport local : `python mcp/mcp_server_stdio.py` (KA_API_KEY en env)
- Documentation complète : `mcp/README_MCP.md`
- Démo : `python mcp/mcp_client_demo.py --mode http --base http://VOTRE_VPS:8767 --api-key <clé>`

## 8 · Sécurité

- **SSO + API Keys** : chaque tenant possède une clé unique ;
- **RBAC** : 5 rôles (admin, manager, utilisateur, auditeur, lecture seule) ;
- **Rate limiting** par tenant (100 requêtes/min par défaut) ;
- **Audit trail** obligatoire, horodaté et haché (SHA256) ;
- **Étanchéité inter-départements** : un hologramme ne peut pas répondre
  depuis le savoir d'un autre.

## 9 · Sauvegarde des données

Tout vit dans `~/ka-enterprise-data`. Sauvegardez ce dossier :

```bash
# Sauvegarde locale
tar czf ka-backup-$(date +%F).tar.gz ~/ka-enterprise-data

# Automatisation (cron) : toutes les nuits à 2h
0 2 * * * tar czf /root/backups/ka-$(date +\%F).tar.gz -C ~ ka-enterprise-data
```

## 10 · Administration courante

```bash
docker logs -f ka-enterprise      # journaux
docker stop ka-enterprise         # arrêt
docker start ka-enterprise        # redémarrage
docker rm -f ka-enterprise        # suppression (les données restent)
```

**Mise à jour** : copiez le nouveau code, relancez `bash deploy_vps.sh` —
l'ancien conteneur est remplacé, **les données sont conservées**.

## 11 · Recommandations production

- Terminaison TLS : reverse proxy **Caddy** ou **nginx** devant le port 8767 ;
- Restreignez le port 8767 au pare-feu si le proxy est sur la même machine ;
- Augmentez `--restart unless-stopped` est déjà configuré (redémarrage
  automatique au reboot du VPS).

---

*KA Enterprise v4 — IA harmonique, zéro hallucination, zéro GPU.*
