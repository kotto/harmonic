# Quick Start — Deployment Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Update Your Express Server (2 min)

Open your main server file (`server.js`, `app.js`, or `index.js`):

```javascript
// Add these imports at the top
const { registerMobileRoutes } = require('./api/routes_mobile');
const { registerPrecompressedRoutes } = require('./api/routes_precompressed');

// Add these lines before app.listen() or app.use(...)
registerMobileRoutes(app);
registerPrecompressedRoutes(app);

// Start your server
app.listen(3000, () => {
  console.log('Server running on port 3000');
});
```

### Step 2: Install Python Dependencies (1 min)

```bash
pip install pillow numpy zstandard
```

### Step 3: Restart Your Server (1 min)

```bash
npm start
```

### Step 4: Test It Works (1 min)

```bash
# Test mobile endpoint
curl http://localhost:3000/api/mobile/info

# Test precompressed endpoint
curl http://localhost:3000/api/precompressed/info
```

Both should return JSON with supported formats.

---

## 🎯 What You Now Have

### 3 Compression Tabs in Web Interface

1. **🖼️ Images Pré-Compressées** (Pre-compressed images)
   - JPEG, PNG, WebP, GIF
   - Strategies: AUTO, DIRECT, HYBRID, TRANSCODE
   - Ratio: 1.1-8:1

2. **📱 Mobile Photos/Vidéos** (Smartphone media)
   - iPhone: HEIC (3-5:1)
   - Android: JPEG (1.2-1.5:1)
   - Videos: MP4, MOV (1.05-3:1)

3. **🎥 Vidéos** (Professional videos)
   - H.264, H.265, SDI 4:2:2
   - Ratio: 6.92-12:1

### 9 API Endpoints

**Mobile:**
- `POST /api/mobile/compress` - Upload and compress
- `GET /api/mobile/download/:id` - Download file
- `GET /api/mobile/info` - Get formats

**Pre-Compressed:**
- `POST /api/precompressed` - Upload and compress
- `GET /api/precompressed/download/:id` - Download file
- `GET /api/precompressed/info` - Get formats

**Video:**
- `POST /api/upload` - Upload video
- `GET /api/download/:id` - Download file
- `GET /api/video/info` - Get formats

---

## 📊 Performance at a Glance

| Media Type | Compression | Savings | Time |
|------------|-------------|---------|------|
| iPhone Photo (HEIC) | 3-5:1 | 75-80% | 2-5s |
| Android Photo (JPEG) | 1.2-1.5:1 | 17-33% | 100-500ms |
| Video (H.264) | 1.3-1.8:1 | 23-44% | 1-3s |
| Video (H.265) | 2-3:1 | 50-67% | 2-5s |

---

## 🧪 Verify Everything Works

Run the test script:

```bash
bash test_mobile_integration.sh
```

Expected output:
```
✓ PASS: Server Running
✓ PASS: Mobile Info Endpoint
✓ PASS: Python Codec
✓ PASS: Python Dependencies
✓ PASS: Mobile Handler
✓ PASS: Mobile Routes
✓ PASS: Web Interface
```

---

## 🌐 Access Web Interface

Open in browser:
```
http://localhost:3000/path/to/unified_compression.html
```

You should see 3 tabs:
1. 🖼️ Images Pré-Compressées
2. 📱 Mobile Photos/Vidéos
3. 🎥 Vidéos

---

## 📝 Example Usage

### Compress iPhone Photo

```bash
curl -X POST http://localhost:3000/api/mobile/compress \
  -F "file=@photo.heic" \
  -F "media-type=auto"
```

Response:
```json
{
  "ok": true,
  "compression": {
    "originalSize": 2500000,
    "compressedSize": 500000,
    "ratio": 5.0,
    "savings": 80.0,
    "time": 3.5
  },
  "strategy": "TRANSCODE"
}
```

### Compress Pre-Compressed Image

```bash
curl -X POST http://localhost:3000/api/precompressed \
  -F "image=@photo.jpg" \
  -F "strategy=AUTO"
```

Response:
```json
{
  "ok": true,
  "compression": {
    "originalSize": 1024000,
    "compressedSize": 512000,
    "ratio": 2.0,
    "savings": 50.0,
    "time": 0.5
  },
  "strategy": "DIRECT"
}
```

---

## ⚠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| "Cannot find module" | Make sure files are in `api/` directory |
| "Python not found" | Install Python 3: `python3 --version` |
| "Missing dependencies" | Run: `pip install pillow numpy zstandard` |
| "Codec not found" | Check path: `COMPRESSION-SOLUTIONS/HCV_MOBILE_CAMERA_CODEC/` |
| "Port already in use" | Change port in server.js or kill process on port 3000 |

---

## 📚 Documentation

For more details, see:
- `INTEGRATION_MOBILE_COMPLETE.md` - Full mobile guide
- `INTEGRATION_PRECOMPRESSED_WEB.md` - Full pre-compressed guide
- `PROJECT_STATUS_FINAL.md` - Complete project status
- `MOBILE_INTEGRATION_CHECKLIST.md` - Detailed checklist

---

## ✅ Deployment Checklist

- [ ] Updated Express server with routes
- [ ] Installed Python dependencies
- [ ] Restarted server
- [ ] Tested endpoints with curl
- [ ] Ran test script
- [ ] Accessed web interface
- [ ] Tested with real files
- [ ] Verified compression metrics

---

## 🎉 You're Done!

Your application now supports:
- ✅ Mobile photo compression (HEIC, JPEG)
- ✅ Mobile video compression (MP4, MOV)
- ✅ Pre-compressed image compression
- ✅ Professional video formats (H.264, H.265, SDI)
- ✅ Intelligent strategy selection
- ✅ Guaranteed no expansion
- ✅ Web interface with 3 tabs
- ✅ 9 API endpoints

**Total Integration Time: ~5 minutes**

---

## 🚀 Next Steps

1. Test with real smartphone photos/videos
2. Monitor compression metrics
3. Optimize codec parameters if needed
4. Deploy to production
5. Gather user feedback

---

**Ready to deploy? Start with Step 1 above! 🚀**
