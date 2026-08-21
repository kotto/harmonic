# Présentation 20 minutes — Équipe IA MTN Group

**Objectif** : obtenir (1) le lancement d'un **POC Enterprise de 90 jours sur un cas client MTN réel**, et (2) le feu vert pour la négociation de l'accord-cadre (licence + équité minoritaire ≤ 25 %).

| | |
|---|---|
| **Audience** | Équipe IA MTN Group (dirigeants IA + 1-2 ingénieurs) — audience technique ET décideuse |
| **Prérequis** | One-pager PDG déjà transmis · NDA signé · validation tierce en cours (à mentionner) |
| **Matériel** | 1 serveur local (ou laptop puissant) avec KA Enterprise · téléphone VITAL KA (mode avion) · fichiers de démo compression · le one-pager PDG en main |
| **Règle d'or** | 3 démos, 3 preuves, 1 demande. Aucune théorie. Aucun slide PowerPoint si possible — **la démo EST la présentation**. |

---

## Déroulé minute par minute

### 0:00–0:02 — Ouverture : le contrat de la réunion (2 min)
**Texte à dire mot pour mot :**
> *« Merci. Le PDG vous a transmis le one-pager : une pile africaine souveraine, déterministe, fonctionnelle aujourd'hui. Vous êtes l'équipe qui doit vérifier que ce n'est pas de la littérature. Donc pas de slides : trois démos, en direct, sur du matériel que vous pouvez contrôler. Si une démo échoue, on s'arrête et on parle honnêtement de ce qui a échoué. À la fin, une demande concrète : un POC de 90 jours sur un de vos cas clients. »*

**Pourquoi ça marche** : vous posez d'emblée la norme de la réunion (la preuve, pas la promesse) — c'est exactement ce que cette audience attend et ce que vos concurrents ne font pas.

### 0:02–0:08 — DÉMO 1 : KA Enterprise — l'IA déterministe sans LLM (6 min) ⭐
**Séquence exacte :**
1. **Montrez le serveur** : *« Voici l'infrastructure : un serveur standard, sans GPU, sans accès internet — vérifiez le câble réseau, il est débranché. »* (le geste de couper le réseau AVANT de commencer = la preuve de souveraineté) ;
2. **Le test d'hallucination, côte à côte** : posez le même prompt à un LLM public (ou montrez la capture préparée) et à KA Enterprise : *« Document : "Le contrat avec le fournisseur X est signé le 12 mars." Question : quelle est la date du contrat ? »* → LLM : répond (ou invente) · KA : **« 12 mars » + la citation du document source affichée à l'écran** ;
3. **Le test du « je ne sais pas »** : posez une question absente des documents : KA répond **« je ne sais pas »** — affichez-le ; *« C'est la réponse la plus importante de la démo : une IA qui admet ne pas savoir est une IA que les banques et les ministères peuvent utiliser. »* ;
4. **Le déterminisme** : posez 3 fois la même question → 3 réponses **identiques, caractère par caractère** ;
5. **Les benchmarks en direct** : math 50 questions (montrez 10 en direct, latence ~5 ms), code 20 (1-2 exemples), raisonnement (1) ;
6. **La phrase de bascule** : *« Pas de GPU, pas de cloud, pas de donnée qui sort, pas d'hallucination, et la même réponse à chaque fois. C'est ça, l'IA souveraine : elle ne dépend de rien. »*

### 0:08–0:12 — DÉMO 2 : VITAL KA — la preuve de production (4 min)
**Version flash (4 étapes, déjà rodée) :**
1. Mode avion → diagnostic offline (30 s) → ordonnance QR ;
2. Wallet UM : *« Ce projet tourne avec MTN Cameroun : 200 pharmacies, MoU en cours. Voici la preuve que la pile vit déjà dans votre écosystème. »* ;
3. Synchronisation quand le réseau revient (2 s) ;
4. **La phrase de bascule** : *« La démo 1 est notre capacité. Celle-ci est notre réalité terrain : la même IA, en production, chez vous, au Cameroun. »*

### 0:12–0:15 — DÉMO 3 : Compression HCV — l'économie du réseau (3 min)
1. Prenez un fichier de démonstration (vidéo ou bundle) → compressez en direct → affichez le ratio mesuré ;
2. *« 2-10× sur les flux réels, latence < 2 ms, zéro terminal modifié. Sur les données publiques du groupe : 150-300 M$/an d'économies potentielles. Ce n'est pas une promesse : le benchmark est là, il tourne devant vous. »* ;
3. **La phrase de bascule** : *« Une seule pile : l'IA qui ne dépend de rien, la santé qui marche sans réseau, le réseau qui coûte moins cher. Trois démos, un moteur. »*

### 0:15–0:18 — LA DEMANDE (3 min)
**Présentez les 3 décisions demandées :**

| # | Décision | Détail |
|---|---|---|
| 1 | **POC 90 jours** sur un cas client MTN réel (banque, assurance ou État) | KA Enterprise sur leur serveur, leurs données, KPI mesurés : exactitude, déterminisme, latence, coût vs LLM |
| 2 | **Validation tierce en parallèle** | Corpus standard + laboratoire indépendant (budget : inclus dans notre plan) |
| 3 | **Feu vert accord-cadre** | Licence continentale + équité minoritaire ≤ 25 %, valorisation avant résultats du POC — le cadre présenté par votre conseil |

**La phrase finale :**
> *« Le PDG a dit que l'Afrique peut avoir sa propre technologie. Elle est sur cette table, débranchée d'internet, en train de répondre. Donnez-nous 90 jours et un cas client : si les KPI ne sont pas au rendez-vous, vous n'avez rien perdu. S'ils y sont, l'Afrique a son IA — et MTN l'a lancée. »*

### 0:18–0:20 — Questions et prochaines étapes (2 min)
- Répondez **par les démos, pas par la théorie** : chaque question = « montrons-le » si possible ;
- **Avant de partir** : le nom du sponsor du POC, la date de la réunion de cadrage (sous 2 semaines), le cas client candidat.

---

## Les objections techniques probables (avec réponses)

| Objection | Réponse |
|---|---|
| **« Comment ça marche sans LLM ? »** | *« La réponse est retrouvée par résonance dans vos documents, pas générée token par token. C'est ce qui garantit le déterminisme — et c'est ce qui rend le "je ne sais pas" possible. Les fondements mathématiques font l'objet d'un document séparé, si vous le souhaitez. »* (proposer le document, ne pas le débiter) |
| **« Vos benchmarks sont faits maison. »** | *« Exact — c'est pour ça que le POC et la validation tierce sont notre demande, pas notre excuse. Votre équipe choisit les corpus. »* |
| **« Ça scale ? »** | *« Les latences mesurées (5 ms) sont en émulateur CPU. Le scale se fait par distribution sur serveurs standard — et la trajectoire matérielle (FPGA) est documentée, à valider avec votre équipe. On ne vend pas la trajectoire : on vend la mesure d'aujourd'hui. »* |
| **« Le coût d'intégration ? »** | *« Inclus dans le POC : votre serveur, notre équipe, 90 jours. L'intégration d'un LLM aujourd'hui coûte plus cher et ne garantit pas le déterminisme. »* |
| **« Pourquoi MTN, pourquoi maintenant ? »** | *« Parce que vous avez le PDG qui veut l'IA africaine, les 16 marchés, et les clients. Orange et les banques panafricaines cherchent la même chose. Le premier à prouver gagne le standard. »* |
| **« Et la Ligne Compute / les datacenters ? »** | *« C'est dans la roadmap, pas dans la démo. Quand l'accélérateur sera mesuré, vous aurez le droit de priorité sur vos datacenters. Aujourd'hui, ce qui compte, c'est ce qui tourne sur cette table. »* |

## Les 5 messages clés (à répéter sous toutes les formes)

1. **« Débranchée d'internet »** — la souveraineté se démontre, elle ne se déclare pas ;
2. **« Le "je ne sais pas" est notre meilleure réponse »** — le déterminisme est la confiance ;
3. **« Une pile, trois démos »** — IA + santé + réseau, un seul moteur ;
4. **« C'est déjà chez vous »** — le pilote santé Cameroun tourne dans l'écosystème MTN ;
5. **« 90 jours, un cas client, vos KPI »** — la demande est mesurable, pas une promesse.

## Checklist avant la réunion

- [ ] NDA signé (avant toute démo)
- [ ] Serveur testé 2 fois le matin même : KA Enterprise + benchmarks + fichier compression
- [ ] **Réseau débranché pendant la démo 1** (le geste de la souveraineté) — prévoir le fallback si le serveur exige une licence en ligne (licence offline pré-configurée)
- [ ] Capture du test d'hallucination LLM vs KA prête (au cas où la connexion LLM ne marche pas en réunion)
- [ ] One-pager PDG + accord-cadre (version résumée) imprimés
- [ ] Le nom du sponsor IA du groupe vérifié + son prénom (utilisé en réunion)
- [ ] 10 questions de test math/code/raisonnement choisies et vérifiées

## Après la réunion (T+2 h max)

1. **Email de synthèse** : les 3 démos (captures à l'appui), les 3 décisions demandées rappelées, la date de cadrage POC proposée ;
2. **Suivre la validation tierce** (proposer 3 laboratoires/corpus au choix de leur équipe) ;
3. **Transmettre l'accord-cadre** à leur conseil (version annotée, annexe A en interne seulement) ;
4. **Mettre à jour le dossier Cameroun** : le POC MTN et le pilote santé doivent rester synchronisés (mêmes benchmarks, mêmes KPI).

---
*Déroulé aligné sur le one-pager PDG et l'accord-cadre. Durée totale : 20 min, sans slides — les démos sont la présentation.*
