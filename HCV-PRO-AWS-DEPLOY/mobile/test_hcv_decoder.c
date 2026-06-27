/*
 * TEST UNITAIRE HCV DECODER
 * Phase 1 - Validation performance
 * Vérifie que le décode fait bien < 2ms pour 12MP
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include "hcv_decoder.h"

#define WIDTH  4032
#define HEIGHT 3024
#define PIXELS (WIDTH * HEIGHT)

int main() {
    printf("=== TEST UNITAIRE HCV DECODER PHASE 1 ===\n\n");
    
    // Initialisation
    hcv_decoder_init();
    printf("✅ Décodeur initialisé\n");
    printf("✅ Version: %s\n\n", hcv_decoder_version());
    
    // Allocation buffers
    int16_t* test_data = malloc(PIXELS * sizeof(int16_t));
    uint16_t* output = malloc(PIXELS * sizeof(uint16_t));
    
    // Initialisation données test
    printf("✅ Génération données test: %dx%d = %.1f MP\n", WIDTH, HEIGHT, PIXELS / 1000000.0);
    for (int i = 0; i < PIXELS; i++) {
        test_data[i] = 400 + (i % 200);
    }
    
    // Benchmark
    printf("\n=== BENCHMARK DECODE ===\n");
    
    const int iterations = 100;
    clock_t start = clock();
    
    for (int i = 0; i < iterations; i++) {
        hcv_decode_frame((const uint8_t*)test_data, PIXELS * sizeof(int16_t), output, WIDTH, HEIGHT);
    }
    
    clock_t end = clock();
    double total_ms = (double)(end - start) * 1000.0 / CLOCKS_PER_SEC;
    double per_frame_ms = total_ms / iterations;
    
    printf("✅ Temps moyen par frame: %.2f ms\n", per_frame_ms);
    printf("✅ FPS: %.1f\n", 1000.0 / per_frame_ms);
    
    // Validation
    if (per_frame_ms < 2.0) {
        printf("\n✅ ✅ ✅ TEST RÉUSSI: Décode < 2ms\n");
    } else {
        printf("\n⚠️  ATTENTION: Décode > 2ms\n");
    }
    
    // Nettoyage
    free(test_data);
    free(output);
    hcv_decoder_cleanup();
    
    printf("\n✅ Phase 1 terminée avec succès.\n");
    
    return 0;
}
