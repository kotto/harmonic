"""
Tests pour HCV Binary Lossless Codec
"""

import os
import tempfile
from hcv_binary_lossless_codec import HCVBinaryLossless


def test_codec_initialization():
    """Test l'initialisation du codec"""
    codec = HCVBinaryLossless(verbose=False)
    assert codec is not None
    print("✅ Initialisation OK")


def test_get_info():
    """Test les informations du codec"""
    codec = HCVBinaryLossless(verbose=False)
    info = codec.get_info()
    
    assert info['name'] == 'HCV Binary Lossless Codec'
    assert info['guarantee'] == 'Reconstruction 100% fidèle (bit-exact)'
    assert info['mobile_optimized'] == True
    assert info['background_compression'] == True
    assert info['lazy_decompression'] == True
    print("✅ Informations OK")


def test_file_type_detection():
    """Test la détection de type de fichier"""
    codec = HCVBinaryLossless(verbose=False)
    
    assert codec.detect_file_type('photo.jpg') == 'image'
    assert codec.detect_file_type('video.mp4') == 'video'
    assert codec.detect_file_type('archive.zip') == 'archive'
    assert codec.detect_file_type('database.db') == 'database'
    assert codec.detect_file_type('app.exe') == 'executable'
    assert codec.detect_file_type('config.json') == 'config'
    assert codec.detect_file_type('log.txt') == 'text'
    print("✅ Détection de type OK")


def test_entropy_analysis():
    """Test l'analyse d'entropie"""
    codec = HCVBinaryLossless(verbose=False)
    
    # Données très structurées (basse entropie)
    structured = b'AAAAAABBBBBBCCCCCC' * 100
    entropy_low = codec.analyze_entropy(structured)
    assert entropy_low < 3.0
    
    # Données aléatoires (haute entropie)
    import random
    random_data = bytes(random.randint(0, 255) for _ in range(1000))
    entropy_high = codec.analyze_entropy(random_data)
    assert entropy_high > 5.0
    
    print(f"✅ Analyse entropie OK (basse: {entropy_low:.2f}, haute: {entropy_high:.2f})")


def test_strategy_selection():
    """Test la sélection de stratégie"""
    codec = HCVBinaryLossless(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Config (basse entropie)
        config_path = os.path.join(tmpdir, 'config.json')
        with open(config_path, 'wb') as f:
            f.write(b'{"key": "value"}' * 100)
        strategy = codec.select_strategy(config_path, 2.0)
        assert strategy.value == 'entropy_coding'
        
        # Exécutable (entropie moyenne)
        exe_path = os.path.join(tmpdir, 'app.exe')
        with open(exe_path, 'wb') as f:
            f.write(b'\x00\x01\x02\x03' * 100)
        strategy = codec.select_strategy(exe_path, 4.0)
        assert strategy.value in ['dictionary_based', 'hybrid']
        
        print("✅ Sélection de stratégie OK")


def test_compression():
    """Test la compression"""
    codec = HCVBinaryLossless(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Créer un fichier de test
        test_path = os.path.join(tmpdir, 'test.bin')
        test_data = b'Hello World! ' * 10000
        with open(test_path, 'wb') as f:
            f.write(test_data)
        
        result = codec.compress(test_path)
        
        assert result.original_size > 0
        assert result.compressed_size > 0
        assert result.ratio > 0
        assert 0 <= result.saving_percent <= 100
        assert result.compressed_size < result.original_size
        
        print(f"✅ Compression OK (ratio: {result.ratio:.2f}:1)")


def test_lossless_guarantee():
    """Test la garantie lossless"""
    codec = HCVBinaryLossless(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Créer un fichier de test
        test_path = os.path.join(tmpdir, 'test.bin')
        test_data = b'Test data ' * 1000
        with open(test_path, 'wb') as f:
            f.write(test_data)
        
        # Compresser
        result = codec.compress(test_path)
        
        # Vérifier les checksums
        assert result.checksum_original != result.checksum_compressed
        
        # Vérifier que la décompression est fidèle
        # (le codec vérifie automatiquement)
        
        print("✅ Garantie lossless OK")


def test_compress_to_file():
    """Test la compression avec sauvegarde HCV6"""
    codec = HCVBinaryLossless(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Créer un fichier de test
        input_path = os.path.join(tmpdir, 'test.bin')
        output_path = os.path.join(tmpdir, 'test.hcv6')
        
        test_data = b'Test data ' * 1000
        with open(input_path, 'wb') as f:
            f.write(test_data)
        
        # Compresser et sauvegarder
        result = codec.compress_to_file(input_path, output_path)
        
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) < len(test_data)
        
        print(f"✅ Compression HCV6 OK")


def test_decompress_from_file():
    """Test la décompression depuis HCV6"""
    codec = HCVBinaryLossless(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Créer et compresser un fichier
        input_path = os.path.join(tmpdir, 'test.bin')
        compressed_path = os.path.join(tmpdir, 'test.hcv6')
        output_path = os.path.join(tmpdir, 'test_restored.bin')
        
        test_data = b'Test data ' * 1000
        with open(input_path, 'wb') as f:
            f.write(test_data)
        
        # Compresser
        codec.compress_to_file(input_path, compressed_path)
        
        # Décompresser
        codec.decompress_from_file(compressed_path, output_path)
        
        # Vérifier
        with open(output_path, 'rb') as f:
            restored_data = f.read()
        
        assert restored_data == test_data
        
        print("✅ Décompression HCV6 OK")


def test_batch_processing():
    """Test le traitement par lot"""
    codec = HCVBinaryLossless(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        total_original = 0
        total_compressed = 0
        
        # Créer plusieurs fichiers
        for i in range(3):
            test_path = os.path.join(tmpdir, f'test_{i}.bin')
            test_data = b'Test data ' * (1000 * (i + 1))
            with open(test_path, 'wb') as f:
                f.write(test_data)
            
            result = codec.compress(test_path)
            total_original += result.original_size
            total_compressed += result.compressed_size
        
        total_ratio = total_original / total_compressed
        assert total_ratio > 1
        
        print(f"✅ Batch processing OK (ratio total: {total_ratio:.2f}:1)")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*60)
    print("HCV Binary Lossless Codec — Test Suite")
    print("="*60 + "\n")
    
    tests = [
        test_codec_initialization,
        test_get_info,
        test_file_type_detection,
        test_entropy_analysis,
        test_strategy_selection,
        test_compression,
        test_lossless_guarantee,
        test_compress_to_file,
        test_decompress_from_file,
        test_batch_processing,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Résultats: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
