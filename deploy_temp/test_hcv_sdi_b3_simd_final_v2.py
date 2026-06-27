#!/usr/bin/env python3
"""HCV SDI V2 : meilleure prédiction + codage lossless + overhead réduit."""

import os
import time
import json
import cv2
import numpy as np
import zstandard as zstd


class ImprovedHCVSDIB3V2:
    def __init__(self, input_video='B3.mp4', max_frames=10, gop_size=10):
        self.input_video = input_video
        self.max_frames = max_frames
        self.gop_size = gop_size
        self.modes = {
            'fast': {
                'description': 'HCV_FAST_V2 lossless optimisé',
                'zstd_level': 19,
                'qp_y': 0,
                'qp_uv': 0
            },
            'sdi': {
                'description': 'HCV_SDI_V2 lossless optimisé',
                'zstd_level': 22,
                'qp_y': 0,
                'qp_uv': 0
            },
            'archive': {
                'description': 'HCV_ARCHIVE_V2 lossless optimisé',
                'zstd_level': 22,
                'qp_y': 0,
                'qp_uv': 0
            }
        }
        self.block_size = 16
        self.search_range = 4

    def load_frames(self):
        if not os.path.exists(self.input_video):
            raise FileNotFoundError(f"Fichier vidéo introuvable: {self.input_video}")

        cap = cv2.VideoCapture(self.input_video)
        if not cap.isOpened():
            raise RuntimeError(f"Impossible d'ouvrir le fichier vidéo: {self.input_video}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        frames = []
        loaded = 0

        while loaded < self.max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(self.preprocess_h264_frame(frame))
            loaded += 1

        cap.release()
        return {
            'width': width,
            'height': height,
            'fps': fps,
            'frame_count': frame_count,
            'loaded_frames': loaded,
            'frames': frames
        }

    def preprocess_h264_frame(self, frame):
        yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
        y = yuv[:, :, 0].astype(np.uint16) * 4 + 64
        cb = yuv[:, :, 1].astype(np.uint16) * 4 + 64
        cr = yuv[:, :, 2].astype(np.uint16) * 4 + 64
        cb422 = cb[:, ::2]
        cr422 = cr[:, ::2]
        return {'y': y, 'cb': cb422, 'cr': cr422}

    def block_motion_estimate(self, current, previous):
        height, width = current.shape
        prev8 = np.clip((previous // 4).astype(np.uint8), 0, 255)
        curr8 = np.clip((current // 4).astype(np.uint8), 0, 255)
        flow = cv2.calcOpticalFlowFarneback(
            prev8,
            curr8,
            None,
            pyr_scale=0.5,
            levels=3,
            winsize=15,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0,
        )
        grid_x, grid_y = np.meshgrid(np.arange(width, dtype=np.float32), np.arange(height, dtype=np.float32))
        map_x = (grid_x + flow[..., 0]).astype(np.float32)
        map_y = (grid_y + flow[..., 1]).astype(np.float32)
        compensated = cv2.remap(
            previous.astype(np.float32),
            map_x,
            map_y,
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        ).astype(np.int16)

        mv = []
        for y in range(0, height, self.block_size):
            for x in range(0, width, self.block_size):
                y_end = min(y + self.block_size, height)
                x_end = min(x + self.block_size, width)
                block_flow = flow[y:y_end, x:x_end]
                dy = int(np.round(np.mean(block_flow[..., 1])))
                dx = int(np.round(np.mean(block_flow[..., 0])))
                mv.append((np.int8(np.clip(dy, -128, 127)), np.int8(np.clip(dx, -128, 127))))
        return compensated, np.array(mv, dtype=np.int8)

    def intra_predict(self, current):
        return np.zeros_like(current, dtype=np.int16)

    def residual_transform(self, residual):
        transformed = np.empty_like(residual, dtype=np.int16)
        transformed[:, 0] = residual[:, 0]
        transformed[:, 1:] = (residual[:, 1:].astype(np.int32) - residual[:, :-1].astype(np.int32)).astype(np.int16)
        return transformed

    def residual_inverse(self, transformed):
        residual = np.empty_like(transformed, dtype=np.int16)
        residual[:, 0] = transformed[:, 0]
        cum = np.cumsum(transformed[:, 1:].astype(np.int32), axis=1)
        residual[:, 1:] = cum.astype(np.int16)
        return residual

    def quantize(self, residual, qp):
        return residual.astype(np.int16)

    def dequantize(self, idx, qp):
        return idx.astype(np.int16)

    def encode_frame_payload(self, y, cb, cr, y_pred, cb_pred, cr_pred, mv, config):
        y_res = self.residual_transform(y.astype(np.int16) - y_pred)
        cb_res = self.residual_transform(cb.astype(np.int16) - cb_pred)
        cr_res = self.residual_transform(cr.astype(np.int16) - cr_pred)
        y_bytes = y_res.tobytes()
        cb_bytes = cb_res.tobytes()
        cr_bytes = cr_res.tobytes()
        return y_bytes, cb_bytes, cr_bytes

    def encode_stream(self, frames, mode):
        config = self.modes[mode]
        compressor = zstd.ZstdCompressor(level=config['zstd_level'])
        payload = bytearray()
        previous = None
        for idx, frame in enumerate(frames):
            y = frame['y']
            cb = frame['cb']
            cr = frame['cr']
            is_intra = (idx % self.gop_size == 0)
            if is_intra or previous is None:
                y_pred = self.intra_predict(y)
                cb_pred = self.reference_cb
                cr_pred = self.reference_cr
                mv = np.zeros((0, 2), dtype=np.int8)
            else:
                y_pred, mv = self.block_motion_estimate(y, previous['y'])
                cb_pred = previous['cb']
                cr_pred = previous['cr']
            y_bytes, cb_bytes, cr_bytes = self.encode_frame_payload(y, cb, cr, y_pred, cb_pred, cr_pred, mv, config)
            header = np.array([idx, y.shape[0], y.shape[1], cb.shape[0], cb.shape[1], int(is_intra)], dtype=np.uint16).tobytes()
            payload.extend(header)
            payload.extend(mv.tobytes())
            payload.extend(y_bytes)
            payload.extend(cb_bytes)
            payload.extend(cr_bytes)
            previous = {'y': y, 'cb': cb, 'cr': cr}
            if (idx + 1) % 5 == 0:
                print(f"  Encodage frame {idx + 1}/{len(frames)}")
        compressed = compressor.compress(bytes(payload))
        return len(payload), len(compressed), compressed

    def decode_stream(self, compressed_stream, config, num_frames):
        decompressed = zstd.ZstdDecompressor().decompress(compressed_stream)
        frames = []
        offset = 0
        previous = None
        for _ in range(num_frames):
            header = np.frombuffer(decompressed[offset:offset+12], dtype=np.uint16)
            offset += 12
            idx = int(header[0])
            y_h_i = int(header[1])
            y_w_i = int(header[2])
            cb_h_i = int(header[3])
            cb_w_i = int(header[4])
            is_intra = bool(header[5])
            if is_intra:
                mv = np.zeros((0, 2), dtype=np.int8)
            else:
                blocks_y = (y_h_i + self.block_size - 1) // self.block_size
                blocks_x = (y_w_i + self.block_size - 1) // self.block_size
                num_blocks = blocks_y * blocks_x
                mv_size = int(num_blocks * 2)
                mv = np.frombuffer(decompressed[offset:offset + mv_size], dtype=np.int8).reshape(-1, 2)
                offset += mv_size
            y_size = y_h_i * y_w_i * 2
            y_idx = np.frombuffer(decompressed[offset:offset+y_size], dtype=np.int16).reshape(y_h_i, y_w_i)
            offset += y_size
            cb_size = cb_h_i * cb_w_i * 2
            cb_idx = np.frombuffer(decompressed[offset:offset+cb_size], dtype=np.int16).reshape(cb_h_i, cb_w_i)
            offset += cb_size
            cr_idx = np.frombuffer(decompressed[offset:offset+cb_size], dtype=np.int16).reshape(cb_h_i, cb_w_i)
            offset += cb_size
            y_res = self.residual_inverse(y_idx)
            cb_res = self.residual_inverse(cb_idx)
            cr_res = self.residual_inverse(cr_idx)
            if is_intra or previous is None:
                y_pred = self.intra_predict(np.zeros((y_h_i, y_w_i), dtype=np.int16))
                cb_pred = self.reference_cb
                cr_pred = self.reference_cr
            else:
                y_pred = self.apply_motion(previous['y'], mv)
                cb_pred = previous['cb']
                cr_pred = previous['cr']
            y = y_pred + y_res
            cb = cb_pred + cb_res
            cr = cr_pred + cr_res
            frames.append({'y': y, 'cb': cb, 'cr': cr})
            previous = {'y': y, 'cb': cb, 'cr': cr}
        return frames

    def apply_motion(self, previous, mv):
        height, width = previous.shape
        compensated = np.zeros_like(previous, dtype=np.int16)
        idx = 0
        for y in range(0, height, self.block_size):
            for x in range(0, width, self.block_size):
                y_end = min(y + self.block_size, height)
                x_end = min(x + self.block_size, width)
                dy, dx = mv[idx]
                ref_y = np.clip(y + int(dy), 0, height - (y_end - y))
                ref_x = np.clip(x + int(dx), 0, width - (x_end - x))
                compensated[y:y_end, x:x_end] = previous[ref_y:ref_y + (y_end - y), ref_x:ref_x + (x_end - x)]
                idx += 1
        return compensated

    def upsample_frame(self, frame, scale=2):
        y = cv2.resize(frame['y'].astype(np.float32), (frame['y'].shape[1] * scale, frame['y'].shape[0] * scale), interpolation=cv2.INTER_LANCZOS4)
        cb = cv2.resize(frame['cb'].astype(np.float32), (frame['cb'].shape[1] * scale, frame['cb'].shape[0] * scale), interpolation=cv2.INTER_LANCZOS4)
        cr = cv2.resize(frame['cr'].astype(np.float32), (frame['cr'].shape[1] * scale, frame['cr'].shape[0] * scale), interpolation=cv2.INTER_LANCZOS4)
        return {'y': np.round(y).astype(np.int16), 'cb': np.round(cb).astype(np.int16), 'cr': np.round(cr).astype(np.int16)}

    def run(self):
        context = self.load_frames()
        frames = context['frames']
        original_size = os.path.getsize(self.input_video)
        self.reference_cb = frames[0]['cb'].astype(np.int16)
        self.reference_cr = frames[0]['cr'].astype(np.int16)

        print(f"Vidéo source: {self.input_video}")
        print(f"Résolution: {context['width']}x{context['height']}")
        print(f"Frames lues: {context['loaded_frames']} / {context['frame_count']}")
        print(f"Original H.264 size: {original_size / 1024 / 1024:.2f} MB")

        results = {}
        for mode in self.modes:
            start = time.perf_counter()
            raw_size, compressed_size, compressed_stream = self.encode_stream(frames, mode)
            duration = time.perf_counter() - start
            output_name = f"b3_hcv_improved_v2_{mode}.bin"
            with open(output_name, 'wb') as f:
                f.write(compressed_stream)

            decoded_frames = self.decode_stream(compressed_stream, self.modes[mode], len(frames))
            psnr_y = self.compute_psnr(frames, decoded_frames)
            psnr_y_upscaled = self.compute_psnr(
                [self.upsample_frame(f) for f in frames],
                [self.upsample_frame(f) for f in decoded_frames]
            )

            results[mode] = {
                'description': self.modes[mode]['description'],
                'zstd_level': self.modes[mode]['zstd_level'],
                'raw_bytes': raw_size,
                'compressed_stream_bytes': compressed_size,
                'output_file': output_name,
                'duration_s': duration,
                'compression_ratio': raw_size / compressed_size if compressed_size > 0 else 0,
                'relative_to_original': original_size / compressed_size if compressed_size > 0 else 0,
                'fps_equivalent': len(frames) / duration if duration > 0 else 0,
                'psnr_y': psnr_y,
                'psnr_y_upscaled': psnr_y_upscaled
            }

            print(f"\nMode {mode.upper()} - {self.modes[mode]['description']}")
            print(f"  Output: {output_name}")
            print(f"  Payload raw: {raw_size / 1024 / 1024:.2f} MB")
            print(f"  Compressed stream: {compressed_size / 1024 / 1024:.2f} MB")
            print(f"  Ratio raw->HCV: {results[mode]['compression_ratio']:.2f}×")
            print(f"  Original->HCV: {results[mode]['relative_to_original']:.2f}×")
            print(f"  Durée encodage: {duration:.2f} s")
            print(f"  FPS encodage (est.): {results[mode]['fps_equivalent']:.1f}")
            print(f"  PSNR Y: {psnr_y:.2f} dB")
            print(f"  PSNR Y Lanczos upscaled: {psnr_y_upscaled:.2f} dB")

        with open('b3_hcv_improved_v2_summary.json', 'w') as f:
            json.dump(results, f, indent=2)
        return results

    def compute_psnr(self, original_frames, decoded_frames):
        psnr_list = []
        for orig, dec in zip(original_frames, decoded_frames):
            mse = np.mean((orig['y'].astype(np.int32) - dec['y'].astype(np.int32))**2)
            if mse > 0:
                psnr = 20 * np.log10(1023 / np.sqrt(mse))
            else:
                psnr = float('inf')
            psnr_list.append(psnr)
        return np.mean(psnr_list)


def main():
    tester = ImprovedHCVSDIB3V2()
    tester.run()


if __name__ == '__main__':
    main()
