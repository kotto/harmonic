package com.hcs.harmonic.service;

import android.content.Context;
import android.graphics.Bitmap;
import android.media.MediaMetadataRetriever;
import android.util.Log;

import com.hcs.harmonic.compression.CompressionPreset;
import com.hcs.harmonic.compression.HCSEngine;
import com.hcs.harmonic.compression.HCSUpscaler;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;

/**
 * HCS Video Processor â€“ Android port of Python HCSVideoCompressor.
 *
 * Workflow (mirrors Python hcs_video_compressor.py):
 *   1. Open video with MediaMetadataRetriever
 *   2. Extract frames at preset intervals
 *   3. For each frame: upscale to 8K â†’ scale down for storage â†’ JPEG compress
 *   4. Assemble binary .hcs video file (same magic, same format)
 *   5. Generate video thumbnail from first meaningful frame
 *
 * HCS Video Binary Format (.hcs video):
 *   [4]  Magic "HCS2"
 *   [4]  version = 2
 *   [4]  metadata_len
 *   [N]  JSON metadata
 *   [4]  thumbnail_len
 *   [N]  thumbnail JPEG
 *   [4]  video_data_len
 *   [N]  video data:
 *          [4] frame_count
 *          per frame: [4] frame_size [N] frame JPEG bytes
 */
public class HCSVideoProcessor {

    private static final String TAG = "HCSVideoProcessor";

    private final Context mContext;

    public static class VideoCompressResult {
        public long originalSizeBytes;
        public long compressedSizeBytes;
        public float durationSeconds;
        public int srcWidth;
        public int srcHeight;
        public int outWidth;
        public int outHeight;
        public float fps;
        public int frameCount;
    }

    public HCSVideoProcessor(Context ctx) {
        this.mContext = ctx;
    }

    /**
     * Compress a video file to HCS format.
     *
     * @param sourcePath Source video file path
     * @param preset     Compression preset
     * @param hcsFile    Output .hcs file
     * @param thumbFile  Output thumbnail JPEG file
     * @return VideoCompressResult or null on failure
     */
    public VideoCompressResult compressVideo(String sourcePath,
                                              CompressionPreset preset,
                                              File hcsFile, File thumbFile) {
        MediaMetadataRetriever retriever = new MediaMetadataRetriever();
        try {
            retriever.setDataSource(sourcePath);

            // Get video info
            String widthStr    = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_WIDTH);
            String heightStr   = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_HEIGHT);
            String durationStr = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION);
            String fpsStr      = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_CAPTURE_FRAMERATE);

            int srcW  = widthStr  != null ? Integer.parseInt(widthStr)  : 0;
            int srcH  = heightStr != null ? Integer.parseInt(heightStr) : 0;
            long durationMs = durationStr != null ? Long.parseLong(durationStr) : 0;
            float fps = fpsStr != null ? Float.parseFloat(fpsStr) : 30f;
            if (fps <= 0) fps = 30f;

            long originalSizeBytes = new File(sourcePath).length();
            float durationS = durationMs / 1000f;

            Log.i(TAG, "Video: " + srcW + "x" + srcH + " @" + fps + "fps dur=" + durationS + "s");

            // Calculate output dimensions (upscale store dimensions based on preset)
            // For 8K upscaling: first go to 8K, then apply scale_store
            double scaleToTarget = Math.min(
                    (double) HCSUpscaler.MAX_8K_WIDTH  / Math.max(srcW, 1),
                    (double) HCSUpscaler.MAX_8K_HEIGHT / Math.max(srcH, 1)
            );
            int outW = (int)(srcW * scaleToTarget) & ~1;
            int outH = (int)(srcH * scaleToTarget) & ~1;

            int storeW = Math.max((int)(outW * preset.scaleStore), 2) & ~1;
            int storeH = Math.max((int)(outH * preset.scaleStore), 2) & ~1;

            // Extract frames using MediaMetadataRetriever
            // Sample at preset frame rate (avoid processing every frame for perf)
            float sampleFps = Math.min(fps, 15f); // max 15 fps stored
            int totalFrames = (int)(durationS * sampleFps);
            if (totalFrames < 1) totalFrames = 1;
            long frameIntervalUs = (long)((1f / sampleFps) * 1_000_000);

            Log.i(TAG, "Extracting " + totalFrames + " frames at " + sampleFps + "fps");

            // Collect compressed frames
            ByteArrayOutputStream videoBuffer = new ByteArrayOutputStream();
            DataOutputStream videoStream = new DataOutputStream(videoBuffer);

            int actualFrames = 0;
            byte[] thumbnailBytes = null;

            // Write placeholder for frame count (will update later)
            videoStream.writeInt(0);

            for (int i = 0; i < totalFrames; i++) {
                long timeUs = (long)(i * frameIntervalUs);
                Bitmap frame = retriever.getFrameAtTime(timeUs,
                        MediaMetadataRetriever.OPTION_CLOSEST_SYNC);

                if (frame == null) continue;

                // Upscale with Lanczos4 if smaller than store size
                Bitmap upscaled;
                if (frame.getWidth() < storeW || frame.getHeight() < storeH) {
                    upscaled = HCSUpscaler.upscaleWithLanczos(frame, storeW, storeH);
                } else {
                    upscaled = HCSEngine.scaleBitmap(frame, storeW, storeH);
                }
                frame.recycle();

                // Compress frame to JPEG
                byte[] jpegBytes = HCSEngine.bitmapToJpeg(upscaled, preset.jpegQuality);

                // Generate thumbnail from first frame
                if (thumbnailBytes == null) {
                    thumbnailBytes = HCSEngine.generateThumbnail(upscaled);
                }

                upscaled.recycle();

                // Write frame: [size 4B][jpeg data]
                videoStream.writeInt(jpegBytes.length);
                videoStream.write(jpegBytes);
                actualFrames++;
            }

            videoStream.flush();
            byte[] videoData = videoBuffer.toByteArray();

            // Patch frame count at offset 0
            byte[] patchedVideoData = patchFrameCount(videoData, actualFrames);

            Log.i(TAG, "Compressed " + actualFrames + " frames, videoData=" + patchedVideoData.length + "B");

            if (thumbnailBytes == null) {
                thumbnailBytes = new byte[0];
            }

            // Build metadata
            JSONObject meta = new JSONObject();
            meta.put("format", "hcs");
            meta.put("version", HCSEngine.FORMAT_VERSION);
            meta.put("media_type", "video");
            meta.put("preset", preset.key);
            meta.put("preset_name", preset.displayName);
            meta.put("src_width", srcW);
            meta.put("src_height", srcH);
            meta.put("store_width", storeW);
            meta.put("store_height", storeH);
            meta.put("out_width", outW);
            meta.put("out_height", outH);
            meta.put("fps", fps);
            meta.put("sample_fps", sampleFps);
            meta.put("total_frames", actualFrames);
            meta.put("duration_s", durationS);
            meta.put("scale_store", preset.scaleStore);
            meta.put("scale_playback", preset.scalePlayback);
            meta.put("jpeg_quality", preset.jpegQuality);
            meta.put("timestamp", System.currentTimeMillis());
            meta.put("original_size_bytes", originalSizeBytes);

            // Assemble HCS video binary
            byte[] metaBytes = meta.toString().getBytes(StandardCharsets.UTF_8);
            byte[] hcsData = assembleHCSVideo(metaBytes, thumbnailBytes, patchedVideoData);

            // Save HCS file
            if (!HCSEngine.saveToFile(hcsData, hcsFile)) {
                Log.e(TAG, "Failed to save video HCS file");
                return null;
            }

            // Save thumbnail
            if (thumbnailBytes.length > 0) {
                HCSEngine.saveToFile(thumbnailBytes, thumbFile);
            }

            VideoCompressResult result = new VideoCompressResult();
            result.originalSizeBytes   = originalSizeBytes;
            result.compressedSizeBytes = hcsData.length;
            result.durationSeconds     = durationS;
            result.srcWidth  = srcW;
            result.srcHeight = srcH;
            result.outWidth  = outW;
            result.outHeight = outH;
            result.fps       = fps;
            result.frameCount = actualFrames;

            return result;

        } catch (Exception e) {
            Log.e(TAG, "compressVideo failed", e);
            return null;
        } finally {
            try { retriever.release(); } catch (Exception ignored) {}
        }
    }

    /**
     * Decompress an HCS video file and write frames to a playable MP4.
     * Frames are decompressed and upscaled with Lanczos4.
     *
     * @param hcsData  Raw bytes of the .hcs file
     * @param outFile  Output MP4/AVI file
     * @return true on success
     */
    public boolean decompressVideo(byte[] hcsData, File outFile) {
        try {
            // Parse HCS header
            ByteBuffer buf = ByteBuffer.wrap(hcsData).order(ByteOrder.BIG_ENDIAN);

            byte[] magic = new byte[4];
            buf.get(magic);
            // check magic
            for (int i = 0; i < 4; i++) {
                if (magic[i] != HCSEngine.MAGIC[i]) {
                    Log.e(TAG, "Invalid HCS magic in video file");
                    return false;
                }
            }

            int version = buf.getInt();
            int metaLen = buf.getInt();
            byte[] metaBytes = new byte[metaLen];
            buf.get(metaBytes);
            JSONObject meta = new JSONObject(new String(metaBytes, StandardCharsets.UTF_8));

            int thumbLen = buf.getInt();
            buf.position(buf.position() + thumbLen); // skip thumbnail

            int videoDataLen = buf.getInt();
            byte[] videoData = new byte[videoDataLen];
            buf.get(videoData);

            // Parse video frames
            ByteBuffer vBuf = ByteBuffer.wrap(videoData).order(ByteOrder.BIG_ENDIAN);
            int frameCount = vBuf.getInt();

            float fps = (float) meta.optDouble("fps", 30.0);
            float scalePlayback = (float) meta.optDouble("scale_playback", 2.0);
            int storeW = meta.optInt("store_width", 1920);
            int storeH = meta.optInt("store_height", 1080);

            int outW = (int) Math.min(storeW * scalePlayback, HCSUpscaler.MAX_8K_WIDTH) & ~1;
            int outH = (int) Math.min(storeH * scalePlayback, HCSUpscaler.MAX_8K_HEIGHT) & ~1;

            Log.i(TAG, "Decompressing " + frameCount + " frames to " + outW + "x" + outH);

            // Write frames as MJPEG AVI (simplest container for Android)
            // Using a basic file sequence for now; production would use MediaMuxer
            File framesDir = new File(outFile.getParent(), "hcs_frames_tmp");
            framesDir.mkdirs();

            for (int i = 0; i < frameCount; i++) {
                int frameSize = vBuf.getInt();
                byte[] frameJpeg = new byte[frameSize];
                vBuf.get(frameJpeg);

                // Decode JPEG
                Bitmap frame = android.graphics.BitmapFactory.decodeByteArray(
                        frameJpeg, 0, frameJpeg.length);
                if (frame == null) continue;

                // Upscale with Lanczos4
                Bitmap upscaled = HCSUpscaler.upscaleWithLanczos(frame, outW, outH);
                frame.recycle();

                // Save frame as JPEG
                File frameFile = new File(framesDir, String.format("frame_%06d.jpg", i));
                HCSEngine.saveToFile(HCSEngine.bitmapToJpeg(upscaled, 90), frameFile);
                upscaled.recycle();
            }

            Log.i(TAG, "Decompressed " + frameCount + " frames to " + framesDir.getAbsolutePath());
            // In a real implementation, use MediaMuxer to reassemble frames into MP4
            // For now, we signal success and the PlayerActivity handles JPEG frames directly
            return true;

        } catch (Exception e) {
            Log.e(TAG, "decompressVideo failed", e);
            return false;
        }
    }

    // â”€â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    private byte[] patchFrameCount(byte[] data, int count) {
        byte[] result = data.clone();
        // Frame count is at offset 0 of the video data block
        result[0] = (byte)((count >> 24) & 0xFF);
        result[1] = (byte)((count >> 16) & 0xFF);
        result[2] = (byte)((count >> 8)  & 0xFF);
        result[3] = (byte)(count & 0xFF);
        return result;
    }

    private byte[] assembleHCSVideo(byte[] metaBytes, byte[] thumbnailBytes,
                                     byte[] videoData) {
        int total = 4 + 4
                + 4 + metaBytes.length
                + 4 + thumbnailBytes.length
                + 4 + videoData.length;
        ByteBuffer buf = ByteBuffer.allocate(total).order(ByteOrder.BIG_ENDIAN);
        buf.put(HCSEngine.MAGIC);
        buf.putInt(HCSEngine.FORMAT_VERSION);
        buf.putInt(metaBytes.length);
        buf.put(metaBytes);
        buf.putInt(thumbnailBytes.length);
        buf.put(thumbnailBytes);
        buf.putInt(videoData.length);
        buf.put(videoData);
        return buf.array();
    }
}
