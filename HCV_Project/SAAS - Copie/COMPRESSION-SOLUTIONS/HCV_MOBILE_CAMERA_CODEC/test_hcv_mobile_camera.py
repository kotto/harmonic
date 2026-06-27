"""
Tests pour HCV Mobile Camera Codec
"""

import os
import tempfile
from pathlib import Path
from hcv_mobile_camera_codec import HCVMobileCamera, MediaType


def test_codec_initialization():
    """Test l'initialisation du codec"""
    codec = HCVMobileCamera(verbose=False)
    assert codec is not None
    assert codec.ZSTD_LEVEL == 11
    print("✅ Initialisation OK")


def test_get_info():
    """Test les informations du codec"""
    codec = HCVMobileCamera(verbose=False)
    info = codec.get_info()
    
    assert info['name'] == 'HCV Mobile Camera Codec'
    assert 'JPEG' in info['formats_supported']['photos']
    assert 'HEIC' in info['formats_supported']['photos']
    assert 'MP4' in info['formats_supported']['videos']
    assert info['guarantee'] == 'Fichier compressé < fichier original'
    print("✅ Informations OK")


def test_media_type_detection():
    """Test la détection de type de média"""
    codec = HCVMobileCamera(verbose=False)
    
    # Créer des fichiers de test
    with tempfile.TemporaryDirectory() as tmpdir:
        # JPEG
        jpeg_path = os.path.join(tmpdir, 'test.jpg')
        with open(jpeg_path, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
        assert codec.detect_media_type(jpeg_path) == MediaType.PHOTO_JPEG
        
        # PNG
        png_path = os.path.join(tmpdir, 'test.png')
        with open(png_path, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
        assert codec.detect_media_type(png_path) == MediaType.PHOTO_PNG
        
        # HEIC
        heic_path = os.path.join(tmpdir, 'test.heic')
        with open(heic_path, 'wb') as f:
            f.write(b'\x00\x00\x00\x18ftypheic' + b'\x00' * 100)
        assert codec.detect_media_type(heic_path) == MediaType.PHOTO_HEIC
        
        print("✅ Détection de type OK")


def test_jpeg_quality_analysis():
    """Test l'analyse de qualité JPEG"""
    codec = HCVMobileCamera(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Créer un fichier JPEG de test
        jpeg_path = os.path.join(tmpdir, 'test.jpg')
        with open(jpeg_path, 'wb') as f:
            # Fichier petit = basse qualité
            f.write(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
        
        quality = codec.analyze_jpeg_quality(jpeg_path)
        assert 1 <= quality <= 100
        print(f"✅ Analyse qualité JPEG OK (qualité estimée: {quality})")


def test_video_bitrate_analysis():
    """Test l'analyse de bitrate vidéo"""
    codec = HCVMobileCamera(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Créer un fichier MP4 de test
        mp4_path = os.path.join(tmpdir, 'test.mp4')
        with open(mp4_path, 'wb') as f:
            f.write(b'\x00\x00\x00\x20ftypmp42' + b'\x00' * 1000000)  # ~1 MB
        
        bitrate = codec.analyze_video_bitrate(mp4_path)
        assert bitrate > 0
        print(f"✅ Analyse bitrate vidéo OK (bitrate estimé: {bitrate} Mbps)")


def test_photo_strategy_selection():
    """Test la sélection de stratégie pour photos"""
    codec = HCVMobileCamera(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # HEIC
        heic_path = os.path.join(tmpdir, 'test.heic')
        with open(heic_path, 'wb') as f:
            f.write(b'\x00\x00\x00\x18ftypheic' + b'\x00' * 100)
        strategy = codec.select_photo_strategy(heic_path, MediaType.PHOTO_HEIC)
        assert strategy.value == 'transcode_heic'
        
        # JPEG
        jpeg_path = os.path.join(tmpdir, 'test.jpg')
        with open(jpeg_path, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'\x00' * 100)
        strategy = codec.select_photo_strategy(jpeg_path, MediaType.PHOTO_JPEG)
        assert strategy.value in ['reencode_jpeg', 'direct_jpeg']
        
        print("✅ Sélection stratégie photo OK")


def test_video_strategy_selection():
    """Test la sélection de stratégie pour vidéos"""
    codec = HCVMobileCamera(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Vidéo basse qualité
        mp4_path = os.path.join(tmpdir, 'test.mp4')
        with open(mp4_path, 'wb') as f:
            f.write(b'\x00\x00\x00\x20ftypmp42' + b'\x00' * 100000)  # ~100 KB
        strategy = codec.select_video_strategy(mp4_path)
        assert strategy.value == 'direct'
        
        print("✅ Sélection stratégie vidéo OK")


def test_photo_compression():
    """Test la compression de photo"""
    codec = HCVMobileCamera(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Créer un fichier JPEG de test
        jpeg_path = os.path.join(tmpdir, 'test.jpg')
        with open(jpeg_path, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'\x00' * 1000000)  # ~1 MB
        
        result = codec.compress_photo(jpeg_path)
        
        assert result.original_size > 0
        assert result.compressed_size > 0
        assert result.ratio > 0
        assert 0 <= result.saving_percent <= 100
        assert result.speed_mbps > 0
        assert result.quality in ['Préservée', 'Identique', '⚠️ Inadapté']
        assert result.compressed_size < result.original_size
        
        print(f"✅ Compression photo OK (ratio: {result.ratio:.2f}:1)")


def test_video_compression():
    """Test la compression de vidéo"""
    codec = HCVMobileCamera(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Créer un fichier MP4 de test
        mp4_path = os.path.join(tmpdir, 'test.mp4')
        with open(mp4_path, 'wb') as f:
            f.write(b'\x00\x00\x00\x20ftypmp42' + b'\x00' * 1000000)  # ~1 MB
        
        result = codec.compress_video(mp4_path)
        
        assert result.original_size > 0
        assert result.compressed_size > 0
        assert result.ratio > 0
        assert 0 <= result.saving_percent <= 100
        assert result.speed_mbps > 0
        assert result.quality in ['Préservée', 'Identique', '⚠️ Inadapté']
        assert result.compressed_size < result.original_size
        
        print(f"✅ Compression vidéo OK (ratio: {result.ratio:.2f}:1)")


def test_compress_photo():
    """Test la compression générale de photo"""
    codec = HCVMobileCamera(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # JPEG
        jpeg_path = os.path.join(tmpdir, 'test.jpg')
        with open(jpeg_path, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'\x00' * 1000000)
        
        result = codec.compress(jpeg_path)
        assert result.media_type == 'photo_jpeg'
        assert result.compressed_size < result.original_size
        
        print(f"✅ Compression photo générale OK")


def test_compress_video():
    """Test la compression générale de vidéo"""
    codec = HCVMobileCamera(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # MP4
        mp4_path = os.path.join(tmpdir, 'test.mp4')
        with open(mp4_path, 'wb') as f:
            f.write(b'\x00\x00\x00\x20ftypmp42' + b'\x00' * 1000000)
        
        result = codec.compress(mp4_path)
        assert result.media_type == 'video'
        assert result.compressed_size < result.original_size
        
        print(f"✅ Compression vidéo générale OK")


def test_guarantee_smaller_than_original():
    """Test la garantie : fichier compressé < original"""
    codec = HCVMobileCamera(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Créer plusieurs fichiers de test
        for i in range(5):
            jpeg_path = os.path.join(tmpdir, f'test_{i}.jpg')
            with open(jpeg_path, 'wb') as f:
                f.write(b'\xff\xd8\xff\xe0' + b'\x00' * (100000 * (i + 1)))
            
            result = codec.compress(jpeg_path)
            assert result.compressed_size < result.original_size, \
                f"Garantie violée: {result.compressed_size} >= {result.original_size}"
    
    print("✅ Garantie OK (tous les fichiers compressés < original)")


def test_batch_processing():
    """Test le traitement par lot"""
    codec = HCVMobileCamera(verbose=False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Créer plusieurs fichiers
        files = []
        for i in range(3):
            jpeg_path = os.path.join(tmpdir, f'photo_{i}.jpg')
            with open(jpeg_path, 'wb') as f:
                f.write(b'\xff\xd8\xff\xe0' + b'\x00' * 500000)
            files.append(jpeg_path)
        
        total_original = 0
        total_compressed = 0
        
        for file_path in files:
            result = codec.compress(file_path)
            total_original += result.original_size
            total_compressed += result.compressed_size
        
        total_ratio = total_original / total_compressed
        assert total_ratio > 1
        
        print(f"✅ Batch processing OK (ratio total: {total_ratio:.2f}:1)")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*50)
    print("HCV Mobile Camera Codec — Test Suite")
    print("="*50 + "\n")
    
    tests = [
        test_codec_initialization,
        test_get_info,
        test_media_type_detection,
        test_jpeg_quality_analysis,
        test_video_bitrate_analysis,
        test_photo_strategy_selection,
        test_video_strategy_selection,
        test_photo_compression,
        test_video_compression,
        test_compress_photo,
        test_compress_video,
        test_guarantee_smaller_than_original,
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
    
    print("\n" + "="*50)
    print(f"Résultats: {passed} passed, {failed} failed")
    print("="*50 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
