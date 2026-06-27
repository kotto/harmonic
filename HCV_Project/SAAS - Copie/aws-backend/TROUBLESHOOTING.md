# 🔧 Dépannage - HCV-PRO-PROJECT

## Problèmes Courants et Solutions

---

## 1. Le Serveur ne Démarre pas

### Symptôme
```
Error: Address already in use
ou
Error: Python not found
```

### Solutions

#### Solution 1: Vérifier Python
```bash
python --version
```
Si Python n'est pas trouvé, installez-le depuis https://www.python.org

#### Solution 2: Vérifier le Port 3000
```bash
# Windows
netstat -ano | findstr :3000

# Linux/Mac
lsof -i :3000
```

Si le port est utilisé, arrêtez le processus ou changez le port dans `server/hcv_pro_server.py`:
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001)  # Changez 3000 en 3001
```

#### Solution 3: Réinstaller les Dépendances
```bash
pip install -r requirements.txt --force-reinstall
```

---

## 2. Erreur "Module not found"

### Symptôme
```
ModuleNotFoundError: No module named 'flask'
ou
ModuleNotFoundError: No module named 'zstandard'
```

### Solutions

#### Solution 1: Installer les Dépendances
```bash
pip install -r requirements.txt
```

#### Solution 2: Vérifier l'Installation
```bash
pip list | grep Flask
pip list | grep numpy
pip list | grep opencv
pip list | grep zstandard
```

#### Solution 3: Réinstaller Complètement
```bash
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

---

## 3. Erreur de Connexion

### Symptôme
```
Connection refused
ou
Cannot connect to localhost:3000
```

### Solutions

#### Solution 1: Vérifier que le Serveur est en Cours d'Exécution
```bash
curl http://localhost:3000/api/health
```

#### Solution 2: Essayer une Autre Adresse
```bash
# Essayer 127.0.0.1 au lieu de localhost
curl http://127.0.0.1:3000/api/health

# Essayer l'adresse IP locale
curl http://192.168.1.190:3000/api/health
```

#### Solution 3: Vérifier le Pare-feu
- Assurez-vous que le port 3000 n'est pas bloqué par le pare-feu
- Ajoutez une exception pour Python si nécessaire

---

## 4. Erreur "Address already in use"

### Symptôme
```
OSError: [Errno 48] Address already in use
ou
OSError: [Errno 98] Address already in use
```

### Solutions

#### Solution 1: Trouver et Arrêter le Processus

**Windows**:
```bash
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Linux/Mac**:
```bash
lsof -i :3000
kill -9 <PID>
```

#### Solution 2: Utiliser un Port Différent
Modifiez `server/hcv_pro_server.py`:
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001)  # Utilisez 3001 au lieu de 3000
```

---

## 5. Erreur "Permission denied"

### Symptôme
```
PermissionError: [Errno 13] Permission denied
```

### Solutions

#### Solution 1: Exécuter en Tant qu'Administrateur

**Windows**:
- Clic droit sur CMD/PowerShell
- Sélectionnez "Exécuter en tant qu'administrateur"

**Linux/Mac**:
```bash
sudo python server/hcv_pro_server.py
```

#### Solution 2: Vérifier les Permissions des Fichiers
```bash
# Linux/Mac
chmod +x start.sh
chmod 755 server/hcv_pro_server.py
```

---

## 6. Erreur "SSL: CERTIFICATE_VERIFY_FAILED"

### Symptôme
```
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

### Solutions

#### Solution 1: Désactiver la Vérification SSL (Développement Uniquement)
```bash
pip install --upgrade certifi
```

#### Solution 2: Configurer les Certificats
```bash
# macOS
/Applications/Python\ 3.x/Install\ Certificates.command
```

---

## 7. Erreur "Out of Memory"

### Symptôme
```
MemoryError
ou
Killed (processus arrêté)
```

### Solutions

#### Solution 1: Réduire la Taille des Fichiers
- Testez avec des fichiers plus petits
- Compressez les fichiers avant de les traiter

#### Solution 2: Augmenter la Mémoire Disponible
- Fermez les autres applications
- Redémarrez l'ordinateur

#### Solution 3: Optimiser le Code
- Utilisez le streaming pour les gros fichiers
- Implémentez le garbage collection

---

## 8. Erreur "Timeout"

### Symptôme
```
Timeout waiting for response
ou
Request timeout
```

### Solutions

#### Solution 1: Augmenter le Timeout
```bash
# Avec curl
curl --max-time 300 http://localhost:3000/api/health
```

#### Solution 2: Vérifier la Performance
- Vérifiez l'utilisation du CPU
- Vérifiez l'utilisation de la mémoire
- Vérifiez la vitesse du disque

#### Solution 3: Réduire la Taille des Fichiers
- Testez avec des fichiers plus petits
- Compressez les fichiers avant de les traiter

---

## 9. Erreur "File not found"

### Symptôme
```
FileNotFoundError: [Errno 2] No such file or directory
```

### Solutions

#### Solution 1: Vérifier le Chemin du Fichier
```bash
# Vérifier que le fichier existe
ls -la server/hcv_pro_server.py
```

#### Solution 2: Vérifier le Répertoire de Travail
```bash
# Vérifier le répertoire courant
pwd

# Changer vers le répertoire du projet
cd HCV-PRO-PROJECT
```

#### Solution 3: Utiliser des Chemins Absolus
```python
import os
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
```

---

## 10. Erreur "Codec Error"

### Symptôme
```
CodecError
ou
Compression failed
```

### Solutions

#### Solution 1: Vérifier le Format du Fichier
- Assurez-vous que le fichier est dans le bon format
- Vérifiez que le fichier n'est pas corrompu

#### Solution 2: Vérifier les Dépendances
```bash
pip install -r requirements.txt --force-reinstall
```

#### Solution 3: Consulter les Logs
- Vérifiez les logs du serveur
- Recherchez les messages d'erreur détaillés

---

## 11. Erreur "CORS Error"

### Symptôme
```
Access to XMLHttpRequest blocked by CORS policy
```

### Solutions

#### Solution 1: Configurer CORS
Modifiez `server/hcv_pro_server.py`:
```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
```

#### Solution 2: Installer flask-cors
```bash
pip install flask-cors
```

---

## 12. Erreur "JSON Decode Error"

### Symptôme
```
JSONDecodeError: Expecting value
```

### Solutions

#### Solution 1: Vérifier le Format JSON
```bash
# Vérifier que la réponse est du JSON valide
curl http://localhost:3000/api/health | python -m json.tool
```

#### Solution 2: Vérifier les Headers
```bash
# Vérifier que le Content-Type est application/json
curl -i http://localhost:3000/api/health
```

---

## 13. Erreur "OpenCV Error"

### Symptôme
```
cv2.error: OpenCV(4.8.0)
```

### Solutions

#### Solution 1: Réinstaller OpenCV
```bash
pip uninstall opencv-python -y
pip install opencv-python==4.8.0.74
```

#### Solution 2: Vérifier la Compatibilité
```bash
python -c "import cv2; print(cv2.__version__)"
```

---

## 14. Erreur "NumPy Error"

### Symptôme
```
numpy.error
ou
ValueError: operands could not be broadcast together
```

### Solutions

#### Solution 1: Vérifier la Version de NumPy
```bash
python -c "import numpy; print(numpy.__version__)"
```

#### Solution 2: Réinstaller NumPy
```bash
pip uninstall numpy -y
pip install numpy==1.24.3
```

---

## 15. Erreur "Werkzeug Error"

### Symptôme
```
werkzeug.exceptions.BadRequest
```

### Solutions

#### Solution 1: Vérifier les Paramètres de la Requête
- Assurez-vous que les paramètres sont corrects
- Vérifiez le format des données

#### Solution 2: Vérifier les Headers
```bash
# Vérifier que le Content-Type est correct
curl -H "Content-Type: application/json" http://localhost:3000/api/health
```

---

## 🆘 Besoin d'Aide?

### Vérifications Rapides
1. ✅ Vérifier que Python est installé: `python --version`
2. ✅ Vérifier que les dépendances sont installées: `pip list`
3. ✅ Vérifier que le serveur est en cours d'exécution: `curl http://localhost:3000/api/health`
4. ✅ Vérifier que le port 3000 est disponible: `netstat -ano | findstr :3000`

### Ressources
- **START.md** - Guide de démarrage
- **VERIFICATION_REPORT.md** - Rapport de vérification
- **README.md** - Documentation générale
- **docs/DOCUMENT_FINAL_HCV_PRO.md** - Documentation technique

### Commandes Utiles
```bash
# Réinstaller complètement
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# Vérifier la santé du serveur
curl http://localhost:3000/api/health

# Voir l'historique
curl http://localhost:3000/api/history

# Arrêter le serveur
Ctrl+C
```

---

**Dernière mise à jour**: 17 Avril 2026  
**Statut**: ✅ Opérationnel
