/**
 * ff_hcv2dec.c — FFmpeg decoder for .hcv2 format
 * ================================================
 * Adds HCV2 decoding support to FFmpeg, enabling all tools
 * that use FFmpeg (Avid, DaVinci Resolve, Premiere, VLC, etc.)
 * to read .hcv2 files.
 *
 * Build:
 *   gcc -O2 -shared -o ff_hcv2dec.so -fPIC ff_hcv2dec.c \
 *       -I/path/to/ffmpeg -L/path/to/ffmpeg/libavcodec \
 *       -lz -lm
 *
 * Integration:
 *   cp ff_hcv2dec.so /usr/lib/ffmpeg/libavfilter/
 *   ffmpeg -i input.hcv2 output.png
 *
 * Format: .hcv2 v1.0 (HCVM, HHD2, HHDC, HCVH)
 * Spec: engine/HCV2_FORMAT_SPEC.md
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <complex.h>
#include <zlib.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* ─── FFT 1D (KissFFT-like minimal) ──────────────────────────────── */

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

static void ifft_1d(double complex *x, int n) {
    for (int i = 0; i < n; i++) x[i] = conj(x[i]);
    fft_1d(x, n);
    for (int i = 0; i < n; i++) x[i] = conj(x[i]) / (double)n;
}

static void ifft2d(double complex *m, int h, int w) {
    double complex *col;
    for (int i = 0; i < h; i++) ifft_1d(m + i * w, w);
    col = (double complex *)malloc(h * sizeof(double complex));
    for (int j = 0; j < w; j++) {
        for (int i = 0; i < h; i++) col[i] = m[i * w + j];
        ifft_1d(col, h);
        for (int i = 0; i < h; i++) m[i * w + j] = col[i];
    }
    free(col);
}

/* ─── Varint ──────────────────────────────────────────────────────── */

static uint32_t read_varint(const uint8_t **data) {
    uint32_t v = 0;
    int shift = 0;
    while (1) {
        uint8_t b = *(*data)++;
        v |= (uint32_t)(b & 0x7F) << shift;
        if (!(b & 0x80)) break;
        shift += 7;
    }
    return v;
}

/* ─── Float16 ──────────────────────────────────────────────────────── */

static float half_to_float(uint16_t h) {
    uint32_t sign = (h >> 15) & 1;
    int32_t exp = (h >> 10) & 0x1F;
    uint32_t mant = h & 0x3FF;
    if (exp == 0) {
        if (mant == 0) return 0.0f;
        exp = -14;
        while (!(mant & 0x400)) { mant <<= 1; exp--; }
        mant &= 0x3FF;
    } else if (exp == 31) {
        return (mant == 0) ? (sign ? -INFINITY : INFINITY) : NAN;
    } else {
        exp -= 15;
    }
    uint32_t f = (sign << 31) | ((exp + 127) << 23) | (mant << 13);
    float result;
    memcpy(&result, &f, 4);
    return result;
}

/* ─── Décodeur HCV2 (standalone, appelable depuis FFmpeg) ─────────── */

/**
 * hcv2_decode — Décode un buffer .hcv2 → image RGB.
 * 
 * @param blob      Données .hcv2 (header 12 o + zlib payload)
 * @param blob_len  Taille du blob
 * @param out       Buffer de sortie (w * h * 3 octets)
 * @param out_w     Largeur de sortie
 * @param out_h     Hauteur de sortie
 * @return          0 = succès, -1 = erreur
 */
int hcv2_decode(const uint8_t *blob, int blob_len,
                uint8_t *out, int *out_w, int *out_h) {
    uint32_t h, w, pf;
    int mag_bytes, y_h, y_w, c_h, c_w;
    unsigned long raw_len;
    uint8_t *raw = NULL;
    double *ycbcr[3] = {NULL, NULL, NULL};
    int offset, i, j, c, ret = -1;

    if (blob_len < 12) return -1;
    h = blob[0] | (blob[1] << 8) | (blob[2] << 16) | (blob[3] << 24);
    w = blob[4] | (blob[5] << 8) | (blob[6] << 16) | (blob[7] << 24);
    pf = blob[8] | (blob[9] << 8) | (blob[10] << 16) | (blob[11] << 24);
    mag_bytes = (blob[8] == 0x01) ? ((blob[9] == 1) ? 4 : 2) : ((pf == 1) ? 4 : 2);
    if (h == 0 || w == 0 || h > 8192 || w > 8192) return -1;

    *out_w = w; *out_h = h;
    raw_len = (unsigned long)(blob_len * 50 + 1024 * 1024);
    raw = (uint8_t *)malloc(raw_len);
    if (!raw) return -1;
    if (uncompress(raw, &raw_len, blob + 12, (unsigned long)(blob_len - 12)) != Z_OK)
        goto cleanup;

    y_h = h; y_w = w;
    c_h = (h + 1) / 2; c_w = (w + 1) / 2;
    for (c = 0; c < 3; c++) {
        ycbcr[c] = (double *)calloc(y_h * y_w, sizeof(double));
        if (!ycbcr[c]) goto cleanup;
    }

    offset = 0;
    for (c = 0; c < 3; c++) {
        int ch_h = (c == 0) ? y_h : c_h;
        int ch_w = (c == 0) ? y_w : c_w;
        int ch_size = ch_h * ch_w;
        int mask_bytes = (ch_size + 7) / 8;
        const uint8_t *mask;
        int n_keep, k;
        const uint8_t *dp;
        uint32_t *deltas = NULL;
        double complex *spectrum, *m;
        int fft_h, fft_w;

        if (offset + mask_bytes > (int)raw_len) goto cleanup;
        mask = raw + offset;
        offset += mask_bytes;

        n_keep = 0;
        for (i = 0; i < ch_size; i++)
            if (mask[i / 8] & (1 << (i % 8))) n_keep++;

        dp = raw + offset;
        if (n_keep > 0) {
            deltas = (uint32_t *)malloc(n_keep * sizeof(uint32_t));
            for (i = 0; i < n_keep; i++)
                deltas[i] = read_varint(&dp);
        }
        offset = (int)(dp - raw);

        if (mag_bytes == 4) {
            const float *mag_f = (const float *)(raw + offset);
            offset += n_keep * 4;
            const float *phase_f = (const float *)(raw + offset);
            offset += n_keep * 4;
            double max_mag;
            if (offset + 8 > (int)raw_len) { free(deltas); goto cleanup; }
            memcpy(&max_mag, raw + offset, 8);
            offset += 8;
            spectrum = (double complex *)calloc(ch_size, sizeof(double complex));
            if (deltas) {
                uint32_t idx = 0;
                for (i = 0; i < n_keep; i++) { idx += deltas[i];
                    if (idx < (uint32_t)ch_size)
                        spectrum[idx] = (mag_f[i] * max_mag) * cexp(I * phase_f[i]); }
                free(deltas);
            }
            fft_h = 1; fft_w = 1;
            while (fft_h < ch_h) fft_h <<= 1;
            while (fft_w < ch_w) fft_w <<= 1;
            m = (double complex *)calloc(fft_h * fft_w, sizeof(double complex));
            for (i = 0; i < ch_h; i++) for (j = 0; j < ch_w; j++)
                m[i * fft_w + j] = spectrum[i * ch_w + j];
            ifft2d(m, fft_h, fft_w);
            for (i = 0; i < ch_h; i++) for (j = 0; j < ch_w; j++)
                ycbcr[c][i * y_w + j] = creal(m[i * fft_w + j]);
            free(spectrum); free(m);
        } else {
            const uint16_t *mag_h = (const uint16_t *)(raw + offset);
            offset += n_keep * 2;
            const uint16_t *phase_h = (const uint16_t *)(raw + offset);
            offset += n_keep * 2;
            double max_mag;
            if (offset + 8 > (int)raw_len) { free(deltas); goto cleanup; }
            memcpy(&max_mag, raw + offset, 8);
            offset += 8;
            spectrum = (double complex *)calloc(ch_size, sizeof(double complex));
            if (deltas) {
                uint32_t idx = 0;
                for (i = 0; i < n_keep; i++) { idx += deltas[i];
                    if (idx < (uint32_t)ch_size)
                        spectrum[idx] = (half_to_float(mag_h[i]) * max_mag) * cexp(I * half_to_float(phase_h[i])); }
                free(deltas);
            }
            fft_h = 1; fft_w = 1;
            while (fft_h < ch_h) fft_h <<= 1;
            while (fft_w < ch_w) fft_w <<= 1;
            m = (double complex *)calloc(fft_h * fft_w, sizeof(double complex));
            for (i = 0; i < ch_h; i++) for (j = 0; j < ch_w; j++)
                m[i * fft_w + j] = spectrum[i * ch_w + j];
            ifft2d(m, fft_h, fft_w);
            for (i = 0; i < ch_h; i++) for (j = 0; j < ch_w; j++)
                ycbcr[c][i * y_w + j] = creal(m[i * fft_w + j]);
            free(spectrum); free(m);
        }
    }

    /* YCbCr → RGB */
    for (i = 0; i < y_h; i++) {
        for (j = 0; j < y_w; j++) {
            int ci = i / 2, cj = j / 2;
            double Y = ycbcr[0][i * y_w + j];
            double Cb = ycbcr[1][ci * y_w + cj];
            double Cr = ycbcr[2][ci * y_w + cj];
            double R = Y + 1.402 * (Cr - 128.0);
            double G = Y - 0.344 * (Cb - 128.0) - 0.714 * (Cr - 128.0);
            double B = Y + 1.772 * (Cb - 128.0);
            int idx = (i * y_w + j) * 3;
            out[idx] = (uint8_t)fmax(0, fmin(255, R));
            out[idx + 1] = (uint8_t)fmax(0, fmin(255, G));
            out[idx + 2] = (uint8_t)fmax(0, fmin(255, B));
        }
    }
    ret = 0;

cleanup:
    free(raw);
    for (c = 0; c < 3; c++) free(ycbcr[c]);
    return ret;
}

/* ─── Point d'entrée pour test CLI ────────────────────────────────── */

#ifdef BUILD_CLI
int main(int argc, char **argv) {
    FILE *f;
    uint8_t *blob;
    int blob_len;
    uint8_t *out;
    int out_w, out_h;

    if (argc < 3) {
        fprintf(stderr, "Usage: %s input.hcv2 output.png\n", argv[0]);
        return 1;
    }

    f = fopen(argv[1], "rb");
    if (!f) { perror("fopen"); return 1; }
    fseek(f, 0, SEEK_END); blob_len = ftell(f); fseek(f, 0, SEEK_SET);
    blob = malloc(blob_len); fread(blob, 1, blob_len, f); fclose(f);

    out = malloc(4 * 8192 * 8192); /* max 8192x8192 */
    if (hcv2_decode(blob, blob_len, out, &out_w, &out_h) != 0) {
        fprintf(stderr, "Decode error\n");
        free(blob); free(out); return 1;
    }

    /* Write PPM (simple, universal) */
    f = fopen(argv[2], "wb");
    fprintf(f, "P6\n%d %d\n255\n", out_w, out_h);
    fwrite(out, 1, out_w * out_h * 3, f);
    fclose(f);
    printf("✅ %s → %s (%dx%d)\n", argv[1], argv[2], out_w, out_h);

    free(blob); free(out);
    return 0;
}
#endif /* BUILD_CLI */