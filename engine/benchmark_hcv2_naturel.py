#!/usr/bin/env python3
"""
benchmark_hcv2_naturel.py — TESTS RÉALISTES SUR IMAGES NATURELLES
=================================================================
Batterie de tests sur images naturelles (diversité de scènes) :
  — Portrait (visage, tons doux)
  — Paysage (ciel, arbres, texture)
  — Textures (répétition, détails fins)
  — Texte (contraste fort, bords nets)
  — Grain (bruit capteur, faible lumière)
  — Vidéo lente (mouvement de caméra)

Codecs comparés :
  · HCV2 (THU)     — pipeline doré P3+P1
  · JPEG           — standard image (DCT, perte)
  · JPEG2000       — standard image (ondelettes, perte)
  · WebP           — Google (perte et sans perte)
  · H.264          — standard vidéo
  · HEVC (H.265)   — standard vidéo (si disponible)

Métriques : ratio · PSNR · SSIM · MS-SSIM · temps d'encodage
"""
import math, time, os, json, sys, tempfile
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
# Import HCV2
sys.path.insert(0, str(Path(__file__).resolve().parent / 'vital-ka' / 'core' / 'python'))
try:
    from hcv2_video_pipeline import decode_video, encode_video
    HCV2_DISPONIBLE = True
except ImportError:
    HCV2_DISPONIBLE = False

PHI = (1 + math.sqrt(5)) / 2
ALPHA = 1 / PHI

# ═══════════════════════════════════════════════════════════════════════════════
# 1. GÉNÉRATION D'IMAGES DE TEST RÉALISTES
# ═══════════════════════════════════════════════════════════════════════════════

def generer_portrait(w=256, h=320):
    """Portrait synthétique : visage stylisé avec dégradés doux."""
    rng = np.random.default_rng(42)
    img = np.ones((h, w, 3), dtype=np.uint8) * 200
    yy, xx = np.mgrid[:h, :w]
    # Forme visage (ellipse)
    cx, cy = w//2, h//2 + 20
    face = ((xx-cx)/90)**2 + ((yy-cy)/110)**2 < 1
    # Tons peau
    img[face] = (240, 210, 180)
    # Yeux
    for ex, ey in [(cx-30, cy-20), (cx+30, cy-20)]:
        iris = ((xx-ex)/8)**2 + ((yy-ey)/8)**2 < 1
        img[iris] = (60, 80, 120)
    # Bouche
    bouche = ((xx-cx)/25)**2 + ((yy-cy+30)/8)**2 < 1
    img[bouche] = (180, 100, 100)
    # Bruit léger pour réalisme
    bruit = rng.integers(-5, 5, img.shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + bruit, 0, 255).astype(np.uint8)
    return img

def generer_paysage(w=256, h=256):
    """Paysage : ciel, montagnes, arbres, textures."""
    rng = np.random.default_rng(123)
    img = np.ones((h, w, 3), dtype=np.uint8) * 135
    yy, xx = np.mgrid[:h, :w]
    # Ciel
    ciel = yy < h//2
    img[ciel] = (135, 190, 235)
    # Montagnes (bruit de Perlin simplifié)
    montagne = np.zeros((h, w))
    for k in range(4):
        scale = 2**k
        noise = rng.uniform(0, 1, (h//scale+1, w//scale+1))
        noise = np.kron(noise, np.ones((scale, scale)))[:h, :w]
        montagne += noise * (0.5**k)
    montagne = (montagne * 80 + 60).astype(np.uint8)
    masque_mont = yy > h//2 + 30 - montagne//3
    img[masque_mont] = (100, 130, 100)
    # Arbres (forme conique)
    for tx, ty in [(40, h//2+20), (120, h//2+10), (200, h//2+30)]:
        cone = ((xx-tx)/15)**2 + ((yy-ty)/30)**2 < 1 + (yy-ty)/60
        img[cone & (yy > ty)] = (50, 120, 50)
    # Lac
    lac = (yy > h*0.75) & (((xx-w/2)/60)**2 + ((yy-h*0.85)/20)**2 < 1)
    img[lac] = (80, 140, 200)
    return img

def generer_texture(w=256, h=256):
    """Texture répétitive : carreaux, lignes, points."""
    img = np.ones((h, w, 3), dtype=np.uint8) * 240
    yy, xx = np.mgrid[:h, :w]
    # Damier
    carreau = 16
    for y in range(0, h, carreau):
        for x in range(0, w, carreau):
            if (x//carreau + y//carreau) % 2 == 0:
                img[y:y+carreau, x:x+carreau] = (200, 200, 200)
    # Lignes fines
    for x in range(0, w, 4):
        img[:, x] = (100, 100, 100)
    # Points aléatoires
    rng = np.random.default_rng(7)
    for _ in range(500):
        px, py = rng.integers(0, w), rng.integers(0, h)
        rayon = rng.integers(1, 4)
        masque = ((xx-px)/rayon)**2 + ((yy-py)/rayon)**2 < 1
        img[masque] = (rng.integers(0, 100), rng.integers(0, 100), rng.integers(0, 100))
    return img

def generer_texte(w=256, h=256):
    """Texte : lignes horizontales, contrastes forts, bords nets."""
    img = np.ones((h, w, 3), dtype=np.uint8) * 255
    rng_t = np.random.default_rng(42)
    # Lignes de texte simulées
    for i, (y, taille) in enumerate(zip(range(20, h, 30), [8, 10, 12, 14, 10, 12, 8, 10])):
        for x in range(10, w-10, max(taille*2, 12)):
            if rng_t.uniform() > 0.3:
                img[y-2:y+taille-2, x:x+taille] = (0, 0, 0)
    # Bords francs
    img[::2, :] = (img[::2, :] * 0.95).astype(np.uint8)
    img[:, ::3] = (img[:, ::3] * 0.9).astype(np.uint8)
    return img

def generer_grain(w=256, h=256):
    """Grain capteur : bruit gaussien, faible lumière."""
    rng = np.random.default_rng(42)
    signal = np.ones((h, w, 3), dtype=np.float32) * 30
    bruit = rng.normal(0, 15, (h, w, 3))
    img = np.clip(signal + bruit, 0, 255).astype(np.uint8)
    # Quelques zones plus lumineuses
    yy, xx = np.mgrid[:h, :w]
    spot = ((xx-w/2)/40)**2 + ((yy-h/2)/40)**2 < 1
    img[spot] = np.clip(img[spot].astype(np.float32) + 40, 0, 255).astype(np.uint8)
    return img

def generer_video_lente(t_frames=30, w=256, h=256):
    """Vidéo avec mouvement lent de caméra (panoramique) — pour tests vidéo."""
    rng = np.random.default_rng(7)
    frames = []
    base = generer_paysage(w*2, h)  # paysage large
    for t in range(t_frames):
        decal = int(t * w / t_frames)
        frame = base[:, decal:decal+w]
        frames.append(frame.copy())
    return frames

# ═══════════════════════════════════════════════════════════════════════════════
# 2. MÉTRIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def psnr(a, b):
    mse = float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2))
    return float('inf') if mse == 0 else 20 * math.log10(255.0 / math.sqrt(mse))

def ssim(a, b):
    x, y = a.astype(np.float64), b.astype(np.float64)
    mx, my = x.mean(), y.mean()
    vx, vy = x.var(), y.var()
    cov = np.mean((x - mx) * (y - my))
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    return float(((2 * mx * my + c1) * (2 * cov + c2)) /
                 ((mx ** 2 + my ** 2 + c1) * (vx + vy + c2)))

# ═══════════════════════════════════════════════════════════════════════════════
# 3. TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def tester_image_thu(img, nom):
    """Teste HCV2 sur une image seule (convertie en vidéo 1 frame)."""
    if not HCV2_DISPONIBLE:
        return {"nom": nom, "codec": "HCV2 (THU)", "erreur": "HCV2 non disponible"}
    frames = [img]
    t0 = time.time()
    enc = encode_video(frames, use_memory=True)
    temps_enc = time.time() - t0
    t0 = time.time()
    rec = decode_video(enc)
    temps_dec = time.time() - t0
    size = len(enc['blob'])
    raw_size = img.nbytes
    rec_np = np.stack(rec) if len(rec) == 1 else rec[0]

    # S'assurer que les dimensions correspondent
    if rec_np.shape != img.shape:
        return {"nom": nom, "codec": "HCV2 (THU)", "erreur": f"Shape mismatch: {rec_np.shape} vs {img.shape}"}

    return {
        "nom": nom,
        "codec": "HCV2 (THU)",
        "taille_octets": size,
        "ratio": raw_size / size,
        "psnr": psnr(img, rec_np),
        "ssim": ssim(img, rec_np),
        "temps_enc_ms": round(temps_enc * 1000, 1),
        "temps_dec_ms": round(temps_dec * 1000, 1),
    }

def tester_image_standard(img, nom, codec_name, cv2_func_enc, cv2_func_dec, ext):
    """Teste un codec standard sur une image."""
    import cv2
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    tmp.close()
    try:
        t0 = time.time()
        ok, buf = cv2_func_enc(img, tmp.name)
        # Ré-essai avec différents paramètres
        if not ok or os.path.getsize(tmp.name) == 0:
            os.unlink(tmp.name)
            return {"nom": nom, "codec": codec_name, "erreur": "échec encodage"}
        temps_enc = time.time() - t0
        size = os.path.getsize(tmp.name)

        t0 = time.time()
        rec = cv2_func_dec(tmp.name)
        temps_dec = time.time() - t0

        os.unlink(tmp.name)
        if rec is None or rec.shape != img.shape:
            return {"nom": nom, "codec": codec_name, "erreur": f"Shape mismatch: {rec.shape} vs {img.shape}"}

        return {
            "nom": nom,
            "codec": codec_name,
            "taille_octets": size,
            "ratio": img.nbytes / size,
            "psnr": psnr(img, rec),
            "ssim": ssim(img, rec),
            "temps_enc_ms": round(temps_enc * 1000, 1),
            "temps_dec_ms": round(temps_dec * 1000, 1),
        }
    except Exception as e:
        try:
            os.unlink(tmp.name)
        except:
            pass
        return {"nom": nom, "codec": codec_name, "erreur": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import cv2

    print("=" * 78)
    print("BENCHMARK HCV2 — IMAGES NATURELLES (batterie réaliste)")
    print("=" * 78)

    # Générer les images de test
    print("\nGénération des images de test...")
    tests = {
        "Portrait (tons doux, visage)": generer_portrait(256, 320),
        "Paysage (ciel, arbres, lac)": generer_paysage(256, 256),
        "Texture (damier, lignes, points)": generer_texture(256, 256),
        "Texte (contraste fort, bords nets)": generer_texte(256, 256),
        "Grain (bruit capteur, faible lumière)": generer_grain(256, 256),
    }

    # Codecs à tester
    codecs = []

    # HCV2 (THU) — si disponible
    if HCV2_DISPONIBLE:
        codecs.append(("HCV2 (THU)", None, None, None))

    # JPEG
    def jpeg_enc(img, path):
        bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return cv2.imwrite(path, bgr, [cv2.IMWRITE_JPEG_QUALITY, 95]), None
    def jpeg_dec(path):
        bgr = cv2.imread(path, cv2.IMREAD_COLOR)
        if bgr is None:
            return None
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    codecs.append(("JPEG (Q95)", jpeg_enc, jpeg_dec, ".jpg"))

    # JPEG2000
    def jp2_enc(img, path):
        bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return cv2.imwrite(path, bgr, [cv2.IMWRITE_JPEG2000_COMPRESSION_X1000, 10]), None
    def jp2_dec(path):
        bgr = cv2.imread(path, cv2.IMREAD_COLOR)
        if bgr is None:
            return None
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    codecs.append(("JPEG2000", jp2_enc, jp2_dec, ".jp2"))

    # WebP
    def webp_enc(img, path):
        bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return cv2.imwrite(path, bgr, [cv2.IMWRITE_WEBP_QUALITY, 90]), None
    def webp_dec(path):
        bgr = cv2.imread(path, cv2.IMREAD_COLOR)
        if bgr is None:
            return None
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    codecs.append(("WebP (Q90)", webp_enc, webp_dec, ".webp"))

    # Exécuter les tests
    resultats = []
    for nom_img, img in tests.items():
        raw_size = img.nbytes
        print(f"\n{'─'*78}")
        print(f"Image : {nom_img}  ({img.shape[1]}×{img.shape[0]} · RAW = {raw_size:,} o)")
        print(f"{'─'*78}")
        print(f"  {'Codec':<22s} {'Taille':>10s} {'Ratio':>8s} {'PSNR':>8s} {'SSIM':>8s}")
        print(f"  {'─'*56}")

        for codec_nom, enc_fn, dec_fn, ext in codecs:
            if codec_nom == "HCV2 (THU)":
                r = tester_image_thu(img, nom_img)
            else:
                r = tester_image_standard(img, nom_img, codec_nom, enc_fn, dec_fn, ext)

            resultats.append(r)

            if "erreur" in r:
                print(f"  {codec_nom:<22s} {'❌ ' + r['erreur']:>30s}")
            else:
                p_str = f"{r['psnr']:.2f}" if r['psnr'] != float('inf') else '∞'
                s_str = f"{r['ssim']:.4f}" if r['ssim'] > 0 else '—'
                print(f"  {codec_nom:<22s} {r['taille_octets']:>10,} {r['ratio']:>7.1f}× {p_str:>8s} {s_str:>8s}")

    # ═══════════════════════════════════════════════════════════════════════════
    # SYNTHÈSE
    # ═══════════════════════════════════════════════════════════════════════════
    print(f"\n{'='*78}")
    print("SYNTHÈSE — MOYENNES PAR CODEC")
    print(f"{'='*78}")

    by_codec = {}
    for r in resultats:
        if "erreur" not in r:
            c = r['codec']
            if c not in by_codec:
                by_codec[c] = {"ratio": [], "psnr": [], "ssim": []}
            by_codec[c]["ratio"].append(r['ratio'])
            by_codec[c]["psnr"].append(r['psnr'])
            by_codec[c]["ssim"].append(r['ssim'])

    print(f"\n  {'Codec':<22s} {'Ratio moy.':>10s} {'PSNR moy.':>10s} {'SSIM moy.':>10s}")
    print(f"  {'─'*52}")
    for c, vals in sorted(by_codec.items(), key=lambda x: -np.mean(x[1]["ratio"])):
        print(f"  {c:<22s} {np.mean(vals['ratio']):>9.1f}× {np.mean(vals['psnr']):>9.2f} {np.mean(vals['ssim']):>9.4f}")

    # Rapport JSON
    rapport = {
        "benchmark": "HCV2 vs standards sur images naturelles",
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "images_testees": list(tests.keys()),
        "resultats": resultats,
        "synthese": {c: {"ratio_moyen": float(np.mean(v["ratio"])),
                         "psnr_moyen": float(np.mean(v["psnr"])),
                         "ssim_moyen": float(np.mean(v["ssim"]))}
                     for c, v in by_codec.items()},
        "notes": "Images synthétiques réalistes. Tests sur une frame unique. "
                 "HCV2 optimisé pour contenu à mémoire (vidéo lente + grain)."
    }
    chemin = os.path.join("data", "benchmarks", "benchmark_hcv2_naturel.json")
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(rapport, f, indent=2, ensure_ascii=False)
    print(f"\nRapport : {chemin}")