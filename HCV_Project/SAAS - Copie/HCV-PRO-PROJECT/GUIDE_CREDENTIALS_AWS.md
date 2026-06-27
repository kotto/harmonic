# 📋 GUIDE OBTENIR SES CREDENTIALS AWS

---

## ✅ ÉTAPES POUR OBTENIR VOTRE ACCESS KEY & SECRET KEY

### 🔹 1. Connectez vous sur la Console AWS
👉 https://console.aws.amazon.com/

---

### 🔹 2. Cliquez sur votre nom en haut à droite
![](https://docs.aws.amazon.com/fr_fr/IAM/latest/UserGuide/images/security-credentials-menu.png)

---

### 🔹 3. Sélectionnez **"Identifiants de sécurité"**

---

### 🔹 4. Descendez jusqu'à la section **"Clés d'accès (clé d'accès et clé d'accès secrète)"**

---

### 🔹 5. Cliquez sur **"Créer une clé d'accès"**
  ✅ Cochez la case confirmation
  ✅ Cliquez sur **"Créer une clé d'accès"**

---

### 🔹 6. TÉLÉCHARGEZ VOTRE FICHIER .CSV
⚠️ **IMPORTANT**: Vous ne pourrez PLUS VOIR LA CLÉ SECRÈTE APRÈS CETTE PAGE. Téléchargez impérativement le fichier CSV.

---

## 🎯 Ce que vous allez obtenir:
| Valeur | Exemple |
|--------|---------|
| `Access Key ID` | `AKIA5XXXXXXXXXXXXXXX` |
| `Secret Access Key` | `kF8z9XcVbN................................` |

---

## ⚡ Une fois que vous avez ces 2 valeurs:

Exécutez simplement cette commande:
```bash
aws configure
```

Et entrez les valeurs:
```
AWS Access Key ID [None]: VOTRE_ACCESS_KEY_ICI
AWS Secret Access Key [None]: VOTRE_SECRET_KEY_ICI
Default region name [None]: eu-west-3
Default output format [None]: json
```

---

## 🚀 Puis lancer le déploiement:
```bash
cd HCV-PRO-PROJECT
./AWS_DEPLOY_NOW.sh
```

✅ Déploiement automatique complet en ~12 minutes.