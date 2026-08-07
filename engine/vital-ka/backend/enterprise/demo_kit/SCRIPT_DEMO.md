# 🎬 SCRIPT DE DÉMO — 15 minutes qui vendent

Vertical : **cabinets comptables & d'expertise** · Outils : portail `/onboard`,
dashboard admin, `run_demo.py` (automatisé) · Durée : 15 min.

## Préparation (avant le client)

1. VPS de démo avec KA Enterprise lancé (`http://VOTRE_VPS:8767`).
2. Ouvrir le portail `/onboard` — l'écran d'accueil.
3. Avoir le dataset de démo sous la main (il se charge en 1 clic dans le
   dashboard, carte « 🎬 Démo commerciale » — `POST /api/enterprise/demo/load`).
4. **En visio : partagez l'écran, faites taper le client lui-même.**

## Déroulé

### 0 · Accroche (1 min)
> « Vous avez déjà essayé de poser une question sur vos dossiers à ChatGPT ?
> Il répond — souvent faux. Nous avons construit l'inverse. Je vous montre. »

### 1 · Onboarding — le client crée SON entreprise (2 min)
Faites-lui remplir : nom du cabinet, description (« cabinet d'expertise
comptable qui gère la comptabilité, la paie et la fiscalité de ses clients »).
→ Les hologrammes proposés apparaissent.
> « Regardez : votre environnement est analysé, et les départements de savoir
> sont créés automatiquement. En 5 minutes, votre IA est née. »

### 2 · Charger la démo (1 clic)
Dashboard → « 🎬 Démo commerciale » → « Charger la démo ».
12 clients, 12 factures, la paie, le bilan, les procédures — ingérés.

### 3 · Les chiffres (2 min) — tapez vous-même :
- « combien de clients actifs avons-nous ? » → **10**
- « chiffre d'affaires total des clients actifs ? » → **3 668 000 €**
- « liste des factures en retard » → **3 lignes**
- « montant total des factures en retard ? » → **40 600 €**
> « Calculé sur vos chiffres réels, colonne par colonne. Pas d'estimation. »

### 4 · La connaissance (1 min)
- « quelles sont les échéances de TVA à respecter ? » → la réponse vient des
  procédures internes ingérées.

### 5 · ÉTANCHÉITÉ (1 min)
- Posez la question de procédures au département comptabilité → **il refuse**.
- Reposez-la au bon département → **il répond**.
> « Chaque département est étanche. Le comptable ne voit pas les procédures,
> le service client ne voit pas les salaires. »

### 6 · LE MOMENT — la question piège (2 min)
- « quelle est la couleur du paradis fiscal ? »
- KA Enterprise : **« Je ne trouve pas cette information »**.
> « ChatGPT vous aurait répondu quelque chose de plausible — et de faux.
> Nous, nous refusons. Lequel voulez-vous pour votre conformité ? »

### 7 · Les documents (2 min)
- « rédige un email aux clients en retard de paiement » → email complet.
- Téléchargez le .docx.
> « Vos collaborateurs gagnent des heures chaque semaine. »

### 8 · L'auto-apprentissage (2 min)
- Posez 3 fois une question sans réponse → dashboard « 🔄 Auto-apprentissage » :
  l'IA s'enrichit automatiquement (Wikipedia + facettes manquantes).
> « Plus vous l'utilisez, plus elle devient compétente. Elle apprend de vos
> vraies questions. »

### 9 · La clôture (1 min)
> « Tout tourne sur votre VPS à 20 €/mois. Vos données ne sortent jamais de
> chez vous. C'est 49 €/mois. On fait l'essai 14 jours ? »

## Version automatisée
`python run_demo.py --onboard "Cabinet Test" admin@cabinet.fr --base http://VOTRE_VPS:8767`
→ exécute tout le parcours avec les arguments de vente affichés (utile pour
se préparer, enregistrer une vidéo, ou en démo technique).

## Pièges à éviter
- Ne jamais dire « l'IA comprend tout » — dire « elle répond sur ce que
  vous lui avez donné, et elle vous le dit quand elle ne sait pas ».
- Toujours faire taper le client (l'effet « c'est MOI qui pose »).
- Ne pas montrer le chaînon D sur des sujets fictifs (démo comptable) —
  le montrer sur un sujet réel (ex. pharmacologie) ou expliquer la mécanique.
