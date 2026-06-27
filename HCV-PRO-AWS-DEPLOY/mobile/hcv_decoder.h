/*
 * HCV PRO DECODER STANDALONE LIBRARY
 * Phase 1 - Bibliothèque standalone sans dépendance
 * Optimisé SIMD: AVX-512 / AVX2 / SSE2 / ARM NEON
 * Décode 12MP < 2ms
 */

#ifndef HCV_DECODER_H
#define HCV_DECODER_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// ========== API MINIMALISTE - SEULEMENT 3 FONCTIONS ==========

/**
 * Initialise le décodeur HCV
 * Détecte automatiquement les capacités SIMD du CPU
 * @return 0 en cas de succès
 */
int hcv_decoder_init(void);

/**
 * Décode un frame HCV compressé
 * @param compressed Données compressées
 * @param compressed_size Taille des données compressées
 * @param output Buffer de sortie (doit être pré-alloué)
 * @param width Largeur de l'image
 * @param height Hauteur de l'image
 * @return 0 en cas de succès
 */
int hcv_decode_frame(const uint8_t* compressed, size_t compressed_size,
                     uint16_t* output, int width, int height);

/**
 * Libère les ressources du décodeur
 */
void hcv_decoder_cleanup(void);

/**
 * Retourne la version de la bibliothèque
 */
const char* hcv_decoder_version(void);

#ifdef __cplusplus
}
#endif

#endif // HCV_DECODER_H
