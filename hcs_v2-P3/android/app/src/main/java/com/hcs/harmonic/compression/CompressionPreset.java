package com.hcs.harmonic.compression;

/**
 * HCS Compression Presets
 * Mirror of Python COMPRESSION_PRESETS in hcs_video_compressor.py
 */
public enum CompressionPreset {

    /** Maximum compression for storage (ratio ~15:1) */
    ARCHIVAGE("archivage", "Archivage Long Terme",
            35, 0.40f, 2.0f, 15.0f,
            "Compression maximale. Ratio ~15:1. Vignettes ultracompactes."),

    /** Social networks, 8K quality on playback (ratio ~8:1) */
    SOCIAL_8K("social_8k", "Reseau Social 8K",
            60, 0.50f, 2.0f, 8.0f,
            "Optimise pour reseaux sociaux. Stockage compact, lecture 8K."),

    /** Professional audiovisual (ratio ~6:1) */
    AUDIOVISUEL_PRO("audiovisuel_pro", "Audiovisuel Professionnel",
            75, 0.75f, 1.5f, 6.0f,
            "Qualite professionnelle. Ratio ~6:1."),

    /** Cinema 4K/8K (ratio ~3:1) */
    CINEMA("cinema", "Cinema 4K/8K",
            92, 1.0f, 1.0f, 3.0f,
            "Qualite cinema, compression minimale. Ratio ~3:1."),

    /** Web streaming (ratio ~20:1) */
    WEB_STREAMING("web_streaming", "Web / Streaming",
            45, 0.50f, 2.0f, 20.0f,
            "Optimise pour diffusion web. Ratio ~20:1.");

    public final String key;
    public final String displayName;
    public final int jpegQuality;          // JPEG quality for compressed frames/images
    public final float scaleStore;         // Scale factor when storing (0.5 = half resolution)
    public final float scalePlayback;      // Upscale factor on playback
    public final float targetRatio;        // Target compression ratio
    public final String description;

    // Thumbnail config (always small, always displayed)
    public static final int THUMBNAIL_SIZE = 320;
    public static final int THUMBNAIL_JPEG_QUALITY = 70;

    CompressionPreset(String key, String displayName,
                      int jpegQuality, float scaleStore, float scalePlayback,
                      float targetRatio, String description) {
        this.key = key;
        this.displayName = displayName;
        this.jpegQuality = jpegQuality;
        this.scaleStore = scaleStore;
        this.scalePlayback = scalePlayback;
        this.targetRatio = targetRatio;
        this.description = description;
    }

    public static CompressionPreset fromKey(String key) {
        for (CompressionPreset p : values()) {
            if (p.key.equals(key)) return p;
        }
        return SOCIAL_8K; // default
    }
}
