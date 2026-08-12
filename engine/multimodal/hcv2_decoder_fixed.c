/**
 * hcv2_decoder_fixed.c — Décodeur .hcv2 (version originale + precision_flag)
 * FFT 1D radix-2, varint, zlib, float16/float32 via precision_flag (header[8..11]).
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

#ifdef _MSC_VER
#define EXPORT __declspec(dllexport)
#else
#define EXPORT __attribute__((visibility("default")))
#endif

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
  int i, j;
  double complex *col;
  for (i = 0; i < h; i++) ifft_1d(m + i * w, w);
  col = (double complex *)malloc(h * sizeof(double complex));
  if (!col) return;
  for (j = 0; j < w; j++) {
    for (i = 0; i < h; i++) col[i] = m[i * w + j];
    ifft_1d(col, h);
    for (i = 0; i < h; i++) m[i * w + j] = col[i];
  }
  free(col);
}

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

EXPORT
int hc_decode(const uint8_t *blob, int blob_len,
                    uint8_t *out, uint32_t *out_w, uint32_t *out_h) {
  uint32_t h, w, pf;
  int mag_bytes, y_h, y_w, c_h, c_w, offset, i, j, c, k;
  unsigned long raw_len;
  uint8_t *raw;
  double *ycbcr[3];
  int ch_h, ch_w, ch_size, mask_bytes, n_keep;
  const uint8_t *mask, *dp;
  uint32_t *deltas;
  double complex *spectrum, *m;
  int fft_h, fft_w;

  if (blob_len < 12) return -1;
  h = blob[0] | (blob[1] << 8) | (blob[2] << 16) | (blob[3] << 24);
  w = blob[4] | (blob[5] << 8) | (blob[6] << 16) | (blob[7] << 24);
  pf = blob[8] | (blob[9] << 8) | (blob[10] << 16) | (blob[11] << 24);
  /* Versioning : byte 8 = 0x01 → v1, precision dans byte 9 */
  if (blob[8] == 0x01) {
    mag_bytes = (blob[9] == 1) ? 4 : 2;
  } else {
    /* Pré-v1 : byte 8 = precision_flag (0, 1, ou 64 pour anciens blobs) */
    mag_bytes = (pf == 1) ? 4 : 2;
  }
  if (h == 0 || w == 0 || h > 8192 || w > 8192) return -1;
  *out_w = w; *out_h = h;

  raw_len = (unsigned long)(blob_len * 50 + 1024 * 1024);
  raw = (uint8_t *)malloc(raw_len);
  if (!raw) return -1;
  if (uncompress(raw, &raw_len, blob + 12, (unsigned long)(blob_len - 12)) != Z_OK) {
    free(raw); return -1;
  }

  y_h = h; y_w = w;
  c_h = (h + 1) / 2; c_w = (w + 1) / 2;
  for (c = 0; c < 3; c++) ycbcr[c] = (double *)calloc(y_h * y_w, sizeof(double));

  offset = 0;
  for (c = 0; c < 3; c++) {
    ch_h = (c == 0) ? y_h : c_h;
    ch_w = (c == 0) ? y_w : c_w;
    ch_size = ch_h * ch_w;
    mask_bytes = (ch_size + 7) / 8;

    if (offset + mask_bytes > (int)raw_len) { free(raw); for (k = 0; k < 3; k++) free(ycbcr[k]); return -1; }
    mask = raw + offset;
    offset += mask_bytes;

    n_keep = 0;
    for (i = 0; i < ch_size; i++)
      if (mask[i / 8] & (1 << (i % 8))) n_keep++;

    dp = raw + offset;
    deltas = NULL;
    if (n_keep > 0) {
      deltas = (uint32_t *)malloc(n_keep * sizeof(uint32_t));
      for (i = 0; i < n_keep; i++) {
        if ((int)(dp - raw) >= (int)raw_len - 5) { free(raw); for (k = 0; k < 3; k++) free(ycbcr[k]); free(deltas); return -1; }
        deltas[i] = read_varint(&dp);
      }
    }
    offset = (int)(dp - raw);

    if (mag_bytes == 4) {
      const float *mag_f = (const float *)(raw + offset);
      offset += n_keep * 4;
      const float *phase_f = (const float *)(raw + offset);
      offset += n_keep * 4;
      double max_mag;
      if (offset + 8 > (int)raw_len) { free(raw); for (k = 0; k < 3; k++) free(ycbcr[k]); if (deltas) free(deltas); return -1; }
      memcpy(&max_mag, raw + offset, 8);
      offset += 8;
      spectrum = (double complex *)calloc(ch_size, sizeof(double complex));
      if (deltas) {
        uint32_t idx = 0;
        for (i = 0; i < n_keep; i++) { idx += deltas[i]; if (idx < (uint32_t)ch_size) spectrum[idx] = (double complex)(mag_f[i] * max_mag) * cexp(I * (double)phase_f[i]); }
        free(deltas);
      }
      fft_h = 1; fft_w = 1;
      while (fft_h < ch_h) fft_h <<= 1;
      while (fft_w < ch_w) fft_w <<= 1;
      m = (double complex *)calloc(fft_h * fft_w, sizeof(double complex));
      for (i = 0; i < ch_h; i++) for (j = 0; j < ch_w; j++) m[i * fft_w + j] = spectrum[i * ch_w + j];
      ifft2d(m, fft_h, fft_w);
      for (i = 0; i < ch_h; i++) for (j = 0; j < ch_w; j++) ycbcr[c][i * y_w + j] = creal(m[i * fft_w + j]);
      free(spectrum); free(m);
    } else {
      const uint16_t *mag_h = (const uint16_t *)(raw + offset);
      offset += n_keep * 2;
      const uint16_t *phase_h = (const uint16_t *)(raw + offset);
      offset += n_keep * 2;
      double max_mag;
      if (offset + 8 > (int)raw_len) { free(raw); for (k = 0; k < 3; k++) free(ycbcr[k]); if (deltas) free(deltas); return -1; }
      memcpy(&max_mag, raw + offset, 8);
      offset += 8;
      spectrum = (double complex *)calloc(ch_size, sizeof(double complex));
      if (deltas) {
        uint32_t idx = 0;
        for (i = 0; i < n_keep; i++) { idx += deltas[i]; if (idx < (uint32_t)ch_size) spectrum[idx] = (double complex)(half_to_float(mag_h[i]) * max_mag) * cexp(I * (double)half_to_float(phase_h[i])); }
        free(deltas);
      }
      fft_h = 1; fft_w = 1;
      while (fft_h < ch_h) fft_h <<= 1;
      while (fft_w < ch_w) fft_w <<= 1;
      m = (double complex *)calloc(fft_h * fft_w, sizeof(double complex));
      for (i = 0; i < ch_h; i++) for (j = 0; j < ch_w; j++) m[i * fft_w + j] = spectrum[i * ch_w + j];
      ifft2d(m, fft_h, fft_w);
      for (i = 0; i < ch_h; i++) for (j = 0; j < ch_w; j++) ycbcr[c][i * y_w + j] = creal(m[i * fft_w + j]);
      free(spectrum); free(m);
    }
  }
  free(raw);

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
  for (c = 0; c < 3; c++) free(ycbcr[c]);
  return 0;
}

int main() { return 0; }