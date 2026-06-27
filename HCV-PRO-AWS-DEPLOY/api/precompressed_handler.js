// api/precompressed_handler.js — Gestionnaire pour fichiers pré-compressés
// Détecte le format et applique la stratégie optimale (DIRECT, HYBRID, TRANSCODE, AUTO)

const { verifyToken } = require('./_middleware');
const Busboy = require('busboy');
const crypto = require('crypto');
const path = require('path');
const os = require('os');
const fs = require('fs');
const { spawn } = require('child_process');

// Extensions pré-compressées supportées
const PRECOMPRESSED_EXT = new Set(['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff']);
const MAX_SIZE_BYTES = 10 * 1024 * 1024 * 1024; // 10 GB

/**
 * Lance le codec pré-compressé Python
 * @param {string} inputPath - Chemin du fichier d'entrée
 * @param {string} strategy - Stratégie (AUTO, DIRECT, HYBRID, TRANSCODE)
 * @param {object} options - Options supplémentaires
 * @returns {Promise<object>} Résultats de compression
 */
function runPrecompressedCodec(inputPath, strategy = 'AUTO', options = {}) {
  return new Promise((resolve, reject) => {
    const outputId = crypto.randomUUID();
    const outputPath = path.join(os.tmpdir(), outputId + '.hcp');

    // Validation des paramètres
    if (!fs.existsSync(inputPath)) {
      return reject(new Error(`Fichier d'entrée introuvable: ${inputPath}`));
    }

    // Validation stratégie
    const validStrategies = ['AUTO', 'DIRECT', 'HYBRID', 'TRANSCODE'];
    if (!validStrategies.includes(strategy.toUpperCase())) {
      return reject(new Error(`Stratégie invalide: ${strategy}. Stratégies supportées: ${validStrategies.join(', ')}`));
    }

    // Chemin vers le codec Python
    const possiblePaths = [
      path.join(process.cwd(), 'COMPRESSION-CAMERA', 'METHOD_2_SDI_LIKE_IMAGE_COMPRESSION', 'hcv_precompressed_codec.py'),
      path.join(__dirname, '..', 'COMPRESSION-CAMERA', 'METHOD_2_SDI_LIKE_IMAGE_COMPRESSION', 'hcv_precompressed_codec.py'),
      './COMPRESSION-CAMERA/METHOD_2_SDI_LIKE_IMAGE_COMPRESSION/hcv_precompressed_codec.py'
    ];

    let scriptPath = null;
    for (const p of possiblePaths) {
      if (fs.existsSync(p)) {
        scriptPath = p;
        break;
      }
    }

    if (!scriptPath) {
      return reject(new Error(`Script hcv_precompressed_codec.py introuvable`));
    }

    // Commande Python
    const pythonCmd = 'python3';
    const timeout = options.timeout || 300000; // 5 min

    const proc = spawn(pythonCmd, [
      scriptPath,
      '--input', inputPath,
      '--output', outputPath,
      '--strategy', strategy.toUpperCase(),
      '--zstd-level', options.zstdLevel || '22'
    ], {
      timeout: timeout,
      stdio: ['ignore', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    proc.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    proc.on('close', (code) => {
      if (code !== 0) {
        return reject(new Error(`Codec échoué (code ${code}): ${stderr}`));
      }

      try {
        // Parser la sortie JSON
        const result = JSON.parse(stdout);

        if (result.error) {
          return reject(new Error(result.error));
        }

        // Vérifier que le fichier de sortie existe
        if (!fs.existsSync(outputPath)) {
          return reject(new Error('Fichier de sortie non créé'));
        }

        // Retourner les résultats
        resolve({
          outputPath: outputPath,
          outputId: outputId,
          ...result
        });
      } catch (e) {
        reject(new Error(`Erreur parsing résultat: ${e.message}`));
      }
    });

    proc.on('error', (err) => {
      reject(new Error(`Erreur spawn: ${err.message}`));
    });
  });
}

/**
 * Détecte le format et la qualité d'une image
 * @param {string} filePath - Chemin du fichier
 * @returns {object} Informations de format
 */
function detectFormat(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const stats = fs.statSync(filePath);

  // Lire les premiers bytes pour détection
  const buffer = Buffer.alloc(512);
  const fd = fs.openSync(filePath, 'r');
  fs.readSync(fd, buffer, 0, 512);
  fs.closeSync(fd);

  let format = 'UNKNOWN';
  let quality = null;

  // Détection JPEG
  if (buffer[0] === 0xFF && buffer[1] === 0xD8) {
    format = 'JPEG';
    // Estimation qualité (simplifié)
    quality = estimateJPEGQuality(filePath);
  }
  // Détection PNG
  else if (buffer[0] === 0x89 && buffer[1] === 0x50 && buffer[2] === 0x4E && buffer[3] === 0x47) {
    format = 'PNG';
    quality = 100; // PNG est lossless
  }
  // Détection WebP
  else if (buffer[0] === 0x52 && buffer[1] === 0x49 && buffer[2] === 0x46 && buffer[3] === 0x46) {
    format = 'WEBP';
    quality = 95; // WebP est généralement bien optimisé
  }
  // Détection GIF
  else if (buffer[0] === 0x47 && buffer[1] === 0x49 && buffer[2] === 0x46) {
    format = 'GIF';
    quality = 100; // GIF est lossless
  }

  return {
    format: format,
    quality: quality,
    size: stats.size,
    extension: ext
  };
}

/**
 * Estime la qualité JPEG (simplifié)
 * @param {string} filePath - Chemin du fichier JPEG
 * @returns {number} Qualité estimée (0-100)
 */
function estimateJPEGQuality(filePath) {
  // Implémentation simplifié: analyser les marqueurs JPEG
  // En production, utiliser une librairie comme 'jpeg-quality'
  const stats = fs.statSync(filePath);
  const sizeKB = stats.size / 1024;

  // Heuristique simple basée sur la taille
  if (sizeKB < 10) return 60;
  if (sizeKB < 50) return 75;
  if (sizeKB < 200) return 85;
  return 95;
}

/**
 * Recommande la meilleure stratégie
 * @param {object} formatInfo - Informations de format
 * @returns {string} Stratégie recommandée
 */
function recommendStrategy(formatInfo) {
  if (formatInfo.format === 'JPEG') {
    if (formatInfo.quality < 70) return 'TRANSCODE'; // Améliorer qualité
    if (formatInfo.quality < 85) return 'HYBRID';    // Équilibre
    return 'DIRECT';                                  // Préserver qualité
  }

  // PNG, WebP, GIF: toujours DIRECT
  if (['PNG', 'WEBP', 'GIF'].includes(formatInfo.format)) {
    return 'DIRECT';
  }

  // Défaut: AUTO
  return 'AUTO';
}

/**
 * Gestionnaire principal pour upload pré-compressé
 */
module.exports = async function handler(req, res) {
  // Auth obligatoire
  const payload = verifyToken(req);
  if (!payload) {
    return res.status(401).json({ error: 'Non authentifié' });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Méthode non autorisée' });
  }

  const contentType = req.headers['content-type'] || '';
  if (!contentType.includes('multipart/form-data')) {
    return res.status(400).json({ error: 'Content-Type doit être multipart/form-data' });
  }

  return new Promise((resolve) => {
    const bb = Busboy({
      headers: req.headers,
      limits: { fileSize: MAX_SIZE_BYTES, files: 1 }
    });

    let strategy = 'AUTO';
    let fileReceived = false;
    let uploadError = null;
    let tmpPath = null;
    let originalName = '';
    let formatInfo = null;

    bb.on('field', (name, val) => {
      if (name === 'strategy' && ['AUTO', 'DIRECT', 'HYBRID', 'TRANSCODE'].includes(val.toUpperCase())) {
        strategy = val.toUpperCase();
      }
    });

    bb.on('file', (fieldname, stream, info) => {
      const { filename, mimeType } = info;
      const ext = path.extname(filename).toLowerCase();

      if (!PRECOMPRESSED_EXT.has(ext)) {
        stream.resume(); // drain
        uploadError = `Extension non autorisée : ${ext}. Formats supportés: ${Array.from(PRECOMPRESSED_EXT).join(', ')}`;
        return;
      }

      fileReceived = true;
      originalName = filename;
      tmpPath = path.join(os.tmpdir(), crypto.randomUUID() + ext);
      const writeStream = fs.createWriteStream(tmpPath);

      stream.on('limit', () => {
        uploadError = 'Fichier trop volumineux (max 10 GB)';
        stream.resume();
      });

      stream.pipe(writeStream);
    });

    bb.on('finish', async () => {
      if (uploadError) {
        if (tmpPath && fs.existsSync(tmpPath)) fs.unlinkSync(tmpPath);
        res.status(400).json({ error: uploadError });
        return resolve();
      }

      if (!fileReceived) {
        res.status(400).json({ error: 'Aucun fichier reçu' });
        return resolve();
      }

      try {
        // Détecte le format
        formatInfo = detectFormat(tmpPath);

        // Recommande la stratégie si AUTO
        let finalStrategy = strategy;
        if (strategy === 'AUTO') {
          finalStrategy = recommendStrategy(formatInfo);
        }

        // Lance le codec
        const result = await runPrecompressedCodec(tmpPath, finalStrategy, {
          timeout: 300000,
          zstdLevel: 22
        });

        // Retourne les résultats
        res.json({
          ok: true,
          outputId: result.outputId,
          strategy: finalStrategy,
          recommendedStrategy: recommendStrategy(formatInfo),
          formatInfo: formatInfo,
          compression: {
            originalSize: result.original_size,
            compressedSize: result.compressed_size,
            ratio: result.ratio,
            savings: result.savings,
            time: result.time
          },
          metadata: result.metadata || {}
        });

      } catch (error) {
        res.status(500).json({
          error: error.message,
          formatInfo: formatInfo
        });
      } finally {
        // Nettoyage
        if (tmpPath && fs.existsSync(tmpPath)) {
          fs.unlinkSync(tmpPath);
        }
      }
    });

    bb.on('error', (err) => {
      res.status(400).json({ error: `Erreur upload: ${err.message}` });
      return resolve();
    });

    req.pipe(bb);
  });
};
