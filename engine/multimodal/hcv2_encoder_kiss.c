/**
 * hcv2_encoder_kiss.c — Encodeur HCV2 avec KissFFT (optimisé temps réel)
 * =========================================================================
 * Pipeline : RGB → YCbCr → FFT 2D (KissFFT) → Parseval → seuil doré → varint → zlib
 * KissFFT est ~10× plus rapide que la FFT radix-2 naïve, sans restriction de taille.
 */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <complex.h>
#include <zlib.h>
#include "kiss_fft.h"

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

static void write_varint(uint8_t **data, uint32_t v) {
    while (v >= 0x80) { *(*data)++ = (v & 0x7F) | 0x80; v >>= 7; }
    *(*data)++ = v & 0x7F;
}

static uint16_t float_to_half(float f) {
    uint32_t u; memcpy(&u, &f, 4);
    uint32_t sign = (u >> 31) & 1;
    int32_t exp = (int32_t)((u >> 23) & 0xFF) - 127 + 15;
    uint32_t mant = (u >> 13) & 0x3FF;
    if (exp <= 0) {
        if (exp < -10) return (uint16_t)(sign << 15);
        mant = (mant | 0x400) >> (1 - exp);
        return (uint16_t)((sign << 15) | mant);
    }
    if (exp >= 31) return (uint16_t)((sign << 15) | 0x7C00 | (mant ? 0x200 : 0));
    return (uint16_t)((sign << 15) | (exp << 10) | mant);
}

static void rgb_to_ycbcr(const uint8_t *rgb, double *ycbcr, int n) {
    for (int i = 0; i < n; i++) {
        double r = rgb[i*3], g = rgb[i*3+1], b = rgb[i*3+2];
        ycbcr[i*3]   = 0.299 * r + 0.587 * g + 0.114 * b;
        ycbcr[i*3+1] = -0.169 * r - 0.331 * g + 0.500 * b + 128.0;
        ycbcr[i*3+2] = 0.500 * r - 0.419 * g - 0.081 * b + 128.0;
    }
}

EXPORT
int hc_encode_kiss(const uint8_t *rgb, int w, int h, int precision,
                   int bit_depth, uint8_t *out, int *out_len) {
    if (!rgb || w <= 0 || h <= 0 || w > 8192 || h > 8192) return -1;
    
    int mag_bytes = (precision == 32) ? 4 : 2;
    int precision_flag = (precision == 32) ? 1 : 0;
    if (bit_depth <= 0) bit_depth = 8;
    
    int n = h * w;
    double *ycbcr = (double *)malloc(n * 3 * sizeof(double));
    rgb_to_ycbcr(rgb, ycbcr, n);
    
    uint8_t *data = (uint8_t *)malloc(n * 3 * 8);
    if (!data) { free(ycbcr); return -1; }
    int data_len = 0;
    
    /* Header v1.1 */
    data[0] = h & 0xFF; data[1] = (h >> 8) & 0xFF;
    data[2] = (h >> 16) & 0xFF; data[3] = (h >> 24) & 0xFF;
    data[4] = w & 0xFF; data[5] = (w >> 8) & 0xFF;
    data[6] = (w >> 16) & 0xFF; data[7] = (w >> 24) & 0xFF;
    data[8] = 0x01;             /* version v1 */
    data[9] = precision_flag;   /* 0 = float16, 1 = float32 */
    data[10] = bit_depth;       /* 8, 10, 12, 16 */
    data[11] = 0;               /* réservé */
    data_len = 12;
    
    for (int c = 0; c < 3; c++) {
        int ch_h = (c == 0) ? h : (h + 1) / 2;
        int ch_w = (c == 0) ? w : (w + 1) / 2;
        int ch_size = ch_h * ch_w;
        
        /* Extraire le canal */
        kiss_fft_cpx *m = (kiss_fft_cpx *)malloc(ch_size * sizeof(kiss_fft_cpx));
        if (c == 0) {
            for (int i = 0; i < ch_size; i++)
                m[i].r = (float)ycbcr[i*3], m[i].i = 0;
        } else {
            for (int i = 0; i < ch_h; i++)
                for (int j = 0; j < ch_w; j++)
                    m[i * ch_w + j].r = (float)ycbcr[(i*2*w + j*2)*3 + c], m[i * ch_w + j].i = 0;
        }
        
        /* FFT 2D avec KissFFT : d'abord les lignes, puis les colonnes */
        kiss_fft_cfg cfg_row = kiss_fft_alloc(ch_w, 0, NULL, NULL);
        kiss_fft_cfg cfg_col = kiss_fft_alloc(ch_h, 0, NULL, NULL);
        if (!cfg_row || !cfg_col) { free(m); return -1; }
        
        for (int i = 0; i < ch_h; i++)
            kiss_fft(cfg_row, m + i * ch_w, m + i * ch_w);
        
        kiss_fft_cpx *col = (kiss_fft_cpx *)malloc(ch_h * sizeof(kiss_fft_cpx));
        for (int j = 0; j < ch_w; j++) {
            for (int i = 0; i < ch_h; i++) col[i] = m[i * ch_w + j];
            kiss_fft(cfg_col, col, col);
            for (int i = 0; i < ch_h; i++) m[i * ch_w + j] = col[i];
        }
        free(col); free(cfg_row); free(cfg_col);
        
        /* Parseval → seuil doré */
        double *p = (double *)malloc(ch_size * sizeof(double));
        double p_sum = 0.0;
        for (int i = 0; i < ch_size; i++) {
            double val = sqrt(m[i].r * m[i].r + m[i].i * m[i].i);
            p[i] = val * val; p_sum += p[i];
        }
        
        double threshold = 1.0 / (PHI * ch_size);
        int n_keep = 0;
        for (int i = 0; i < ch_size; i++)
            if (p[i] / p_sum > threshold) n_keep++;
        
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
                double val = sqrt(m[i].r * m[i].r + m[i].i * m[i].i);
                mag[k] = val;
                if (val > max_mag) max_mag = val;
                phase[k] = atan2(m[i].i, m[i].r);
                k++;
            }
        }
        free(m); free(p);
        
        /* Écrire mask */
        memcpy(data + data_len, mask, mask_bytes);
        data_len += mask_bytes;
        
        /* Varint */
        uint8_t *varint_buf = (uint8_t *)malloc(n_keep * 5);
        uint8_t *vp = varint_buf;
        uint32_t prev = 0;
        for (int i = 0; i < n_keep; i++) { write_varint(&vp, idx[i] - prev); prev = idx[i]; }
        int varint_len = (int)(vp - varint_buf);
        memcpy(data + data_len, varint_buf, varint_len);
        data_len += varint_len;
        free(varint_buf);
        
        /* Mags + phases */
        if (mag_bytes == 4) {
            float *buf = (float *)malloc(n_keep * sizeof(float));
            for (int i = 0; i < n_keep; i++) buf[i] = (float)(mag[i] / max_mag);
            memcpy(data + data_len, buf, n_keep * 4);
            data_len += n_keep * 4;
            for (int i = 0; i < n_keep; i++) buf[i] = (float)phase[i];
            memcpy(data + data_len, buf, n_keep * 4);
            data_len += n_keep * 4;
            free(buf);
        } else {
            uint16_t *buf = (uint16_t *)malloc(n_keep * 2);
            for (int i = 0; i < n_keep; i++) buf[i] = float_to_half((float)(mag[i] / max_mag));
            memcpy(data + data_len, buf, n_keep * 2);
            data_len += n_keep * 2;
            for (int i = 0; i < n_keep; i++) buf[i] = float_to_half((float)phase[i]);
            memcpy(data + data_len, buf, n_keep * 2);
            data_len += n_keep * 2;
            free(buf);
        }
        
        memcpy(data + data_len, &max_mag, 8);
        data_len += 8;
        free(mask); free(idx); free(mag); free(phase);
    }
    free(ycbcr);
    
    /* zlib */
    int payload_len = data_len - 12;
    uLongf comp_len = compressBound(payload_len);
    uint8_t *compressed = (uint8_t *)malloc(comp_len);
    if (compress2(compressed, &comp_len, data + 12, payload_len, 9) != Z_OK) {
        free(data); free(compressed); return -1;
    }
    memcpy(out, data, 12);
    memcpy(out + 12, compressed, comp_len);
    *out_len = 12 + (int)comp_len;
    free(data); free(compressed);
    return 0;
}

int main() { return 0; }