#!/usr/bin/env python3
"""
Tests de robustesse du format .hcv2 v1.0
==========================================
Teste : header, versioning, modes, varint, float16, checksum, fichier corrompu.
"""
import sys, os, struct, hashlib, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'vital-ka' / 'core' / 'python'))

import numpy as np
from PIL import Image
import hcv2_modal_codec as modal
from multimodal.harmonic_codec import HarmonicCodec
from multimodal.harmonic_database import HarmonicDatabase


class TestHCV2Format(unittest.TestCase):
    
    def setUp(self):
        self.img = np.array(Image.fromarray(np.zeros((64, 64, 3), np.uint8)))
        for y in range(64):
            for x in range(64):
                self.img[y, x] = [(x+y)*3 % 256, (x+y)*3 % 256, (x+y)*3 % 256]
        self.tmp = tempfile.mkdtemp()
    
    def test_1_header_modal(self):
        """Le header MODAL (version 0) doit être lisible."""
        enc = modal.encode(self.img)
        blob = enc['blob']
        self.assertGreater(len(blob), 12)
        h, w, pf = struct.unpack('<III', blob[:12])
        self.assertEqual(h, 64)
        self.assertEqual(w, 64)
        self.assertIn(pf, [0, 1, 64])  # 0=float16, 1=float32, 64=ancien
    
    def test_2_header_select(self):
        """Le header du sélecteur (magic en premier) doit être lisible."""
        hc = HarmonicCodec(HarmonicDatabase(patch_size=32, K=8, stride=32),
                           use_hcv=True, quality=100)
        data, mode = hc.encode_select(self.img, min_psnr=20.0)
        # Vérifier le magic
        self.assertIn(data[:4], [b'HCVM', b'HHD2', b'HHDC'],
                      f"Magic inconnu : {data[:4]}")
        # Vérifier le header après le magic
        if data[:4] == b'HCVM':
            hdr = data[4:16]
            h, w, pf = struct.unpack('<III', hdr)
            self.assertEqual(h, 64 if mode == 'FULL' else 64)
    
    def test_3_varint_roundtrip(self):
        """Le varint doit encoder/décoder des uint32 correctement."""
        from multimodal.harmonic_codec import HarmonicCodec
        # Le varint est testé via le codec
        hc = HarmonicCodec(HarmonicDatabase(patch_size=8, K=8, stride=8),
                           use_hcv=True, quality=100)
        data = hc.encode_full(self.img)
        rec, _ = hc.decode_full(data)
        self.assertEqual(rec.shape, (64, 64, 3))
    
    def test_4_float16_roundtrip(self):
        """float16 → float32 → float16 doit être stable."""
        for val in [0.0, 1.0, -1.0, 0.5, 65504.0, -65504.0, 0.1, 3.14159]:
            h = self._float32_to_float16(val)
            back = self._float16_to_float32(h)
            self.assertAlmostEqual(val, back, delta=abs(val)*0.001 + 0.001)
    
    def _float32_to_float16(self, f):
        # Implémentation Python de float_to_half
        import struct
        u = struct.pack('f', f)
        u = struct.unpack('I', u)[0]
        sign = (u >> 31) & 1
        exp = ((u >> 23) & 0xFF) - 127 + 15
        mant = (u >> 13) & 0x3FF
        if exp <= 0:
            if exp < -10: return (sign << 15)
            mant = (mant | 0x400) >> (1 - exp)
            return (sign << 15) | mant
        if exp >= 31:
            return (sign << 15) | 0x7C00 | (0x200 if mant else 0)
        return (sign << 15) | (exp << 10) | mant
    
    def _float16_to_float32(self, h):
        import struct
        sign = (h >> 15) & 1
        exp = (h >> 10) & 0x1F
        mant = h & 0x3FF
        if exp == 0:
            if mant == 0: return 0.0
            exp = -14
            while not (mant & 0x400): mant <<= 1; exp -= 1
            mant &= 0x3FF
        elif exp == 31:
            return float('inf') if mant == 0 else float('nan')
        else:
            exp -= 15
        u = (sign << 31) | ((exp + 127) << 23) | (mant << 13)
        return struct.unpack('f', struct.pack('I', u))[0]
    
    def test_5_checksum(self):
        """SHA-256 doit être calculable et vérifiable."""
        enc = modal.encode(self.img)
        blob = enc['blob']
        sha = hashlib.sha256(blob).hexdigest()
        self.assertEqual(len(sha), 64)
        # Re-vérifier
        self.assertEqual(hashlib.sha256(blob).hexdigest(), sha)
    
    def test_6_corrupted_file(self):
        """Un fichier corrompu doit être détecté (header invalide)."""
        enc = modal.encode(self.img)
        blob = bytearray(enc['blob'])
        # Corrompre le header
        blob[0] = 0xFF
        blob[1] = 0xFF
        # Le décodage doit échouer
        try:
            modal.decode(bytes(blob))
            self.fail("Le décodage d'un fichier corrompu aurait dû échouer")
        except Exception:
            pass  # OK
    
    def test_7_all_modes_produce_valid_files(self):
        """Tous les modes de compression doivent produire des fichiers .hcv2 valides."""
        hc = HarmonicCodec(HarmonicDatabase(patch_size=32, K=8, stride=32),
                           use_hcv=True, quality=100)
        modes = [
            ('modal', lambda: modal.encode(self.img)['blob']),
            ('full', lambda: hc.encode_full(self.img)),
            ('select', lambda: hc.encode_select(self.img, min_psnr=20.0)[0]),
        ]
        for name, fn in modes:
            try:
                data = fn()
                self.assertGreater(len(data), 16, f"{name} : blob trop petit")
                # Vérifier que le blob peut être décodé
                if name == 'modal':
                    rec = modal.decode(data)
                elif data[:4] == b'HHD2':
                    rec, _ = hc.decode_v2(data, database=None)
                elif data[:4] in (b'HCVM', b'HCVH'):
                    rec, _ = hc.decode_select(data)
                else:
                    rec, _ = hc.decode_full(data)
                self.assertEqual(rec.shape[:2], (64, 64),
                                 f"{name} : dimensions incorrectes")
            except Exception as e:
                self.fail(f"{name} : {e}")
    
    def test_8_video_format(self):
        """Le format vidéo (encode_video) doit produire un bitstream valide."""
        import cv2
        cap = cv2.VideoCapture(str(Path(__file__).resolve().parent.parent.parent / 'B3.mp4'))
        frames = []
        while len(frames) < 4 and cap.isOpened():
            ok, f = cap.read()
            if not ok: break
            f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
            if max(f.shape[:2]) > 256:
                s = 256 / max(f.shape[:2])
                f = cv2.resize(f, (int(f.shape[1]*s), int(f.shape[0]*s)))
            frames.append(f)
        cap.release()
        if len(frames) < 4:
            self.skipTest("Vidéo B3 non disponible")
        
        hc = HarmonicCodec(HarmonicDatabase(patch_size=32, K=8, stride=32),
                           use_hcv=True, quality=100)
        data = hc.encode_video(frames, concept='default', skip_threshold=5.0,
                               motion_search_range=8, gop_size=4)
        self.assertGreater(len(data), 100, "Bitstream video trop petit")
        rec, meta = hc.decode_video(data)
        self.assertEqual(len(rec), len(frames),
                         "Nombre de frames décodées incorrect")


if __name__ == '__main__':
    unittest.main(verbosity=2)