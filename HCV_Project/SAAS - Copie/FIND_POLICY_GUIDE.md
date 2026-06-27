# 🔍 GUIDE POUR TROUVER HARMONICAI-S3-POLICY

## 📋 **VOTRE SITUATION ACTUELLE**

Vous êtes sur la page **IAM → Policies** avec **1487 politiques**.
Vous cherchez votre politique `HarmonicAI-S3-Policy` que vous avez créée.

---

## 🎯 **MÉTHODE 1: RECHERCHE DIRECTE (PLUS RAPIDE)**

### **Étape 1: Barre de recherche**
```
┌─────────────────────────────────────────┐
│ Politiques (1487)                       │
├─────────────────────────────────────────┤
│ 🔍 [Search...] ← TAPEZ ICI              │
│                                         │
│ ☐ Gérées par AWS                        │
│ ☐ Gérées par mon compte                 │
│ ☐ Politiques personnalisées            │
│                                         │
│ [Créer une politique]                   │
└─────────────────────────────────────────┘
```

### **Étape 2: Tapez exactement**
```
🔍 [HarmonicAI-S3-Policy]
```

### **Étape 3: Filtres**
- **Décochez** "Gérées par AWS"
- **Cochez** "Gérées par mon compte"
- **Cochez** "Politiques personnalisées"

---

## 🎯 **MÉTHODE 2: FILTRAGE PAR TYPE**

### **Filtres à appliquer:**
```
☑️ Gérées par mon compte
☑️ Politiques personnalisées
❌ Gérées par AWS
```

### **Résultat attendu:**
```
Nom de la politique           Type                      Description
─────────────────────────────────────────────────────────────────────
HarmonicAI-S3-Policy          Gérées par mon compte     Politique S3 limitée pour Harmonic AI
```

---

## 🎯 **MÉTHODE 3: NAVIGATION MANUELLE**

### **Si la recherche ne fonctionne pas:**

1. **Filtrez par Type**:
   - **Type**: "Gérées par mon compte"
   - **Cliquez** sur le filtre

2. **Cherchez alphabétiquement**:
   - Les politiques sont classées par ordre alphabétique
   - **Cherchez sous la lettre "H"**
   - **Position**: environ dans les 10-15 premières politiques

---

## 🔍 **CE QUE VOUS DEVEZ VOIR**

### **Votre politique apparaîtra comme:**
```
┌─────────────────────────────────────────┐
│ HarmonicAI-S3-Policy                    │
│ Gérées par mon compte                   │
│ Politique S3 limitée pour Harmonic AI   │
│                                         │
│ ☑️ [ ]                                   │
│ 📝 [Modifier] 🗑️ [Supprimer]             │
└─────────────────────────────────────────┘
```

---

## 🚨 **SI VOUS NE LA TROUVEZ PAS**

### **Cas 1: Politique non créée**
- **Solution**: Recréez-la avec le script précédent
- **Lien**: https://console.aws.amazon.com/iam/home#/policies$new

### **Cas 2: Dans une autre région**
- **Vérifiez** la région en haut à droite
- **Assurez-vous** d'être dans la bonne région

### **Cas 3: Nom différent**
- **Cherchez**: "harmonic" (sans majuscules)
- **Cherchez**: "s3" (politiques S3)
- **Cherchez**: "policy" (toutes vos politiques)

---

## 🔗 **LIENS DIRECTS**

### **Recherche rapide:**
- **Toutes politiques**: https://console.aws.amazon.com/iam/home#/policies
- **Politiques personnalisées**: https://console.aws.amazon.com/iam/home#/policies$filter=CustomerManaged
- **Création politique**: https://console.aws.amazon.com/iam/home#/policies$new

---

## 📱 **INTERFACE VISUELLE**

### **Barre de recherche:**
```
┌─────────────────────────────────────────┐
│ Policies (1487)                        │
├─────────────────────────────────────────┤
│ 🔍 Search policies [HarmonicAI...]     │
│                                         │
│ Filters:                                │
│ ☑️ Customer managed                     │
│ ❌ AWS managed                          │
│                                         │
│ Table:                                  │
│ ┌─────────────────────────────────────┐ │
│ │ ☐ HarmonicAI-S3-Policy             │ │
│ │    Customer managed                 │ │
│ │    Politique S3 limitée...          │ │
│ │    [ ] [Edit] [Delete]              │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 🎯 **ACTION IMMÉDIATE**

1. **Dans la barre de recherche**, tapez: `HarmonicAI-S3-Policy`
2. **Filtrez**: "Gérées par mon compte"
3. **Cliquez** sur votre politique
4. **Vérifiez** les permissions
5. **Notez** l'ARN de la politique

---

## 📋 **VÉRIFICATION DES PERMISSIONS**

Une fois trouvée, vérifiez qu'elle contient:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:CreateBucket",
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::harmonic-ai-knowledge-base",
                "arn:aws:s3:::harmonic-ai-knowledge-base/*"
            ]
        }
    ]
}
```

---

**🔍 Votre politique HarmonicAI-S3-Policy doit être trouvée facilement avec la recherche !**
