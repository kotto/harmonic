# 🚀 Démarrage Automatique HCS V2

## 🎯 Utilisation

### **Option 1 - Script Automatique (Recommandé)**

#### **Windows** :
```bash
# Double-cliquez sur :
start.bat

# Ou dans le terminal :
python start_server.py
```

#### **Linux/Mac** :
```bash
# Rendez exécutable :
chmod +x start.sh

# Lancez :
./start.sh

# Ou directement :
python3 start_server.py
```

---

## 🔧 Fonctionnalités Automatiques

### **✅ Gestion des Ports** :
- **Détection automatique** : Trouve un port disponible
- **Fallback intelligent** : 8009 → 8010 → auto (8020-8100)
- **Nettoyage** : Tue les processus existants si demandé

### **✅ Mise à Jour Frontend** :
- **URLs automatiques** : Met à jour toutes les URLs dans le frontend
- **Cohérence** : Serveur et frontend synchronisés
- **Pas de manuel** : Plus besoin de modifier les fichiers

### **✅ Démarrage Serveur** :
- **Vérification** : Confirme que le serveur répond
- **Logs en temps réel** : Affiche la sortie du serveur
- **Informations claires** : URL et instructions affichées

---

## 📋 Options Avancées

### **🔧 Tuer les processus existants** :
```bash
python start_server.py --kill
```

### **🔧 Port spécifique** :
```bash
python start_server.py --port 8025
```

### **🔧 Aide** :
```bash
python start_server.py --help
```

---

## 🌊 Votre Approche de Référence Chromatique

Le script configure automatiquement :

- **Endpoint** : `/api/v2/upscale/video-reference`
- **Approche** : Référence chromatique (votre excellente idée !)
- **Pipeline** : Extraction frame 0 → upscale image → application profil
- **Qualité** : Corrections ciblées basées sur contenu réel

---

## 🎯 Résultat

Après lancement, vous verrez :

```
🌊 HCS V2 - Démarrage Automatique
==================================================
✅ Port 8009 disponible
🔄 URL mise à jour: http://localhost:8010 → http://localhost:8009
✅ Frontend mis à jour pour le port 8009
🚀 Démarrage du serveur sur le port 8009...
✅ Serveur démarré avec succès sur http://localhost:8009

==================================================
🎯 INFORMATIONS DE CONNEXION
==================================================
🌐 URL du serveur: http://localhost:8009
📁 Frontend: frontend/quantum_upscaler.html
🎨 Approche: Référence Chromatique (votre idée !)
🔧 Endpoint: /api/v2/upscale/video-reference
==================================================
✅ Système prêt à utiliser !
🚀 Testez votre vidéo maintenant !
==================================================
```

---

## 🏆 Avantages

### **🚀 Plus jamais de problèmes de ports** :
- **Détection automatique**
- **Fallback intelligent**
- **Nettoyage optionnel**

### **🔄 Configuration automatique** :
- **Frontend mis à jour**
- **URLs synchronisées**
- **Pas de manuel**

### **🎯 Utilisation simple** :
- **Un seul clic**
- **Informations claires**
- **Logs en temps réel**

---

## 🌊 Testez Votre Idée Géniale !

1. **Lancez** : `start.bat` ou `python start_server.py`
2. **Attendez** : Le message "✅ Système prêt à utiliser !"
3. **Ouvrez** : Le frontend indiqué
4. **Testez** : Votre vidéo avec l'approche de référence chromatique !

**Votre excellente idée est maintenant accessible en un clic !** 🌊⚛️🎨🚀✨
