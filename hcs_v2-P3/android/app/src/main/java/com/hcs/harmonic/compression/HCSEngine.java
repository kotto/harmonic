package com.hcs.harmonic.compression;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.media.MediaExtractor;
import android.media.MediaFormat;
import android.media.MediaMetadataRetriever;
import android.util.Log;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;

/**
 * HCS Engine – Android port of the Python HCS compression/decompression system.
 *
 * Binary format (.hcs):
 *   [4 bytes]  Magic "HCS2"
 *   [4 bytes]  uint32 version = 2
 *   [4 bytes]  uint32 metadata_len
 *   [N bytes]  JSON metadata (UTF-8)
 *   [4 bytes]  uint32 thumbnail_len
 *   [N bytes]  thumbnail JPEG (THUMBNAIL_SIZE x THUMBNAIL_SIZE)
 *   [4 bytes]  uint32 data_len
 *   [N bytes]  compressed image JPEG data
 *
 * This mirrors exactly the Python format so files can be cross-read.
 */
public class HCSEngine {

    private static final String TAG = "HCSEngine";
    public static final byte[] MAGIC = {'H', 'C', 'S', '2'};
    public static final int FORMAT_VERSION = 2;

    // ─── Types ──────────────────────────────────────────────────────────────
    public static class CompressResult {
        public final byte[] hcsData;
        public final byte[] thumbnailJpeg;
        public final JSONObject metadata;
        public final long originalSizeBytes;
        public final long compressedSizeBytes;
        public final float compressionRatio;

        public CompressResult(byte[] hcsData, byte[] thumbnailJpeg, JSONObject metadata,
                               long origBytes, long compBytes) {
            this.hcsData = hcsData;
            this.thumbnailJpeg = thumbnailJpeg;
            this.metadata = metadata;
            this.originalSizeBytes = origBytes;
            this.compressedSizeBytes = compBytes;
            this.compressionRatio = origBytes > 0 ? (float) origBytes / compBytes : 1f;
        }
    }

    public static class DecompressResult {
        public final Bitmap bitmap;    // null for video
        public final File videoFile;   // null for image
        public final JSONObject metadata;
        public final boolean isVideo;

        public DecompressResult(Bitmap bitmap, JSONObject metadata) {
            this.bitmap = bitmap;
            this.videoFile = null;
            this.metadata = metadata;
            this.isVideo = false;
        }

        public DecompressResult(File videoFile, JSONObject metadata) {
            this.bitmap = null;
            this.videoFile = videoFile;
            this.metadata = metadata;
            this.isVideo = true;
        }
    }

    // ─── Image Compression ──────────────────────────────────────────────────

    /**
     * Compress a Bitmap to HCS format with the given preset.
     * Transparent to user: stores compact, displays thumbnail.
     *
     * @param original  Source bitmap (any resolution)
     * @param preset    Compression preset
     * @param mediaType "image"
     * @return CompressResult containing HCS binary and thumbnail
     */
    public static CompressResult compressImage(Bitmap original, CompressionPreset preset,
                                                String mediaType) {
        try {
            int srcW = original.getWidth();
            int srcH = original.getHeight();
            long originalEstimatedBytes = (long) srcW * srcH * 4;

            // 1. Upscale to 8K first using OpenCV Lanczos4
            Bitmap upscaled = HCSUpscaler.upscaleTo8K(original);
            int outW = upscaled.getWidth();
            int outH = upscaled.getHeight();

            // 2. Scale down for storage (as per preset)
            int storeW = Math.max((int) (outW * preset.scaleStore), 2) & ~1;
            int storeH = Math.max((int) (outH * preset.scaleStore), 2) & ~1;
            Bitmap stored = scaleBitmap(upscaled, storeW, storeH);
            if (stored != upscaled) upscaled.recycle();

            // 3. Compress stored bitmap to JPEG
            byte[] jpegData = bitmapToJpeg(stored, preset.jpegQuality);

            // 4. Generate thumbnail (THUMBNAIL_SIZE px, square crop)
            byte[] thumbnail = generateThumbnail(stored);
            stored.recycle();

            // 5. Build metadata JSON
            JSONObject meta = new JSONObject();
            meta.put("format", "hcs");
            meta.put("version", FORMAT_VERSION);
            meta.put("preset", preset.key);
            meta.put("preset_name", preset.displayName);
            meta.put("media_type", mediaType);
            meta.put("src_width", srcW);
            meta.put("src_height", srcH);
            meta.put("store_width", storeW);
            meta.put("store_height", storeH);
            meta.put("out_width", outW);
            meta.put("out_height", outH);
            meta.put("jpeg_quality", preset.jpegQuality);
            meta.put("scale_store", preset.scaleStore);
            meta.put("scale_playback", preset.scalePlayback);
            meta.put("compression_ratio", (float) originalEstimatedBytes / jpegData.length);
            meta.put("timestamp", System.currentTimeMillis());

            // 6. Assemble HCS binary
            byte[] hcsData = assembleHCS(meta.toString().getBytes(StandardCharsets.UTF_8),
                    thumbnail, jpegData);

            return new CompressResult(hcsData, thumbnail, meta,
                    originalEstimatedBytes, hcsData.length);

        } catch (Exception e) {
            Log.e(TAG, "compressImage failed", e);
            return null;
        }
    }

    /**
     * Decompress an HCS image file back to full-resolution Bitmap (with 8K upscaling).
     */
    public static DecompressResult decompressImage(byte[] hcsData) {
        try {
            HCSParts parts = parseHCS(hcsData);
            if (parts == null) return null;

            // Decode compressed JPEG
            Bitmap stored = BitmapFactory.decodeByteArray(parts.data, 0, parts.data.length);
            if (stored == null) return null;

            // Extract scale_playback from metadata
            float scalePlayback = 2.0f;
            try {
                scalePlayback = (float) parts.metadata.getDouble("scale_playback");
            } catch (Exception ignored) {}

            // Upscale with OpenCV Lanczos4
            int tw = (int) Math.min(stored.getWidth() * scalePlayback, 7680) & ~1;
            int th = (int) Math.min(stored.getHeight() * scalePlayback, 4320) & ~1;

            Bitmap upscaled = HCSUpscaler.upscaleWithLanczos(stored, tw, th);
            stored.recycle();

            return new DecompressResult(upscaled, parts.metadata);

        } catch (Exception e) {
            Log.e(TAG, "decompressImage failed", e);
            return null;
        }
    }

    /**
     * Read only the thumbnail from an HCS file (fast – no full decompression).
     */
    public static Bitmap readThumbnail(byte[] hcsData) {
        try {
            HCSParts parts = parseHCS(hcsData);
            if (parts == null || parts.thumbnail == null || parts.thumbnail.length == 0)
                return null;
            return BitmapFactory.decodeByteArray(parts.thumbnail, 0, parts.thumbnail.length);
        } catch (Exception e) {
            Log.e(TAG, "readThumbnail failed", e);
            return null;
        }
    }

    /**
     * Read metadata JSON from an HCS file without full decompression.
     */
    public static JSONObject readMetadata(byte[] hcsData) {
        try {
            HCSParts parts = parseHCS(hcsData);
            return parts != null ? parts.metadata : null;
        } catch (Exception e) {
            Log.e(TAG, "readMetadata failed", e);
            return null;
        }
    }

    // ─── Binary format helpers ───────────────────────────────────────────────

    private static byte[] assembleHCS(byte[] metaBytes, byte[] thumbnailBytes,
                                       byte[] dataBytes) {
        int totalSize = 4 + 4 + 4 + metaBytes.length
                + 4 + thumbnailBytes.length
                + 4 + dataBytes.length;
        ByteBuffer buf = ByteBuffer.allocate(totalSize).order(ByteOrder.BIG_ENDIAN);
        buf.put(MAGIC);
        buf.putInt(FORMAT_VERSION);
        buf.putInt(metaBytes.length);
        buf.put(metaBytes);
        buf.putInt(thumbnailBytes.length);
        buf.put(thumbnailBytes);
        buf.putInt(dataBytes.length);
        buf.put(dataBytes);
        return buf.array();
    }

    private static class HCSParts {
        JSONObject metadata;
        byte[] thumbnail;
        byte[] data;
    }

    private static HCSParts parseHCS(byte[] raw) {
        try {
            ByteBuffer buf = ByteBuffer.wrap(raw).order(ByteOrder.BIG_ENDIAN);
            byte[] magic = new byte[4];
            buf.get(magic);
            // Verify magic
            for (int i = 0; i < 4; i++) {
                if (magic[i] != MAGIC[i]) {
                    Log.e(TAG, "Invalid HCS magic");
                    return null;
                }
            }
            int version = buf.getInt();
            if (version != FORMAT_VERSION) {
                Log.e(TAG, "Unsupported HCS version: " + version);
                return null;
            }
            int metaLen = buf.getInt();
            byte[] metaBytes = new byte[metaLen];
            buf.get(metaBytes);
            String metaStr = new String(metaBytes, StandardCharsets.UTF_8);

            int thumbLen = buf.getInt();
            byte[] thumbBytes = new byte[thumbLen];
            buf.get(thumbBytes);

            int dataLen = buf.getInt();
            byte[] dataBytes = new byte[dataLen];
            buf.get(dataBytes);

            HCSParts parts = new HCSParts();
            parts.metadata = new JSONObject(metaStr);
            parts.thumbnail = thumbBytes;
            parts.data = dataBytes;
            return parts;
        } catch (Exception e) {
            Log.e(TAG, "parseHCS failed", e);
            return null;
        }
    }

    // ─── Utilities ───────────────────────────────────────────────────────────

    public static Bitmap scaleBitmap(Bitmap src, int newW, int newH) {
        if (src.getWidth() == newW && src.getHeight() == newH) return src;
        return Bitmap.createScaledBitmap(src, newW, newH, true);
    }

    public static byte[] bitmapToJpeg(Bitmap bmp, int quality) {
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        bmp.compress(Bitmap.CompressFormat.JPEG, quality, baos);
        return baos.toByteArray();
    }

    public static byte[] generateThumbnail(Bitmap src) {
        int size = CompressionPreset.THUMBNAIL_SIZE;
        // Crop to square center
        int minDim = Math.min(src.getWidth(), src.getHeight());
        int x = (src.getWidth() - minDim) / 2;
        int y = (src.getHeight() - minDim) / 2;
        Bitmap cropped = Bitmap.createBitmap(src, x, y, minDim, minDim);
        Bitmap thumb = Bitmap.createScaledBitmap(cropped, size, size, true);
        if (cropped != src) cropped.recycle();
        byte[] result = bitmapToJpeg(thumb, CompressionPreset.THUMBNAIL_JPEG_QUALITY);
        thumb.recycle();
        return result;
    }

    /**
     * Save raw bytes to a file.
     */
    public static boolean saveToFile(byte[] data, File outputFile) {
        try {
            File parent = outputFile.getParentFile();
            if (parent != null && !parent.exists()) parent.mkdirs();
            try (FileOutputStream fos = new FileOutputStream(outputFile)) {
                fos.write(data);
            }
            return true;
        } catch (IOException e) {
            Log.e(TAG, "saveToFile failed: " + outputFile.getAbsolutePath(), e);
            return false;
        }
    }

    /**
     * Read a file completely into a byte array.
     */
    public static byte[] readFile(File file) {
        try (RandomAccessFile raf = new RandomAccessFile(file, "r")) {
            byte[] buf = new byte[(int) raf.length()];
            raf.readFully(buf);
            return buf;
        } catch (IOException e) {
            Log.e(TAG, "readFile failed: " + file.getAbsolutePath(), e);
            return null;
        }
    }

    /**
     * Estimate savings description string for UI display.
     */
    public static String formatSavings(long origBytes, long compBytes) {
        long saved = origBytes - compBytes;
        double pct = origBytes > 0 ? (100.0 * saved / origBytes) : 0;
        double ratio = origBytes > 0 ? (double) origBytes / compBytes : 1.0;
        return String.format("%.0f%% economise (x%.1f compression)",
                pct, ratio);
    }

    public static String formatBytes(long bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return String.format("%.1f KB", bytes / 1024.0);
        if (bytes < 1024L * 1024 * 1024) return String.format("%.1f MB", bytes / (1024.0 * 1024));
        return String.format("%.2f GB", bytes / (1024.0 * 1024 * 1024));
    }
}
