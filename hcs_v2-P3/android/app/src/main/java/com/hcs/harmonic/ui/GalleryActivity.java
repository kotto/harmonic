package com.hcs.harmonic.ui;

import android.content.Intent;
import android.os.Bundle;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.GridLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.hcs.harmonic.R;
import com.hcs.harmonic.model.MediaItem;
import com.hcs.harmonic.storage.HCSMediaDatabase;

import java.io.File;
import java.util.List;
import java.util.concurrent.Executors;

/**
 * Gallery Activity – Thumbnail-only media browser.
 *
 * ALL items are displayed as compressed thumbnails.
 * Tapping an item opens PlayerActivity which performs
 * on-demand decompression + 8K upscaling.
 */
public class GalleryActivity extends AppCompatActivity
        implements GalleryAdapter.OnItemClickListener {

    public static final String EXTRA_ITEM_ID = "item_id";

    private RecyclerView mRecyclerView;
    private GalleryAdapter mAdapter;
    private TextView mTvEmpty;
    private TextView mTvCount;
    private HCSMediaDatabase mDatabase;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_gallery);

        mDatabase = HCSMediaDatabase.getInstance(this);

        mRecyclerView = findViewById(R.id.recycler_gallery);
        mTvEmpty      = findViewById(R.id.tv_empty_gallery);
        mTvCount      = findViewById(R.id.tv_item_count);

        // 3-column grid
        mRecyclerView.setLayoutManager(new GridLayoutManager(this, 3));

        loadGallery();
    }

    @Override
    protected void onResume() {
        super.onResume();
        loadGallery();
    }

    private void loadGallery() {
        Executors.newSingleThreadExecutor().execute(() -> {
            List<MediaItem> items = mDatabase.getAllItems();
            runOnUiThread(() -> {
                if (items.isEmpty()) {
                    mTvEmpty.setVisibility(android.view.View.VISIBLE);
                    mRecyclerView.setVisibility(android.view.View.GONE);
                    mTvCount.setText("Aucun media HCS");
                } else {
                    mTvEmpty.setVisibility(android.view.View.GONE);
                    mRecyclerView.setVisibility(android.view.View.VISIBLE);
                    mTvCount.setText(items.size() + " medias (vignettes HCS)");

                    if (mAdapter == null) {
                        mAdapter = new GalleryAdapter(items, this);
                        mRecyclerView.setAdapter(mAdapter);
                    } else {
                        mAdapter.updateItems(items);
                    }
                }
            });
        });
    }

    // ─── Item interactions ────────────────────────────────────────────────

    @Override
    public void onItemClick(MediaItem item) {
        // Navigate to PlayerActivity – decompression triggered there
        Intent intent = new Intent(this, PlayerActivity.class);
        intent.putExtra(EXTRA_ITEM_ID, item.id);
        startActivity(intent);
    }

    @Override
    public void onItemLongClick(MediaItem item) {
        // Show options dialog
        String[] options = {"Voir en 8K", "Supprimer", "Infos"};
        new AlertDialog.Builder(this)
                .setTitle(item.displayName)
                .setItems(options, (dialog, which) -> {
                    switch (which) {
                        case 0: onItemClick(item); break;
                        case 1: deleteItem(item); break;
                        case 2: showItemInfo(item); break;
                    }
                })
                .show();
    }

    private void deleteItem(MediaItem item) {
        new AlertDialog.Builder(this)
                .setTitle("Supprimer")
                .setMessage("Supprimer " + item.displayName + " ? Action irreversible.")
                .setPositiveButton("Supprimer", (d, w) -> {
                    Executors.newSingleThreadExecutor().execute(() -> {
                        // Delete HCS file and thumbnail
                        if (item.hcsFilePath != null) new File(item.hcsFilePath).delete();
                        if (item.thumbnailPath != null) new File(item.thumbnailPath).delete();
                        mDatabase.deleteByPath(item.hcsFilePath);
                        runOnUiThread(() -> {
                            Toast.makeText(this, "Media supprime", Toast.LENGTH_SHORT).show();
                            loadGallery();
                        });
                    });
                })
                .setNegativeButton("Annuler", null)
                .show();
    }

    private void showItemInfo(MediaItem item) {
        String info = "Nom: " + item.displayName + "\n"
                + "Type: " + (item.isVideo() ? "Video" : "Image") + "\n"
                + "Preset: " + item.presetKey + "\n"
                + "Resolution: " + item.resolutionLabel() + "\n"
                + "Compression: x" + String.format("%.1f", item.compressionRatio) + "\n"
                + "Economie: " + item.savingsLabel() + "\n"
                + "Taille: " + formatBytes(item.compressedSizeBytes)
                + " (original: " + formatBytes(item.originalSizeBytes) + ")";

        new AlertDialog.Builder(this)
                .setTitle("Informations HCS")
                .setMessage(info)
                .setPositiveButton("OK", null)
                .show();
    }

    private String formatBytes(long bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return String.format("%.1f KB", bytes / 1024.0);
        return String.format("%.1f MB", bytes / (1024.0 * 1024));
    }
}
