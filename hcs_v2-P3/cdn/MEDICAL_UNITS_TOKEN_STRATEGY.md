# Stratégie: Unités Médicales comme Tokens de Valeur
## Système de Crédits Médicaux pour Frais Médicaux en Afrique

**Date**: Février 2026  
**Concept**: Unités Médicales = Tokens de valeur spécifique (pas de monnaie)  
**Marché**: Afrique (1.4B habitants, 35% bancarisés)  
**TAM**: $50B+ (assurance santé informelle)

---

## 1. CONCEPT: UNITÉS MÉDICALES COMME TOKENS

### Qu'est-ce qu'une Unité Médicale?
**Définition**: Token/crédit de valeur spécifique envoyé à un bénéficiaire pour payer frais médicaux

**Caractéristiques**:
- ✅ Pas de monnaie réelle (token virtuel)
- ✅ Valeur spécifique (ex: 1 UM = $10)
- ✅ Utilisable uniquement chez prestataires partenaires
- ✅ Convertible en argent réel par prestataire
- ✅ Traçabilité complète
- ✅ Chiffrement E2E

### Flux Complet

```
ÉTAPE 1: CRÉATION D'UNITÉS MÉDICALES
┌─────────────────────────────────────────┐
│ Famille envoie Unités Médicales         │
│ (pas d'argent réel)                     │
│                                         │
│ Exemple:                                │
│ - Fils (USA) envoie 50 UM               │
│   (50 UM = $500 à taux de change)      │
│ - Frère (Dakar) envoie 10 UM            │
│ - Sœur (Abidjan) envoie 10 UM           │
│ - Oncle (Paris) envoie 15 UM            │
│ - Tante (Londres) envoie 5 UM           │
│ - Cousin (Lagos) envoie 10 UM           │
│                                         │
│ TOTAL: 100 UM collectées                │
└─────────────────────────────────────────┘
                    ↓
ÉTAPE 2: BÉNÉFICIAIRE REÇOIT UNITÉS
┌─────────────────────────────────────────┐
│ Maman reçoit 100 UM                     │
│ (dans son portefeuille digital)         │
│                                         │
│ Solde: 100 UM                           │
│ Valeur équivalente: $1000               │
│ (à taux de change actuel)               │
└─────────────────────────────────────────┘
                    ↓
ÉTAPE 3: BÉNÉFICIAIRE UTILISE UNITÉS
┌─────────────────────────────────────────┐
│ Maman va à l'hôpital partenaire         │
│ Facture: $500                           │
│                                         │
│ Paiement avec Unités Médicales:         │
│ - Envoie 50 UM à l'hôpital              │
│ - Hôpital reçoit 50 UM                  │
│ - Solde Maman: 50 UM restants           │
└─────────────────────────────────────────┘
                    ↓
ÉTAPE 4: PRESTATAIRE CONVERTIT EN ARGENT
┌─────────────────────────────────────────┐
│ Hôpital reçoit 50 UM                    │
│ Demande conversion à la plateforme      │
│                                         │
│ Conversion:                             │
│ - 50 UM × $10/UM = $500                 │
│ - Frais plateforme: 2% = $10            │
│ - Hôpital reçoit: $490                  │
│                                         │
│ Virement sur compte bancaire            │
│ (M-Pesa, Airtel, Orange, Bank)         │
└─────────────────────────────────────────┘
```

---

## 2. MODÈLE ÉCONOMIQUE: UNITÉS MÉDICALES

### Valeurs d'Unités Médicales

```
Unité Médicale Standard (UM):
- 1 UM = $10 USD (valeur de base)
- Convertible en devises locales
- Taux de change: Mis à jour quotidiennement

Exemples de valeurs:
- 1 UM = $10 USD
- 1 UM = 6000 XOF (Franc CFA)
- 1 UM = 1300 KES (Shilling kényan)
- 1 UM = 4100 NGN (Naira nigérian)
- 1 UM = 185 ZAR (Rand sud-africain)
```

### Trois Types d'Unités Médicales

#### Type 1: URGENCE MÉDICALE
**Déclencheur**: Maladie soudaine, accident, urgence  
**Montant**: 10-500 UM ($100-$5000)  
**Durée**: 1-7 jours  
**Urgence**: Très haute  
**Frais conversion**: 2%  
**Exemple**: Appendicite, accident, crise cardiaque

```python
# POST /medical-units/create-emergency
{
    "initiator_id": "user_son_usa",
    "beneficiary_id": "user_mother_senegal",
    "type": "emergency",
    "amount_um": 50,  # 50 UM = $500
    "reason": "Appendicite - hospitalisation urgente",
    "medical_proof": "photo_ordonnance.jpg",
    "hospital": "Hôpital Principal Dakar",
    "duration_days": 7,
    "family_members": [
        "user_brother_dakar",
        "user_sister_abidjan",
        "user_uncle_paris"
    ]
}

# Réponse
{
    "unit_id": "mu_emergency_123",
    "status": "active",
    "amount_um": 50,
    "value_usd": 500.00,
    "collected_um": 0,
    "contributors": 0,
    "deadline": "2026-02-25T10:00:00Z",
    "urgency": "high",
    "notifications_sent": 3
}
```

---

#### Type 2: SUIVI MÉDICAL CHRONIQUE
**Déclencheur**: Maladie chronique (diabète, hypertension, asthme)  
**Montant**: 5-50 UM/mois ($50-$500)  
**Durée**: Mensuel, récurrent  
**Urgence**: Moyenne  
**Frais conversion**: 1.5%  
**Exemple**: Diabète, hypertension, asthme

```python
# POST /medical-units/create-chronic
{
    "initiator_id": "user_father_senegal",
    "beneficiary_id": "user_father_senegal",
    "type": "chronic",
    "amount_um": 10,  # 10 UM = $100/mois
    "reason": "Diabète - médicaments mensuels",
    "medical_condition": "diabetes",
    "frequency": "monthly",
    "duration_months": 12,
    "family_members": [
        "user_son_usa",
        "user_daughter_france",
        "user_brother_dakar"
    ]
}

# Réponse
{
    "unit_id": "mu_chronic_456",
    "status": "active",
    "amount_um": 10,
    "value_usd": 100.00,
    "frequency": "monthly",
    "next_collection": "2026-03-18",
    "total_annual_um": 120,
    "contributors": 3,
    "auto_collect": true
}
```

---

#### Type 3: PRÉVENTION & BIEN-ÊTRE
**Déclencheur**: Prévention, check-up, vaccination  
**Montant**: 2-20 UM ($20-$200)  
**Durée**: Annuel ou ponctuel  
**Urgence**: Basse  
**Frais conversion**: 1%  
**Exemple**: Vaccination, check-up annuel, dentiste

```python
# POST /medical-units/create-prevention
{
    "initiator_id": "user_mother_senegal",
    "beneficiary_id": "user_child_senegal",
    "type": "prevention",
    "amount_um": 5,  # 5 UM = $50
    "reason": "Vaccination annuelle enfant",
    "medical_service": "vaccination",
    "frequency": "annual",
    "family_members": [
        "user_father_senegal",
        "user_uncle_dakar"
    ]
}

# Réponse
{
    "unit_id": "mu_prevention_789",
    "status": "active",
    "amount_um": 5,
    "value_usd": 50.00,
    "frequency": "annual",
    "next_collection": "2027-02-18",
    "contributors": 2
}
```

---

## 3. ARCHITECTURE: UNITÉS MÉDICALES COMME TOKENS

### Modèle de Données

```python
@dataclass
class MedicalUnit:
    """Unité médicale (token)"""
    unit_id: str
    initiator_id: str  # Qui crée la demande
    beneficiary_id: str  # Qui reçoit les UM
    type: str  # emergency, chronic, prevention
    amount_um: float  # Montant en UM (pas en argent)
    value_usd: float  # Valeur équivalente en USD
    reason: str  # Raison médicale
    medical_proof: str  # URL photo ordonnance/facture
    hospital: str  # Nom hôpital/clinique
    family_members: List[str]  # IDs membres famille
    contributions_um: Dict[str, float]  # {user_id: amount_um}
    total_collected_um: float  # Total collecté en UM
    status: str  # active, completed, cancelled
    created_at: str
    deadline: str  # Délai pour contribuer
    transferred_at: str  # Quand transféré au bénéficiaire
    insurance_coverage_um: float  # Couverture assurance en UM
    fee_percent: float  # 1-2% frais conversion

@dataclass
class MedicalUnitWallet:
    """Portefeuille d'unités médicales"""
    wallet_id: str
    user_id: str
    balance_um: float  # Solde en UM
    value_usd: float  # Valeur équivalente en USD
    transactions: List[Dict]  # Historique transactions
    created_at: str

@dataclass
class MedicalUnitConversion:
    """Conversion UM → Argent réel"""
    conversion_id: str
    provider_id: str  # ID prestataire (hôpital, pharmacie)
    amount_um: float  # Montant en UM
    value_usd: float  # Valeur en USD
    fee_percent: float  # Frais conversion (1-2%)
    fee_usd: float  # Montant frais
    amount_to_transfer: float  # Montant à transférer
    currency: str  # Devise locale (XOF, KES, NGN, etc)
    amount_local: float  # Montant en devise locale
    status: str  # pending, completed, failed
    bank_account: str  # Compte bancaire prestataire
    payment_method: str  # M-Pesa, Airtel, Orange, Bank
    created_at: str
    completed_at: str
```

### Flux Complet

```
┌─────────────────────────────────────────────────────────┐
│ 1. CRÉATION D'UNITÉS MÉDICALES (Tokens)                 │
│    - Famille envoie UM (pas d'argent)                   │
│    - Chaque UM = $10 USD (valeur fixe)                  │
│    - Traçabilité complète                               │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 2. NOTIFICATION FAMILLE                                 │
│    - SMS + App notification                            │
│    - Montant en UM + valeur USD équivalente            │
│    - Preuve médicale visible                           │
│    - Délai de contribution                             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 3. CONTRIBUTION FAMILIALE (En UM)                        │
│    - Chaque membre envoie UM (pas d'argent)            │
│    - Paiement instantané (M-Pesa, Airtel, etc)         │
│    - Confirmation immédiate                            │
│    - UM ajoutées au portefeuille bénéficiaire          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 4. COLLECTE & AGRÉGATION (En UM)                         │
│    - UM collectées en temps réel                        │
│    - Transparence: Tous voient contributions           │
│    - Historique: Traçabilité complète                  │
│    - Assurance: Couverture si montant insuffisant      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 5. TRANSFERT AU BÉNÉFICIAIRE (En UM)                     │
│    - UM transférées instantanément                      │
│    - Bénéficiaire reçoit UM dans portefeuille          │
│    - Confirmation: SMS + App                           │
│    - Reçu: Partagé avec famille                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 6. UTILISATION CHEZ PRESTATAIRE (Paiement en UM)        │
│    - Bénéficiaire va chez prestataire partenaire       │
│    - Paie avec UM (pas d'argent réel)                  │
│    - Prestataire reçoit UM                             │
│    - Solde bénéficiaire: UM restants                   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 7. CONVERSION UM → ARGENT RÉEL (Prestataire)            │
│    - Prestataire demande conversion                     │
│    - Plateforme convertit UM en argent réel            │
│    - Frais: 1-2% (selon type)                          │
│    - Virement sur compte prestataire                   │
│    - Méthode: M-Pesa, Airtel, Orange, Bank            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 8. HISTORIQUE MÉDICAL CRÉÉ                              │
│    - Facture enregistrée                               │
│    - Dossier médical mis à jour                        │
│    - Reçu partagé avec famille                         │
│    - Traçabilité complète                              │
└─────────────────────────────────────────────────────────┘
```

---

## 4. RÉSEAU DE PRESTATAIRES PARTENAIRES

### Types de Prestataires
1. **Hôpitaux** (publics et privés)
2. **Cliniques** (généralistes et spécialisées)
3. **Pharmacies** (indépendantes et chaînes)
4. **Laboratoires** (analyses médicales)
5. **Cabinets dentaires**
6. **Centres de vaccination**
7. **Maternités**
8. **Centres de réadaptation**

### Intégration Prestataire

```python
# POST /providers/register
{
    "provider_name": "Hôpital Principal Dakar",
    "provider_type": "hospital",
    "country": "Senegal",
    "city": "Dakar",
    "phone": "+221 33 123 4567",
    "email": "contact@hopital-dakar.sn",
    "bank_account": "SN64 BMCE 0000 1234 5678 9012 34",
    "payment_method": "bank_transfer",  # ou M-Pesa, Airtel, Orange
    "accepted_um": true,
    "conversion_fee_percent": 2.0
}

# Réponse
{
    "provider_id": "prov_123",
    "status": "registered",
    "verified": false,  # À vérifier manuellement
    "um_wallet": "prov_wallet_123",
    "balance_um": 0
}
```

### Conversion UM → Argent Réel

```python
# POST /providers/{provider_id}/convert-um
{
    "amount_um": 50,  # 50 UM = $500
    "currency": "XOF",  # Franc CFA
    "bank_account": "SN64 BMCE 0000 1234 5678 9012 34",
    "payment_method": "bank_transfer"
}

# Réponse
{
    "conversion_id": "conv_123",
    "amount_um": 50,
    "value_usd": 500.00,
    "fee_percent": 2.0,
    "fee_usd": 10.00,
    "amount_to_transfer": 490.00,
    "currency": "XOF",
    "exchange_rate": 600.0,  # 1 USD = 600 XOF
    "amount_local": 294000.00,  # 490 × 600
    "status": "pending",
    "estimated_arrival": "2026-02-20T10:00:00Z",
    "timestamp": "2026-02-18T10:30:00Z"
}
```

---

## 5. AVANTAGES DU MODÈLE TOKEN

### vs Argent Réel
| Aspect | Argent Réel | Unités Médicales (Tokens) |
|--------|------------|--------------------------|
| Risque fraude | Élevé | **Très faible** |
| Traçabilité | Limitée | **Complète** |
| Utilisation | Illimitée | **Uniquement santé** |
| Contrôle | Difficile | **Complet** |
| Assurance | Non | **Oui** |
| Historique médical | Non | **Oui** |
| Conversion | N/A | **À la demande** |

### vs Assurance Formelle
| Aspect | Assurance Formelle | Unités Médicales |
|--------|------------------|-----------------|
| Accès | 35% population | **100% (famille)** |
| Coût | $50-$200/mois | **Flexible** |
| Délai approbation | 1-2 semaines | **Instantané** |
| Couverture | Limitée | **Flexible** |
| Famille impliquée | Non | **Oui** |
| Traçabilité | Oui | **Oui** |
| Utilisation | Hôpitaux agréés | **Réseau partenaires** |

---

## 6. IMPLÉMENTATION

### Phase 1: MVP (Semaines 1-4)
- [ ] Modèle MedicalUnit (tokens)
- [ ] Endpoints: create, contribute, transfer
- [ ] Portefeuille UM
- [ ] Notifications: SMS + App
- [ ] Paiements: M-Pesa, Airtel, Orange
- **Effort**: 120 heures

### Phase 2: Réseau Prestataires (Semaines 5-8)
- [ ] Enregistrement prestataires
- [ ] Conversion UM → Argent réel
- [ ] Intégration bancaire
- [ ] Virement automatique
- **Effort**: 100 heures

### Phase 3: Preuve Médicale (Semaines 9-12)
- [ ] Upload preuve (ordonnance, facture)
- [ ] OCR: Extraire texte
- [ ] Validation: Vérifier authenticité
- [ ] Historique médical
- **Effort**: 80 heures

### Phase 4: Assurance (Semaines 13-16)
- [ ] Assurance intégrée
- [ ] Couverture automatique
- [ ] Payout automatique
- [ ] Gestion sinistres
- **Effort**: 100 heures

### Phase 5: Optimisation (Semaines 17-20)
- [ ] Performance 2G/3G
- [ ] Offline-first
- [ ] Analytics
- [ ] Sécurité
- **Effort**: 80 heures

**Effort Total**: 480 heures (12 semaines, 2-3 devs)

---

## 7. PROJECTIONS FINANCIÈRES

### Utilisateurs (12 mois)
- Mois 1-3: 100K
- Mois 4-6: 500K
- Mois 7-9: 2M
- Mois 10-12: 5M

### Unités Médicales (12 mois)
- Mois 1-3: 10K unités/mois
- Mois 4-6: 50K unités/mois
- Mois 7-9: 200K unités/mois
- Mois 10-12: 500K unités/mois

### Revenus (12 mois)
- **Frais conversion**: 500K unités × 50 UM avg × $10 × 1.5% = **$375K/mois**
- **Assurance**: 500K unités × 10% sinistres × 50 UM × $10 × 20% margin = **$150K/mois**
- **Abonnements**: 5M users × 5% conversion × $1.99/mois = **$500K/mois**
- **TOTAL**: ~$1M/mois = **$12M/an**

### Coûts
- Infrastructure: $500K
- Équipe: $1M
- Marketing: $1M
- Assurance: $400K
- Opérations: $500K
- **TOTAL**: ~$3.4M/an

### Profit
- **Gross Profit**: $12M - $3.4M = **$8.6M**
- **Margin**: 72%

---

## 8. RISQUES & MITIGATION

| Risque | Probabilité | Impact | Mitigation |
|--------|------------|--------|-----------|
| **Fraude prestataire** | Moyenne | Moyen | Vérification prestataire, audit |
| **Fraude utilisateur** | Faible | Faible | Limite quotidienne, 2FA |
| **Régulation** | Élevée | Moyen | Conformité locale, licences |
| **Adoption** | Moyenne | Élevé | Marketing familial, influencers |
| **Assurance** | Faible | Moyen | Partenaires assurance, réserves |

---

## 9. MÉTRIQUES DE SUCCÈS

### Utilisateurs
- **12 mois**: 5M utilisateurs actifs
- **24 mois**: 20M utilisateurs actifs

### Unités Médicales
- **12 mois**: 500K unités/mois
- **Montant moyen**: 50 UM ($500)
- **Taux de complétion**: 95%
- **Taux de satisfaction**: 4.8/5.0

### Prestataires
- **12 mois**: 5000 prestataires partenaires
- **Conversions mensuelles**: 100K conversions
- **Montant moyen conversion**: 50 UM ($500)

### Financiers
- **Revenus 12 mois**: $12M
- **Profit 12 mois**: $8.6M
- **CAC**: $2
- **LTV**: $400
- **LTV/CAC Ratio**: 200x

---

## 10. CONCLUSION

### Opportunité
**TRANSFORMATRICE** - Système de tokens médicaux pour 1.4B africains

### Faisabilité
**TRÈS HAUTE** - 480 heures (12 semaines, 2-3 devs)

### ROI
**EXCELLENT** - 40x (si adoption réussit)

### Impact Social
**MAJEUR** - Accès à santé pour familles sans assurance

### Recommandation
**GO IMMÉDIATEMENT** ✅

---

## FICHIERS À CRÉER

1. ✅ `cdn/MEDICAL_UNITS_TOKEN_STRATEGY.md` - Ce document
2. ⏳ `cdn/services/svc_medical_units_token.py` - Implémentation
3. ⏳ `cdn/MEDICAL_UNITS_TOKEN_ROADMAP.md` - Roadmap détaillée
4. ⏳ `cdn/frontend/medical_units_token.html` - Interface

