package com.hcs.harmonic;

/**
 * @deprecated Replaced by com.hcs.harmonic.ui.MainActivity (HCS Bundle v2)
 *
 * This file is kept as a placeholder to avoid removing the original class
 * from version control history.
 *
 * The application now uses the full HCS Bundle Service architecture:
 *   - com.hcs.harmonic.ui.MainActivity       (Home / Launcher)
 *   - com.hcs.harmonic.ui.CameraActivity     (Camera 8K + HCS compression)
 *   - com.hcs.harmonic.ui.GalleryActivity    (Thumbnail-only gallery)
 *   - com.hcs.harmonic.ui.PlayerActivity     (Decompression on playback)
 *   - com.hcs.harmonic.ui.DashboardActivity  (Space savings dashboard)
 *   - com.hcs.harmonic.service.HCSBundleService (Background compression)
 *   - com.hcs.harmonic.compression.HCSEngine (Core HCS engine)
 *   - com.hcs.harmonic.compression.HCSUpscaler (OpenCV Lanczos4 8K upscaler)
 */
@Deprecated
public class MainActivity {
    // Intentionally empty – see com.hcs.harmonic.ui.MainActivity
}
