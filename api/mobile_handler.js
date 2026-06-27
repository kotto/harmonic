// api/mobile_handler.js — Gestionnaire pour compression mobile (photos/vidéos smartphone)
// Détecte le type de média et applique la stratégie optimale pour mobile

const { verifyToken } = require('./_middleware');
const Busboy = require('busboy');
const crypto = require('crypto');
const path = require('path');
const os = require('os');
const fs = require('fs');
const { spawn } = require('child_process');

// Extensions mobiles supportées
const MOBILE_PHOTO_EXT = new Set(['.jpg', '.jpeg', '.heic', '.heif', '.png', '.webp']);
const MOBILE_VIDEO_EXT = new Set(['.mp4', '.mov', '.m4v']);
const MAX_SIZE_BYTES = 10 * 1024 * 1024 * 1024; // 10 GB

/**
 * Lance le codec mobile Python
 * @param {string} inputPath - Chemin du fichier d'entrée
 * @param {string} mediaType - Type de média (photo ou video)
 * @param {object} options - Options supplémentaires
 * @returns {Promise<object>} Résultats de compression
 */
function runMobileCodec(inputPath, mediaType = 'auto', options = {}) {
  return new Promise((resolve, reject) => {
    const outputId = crypto.randomUUID();
    const outputPath = path.join(os.tmpdir(), outputId + '.hcv5');

    // Validation des paramètres
    if (!fs.existsSync(inputPath)) {
      return reject(new Error(`Fichier d'entrée introuvable: ${inputPath}`));
    }

    // Validation type média
    const validTypes = ['auto', 'photo', 'video'];
    if (!validTypes.includes(mediaType.toLowerCase())) {
      return reject(new Error(`Type média invalide: ${mediaType}. Types supportés: ${validTypes.join(', ')}`));
    }

    // Chemin vers le codec Python
    const possiblePaths = [
      path.join(process.cwd(), 'COMPRESSION-SOLUTIONS', 'HCV_MOBILE_CAMERA_CODEC', 'hcv_mobile_camera_codec.py'),
      path.join(__dirname, '..', 'COMPRESSION-SOLUTIONS', 'HCV_MOBILE_CAMERA_CODEC', 'hcv_mobile_camera_codec.py'),
      './COMPRESSION-SOLUTIONS/HCV_MOBILE_CAMERA_CODEC/hcv_mobile_camera_codec.py'
    ];

    let scriptPath = null;
    for (const p of possiblePaths) {
      if (fs.existsSync(p)) {
        scriptPath = p;
        break;
      }
    }

    if (!scriptPath) {
      return reject(new Error(`Script hcv_mobile_camera_codec.py introuvable`));
    }

    // Commande Python
    const pythonCmd = 'python3';
    const timeout = options.timeout || 600000; // 10 min pour vidéos

    const proc = spawn(pythonCmd, [
      scriptPath,
      '--input', inputPath,
      '--output', outputPath,
      '--media-type', mediaType.toLowerCase(),
      '--verbose', options.verbose ? 'true' : 'false'
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
 * Détecte le type de média (photo ou vidéo)
 * @param {string} filePath - Chemin du fichier
 * @returns {string} Type de média (photo, video, ou unknown)
 */
function detectMediaType(filePath) {
  const ext = path.extname(filePath).toLowerCase();

  if (MOBILE_PHOTO_EXT.has(ext)) {
    return 'photo';
  }

  if (MOBILE_VIDEO_EXT.has(ext)) {
    return 'video';
  }

  return 'unknown';
}

/**
 * Détecte le format spécifique
 * @param {string} filePath - Chemin du fichier
 * @returns {object} Informations de format
 */
function detectFormat(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const stats = fs.statSync(filePath);
  const mediaType = detectMediaType(filePath);

  // Lire les premiers bytes pour détection
  const buffer = Buffer.alloc(512);
  const fd = fs.openSync(filePath, 'r');
  fs.readSync(fd, buffer, 0, 512);
  fs.closeSync(fd);

  let format = 'UNKNOWN';
  let subType = null;

  // Détection JPEG
  if (buffer[0] === 0xFF && buffer[1] === 0xD8) {
    format = 'JPEG';
  }
  // Détection PNG
  else if (buffer[0] === 0x89 && buffer[1] === 0x50 && buffer[2] === 0x4E && buffer[3] === 0x47) {
    format = 'PNG';
  }
  // Détection WebP
  else if (buffer[0] === 0x52 && buffer[1] === 0x49 && buffer[2] === 0x46 && buffer[3] === 0x46) {
    format = 'WEBP';
  }
  // Détection HEIC/HEIF
  else if (ext === '.heic' || ext === '.heif') {
    format = 'HEIC';
  }
  // Détection MP4/MOV
  else if (buffer[4] === 0x66 && buffer[5] === 0x74 && buffer[6] === 0x79 && buffer[7] === 0x70) {
    format = 'MP4';
    // Déterminer le codec
    if (ext === '.mov') {
      subType = 'MOV';
    }
  }

  return {
    format: format,
    subType: subType,
    mediaType: mediaType,
    size: stats.size,
    extension: ext
  };
}

/**
 * Recommande la meilleure stratégie pour mobile
 * @param {object} formatInfo - Informations de format
 * @returns {string} Stratégie recommandée
 */
function recommendMobileStrategy(formatInfo) {
  if (formatInfo.mediaType === 'photo') {
    // Photos: toujours utiliser détection automatique du codec
    return 'AUTO';
  }

  if (formatInfo.mediaType === 'video') {
    // Vidéos: toujours utiliser détection automatique du codec
    return 'AUTO';
  }

  return 'AUTO';
}

/**
 * Gestionnaire principal pour upload mobile
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

    let mediaType = 'auto';
    let fileReceived = false;
    let uploadError = null;
    let tmpPath = null;
    let originalName = '';
    let formatInfo = null;

    bb.on('field', (name, val) => {
      if (name === 'media-type' && ['auto', 'photo', 'video'].includes(val.toLowerCase())) {
        mediaType = val.toLowerCase();
      }
    });

    bb.on('file', (fieldname, stream, info) => {
      const { filename, mimeType } = info;
      const ext = path.extname(filename).toLowerCase();

      // Vérifier que c'est un fichier mobile
      if (!MOBILE_PHOTO_EXT.has(ext) && !MOBILE_VIDEO_EXT.has(ext)) {
        stream.resume(); // drain
        uploadError = `Extension non autorisée : ${ext}. Formats supportés: ${Array.from(MOBILE_PHOTO_EXT).concat(Array.from(MOBILE_VIDEO_EXT)).join(', ')}`;
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

        // Détecte le type de média si auto
        let finalMediaType = mediaType;
        if (mediaType === 'auto') {
          finalMediaType = detectMediaType(tmpPath);
        }

        // Lance le codec mobile
        const result = await runMobileCodec(tmpPath, finalMediaType, {
          timeout: finalMediaType === 'video' ? 600000 : 60000, // 10 min pour vidéos, 1 min pour photos
          verbose: false
        });

        // Retourne les résultats
        res.json({
          ok: true,
          outputId: result.outputId,
          mediaType: finalMediaType,
          formatInfo: formatInfo,
          compression: {
            originalSize: result.original_size,
            compressedSize: result.compressed_size,
            ratio: result.ratio,
            savings: result.savings,
            time: result.time
          },
          strategy: result.strategy || 'AUTO',
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
