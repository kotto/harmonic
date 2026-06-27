# 🔍 GUIDE LOCALISATION EXACTE UTILISATEUR IAM

## 📍 OÙ TROUVER LES OPTIONS PRÉCISES

### 🎯 **ACCÈS UTILISATEUR IAM**

1. **CONSOLE AWS** → **IAM** → **Users**
   - Lien direct: https://console.aws.amazon.com/iam/home#/users

2. **CRÉATION UTILISATEUR**
   - Cliquez sur **Create user** (bouton bleu en haut à droite)

---

## 🔑 **ÉTAPE 1: DÉTAILS UTILISATEUR**

### 📋 **"User details" Section**
```
┌─────────────────────────────────────────┐
│ User details                            │
├─────────────────────────────────────────┤
│ User name: [harmonic-ai-user]           │
│                                         │
│ ☐ Add a display name (optional)        │
│                                         │
│ [Next: Permissions] (bouton bleu)      │
└─────────────────────────────────────────┘
```

3. **Remplissez**:
   - **User name**: `harmonic-ai-user`
   - Cliquez sur **Next: Permissions**

---

## 🔑 **ÉTAPE 2: PERMISSIONS (OÙ TROUVER LES OPTIONS)**

### 🎯 **"Set permissions" Section**

#### **OPTION A: "Attach policies directly"**
```
┌─────────────────────────────────────────┐
│ Set permissions                         │
├─────────────────────────────────────────┤
│ ○ Add user to group                    │
│ ● Attach policies directly  ← SÉLECTIONNEZ CECI │
│ ○ Copy permissions from existing user  │
│ ○ Copy permissions from existing group  │
│                                         │
│ [Next: Tags] (bouton bleu)             │
└─────────────────────────────────────────┘
```

**Localisation exacte**:
- C'est la **première option** dans la section "Set permissions"
- **Cochez le cercle** à côté de "Attach policies directly"
- Cliquez sur **Next: Tags**

---

## 🔑 **ÉTAPE 3: CRÉATION CLÉ D'ACCÈS**

### 🎯 **"Access key" Section**
```
┌─────────────────────────────────────────┐
│ Access key                              │
├─────────────────────────────────────────┤
│ Access key type:                        │
│                                         │
│ ○ Access key - CLI                      │
│ ● Access key - Programmatic access  ← SÉLECTIONNEZ CECI │
│                                         │
│ Description (optional):                 │
│ [Harmonic AI S3 access]                 │
│                                         │
│ [Create access key] (bouton bleu)      │
└─────────────────────────────────────────┘
```

**Localisation exacte**:
- Après avoir créé l'utilisateur, allez dans **Security credentials**
- Cliquez sur **Create access key**
- **Cochez le cercle** à côté de "Access key - Programmatic access"

---

## 📋 **ÉTAPES COMPLÈTES DÉTAILLÉES**

### 🌐 **MÉTHODE 1: CONSOLE AWS (VISUEL)**

#### **ÉTAPE 1: CRÉATION UTILISATEUR**
1. **Console AWS** → **IAM** → **Users**
2. **Create user** (bouton bleu)
3. **User name**: `harmonic-ai-user`
4. **Next: Permissions**

#### **ÉTAPE 2: PERMISSIONS**
5. **● Attach policies directly** ← SÉLECTIONNEZ CECI
6. **Search policies**: tapez `HarmonicAI-S3-Policy`
7. **☐ HarmonicAI-S3-Policy** ← COCHEZ LA CASE
8. **Next: Tags**
9. **Next: Review**
10. **Create user**

#### **ÉTAPE 3: CLÉ D'ACCÈS**
11. **Retour à Users** → **harmonic-ai-user**
12. **Security credentials** (onglet)
13. **Create access key**
14. **● Access key - Programmatic access** ← SÉLECTIONNEZ CECI
15. **Next**
16. **Create access key**
17. **Copiez** l'Access Key ID et Secret Access Key

---

## 🔗 **LIENS DIRECTS**

### **Navigation Directe**
- **Console IAM**: https://console.aws.amazon.com/iam/
- **Users**: https://console.aws.amazon.com/iam/home#/users
- **Création User**: https://console.aws.amazon.com/iam/home#/users$new
- **Politiques**: https://console.aws.amazon.com/iam/home#/policies

---

## 📱 **CAPTURES D'ÉCRAN VIRTUELLES**

### **Écran 1: Création Utilisateur**
```
AWS Management Console
┌─────────────────────────────────────────┐
│ IAM                                    │
│ ─────────────────────────────────────── │
│ Users  Groups  Policies  Roles          │
│                                         │
│ Users                                   │
│ ┌─────────────────────────────────────┐ │
│ │ Create user (bouton bleu)           │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ User name: [harmonic-ai-user]           │
│                                         │
│ ☐ Provide user permissions             │
│                                         │
│ [Next: Permissions]                    │
└─────────────────────────────────────────┘
```

### **Écran 2: Permissions**
```
Set permissions - harmonic-ai-user
┌─────────────────────────────────────────┐
│ Set permissions                         │
├─────────────────────────────────────────┤
│ ○ Add user to group                    │
│ ● Attach policies directly  ← CECI     │
│ ○ Copy permissions from existing user  │
│ ○ Copy permissions from existing group  │
│                                         │
│ Filter policies [Search...]             │
│                                         │
│ ☐ HarmonicAI-S3-Policy                 │
│                                         │
│ [Next: Tags]                           │
└─────────────────────────────────────────┘
```

### **Écran 3: Clé d'Accès**
```
Create access key - harmonic-ai-user
┌─────────────────────────────────────────┐
│ Access key type                         │
├─────────────────────────────────────────┤
│ ○ Access key - CLI                      │
│ ● Access key - Programmatic access ← CECI│
│                                         │
│ Description:                            │
│ [Harmonic AI S3 access]                 │
│                                         │
│ [Create access key]                     │
└─────────────────────────────────────────┘
```

---

## 🔧 **SCRIPT AUTOMATIQUE (AWS CLI)**

Si vous préférez la ligne de commande:

```bash
# Créer l'utilisateur
aws iam create-user --user-name harmonic-ai-user

# Attacher la politique
aws iam attach-user-policy \
    --user-name harmonic-ai-user \
    --policy-arn arn:aws:iam::aws:policy/HarmonicAI-S3-Policy

# Créer la clé d'accès
aws iam create-access-key --user-name harmonic-ai-user
```

---

## 📋 **VÉRIFICATION**

Une fois créé, vérifiez:

1. **IAM** → **Users** → **harmonic-ai-user**
2. **Permissions** → Vérifiez `HarmonicAI-S3-Policy`
3. **Security credentials** → Vérifiez la clé d'accès

---

## 🚨 **POINTS IMPORTANTS**

- **"Attach policies directly"** = Première option dans "Set permissions"
- **"Access key - Programmatic access"** = Option dans "Create access key"
- **Copiez immédiatement** les clés (elles ne s'affichent qu'une fois)
- **Sauvegardez** les clés dans un endroit sécurisé

---

**🔐 Utilisateur IAM harmonic-ai-user prêt pour la sécurité maximale !**
