package com.hcs.harmonic.model;

/**
 * Represents one compressed HCS media item (image or video).
 * The gallery only ever shows the thumbnail.
 * The full decompressed media is only materialised on playback.
 */
public class MediaItem {

    public enum Type { IMAGE, VIDEO }

    /** Unique DB row id */
    public long id;

    /** File type */
    public Type type;

    /** Absolute path to the .hcs compressed file on disk */
    public String hcsFilePath;

    /** Absolute path to the thumbnail JPEG on disk (fast gallery display) */
    public String thumbnailPath;

    /** Display name shown in gallery */
    public String displayName;

    /** Timestamp (ms since epoch) */
    public long timestamp;

    /** Compressed size in bytes */
    public long compressedSizeBytes;

    /** Estimated original size in bytes (for savings display) */
    public long originalSizeBytes;

    /** Compression ratio (e.g. 8.0 = 8:1) */
    public float compressionRatio;

    /** Preset key used ("social_8k", "archivage", etc.) */
    public String presetKey;

    /** Original width (before any upscaling/compression) */
    public int srcWidth;

    /** Original height */
    public int srcHeight;

    /** Output resolution on playback (after upscaling) */
    public int outWidth;
    public int outHeight;

    /** Duration in seconds (for video, 0 for images) */
    public float durationSeconds;

    // ──────────────────────────────────────────────────────────────

    public MediaItem() {}

    public boolean isVideo() { return type == Type.VIDEO; }
    public boolean isImage() { return type == Type.IMAGE; }

    /** Human-readable savings string */
    public String savingsLabel() {
        if (originalSizeBytes <= 0) return "";
        long saved = originalSizeBytes - compressedSizeBytes;
        double pct = 100.0 * saved / originalSizeBytes;
        return String.format("%.0f%% economise", pct);
    }

    /** E.g. "7680×4320 (8K)" */
    public String resolutionLabel() {
        if (outWidth >= 7000) return outWidth + "x" + outHeight + " (8K)";
        if (outWidth >= 3840) return outWidth + "x" + outHeight + " (4K)";
        if (outWidth >= 1920) return outWidth + "x" + outHeight + " (HD)";
        return outWidth + "x" + outHeight;
    }

    @Override
    public String toString() {
        return "MediaItem{id=" + id + ", type=" + type
                + ", name=" + displayName
                + ", ratio=" + compressionRatio + "}";
    }
}
