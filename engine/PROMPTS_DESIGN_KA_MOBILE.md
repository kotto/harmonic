# Prompts de Design — KA Mobile

## À soumettre à une IA experte en design frontend (v0, Lovable, Bolt, etc.)

---

## Prompt 1 — Écran d'Accueil

```
Crée l'écran d'accueil de KA Mobile, un compagnon personnel qui vit dans le téléphone.
100% local, 0 cloud, gratuit.

ÉLÉMENTS :
1. Une sphère 3D animée au centre (représente KA — mystérieuse, dorée, pulsative)
   - iframe vers /ka_sphere.html, dans un cercle de 120px
2. Message de bienvenue : "KA — votre compagnon harmonique"
   Sous-titre discret : "100% local · Zéro cloud · Gratuit"
3. Deux rangées de 2 cartes :
   - 🖼️ Média — "Compresser vos photos" (fonction PHARE, bordure or)
   - 💬 Compagnon — "Conversation + Voix"
   - 🤖 Agent — "Tâches autonomes"
   - 👤 Contacts — "Répertoire"
4. Footer minimal : "📱 KA Mobile v4 · φ · 100% local"
5. Barre de navigation en bas : 🏠 Accueil | 💬 Compagnon | 🖼️ Média | 🤖 Agent | 👤 Contacts

STYLE : épuré, premium, sombre (#0a0a0f), or (#c9a84c) comme accent.
Pas de stats, pas de théorie, pas de liens externes. Juste le compagnon.
```

---

## Prompt 2 — Écran Média (Compression Photo)

```
Crée l'écran "Média" de KA Mobile — la fonction PHARE.
Compresse les photos/vidéos jusqu'à 64:1 sans perte visible.

L'écran doit avoir :

1. Dashboard stockage en haut :
   - Jauge circulaire ou barre horizontale
   - "112 Go utilisés" → "22 Go après KA" → "90 Go économisés (80%)"
   - Rafraîchissement automatique via navigator.storage.estimate()

2. Deux boutons d'action :
   - "🗜️ Compresser tout" (bouton principal, or)
   - "📤 Choisir des fichiers" (bouton secondaire)

3. Grille d'outils complémentaires :
   - 🔍 Upscaler ×2/×4
   - ✨ Restaurer (déflouter, débruiter)

4. Zone "Avant/Après" avec preview des photos traitées
   - Compteur : "📸 1 247 photos | 🎥 83 vidéos"
   - Miniatures avec ratio (ex: "6.2 Mo → 220 Ko — 28:1")

5. Activité récente (journal des compressions)

Style premium, dark, or comme accent. Animations fluides.
```

---

## Prompt 3 — Écran Compagnon (Chat + Voix)

```
Crée l'écran de conversation du compagnon KA.

C'est un ami qui parle, pas un chatbot. Il a 10 émotions vocales, de la mémoire,
et fonctionne sans Internet.

L'écran doit avoir :

1. En-tête :
   - Avatar KA : petite sphère animée (20px, or)
   - Nom "KA" avec indicateur d'émotion active (ex: 🤗 Chaleureux)
   - Sélecteur d'émotion discret (menu déroulant 10 options)

2. Zone de messages :
   - Bulles KA : fond sombre, alignées à gauche, avec avatar
   - Bulles utilisateur : fond or, alignées à droite
   - Timestamps légers
   - Animation d'apparition fluide
   - Bouton 🔊 pour réécouter le message en voix

3. Barre de saisie :
   - Champ texte "Écrivez votre message..."
   - Bouton micro pour dictée vocale
   - Bouton envoi ➤

4. Suggestions rapides (chips) :
   "Raconte-moi une blague" | "Quel temps fait-il ?" | "Résume ma journée"

Style : conversationnel, chaleureux. L'interface doit donner envie de parler.
Pas de jargon technique. Pas de "prompt engineering". Juste une conversation.
```

---

## Prompt 4 — Écran Agent

```
Crée l'écran "Agent" de KA Mobile. KA exécute des tâches de façon autonome.

L'écran doit avoir :

1. Zone de commande :
   - "Que voulez-vous que KA fasse ?"
   - Champ texte + bouton ▶️
   - Chips : "📧 Vérifie mes messages" | "📞 Appelle Maman" | "⏰ Rappelle-moi..."

2. Liste des tâches (en cours / terminées) :
   - Chaque tâche = carte avec :
     - Icône, titre, barre de progression ou statut
     - Timestamp, bouton annuler si en cours
   - Animation quand une tâche se termine

3. Mini-dashboard Téléphone :
   - 4 compteurs cliquables :
     👤 Contacts | 💬 Messages | ⏰ Rappels | 📞 Appels

4. Historique récent (compact)

Style : organisé, efficace, professionnel mais chaleureux.
```

---

## Prompt 5 — Écran Contacts

```
Crée l'écran "Contacts" de KA Mobile. Un répertoire intelligent.

L'écran doit avoir :

1. Barre de recherche en haut
2. Liste de contacts avec :
   - Avatar (initiales dans cercle coloré)
   - Nom, téléphone
   - Icône si voix clonée disponible 🎵
   - Boutons rapides : 📞 Appeler | 💬 Message
3. Bouton "+" pour ajouter un contact
4. Option "Cloner la voix" si 3s d'audio disponible

Style : épuré, lisible, conforme aux guidelines iOS/Android.
```

---

## Spécifications Globales

```
Application : KA Mobile — Compagnon Harmonique
Type : PWA (iOS Safari + Android Chrome)
Écrans : Accueil, Compagnon, Média, Agent, Contacts (5 écrans)

COULEURS :
  Fond          : #0a0a0f (noir profond)
  Surface       : #14141f
  Surface alt   : #1a1a2e
  Or (accent)   : #c9a84c
  Or clair      : #e6d088
  Vert succès   : #00d2a0
  Rouge erreur  : #e74c3c
  Texte         : #d4c8a0
  Texte muted   : #8b7b60
  Bordures      : #2a2a3a

TYPOGRAPHIE :
  Inter (corps, 400-600)
  JetBrains Mono (chiffres, 500)
  Tailles : caption 0.65rem → headline 1.5rem

COMPOSANTS :
  Cards : border-radius 12-16px, fond surface, bordure subtile
  Boutons : primary (fond or), outline (bordure or), ghost (transparent)
  Chips : boutons arrondis 20px, suggestions
  Progress bars : animées, couleur or
  Navigation bar : 5 icônes, fixée en bas, glassmorphism

IDENTITÉ :
  La sphère KA est le SEUL élément visuel distinctif.
  Mystérieuse, dorée, animée lentement. Jamais statique.
  Pas de mascotte. Pas de logo complexe. Juste la sphère.

ANIMATIONS :
  fade-in + slide-up (nouveaux éléments)
  scale (interactions tactiles)
  transitions 0.3s cubic-bezier
  skeleton loaders (chargement)

ACCESSIBILITÉ :
  Contraste ≥ 4.5:1
  Touch targets ≥ 44px
  Support VoiceOver/TalkBack
```

---

## Ce qu'il ne faut SURTOUT PAS

```
❌ Pas de mentions de KA Enterprise ou KA PC
❌ Pas de formules mathématiques (α=1/137)
❌ Pas de jargon technique (φ-orthogonalité, ℂ⁵¹²)
❌ Pas de liens vers GitHub ou documentation
❌ Pas de "produits" ou "versions"
❌ Pas de stats (110K faits, etc.)
❌ Pas de code, pas de store, pas de mémoire holographique

✅ Juste un compagnon qui vit dans le téléphone.
✅ La compression photo comme porte d'entrée.
✅ La voix et les émotions comme cœur de l'expérience.
✅ La sphère comme unique élément d'identité visuelle.
```
