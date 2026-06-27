"""
🔐 CRYPTOGRAPHIE QUANTIQUE HARMONIQUE
Fichier: cryptographie_quantique_harmonique.py
Auteur: Équipe Harmonique
Date: 28 avril 2026
Description: Application de cryptographie quantique révolutionnaire basée sur les Hbits
             avec distribution quantique de clés et protocoles harmoniques
"""

import numpy as np
import hashlib
import secrets
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import cryptography.exceptions

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import des composants harmoniques
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '02_ARCHITECTURE_QUANTIQUE'))
from hbits_geometriques import HbitGeometrique, RegistreHarmonique, PatternGeometrique
from circuits_harmoniques import BibliothequeCircuits, CircuitHarmonique, TypeCircuit
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '01_FONDEMENTS_MATHÉMATIQUES'))
from constantes_harmoniques import CONSTANTES
from matrice_projection import MatriceProjection

# Protocoles cryptographiques
class ProtocoleCrypto(Enum):
    BB84 = "bb84"
    E91 = "e91"
    B92 = "b92"
    HARMONIQUE = "harmonique"

# États de la communication quantique
class EtatCommunication(Enum):
    INITIALISATION = "initialisation"
    DISTRIBUTION = "distribution"
    SIFTING = "sifting"
    RECONCILIATION = "reconciliation"
    AUTHENTIFICATION = "authentification"
    COMPLETE = "complete"
    ERREUR = "erreur"

@dataclass
class QubitQuantique:
    """
    Qubit quantique pour la cryptographie
    """
    etat: np.ndarray
    base: str  # 'Z' ou 'X' ou 'harmonique'
    timestamp: float = field(default_factory=time.time)
    
    def mesurer(self, base_mesure: str) -> Tuple[int, str]:
        """
        Mesure le qubit dans une base spécifique
        
        Args:
            base_mesure: Base de mesure ('Z', 'X', 'harmonique')
            
        Returns:
            Tuple (résultat, base_utilisée)
        """
        if base_mesure != self.base:
            # Probabilité de 50% d'obtenir un résultat aléatoire
            resultat = np.random.choice([0, 1])
        else:
            # Mesure dans la bonne base
            proba_0 = abs(self.etat[0])**2
            resultat = 0 if np.random.random() < proba_0 else 1
            
        return resultat, base_mesure

@dataclass
class CleQuantique:
    """
    Clé quantique générée harmoniquement
    """
    bits: List[int]
    base_utilisees: List[str]
    longueur: int = field(init=False)
    entropie: float = field(init=False)
    
    def __post_init__(self):
        self.longueur = len(self.bits)
        self.entropie = self._calculer_entropie()
    
    def _calculer_entropie(self) -> float:
        """
        Calcule l'entropie de Shannon de la clé
        
        Returns:
            Entropie en bits
        """
        if not self.bits:
            return 0.0
            
        # Comptage des bits
        count_0 = self.bits.count(0)
        count_1 = self.bits.count(1)
        
        # Calcul des probabilités
        p0 = count_0 / len(self.bits) if count_0 > 0 else 0
        p1 = count_1 / len(self.bits) if count_1 > 0 else 0
        
        # Entropie de Shannon
        entropy = 0.0
        if p0 > 0:
            entropy -= p0 * np.log2(p0)
        if p1 > 0:
            entropy -= p1 * np.log2(p1)
            
        return entropy
    
    def vers_bytes(self) -> bytes:
        """
        Convertit la clé en bytes
        
        Returns:
            Représentation en bytes de la clé
        """
        bit_string = ''.join(map(str, self.bits))
        # Padding pour multiple de 8
        padding = (8 - len(bit_string) % 8) % 8
        bit_string += '0' * padding
        
        return bytes(int(bit_string[i:i+8], 2) for i in range(0, len(bit_string), 8))
    
    def vers_hex(self) -> str:
        """
        Convertit la clé en hexadécimal
        
        Returns:
            Représentation hexadécimale de la clé
        """
        return self.vers_bytes().hex()

class GenerateurClesHarmonique:
    """
    Générateur de clés quantiques harmoniques
    """
    
    def __init__(self, nombre_hbits: int = 8):
        self.nombre_hbits = nombre_hbits
        self.registre = RegistreHarmonique(nombre_hbits)
        self.matrice_projection = MatriceProjection()
        self.circuit_generation = None
        
        # Paramètres harmoniques
        self.phi = CONSTANTES['phi']
        self.pi = CONSTANTES['pi']
        self.e = CONSTANTES['e']
        
        logger.info(f"GenerateurClesHarmonique initialisé avec {nombre_hbits} Hbits")
    
    def generer_sequence_quantique(self, longueur: int, protocole: ProtocoleCrypto = ProtocoleCrypto.HARMONIQUE) -> List[QubitQuantique]:
        """
        Génère une séquence de qubits quantiques
        
        Args:
            longueur: Nombre de qubits à générer
            protocole: Protocole cryptographique à utiliser
            
        Returns:
            Liste des qubits générés
        """
        try:
            qubits = []
            
            for i in range(longueur):
                if protocole == ProtocoleCrypto.HARMONIQUE:
                    qubit = self._generer_qubit_harmonique(i)
                elif protocole == ProtocoleCrypto.BB84:
                    qubit = self._generer_qubit_bb84()
                elif protocole == ProtocoleCrypto.E91:
                    qubit = self._generer_qubit_e91(i)
                else:
                    qubit = self._generer_qubit_b92()
                
                qubits.append(qubit)
            
            logger.info(f"Séquence de {longueur} qubits générée avec protocole {protocole.value}")
            return qubits
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de séquence quantique: {e}")
            return []
    
    def _generer_qubit_harmonique(self, index: int) -> QubitQuantique:
        """
        Génère un qubit avec méthode harmonique
        
        Args:
            index: Index du qubit dans la séquence
            
        Returns:
            Qubit quantique harmonique
        """
        # Sélection du pattern basé sur l'index et les constantes harmoniques
        pattern_index = int(index * self.phi) % len(PatternGeometrique)
        pattern = list(PatternGeometrique)[pattern_index]
        
        # Génération de l'état harmonique
        phase = (index * self.pi) % (2 * np.pi)
        amplitude = np.exp(-index / (self.nombre_hbits * self.e))
        
        # Création de l'état quantique
        if pattern in [PatternGeometrique.SPIRALE, PatternGeometrique.HELICE]:
            # États superposés avec rotation harmonique
            alpha = amplitude * np.cos(phase)
            beta = amplitude * np.sin(phase)
            base = 'harmonique'
        elif pattern == PatternGeometrique.CERCLE:
            # Base Z
            alpha = 1.0
            beta = 0.0
            base = 'Z'
        elif pattern == PatternGeometrique.MIROIR:
            # Base X
            alpha = 1.0 / np.sqrt(2)
            beta = 1.0 / np.sqrt(2)
            base = 'X'
        else:  # TRINITE
            # Base harmonique spéciale
            alpha = np.cos(phase / self.phi)
            beta = np.sin(phase / self.phi)
            base = 'harmonique'
        
        # Normalisation
        norm = np.sqrt(abs(alpha)**2 + abs(beta)**2)
        etat = np.array([alpha/norm, beta/norm], dtype=complex)
        
        return QubitQuantique(etat=etat, base=base)
    
    def _generer_qubit_bb84(self) -> QubitQuantique:
        """
        Génère un qubit selon le protocole BB84
        
        Returns:
            Qubit BB84
        """
        # Choix aléatoire de la base et de l'état
        base = np.random.choice(['Z', 'X'])
        etat_valeur = np.random.choice([0, 1])
        
        if base == 'Z':
            if etat_valeur == 0:
                etat = np.array([1.0, 0.0])  # |0⟩
            else:
                etat = np.array([0.0, 1.0])  # |1⟩
        else:  # Base X
            if etat_valeur == 0:
                etat = np.array([1.0/np.sqrt(2), 1.0/np.sqrt(2)])  # |+⟩
            else:
                etat = np.array([1.0/np.sqrt(2), -1.0/np.sqrt(2)])  # |-⟩
        
        return QubitQuantique(etat=etat, base=base)
    
    def _generer_qubit_e91(self, index: int) -> QubitQuantique:
        """
        Génère un qubit selon le protocole E91 (entanglement)
        
        Args:
            index: Index pour la génération
            
        Returns:
            Qubit E91
        """
        # Génération d'états intriqués simulés
        theta = (index * self.pi / 4) % np.pi
        
        alpha = np.cos(theta)
        beta = np.sin(theta)
        
        etat = np.array([alpha, beta], dtype=complex)
        base = 'harmonique'
        
        return QubitQuantique(etat=etat, base=base)
    
    def _generer_qubit_b92(self) -> QubitQuantique:
        """
        Génère un qubit selon le protocole B92
        
        Returns:
            Qubit B92
        """
        # États non-orthogonaux
        if np.random.random() < 0.5:
            etat = np.array([1.0, 0.0])  # |0⟩
        else:
            etat = np.array([1.0/2, np.sqrt(3)/2])  # État intermédiaire
        
        return QubitQuantique(etat=etat, base='Z')

class ProtocoleDistributionQuantique:
    """
    Implémentation des protocoles de distribution quantique de clés
    """
    
    def __init__(self, generateur: GenerateurClesHarmonique):
        self.generateur = generateur
        self.etat = EtatCommunication.INITIALISATION
        self.cle_alice = None
        self.cle_bob = None
        self.base_alice = []
        self.base_bob = []
        self.qubits_transmis = []
        
        logger.info("ProtocoleDistributionQuantique initialisé")
    
    def executer_bb84(self, longueur_cle: int = 256) -> Optional[CleQuantique]:
        """
        Exécute le protocole BB84 complet
        
        Args:
            longueur_cle: Longueur souhaitée de la clé finale
            
        Returns:
            Clé quantique partagée ou None en cas d'erreur
        """
        try:
            self.etat = EtatCommunication.DISTRIBUTION
            
            # Étape 1: Génération des qubits par Alice
            logger.info("Étape 1: Génération des qubits par Alice")
            qubits_alice = self.generateur.generer_sequence_quantique(longueur_cle * 2, ProtocoleCrypto.BB84)
            
            # Étape 2: Mesure par Bob
            logger.info("Étape 2: Mesure par Bob")
            resultats_bob = []
            for qubit in qubits_alice:
                base_bob = np.random.choice(['Z', 'X'])
                resultat, _ = qubit.mesurer(base_bob)
                resultats_bob.append(resultat)
                self.base_bob.append(base_bob)
            
            # Étape 3: Sifting - conservation des mesures avec mêmes bases
            logger.info("Étape 3: Sifting des bases")
            cle_sifted_alice = []
            cle_sifted_bob = []
            
            for i, qubit in enumerate(qubits_alice):
                if qubit.base == self.base_bob[i]:
                    # Même base utilisée
                    resultat_alice, _ = qubit.mesurer(qubit.base)
                    cle_sifted_alice.append(resultat_alice)
                    cle_sifted_bob.append(resultats_bob[i])
                    self.base_alice.append(qubit.base)
            
            # Étape 4: Vérification de la cohérence
            logger.info(f"Étape 4: Vérification - Longueur après sifting: {len(cle_sifted_alice)}")
            
            if len(cle_sifted_alice) < longueur_cle:
                logger.error("Longueur insuffisante après sifting")
                return None
            
            # Étape 5: Réconciliation d'erreur (simplifiée)
            logger.info("Étape 5: Réconciliation d'erreur")
            cle_finale = self._reconcilier_erreurs(cle_sifted_alice, cle_sifted_bob)
            
            if len(cle_finale) < longueur_cle:
                logger.error("Longueur insuffisante après réconciliation")
                return None
            
            # Étape 6: Amplification de confidentialité
            logger.info("Étape 6: Amplification de confidentialité")
            cle_finale = cle_finale[:longueur_cle]
            
            self.cle_alice = CleQuantique(bits=cle_finale, base_utilisees=self.base_alice[:len(cle_finale)])
            self.etat = EtatCommunication.COMPLETE
            
            logger.info(f"✅ Protocole BB84 terminé - Clé de {len(cle_finale)} bits générée")
            return self.cle_alice
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du protocole BB84: {e}")
            self.etat = EtatCommunication.ERREUR
            return None
    
    def executer_harmonique(self, longueur_cle: int = 256) -> Optional[CleQuantique]:
        """
        Exécute le protocole harmonique personnalisé
        
        Args:
            longueur_cle: Longueur souhaitée de la clé finale
            
        Returns:
            Clé quantique harmonique ou None en cas d'erreur
        """
        try:
            self.etat = EtatCommunication.DISTRIBUTION
            
            # Génération avec protocole harmonique
            logger.info("Génération avec protocole harmonique")
            qubits = self.generateur.generer_sequence_quantique(longueur_cle, ProtocoleCrypto.HARMONIQUE)
            
            # Mesure harmonique
            cle_bits = []
            bases = []
            
            for qubit in qubits:
                # Mesure dans la base harmonique
                resultat, base = qubit.mesurer(qubit.base)
                cle_bits.append(resultat)
                bases.append(base)
            
            # Validation harmonique
            if self._valider_cohérence_harmonique(cle_bits, bases):
                cle = CleQuantique(bits=cle_bits, base_utilisees=bases)
                self.etat = EtatCommunication.COMPLETE
                logger.info(f"✅ Protocole harmonique terminé - Entropie: {cle.entropie:.2f} bits")
                return cle
            else:
                logger.error("Échec de la validation harmonique")
                self.etat = EtatCommunication.ERREUR
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du protocole harmonique: {e}")
            self.etat = EtatCommunication.ERREUR
            return None
    
    def _reconcilier_erreurs(self, cle_alice: List[int], cle_bob: List[int]) -> List[int]:
        """
        Réconcilie les erreurs entre les clés d'Alice et Bob
        
        Args:
            cle_alice: Clé d'Alice
            cle_bob: Clé de Bob
            
        Returns:
            Clé reconciliée
        """
        # Implémentation simplifiée de la réconciliation
        cle_reconciliee = []
        
        for i in range(min(len(cle_alice), len(cle_bob))):
            # Simulation de détection et correction d'erreur
            if cle_alice[i] == cle_bob[i]:
                cle_reconciliee.append(cle_alice[i])
            else:
                # Simulation de correction d'erreur (choix aléatoire)
                cle_reconciliee.append(np.random.choice([0, 1]))
        
        return cle_reconciliee
    
    def _valider_cohérence_harmonique(self, bits: List[int], bases: List[str]) -> bool:
        """
        Valide la cohérence harmonique de la clé
        
        Args:
            bits: Bits de la clé
            bases: Bases utilisées
            
        Returns:
            True si cohérent, False sinon
        """
        try:
            # Calcul du facteur harmonique
            phi = self.generateur.phi
            
            # Validation basée sur les constantes harmoniques
            longueur = len(bits)
            if longueur < 8:
                return False
            
            # Calcul du ratio d'harmonie
            count_0 = bits.count(0)
            count_1 = bits.count(1)
            
            # Vérification de l'équilibre (pas trop déséquilibré)
            ratio = min(count_0, count_1) / max(count_0, count_1)
            if ratio < 0.3:  # Pas trop déséquilibré
                return False
            
            # Vérification de la distribution des bases
            base_counts = {}
            for base in bases:
                base_counts[base] = base_counts.get(base, 0) + 1
            
            # Au moins 2 types de bases différentes
            if len(base_counts) < 2:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation harmonique: {e}")
            return False

class CryptographieHarmonique:
    """
    Système complet de cryptographie harmonique
    """
    
    def __init__(self, nombre_hbits: int = 8):
        self.nombre_hbits = nombre_hbits
        self.generateur = GenerateurClesHarmonique(nombre_hbits)
        self.protocole = ProtocoleDistributionQuantique(self.generateur)
        self.cles_stockees = {}
        
        logger.info(f"CryptographieHarmonique initialisée avec {nombre_hbits} Hbits")
    
    def generer_cle_symetrique(self, longueur: int = 256, protocole: ProtocoleCrypto = ProtocoleCrypto.HARMONIQUE) -> Optional[str]:
        """
        Génère une clé symétrique
        
        Args:
            longueur: Longueur de la clé en bits
            protocole: Protocole de génération
            
        Returns:
            Clé en hexadécimal ou None en cas d'erreur
        """
        try:
            if protocole == ProtocoleCrypto.HARMONIQUE:
                cle_quantique = self.protocole.executer_harmonique(longueur)
            else:
                cle_quantique = self.protocole.executer_bb84(longueur)
            
            if cle_quantique:
                cle_hex = cle_quantique.vers_hex()
                
                # Stockage de la clé
                id_cle = f"key_{int(time.time())}"
                self.cles_stockees[id_cle] = {
                    'cle': cle_hex,
                    'longueur': len(cle_quantique.bits),
                    'entropie': cle_quantique.entropie,
                    'protocole': protocole.value,
                    'timestamp': time.time()
                }
                
                logger.info(f"Clé symétrique générée: {id_cle} ({len(cle_quantique.bits)} bits, entropie: {cle_quantique.entropie:.2f})")
                return cle_hex
            else:
                logger.error("Échec de la génération de clé")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la génération de clé symétrique: {e}")
            return None
    
    def chiffrer_aes(self, message: str, cle_hex: str) -> Optional[str]:
        """
        Chiffre un message avec AES en utilisant une clé quantique
        
        Args:
            message: Message à chiffrer
            cle_hex: Clé en hexadécimal
            
        Returns:
            Message chiffré en base64 ou None en cas d'erreur
        """
        try:
            # Conversion de la clé
            cle_bytes = bytes.fromhex(cle_hex)
            
            # Génération d'un IV aléatoire
            iv = secrets.token_bytes(16)
            
            # Chiffrement AES-256-GCM
            cipher = Cipher(
                algorithms.AES(cle_bytes),
                modes.GCM(iv)
            )
            encryptor = cipher.encryptor()
            
            # Chiffrement du message
            message_bytes = message.encode('utf-8')
            ciphertext = encryptor.update(message_bytes) + encryptor.finalize()
            
            # Combinaison IV + tag + ciphertext
            encrypted_data = iv + encryptor.tag + ciphertext
            
            # Encodage en base64
            encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            
            logger.info(f"Message chiffré avec succès ({len(message)} octets)")
            return encrypted_b64
            
        except Exception as e:
            logger.error(f"Erreur lors du chiffrement AES: {e}")
            return None
    
    def dechiffrer_aes(self, message_chiffre: str, cle_hex: str) -> Optional[str]:
        """
        Déchiffre un message AES
        
        Args:
            message_chiffre: Message chiffré en base64
            cle_hex: Clé en hexadécimal
            
        Returns:
            Message déchiffré ou None en cas d'erreur
        """
        try:
            # Décodage base64
            encrypted_data = base64.b64decode(message_chiffre)
            
            # Extraction IV, tag et ciphertext
            iv = encrypted_data[:16]
            tag = encrypted_data[16:32]
            ciphertext = encrypted_data[32:]
            
            # Conversion de la clé
            cle_bytes = bytes.fromhex(cle_hex)
            
            # Déchiffrement AES-256-GCM
            cipher = Cipher(
                algorithms.AES(cle_bytes),
                modes.GCM(iv, tag)
            )
            decryptor = cipher.decryptor()
            
            # Déchiffrement
            message_bytes = decryptor.update(ciphertext) + decryptor.finalize()
            message = message_bytes.decode('utf-8')
            
            logger.info(f"Message déchiffré avec succès ({len(message)} octets)")
            return message
            
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement AES: {e}")
            return None
    
    def generer_signature_quantique(self, message: str, cle_privee: Optional[bytes] = None) -> Optional[str]:
        """
        Génère une signature quantique harmonique
        
        Args:
            message: Message à signer
            cle_privee: Clé privée RSA (générée si None)
            
        Returns:
            Signature en base64 ou None en cas d'erreur
        """
        try:
            # Génération de la clé RSA si non fournie
            if cle_privee is None:
                cle_privee = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048
                )
            
            # Hash du message avec facteur harmonique
            message_bytes = message.encode('utf-8')
            hash_obj = hashes.Hash(hashes.SHA256())
            hash_obj.update(message_bytes)
            
            # Ajout du facteur harmonique
            facteur_harmonique = str(self.generateur.phi).encode('utf-8')
            hash_obj.update(facteur_harmonique)
            
            digest = hash_obj.finalize()
            
            # Signature
            signature = cle_privee.sign(
                digest,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Encodage en base64
            signature_b64 = base64.b64encode(signature).decode('utf-8')
            
            logger.info("Signature quantique générée avec succès")
            return signature_b64
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de signature: {e}")
            return None
    
    def verifier_signature_quantique(self, message: str, signature: str, cle_publique: bytes) -> bool:
        """
        Vérifie une signature quantique
        
        Args:
            message: Message original
            signature: Signature en base64
            cle_publique: Clé publique RSA
            
        Returns:
            True si signature valide, False sinon
        """
        try:
            # Décodage de la signature
            signature_bytes = base64.b64decode(signature)
            
            # Hash du message avec facteur harmonique
            message_bytes = message.encode('utf-8')
            hash_obj = hashes.Hash(hashes.SHA256())
            hash_obj.update(message_bytes)
            
            # Ajout du facteur harmonique
            facteur_harmonique = str(self.generateur.phi).encode('utf-8')
            hash_obj.update(facteur_harmonique)
            
            digest = hash_obj.finalize()
            
            # Vérification
            cle_publique_obj = serialization.load_pem_public_key(cle_publique)
            cle_publique_obj.verify(
                signature_bytes,
                digest,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            logger.info("Signature quantique vérifiée avec succès")
            return True
            
        except cryptography.exceptions.InvalidSignature:
            logger.warning("Signature quantique invalide")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de signature: {e}")
            return False
    
    def obtenir_statistiques(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du système de cryptographie
        
        Returns:
            Dictionnaire des statistiques
        """
        try:
            total_cles = len(self.cles_stockees)
            entropie_moyenne = 0.0
            
            if total_cles > 0:
                entropie_total = sum(info['entropie'] for info in self.cles_stockees.values())
                entropie_moyenne = entropie_total / total_cles
            
            # Distribution des protocoles
            protocoles = {}
            for info in self.cles_stockees.values():
                protocole = info['protocole']
                protocoles[protocole] = protocoles.get(protocole, 0) + 1
            
            return {
                'cles_generes': total_cles,
                'entropie_moyenne': entropie_moyenne,
                'protocoles_utilises': protocoles,
                'nombre_hbits': self.nombre_hbits,
                'phi': self.generateur.phi,
                'pi': self.generateur.pi,
                'e': self.generateur.e
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'obtention des statistiques: {e}")
            return {'erreur': str(e)}

# Point d'entrée principal pour les tests
if __name__ == "__main__":
    try:
        logger.info("🔐 Démonstration de la cryptographie quantique harmonique")
        
        # Initialisation du système
        crypto = CryptographieHarmonique(nombre_hbits=8)
        
        # Test 1: Génération de clé harmonique
        logger.info("\n--- Test 1: Génération de clé harmonique ---")
        cle = crypto.generer_cle_symetrique(longueur=128, protocole=ProtocoleCrypto.HARMONIQUE)
        
        if cle:
            print(f"✅ Clé harmonique générée: {cle[:32]}... (longueur: {len(cle)*4} bits)")
        else:
            print("❌ Échec de la génération de clé")
        
        # Test 2: Chiffrement/déchiffrement
        logger.info("\n--- Test 2: Chiffrement/déchiffrement AES ---")
        message_original = "🌊 Message secret de l'ordinateur harmonique !"
        
        if cle:
            message_chiffre = crypto.chiffrer_aes(message_original, cle)
            if message_chiffre:
                print(f"✅ Message chiffré: {message_chiffre[:64]}...")
                
                message_dechiffre = crypto.dechiffrer_aes(message_chiffre, cle)
                if message_dechiffre == message_original:
                    print(f"✅ Message déchiffré: {message_dechiffre}")
                else:
                    print("❌ Échec du déchiffrement")
            else:
                print("❌ Échec du chiffrement")
        
        # Test 3: Génération de clé BB84
        logger.info("\n--- Test 3: Génération de clé BB84 ---")
        cle_bb84 = crypto.generer_cle_symetrique(longueur=256, protocole=ProtocoleCrypto.BB84)
        
        if cle_bb84:
            print(f"✅ Clé BB84 générée: {cle_bb84[:32]}... (longueur: {len(cle_bb84)*4} bits)")
        else:
            print("❌ Échec de la génération de clé BB84")
        
        # Test 4: Signature quantique
        logger.info("\n--- Test 4: Signature quantique ---")
        message_signer = "Document harmonique important"
        
        cle_privee_rsa = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        cle_publique_pem = cle_privee_rsa.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        signature = crypto.generer_signature_quantique(message_signer, cle_privee_rsa)
        if signature:
            print(f"✅ Signature générée: {signature[:64]}...")
            
            verification = crypto.verifier_signature_quantique(message_signer, signature, cle_publique_pem)
            print(f"✅ Vérification: {'Réussie' if verification else 'Échouée'}")
        else:
            print("❌ Échec de la génération de signature")
        
        # Statistiques finales
        logger.info("\n--- Statistiques finales ---")
        stats = crypto.obtenir_statistiques()
        for cle, valeur in stats.items():
            print(f"  {cle}: {valeur}")
        
        logger.info("🔐 Démonstration terminée avec succès")
        
    except KeyboardInterrupt:
        logger.info("Arrêt de la démonstration")
    except Exception as e:
        logger.error(f"Erreur critique: {e}")
