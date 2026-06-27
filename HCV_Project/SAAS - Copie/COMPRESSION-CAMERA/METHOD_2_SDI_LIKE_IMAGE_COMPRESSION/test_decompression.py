#!/usr/bin/env python3
"""
TEST DE DÉCOMPRESSION CORRIGÉ
"""

from decompression_utils import SDIImageDecompressor
import json

def test_decompression():
    """Test la décompression avec le fichier existant"""
    
    print("=== TEST DE DÉCOMPRESSION CORRIGÉ ===")
    
    # Test de décompression
    decompressor = SDIImageDecompressor()
    result = decompressor.decompress_sdi_img('outputs/compressed_high_1775827009_essai-up.sdi-img')
    
    print(f"Succès: {result.get('success', False)}")
    
    if result.get('success'):
        print(f"Width: {result['width']}")
        print(f"Height: {result['height']}")
        print(f"Bit depth: {result['bit_depth']}")
        print(f"Quality: {result['quality']}")
        print(f"File size: {result['file_size']}")
        print(f"Header size: {result.get('header_size', 'N/A')}")
        print(f"Metadata size: {result.get('metadata_size', 'N/A')}")
        print(f"Compressed data size: {result.get('compressed_data_size', 'N/A')}")
        
        if isinstance(result['metadata'], dict):
            print(f"Metadata keys: {list(result['metadata'].keys())}")
        else:
            print(f"Metadata type: {type(result['metadata'])}")
            print(f"Metadata content: {result['metadata']}")
        
        # Test de conversion en base64
        try:
            base64_image = decompressor.get_image_base64(result['reconstructed_image'])
            print(f"Base64 conversion: SUCCESS ({len(base64_image)} chars)")
        except Exception as e:
            print(f"Base64 conversion error: {e}")
            
    else:
        print(f"Erreur: {result.get('error', 'Unknown error')}")
    
    print("\n=== TEST INFORMATIONS FICHIER ===")
    
    # Test des informations du fichier
    file_info = decompressor.get_file_info('outputs/compressed_high_1775827009_essai-up.sdi-img')
    
    print(f"Succès: {file_info.get('success', False)}")
    
    if file_info.get('success'):
        print(f"Format: {file_info['format']}")
        print(f"Dimensions: {file_info['width']}x{file_info['height']}")
        print(f"Bit depth: {file_info['bit_depth']}")
        print(f"Quality: {file_info['quality']}")
        print(f"File size: {file_info['file_size_bytes']} bytes")
        print(f"File size: {file_info['file_size_kb']} KB")
        print(f"File size: {file_info['file_size_mb']} MB")
    else:
        print(f"Erreur: {file_info.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_decompression()
