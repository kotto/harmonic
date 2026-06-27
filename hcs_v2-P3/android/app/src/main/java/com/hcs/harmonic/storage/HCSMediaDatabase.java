package com.hcs.harmonic.storage;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.util.Log;

import com.hcs.harmonic.model.MediaItem;

import java.util.ArrayList;
import java.util.List;

/**
 * SQLite database for HCS media items.
 * Maps thumbnail paths ↔ HCS compressed files ↔ metadata.
 *
 * Table: media_items
 *   id               INTEGER PRIMARY KEY
 *   type             TEXT ('image'|'video')
 *   hcs_file_path    TEXT (path to .hcs file)
 *   thumbnail_path   TEXT (path to thumbnail JPEG)
 *   display_name     TEXT
 *   timestamp        INTEGER (ms since epoch)
 *   compressed_bytes INTEGER
 *   original_bytes   INTEGER
 *   compression_ratio REAL
 *   preset_key       TEXT
 *   src_width        INTEGER
 *   src_height       INTEGER
 *   out_width        INTEGER
 *   out_height       INTEGER
 *   duration_s       REAL
 */
public class HCSMediaDatabase extends SQLiteOpenHelper {

    private static final String TAG = "HCSMediaDatabase";
    private static final String DB_NAME = "hcs_media.db";
    private static final int DB_VERSION = 1;

    private static final String TABLE = "media_items";

    // Column names
    private static final String COL_ID               = "id";
    private static final String COL_TYPE             = "type";
    private static final String COL_HCS_PATH         = "hcs_file_path";
    private static final String COL_THUMB_PATH       = "thumbnail_path";
    private static final String COL_DISPLAY_NAME     = "display_name";
    private static final String COL_TIMESTAMP        = "timestamp";
    private static final String COL_COMP_BYTES       = "compressed_bytes";
    private static final String COL_ORIG_BYTES       = "original_bytes";
    private static final String COL_RATIO            = "compression_ratio";
    private static final String COL_PRESET           = "preset_key";
    private static final String COL_SRC_W            = "src_width";
    private static final String COL_SRC_H            = "src_height";
    private static final String COL_OUT_W            = "out_width";
    private static final String COL_OUT_H            = "out_height";
    private static final String COL_DURATION         = "duration_s";

    private static HCSMediaDatabase sInstance;

    public static synchronized HCSMediaDatabase getInstance(Context ctx) {
        if (sInstance == null) {
            sInstance = new HCSMediaDatabase(ctx.getApplicationContext());
        }
        return sInstance;
    }

    private HCSMediaDatabase(Context ctx) {
        super(ctx, DB_NAME, null, DB_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE IF NOT EXISTS " + TABLE + " ("
                + COL_ID           + " INTEGER PRIMARY KEY AUTOINCREMENT,"
                + COL_TYPE         + " TEXT NOT NULL,"
                + COL_HCS_PATH     + " TEXT NOT NULL UNIQUE,"
                + COL_THUMB_PATH   + " TEXT,"
                + COL_DISPLAY_NAME + " TEXT,"
                + COL_TIMESTAMP    + " INTEGER,"
                + COL_COMP_BYTES   + " INTEGER,"
                + COL_ORIG_BYTES   + " INTEGER,"
                + COL_RATIO        + " REAL,"
                + COL_PRESET       + " TEXT,"
                + COL_SRC_W        + " INTEGER,"
                + COL_SRC_H        + " INTEGER,"
                + COL_OUT_W        + " INTEGER,"
                + COL_OUT_H        + " INTEGER,"
                + COL_DURATION     + " REAL"
                + ")");
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        db.execSQL("DROP TABLE IF EXISTS " + TABLE);
        onCreate(db);
    }

    // ─── Write ────────────────────────────────────────────────────────────

    /** Insert or update (REPLACE) a media item. Returns row id or -1. */
    public long upsertItem(MediaItem item) {
        try {
            SQLiteDatabase db = getWritableDatabase();
            ContentValues cv = toContentValues(item);
            long rowId = db.insertWithOnConflict(TABLE, null, cv,
                    SQLiteDatabase.CONFLICT_REPLACE);
            Log.d(TAG, "upsertItem -> rowId=" + rowId + " " + item.hcsFilePath);
            return rowId;
        } catch (Exception e) {
            Log.e(TAG, "upsertItem failed", e);
            return -1;
        }
    }

    /** Delete item by its HCS file path. */
    public boolean deleteByPath(String hcsPath) {
        try {
            SQLiteDatabase db = getWritableDatabase();
            int rows = db.delete(TABLE, COL_HCS_PATH + "=?", new String[]{hcsPath});
            return rows > 0;
        } catch (Exception e) {
            Log.e(TAG, "deleteByPath failed", e);
            return false;
        }
    }

    // ─── Read ─────────────────────────────────────────────────────────────

    /** Get all items ordered by timestamp descending (most recent first). */
    public List<MediaItem> getAllItems() {
        List<MediaItem> list = new ArrayList<>();
        try {
            SQLiteDatabase db = getReadableDatabase();
            Cursor c = db.query(TABLE, null, null, null, null, null,
                    COL_TIMESTAMP + " DESC");
            while (c.moveToNext()) {
                list.add(fromCursor(c));
            }
            c.close();
        } catch (Exception e) {
            Log.e(TAG, "getAllItems failed", e);
        }
        return list;
    }

    /** Get only image items. */
    public List<MediaItem> getImages() {
        return getByType("image");
    }

    /** Get only video items. */
    public List<MediaItem> getVideos() {
        return getByType("video");
    }

    private List<MediaItem> getByType(String type) {
        List<MediaItem> list = new ArrayList<>();
        try {
            SQLiteDatabase db = getReadableDatabase();
            Cursor c = db.query(TABLE, null, COL_TYPE + "=?",
                    new String[]{type}, null, null, COL_TIMESTAMP + " DESC");
            while (c.moveToNext()) {
                list.add(fromCursor(c));
            }
            c.close();
        } catch (Exception e) {
            Log.e(TAG, "getByType(" + type + ") failed", e);
        }
        return list;
    }

    /** Get single item by id. */
    public MediaItem getById(long id) {
        try {
            SQLiteDatabase db = getReadableDatabase();
            Cursor c = db.query(TABLE, null, COL_ID + "=?",
                    new String[]{String.valueOf(id)}, null, null, null);
            if (c.moveToFirst()) {
                MediaItem item = fromCursor(c);
                c.close();
                return item;
            }
            c.close();
        } catch (Exception e) {
            Log.e(TAG, "getById failed", e);
        }
        return null;
    }

    // ─── Statistics ───────────────────────────────────────────────────────

    public static class Stats {
        public long totalItems;
        public long totalImages;
        public long totalVideos;
        public long totalCompressedBytes;
        public long totalOriginalBytes;
        public double averageRatio;
        public long savedBytes;
        public double savedPercent;
    }

    public Stats getStats() {
        Stats stats = new Stats();
        try {
            SQLiteDatabase db = getReadableDatabase();
            Cursor c = db.rawQuery(
                    "SELECT COUNT(*), "
                    + "SUM(CASE WHEN type='image' THEN 1 ELSE 0 END), "
                    + "SUM(CASE WHEN type='video' THEN 1 ELSE 0 END), "
                    + "SUM(compressed_bytes), "
                    + "SUM(original_bytes), "
                    + "AVG(compression_ratio) "
                    + "FROM " + TABLE, null);
            if (c.moveToFirst()) {
                stats.totalItems          = c.getLong(0);
                stats.totalImages         = c.getLong(1);
                stats.totalVideos         = c.getLong(2);
                stats.totalCompressedBytes = c.getLong(3);
                stats.totalOriginalBytes  = c.getLong(4);
                stats.averageRatio        = c.getDouble(5);
                stats.savedBytes          = stats.totalOriginalBytes - stats.totalCompressedBytes;
                stats.savedPercent        = stats.totalOriginalBytes > 0
                        ? 100.0 * stats.savedBytes / stats.totalOriginalBytes : 0;
            }
            c.close();
        } catch (Exception e) {
            Log.e(TAG, "getStats failed", e);
        }
        return stats;
    }

    // ─── Mapping helpers ─────────────────────────────────────────────────

    private ContentValues toContentValues(MediaItem item) {
        ContentValues cv = new ContentValues();
        cv.put(COL_TYPE,         item.type == MediaItem.Type.VIDEO ? "video" : "image");
        cv.put(COL_HCS_PATH,     item.hcsFilePath);
        cv.put(COL_THUMB_PATH,   item.thumbnailPath);
        cv.put(COL_DISPLAY_NAME, item.displayName);
        cv.put(COL_TIMESTAMP,    item.timestamp);
        cv.put(COL_COMP_BYTES,   item.compressedSizeBytes);
        cv.put(COL_ORIG_BYTES,   item.originalSizeBytes);
        cv.put(COL_RATIO,        item.compressionRatio);
        cv.put(COL_PRESET,       item.presetKey);
        cv.put(COL_SRC_W,        item.srcWidth);
        cv.put(COL_SRC_H,        item.srcHeight);
        cv.put(COL_OUT_W,        item.outWidth);
        cv.put(COL_OUT_H,        item.outHeight);
        cv.put(COL_DURATION,     item.durationSeconds);
        return cv;
    }

    private MediaItem fromCursor(Cursor c) {
        MediaItem item = new MediaItem();
        item.id                 = c.getLong(c.getColumnIndexOrThrow(COL_ID));
        String typeStr          = c.getString(c.getColumnIndexOrThrow(COL_TYPE));
        item.type               = "video".equals(typeStr) ? MediaItem.Type.VIDEO : MediaItem.Type.IMAGE;
        item.hcsFilePath        = c.getString(c.getColumnIndexOrThrow(COL_HCS_PATH));
        item.thumbnailPath      = c.getString(c.getColumnIndexOrThrow(COL_THUMB_PATH));
        item.displayName        = c.getString(c.getColumnIndexOrThrow(COL_DISPLAY_NAME));
        item.timestamp          = c.getLong(c.getColumnIndexOrThrow(COL_TIMESTAMP));
        item.compressedSizeBytes = c.getLong(c.getColumnIndexOrThrow(COL_COMP_BYTES));
        item.originalSizeBytes  = c.getLong(c.getColumnIndexOrThrow(COL_ORIG_BYTES));
        item.compressionRatio   = c.getFloat(c.getColumnIndexOrThrow(COL_RATIO));
        item.presetKey          = c.getString(c.getColumnIndexOrThrow(COL_PRESET));
        item.srcWidth           = c.getInt(c.getColumnIndexOrThrow(COL_SRC_W));
        item.srcHeight          = c.getInt(c.getColumnIndexOrThrow(COL_SRC_H));
        item.outWidth           = c.getInt(c.getColumnIndexOrThrow(COL_OUT_W));
        item.outHeight          = c.getInt(c.getColumnIndexOrThrow(COL_OUT_H));
        item.durationSeconds    = c.getFloat(c.getColumnIndexOrThrow(COL_DURATION));
        return item;
    }
}
