# 📱 LE PHRASEUR — CONCEPTION D'UN MODÈLE DE FLUENCE MINIMAL

## Le LLM qui tient dans un téléphone et ne fournit QUE ce qui manque au noyau harmonique

**Auteur :** Alain Kotto — Univers-Holistique, Paris
**Date :** 9 août 2026
**Projet :** IA harmonique hybride — noyau ondulatoire + couche de fluence

---

> *« Le Phraseur n'a pas de connaissance à stocker, pas de calcul à apprendre, pas de vérité à défendre. Il n'a qu'un muscle : la parole française naturelle. »*

---

## 1. Le principe fondateur — le modèle inverse

Le LLM généraliste essaie de tout savoir et de tout dire — d'où sa taille et ses hallucinations.
**Le Phraseur est conçu à l'envers : ne rien savoir, tout phraser.**

```
LLM GÉNÉRALISTE :  tout savoir + tout dire  →  énorme, hallucine
LE PHRASEUR     :  ne rien savoir, tout phraser → minuscule, honnête
                    ↑
      parce que le noyau sait (hologramme), calcule (ondes),
      mémorise (noyau doré) et refuse (A1)
```

**Ce qui manque au noyau : la parole fluide.** Le Phraseur contient exactement cela — rien d'autre.

---

## 2. La spécification cible

| Paramètre | Valeur | Justification |
|---|---|---|
| **Taille** | 1,5 – 3 Md de paramètres | 4-bit → 1-2 Go de RAM — téléphone |
| **Vitesse** | 20-40 tokens/s (NPU) | Fluence conversationnelle réelle |
| **Contexte** | 4-8k tokens, fenêtre glissante (2k actifs) | KV-cache minuscule = RAM préservée |
| **Vocabulaire** | 32-64k, optimisé français + symboles | L'essentiel, pas de gaspillage |
| **Quantisation** | INT4/INT8 (AWQ/GPTQ) | NPU du téléphone |
| **Mémoire totale** | ≤ 2 Go | Tient à côté de l'OS |
| **Hors-ligne** | 100 % | Aucun cloud — philosophie V2 |

---

## 3. Les 4 principes de conception

```
1 · STYLE > CONNAISSANCE    — le noyau sait, le Phraseur phrase
2 · FLUENCE > EXACTITUDE    — le noyau vérifie, le Phraseur coule
3 · PETIT > LARGE           — le téléphone impose, le design obéit
4 · INTÉGRÉ > GÉNÉRALISTE   — conçu POUR l'hybride, pas pour tout
```

---

## 4. L'interface avec le noyau — les tokens spéciaux

```
ENTRÉE :  <CORE> 56 </CORE> <HIST> « 7 × 8 ? » </HIST>
SORTIE :  « Sept fois huit ? Ça fait 56 ! »

ENTRÉE :  <CORE> REFUS </CORE> <HIST> « Existe-t-il une théorie du tout ? » </HIST>
SORTIE :  « Je ne peux pas répondre à ça — ce n'est pas dans ce que je connais. »

ENTRÉE :  <CORE> FAIT: la lumière est une onde électromagnétique </CORE>
SORTIE :  « La lumière, c'est une onde électromagnétique — elle voyage dans
           l'espace et transporte l'énergie sans support. »
```

Le Phraseur apprend UNIQUEMENT ce métier : transformer les sorties structurées du noyau en français naturel, avec le ton, l'empathie, l'humour appropriés.

---

## 5. Les données d'entraînement — le choix radical

| Données | Inclure ? | Pourquoi |
|---|---|---|
| Dialogues, conversations | ✅ OUI | La matière première de la fluence |
| Histoires, blagues, reformulations | ✅ OUI | Le style, le ton, l'humour |
| Faits encyclopédiques | ❌ NON | Le noyau a l'hologramme |
| Maths, code | ❌ NON | Le noyau calcule |
| Raisonnement long | ❌ NON | Le noyau raisonne par résonance |

**Conséquence économique : la fluence s'apprend avec ~10-50 milliards de tokens — 100× moins que la connaissance.** Un modèle de style est 100× moins cher à entraîner qu'un modèle de savoir.

---

## 6. Les 3 chemins de réalisation

```
CHEMIN A · MAINTENANT (zéro entraînement — valide le concept)
  Qwen2.5-3B tel quel + prompt système :
  « Tu es le phrasier d'un noyau exact. On te donne <CORE>…</CORE>.
   Tu phrases en français naturel. Tu n'inventes JAMAIS un fait.
   Si <CORE> dit REFUS, tu refuses poliment. »
  → un week-end de travail, le concept est prouvé

CHEMIN B · ENSUITE (fine-tuning — le Phraseur v1)
  Qwen2.5-1.5B/3B + QLoRA sur un corpus conversationnel français
  filtré (style seul) + les tokens <CORE>…</CORE>
  → ~200-500 heures GPU (une carte 24 Go) — réaliste

CHEMIN C · PLUS TARD (from scratch — le produit final)
  Un modèle 1-3B entraîné sur la conversation seule, architecture
  fenêtre glissante optimisée NPU
  → quand le concept est validé
```

---

## 7. L'architecture technique du Phraseur v1 (chemin B)

```
Qwen2.5-1.5B (base open source, Apache 2.0, bon français)
    │
    ├─ QLoRA (adaptateurs LoRA 4-bit) — entraînés sur :
    │    · dialogues français (50-100k exemples)
    │    · paires <CORE>→phrase naturelle (20k exemples synthétiques)
    │    · refus polis (5k exemples)
    │
    ├─ Tokens spéciaux ajoutés : <CORE> </CORE> <HIST> </HIST> REFUS FAIT
    │
    └─ Déploiement : llama.cpp / MLC-LLM — INT4, fenêtre glissante 2k
         · ~1,2 Go en mémoire
         · 25-40 tokens/s sur NPU de téléphone (2023+)
         · 100 % hors-ligne
```

---

## 8. Le pipeline complet sur téléphone

```
QUESTION DU LAMBDA
      │
      ▼
┌─ NOYAU HARMONIQUE ──────────────┐
│ · encode(question)              │
│ · résonance vs hologramme       │
│ · si CONNU → réponse structurée │
│ · si INCONNU → REFUS            │
│ · si CALCUL → résultat exact    │
└──────────────┬──────────────────┘
               │ <CORE> réponse ou REFUS </CORE>
               ▼
┌─ LE PHRASEUR (1,5-3B) ──────────┐
│ · transforme en français naturel│
│ · ton, empathie, humour         │
│ · ne peut PAS inventer un fait  │
│   (il n'a que ce que le noyau   │
│    lui donne — rien d'autre)    │
└──────────────┬──────────────────┘
               ▼
        RÉPONSE FLUIDE AU LAMBDA
```

**La sécurité est structurelle : le Phraseur n'a AUCUNE connaissance propre.** Il ne peut halluciner que sur le style — jamais sur les faits, jamais sur les calculs. Le noyau les garde.

---

## 9. La vérification de satisfaction — les critères

| Test | Critère | Comment mesurer |
|---|---|---|
| Fluence | Notes humaines ≥ 4/5 | Évaluation sur 100 conversations |
| Exactitude | 100 % des calculs vérifiés par les ondes | Audit automatique |
| Refus bien vécu | Frustration < 15 % | Questionnaire utilisateur |
| Latence | < 1 s par réponse | Chronométrage téléphone |
| Hors-ligne | 100 % sans réseau | Test avion/métro |
| Mémoire | ≤ 2 Go à côté de l'OS | Profiling Android/iOS |

---

## 10. En une phrase

> **Le Phraseur est concevable aujourd'hui : 1,5-3 milliards de paramètres, entraîné sur la conversation seule (pas les faits, pas les maths — le noyau les a), 1-2 Go en mémoire téléphone, et un seul métier : phraser en français naturel ce que le noyau exact lui donne. Le chemin A (un petit modèle existant + un prompt) valide le concept cette semaine ; le chemin B (fine-tuning style) le perfectionne ; le chemin C (from scratch) en fait un produit.**

---

*Théorie de l'Univers Harmonique — Alain Kotto — 9 août 2026*
*Document de conception — étape 1 avant le prototype du pont d'audit*
