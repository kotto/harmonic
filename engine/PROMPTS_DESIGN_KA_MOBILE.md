# Prompts de Design — KA Mobile

## À soumettre à une IA experte en design frontend (v0, Lovable, Bolt, etc.)

---

## Prompt 1 — Écran d'Accueil / Dashboard

```
Crée l'écran d'accueil d'une application mobile PWA appelée "KA".
C'est un compagnon IA qui fonctionne 100% localement sur le téléphone.

L'écran doit afficher :
1. Un message de bienvenue personnalisé : "Bonjour [prénom], prêt à libérer de l'espace ?"
2. Une carte "Stockage" avec :
   - Espace utilisé (ex: 87 Go) → après KA (ex: 17 Go)
   - Barre de progression montrant l'espace économisé
   - Bouton "Compresser mes photos"
3. Une carte "Compagnon" avec :
   - Dernière conversation (extrait)
   - Bouton "Parler à KA"
4. Une carte "Aujourd'hui" avec :
   - Rappels du jour
   - Tâches agent en cours
5. Barre de navigation en bas avec 5 icônes : Accueil, Chat, Média, Agent, Profil

Style :
- Thème sombre luxueux (fond #0a0a0f)
- Couleur accent : or (#c9a84c) pour les éléments importants
- Typographie : Inter pour le texte, JetBrains Mono pour les chiffres
- Design mobile-first, pas de scroll horizontal
- Transitions fluides (cubic-bezier)
- Compatible PWA (ajout à l'écran d'accueil)
```

---

## Prompt 2 — Écran Média (Compression Photo/Vidéo)

```
Crée l'écran "Média" de KA Mobile — la fonction PHARE de l'application.

Cet écran permet de compresser les photos et vidéos du téléphone jusqu'à 64:1
sans perte de qualité visible, grâce à la technologie HCV (Harmonic Compression).

L'écran doit contenir :

1. Un indicateur de stockage en haut :
   - Jauge circulaire ou barre horizontale
   - "112 Go utilisés" → "22 Go après KA" → "90 Go économisés (80%)"
   - Animation de la barre qui se remplit quand l'utilisateur arrive

2. Un compteur de fichiers :
   - "📸 1 247 photos" | "🎥 83 vidéos" | "📄 156 documents"
   - Chaque compteur est cliquable pour filtrer

3. Deux boutons d'action principaux :
   - "🗜️ Compresser tout" (bouton large, style primary, or)
   - "📤 Choisir des fichiers" (bouton outline)
   - Animation de progression pendant la compression

4. Une grille de miniatures "Avant/Après" :
   - 3-4 exemples de photos déjà compressées
   - Slider pour comparer avant/après (glisser pour voir la différence)
   - Indicateur de ratio (ex: "6.2 Mo → 220 Ko (28:1)")

5. Section "Autres outils" :
   - 🔍 Upscaler ×2/×4
   - ✨ Restaurer (déflouter)
   - 🎨 Coloriser (photos N&B)

6. Un compteur "Économies totales" en bas :
   - "Vous avez économisé 90 Go et 36€/an d'iCloud depuis que vous utilisez KA"

Style : premium, luxueux, dark theme, or comme accent, animations fluides.
```

---

## Prompt 3 — Écran Chat / Compagnon

```
Crée l'écran de conversation du compagnon KA.

C'est un chat avec une IA qui a de la personnalité, de la mémoire, et 10 émotions
vocales. Tout fonctionne localement sur le téléphone.

L'écran doit avoir :

1. En-tête avec :
   - Avatar de KA (cercle avec dégradé or)
   - Nom "KA" et statut "● En ligne" ou "💭 En train d'écrire..."
   - Indicateur d'émotion active (ex: 🤗 Chaleureux)
   - Bouton pour changer l'émotion

2. Zone de messages :
   - Bulles KA : fond sombre (#1a1a2e), texte clair, aligné à gauche
   - Bulles utilisateur : fond or (#c9a84c), texte sombre, aligné à droite
   - Timestamps discrets
   - Avatar KA miniature dans les bulles
   - Animation d'apparition fluide (fade-in + slide-up)
   - Bouton 🔁 pour réécouter le message vocal à côté des bulles KA

3. Barre de saisie en bas :
   - Champ texte avec placeholder "Écrivez votre message..."
   - Bouton micro 🎤 pour dictée vocale
   - Bouton envoi ➤ (devient ▶️ stop pendant la lecture audio)
   - Sélecteur d'émotion intégré (petit menu déroulant)

4. Suggestions rapides au-dessus de la barre de saisie :
   - Chips cliquables : "Quel temps fait-il ?", "Raconte-moi une blague", "Résume ma journée"

Style : conversationnel, chaleureux, premium. L'interface doit donner envie de parler.
```

---

## Prompt 4 — Écran Agent (Tâches Autonomes)

```
Crée l'écran "Agent" de KA Mobile — l'écran où KA exécute des tâches de façon
autonome (vérifier les emails, chercher des infos, programmer des rappels...).

L'écran doit avoir :

1. Une zone de commande en haut :
   - "Que voulez-vous que KA fasse ?"
   - Champ texte + bouton ▶️ Exécuter
   - Chips de suggestions : "Vérifie mes messages", "Appelle Maman", "Cherche les news"

2. Liste des tâches en cours / terminées :
   - Chaque tâche = une carte avec :
     - Icône (📧 email, 📞 appel, 🔍 recherche, ⏰ rappel)
     - Titre de la tâche
     - Barre de progression ou statut (⏳ En cours, ✅ Terminé, ❌ Échoué)
     - Timestamp
     - Bouton pour annuler si en cours
   - Animation quand une tâche se termine

3. Mini-dashboard "Téléphone Harmonique" :
   - 4 compteurs : 👤 Contacts | 💬 Messages | ⏰ Rappels | 📞 Appels
   - Chaque compteur cliquable

4. Historique des tâches récentes (compact)

Style : organisé, efficace, professionnel mais chaleureux.
```

---

## Prompt 5 — Écran Profil & Réglages

```
Crée l'écran "Profil" de KA Mobile.

L'écran doit avoir :

1. En-tête avec :
   - Avatar utilisateur (initiales dans un cercle)
   - Nom et email
   - "Membre depuis [date]"

2. Section "Voix" :
   - Voix actuelle de KA (ex: "KA Standard" avec aperçu ▶️)
   - Bouton "Cloner une voix" (enregistrer 3 secondes)
   - Liste des voix clonées
   - Curseur d'émotion par défaut

3. Section "Stockage" :
   - Espace libéré par KA
   - Nombre de photos/vidéos compressées
   - Économies réalisées (€)

4. Section "Vie privée" :
   - "Toutes vos données sont stockées LOCALEMENT"
   - Aucune donnée ne quitte votre téléphone
   - Certificat de confidentialité

5. Section "À propos" :
   - Version de KA
   - Lien vers la documentation
   - "Propulsé par l'architecture harmonique — 0 GPU, 0 cloud"

Style : épuré, premium, rassurant sur la vie privée.
```

---

## Spécifications Globales de Design

```
Application : KA Mobile — Compagnon Harmonique
Type : PWA (Progressive Web App)
Cible : iOS Safari et Android Chrome

Palette de couleurs :
  Fond principal  : #0a0a0f (noir profond)
  Fond surface     : #14141f (gris très foncé)
  Fond surface alt : #1a1a2e (gris bleuté)
  Accent primaire  : #c9a84c (or)
  Accent succès    : #00d2a0 (vert)
  Accent erreur    : #e74c3c (rouge)
  Texte principal  : #e0d6c2 (beige clair)
  Texte secondaire : #a09080 (beige foncé)
  Bordures         : #2a2a3a

Typographie :
  Titres    : Inter, 600 weight
  Corps     : Inter, 400 weight
  Chiffres  : JetBrains Mono, 500 weight
  Tailles   : 0.65rem (caption) à 1.5rem (headline)

Composants réutilisables :
  - Cards avec bordure subtile et border-radius 12-16px
  - Boutons : primary (fond or), secondary (bordure or), ghost (transparent)
  - Chips : petits boutons arrondis pour les suggestions
  - Progress bars : animées, couleur or
  - Badges : compteurs, statuts
  - Navigation bar : fixée en bas, 5 icônes, fond glassmorphism

Animations :
  - fade-in + slide-up pour les nouveaux éléments
  - scale pour les interactions tactiles
  - smooth transitions (0.3s cubic-bezier)
  - skeleton loaders pour le chargement
  - pulse pour les indicateurs d'activité

Accessibilité :
  - Contraste minimum 4.5:1
  - Touch targets minimum 44px
  - Support lecteur d'écran
  - Mode sombre uniquement (économie batterie)
```

---

## Prompt pour l'écran d'accueil de l'app native (quand on passera en natif)

```
Crée l'écran principal d'une application mobile native (iOS/Android) appelée KA.

Cet écran est la première chose que l'utilisateur voit. Il doit IMMÉDIATEMENT
communiquer la proposition de valeur : "Cette app libère de l'espace."

Design :
- Fond noir profond avec particules dorées animées (rappelant l'espace/les ondes)
- Au centre : un cercle qui se remplit comme une jauge de stockage
  - 87% rempli → rouge/orange
  - Après compression : 17% → vert
- Texte en dessous : "112 Go → 22 Go. 90 Go libérés."
- Bouton principal : "Libérer mon espace" (or, large, vibrant)
- En bas : "100% local. 0 cloud. 0€." en petit

Animation :
- Quand l'utilisateur arrive, la jauge passe de 87% à 17% avec une animation fluide
- Les particules dorées tournent lentement
- Le bouton pulse doucement pour inviter à l'action

Style : premium, futuriste mais chaleureux, Apple-esque.
```
