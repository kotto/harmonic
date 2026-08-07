# KA CARE — Dépistage Médical Communautaire Harmonique

**Outil de santé pour zones à infrastructure médicale limitée.**

🫀 Fonctionne **sans Internet**. Uniquement avec un smartphone standard.
📡 Fondé sur la **Théorie de l'Univers Harmonique** (constantes φ, π, e, √2, √3, √5).
🏥 Conforme aux protocoles **OMS** (IMCI, ETAT).

---

## 🚀 Démarrage rapide

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
python ka_care.py
```

→ Ouvrir `http://localhost:8700` sur le téléphone ou l'ordinateur.

Pour installer comme PWA : ouvrir dans Chrome → Menu → « Ajouter à l'écran d'accueil ».

---

## 🧰 Outils de dépistage

| Outil | Cible | Protocole OMS |
|-------|-------|---------------|
| **Pneumonie** | Enfant < 5 ans | IMCI — respiration rapide, tirage |
| **Déshydratation** | Enfant | IMCI — pli cutané, yeux, soif, TRC |
| **Syndrome fébrile** | Tout âge | Détection harmonique (FC, HRV, FR) |
| **Anémie** | Tout âge | Pâleur palmaire/conjonctivale |
| **Nouveau-né** | 0-28 jours | 7 signes de danger OMS |

---

## 📡 API

Tous les endpoints sont en `POST /api/screen/<outil>` et `POST /api/assess`.

Voir `ka_care.py` pour la documentation complète des endpoints.

---

## 🌍 Déploiement terrain

### Option 1 : Raspberry Pi / vieux laptop
```bash
python ka_care.py
# Le serveur est accessible sur le réseau local WiFi
# Les téléphones des agents de santé se connectent via WiFi
```

### Option 2 : Téléphone Android (Pydroid)
1. Installer Pydroid 3
2. Installer Flask et flask-cors via pip dans Pydroid
3. Ouvrir `ka_care.py` dans Pydroid → Exécuter
4. Ouvrir `http://localhost:8700` dans Chrome Android
5. Ajouter à l'écran d'accueil

### Option 3 : Déploiement cloud (si Internet disponible)
Compatible Render, Railway, Fly.io, Heroku.
```bash
# Render: définir la commande de démarrage
gunicorn ka_care:app --bind 0.0.0.0:$PORT
```

---

## ⚠ Avertissement

**KA CARE n'est pas un dispositif médical certifié.**

C'est un outil d'aide au dépistage destiné aux agents de santé communautaire.
Toute décision médicale doit être validée par un professionnel de santé qualifié.

Les algorithmes de détection sont fondés sur les critères OMS/IMCI et
l'analyse harmonique. Ils n'ont pas fait l'objet d'une validation clinique
indépendante à ce jour.

---

## 📄 Licence

Tous droits réservés — Kotto Alain — Juillet 2026.

Développé dans le cadre de la Théorie de l'Univers Harmonique.
