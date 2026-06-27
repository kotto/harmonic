"""
Exemples d'utilisation du HCV Mobile Camera Codec
"""

from hcv_mobile_camera_codec import HCVMobileCamera
import os


def example_1_single_photo():
    """Exemple 1: Compresser une seule photo"""
    print("\n" + "="*60)
    print("EXEMPLE 1: Compresser une seule photo")
    print("="*60)
    
    codec = HCVMobileCamera(verbose=True)
    
    # Créer un fichier de test
    test_file = 'test_photo.jpg'
    with open(test_file, 'wb') as f:
        f.write(b'\xff\xd8\xff\xe0' + b'\x00' * 1000000)  # ~1 MB
    
    try:
        result = codec.compress(test_file)
        
        print(f"\nRésultat:")
        print(f"  Fichier: {test_file}")
        print(f"  Taille originale: {result.original_size / 1024 / 1024:.2f} MB")
        print(f"  Taille compressée: {result.compressed_size / 1024 / 1024:.2f} MB")
        print(f"  Ratio: {result.ratio:.2f}:1")
        print(f"  Économie: {result.saving_percent:.1f}%")
        print(f"  Stratégie: {result.strategy}")
        print(f"  Qualité: {result.quality}")
        print(f"  Vitesse: {result.speed_mbps:.1f} MB/s")
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def example_2_single_video():
    """Exemple 2: Compresser une seule vidéo"""
    print("\n" + "="*60)
    print("EXEMPLE 2: Compresser une seule vidéo")
    print("="*60)
    
    codec = HCVMobileCamera(verbose=True)
    
    # Créer un fichier de test
    test_file = 'test_video.mp4'
    with open(test_file, 'wb') as f:
        f.write(b'\x00\x00\x00\x20ftypmp42' + b'\x00' * 5000000)  # ~5 MB
    
    try:
        result = codec.compress(test_file)
        
        print(f"\nRésultat:")
        print(f"  Fichier: {test_file}")
        print(f"  Taille originale: {result.original_size / 1024 / 1024:.2f} MB")
        print(f"  Taille compressée: {result.compressed_size / 1024 / 1024:.2f} MB")
        print(f"  Ratio: {result.ratio:.2f}:1")
        print(f"  Économie: {result.saving_percent:.1f}%")
        print(f"  Stratégie: {result.strategy}")
        print(f"  Qualité: {result.quality}")
        print(f"  Vitesse: {result.speed_mbps:.1f} MB/s")
        print(f"  Bitrate: {result.metadata.get('bitrate_mbps', 'N/A')} Mbps")
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)


def example_3_batch_processing():
    """Exemple 3: Traitement par lot"""
    print("\n" + "="*60)
    print("EXEMPLE 3: Traitement par lot (batch processing)")
    print("="*60)
    
    codec = HCVMobileCamera(verbose=False)
    
    # Créer des fichiers de test
    test_files = []
    for i in range(3):
        test_file = f'test_photo_{i}.jpg'
        with open(test_file, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'\x00' * (500000 * (i + 1)))
        test_files.append(test_file)
    
    try:
        total_original = 0
        total_compressed = 0
        
        print("\nTraitement:")
        for file_path in test_files:
            result = codec.compress(file_path)
            total_original += result.original_size
            total_compressed += result.compressed_size
            
            print(f"  {file_path}: {result.ratio:.2f}:1 ({result.saving_percent:.1f}%)")
        
        total_ratio = total_original / total_compressed
        total_saving = (1 - total_compressed / total_original) * 100
        
        print(f"\nRésumé:")
        print(f"  Taille totale originale: {total_original / 1024 / 1024:.2f} MB")
        print(f"  Taille totale compressée: {total_compressed / 1024 / 1024:.2f} MB")
        print(f"  Ratio total: {total_ratio:.2f}:1")
        print(f"  Économie totale: {total_saving:.1f}%")
    finally:
        for file_path in test_files:
            if os.path.exists(file_path):
                os.remove(file_path)


def example_4_media_type_detection():
    """Exemple 4: Détection de type de média"""
    print("\n" + "="*60)
    print("EXEMPLE 4: Détection de type de média")
    print("="*60)
    
    codec = HCVMobileCamera(verbose=False)
    
    # Créer des fichiers de test
    test_files = {
        'test.jpg': b'\xff\xd8\xff\xe0' + b'\x00' * 100,
        'test.png': b'\x89PNG\r\n\x1a\n' + b'\x00' * 100,
        'test.heic': b'\x00\x00\x00\x18ftypheic' + b'\x00' * 100,
        'test.mp4': b'\x00\x00\x00\x20ftypmp42' + b'\x00' * 100,
    }
    
    try:
        print("\nDétection:")
        for filename, content in test_files.items():
            with open(filename, 'wb') as f:
                f.write(content)
            
            media_type = codec.detect_media_type(filename)
            print(f"  {filename}: {media_type.value}")
    finally:
        for filename in test_files.keys():
            if os.path.exists(filename):
                os.remove(filename)


def example_5_codec_info():
    """Exemple 5: Informations du codec"""
    print("\n" + "="*60)
    print("EXEMPLE 5: Informations du codec")
    print("="*60)
    
    codec = HCVMobileCamera(verbose=False)
    info = codec.get_info()
    
    print(f"\nNom: {info['name']}")
    print(f"Version: {info['version']}")
    print(f"Description: {info['description']}")
    print(f"Garantie: {info['guarantee']}")
    print(f"Niveau zstd: {info['zstd_level']}")
    
    print(f"\nFormats supportés (photos):")
    for fmt in info['formats_supported']['photos']:
        print(f"  - {fmt}")
    
    print(f"\nFormats supportés (vidéos):")
    for fmt in info['formats_supported']['videos']:
        print(f"  - {fmt}")
    
    print(f"\nStratégies (photos):")
    for fmt, strat in info['strategies']['photos'].items():
        print(f"  - {fmt}: {strat}")
    
    print(f"\nStratégies (vidéos):")
    for fmt, strat in info['strategies']['videos'].items():
        print(f"  - {fmt}: {strat}")


def example_6_quality_analysis():
    """Exemple 6: Analyse de qualité JPEG"""
    print("\n" + "="*60)
    print("EXEMPLE 6: Analyse de qualité JPEG")
    print("="*60)
    
    codec = HCVMobileCamera(verbose=False)
    
    # Créer des fichiers de test de différentes tailles
    test_files = {
        'small.jpg': 100000,      # Petit = basse qualité
        'medium.jpg': 500000,     # Moyen = qualité moyenne
        'large.jpg': 2000000,     # Grand = haute qualité
    }
    
    try:
        print("\nAnalyse de qualité:")
        for filename, size in test_files.items():
            with open(filename, 'wb') as f:
                f.write(b'\xff\xd8\xff\xe0' + b'\x00' * size)
            
            quality = codec.analyze_jpeg_quality(filename)
            print(f"  {filename} ({size/1024:.0f} KB): Qualité estimée = {quality}")
    finally:
        for filename in test_files.keys():
            if os.path.exists(filename):
                os.remove(filename)


def example_7_bitrate_analysis():
    """Exemple 7: Analyse de bitrate vidéo"""
    print("\n" + "="*60)
    print("EXEMPLE 7: Analyse de bitrate vidéo")
    print("="*60)
    
    codec = HCVMobileCamera(verbose=False)
    
    # Créer des fichiers de test de différentes tailles
    test_files = {
        'low.mp4': 500000,        # Petit = bitrate faible
        'medium.mp4': 2000000,    # Moyen = bitrate moyen
        'high.mp4': 5000000,      # Grand = bitrate élevé
    }
    
    try:
        print("\nAnalyse de bitrate:")
        for filename, size in test_files.items():
            with open(filename, 'wb') as f:
                f.write(b'\x00\x00\x00\x20ftypmp42' + b'\x00' * size)
            
            bitrate = codec.analyze_video_bitrate(filename)
            print(f"  {filename} ({size/1024/1024:.1f} MB): Bitrate estimé = {bitrate} Mbps")
    finally:
        for filename in test_files.keys():
            if os.path.exists(filename):
                os.remove(filename)


def example_8_use_cases():
    """Exemple 8: Cas d'usage typiques"""
    print("\n" + "="*60)
    print("EXEMPLE 8: Cas d'usage typiques")
    print("="*60)
    
    codec = HCVMobileCamera(verbose=False)
    
    print("\n1. Sauvegarde Cloud (iCloud, Google Drive)")
    print("   Objectif: Maximiser l'économie d'espace")
    print("   Configuration:")
    print("     - Photos HEIC → TRANSCODE (3-5:1)")
    print("     - Photos JPEG → REENCODE si Q<80 (2-3:1)")
    print("     - Vidéos → REENCODE H.264 (1.3-1.8:1)")
    print("   Résultat: 5.8 GB → 3.0-4.2 GB (48-65% économie)")
    
    print("\n2. Partage Réseau (WhatsApp, Telegram)")
    print("   Objectif: Vitesse maximale")
    print("   Configuration:")
    print("     - Photos JPEG Q≥80 → DIRECT (1.2-1.5:1)")
    print("     - Photos HEIC → TRANSCODE (3-5:1)")
    print("     - Vidéos <10 Mbps → DIRECT (1.05-1.1:1)")
    print("   Résultat: 600 MB → 493-534 MB (11-18% économie)")
    
    print("\n3. Archivage Long Terme")
    print("   Objectif: Meilleure compression")
    print("   Configuration:")
    print("     - Photos HEIC → TRANSCODE (3-5:1)")
    print("     - Photos JPEG → REENCODE (2-3:1)")
    print("     - Vidéos → REENCODE H.265 (2-3:1)")
    print("   Résultat: 60 GB → 19-28 GB (53-68% économie)")


def main():
    """Exécute tous les exemples"""
    print("\n" + "="*60)
    print("HCV Mobile Camera Codec — Exemples d'Utilisation")
    print("="*60)
    
    examples = [
        example_1_single_photo,
        example_2_single_video,
        example_3_batch_processing,
        example_4_media_type_detection,
        example_5_codec_info,
        example_6_quality_analysis,
        example_7_bitrate_analysis,
        example_8_use_cases,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n❌ Erreur dans {example.__name__}: {e}")
    
    print("\n" + "="*60)
    print("Exemples terminés")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
