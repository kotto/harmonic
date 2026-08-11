# 🏛️ ARCHITECTURE_ENTREE — L'ordre du projet KA Mobile (Capacitor)

**Le point d'entrée, la règle de source, la procédure de synchronisation — vérifié le 11/08/2026**
**Branche** : `memory-first-hybride`

---

## 1. La chaîne d'entrée (vérifiée)

```
www/index.html  (73 l.)  → REDIRECTEUR : location.href='ka_index.html'
www/ka_index.html (2912 l.) → LE VRAI SHELL de l'app (chat, optimiseur,
                              stockage, actions…) — le point d'entrée réel
www/*.js                → les modules (ka_hybrid, ka_native, vital_ka_voice,
                          harmonic_v3, ka_llm_agent, ka_server_switch)
www/sw.js               → le service worker (cache — référence ka_hcv.js)
www/manifest.json       → le PWA manifest
```

## 2. La règle d'or — LA SOURCE DE VÉRITÉ

**On édite UNIQUEMENT dans `www/`** (le `webDir` de `capacitor.config.json`).
Les copies suivantes sont **GÉNÉRÉES** — ne jamais les éditer directement
(elles seraient écrasées au prochain sync) — et **GITIGNORÉES** (seule
`www/` est suivie par git — c'est l'ordre Capacitor standard) :

| Copie | Rôle | État (11/08/2026) |
|---|---|---|
| `android/app/src/main/assets/public/` | Le bundle Android | ✅ resynchronisée (icons réintégré, orphelins cordova retirés) |
| `ios/App/App/public/` | Le bundle iOS | ✅ resynchronisée (7 fichiers réintégrés) |

## 3. La procédure (après toute modification de `www/`)

```bash
# 1 · Vérifier l'état de la synchro (le contrôle maintenable)
python scripts/check_sync.py

# 2 · Propager la source vers les copies (npx cap sync, ou la copie directe)
cp -r www/. android/app/src/main/assets/public/
cp -r www/. ios/App/App/public/

# 3 · Re-vérifier
python scripts/check_sync.py   # → « 0 divergence »
```

## 4. Les pièces manquantes — ÉTAT (les deux livrées le 11/08/2026)

| Pièce | Où | État |
|---|---|---|
| `www/ka_hcv.js` | ✅ **livrée dans `www/`** (la source — puis sync) | Le codec client : chargeur WASM honnête (état déclaré tant que `hcv_wasm.wasm` n'est pas livré par le projet HCV), décodage standard par sniff des signatures (JPEG/PNG/WebP/GIF), délégation serveur pour la compression — propagée aux copies Android/iOS, `check_sync` = 0 |
| Le 2ᵉ chemin d'entrée | ✅ **implémenté** — `ka_server/app.py` | La route `/` sert le shell de l'app (`www/ka_index.html`) avec repli JSON de santé ; la route `/<path:filename>` sert les assets de l'app (repli 404 → les routes du site restent intactes) — vérifié : `/` → app · `/ka_hcv.js` → codec · `/api/health` et `/corporation` intacts |

**Le serveur confirme** : `HCV Codec: WASM=True, Server=True (android=True, upscaler=True, pro=True)` — la chaîne complète : mémoire → commande (`hcv_compress`) → serveur (codec complet) → client (`ka_hcv.js`) → `.hcv` téléchargé. Il ne reste que le binaire WASM natif (projet HCV) pour le décodage hors formats standard.

## 5. Les fichiers du projet (inventaire)

| Fichier | Rôle |
|---|---|
| `capacitor.config.json` | webDir = www · appId com.vitalka.ka · server.url (mode distant) |
| `ka-actions/` | Le plugin agentique natif (call, sms, contacts, diskSpace, battery, openApp, listApps, deviceInfo, wifiInfo, **compress ZIP natif**) |
| `ka-actions/src/definitions.ts` | Le contrat TypeScript du plugin |
| `ka-actions/android/src/main/java/com/vitalka/ka/actions/KAActionsPlugin.java` | L'implémentation Java (361+ lignes) |

---

*Document d'ordre — FIN — la règle est une seule : www/ est la source, le sync propage, le check maintient — et ka_hcv.js viendra dans la source, pas dans les copies*
