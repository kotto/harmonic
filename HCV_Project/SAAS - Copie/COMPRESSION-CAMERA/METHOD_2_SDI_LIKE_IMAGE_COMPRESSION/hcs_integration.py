#!/usr/bin/env python3
"""
INTÉGRATION HCS POUR METHOD_2
Adapte METHOD_2 au serveur API sécurisé HCS
Gère les sessions, l'authentification, et l'audit
"""

from typing import Optional, Dict, Any, Tuple
from sdi_pure_image_compression import SDIPureImageCompressor
from sdi_pure_image_decompressor import SDIPureImageDecompressor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HCSMethod2Adapter:
    """
    Adaptateur pour intégrer METHOD_2 avec le serveur HCS
    Gère les sessions, l'authentification, et les opérations sécurisées
    """
    
    def __init__(self):
        self.active_sessions = {}
        self.compressors = {}
        self.decompressors = {}
    
    def create_session_compressor(self, session_id: str, shared_secret: bytes) -> SDIPureImageCompressor:
        """Crée un compresseur lié à une session HCS"""
        compressor = SDIPureImageCompressor(
            session_id=session_id,
            shared_secret=shared_secret
        )
        self.compressors[session_id] = compressor
        logger.info(f"Compresseur créé pour session: {session_id}")
        return compressor
    
    def create_session_decompressor(self, session_id: str, shared_secret: bytes) -> SDIPureImageDecompressor:
        """Crée un décompresseur lié à une session HCS"""
        decompressor = SDIPureImageDecompressor(
            session_id=session_id,
            shared_secret=shared_secret
        )
        self.decompressors[session_id] = decompressor
        logger.info(f"Décompresseur créé pour session: {session_id}")
        return decompressor
    
    def compress_with_session(self, session_id: str, image_path: str, output_path: str) -> Dict[str, Any]:
        """Compression avec gestion de session"""
        if session_id not in self.compressors:
            return {
                'success': False,
                'error': f'Session {session_id} non trouvée'
            }
        
        compressor = self.compressors[session_id]
        try:
            metrics = compressor.save_compressed_image(image_path, output_path)
            metrics['session_id'] = session_id
            return metrics
        except Exception as e:
            logger.error(f"Erreur compression: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    def decompress_with_session(self, session_id: str, file_path: str) -> Dict[str, Any]:
        """Décompression avec gestion de session"""
        if session_id not in self.decompressors:
            return {
                'success': False,
                'error': f'Session {session_id} non trouvée'
            }
        
        decompressor = self.decompressors[session_id]
        try:
            result = decompressor.decompress_sdi_img(file_path)
            result['session_id'] = session_id
            return result
        except Exception as e:
            logger.error(f"Erreur décompression: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    def get_session_audit_log(self, session_id: str) -> Dict[str, Any]:
        """Récupère l'historique d'audit pour une session"""
        compression_history = []
        decompression_history = []
        
        if session_id in self.compressors:
            compression_history = self.compressors[session_id].get_compression_history()
        
        if session_id in self.decompressors:
            decompression_history = self.decompressors[session_id].get_decompression_history()
        
        return {
            'session_id': session_id,
            'compression_operations': compression_history,
            'decompression_operations': decompression_history,
            'total_operations': len(compression_history) + len(decompression_history)
        }
    
    def cleanup_session(self, session_id: str) -> bool:
        """Nettoie les ressources d'une session"""
        try:
            if session_id in self.compressors:
                del self.compressors[session_id]
            if session_id in self.decompressors:
                del self.decompressors[session_id]
            logger.info(f"Session {session_id} nettoyée")
            return True
        except Exception as e:
            logger.error(f"Erreur nettoyage session: {e}")
            return False
