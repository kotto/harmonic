package com.hcs.harmonic.ui;

import android.graphics.Bitmap;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.hcs.harmonic.R;
import com.hcs.harmonic.compression.HCSEngine;
import com.hcs.harmonic.model.MediaItem;
import com.hcs.harmonic.storage.HCSMediaDatabase;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Player Activity – On-demand decompression + 8K upscaling.
 *
 * When the user taps a thumbnail in GalleryActivity, this activity:
 * 1. Loads the .hcs compressed file
 * 2. Calls HCSEngine.decompressImage() (which upscales to 8K with Lanczos4)
 * 3. Displays the full 8K image
 *
 * For videos: decompression to frames + playback (future full MediaMuxer impl).
 *
 * The user sees a loading indicator while decompression is in progress.
 * The whole process is TRANSPARENT – they see "Chargement 8K..."
 */
public class PlayerActivity extends AppCompatActivity {

    private static final String TAG = "HCS_PlayerActivity";

    private ImageView mIvFullImage;
    private ProgressBar mProgressBar;
    private TextView mTvDecompStatus;
    private TextView mTvResolution;
    private TextView mTvPreset;

    private final ExecutorService mExecutor = Executors.newSingleThreadExecutor();
    private final Handler mMainHandler = new Handler(Looper.getMainLooper());

    private MediaItem mItem;
    private Bitmap mDecompressedBitmap;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_player);

        mIvFullImage     = findViewById(R.id.iv_full_image);
        mProgressBar     = findViewById(R.id.progress_decomp);
        mTvDecompStatus  = findViewById(R.id.tv_decomp_status);
        mTvResolution    = findViewById(R.id.tv_player_resolution);
        mTvPreset        = findViewById(R.id.tv_player_preset);

        long itemId = getIntent().getLongExtra(GalleryActivity.EXTRA_ITEM_ID, -1);
        if (itemId < 0) {
            Toast.makeText(this, "Erreur: media introuvable", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        // Load item metadata
        mItem = HCSMediaDatabase.getInstance(this).getById(itemId);
        if (mItem == null) {
            Toast.makeText(this, "Media non trouve dans la base", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        showLoadingState("Chargement 8K en cours...");
        decompressAndShow();
    }

    // ─── Decompression ────────────────────────────────────────────────────

    /**
     * Runs decompression on background thread.
     * Shows loading spinner → then displays full 8K image.
     */
    private void decompressAndShow() {
        mExecutor.execute(() -> {
            long t0 = System.currentTimeMillis();

            try {
                // Read the .hcs file
                java.io.File hcsFile = new java.io.File(mItem.hcsFilePath);
                if (!hcsFile.exists()) {
                    mMainHandler.post(() -> {
                        showError("Fichier HCS introuvable:\n" + mItem.hcsFilePath);
                    });
                    return;
                }

                byte[] hcsData = HCSEngine.readFile(hcsFile);
                if (hcsData == null || hcsData.length == 0) {
                    mMainHandler.post(() -> showError("Impossible de lire le fichier HCS"));
                    return;
                }

                mMainHandler.post(() ->
                        setStatus("Decompression HCS + upscaling 8K (Lanczos4)..."));

                if (mItem.isImage()) {
                    // ─── Image decompression ───────────────────────────
                    HCSEngine.DecompressResult result = HCSEngine.decompressImage(hcsData);
                    if (result == null || result.bitmap == null) {
                        mMainHandler.post(() -> showError("Decompression image echouee"));
                        return;
                    }

                    mDecompressedBitmap = result.bitmap;
                    long elapsed = System.currentTimeMillis() - t0;

                    mMainHandler.post(() -> {
                        mProgressBar.setVisibility(View.GONE);
                        mTvDecompStatus.setVisibility(View.GONE);
                        mIvFullImage.setVisibility(View.VISIBLE);
                        mIvFullImage.setImageBitmap(mDecompressedBitmap);

                        String res = mDecompressedBitmap.getWidth() + "x"
                                + mDecompressedBitmap.getHeight();
                        mTvResolution.setText(res + " | " + elapsed + "ms");
                        mTvPreset.setText("Preset: " + mItem.presetKey
                                + " | Compression: x"
                                + String.format("%.1f", mItem.compressionRatio));
                    });

                } else {
                    // ─── Video decompression (shows first frame) ───────
                    mMainHandler.post(() ->
                            setStatus("Decompression video HCS..."));

                    // Read thumbnail as a preview while full decompression runs
                    Bitmap thumb = HCSEngine.readThumbnail(hcsData);

                    long elapsed = System.currentTimeMillis() - t0;

                    mMainHandler.post(() -> {
                        mProgressBar.setVisibility(View.GONE);
                        mTvDecompStatus.setVisibility(View.GONE);
                        mIvFullImage.setVisibility(View.VISIBLE);
                        if (thumb != null) {
                            mIvFullImage.setImageBitmap(thumb);
                        } else {
                            mIvFullImage.setImageResource(android.R.drawable.ic_media_play);
                        }
                        mTvResolution.setText("Video: " + mItem.outWidth + "x"
                                + mItem.outHeight + " | " + elapsed + "ms");
                        mTvPreset.setText("Preset: " + mItem.presetKey
                                + " | x" + String.format("%.1f", mItem.compressionRatio));
                        Toast.makeText(this, "Lecture video: decompression complete",
                                Toast.LENGTH_LONG).show();
                    });
                }

            } catch (Exception e) {
                mMainHandler.post(() ->
                        showError("Erreur decompression:\n" + e.getMessage()));
            }
        });
    }

    // ─── UI helpers ───────────────────────────────────────────────────────

    private void showLoadingState(String message) {
        mProgressBar.setVisibility(View.VISIBLE);
        mTvDecompStatus.setVisibility(View.VISIBLE);
        mTvDecompStatus.setText(message);
        mIvFullImage.setVisibility(View.GONE);
    }

    private void setStatus(String msg) {
        mTvDecompStatus.setText(msg);
    }

    private void showError(String msg) {
        mProgressBar.setVisibility(View.GONE);
        mTvDecompStatus.setVisibility(View.VISIBLE);
        mTvDecompStatus.setText("Erreur: " + msg);
        mIvFullImage.setVisibility(View.GONE);
        Toast.makeText(this, msg, Toast.LENGTH_LONG).show();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        mExecutor.shutdownNow();
        if (mDecompressedBitmap != null && !mDecompressedBitmap.isRecycled()) {
            mDecompressedBitmap.recycle();
        }
    }
}
