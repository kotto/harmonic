#!/usr/bin/env python3
"""Version améliorée HCV SDI B3 avec compression plus efficace que l'original H.264."""

import os
import time
import json
import cv2
import numpy as np
import zstandard as zstd


class ImprovedHCVSDIB3:
    def __init__(self, input_video='B3.mp4', max_frames=10, gop_size=10):
        self.input_video = input_video
        self.max_frames = max_frames
        self.gop_size = gop_size
        self.modes = {
            'fast': {
                'description': 'HCV_FAST haute qualité',
                'zstd_level': 22,
                'qp_y': 2,
                'qp_uv': 2
            },
            'sdi': {
                'description': 'HCV_SDI haute qualité',
                'zstd_level': 22,
                'qp_y': 2,
                'qp_uv': 2
            },
            'archive': {
                'description': 'HCV_ARCHIVE haute qualité',
                'zstd_level': 22,
                'qp_y': 1,
                'qp_uv': 1
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

            processed = self.preprocess_h264_frame(frame)
            frames.append(processed)
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
        """Conversion simple BGR -> YUV 10-bit SDI sans débruitage."""
        yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)

        # Passage direct en 10-bit SDI simulé (sans débruitage)
        y = yuv[:, :, 0].astype(np.uint16) * 4 + 64
        cb = yuv[:, :, 1].astype(np.uint16) * 4 + 64
        cr = yuv[:, :, 2].astype(np.uint16) * 4 + 64

        # Alignement 4:2:2 SDI (sous-échantillonnage horizontal)
        cb422 = cb[:, ::2]
        cr422 = cr[:, ::2]

        return {'y': y, 'cb': cb422, 'cr': cr422}

    def block_motion_estimate(self, current, previous):
        height, width = current.shape

        # Use dense optical flow to estimate frame motion, then derive block vectors.
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

        mv_y = []
        for y in range(0, height, self.block_size):
            for x in range(0, width, self.block_size):
                y_end = min(y + self.block_size, height)
                x_end = min(x + self.block_size, width)
                block_flow = flow[y:y_end, x:x_end]
                avg_dy = int(np.round(np.mean(block_flow[..., 1])))
                avg_dx = int(np.round(np.mean(block_flow[..., 0])))
                avg_dy = int(np.clip(avg_dy, -128, 127))
                avg_dx = int(np.clip(avg_dx, -128, 127))
                mv_y.append((avg_dy, avg_dx))

        motion_vectors = np.array(mv_y, dtype=np.int8)
        return compensated, motion_vectors

    def intra_predict(self, current):
        # For lossless, no prediction
        return np.zeros_like(current, dtype=np.int16)

    def quantize(self, residual, qp):
        if qp == 0:
            return residual.astype(np.int16)
        else:
            scale = 1 << qp
            return (residual // scale).astype(np.int16)

    def dequantize(self, idx, qp):
        if qp == 0:
            return idx.astype(np.int16)
        else:
            scale = 1 << qp
            return (idx * scale).astype(np.int16)

    def apply_motion(self, previous, mv):
        height, width = previous.shape
        compensated = np.zeros_like(previous, dtype=np.int16)
        idx = 0
        for y in range(0, height, self.block_size):
            for x in range(0, width, self.block_size):
                y_end = min(y + self.block_size, height)
                x_end = min(x + self.block_size, width)
                dy, dx = mv[idx]
                ref_y = np.clip(y + dy, 0, height - (y_end - y))
                ref_x = np.clip(x + dx, 0, width - (x_end - x))
                compensated[y:y_end, x:x_end] = previous[ref_y:ref_y + (y_end - y), ref_x:ref_x + (x_end - x)]
                idx += 1
        return compensated

    def encode_frames(self, frames, mode):
        config = self.modes[mode]
        compressor = zstd.ZstdCompressor(level=config['zstd_level'])

        output_packets = []
        total_raw_size = 0
        total_compressed_size = 0
        frame_sizes = []

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
                motion_vectors = np.zeros((0, 2), dtype=np.int8)
            else:
                y_pred, motion_vectors = self.block_motion_estimate(y, previous['y'])
                cb_pred = previous['cb']
                cr_pred = previous['cr']

            y_res = y.astype(np.int16) - y_pred
            cb_res = cb.astype(np.int16) - cb_pred
            cr_res = cr.astype(np.int16) - cr_pred

            y_idx = self.quantize(y_res, config['qp_y'])
            cb_idx = self.quantize(cb_res, config['qp_uv'])
            cr_idx = self.quantize(cr_res, config['qp_uv'])

            frame_header = np.array([idx, y.shape[0], y.shape[1], cb.shape[0], cb.shape[1], int(is_intra)], dtype=np.int32).tobytes()
            payload = frame_header + motion_vectors.tobytes() + y_idx.tobytes() + cb_idx.tobytes() + cr_idx.tobytes()
            compressed = compressor.compress(payload)

            total_raw_size += len(payload)
            total_compressed_size += len(compressed)
            frame_sizes.append(len(compressed))
            output_packets.append(compressed)
            previous = {'y': y, 'cb': cb, 'cr': cr}

        return output_packets, total_raw_size, total_compressed_size, frame_sizes

    def encode_stream(self, frames, mode):
        config = self.modes[mode]
        compressor = zstd.ZstdCompressor(level=config['zstd_level'])

        all_payload = bytearray()
        previous = None
        for idx, frame in enumerate(frames):
            y = frame['y']
            cb = frame['cb']
            cr = frame['cr']

            # GOP : Frame intra tous les gop_size frames
            is_intra = (idx % self.gop_size == 0)
            if is_intra or previous is None:
                y_pred = self.intra_predict(y)
                cb_pred = self.reference_cb
                cr_pred = self.reference_cr
                motion_vectors = np.zeros((0, 2), dtype=np.int8)
            else:
                y_pred, motion_vectors = self.block_motion_estimate(y, previous['y'])
                cb_pred = previous['cb']
                cr_pred = previous['cr']

            y_res = y.astype(np.int16) - y_pred
            cb_res = cb.astype(np.int16) - cb_pred
            cr_res = cr.astype(np.int16) - cr_pred

            y_idx = self.quantize(y_res, config['qp_y'])
            cb_idx = self.quantize(cb_res, config['qp_uv'])
            cr_idx = self.quantize(cr_res, config['qp_uv'])

            frame_header = np.array([idx, y.shape[0], y.shape[1], cb.shape[0], cb.shape[1], int(is_intra)], dtype=np.int32).tobytes()
            all_payload.extend(frame_header)
            all_payload.extend(motion_vectors.tobytes())
            all_payload.extend(y_idx.tobytes())
            all_payload.extend(cb_idx.tobytes())
            all_payload.extend(cr_idx.tobytes())

            previous = {'y': y, 'cb': cb, 'cr': cr}
            if (idx + 1) % 5 == 0:
                print(f"  Encodage frame {idx + 1}/{len(frames)}")

        compressed_stream = compressor.compress(bytes(all_payload))
        return len(all_payload), len(compressed_stream), compressed_stream

    def decode_stream(self, compressed_stream, config, num_frames):
        decompressed = zstd.ZstdDecompressor().decompress(compressed_stream)
        frames = []
        offset = 0
        previous = None
        for i in range(num_frames):
            header = np.frombuffer(decompressed[offset:offset+24], dtype=np.int32)
            offset += 24
            idx, y_h, y_w, cb_h, cb_w, is_intra = header
            if is_intra:
                mv = np.zeros((0, 2), dtype=np.int8)
            else:
                num_y = len(range(0, y_h, self.block_size))
                num_x = len(range(0, y_w, self.block_size))
                num_blocks = num_y * num_x
                mv_size = num_blocks * 2
                mv_flat = np.frombuffer(decompressed[offset:offset+mv_size], dtype=np.int8)
                offset += mv_size
                mv = mv_flat.reshape(-1, 2)
            y_size = y_h * y_w * 2  # int16
            y_idx = np.frombuffer(decompressed[offset:offset+y_size], dtype=np.int16).reshape(y_h, y_w)
            offset += y_size
            cb_size = cb_h * cb_w * 2
            cb_idx = np.frombuffer(decompressed[offset:offset+cb_size], dtype=np.int16).reshape(cb_h, cb_w)
            offset += cb_size
            cr_size = cb_h * cb_w * 2
            cr_idx = np.frombuffer(decompressed[offset:offset+cr_size], dtype=np.int16).reshape(cb_h, cb_w)
            offset += cr_size
            y_res = self.dequantize(y_idx, config['qp_y'])
            cb_res = self.dequantize(cb_idx, config['qp_uv'])
            cr_res = self.dequantize(cr_idx, config['qp_uv'])
            if is_intra or previous is None:
                y_pred = self.intra_predict(np.zeros((y_h, y_w), dtype=np.int16))
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

    def upsample_frame(self, frame, scale=2):
        y = cv2.resize(frame['y'].astype(np.float32), (frame['y'].shape[1] * scale, frame['y'].shape[0] * scale), interpolation=cv2.INTER_LANCZOS4)
        cb = cv2.resize(frame['cb'].astype(np.float32), (frame['cb'].shape[1] * scale, frame['cb'].shape[0] * scale), interpolation=cv2.INTER_LANCZOS4)
        cr = cv2.resize(frame['cr'].astype(np.float32), (frame['cr'].shape[1] * scale, frame['cr'].shape[0] * scale), interpolation=cv2.INTER_LANCZOS4)
        return {'y': np.round(y).astype(np.int16), 'cb': np.round(cb).astype(np.int16), 'cr': np.round(cr).astype(np.int16)}

    def run(self):
        context = self.load_frames()
        frames = context['frames']
        original_size = os.path.getsize(self.input_video)

        # Set chromatic reference from first frame
        self.reference_cb = frames[0]['cb'].astype(np.int16)
        self.reference_cr = frames[0]['cr'].astype(np.int16)

        print(f"Vidéo source: {self.input_video}")
        print(f"Résolution: {context['width']}x{context['height']}")
        print(f"Frames lues: {context['loaded_frames']} / {context['frame_count']}")
        print(f"Original H.264 size: {original_size / 1024 / 1024:.2f} MB")

        results = {}

        for mode in self.modes:
            start = time.perf_counter()
            packets, raw_size, compressed_size, frame_sizes = self.encode_frames(frames, mode)
            overall_raw, overall_compressed, compressed_stream = self.encode_stream(frames, mode)
            duration = time.perf_counter() - start

            output_name = f"b3_hcv_improved_{mode}.bin"
            with open(output_name, 'wb') as f:
                f.write(compressed_stream)

            # Decode and compute metrics
            decoded_frames = self.decode_stream(compressed_stream, self.modes[mode], len(frames))
            psnr_y_list = []
            psnr_y_upscaled_list = []
            for orig, dec in zip(frames, decoded_frames):
                mse_y = np.mean((orig['y'].astype(np.int32) - dec['y'].astype(np.int32))**2)
                if mse_y > 0:
                    psnr_y = 20 * np.log10(1023 / np.sqrt(mse_y))
                else:
                    psnr_y = float('inf')
                psnr_y_list.append(psnr_y)

                orig_up = self.upsample_frame(orig)
                dec_up = self.upsample_frame(dec)
                mse_y_up = np.mean((orig_up['y'].astype(np.int32) - dec_up['y'].astype(np.int32))**2)
                if mse_y_up > 0:
                    psnr_y_up = 20 * np.log10(1023 / np.sqrt(mse_y_up))
                else:
                    psnr_y_up = float('inf')
                psnr_y_upscaled_list.append(psnr_y_up)

            avg_psnr_y = np.mean(psnr_y_list)
            avg_psnr_y_upscaled = np.mean(psnr_y_upscaled_list)

            results[mode] = {
                'description': self.modes[mode]['description'],
                'qp_y': self.modes[mode]['qp_y'],
                'qp_uv': self.modes[mode]['qp_uv'],
                'zstd_level': self.modes[mode]['zstd_level'],
                'raw_bytes': raw_size,
                'compressed_stream_bytes': overall_compressed,
                'per_frame_bytes': sum(frame_sizes),
                'output_file': output_name,
                'duration_s': duration,
                'compression_ratio': raw_size / overall_compressed if overall_compressed > 0 else 0,
                'relative_to_original': original_size / overall_compressed if overall_compressed > 0 else 0,
                'fps_equivalent': len(frames) / duration if duration > 0 else 0,
                'psnr_y': avg_psnr_y,
                'psnr_y_upscaled': avg_psnr_y_upscaled
            }

            print(f"\nMode {mode.upper()} - {self.modes[mode]['description']}")
            print(f"  Output: {output_name}")
            print(f"  Payload raw: {raw_size / 1024 / 1024:.2f} MB")
            print(f"  Compressed stream: {overall_compressed / 1024 / 1024:.2f} MB")
            print(f"  Ratio raw->HCV: {results[mode]['compression_ratio']:.2f}×")
            print(f"  Original->HCV: {results[mode]['relative_to_original']:.2f}×")
            print(f"  Durée encodage: {duration:.2f} s")
            print(f"  FPS encodage (est.): {results[mode]['fps_equivalent']:.1f}")
            print(f"  PSNR Y: {avg_psnr_y:.2f} dB")
            print(f"  PSNR Y Lanczos upscaled: {avg_psnr_y_upscaled:.2f} dB")

        with open('b3_hcv_improved_summary.json', 'w') as f:
            json.dump(results, f, indent=2)

        return results


def main():
    tester = ImprovedHCVSDIB3()
    tester.run()


if __name__ == '__main__':
    main()
