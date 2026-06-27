package com.hcs.harmonic.ui;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.hcs.harmonic.R;
import com.hcs.harmonic.storage.HCSMediaDatabase;

import java.util.ArrayList;
import java.util.List;

/**
 * HCS Bundle – Home / Launcher Activity
 *
 * Presents the four main features:
 *  1. Camera 8K  → CameraActivity
 *  2. Galerie    → GalleryActivity  (thumbnails only)
 *  3. Dashboard  → DashboardActivity (space savings)
 *  4. Info
 */
public class MainActivity extends AppCompatActivity {

    private static final String TAG = "HCS_MainActivity";
    private static final int REQUEST_PERMISSIONS = 42;

    private TextView mStatusText;
    private TextView mStatsText;
    private boolean mOpenCVReady = true;  // HCS engine always ready (no OpenCV needed)

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        initViews();
        checkPermissions();
        refreshStats();
    }

    @Override
    protected void onResume() {
        super.onResume();
        refreshStats();
    }

    private void initViews() {
        mStatusText = findViewById(R.id.tv_status);
        mStatsText  = findViewById(R.id.tv_stats);

        mStatusText.setText("HCS Bundle pret  |  Moteur 8K actif  |  OK");

        // Camera 8K button
        Button btnCamera = findViewById(R.id.btn_camera);
        btnCamera.setOnClickListener(v ->
                startActivity(new Intent(this, CameraActivity.class)));

        // Gallery button
        Button btnGallery = findViewById(R.id.btn_gallery);
        btnGallery.setOnClickListener(v ->
                startActivity(new Intent(this, GalleryActivity.class)));

        // Dashboard button
        Button btnDashboard = findViewById(R.id.btn_dashboard);
        btnDashboard.setOnClickListener(v ->
                startActivity(new Intent(this, DashboardActivity.class)));

        // Info text
        TextView tvInfo = findViewById(R.id.tv_info);
        tvInfo.setText(
                "HCS Bundle Service\n" +
                "Compression transparente automatique\n" +
                "Photos & Videos stockees en miniatures\n" +
                "Lecture = decompression + upscaling 8K\n" +
                "Zero probleme d'espace disque"
        );
    }

    private void refreshStats() {
        try {
            HCSMediaDatabase.Stats stats =
                    HCSMediaDatabase.getInstance(this).getStats();
            String txt = String.format(
                    "Medias: %d (%d photos, %d videos)\n" +
                    "Espace economise: %.1f GB\n" +
                    "Ratio moyen: %.1f:1",
                    stats.totalItems, stats.totalImages, stats.totalVideos,
                    stats.savedBytes / (1024.0 * 1024 * 1024),
                    stats.averageRatio
            );
            mStatsText.setText(txt);
        } catch (Exception e) {
            mStatsText.setText("Aucun media HCS pour l'instant");
        }
    }

    // ─── Permissions ──────────────────────────────────────────────────────

    private void checkPermissions() {
        List<String> needed = new ArrayList<>();
        String[] perms;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            perms = new String[]{
                Manifest.permission.CAMERA,
                Manifest.permission.RECORD_AUDIO,
                Manifest.permission.READ_MEDIA_IMAGES,
                Manifest.permission.READ_MEDIA_VIDEO,
                Manifest.permission.POST_NOTIFICATIONS
            };
        } else {
            perms = new String[]{
                Manifest.permission.CAMERA,
                Manifest.permission.RECORD_AUDIO,
                Manifest.permission.READ_EXTERNAL_STORAGE,
                Manifest.permission.WRITE_EXTERNAL_STORAGE
            };
        }
        for (String p : perms) {
            if (ContextCompat.checkSelfPermission(this, p) != PackageManager.PERMISSION_GRANTED) {
                needed.add(p);
            }
        }
        if (!needed.isEmpty()) {
            ActivityCompat.requestPermissions(this,
                    needed.toArray(new String[0]), REQUEST_PERMISSIONS);
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode,
                                            @NonNull String[] permissions,
                                            @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_PERMISSIONS) {
            boolean allGranted = true;
            for (int r : grantResults) {
                if (r != PackageManager.PERMISSION_GRANTED) {
                    allGranted = false;
                    break;
                }
            }
            if (!allGranted) {
                Toast.makeText(this, "Certaines permissions refusees", Toast.LENGTH_LONG).show();
            }
        }
    }
}
