/**
 * hcv2_encoder.c — Encodeur du format .hcv2 (codec modal harmonique, P1)
 * =========================================================================
 * Pipeline : RGB → YCbCr → FFT 2D → Parseval → seuil doré → varint → zlib
 * Format basé sur hcv2_modal_codec.py (Python → C).
 *
 * Compilation MSVC :
 *   cl /O2 /LD hcv2_encoder.c /Fehcv2_encoder.dll /link zlib.lib
 * Compilation Emscripten :
 *   emcc -O2 -s WASM=1 -s USE_ZLIB=1 -s EXPORTED_FUNCTIONS='["_hc_encode"]' \
 *        -s ALLOW_MEMORY_GROWTH=1 -o hcv2_encoder.js hcv2_encoder.c
 */

#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <complex.h>
#include <zlib.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif
#ifndef PHI
#define PHI 1.61803398874989484820
#endif

#ifdef _MSC_VER
#define EXPORT __declspec(dllexport)
#else
#define EXPORT __attribute__((visibility("default")))
#endif

/* ─── FFT 1D (identique au décodeur) ──────────────────────────────── */
static void fft_1d(double complex *x, int n) {
    for (int i = 1, j = 0; i < n; i++) {
        int bit = n >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) { double complex t = x[i]; x[i] = x[j]; x[j] = t; }
    }
    for (int len = 2; len <= n; len <<= 1) {
        double ang = -2.0 * M_PI / len;
        double complex wlen = cos(ang) + sin(ang) * I;
        for (int i = 0; i < n; i += len) {
            double complex w = 1.0 + 0.0 * I;
            for (int j = 0; j < len / 2; j++) {
                double complex u = x[i + j];
                double complex v = x[i + j + len / 2] * w;
                x[i + j] = u + v;
                x[i + j + len / 2] = u - v;
                w *= wlen;
            }
        }
    }
}

static void fft2d(double complex *m, int h, int w) {
    for (int i = 0; i < h; i++) fft_1d(m + i * w, w);
    double complex *col = (double complex *)malloc(h * sizeof(double complex));
    for (int j = 0; j < w; j++) {
        for (int i = 0; i < h; i++) col[i] = m[i * w + j];
        fft_1d(col, h);
        for (int i = 0; i < h; i++) m[i * w + j] = col[i];
    }
    free(col);
}

/* ─── Varint (écriture) ───────────────────────────────────────────── */
static void write_varint(uint8_t **data, uint32_t v) {
    while (v >= 0x80) { *(*data)++ = (v & 0x7F) | 0x80; v >>= 7; }
    *(*data)++ = v & 0x7F;
}

/* ─── Conversion float → float16 (half-precision) ─────────────────── */
static uint16_t float_to_half(float f) {
    uint32_t u;
    memcpy(&u, &f, 4);
    uint32_t sign = (u >> 31) & 1;
    int32_t exp = (int32_t)((u >> 23) & 0xFF) - 127 + 15;
    uint32_t mant = (u >> 13) & 0x3FF;
    if (exp <= 0) { /* subnormal / zero */
        if (exp < -10) return (uint16_t)(sign << 15);
        mant = (mant | 0x400) >> (1 - exp);
        return (uint16_t)((sign << 15) | mant);
    }
    if (exp >= 31) return (uint16_t)((sign << 15) | 0x7C00 | (mant ? 0x200 : 0));
    return (uint16_t)((sign << 15) | (exp << 10) | mant);
}

/* ─── Conversion RGB → YCbCr (matrice 3×3) ────────────────────────── */
static void rgb_to_ycbcr(const uint8_t *rgb, double *ycbcr, int n) {
    for (int i = 0; i < n; i++) {
        double r = rgb[i*3], g = rgb[i*3+1], b = rgb[i*3+2];
        ycbcr[i*3]   = 0.299 * r + 0.587 * g + 0.114 * b;
        ycbcr[i*3+1] = -0.169 * r - 0.331 * g + 0.500 * b + 128.0;
        ycbcr[i*3+2] = 0.500 * r - 0.419 * g - 0.081 * b + 128.0;
    }
}

/* ─── Encodeur principal ──────────────────────────────────────────── */

/**
 * hc_encode — Encode une image RGB en format .hcv2 (MODAL).
 *
 * @param rgb      Image RGB (H × W × 3, uint8)
 * @param w        Largeur
 * @param h        Hauteur
 * @param precision 16 (float16) ou 32 (float32)
 * @param out      Buffer de sortie (taille estimée : w*h*2)
 * @param out_len  Taille réelle de sortie
 * @return 0 = succès, -1 = erreur
 */
EXPORT
int hc_encode(const uint8_t *rgb, int w, int h, int precision,
              uint8_t *out, int *out_len) {
    if (!rgb || w <= 0 || h <= 0 || w > 8192 || h > 8192) return -1;
    
    int mag_bytes = (precision == 32) ? 4 : 2;
    int precision_flag = (precision == 32) ? 1 : 0;
    
    /* Conversion RGB → YCbCr */
    int n = h * w;
    double *ycbcr = (double *)malloc(n * 3 * sizeof(double));
    rgb_to_ycbcr(rgb, ycbcr, n);
    
    /* Header + payload */
    uint8_t *data = (uint8_t *)malloc(n * 3 * 8); /* buffer large (pire cas : n_keep ≈ n) */
    if (!data) { free(ycbcr); return -1; }
    int data_len = 0;
    
    /* Header 12 o */
    data[0] = h & 0xFF; data[1] = (h >> 8) & 0xFF;
    data[2] = (h >> 16) & 0xFF; data[3] = (h >> 24) & 0xFF;
    data[4] = w & 0xFF; data[5] = (w >> 8) & 0xFF;
    data[6] = (w >> 16) & 0xFF; data[7] = (w >> 24) & 0xFF;
    data[8] = precision_flag; data[9] = 0; data[10] = 0; data[11] = 0;
    data_len = 12;
    
    /* Pour chaque canal (Y, Cb, Cr) */
    for (int c = 0; c < 3; c++) {
        int ch_h = (c == 0) ? h : (h + 1) / 2;
        int ch_w = (c == 0) ? w : (w + 1) / 2;
        int ch_size = ch_h * ch_w;
        
        /* Extraire le canal */
        double *ch = (double *)malloc(ch_size * sizeof(double));
        if (c == 0) {
            for (int i = 0; i < ch_size; i++) ch[i] = ycbcr[i*3];
        } else {
            for (int i = 0; i < ch_h; i++)
                for (int j = 0; j < ch_w; j++)
                    ch[i * ch_w + j] = ycbcr[(i * 2 * w + j * 2) * 3 + c];
        }
        
        /* FFT 2D */
        int fft_h = 1, fft_w = 1;
        while (fft_h < ch_h) fft_h <<= 1;
        while (fft_w < ch_w) fft_w <<= 1;
        
        double complex *m = (double complex *)calloc(fft_h * fft_w, sizeof(double complex));
        for (int i = 0; i < ch_h; i++)
            for (int j = 0; j < ch_w; j++)
                m[i * fft_w + j] = ch[i * ch_w + j];
        fft2d(m, fft_h, fft_w);
        
        /* Parseval → seuil doré */
        double *p = (double *)malloc(ch_size * sizeof(double));
        double p_sum = 0.0;
        for (int i = 0; i < ch_h; i++)
            for (int j = 0; j < ch_w; j++) {
                double val = cabs(m[i * fft_w + j]);
                p[i * ch_w + j] = val * val;
                p_sum += p[i * ch_w + j];
            }
        
        double threshold = 1.0 / (PHI * ch_size);
        int n_keep = 0;
        for (int i = 0; i < ch_size; i++) {
            if (p[i] / p_sum > threshold) n_keep++;
        }
        
        /* Mask */
        int mask_bytes = (ch_size + 7) / 8;
        uint8_t *mask = (uint8_t *)calloc(mask_bytes, 1);
        uint32_t *idx = (uint32_t *)malloc(n_keep * sizeof(uint32_t));
        double *mag = (double *)malloc(n_keep * sizeof(double));
        double *phase = (double *)malloc(n_keep * sizeof(double));
        double max_mag = 0.0;
        
        int k = 0;
        for (int i = 0; i < ch_size; i++) {
            if (p[i] / p_sum > threshold) {
                mask[i / 8] |= (1 << (i % 8));
                idx[k] = i;
                double val = cabs(m[(i / ch_w) * fft_w + (i % ch_w)]);
                mag[k] = val;
                if (val > max_mag) max_mag = val;
                phase[k] = carg(m[(i / ch_w) * fft_w + (i % ch_w)]);
                k++;
            }
        }
        
        /* Écrire mask */
        memcpy(data + data_len, mask, mask_bytes);
        data_len += mask_bytes;
        
        /* Écrire varint (deltas des indices) */
        uint8_t *varint_buf = (uint8_t *)malloc(n_keep * 5);
        uint8_t *vp = varint_buf;
        uint32_t prev = 0;
        for (int i = 0; i < n_keep; i++) {
            write_varint(&vp, idx[i] - prev);
            prev = idx[i];
        }
        int varint_len = (int)(vp - varint_buf);
        memcpy(data + data_len, varint_buf, varint_len);
        data_len += varint_len;
        free(varint_buf);
        
        /* Écrire mags */
        if (mag_bytes == 4) {
            float *mag_f = (float *)malloc(n_keep * sizeof(float));
            for (int i = 0; i < n_keep; i++) {
                mag_f[i] = (float)(mag[i] / max_mag);
            }
            memcpy(data + data_len, mag_f, n_keep * 4);
            data_len += n_keep * 4;
            free(mag_f);
        } else {
            uint16_t *mag_h = (uint16_t *)malloc(n_keep * 2);
            for (int i = 0; i < n_keep; i++) {
                mag_h[i] = float_to_half((float)(mag[i] / max_mag));
            }
            memcpy(data + data_len, mag_h, n_keep * 2);
            data_len += n_keep * 2;
            free(mag_h);
        }
        
        /* Écrire phases */
        if (mag_bytes == 4) {
            float *ph_f = (float *)malloc(n_keep * sizeof(float));
            for (int i = 0; i < n_keep; i++) ph_f[i] = (float)phase[i];
            memcpy(data + data_len, ph_f, n_keep * 4);
            data_len += n_keep * 4;
            free(ph_f);
        } else {
            uint16_t *ph_h = (uint16_t *)malloc(n_keep * 2);
            for (int i = 0; i < n_keep; i++) ph_h[i] = float_to_half((float)phase[i]);
            memcpy(data + data_len, ph_h, n_keep * 2);
            data_len += n_keep * 2;
            free(ph_h);
        }
        
        /* Écrire max_mag */
        memcpy(data + data_len, &max_mag, 8);
        data_len += 8;
        
        free(ch); free(m); free(p); free(mask); free(idx); free(mag); free(phase);
    }
    
    free(ycbcr);
    
    /* Compression zlib du PAYLOAD uniquement (header 12 o non compressé —
    même format que le codec Python : header + zlib(payload)) */
    int payload_len = data_len - 12;
    uLongf comp_len = compressBound(payload_len);
    uint8_t *compressed = (uint8_t *)malloc(comp_len);
    if (compress2(compressed, &comp_len, data + 12, payload_len, 9) != Z_OK) {
        free(data); free(compressed); return -1;
    }
    
    /* Assembler le blob final : header 12 o + zlib(payload) */
    memcpy(out, data, 12);
    memcpy(out + 12, compressed, comp_len);
    *out_len = 12 + (int)comp_len;
    
    free(data); free(compressed);
    return 0;
}

/* Le main est dans le décodeur (hcv2_decoder.c) */