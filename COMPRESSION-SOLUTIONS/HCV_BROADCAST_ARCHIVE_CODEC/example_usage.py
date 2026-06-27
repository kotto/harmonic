"""
Exemples d'utilisation du HCV Broadcast Archive Codec (Solution 7)
"""

from hcv_broadcast_archive_codec import HCVBroadcastArchive, ArchiveStrategy
import os
import tempfile


def example_1_basic_compression():
    """Exemple 1: Compression basique"""
    print("\n" + "="*60)
    print("EXEMPLE 1: Compression Basique")
    print("="*60)
    
    codec = HCVBroadcastArchive()
    
    # Créer un fichier de test
    test_file = 'test_video.mov'
    with open(test_file, 'wb') as f:
        f.write(b'BROADCAST_VIDEO_DATA_' * 50000)
    
    # Compresser
    result = codec.compress(test_file)
    
    print(f"\nFichier: {test_file}")
    print(f"Taille originale: {result.original_size:,} bytes")
    print(f"Taille compressée: {result.compressed_size:,} bytes")
    print(f"Ratio: {result.ratio:.2f}:1")
    print(f"Économie: {(1 - result.compressed_size/result.original_size)*100:.1f}%")
    print(f"Temps: {result.time_ms:.0f}ms")
    print(f"Stratégie: {result.strategy}")
    
    # Nettoyer
    os.remove(test_file)


def example_2_strategies():
    """Exemple 2: Comparaison des stratégies"""
    print("\n" + "="*60)
    print("EXEMPLE 2: Comparaison des Stratégies")
    print("="*60)
    
    codec = HCVBroadcastArchive()
    
    # Créer un fichier de test
    test_file = 'test_video.mov'
    with open(test_file, 'wb') as f:
        f.write(b'BROADCAST_VIDEO_DATA_' * 50000)
    
    strategies = [
        ArchiveStrategy.LOSSLESS_ARCHIVE,
        ArchiveStrategy.MEZZANINE,
        ArchiveStrategy.PROXY,
        ArchiveStrategy.REDUNDANCY
    ]
    
    print(f"\nFichier: {test_file}")
    print(f"Taille originale: {os.path.getsize(test_file):,} bytes\n")
    
    for strategy in strategies:
        result = codec.compress(test_file, strategy)
        print(f"{strategy.value.upper()}")
        print(f"  Ratio: {result.ratio:.2f}:1")
        print(f"  Économie: {(1 - result.compressed_size/result.original_size)*100:.1f}%")
        print(f"  Temps: {result.time_ms:.0f}ms")
    
    # Nettoyer
    os.remove(test_file)


def example_3_compress_to_file():
    """Exemple 3: Compression vers fichier"""
    print("\n" + "="*60)
    print("EXEMPLE 3: Compression vers Fichier")
    print("="*60)
    
    codec = HCVBroadcastArchive()
    
    # Créer un fichier de test
    input_file = 'input_video.mov'
    output_file = 'output_video.hcv7'
    
    with open(input_file, 'wb') as f:
        f.write(b'BROADCAST_VIDEO_DATA_' * 50000)
    
    # Compresser et sauvegarder
    result = codec.compress_to_file(input_file, output_file)
    
    print(f"\nFichier d'entrée: {input_file}")
    print(f"Fichier de sortie: {output_file}")
    print(f"Taille originale: {result.original_size:,} bytes")
    print(f"Taille compressée: {result.compressed_size:,} bytes")
    print(f"Ratio: {result.ratio:.2f}:1")
    print(f"Économie: {(1 - result.compressed_size/result.original_size)*100:.1f}%")
    
    # Vérifier que le fichier existe
    if os.path.exists(output_file):
        print(f"✓ Fichier créé: {output_file}")
    
    # Nettoyer
    os.remove(input_file)
    os.remove(output_file)


def example_4_decompress():
    """Exemple 4: Décompression"""
    print("\n" + "="*60)
    print("EXEMPLE 4: Décompression")
    print("="*60)
    
    codec = HCVBroadcastArchive()
    
    # Créer et compresser un fichier
    input_file = 'input_video.mov'
    compressed_file = 'compressed_video.hcv7'
    decompressed_file = 'decompressed_video.mov'
    
    with open(input_file, 'wb') as f:
        f.write(b'BROADCAST_VIDEO_DATA_' * 50000)
    
    # Compresser
    codec.compress_to_file(input_file, compressed_file)
    print(f"✓ Fichier compressé: {compressed_file}")
    
    # Décompresser
    success = codec.decompress_from_file(compressed_file, decompressed_file)
    
    if success:
        print(f"✓ Fichier décompressé: {decompressed_file}")
        
        # Vérifier que les données sont identiques
        with open(input_file, 'rb') as f:
            original = f.read()
        with open(decompressed_file, 'rb') as f:
            decompressed = f.read()
        
        if original == decompressed:
            print("✓ Données identiques (100% fidèle)")
        else:
            print("✗ Données différentes")
    else:
        print("✗ Erreur décompression")
    
    # Nettoyer
    os.remove(input_file)
    os.remove(compressed_file)
    os.remove(decompressed_file)


def example_5_verify_archive():
    """Exemple 5: Vérification d'archive"""
    print("\n" + "="*60)
    print("EXEMPLE 5: Vérification d'Archive")
    print("="*60)
    
    codec = HCVBroadcastArchive()
    
    # Créer et compresser un fichier
    input_file = 'input_video.mov'
    archive_file = 'archive_video.hcv7'
    
    with open(input_file, 'wb') as f:
        f.write(b'BROADCAST_VIDEO_DATA_' * 50000)
    
    # Compresser
    codec.compress_to_file(input_file, archive_file)
    
    # Vérifier l'archive
    is_valid = codec.verify_archive(archive_file)
    
    if is_valid:
        print(f"✓ Archive valide: {archive_file}")
    else:
        print(f"✗ Archive corrompue: {archive_file}")
    
    # Nettoyer
    os.remove(input_file)
    os.remove(archive_file)


def example_6_archive_to_storage():
    """Exemple 6: Archivage vers stockage"""
    print("\n" + "="*60)
    print("EXEMPLE 6: Archivage vers Stockage")
    print("="*60)
    
    codec = HCVBroadcastArchive()
    
    # Créer un fichier de test
    input_file = 'input_video.mov'
    storage_path = 'archive_storage'
    
    with open(input_file, 'wb') as f:
        f.write(b'BROADCAST_VIDEO_DATA_' * 50000)
    
    # Archiver vers stockage
    result = codec.archive_to_storage(input_file, storage_path)
    
    if result.success:
        print(f"✓ Archivé vers: {storage_path}")
        print(f"  Ratio: {result.ratio:.2f}:1")
        print(f"  Économie: {(1 - result.compressed_size/result.original_size)*100:.1f}%")
    else:
        print("✗ Erreur archivage")
    
    # Nettoyer
    import shutil
    os.remove(input_file)
    if os.path.exists(storage_path):
        shutil.rmtree(storage_path)


def example_7_conformity():
    """Exemple 7: Vérification conformité"""
    print("\n" + "="*60)
    print("EXEMPLE 7: Vérification Conformité")
    print("="*60)
    
    codec = HCVBroadcastArchive()
    
    # Créer un fichier de test
    test_file = 'test_video.mov'
    with open(test_file, 'wb') as f:
        f.write(b'BROADCAST_VIDEO_DATA_' * 50000)
    
    # Vérifier la conformité
    conformity = codec.verify_conformity(test_file)
    
    print(f"\nConformité pour: {test_file}")
    print(f"  EBU R128: {'✓' if conformity['ebu_r128'] else '✗'}")
    print(f"  SMPTE ST 2110: {'✓' if conformity['smpte_st2110'] else '✗'}")
    print(f"  ITU-R BT.709: {'✓' if conformity['itu_r_bt709'] else '✗'}")
    print(f"  Timecode: {'✓' if conformity['timecode_preserved'] else '✗'}")
    print(f"  Métadonnées: {'✓' if conformity['metadata_preserved'] else '✗'}")
    print(f"  Audio sync: {'✓' if conformity['audio_sync'] else '✗'}")
    
    # Nettoyer
    os.remove(test_file)


def example_8_codec_info():
    """Exemple 8: Informations codec"""
    print("\n" + "="*60)
    print("EXEMPLE 8: Informations Codec")
    print("="*60)
    
    codec = HCVBroadcastArchive()
    info = codec.get_info()
    
    print(f"\nCodec: {info['name']}")
    print(f"Version: {info['version']}")
    print(f"Solution: {info['solution']}")
    print(f"Cas d'usage: {info['use_case']}")
    print(f"Ratio: {info['ratio_range']}")
    print(f"Économie: {info['economy']}")
    print(f"Conformité: {', '.join(info['conformity'])}")
    print(f"Garantie: {info['guarantee']}")
    print(f"\nStratégies:")
    for strategy in info['strategies']:
        print(f"  - {strategy}")
    print(f"\nFormats:")
    for fmt_type, exts in info['formats'].items():
        print(f"  {fmt_type}: {', '.join(exts)}")


def main():
    """Exécute tous les exemples"""
    print("\n" + "="*60)
    print("HCV BROADCAST ARCHIVE CODEC — EXEMPLES D'UTILISATION")
    print("="*60)
    
    try:
        example_1_basic_compression()
        example_2_strategies()
        example_3_compress_to_file()
        example_4_decompress()
        example_5_verify_archive()
        example_6_archive_to_storage()
        example_7_conformity()
        example_8_codec_info()
        
        print("\n" + "="*60)
        print("✓ TOUS LES EXEMPLES EXÉCUTÉS AVEC SUCCÈS")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\n✗ Erreur: {e}\n")


if __name__ == '__main__':
    main()
