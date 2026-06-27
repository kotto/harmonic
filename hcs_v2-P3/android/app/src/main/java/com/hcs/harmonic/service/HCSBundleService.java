package com.hcs.harmonic.service;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.util.Log;

import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;

import com.hcs.harmonic.compression.CompressionPreset;
import com.hcs.harmonic.compression.HCSEngine;
import com.hcs.harmonic.model.MediaItem;
import com.hcs.harmonic.storage.HCSMediaDatabase;
import com.hcs.harmonic.ui.MainActivity;

import org.json.JSONObject;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * HCS Bundle Service – Background service that:
 * 1. Receives compress requests (from CameraActivity or external intents)
 * 2. Compresses images/videos transparently with HCS engine
 * 3. Stores only the compressed .hcs file + thumbnail on disk
 * 4. Indexes everything in HCSMediaDatabase
 * 5. Notifies the user of space saved
 *
 * The user NEVER manually interacts with this service.
 * Compression is FULLY TRANSPARENT.
 */
public class HCSBundleService extends Service {

    private static final String TAG = "HCSBundleService";
    private static final String CHANNEL_ID = "hcs_bundle_channel";
    private static final int NOTIF_ID_ONGOING = 1001;
    private static final int NOTIF_ID_DONE    = 1002;

    // Intent action constants
    public static final String ACTION_COMPRESS_IMAGE = "com.hcs.harmonic.COMPRESS_IMAGE";
    public static final String ACTION_COMPRESS_VIDEO = "com.hcs.harmonic.COMPRESS_VIDEO";

    // Intent extras
    public static final String EXTRA_SOURCE_PATH   = "source_path";
    public static final String EXTRA_PRESET        = "preset";
    public static final String EXTRA_DELETE_SOURCE = "delete_source";

    // HCS storage directory name
    public static final String HCS_DIR_NAME = "HCS_Bundle";
    public static final String THUMB_DIR_NAME = "HCS_Thumbnails";

    private ExecutorService mExecutor;
    private HCSMediaDatabase mDatabase;
    private Handler mMainHandler;
    private CompressionPreset mDefaultPreset = CompressionPreset.SOCIAL_8K;

    // ─── Service lifecycle ────────────────────────────────────────────────

    @Override
    public void onCreate() {
        super.onCreate();
        mExecutor = Executors.newSingleThreadExecutor();
        mDatabase = HCSMediaDatabase.getInstance(this);
        mMainHandler = new Handler(Looper.getMainLooper());
        createNotificationChannel();
        Log.i(TAG, "HCS Bundle Service created");
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent == null) return START_NOT_STICKY;

        String action = intent.getAction();
        if (action == null) return START_NOT_STICKY;

        String sourcePath = intent.getStringExtra(EXTRA_SOURCE_PATH);
        String presetKey  = intent.getStringExtra(EXTRA_PRESET);
        boolean deleteSource = intent.getBooleanExtra(EXTRA_DELETE_SOURCE, false);

        if (sourcePath == null || sourcePath.isEmpty()) {
            Log.w(TAG, "No source path provided");
            return START_NOT_STICKY;
        }

        CompressionPreset preset = presetKey != null
                ? CompressionPreset.fromKey(presetKey)
                : mDefaultPreset;

        // Show foreground notification while compressing
        startForeground(NOTIF_ID_ONGOING, buildOngoingNotification("Compression HCS en cours..."));

        if (ACTION_COMPRESS_IMAGE.equals(action)) {
            mExecutor.submit(() -> handleCompressImage(sourcePath, preset, deleteSource));
        } else if (ACTION_COMPRESS_VIDEO.equals(action)) {
            mExecutor.submit(() -> handleCompressVideo(sourcePath, preset, deleteSource));
        }

        return START_NOT_STICKY;
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (mExecutor != null) mExecutor.shutdown();
        Log.i(TAG, "HCS Bundle Service destroyed");
    }

    // ─── Compression handlers ─────────────────────────────────────────────

    private void handleCompressImage(String sourcePath, CompressionPreset preset,
                                      boolean deleteSource) {
        long t0 = System.currentTimeMillis();
        File sourceFile = new File(sourcePath);
        if (!sourceFile.exists()) {
            Log.e(TAG, "Source file not found: " + sourcePath);
            stopForeground(true);
            stopSelf();
            return;
        }

        try {
            Log.i(TAG, "Compressing image: " + sourcePath + " [preset=" + preset.key + "]");

            // Load bitmap
            BitmapFactory.Options opts = new BitmapFactory.Options();
            opts.inPreferredConfig = Bitmap.Config.ARGB_8888;
            Bitmap original = BitmapFactory.decodeFile(sourcePath, opts);
            if (original == null) {
                Log.e(TAG, "Failed to decode image: " + sourcePath);
                return;
            }

            // Compress with HCS engine (transparent 8K upscaling + HCS compression)
            HCSEngine.CompressResult result = HCSEngine.compressImage(original, preset, "image");
            original.recycle();

            if (result == null) {
                Log.e(TAG, "HCS compression failed for: " + sourcePath);
                return;
            }

            // Determine output paths
            String baseName = getBaseNameWithoutExt(sourceFile.getName());
            String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
            String hcsFileName = "IMG_HCS_" + timestamp + "_" + baseName + ".hcs";
            String thumbFileName = "THUMB_" + timestamp + "_" + baseName + ".jpg";

            File hcsDir = getHCSDir();
            File thumbDir = getThumbDir();

            File hcsFile = new File(hcsDir, hcsFileName);
            File thumbFile = new File(thumbDir, thumbFileName);

            // Save HCS file
            if (!HCSEngine.saveToFile(result.hcsData, hcsFile)) {
                Log.e(TAG, "Failed to save HCS file");
                return;
            }

            // Save thumbnail separately for fast gallery loading
            if (!HCSEngine.saveToFile(result.thumbnailJpeg, thumbFile)) {
                Log.w(TAG, "Failed to save thumbnail file");
            }

            // Build MediaItem and insert to database
            MediaItem item = buildMediaItem(result, hcsFile, thumbFile,
                    "image", baseName, preset, 0f);
            item.srcWidth  = result.metadata.optInt("src_width");
            item.srcHeight = result.metadata.optInt("src_height");
            item.outWidth  = result.metadata.optInt("out_width");
            item.outHeight = result.metadata.optInt("out_height");
            mDatabase.upsertItem(item);

            // Optionally delete the original to free space
            if (deleteSource) {
                boolean deleted = sourceFile.delete();
                Log.i(TAG, "Original deleted: " + deleted + " -> " + sourcePath);
            }

            long elapsed = System.currentTimeMillis() - t0;
            String savings = HCSEngine.formatSavings(result.originalSizeBytes, result.compressedSizeBytes);
            Log.i(TAG, "Image compressed in " + elapsed + "ms | " + savings);

            // Notify user
            showDoneNotification(
                    "Image comprimee HCS",
                    savings + " | " + result.metadata.optInt("out_width")
                            + "x" + result.metadata.optInt("out_height") + " (8K)"
            );

        } catch (Exception e) {
            Log.e(TAG, "handleCompressImage exception", e);
        } finally {
            stopForeground(true);
            stopSelf();
        }
    }

    private void handleCompressVideo(String sourcePath, CompressionPreset preset,
                                      boolean deleteSource) {
        long t0 = System.currentTimeMillis();
        File sourceFile = new File(sourcePath);
        if (!sourceFile.exists()) {
            Log.e(TAG, "Source video not found: " + sourcePath);
            stopForeground(true);
            stopSelf();
            return;
        }

        try {
            Log.i(TAG, "Compressing video: " + sourcePath + " [preset=" + preset.key + "]");

            String baseName = getBaseNameWithoutExt(sourceFile.getName());
            String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(new Date());
            String hcsFileName = "VID_HCS_" + timestamp + "_" + baseName + ".hcs";
            String thumbFileName = "VTHUMB_" + timestamp + "_" + baseName + ".jpg";

            File hcsDir = getHCSDir();
            File thumbDir = getThumbDir();
            File hcsFile = new File(hcsDir, hcsFileName);
            File thumbFile = new File(thumbDir, thumbFileName);

            // Compress video with HCS video engine
            HCSVideoProcessor processor = new HCSVideoProcessor(this);
            HCSVideoProcessor.VideoCompressResult vResult =
                    processor.compressVideo(sourcePath, preset, hcsFile, thumbFile);

            if (vResult == null || !hcsFile.exists()) {
                Log.e(TAG, "Video HCS compression failed");
                return;
            }

            // Build MediaItem
            MediaItem item = buildMediaItem(null, hcsFile, thumbFile,
                    "video", baseName, preset, vResult.durationSeconds);
            item.originalSizeBytes   = vResult.originalSizeBytes;
            item.compressedSizeBytes = hcsFile.length();
            item.compressionRatio    = vResult.originalSizeBytes > 0
                    ? (float) vResult.originalSizeBytes / hcsFile.length() : 1f;
            item.srcWidth  = vResult.srcWidth;
            item.srcHeight = vResult.srcHeight;
            item.outWidth  = vResult.outWidth;
            item.outHeight = vResult.outHeight;
            mDatabase.upsertItem(item);

            if (deleteSource) {
                sourceFile.delete();
            }

            long elapsed = System.currentTimeMillis() - t0;
            String savings = HCSEngine.formatSavings(item.originalSizeBytes, item.compressedSizeBytes);
            Log.i(TAG, "Video compressed in " + elapsed + "ms | " + savings);

            showDoneNotification("Video comprimee HCS",
                    savings + " | " + vResult.outWidth + "x" + vResult.outHeight + " (8K)");

        } catch (Exception e) {
            Log.e(TAG, "handleCompressVideo exception", e);
        } finally {
            stopForeground(true);
            stopSelf();
        }
    }

    // ─── Static helpers to start the service ─────────────────────────────

    /**
     * Start the service to compress an image file.
     * Call this from CameraActivity after taking a photo.
     */
    public static void compressImage(Context ctx, String sourcePath,
                                      CompressionPreset preset, boolean deleteSource) {
        Intent intent = new Intent(ctx, HCSBundleService.class);
        intent.setAction(ACTION_COMPRESS_IMAGE);
        intent.putExtra(EXTRA_SOURCE_PATH, sourcePath);
        intent.putExtra(EXTRA_PRESET, preset.key);
        intent.putExtra(EXTRA_DELETE_SOURCE, deleteSource);
        ctx.startService(intent);
    }

    /**
     * Start the service to compress a video file.
     */
    public static void compressVideo(Context ctx, String sourcePath,
                                      CompressionPreset preset, boolean deleteSource) {
        Intent intent = new Intent(ctx, HCSBundleService.class);
        intent.setAction(ACTION_COMPRESS_VIDEO);
        intent.putExtra(EXTRA_SOURCE_PATH, sourcePath);
        intent.putExtra(EXTRA_PRESET, preset.key);
        intent.putExtra(EXTRA_DELETE_SOURCE, deleteSource);
        ctx.startService(intent);
    }

    // ─── File system helpers ──────────────────────────────────────────────

    public static File getHCSDir(Context ctx) {
        File dir = new File(ctx.getExternalFilesDir(null), HCS_DIR_NAME);
        if (!dir.exists()) dir.mkdirs();
        return dir;
    }

    private File getHCSDir() {
        return getHCSDir(this);
    }

    private File getThumbDir() {
        File dir = new File(getExternalFilesDir(null), THUMB_DIR_NAME);
        if (!dir.exists()) dir.mkdirs();
        return dir;
    }

    private static String getBaseNameWithoutExt(String fileName) {
        int dot = fileName.lastIndexOf('.');
        return dot > 0 ? fileName.substring(0, dot) : fileName;
    }

    private MediaItem buildMediaItem(HCSEngine.CompressResult imgResult,
                                      File hcsFile, File thumbFile,
                                      String type, String baseName,
                                      CompressionPreset preset, float durationS) {
        MediaItem item = new MediaItem();
        item.type = "video".equals(type) ? MediaItem.Type.VIDEO : MediaItem.Type.IMAGE;
        item.hcsFilePath     = hcsFile.getAbsolutePath();
        item.thumbnailPath   = thumbFile.exists() ? thumbFile.getAbsolutePath() : "";
        item.displayName     = baseName;
        item.timestamp       = System.currentTimeMillis();
        item.presetKey       = preset.key;
        item.durationSeconds = durationS;

        if (imgResult != null) {
            item.compressedSizeBytes = imgResult.compressedSizeBytes;
            item.originalSizeBytes   = imgResult.originalSizeBytes;
            item.compressionRatio    = imgResult.compressionRatio;
            try {
                item.srcWidth  = imgResult.metadata.getInt("src_width");
                item.srcHeight = imgResult.metadata.getInt("src_height");
                item.outWidth  = imgResult.metadata.getInt("out_width");
                item.outHeight = imgResult.metadata.getInt("out_height");
            } catch (Exception ignored) {}
        } else {
            item.compressedSizeBytes = hcsFile.length();
        }
        return item;
    }

    // ─── Notifications ────────────────────────────────────────────────────

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID, "HCS Bundle Service",
                    NotificationManager.IMPORTANCE_LOW);
            channel.setDescription("Compression transparente HCS");
            NotificationManager nm = getSystemService(NotificationManager.class);
            if (nm != null) nm.createNotificationChannel(channel);
        }
    }

    private Notification buildOngoingNotification(String text) {
        Intent mainIntent = new Intent(this, MainActivity.class);
        PendingIntent pi = PendingIntent.getActivity(this, 0, mainIntent,
                PendingIntent.FLAG_IMMUTABLE);

        return new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_menu_camera)
                .setContentTitle("HCS Bundle")
                .setContentText(text)
                .setContentIntent(pi)
                .setOngoing(true)
                .setPriority(NotificationCompat.PRIORITY_LOW)
                .build();
    }

    private void showDoneNotification(String title, String text) {
        NotificationManager nm = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        if (nm == null) return;
        Notification notif = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_menu_save)
                .setContentTitle(title)
                .setContentText(text)
                .setAutoCancel(true)
                .setPriority(NotificationCompat.PRIORITY_DEFAULT)
                .build();
        nm.notify(NOTIF_ID_DONE, notif);
    }
}
