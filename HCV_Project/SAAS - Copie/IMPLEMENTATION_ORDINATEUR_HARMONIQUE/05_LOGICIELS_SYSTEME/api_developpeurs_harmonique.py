"""
🚀 API DÉVELOPPEURS HARMONIQUE
Fichier: api_developpeurs_harmonique.py
Auteur: Équipe Harmonique
Date: 28 avril 2026
Description: API RESTful complète pour les développeurs utilisant l'ordinateur harmonique
             avec endpoints quantiques, documentation interactive et monitoring
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
import asyncio
import time
import uuid
import hashlib
import secrets
import json
import logging
import numpy as np
from datetime import datetime, timedelta
import jwt
from contextlib import asynccontextmanager

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import des composants harmoniques
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '02_ARCHITECTURE_QUANTIQUE'))
from hbits_geometriques import HbitGeometrique, RegistreHarmonique, PatternGeometrique
from circuits_harmoniques import BibliothequeCircuits, CircuitHarmonique, TypeCircuit
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '03_ALGORITHMES_HARMONIQUES'))
from factorisation_harmonique import FactorisationHarmonique
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '01_FONDEMENTS_MATHÉMATIQUES'))
from constantes_harmoniques import CONSTANTES
from matrice_projection import MatriceProjection

# Import des applications
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '06_APPLICATIONS_PILOTES'))
from cryptographie_quantique_harmonique import CryptographieHarmonique, ProtocoleCrypto
from simulation_medicale_harmonique import SimulateurMoleculaireHarmonique

# Configuration
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Stockage en mémoire (à remplacer par une base de données en production)
utilisateurs_db = {}
sessions_actives = {}
calculs_en_cours = {}
resultats_calculs = {}

# Modèles Pydantic
class HbitConfig(BaseModel):
    """Configuration d'un Hbit"""
    pattern: str = Field(..., description="Pattern géométrique (spirale, cercle, helice, miroir, trinite)")
    amplitude: float = Field(1.0, ge=0.0, le=2.0, description="Amplitude de l'Hbit")
    phase: float = Field(0.0, ge=0.0, le=6.283, description="Phase de l'Hbit")
    
    @validator('pattern')
    def validate_pattern(cls, v):
        patterns_valides = ['spirale', 'cercle', 'helice', 'miroir', 'trinite']
        if v.lower() not in patterns_valides:
            raise ValueError(f"Pattern doit être un de: {patterns_valides}")
        return v.lower()

class RegistreConfig(BaseModel):
    """Configuration d'un registre harmonique"""
    nombre_hbits: int = Field(8, ge=1, le=16, description="Nombre d'Hbits dans le registre")
    hbits: Optional[List[HbitConfig]] = Field(None, description="Configuration individuelle des Hbits")

class CircuitConfig(BaseModel):
    """Configuration d'un circuit harmonique"""
    type_circuit: str = Field(..., description="Type de circuit (factorisation, simulation, optimisation, cryptographie)")
    parametres: Optional[Dict[str, Any]] = Field(None, description="Paramètres spécifiques au circuit")

class CalculRequest(BaseModel):
    """Requête de calcul quantique"""
    id_session: str = Field(..., description="Identifiant de session")
    type_calcul: str = Field(..., description="Type de calcul (circuit, factorisation, cryptographie, simulation)")
    registre: RegistreConfig = Field(..., description="Configuration du registre")
    circuit: Optional[CircuitConfig] = Field(None, description="Configuration du circuit")
    parametres: Optional[Dict[str, Any]] = Field(None, description="Paramètres additionnels")

class UtilisateurCreate(BaseModel):
    """Création d'utilisateur"""
    nom_utilisateur: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    mot_de_passe: str = Field(..., min_length=8)

class UtilisateurLogin(BaseModel):
    """Connexion d'utilisateur"""
    nom_utilisateur: str = Field(...)
    mot_de_passe: str = Field(...)

class TokenResponse(BaseModel):
    """Réponse de token"""
    access_token: str
    token_type: str
    expires_in: int

class CalculResponse(BaseModel):
    """Réponse de calcul"""
    id_calcul: str
    statut: str
    resultat: Optional[Dict[str, Any]] = None
    erreur: Optional[str] = None
    temps_execution: Optional[float] = None

# Gestion du cycle de vie de l'API
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du démarrage et arrêt de l'API"""
    logger.info("🚀 Démarrage de l'API Harmonique")
    yield
    logger.info("🛑 Arrêt de l'API Harmonique")

# Initialisation de FastAPI
app = FastAPI(
    title="🌊 API Harmonique - Ordinateur Quantique Harmonique",
    description="""
    ## API Révolutionnaire pour l'Ordinateur Quantique Harmonique
    
    Cette API permet aux développeurs d'accéder à la puissance de l'ordinateur harmonique
    avec des endpoints quantiques, des visualisations 3D/4D et des applications spécialisées.
    
    ### Fonctionnalités principales:
    - 🔧 **Configuration de Hbits**: Patterns géométriques quantiques
    - ⚡ **Circuits harmoniques**: Algorithmes quantiques optimisés
    - 🔐 **Cryptographie quantique**: Génération de clés et chiffrement
    - 🧬 **Simulation médicale**: Modélisation moléculaire quantique
    - 📊 **Monitoring**: Performance et métriques en temps réel
    
    ### Constantes harmoniques intégrées:
    - φ (phi): Nombre d'or ≈ 1.618033988749895
    - π (pi): ≈ 3.141592653589793
    - e: ≈ 2.718281828459045
    - √2: ≈ 1.414213562373095
    - √3: ≈ 1.732050807568877
    
    ### Patterns géométriques:
    - **Spirale**: Motif de la spirale dorée φ
    - **Cercle**: Motif circulaire π
    - **Helice**: Motif hélicoïdal e
    - **Miroir**: Motif miroir √2
    - **Trinité**: Motif trinité √3
    """,
    version="1.0.0",
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
    lifespan=lifespan
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À configurer en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sécurité
security = HTTPBearer()

# Services harmoniques
class ServiceHarmonique:
    """Service principal pour les opérations harmoniques"""
    
    def __init__(self):
        self.registres_actifs = {}
        self.circuits_actifs = {}
        self.crypto_service = CryptographieHarmonique()
        self.simulation_service = SimulateurMoleculaireHarmonique()
        
    async def creer_registre(self, config: RegistreConfig) -> str:
        """Crée un nouveau registre harmonique"""
        try:
            id_registre = str(uuid.uuid4())
            registre = RegistreHarmonique(config.nombre_hbits)
            
            # Configuration individuelle des Hbits si spécifiée
            if config.hbits:
                for i, hbit_config in enumerate(config.hbits[:config.nombre_hbits]):
                    if i < len(registre.qubits):
                        hbit = registre.qubits[i]
                        # Application de la configuration
                        pattern_map = {
                            'spirale': PatternGeometrique.SPIRALE,
                            'cercle': PatternGeometrique.CERCLE,
                            'helice': PatternGeometrique.HELICE,
                            'miroir': PatternGeometrique.MIROIR,
                            'trinite': PatternGeometrique.TRINITE
                        }
                        hbit.pattern = pattern_map.get(hbit_config.pattern, PatternGeometrique.SPIRALE)
                        hbit.amplitude = hbit_config.amplitude
                        hbit.phase = hbit_config.phase
            
            self.registres_actifs[id_registre] = registre
            logger.info(f"Registre {id_registre} créé avec {config.nombre_hbits} Hbits")
            return id_registre
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du registre: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur création registre: {str(e)}")
    
    async def executer_circuit(self, id_registre: str, config: CircuitConfig) -> Dict[str, Any]:
        """Exécute un circuit harmonique"""
        try:
            if id_registre not in self.registres_actifs:
                raise HTTPException(status_code=404, detail="Registre non trouvé")
            
            registre = self.registres_actifs[id_registre]
            bibliotheque = BibliothequeCircuits()
            
            # Création du circuit selon le type
            if config.type_circuit == "factorisation":
                circuit = bibliotheque.creer_circuit_factorisation(registre)
            elif config.type_circuit == "simulation":
                circuit = bibliotheque.creer_circuit_simulation(registre)
            elif config.type_circuit == "optimisation":
                circuit = bibliotheque.creer_circuit_optimisation(registre)
            elif config.type_circuit == "cryptographie":
                circuit = bibliotheque.creer_circuit_cryptographie(registre)
            else:
                raise HTTPException(status_code=400, detail=f"Type de circuit inconnu: {config.type_circuit}")
            
            # Exécution du circuit
            temps_debut = time.time()
            resultats = circuit.executer()
            temps_execution = time.time() - temps_debut
            
            # Mesure des résultats
            mesures = registre.mesurer()
            
            return {
                "resultats": resultats,
                "mesures": mesures,
                "temps_execution": temps_execution,
                "nombre_etapes": len(circuit.etapes),
                "type_circuit": config.type_circuit
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du circuit: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur exécution circuit: {str(e)}")
    
    async def factoriser_nombre(self, nombre: int, id_registre: str) -> Dict[str, Any]:
        """Factorise un nombre avec l'algorithme harmonique"""
        try:
            if id_registre not in self.registres_actifs:
                raise HTTPException(status_code=404, detail="Registre non trouvé")
            
            registre = self.registres_actifs[id_registre]
            factorisation = FactorisationHarmonique(registre)
            
            temps_debut = time.time()
            facteurs = factorisation.factoriser(nombre)
            temps_execution = time.time() - temps_debut
            
            return {
                "nombre_original": nombre,
                "facteurs": facteurs,
                "temps_execution": temps_execution,
                "algorithme": "harmonique_shor"
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la factorisation: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur factorisation: {str(e)}")
    
    async def generer_cle_quantique(self, protocole: str = "harmonique", longueur: int = 256) -> Dict[str, Any]:
        """Génère une clé quantique"""
        try:
            if protocole == "harmonique":
                cle = self.crypto_service.generateur.generer_sequence_quantique(longueur)
            else:
                from cryptographie_quantique_harmonique import ProtocoleDistributionQuantique
                protocole_dist = ProtocoleDistributionQuantique(self.crypto_service.generateur)
                
                if protocole == "bb84":
                    cle_quantique = protocole_dist.executer_bb84(longueur)
                else:
                    cle_quantique = protocole_dist.executer_harmonique(longueur)
                
                if cle_quantique:
                    cle = cle_quantique.vers_hex()
                else:
                    raise HTTPException(status_code=500, detail="Échec génération clé")
            
            return {
                "cle": cle if isinstance(cle, str) else "générée",
                "protocole": protocole,
                "longueur": longueur,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de clé: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur génération clé: {str(e)}")
    
    async def simuler_molecule(self, molecules_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simule des molécules"""
        try:
            # Configuration de la simulation
            for mol_config in molecules_config:
                if mol_config.get("type") == "eau":
                    from simulation_medicale_harmonique import creer_molecule_eau
                    molecule = creer_molecule_eau()
                elif mol_config.get("type") == "medicament":
                    from simulation_medicale_harmonique import creer_molecule_medicament
                    molecule = creer_molecule_medicament()
                elif mol_config.get("type") == "proteine":
                    from simulation_medicale_harmonique import creer_proteine_simplifiee
                    molecule = creer_proteine_simplifiee()
                else:
                    continue
                
                self.simulation_service.ajouter_molecule(molecule)
            
            # Exécution de la simulation
            self.simulation_service.calculer_interactions()
            self.simulation_service.dynamique_moleculaire(pas=50)
            
            # Analyse des résultats
            stats = self.simulation_service.obtenir_statistiques()
            energies = self.simulation_service.analyser_energetique()
            
            return {
                "statistiques": stats,
                "energies": energies,
                "temps_simulation": self.simulation_service.temps_simulation
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la simulation moléculaire: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur simulation: {str(e)}")

# Instance du service
service_harmonique = ServiceHarmonique()

# Fonctions utilitaires
def creer_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crée un token d'accès JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verifier_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Vérifie le token JWT"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        nom_utilisateur: str = payload.get("sub")
        if nom_utilisateur is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        return nom_utilisateur
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalide")

# Endpoints d'authentification
@app.post(f"{API_PREFIX}/auth/inscription", response_model=dict)
async def inscription(utilisateur: UtilisateurCreate):
    """Inscription d'un nouvel utilisateur"""
    try:
        if utilisateur.nom_utilisateur in utilisateurs_db:
            raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà utilisé")
        
        # Hash du mot de passe
        mot_de_passe_hash = hashlib.sha256(utilisateur.mot_de_passe.encode()).hexdigest()
        
        # Stockage de l'utilisateur
        utilisateurs_db[utilisateur.nom_utilisateur] = {
            "nom_utilisateur": utilisateur.nom_utilisateur,
            "email": utilisateur.email,
            "mot_de_passe_hash": mot_de_passe_hash,
            "date_creation": datetime.utcnow().isoformat(),
            "quota_calculs": 100,
            "calculs_utilises": 0
        }
        
        logger.info(f"Utilisateur {utilisateur.nom_utilisateur} inscrit")
        return {"message": "Utilisateur créé avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'inscription: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

@app.post(f"{API_PREFIX}/auth/connexion", response_model=TokenResponse)
async def connexion(utilisateur: UtilisateurLogin):
    """Connexion d'un utilisateur"""
    try:
        if utilisateur.nom_utilisateur not in utilisateurs_db:
            raise HTTPException(status_code=401, detail="Identifiants invalides")
        
        utilisateur_db = utilisateurs_db[utilisateur.nom_utilisateur]
        mot_de_passe_hash = hashlib.sha256(utilisateur.mot_de_passe.encode()).hexdigest()
        
        if mot_de_passe_hash != utilisateur_db["mot_de_passe_hash"]:
            raise HTTPException(status_code=401, detail="Identifiants invalides")
        
        # Création du token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = creer_access_token(
            data={"sub": utilisateur.nom_utilisateur}, 
            expires_delta=access_token_expires
        )
        
        # Stockage de la session
        id_session = str(uuid.uuid4())
        sessions_actives[id_session] = {
            "nom_utilisateur": utilisateur.nom_utilisateur,
            "date_connexion": datetime.utcnow().isoformat(),
            "token": access_token
        }
        
        logger.info(f"Utilisateur {utilisateur.nom_utilisateur} connecté")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la connexion: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

# Endpoints principaux
@app.get(f"{API_PREFIX}/constantes")
async def obtenir_constantes():
    """Retourne les constantes harmoniques fondamentales"""
    return {
        "phi": {
            "valeur": CONSTANTES['phi'],
            "description": "Nombre d'or",
            "formule": "(1 + √5) / 2"
        },
        "pi": {
            "valeur": CONSTANTES['pi'],
            "description": "Constante du cercle",
            "formule": "Circonférence / Diamètre"
        },
        "e": {
            "valeur": CONSTANTES['e'],
            "description": "Nombre d'Euler",
            "formule": "lim(n→∞) (1 + 1/n)ⁿ"
        },
        "sqrt2": {
            "valeur": CONSTANTES['sqrt2'],
            "description": "Racine carrée de 2",
            "formule": "√2"
        },
        "sqrt3": {
            "valeur": CONSTANTES['sqrt3'],
            "description": "Racine carrée de 3",
            "formule": "√3"
        }
    }

@app.get(f"{API_PREFIX}/patterns")
async def obtenir_patterns():
    """Retourne les patterns géométriques disponibles"""
    return {
        "patterns": {
            "spirale": {
                "nom": "Spirale dorée",
                "constante": "φ",
                "description": "Motif basé sur la spirale logarithmique du nombre d'or"
            },
            "cercle": {
                "nom": "Cercle",
                "constante": "π",
                "description": "Motif circulaire basé sur la constante pi"
            },
            "helice": {
                "nom": "Helice",
                "constante": "e",
                "description": "Motif hélicoïdal basé sur la constante d'Euler"
            },
            "miroir": {
                "nom": "Miroir",
                "constante": "√2",
                "description": "Motif de symétrie basé sur la racine carrée de 2"
            },
            "trinite": {
                "nom": "Trinité",
                "constante": "√3",
                "description": "Motif trinitaire basé sur la racine carrée de 3"
            }
        }
    }

@app.post(f"{API_PREFIX}/registres/creer")
async def creer_registre(config: RegistreConfig, nom_utilisateur: str = Depends(verifier_token)):
    """Crée un nouveau registre harmonique"""
    try:
        # Vérification du quota
        utilisateur_db = utilisateurs_db[nom_utilisateur]
        if utilisateur_db["calculs_utilises"] >= utilisateur_db["quota_calculs"]:
            raise HTTPException(status_code=429, detail="Quota de calculs dépassé")
        
        id_registre = await service_harmonique.creer_registre(config)
        
        return {
            "id_registre": id_registre,
            "message": "Registre créé avec succès",
            "nombre_hbits": config.nombre_hbits
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la création du registre: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

@app.post(f"{API_PREFIX}/calculs/executer")
async def executer_calcul(request: CalculRequest, background_tasks: BackgroundTasks, nom_utilisateur: str = Depends(verifier_token)):
    """Exécute un calcul quantique"""
    try:
        # Vérification du quota
        utilisateur_db = utilisateurs_db[nom_utilisateur]
        if utilisateur_db["calculs_utilises"] >= utilisateur_db["quota_calculs"]:
            raise HTTPException(status_code=429, detail="Quota de calculs dépassé")
        
        # Génération de l'ID de calcul
        id_calcul = str(uuid.uuid4())
        
        # Stockage du calcul
        calculs_en_cours[id_calcul] = {
            "id_session": request.id_session,
            "type_calcul": request.type_calcul,
            "statut": "en_attente",
            "date_creation": datetime.utcnow().isoformat(),
            "nom_utilisateur": nom_utilisateur
        }
        
        # Exécution en arrière-plan
        background_tasks.add_task(executer_calcul_background, id_calcul, request)
        
        # Mise à jour du quota
        utilisateur_db["calculs_utilises"] += 1
        
        return {
            "id_calcul": id_calcul,
            "statut": "soumis",
            "message": "Calcul soumis avec succès"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la soumission du calcul: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

async def executer_calcul_background(id_calcul: str, request: CalculRequest):
    """Exécution en arrière-plan d'un calcul"""
    try:
        # Mise à jour du statut
        calculs_en_cours[id_calcul]["statut"] = "en_execution"
        calculs_en_cours[id_calcul]["debut_execution"] = datetime.utcnow().isoformat()
        
        resultat = None
        erreur = None
        
        # Exécution selon le type de calcul
        if request.type_calcul == "circuit":
            # Création du registre
            id_registre = await service_harmonique.creer_registre(request.registre)
            
            # Exécution du circuit
            if request.circuit:
                resultat = await service_harmonique.executer_circuit(id_registre, request.circuit)
            else:
                erreur = "Configuration de circuit manquante"
                
        elif request.type_calcul == "factorisation":
            nombre = request.parametres.get("nombre", 15) if request.parametres else 15
            id_registre = await service_harmonique.creer_registre(request.registre)
            resultat = await service_harmonique.factoriser_nombre(nombre, id_registre)
            
        elif request.type_calcul == "cryptographie":
            protocole = request.parametres.get("protocole", "harmonique") if request.parametres else "harmonique"
            longueur = request.parametres.get("longueur", 256) if request.parametres else 256
            resultat = await service_harmonique.generer_cle_quantique(protocole, longueur)
            
        elif request.type_calcul == "simulation":
            molecules = request.parametres.get("molecules", []) if request.parametres else []
            resultat = await service_harmonique.simuler_molecule(molecules)
            
        else:
            erreur = f"Type de calcul inconnu: {request.type_calcul}"
        
        # Stockage du résultat
        temps_execution = None
        if "debut_execution" in calculs_en_cours[id_calcul]:
            debut = datetime.fromisoformat(calculs_en_cours[id_calcul]["debut_execution"])
            temps_execution = (datetime.utcnow() - debut).total_seconds()
        
        resultats_calculs[id_calcul] = {
            "id_calcul": id_calcul,
            "statut": "termine" if not erreur else "erreur",
            "resultat": resultat,
            "erreur": erreur,
            "temps_execution": temps_execution,
            "date_fin": datetime.utcnow().isoformat()
        }
        
        # Nettoyage des calculs en cours
        if id_calcul in calculs_en_cours:
            del calculs_en_cours[id_calcul]
        
        logger.info(f"Calcul {id_calcul} terminé")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du calcul {id_calcul}: {e}")
        
        resultats_calculs[id_calcul] = {
            "id_calcul": id_calcul,
            "statut": "erreur",
            "erreur": str(e),
            "date_fin": datetime.utcnow().isoformat()
        }

@app.get(f"{API_PREFIX}/calculs/{{id_calcul}}/statut")
async def obtenir_statut_calcul(id_calcul: str, nom_utilisateur: str = Depends(verifier_token)):
    """Obtient le statut d'un calcul"""
    try:
        # Vérification des calculs en cours
        if id_calcul in calculs_en_cours:
            calcul = calculs_en_cours[id_calcul]
            if calcul["nom_utilisateur"] != nom_utilisateur:
                raise HTTPException(status_code=403, detail="Accès non autorisé")
            
            return {
                "id_calcul": id_calcul,
                "statut": calcul["statut"],
                "type_calcul": calcul["type_calcul"],
                "date_creation": calcul["date_creation"]
            }
        
        # Vérification des résultats
        elif id_calcul in resultats_calculs:
            resultat = resultats_calculs[id_calcul]
            return resultat
        
        else:
            raise HTTPException(status_code=404, detail="Calcul non trouvé")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'obtention du statut: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

@app.get(f"{API_PREFIX}/calculs")
async def lister_calculs(nom_utilisateur: str = Depends(verifier_token)):
    """Liste les calculs de l'utilisateur"""
    try:
        calculs_utilisateur = []
        
        # Calculs en cours
        for id_calcul, calcul in calculs_en_cours.items():
            if calcul["nom_utilisateur"] == nom_utilisateur:
                calculs_utilisateur.append({
                    "id_calcul": id_calcul,
                    "statut": calcul["statut"],
                    "type_calcul": calcul["type_calcul"],
                    "date_creation": calcul["date_creation"]
                })
        
        # Calculs terminés
        for id_calcul, resultat in resultats_calculs.items():
            if id_calcul not in [c["id_calcul"] for c in calculs_utilisateur]:
                calculs_utilisateur.append({
                    "id_calcul": id_calcul,
                    "statut": resultat["statut"],
                    "type_calcul": resultat.get("type_calcul", "inconnu"),
                    "date_creation": resultat.get("date_creation", resultat.get("date_fin"))
                })
        
        return {
            "calculs": calculs_utilisateur,
            "total": len(calculs_utilisateur)
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la liste des calculs: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

@app.get(f"{API_PREFIX}/systeme/statistiques")
async def obtenir_statistiques_systeme():
    """Retourne les statistiques du système"""
    try:
        return {
            "constantes_harmoniques": CONSTANTES,
            "calculs_en_cours": len(calculs_en_cours),
            "calculs_termines": len(resultats_calculs),
            "utilisateurs_actifs": len(sessions_actives),
            "registres_actifs": len(service_harmonique.registres_actifs),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'obtention des statistiques: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")

@app.get(f"{API_PREFIX}/systeme/sante")
async def sante_systeme():
    """Vérifie la santé du système"""
    try:
        # Tests de santé
        tests = {
            "constantes": CONSTANTES is not None,
            "service_harmonique": service_harmonique is not None,
            "crypto_service": service_harmonique.crypto_service is not None,
            "simulation_service": service_harmonique.simulation_service is not None
        }
        
        tous_healthy = all(tests.values())
        
        return {
            "statut": "healthy" if tous_healthy else "unhealthy",
            "tests": tests,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de santé: {e}")
        return {
            "statut": "unhealthy",
            "erreur": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Endpoint de streaming pour les calculs en temps réel
@app.get(f"{API_PREFIX}/calculs/{{id_calcul}}/stream")
async def stream_calcul(id_calcul: str, nom_utilisateur: str = Depends(verifier_token)):
    """Stream en temps réel d'un calcul"""
    async def generer_stream():
        try:
            # Vérification des droits
            if id_calcul in calculs_en_cours:
                if calculs_en_cours[id_calcul]["nom_utilisateur"] != nom_utilisateur:
                    yield f"data: {json.dumps({'erreur': 'Accès non autorisé'})}\n\n"
                    return
            elif id_calcul not in resultats_calculs:
                yield f"data: {json.dumps({'erreur': 'Calcul non trouvé'})}\n\n"
                return
            
            # Envoi des mises à jour
            dernier_statut = None
            while True:
                statut_actuel = None
                
                if id_calcul in calculs_en_cours:
                    statut_actuel = calculs_en_cours[id_calcul]["statut"]
                elif id_calcul in resultats_calculs:
                    statut_actuel = resultats_calculs[id_calcul]["statut"]
                
                if statut_actuel and statut_actuel != dernier_statut:
                    data = {
                        "id_calcul": id_calcul,
                        "statut": statut_actuel,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    dernier_statut = statut_actuel
                
                # Arrêt si le calcul est terminé
                if statut_actuel in ["termine", "erreur"]:
                    break
                
                await asyncio.sleep(1)
                
        except Exception as e:
            error_data = {"erreur": str(e), "timestamp": datetime.utcnow().isoformat()}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generer_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

# Point d'entrée pour le développement
if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Démarrage de l'API Harmonique en mode développement")
    
    uvicorn.run(
        "api_developpeurs_harmonique:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
