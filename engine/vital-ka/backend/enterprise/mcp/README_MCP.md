# 🤖 KA Enterprise — Agents spécialisés MCP

KA Enterprise expose ses hologrammes (départements de savoir) au **Model
Context Protocol (MCP)** : vos assistants, IDE et automatisations peuvent
appeler les compétences de votre IA ondulatoire — Q&A sur les données
privées, tableaux Excel, textes rédigés, conformité, onboarding — **sans
LLM, sans GPU, sans que vos données quittent votre VPS**.

## Les agents spécialisés (le « concours »)

Une question entrante fait **concourir les agents** : chacun score les
mots-clés de sa spécialité, le meilleur score exécute (support en fallback).
Le routage est déterministe et auditable.

| Agent | Rôle | Exemples de questions |
|---|---|---|
| 🧠 **Agent Data** | listes, comptages, totaux, moyennes, Excel | « liste des clients », « chiffre d'affaires total » |
| ✍️ **Agent Rédaction** | emails, rapports, comptes-rendus, lettres, notes | « rédige un email sur la situation », « fais le compte-rendu » |
| 🕵️ **Agent Conformité** | audit, journal, étanchéité, couverture | « donne les indicateurs », « vérifie l'audit », « couverture du département » |
| 🌱 **Agent Onboarding** | analyse d'environnement, création d'hologrammes | « analyse mon environnement », « crée un nouveau département » |
| 💬 **Agent Support** | toute question sur le savoir des départements | « quelle est la procédure de paiement ? » |

Chaque réponse passe par le **gate anti-hallucination** (confiance + sources)
et, en cas d'incertitude, déclenche le **chaînon D** : la question est
enregistrée pour enrichissement automatique en arrière-plan.

## Les 15 outils exposés

| Outil | Compétence |
|---|---|
| `agent_handle` | 🏆 concours des agents — une question, l'agent le plus pertinent répond |
| `ask_department` | Q&A sur le savoir d'un département (gate + chaînon D) |
| `ask_tenant` | Q&A sur tous les départements (consensus inter-hologrammes) |
| `query_data` | tableau (colonnes/lignes) + agrégats (compte, somme, moyenne, min, max) |
| `export_excel` | fichier Excel (.xlsx Données+Résumé) ou CSV — retourné en base64 |
| `compose_document` | email, rapport, compte_rendu, lettre, note — français corrigé |
| `summarize_department` | synthèse du savoir d'un département |
| `ingest_text` | ingestion d'un texte dans un département |
| `list_departments` | départements (hologrammes) du tenant |
| `department_coverage` | complétude par facettes + facettes manquantes |
| `check_seal` | étanchéité entre deux départements |
| `audit_recent` | journal d'audit du tenant |
| `dashboard` | indicateurs du tenant |
| `analyze_environment` | analyse d'environnement (agent Onboarding) |
| `create_environment` | création d'un environnement complet (tenant + hologrammes) |

## Connexion

### 1. Streamable HTTP (VPS, recommandé)

Le serveur KA Enterprise expose `/mcp` (POST JSON-RPC, authentifié par la
clé API du tenant) :

```
POST http://VOTRE_VPS:8767/mcp
X-API-Key: <clé API du tenant>        # ou Authorization: Bearer <token SSO>
Content-Type: application/json
Accept: application/json, text/event-stream
```

### 2. Stdio (local, même machine)

```bash
KA_API_KEY=<clé du tenant> python mcp_server_stdio.py
```

Configuration **Claude Desktop** (`claude_desktop_config.json`) :

```json
{ "mcpServers": {
    "ka-enterprise": {
      "command": "python",
      "args": ["/opt/ka-enterprise/mcp/mcp_server_stdio.py"],
      "env": { "KA_API_KEY": "votre_clé_tenant" } } } }
```

Configuration **Cursor** (`.cursor/mcp.json`) :

```json
{ "mcpServers": {
    "ka-enterprise": {
      "command": "python",
      "args": ["/opt/ka-enterprise/mcp/mcp_server_stdio.py"],
      "env": { "KA_API_KEY": "votre_clé_tenant" } } } }
```

## Exemple de dialogue (client de démonstration)

```bash
# stdio — lance le serveur local et dialogue
python mcp_client_demo.py --mode stdio --api-key <clé>

# http — se connecte à un serveur distant
python mcp_client_demo.py --mode http --base http://VOTRE_VPS:8767 \
    --api-key <clé>
```

Sortie :

```
── 3. CONCOURS : agent_handle « liste des clients » ────────
   agent gagnant : 🧠 Agent Data · 3 lignes
── 4. CONCOURS : « rédige un email sur la situation » ──────
   agent gagnant : ✍️ Agent Rédaction · format email · 5 faits
── 5. ask_department direct (gate + chaînon D) ─────────────
   … confiance 0.0 · chaînon D: True
```

Appel MCP brut (JSON-RPC) :

```json
{ "jsonrpc": "2.0", "id": 1, "method": "tools/call",
  "params": { "name": "agent_handle",
              "arguments": { "question": "combien de clients avons-nous ?",
                             "department_id": "dep_xxxx" } } }
```

Réponse (extrait) :

```json
{ "result": { "content": [
    { "type": "text",
      "text": "{\"agent\": \"data\", \"agent_nom\": \"🧠 Agent Data\", \"count\": 5, \"aggregates\": [{\"operation\": \"compte\", \"libelle\": \"Nombre de lignes\", \"valeur\": 5}]}" } ],
  "isError": false } }
```

## Catalogue des agents (pour vos clients)

```
GET /mcp/agents?question=<une question>     # avec X-API-Key
```

Retourne les 5 agents + l'agent gagnant du routage pour la question donnée.

## Sécurité

- **Authentification** : clé API du tenant (`X-API-Key`) ou SSO (`Bearer`).
- **RBAC** : les utilisateurs SSO voient leurs départements autorisés.
- **Étanchéité** : un outil ne peut jamais accéder au savoir d'un autre
  tenant (vérification d'appartenance sur chaque appel).
- **Audit** : chaque appel MCP passe par le middleware d'audit du serveur.
- **0 LLM / 0 GPU** : le protocole est un transport ; toute la logique reste
  ondulatoire et déterministe.
