// api/routes_precompressed.js — Routes pour compression pré-compressée
// À intégrer dans le serveur Express/Node.js existant

const precompressedHandler = require('./precompressed_handler');

/**
 * Enregistre les routes pour compression pré-compressée
 * @param {Express} app - Application Express
 */
function registerPrecompressedRoutes(app) {
  /**
   * POST /api/precompressed
   * Upload et compression d'images pré-compressées
   * 
   * Body (multipart/form-data):
   *   - image: File (JPEG, PNG, WebP, GIF, etc.)
   *   - strategy: string (AUTO, DIRECT, HYBRID, TRANSCODE) [optional]
   * 
   * Response:
   *   {
   *     ok: boolean,
   *     outputId: string,
   *     strategy: string,
   *     recommendedStrategy: string,
   *     formatInfo: {
   *       format: string,
   *       quality: number,
   *       size: number,
   *       extension: string
   *     },
   *     compression: {
   *       originalSize: number,
   *       compressedSize: number,
   *       ratio: number,
   *       savings: number,
   *       time: number
   *     },
   *     metadata: object
   *   }
   */
  app.post('/api/precompressed', precompressedHandler);

  /**
   * GET /api/precompressed/download/:id
   * Télécharge le fichier compressé
   */
  app.get('/api/precompressed/download/:id', (req, res) => {
    const { id } = req.params;
    const path = require('path');
    const os = require('os');
    const fs = require('fs');

    // Validation UUID
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(id)) {
      return res.status(400).json({ error: 'ID invalide' });
    }

    const filePath = path.join(os.tmpdir(), id + '.hcp');

    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: 'Fichier non trouvé' });
    }

    res.download(filePath, `compressed_${id.slice(0, 8)}.hcp`, (err) => {
      if (err) {
        console.error('Erreur download:', err);
      }
      // Nettoyer le fichier après téléchargement
      try {
        fs.unlinkSync(filePath);
      } catch (e) {
        // Ignorer les erreurs de suppression
      }
    });
  });

  /**
   * GET /api/precompressed/info/:id
   * Récupère les informations de compression
   */
  app.get('/api/precompressed/info/:id', (req, res) => {
    // À implémenter: récupérer les métadonnées depuis une base de données
    res.json({
      error: 'Non implémenté'
    });
  });

  /**
   * POST /api/precompressed/batch
   * Compression en batch de plusieurs images
   */
  app.post('/api/precompressed/batch', async (req, res) => {
    // À implémenter: traiter plusieurs fichiers
    res.json({
      error: 'Non implémenté'
    });
  });
}

module.exports = { registerPrecompressedRoutes };
