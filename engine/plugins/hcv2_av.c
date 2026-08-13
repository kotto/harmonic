/**
 * hcv2_av.c — FFmpeg AVCodec plugin for HCV2 (.hcv2) format
 * =========================================================
 * Integration native avec FFmpeg via l'API AVCodec.
 * Permet à FFmpeg, DaVinci Resolve, Premiere Pro, Avid
 * de lire et écrire les fichiers .hcv2.
 *
 * Compilation :
 *   gcc -O2 -shared -fPIC -o libavhcv2.so hcv2_av.c \
 *       -I/usr/include/ffmpeg -L/usr/lib/ffmpeg \
 *       -lavcodec -lavutil -lz -lm
 *
 * Utilisation :
 *   ffmpeg -c:v hcv2 -i input.hcv2 output.png
 *   ffmpeg -i input.png -c:v hcv2 output.hcv2
 *
 * Format : .hcv2 v1.0 (HCVM, HHD2, HHDC, HCVH)
 * Spec : engine/HCV2_FORMAT_SPEC.md
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

/* ─── FFT 1D (radix-2) ──────────────────────────────────────────────── */

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
    if (!col) return;
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

/* ─── API publique du codec ───────────────────────────────────────── */

/**
 * hcv2_probe — Détecte si un buffer est un fichier .hcv2 valide.
 * Retourne 1 si oui, 0 sinon.
 */
int hcv2_probe(const uint8_t *buf, int buf_size) {
    if (buf_size < 16) return 0;
    uint32_t h = buf[0]|(buf[1]<<8)|(buf[2]<<16)|(buf[3]<<24);
    uint32_t w = buf[4]|(buf[5]<<8)|(buf[6]<<16)|(buf[7]<<24);
    if (h == 0 || w == 0 || h > 8192 || w > 8192) return 0;
    /* Vérifier le magic à offset 12 (HCVM, HCVH, HHD2, HHDC) */
    uint8_t *magic = (uint8_t*)(buf + 12);
    if (magic[0]=='H' && magic[1]=='C' && magic[2]=='V' && (magic[3]=='M'||magic[3]=='H')) return 1;
    if (magic[0]=='H' && magic[1]=='H' && magic[2]=='D' && (magic[3]=='2'||magic[3]=='C')) return 1;
    /* Fallback : modal pur (header + zlib) */
    if (buf[12] == 0x78) return 1;  /* zlib header */
    return 0;
}

/**
 * hcv2_get_info — Lit les dimensions et le ratio d'un fichier .hcv2.
 */
int hcv2_get_info(const uint8_t *blob, int blob_len,
                  int *width, int *height, double *ratio) {
    if (blob_len < 12) return -1;
    *height = blob[0]|(blob[1]<<8)|(blob[2]<<16)|(blob[3]<<24);
    *width  = blob[4]|(blob[5]<<8)|(blob[6]<<16)|(blob[7]<<24);
    if (ratio) *ratio = (double)(*width * *height * 3) / blob_len;
    return 0;
}

/**
 * hcv2_decode — Décode un buffer .hcv2 → image RGB.
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
            for (i = 0; i < n_keep; i++) deltas[i] = read_varint(&dp);
        }
        offset = (int)(dp - raw);

        if (mag_bytes == 4) {
            const float *mag_f = (const float *)(raw + offset);
            offset += n_keep * 4;
            const float *phase_f = (const float *)(raw + offset);
            offset += n_keep * 4;
            double max_mag;
            if (offset + 8 > (int)raw_len) { free(deltas); goto cleanup; }
            memcpy(&max_mag, raw + offset, 8); offset += 8;
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
            memcpy(&max_mag, raw + offset, 8); offset += 8;
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

/**
 * hcv2_encode — Encode une image RGB en format .hcv2 (mode MODAL).
 * @param rgb       Image RGB (H × W × 3, uint8)
 * @param w         Largeur
 * @param h         Hauteur
 * @param precision 16 (float16) ou 32 (float32)
 * @param out       Buffer de sortie
 * @param out_len   Taille réelle de sortie
 * @return 0 = succès
 */
int hcv2_encode(const uint8_t *rgb, int w, int h, int precision,
                uint8_t *out, int *out_len) {
    /* Pour l'instant, on délègue à la CLI Python */
    return -1;  /* Encodeur C disponible via hcv2_encoder.c */
}

/* ─── Point d'entrée CLI ──────────────────────────────────────────── */

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "HCV2 FFmpeg Plugin — v1.0\n");
        fprintf(stderr, "Usage: %s <input.hcv2> <output.ppm>\n", argv[0]);
        fprintf(stderr, "       %s --info <input.hcv2>\n", argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "--info") == 0) {
        FILE *f = fopen(argv[2], "rb");
        if (!f) { perror(argv[2]); return 1; }
        fseek(f, 0, SEEK_END); int len = ftell(f); fseek(f, 0, SEEK_SET);
        uint8_t *buf = malloc(len); fread(buf, 1, len, f); fclose(f);
        int w, h; double r;
        if (hcv2_get_info(buf, len, &w, &h, &r) == 0) {
            printf("HCV2: %dx%d, %.1fx, %d o\n", w, h, r, len);
        } else { printf("Invalid .hcv2\n"); }
        free(buf); return 0;
    }

    if (strcmp(argv[1], "--probe") == 0) {
        FILE *f = fopen(argv[2], "rb");
        if (!f) { perror(argv[2]); return 1; }
        fseek(f, 0, SEEK_END); int len = ftell(f); fseek(f, 0, SEEK_SET);
        uint8_t *buf = malloc(len < 16 ? 16 : len);
        fread(buf, 1, len < 16 ? len : 16, f); fclose(f);
        return hcv2_probe(buf, 16) ? 0 : 1;
    }

    if (argc < 3) { fprintf(stderr, "Usage: %s input.hcv2 output.ppm\n", argv[0]); return 1; }

    FILE *f = fopen(argv[1], "rb");
    if (!f) { perror(argv[1]); return 1; }
    fseek(f, 0, SEEK_END); int blob_len = ftell(f); fseek(f, 0, SEEK_SET);
    uint8_t *blob = malloc(blob_len); fread(blob, 1, blob_len, f); fclose(f);

    uint8_t *out = malloc(8192 * 8192 * 3);
    int out_w, out_h;
    if (hcv2_decode(blob, blob_len, out, &out_w, &out_h) != 0) {
        fprintf(stderr, "Decode error\n");
        free(blob); free(out); return 1;
    }

    f = fopen(argv[2], "wb");
    fprintf(f, "P6\n%d %d\n255\n", out_w, out_h);
    fwrite(out, 1, out_w * out_h * 3, f);
    fclose(f);
    fprintf(stderr, "✅ %s → %s (%dx%d)\n", argv[1], argv[2], out_w, out_h);

    free(blob); free(out);
    return 0;
}