#!/usr/bin/env python3
"""
GUIDE POUR TROUVER VOTRE POLITIQUE HARMONICAI-S3-POLICY
Dans la liste des 1487 politiques AWS
"""

import webbrowser

def create_policy_search_guide():
    """Crée un guide pour trouver la politique dans la liste"""
    
    guide = """# 🔍 GUIDE POUR TROUVER HARMONICAI-S3-POLICY

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
"""
    
    with open("FIND_POLICY_GUIDE.md", 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("✅ Guide de recherche créé: FIND_POLICY_GUIDE.md")

def open_policies_page():
    """Ouvre la page des politiques avec filtre"""
    
    print("\n🌐 OUVERTURE PAGE POLITIQUES...")
    print("   Navigation vers: IAM → Policies")
    
    # Ouvre la page des politiques avec filtre pour politiques personnalisées
    webbrowser.open("https://console.aws.amazon.com/iam/home#/policies$filter=CustomerManaged")
    
    print("✅ Page politiques ouverte (filtrée sur politiques personnalisées)")

def create_quick_search_tips():
    """Crée des astuces de recherche rapide"""
    
    tips = """# 🚀 ASTUCES RECHERCHE RAPIDE

## 🔍 **TERMES DE RECHERCHE À ESSAYER**

1. **Exact**: `HarmonicAI-S3-Policy`
2. **Partiel**: `HarmonicAI`
3. **Partiel**: `harmonic`
4. **Par type**: `s3`
5. **Par utilisateur**: `customer`

## 🎯 **FILTRES EFFICACES**

### **Pour réduire de 1487 → ~10:**
- ✅ **Customer managed** (politiques créées par vous)
- ❌ **AWS managed** (politiques AWS par défaut)

### **Résultat attendu:**
```
Avant: 1487 politiques
Après: ~10-20 politiques maximum
```

## 📊 **STATISTIQUES RECHERCHE**

- **AWS managed**: ~1470 politiques
- **Customer managed**: ~17 politiques
- **Votre politique**: 1 politique

---

**🎯 De 1487 → 1 politique en 3 clics !**
"""
    
    with open("SEARCH_TIPS.md", 'w', encoding='utf-8') as f:
        f.write(tips)
    
    print("✅ Astuces de recherche créées: SEARCH_TIPS.md")

def main():
    """Fonction principale"""
    
    print("🔍 GUIDE POUR TROUVER HARMONICAI-S3-POLICY")
    print("=" * 60)
    print("📍 Dans la liste des 1487 politiques AWS")
    print("=" * 60)
    
    # Créer le guide de recherche
    create_policy_search_guide()
    
    # Créer les astuces de recherche
    create_quick_search_tips()
    
    # Ouvrir la page des politiques
    open_policies_page()
    
    print(f"\n🎯 RÉPONSE DIRECTE À VOTRE SITUATION:")
    print("=" * 50)
    print("📍 Vous êtes sur: IAM → Policies (1487 politiques)")
    print("🔍 Tapez dans la recherche: HarmonAI-S3-Policy")
    print("☑️ Filtrez: Customer managed uniquement")
    print("📊 Résultat: 1 politique trouvée")
    print("=" * 50)
    
    print(f"\n📋 MÉTHODE la plus rapide:")
    print("1. 🔍 Barre de recherche → Tapez: HarmonAI-S3-Policy")
    print("2. ☑️ Filtre → Customer managed")
    print("3. 🎯 Cliquez sur votre politique")
    
    print(f"\n📚 Fichiers créés:")
    print("   📋 FIND_POLICY_GUIDE.md")
    print("   🚀 SEARCH_TIPS.md")
    
    print(f"\n🌐 Page ouverte:")
    print("   https://console.aws.amazon.com/iam/home#/policies$filter=CustomerManaged")
    
    print(f"\n🔍 Votre politique trouvée facilement !")

if __name__ == "__main__":
    main()
