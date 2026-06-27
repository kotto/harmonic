#!/usr/bin/env python3
"""
TEST DE L'IMAGE DE PREVIEW CORRIGÉE
"""

from decompression_utils import SDIImageDecompressor
import cv2

def test_preview_image():
    """Test la création de l'image de preview"""
    
    print("=== TEST IMAGE PREVIEW ===")
    
    # Test de décompression
    decompressor = SDIImageDecompressor()
    result = decompressor.decompress_sdi_img('outputs/compressed_high_1775827009_essai-up.sdi-img')
    
    if result.get('success'):
        print(f"✅ Décompression réussie")
        print(f"   Dimensions: {result['width']}x{result['height']}")
        print(f"   Qualité: {result['quality']}")
        
        # Test de sauvegarde de l'image reconstruite
        reconstructed_image = result['reconstructed_image']
        print(f"   Image shape: {reconstructed_image.shape}")
        print(f"   Image dtype: {reconstructed_image.dtype}")
        print(f"   Valeurs min/max: {reconstructed_image.min()}/{reconstructed_image.max()}")
        
        # Sauvegarde pour vérification visuelle
        cv2.imwrite('preview_reconstructed_image.png', reconstructed_image)
        print("   ✅ Image sauvegardée: preview_reconstructed_image.png")
        
        # Test conversion base64
        base64_data = decompressor.get_image_base64(reconstructed_image)
        if base64_data.startswith('data:image/png;base64,'):
            print(f"   ✅ Base64 conversion: SUCCESS ({len(base64_data)} chars)")
        else:
            print(f"   ❌ Base64 conversion: FAILED")
        
        # Vérification que l'image n'est pas noire
        unique_values = len(reconstructed_image.reshape(-1, 3).tolist())
        unique_colors = len(set(tuple(row) for row in reconstructed_image.reshape(-1, 3)))
        
        print(f"   Nombre de pixels: {reconstructed_image.size}")
        print(f"   Valeurs uniques: {unique_values}")
        print(f"   Couleurs uniques: {unique_colors}")
        
        if unique_colors > 10:
            print("   ✅ Image a suffisamment de couleurs (pas noire)")
        else:
            print("   ❌ Image semble noire ou monochrome")
            
        # Vérification de la luminosité moyenne
        brightness = reconstructed_image.mean()
        print(f"   Luminosité moyenne: {brightness:.2f}")
        
        if brightness > 50:
            print("   ✅ Image suffisamment lumineuse")
        else:
            print("   ❌ Image trop sombre")
            
    else:
        print(f"❌ Décompression échouée: {result.get('error')}")
    
    print("\n=== FIN TEST ===")

if __name__ == "__main__":
    test_preview_image()
