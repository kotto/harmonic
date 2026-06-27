#!/usr/bin/env node

/**
 * HCV Studio — Serveur Express Principal
 * Lance l'application web avec support pour:
 * - Compression mobile (photos/vidéos smartphone)
 * - Compression pré-compressée (images/vidéos)
 * - Compression vidéo professionnelle (H264, H265, SDI)
 */

const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json({ limit: '100mb' }));
app.use(express.urlencoded({ limit: '100mb', extended: true }));
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.static(path.join(__dirname, 'COMPRESSION-SOLUTIONS')));

// Routes pour les fichiers statiques
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'COMPRESSION-SOLUTIONS', 'index.html'));
});

app.get('/studio', (req, res) => {
  res.sendFile(path.join(__dirname, 'hcv_studio.html'));
});

app.get('/compression', (req, res) => {
  res.sendFile(path.join(__dirname, 'COMPRESSION-SOLUTIONS', 'unified_compression.html'));
});

app.get('/player', (req, res) => {
  res.sendFile(path.join(__dirname, 'hcv_studio.html'));
});

// Importer et enregistrer les routes mobiles
try {
  const { registerMobileRoutes } = require('./api/routes_mobile');
  registerMobileRoutes(app);
  console.log('✅ Routes mobiles enregistrées');
} catch (err) {
  console.warn('⚠️  Routes mobiles non disponibles:', err.message);
}

// Importer et enregistrer les routes pré-compressées
try {
  const { registerPrecompressedRoutes } = require('./api/routes_precompressed');
  registerPrecompressedRoutes(app);
  console.log('✅ Routes pré-compressées enregistrées');
} catch (err) {
  console.warn('⚠️  Routes pré-compressées non disponibles:', err.message);
}

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    ok: true,
    status: 'running',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Info endpoint
app.get('/api/info', (req, res) => {
  res.json({
    name: 'HCV Studio',
    version: '1.0.0',
    features: [
      'Mobile photo compression (HEIC, JPEG)',
      'Mobile video compression (MP4, MOV)',
      'Pre-compressed image compression',
      'Professional video formats (H.264, H.265, SDI)'
    ],
    endpoints: {
      mobile: '/api/mobile',
      precompressed: '/api/precompressed',
      compression: '/compression'
    }
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Not found',
    path: req.path,
    method: req.method
  });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: err.message
  });
});

// Start server
app.listen(PORT, () => {
  console.log('\n');
  console.log('╔════════════════════════════════════════════════════════╗');
  console.log('║          🎬 HCV Studio — Serveur Lancé                 ║');
  console.log('╚════════════════════════════════════════════════════════╝');
  console.log('\n');
  console.log(`✅ Serveur en écoute sur: http://localhost:${PORT}`);
  console.log('\n');
  console.log('📱 Interfaces disponibles:');
  console.log(`   • Interface principale:     http://localhost:${PORT}/`);
  console.log(`   • Compression unifiée:      http://localhost:${PORT}/compression`);
  console.log(`   • Lecteur HCV:              http://localhost:${PORT}/player`);
  console.log('\n');
  console.log('🔌 API Endpoints:');
  console.log(`   • Mobile:                   http://localhost:${PORT}/api/mobile/info`);
  console.log(`   • Pré-compressé:            http://localhost:${PORT}/api/precompressed/info`);
  console.log(`   • Santé du serveur:         http://localhost:${PORT}/api/health`);
  console.log(`   • Infos serveur:            http://localhost:${PORT}/api/info`);
  console.log('\n');
  console.log('📚 Documentation:');
  console.log('   • QUICK_START_DEPLOYMENT.md');
  console.log('   • README_MOBILE_INTEGRATION.md');
  console.log('   • DOCUMENTATION_INDEX.md');
  console.log('\n');
  console.log('💡 Appuyez sur Ctrl+C pour arrêter le serveur');
  console.log('\n');
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n\n🛑 Arrêt du serveur...');
  process.exit(0);
});
