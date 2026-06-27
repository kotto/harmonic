package com.hcs.harmonic.ui;

import android.content.Intent;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.camera.core.Camera;
import androidx.camera.core.CameraSelector;
import androidx.camera.core.ImageCapture;
import androidx.camera.core.ImageCaptureException;
import androidx.camera.core.Preview;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.camera.video.FileOutputOptions;
import androidx.camera.video.Quality;
import androidx.camera.video.QualitySelector;
import androidx.camera.video.Recorder;
import androidx.camera.video.Recording;
import androidx.camera.video.VideoCapture;
import androidx.camera.video.VideoRecordEvent;
import androidx.camera.view.PreviewView;
import androidx.core.content.ContextCompat;

import com.google.common.util.concurrent.ListenableFuture;
import com.hcs.harmonic.R;
import com.hcs.harmonic.compression.CompressionPreset;
import com.hcs.harmonic.service.HCSBundleService;

import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Camera Activity – 8K HCS Bundle
 *
 * Captures photos/videos then immediately hands them to HCSBundleService
 * for transparent compression + 8K upscaling.
 * The user never sees the raw file.
 */
public class CameraActivity extends AppCompatActivity {

    private static final String TAG = "HCS_CameraActivity";

    private PreviewView mPreviewView;
    private Button mBtnPhoto;
    private Button mBtnVideo;
    private Button mBtnFlip;
    private TextView mTvStatus;
    private TextView mTvPreset;

    private ProcessCameraProvider mCameraProvider;
    private ImageCapture mImageCapture;
    private VideoCapture<Recorder> mVideoCapture;
    private Recording mCurrentRecording;
    private Camera mCamera;

    private boolean mIsRecording = false;
    private boolean mFrontCamera = false;
    private CompressionPreset mPreset = CompressionPreset.SOCIAL_8K;

    private final ExecutorService mCameraExecutor = Executors.newSingleThreadExecutor();
    private final Handler mMainHandler = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_camera);

        initViews();
        startCamera();
    }

    private void initViews() {
        mPreviewView = findViewById(R.id.preview_view);
        mBtnPhoto    = findViewById(R.id.btn_photo);
        mBtnVideo    = findViewById(R.id.btn_video);
        mBtnFlip     = findViewById(R.id.btn_flip);
        mTvStatus    = findViewById(R.id.tv_camera_status);
        mTvPreset    = findViewById(R.id.tv_preset);

        updatePresetLabel();

        mBtnPhoto.setOnClickListener(v -> takePhoto());
        mBtnVideo.setOnClickListener(v -> toggleVideo());
        mBtnFlip.setOnClickListener(v -> flipCamera());

        // Preset selector button (cycles through presets)
        Button btnPreset = findViewById(R.id.btn_preset);
        btnPreset.setOnClickListener(v -> cyclePreset());

        setStatus("Camera HCS 8K prete");
    }

    // ─── Camera setup ────────────────────────────────────────────────────

    private void startCamera() {
        ListenableFuture<ProcessCameraProvider> future =
                ProcessCameraProvider.getInstance(this);

        future.addListener(() -> {
            try {
                mCameraProvider = future.get();
                bindUseCases();
            } catch (ExecutionException | InterruptedException e) {
                Log.e(TAG, "CameraProvider init failed", e);
                setStatus("Erreur: " + e.getMessage());
            }
        }, ContextCompat.getMainExecutor(this));
    }

    private void bindUseCases() {
        if (mCameraProvider == null) return;

        // Preview
        Preview preview = new Preview.Builder().build();
        preview.setSurfaceProvider(mPreviewView.getSurfaceProvider());

        // Image capture (highest available quality)
        mImageCapture = new ImageCapture.Builder()
                .setCaptureMode(ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY)
                .build();

        // Video capture with highest quality (fallback handled by CameraX automatically)
        Recorder recorder = new Recorder.Builder()
                .setQualitySelector(QualitySelector.fromOrderedList(
                        java.util.Arrays.asList(Quality.HIGHEST, Quality.UHD,
                                Quality.FHD, Quality.HD)))
                .build();
        mVideoCapture = VideoCapture.withOutput(recorder);

        CameraSelector selector = mFrontCamera
                ? CameraSelector.DEFAULT_FRONT_CAMERA
                : CameraSelector.DEFAULT_BACK_CAMERA;

        try {
            mCameraProvider.unbindAll();
            mCamera = mCameraProvider.bindToLifecycle(
                    this, selector, preview, mImageCapture, mVideoCapture);

            setStatus("Camera 8K initialisee | Preset: " + mPreset.displayName);
        } catch (Exception e) {
            Log.e(TAG, "bindUseCases failed", e);
            setStatus("Erreur camera: " + e.getMessage());
        }
    }

    // ─── Photo ────────────────────────────────────────────────────────────

    private void takePhoto() {
        if (mImageCapture == null) return;

        mBtnPhoto.setEnabled(false);
        setStatus("Capture photo 8K...");

        // Temp file for raw capture
        File tempDir = getExternalFilesDir(Environment.DIRECTORY_PICTURES);
        String filename = "RAW_" + new SimpleDateFormat("yyyyMMdd_HHmmss",
                Locale.US).format(new Date()) + ".jpg";
        File photoFile = new File(tempDir, filename);

        ImageCapture.OutputFileOptions opts =
                new ImageCapture.OutputFileOptions.Builder(photoFile).build();

        mImageCapture.takePicture(opts, ContextCompat.getMainExecutor(this),
                new ImageCapture.OnImageSavedCallback() {

                    @Override
                    public void onImageSaved(@NonNull ImageCapture.OutputFileResults r) {
                        Log.d(TAG, "Raw photo saved: " + photoFile.getAbsolutePath());
                        setStatus("Photo capturee – compression 8K HCS...");

                        // Hand off to HCS Bundle Service (transparent compression)
                        // deleteSource=true: raw file deleted after compression
                        HCSBundleService.compressImage(
                                CameraActivity.this,
                                photoFile.getAbsolutePath(),
                                mPreset,
                                true /* delete source after compression */
                        );

                        setStatus("Photo 8K HCS en cours de compression...");
                        Toast.makeText(CameraActivity.this,
                                "Photo capturee – compression 8K en cours",
                                Toast.LENGTH_SHORT).show();

                        mBtnPhoto.setEnabled(true);
                    }

                    @Override
                    public void onError(@NonNull ImageCaptureException e) {
                        Log.e(TAG, "Photo capture failed", e);
                        setStatus("Erreur capture photo");
                        mBtnPhoto.setEnabled(true);
                    }
                });
    }

    // ─── Video ────────────────────────────────────────────────────────────

    private void toggleVideo() {
        if (mIsRecording) stopVideo();
        else startVideo();
    }

    private void startVideo() {
        if (mVideoCapture == null) return;

        File tempDir = getExternalFilesDir(Environment.DIRECTORY_MOVIES);
        String filename = "RAW_VID_" + new SimpleDateFormat("yyyyMMdd_HHmmss",
                Locale.US).format(new Date()) + ".mp4";
        File videoFile = new File(tempDir, filename);

        FileOutputOptions fileOptions = new FileOutputOptions.Builder(videoFile).build();

        try {
            mCurrentRecording = mVideoCapture.getOutput()
                    .prepareRecording(this, fileOptions)
                    .withAudioEnabled()
                    .start(ContextCompat.getMainExecutor(this), event -> {
                        if (event instanceof VideoRecordEvent.Start) {
                            mIsRecording = true;
                            mMainHandler.post(() -> {
                                mBtnVideo.setText("STOP");
                                mBtnVideo.setBackgroundColor(0xFFFF4444);
                                setStatus("Enregistrement 8K HCS en cours...");
                            });
                        } else if (event instanceof VideoRecordEvent.Finalize) {
                            VideoRecordEvent.Finalize fin = (VideoRecordEvent.Finalize) event;
                            mIsRecording = false;
                            mMainHandler.post(() -> {
                                mBtnVideo.setText("VIDEO 8K");
                                mBtnVideo.setBackgroundColor(0xFF2196F3);
                                if (!fin.hasError()) {
                                    setStatus("Video capturee – compression HCS...");
                                    // Hand to HCS Bundle Service
                                    HCSBundleService.compressVideo(
                                            CameraActivity.this,
                                            videoFile.getAbsolutePath(),
                                            mPreset,
                                            true
                                    );
                                    Toast.makeText(CameraActivity.this,
                                            "Video 8K HCS en cours de compression",
                                            Toast.LENGTH_SHORT).show();
                                } else {
                                    setStatus("Erreur enregistrement video");
                                    Log.e(TAG, "Video error: " + fin.getCause());
                                }
                            });
                        }
                    });
        } catch (Exception e) {
            Log.e(TAG, "startVideo failed", e);
            setStatus("Erreur demarrage video");
        }
    }

    private void stopVideo() {
        if (mCurrentRecording != null) {
            mCurrentRecording.stop();
            mCurrentRecording = null;
        }
    }

    // ─── Utilities ────────────────────────────────────────────────────────

    private void flipCamera() {
        mFrontCamera = !mFrontCamera;
        bindUseCases();
    }

    private void cyclePreset() {
        CompressionPreset[] presets = CompressionPreset.values();
        int currentIdx = 0;
        for (int i = 0; i < presets.length; i++) {
            if (presets[i] == mPreset) { currentIdx = i; break; }
        }
        mPreset = presets[(currentIdx + 1) % presets.length];
        updatePresetLabel();
        Toast.makeText(this, "Preset: " + mPreset.displayName, Toast.LENGTH_SHORT).show();
    }

    private void updatePresetLabel() {
        if (mTvPreset != null) {
            mTvPreset.setText("Preset: " + mPreset.displayName
                    + "  (x" + mPreset.targetRatio + " compression)");
        }
    }

    private void setStatus(String msg) {
        mMainHandler.post(() -> {
            if (mTvStatus != null) mTvStatus.setText(msg);
        });
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (mCurrentRecording != null) mCurrentRecording.stop();
        if (mCameraProvider != null) mCameraProvider.unbindAll();
        mCameraExecutor.shutdown();
    }
}
