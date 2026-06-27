"""
Test suite for HCV Broadcast Archive Codec (Solution 7)
"""

import os
import tempfile
import unittest
from pathlib import Path
from hcv_broadcast_archive_codec import (
    HCVBroadcastArchive,
    ArchiveStrategy,
    ArchiveResult
)


class TestHCVBroadcastArchive(unittest.TestCase):
    """Tests pour le codec d'archivage broadcast"""
    
    def setUp(self):
        """Initialisation avant chaque test"""
        self.codec = HCVBroadcastArchive(verbose=False)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, name: str, size: int) -> str:
        """Crée un fichier de test"""
        file_path = os.path.join(self.temp_dir, name)
        with open(file_path, 'wb') as f:
            # Créer des données répétitives (compressibles)
            pattern = b'BROADCAST_ARCHIVE_TEST_DATA_' * 100
            while f.tell() < size:
                f.write(pattern)
        return file_path
    
    def test_detect_format_video(self):
        """Test détection format vidéo"""
        test_file = self.create_test_file('test.mov', 1000)
        fmt = self.codec.detect_format(test_file)
        self.assertEqual(fmt, 'video')
    
    def test_detect_format_audio(self):
        """Test détection format audio"""
        test_file = self.create_test_file('test.wav', 1000)
        fmt = self.codec.detect_format(test_file)
        self.assertEqual(fmt, 'audio')
    
    def test_detect_format_unknown(self):
        """Test détection format inconnu"""
        test_file = self.create_test_file('test.xyz', 1000)
        fmt = self.codec.detect_format(test_file)
        self.assertEqual(fmt, 'unknown')
    
    def test_select_strategy_large_video(self):
        """Test sélection stratégie pour vidéo large"""
        test_file = self.create_test_file('large.mov', 2_000_000_000)
        strategy = self.codec.select_strategy(test_file, 2_000_000_000)
        self.assertEqual(strategy, ArchiveStrategy.LOSSLESS_ARCHIVE)
    
    def test_select_strategy_medium_video(self):
        """Test sélection stratégie pour vidéo moyenne"""
        test_file = self.create_test_file('medium.mov', 500_000_000)
        strategy = self.codec.select_strategy(test_file, 500_000_000)
        self.assertEqual(strategy, ArchiveStrategy.MEZZANINE)
    
    def test_select_strategy_small_video(self):
        """Test sélection stratégie pour vidéo petite"""
        test_file = self.create_test_file('small.mov', 50_000_000)
        strategy = self.codec.select_strategy(test_file, 50_000_000)
        self.assertEqual(strategy, ArchiveStrategy.PROXY)
    
    def test_compress_lossless_archive(self):
        """Test compression LOSSLESS_ARCHIVE"""
        test_file = self.create_test_file('test.mov', 1_000_000)
        result = self.codec.compress(test_file, ArchiveStrategy.LOSSLESS_ARCHIVE)
        
        self.assertTrue(result.success)
        self.assertGreater(result.ratio, 1.0)
        self.assertLess(result.compressed_size, result.original_size)
        self.assertEqual(result.strategy, 'lossless_archive')
    
    def test_compress_mezzanine(self):
        """Test compression MEZZANINE"""
        test_file = self.create_test_file('test.mov', 1_000_000)
        result = self.codec.compress(test_file, ArchiveStrategy.MEZZANINE)
        
        self.assertTrue(result.success)
        self.assertGreater(result.ratio, 1.0)
        self.assertLess(result.compressed_size, result.original_size)
        self.assertEqual(result.strategy, 'mezzanine')
    
    def test_compress_proxy(self):
        """Test compression PROXY"""
        test_file = self.create_test_file('test.mov', 1_000_000)
        result = self.codec.compress(test_file, ArchiveStrategy.PROXY)
        
        self.assertTrue(result.success)
        self.assertGreater(result.ratio, 1.0)
        self.assertLess(result.compressed_size, result.original_size)
        self.assertEqual(result.strategy, 'proxy')
    
    def test_compress_redundancy(self):
        """Test compression REDUNDANCY"""
        test_file = self.create_test_file('test.mov', 1_000_000)
        result = self.codec.compress(test_file, ArchiveStrategy.REDUNDANCY)
        
        self.assertTrue(result.success)
        self.assertGreater(result.ratio, 1.0)
        self.assertEqual(result.strategy, 'redundancy')
    
    def test_checksum_calculation(self):
        """Test calcul checksum"""
        data = b'TEST_DATA_FOR_CHECKSUM'
        checksum = self.codec.calculate_checksum(data)
        
        self.assertIsInstance(checksum, str)
        self.assertEqual(len(checksum), 64)  # SHA256 = 64 hex chars
    
    def test_checksum_consistency(self):
        """Test cohérence checksum"""
        data = b'TEST_DATA'
        checksum1 = self.codec.calculate_checksum(data)
        checksum2 = self.codec.calculate_checksum(data)
        
        self.assertEqual(checksum1, checksum2)
    
    def test_compress_to_file(self):
        """Test compression vers fichier"""
        input_file = self.create_test_file('input.mov', 1_000_000)
        output_file = os.path.join(self.temp_dir, 'output.hcv7')
        
        result = self.codec.compress_to_file(input_file, output_file)
        
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(output_file))
        self.assertLess(os.path.getsize(output_file), os.path.getsize(input_file))
    
    def test_decompress_from_file(self):
        """Test décompression depuis fichier"""
        input_file = self.create_test_file('input.mov', 1_000_000)
        compressed_file = os.path.join(self.temp_dir, 'compressed.hcv7')
        decompressed_file = os.path.join(self.temp_dir, 'decompressed.mov')
        
        # Compresser
        self.codec.compress_to_file(input_file, compressed_file)
        
        # Décompresser
        success = self.codec.decompress_from_file(compressed_file, decompressed_file)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(decompressed_file))
        
        # Vérifier que les données sont identiques
        with open(input_file, 'rb') as f:
            original = f.read()
        with open(decompressed_file, 'rb') as f:
            decompressed = f.read()
        
        self.assertEqual(original, decompressed)
    
    def test_verify_archive_valid(self):
        """Test vérification archive valide"""
        input_file = self.create_test_file('input.mov', 1_000_000)
        archive_file = os.path.join(self.temp_dir, 'archive.hcv7')
        
        self.codec.compress_to_file(input_file, archive_file)
        
        is_valid = self.codec.verify_archive(archive_file)
        self.assertTrue(is_valid)
    
    def test_verify_archive_invalid(self):
        """Test vérification archive invalide"""
        archive_file = os.path.join(self.temp_dir, 'invalid.hcv7')
        
        # Créer un fichier invalide
        with open(archive_file, 'wb') as f:
            f.write(b'INVALID_ARCHIVE_DATA')
        
        is_valid = self.codec.verify_archive(archive_file)
        self.assertFalse(is_valid)
    
    def test_archive_to_storage(self):
        """Test archivage vers stockage"""
        input_file = self.create_test_file('input.mov', 1_000_000)
        storage_path = os.path.join(self.temp_dir, 'storage')
        
        result = self.codec.archive_to_storage(input_file, storage_path)
        
        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(storage_path))
    
    def test_conformity_verification(self):
        """Test vérification conformité"""
        test_file = self.create_test_file('test.mov', 1_000_000)
        conformity = self.codec.verify_conformity(test_file)
        
        self.assertIn('ebu_r128', conformity)
        self.assertIn('smpte_st2110', conformity)
        self.assertIn('itu_r_bt709', conformity)
        self.assertTrue(conformity['ebu_r128'])
        self.assertTrue(conformity['smpte_st2110'])
        self.assertTrue(conformity['itu_r_bt709'])
    
    def test_get_info(self):
        """Test récupération informations codec"""
        info = self.codec.get_info()
        
        self.assertEqual(info['name'], 'HCV Broadcast Archive Codec')
        self.assertEqual(info['version'], '7.0')
        self.assertEqual(info['solution'], 7)
        self.assertIn('EBU R128', info['conformity'])
        self.assertIn('SMPTE ST 2110', info['conformity'])
    
    def test_compression_ratio_lossless_archive(self):
        """Test ratio compression LOSSLESS_ARCHIVE"""
        test_file = self.create_test_file('test.mov', 10_000_000)
        result = self.codec.compress(test_file, ArchiveStrategy.LOSSLESS_ARCHIVE)
        
        # Ratio devrait être entre 5-15:1 pour données répétitives
        self.assertGreater(result.ratio, 3.0)
    
    def test_compression_ratio_mezzanine(self):
        """Test ratio compression MEZZANINE"""
        test_file = self.create_test_file('test.mov', 10_000_000)
        result = self.codec.compress(test_file, ArchiveStrategy.MEZZANINE)
        
        # Ratio devrait être entre 3-8:1
        self.assertGreater(result.ratio, 2.0)
    
    def test_compression_ratio_proxy(self):
        """Test ratio compression PROXY"""
        test_file = self.create_test_file('test.mov', 10_000_000)
        result = self.codec.compress(test_file, ArchiveStrategy.PROXY)
        
        # Ratio devrait être entre 1.5-3:1
        self.assertGreater(result.ratio, 1.0)
    
    def test_metadata_preservation(self):
        """Test préservation métadonnées"""
        test_file = self.create_test_file('test.mov', 1_000_000)
        result = self.codec.compress(test_file)
        
        self.assertIn('format', result.metadata)
        self.assertIn('filename', result.metadata)
        self.assertEqual(result.metadata['format'], 'video')
    
    def test_nonexistent_file(self):
        """Test fichier inexistant"""
        result = self.codec.compress('/nonexistent/file.mov')
        
        self.assertFalse(result.success)
        self.assertEqual(result.ratio, 0)


if __name__ == '__main__':
    unittest.main()
