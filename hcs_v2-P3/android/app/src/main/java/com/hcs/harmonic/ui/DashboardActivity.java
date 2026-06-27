package com.hcs.harmonic.ui;

import android.os.Bundle;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import com.hcs.harmonic.R;
import com.hcs.harmonic.compression.HCSEngine;
import com.hcs.harmonic.storage.HCSMediaDatabase;

import java.util.concurrent.Executors;

/**
 * Dashboard – Space savings overview.
 * Shows total media count, GB saved, average compression ratio.
 */
public class DashboardActivity extends AppCompatActivity {

    private TextView mTvTotalItems;
    private TextView mTvSpaceSaved;
    private TextView mTvOriginalSize;
    private TextView mTvCompressedSize;
    private TextView mTvAvgRatio;
    private TextView mTvImages;
    private TextView mTvVideos;
    private TextView mTvSavedPercent;
    private TextView mTvPresetInfo;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_dashboard);

        mTvTotalItems     = findViewById(R.id.tv_total_items);
        mTvSpaceSaved     = findViewById(R.id.tv_space_saved);
        mTvOriginalSize   = findViewById(R.id.tv_original_size);
        mTvCompressedSize = findViewById(R.id.tv_compressed_size);
        mTvAvgRatio       = findViewById(R.id.tv_avg_ratio);
        mTvImages         = findViewById(R.id.tv_images_count);
        mTvVideos         = findViewById(R.id.tv_videos_count);
        mTvSavedPercent   = findViewById(R.id.tv_saved_percent);
        mTvPresetInfo     = findViewById(R.id.tv_preset_info);

        loadStats();
        showPresetInfo();
    }

    @Override
    protected void onResume() {
        super.onResume();
        loadStats();
    }

    private void loadStats() {
        Executors.newSingleThreadExecutor().execute(() -> {
            HCSMediaDatabase.Stats stats =
                    HCSMediaDatabase.getInstance(this).getStats();
            runOnUiThread(() -> updateUI(stats));
        });
    }

    private void updateUI(HCSMediaDatabase.Stats stats) {
        mTvTotalItems.setText(String.valueOf(stats.totalItems));
        mTvImages.setText(stats.totalImages + " photos");
        mTvVideos.setText(stats.totalVideos + " videos");

        mTvOriginalSize.setText(HCSEngine.formatBytes(stats.totalOriginalBytes)
                + " original");
        mTvCompressedSize.setText(HCSEngine.formatBytes(stats.totalCompressedBytes)
                + " stocke");

        mTvSpaceSaved.setText(HCSEngine.formatBytes(stats.savedBytes) + " liberes");
        mTvSavedPercent.setText(String.format("%.1f%% economise", stats.savedPercent));

        mTvAvgRatio.setText(String.format("x%.1f compression moyenne", stats.averageRatio));
    }

    private void showPresetInfo() {
        StringBuilder sb = new StringBuilder();
        sb.append("Presets disponibles:\n\n");
        for (com.hcs.harmonic.compression.CompressionPreset p :
                com.hcs.harmonic.compression.CompressionPreset.values()) {
            sb.append("  ").append(p.displayName)
              .append("  x").append((int) p.targetRatio)
              .append(":1\n");
        }
        mTvPresetInfo.setText(sb.toString());
    }
}
