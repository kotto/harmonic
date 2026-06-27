// api/routes_mobile.js — Routes pour compression mobile (photos/vidéos smartphone)
// Intègre le gestionnaire mobile dans l'application Express

const express = require('express');
const mobileHandler = require('./mobile_handler');

/**
 * Enregistre les routes de compression mobile
 * @param {express.Application} app - Application Express
 */
function registerMobileRoutes(app) {
  const router = express.Router();

  /**
   * POST /api/mobile/compress
   * Upload et compresse une photo/vidéo de smartphone
   * 
   * Body: multipart/form-data
   *   - file: Fichier à compresser (JPEG, HEIC, MP4, MOV, etc.)
   *   - media-type: Type de média (auto, photo, video) - optionnel
   * 
   * Response:
   *   {
   *     ok: true,
   *     outputId: "uuid",
   *     mediaType: "photo" | "video",
   *     formatInfo: { format, subType, mediaType, size, extension },
   *     compression: {
   *       originalSize: number,
   *       compressedSize: number,
   *       ratio: number,
   *       savings: number,
   *       time: number
   *     },
   *     strategy: "AUTO" | "TRANSCODE" | "REENCODE" | "DIRECT",
   *     metadata: { quality, bitrate, duration, etc. }
   *   }
   */
  router.post('/compress', mobileHandler);

  /**
   * GET /api/mobile/download/:id
   * Télécharge le fichier compressé
   * 
   * Params:
   *   - id: ID de sortie du fichier compressé
   * 
   * Response: Fichier binaire .hcv5
   */
  router.get('/download/:id', (req, res) => {
    const { id } = req.params;
    const path = require('path');
    const os = require('os');
    const fs = require('fs');

    const filePath = path.join(os.tmpdir(), id + '.hcv5');

    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: 'Fichier non trouvé' });
    }

    res.download(filePath, `compressed_${id}.hcv5`, (err) => {
      if (err) {
        console.error('Erreur téléchargement:', err);
      }
      // Nettoyer après téléchargement
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
      }
    });
  });

  /**
   * GET /api/mobile/info
   * Retourne les informations sur les formats supportés
   */
  router.get('/info', (req, res) => {
    res.json({
      supported_formats: {
        photos: ['JPEG', 'HEIC', 'HEIF', 'PNG', 'WebP'],
        videos: ['MP4', 'MOV', 'H.264', 'H.265']
      },
      strategies: {
        TRANSCODE: {
          description: 'Décode → Réencode avec HCV',
          ratio: '3-5:1',
          time: '2-5s',
          quality: 'Optimal'
        },
        REENCODE: {
          description: 'Réencode avec codec optimisé',
          ratio: '1.3-1.8:1',
          time: '1-3s',
          quality: 'Très bon'
        },
        DIRECT: {
          description: 'Compression directe zstd',
          ratio: '1.05-1.3:1',
          time: '100-500ms',
          quality: 'Préservé'
        },
        AUTO: {
          description: 'Détection automatique et sélection optimale',
          ratio: 'Variable',
          time: 'Variable',
          quality: 'Optimal'
        }
      },
      max_file_size: '10 GB',
      supported_media_types: ['auto', 'photo', 'video']
    });
  });

  // Enregistrer le routeur
  app.use('/api/mobile', router);
}

module.exports = { registerMobileRoutes };
