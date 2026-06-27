package com.hcs.harmonic.ui;

import android.graphics.BitmapFactory;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.hcs.harmonic.R;
import com.hcs.harmonic.model.MediaItem;

import java.util.List;

/**
 * Gallery RecyclerView Adapter.
 *
 * Displays ONLY thumbnails (fast).
 * Full decompression happens in PlayerActivity on tap.
 */
public class GalleryAdapter extends RecyclerView.Adapter<GalleryAdapter.ViewHolder> {

    public interface OnItemClickListener {
        void onItemClick(MediaItem item);
        void onItemLongClick(MediaItem item);
    }

    private List<MediaItem> mItems;
    private final OnItemClickListener mListener;

    public GalleryAdapter(List<MediaItem> items, OnItemClickListener listener) {
        this.mItems = items;
        this.mListener = listener;
    }

    public void updateItems(List<MediaItem> newItems) {
        this.mItems = newItems;
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View v = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_media_thumbnail, parent, false);
        return new ViewHolder(v);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        MediaItem item = mItems.get(position);
        holder.bind(item, mListener);
    }

    @Override
    public int getItemCount() {
        return mItems != null ? mItems.size() : 0;
    }

    // ─── ViewHolder ────────────────────────────────────────────────────

    static class ViewHolder extends RecyclerView.ViewHolder {

        private final ImageView ivThumbnail;
        private final TextView tvName;
        private final TextView tvSavings;
        private final TextView tvResolution;
        private final ImageView ivVideoIcon;
        private final TextView tvDuration;

        ViewHolder(View itemView) {
            super(itemView);
            ivThumbnail  = itemView.findViewById(R.id.iv_thumbnail);
            tvName       = itemView.findViewById(R.id.tv_item_name);
            tvSavings    = itemView.findViewById(R.id.tv_savings);
            tvResolution = itemView.findViewById(R.id.tv_resolution);
            ivVideoIcon  = itemView.findViewById(R.id.iv_video_icon);
            tvDuration   = itemView.findViewById(R.id.tv_duration);
        }

        void bind(MediaItem item, OnItemClickListener listener) {
            // Load thumbnail from disk (fast – no decompression)
            if (item.thumbnailPath != null && !item.thumbnailPath.isEmpty()) {
                BitmapFactory.Options opts = new BitmapFactory.Options();
                opts.inSampleSize = 1;
                try {
                    android.graphics.Bitmap thumb =
                            BitmapFactory.decodeFile(item.thumbnailPath, opts);
                    if (thumb != null) {
                        ivThumbnail.setImageBitmap(thumb);
                    } else {
                        ivThumbnail.setImageResource(android.R.drawable.ic_menu_gallery);
                    }
                } catch (Exception e) {
                    ivThumbnail.setImageResource(android.R.drawable.ic_menu_gallery);
                }
            } else {
                ivThumbnail.setImageResource(android.R.drawable.ic_menu_gallery);
            }

            // Name
            tvName.setText(item.displayName != null ? item.displayName : "HCS Media");

            // Savings badge
            tvSavings.setText(item.savingsLabel());

            // Resolution
            tvResolution.setText(item.resolutionLabel());

            // Video icon and duration
            if (item.isVideo()) {
                ivVideoIcon.setVisibility(View.VISIBLE);
                if (item.durationSeconds > 0) {
                    int mins = (int)(item.durationSeconds / 60);
                    int secs = (int)(item.durationSeconds % 60);
                    tvDuration.setText(String.format("%d:%02d", mins, secs));
                    tvDuration.setVisibility(View.VISIBLE);
                } else {
                    tvDuration.setVisibility(View.GONE);
                }
            } else {
                ivVideoIcon.setVisibility(View.GONE);
                tvDuration.setVisibility(View.GONE);
            }

            // Click → PlayerActivity (triggers decompression + 8K playback)
            itemView.setOnClickListener(v -> {
                if (listener != null) listener.onItemClick(item);
            });

            // Long click → options (delete, share, etc.)
            itemView.setOnLongClickListener(v -> {
                if (listener != null) listener.onItemLongClick(item);
                return true;
            });
        }
    }
}
