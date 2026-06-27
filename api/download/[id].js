// api/download/[id].js — Téléchargement sécurisé du fichier .hcv16 compressé
// Seuls les utilisateurs authentifiés peuvent télécharger

const { verifyToken } = require('../_middleware');
const crypto = require('crypto');
const path = require('path');
const fs = require('fs');
const os = require('os');

// En production, récupérer le fichier depuis S3/stockage selon l'ID
// Ici on génère un fichier .hcv16 de démonstration valide
function getCompressedFile(id) {
  // Validation UUID pour éviter path traversal
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!uuidRegex.test(id)) return null;

  // En production : chemin réel depuis le stockage
  // const filePath = path.join('/mnt/hcv-storage', id + '.hcv16');
  // if (!fs.existsSync(filePath)) return null;
  // return { path: filePath, name: id + '.hcv16' };

  // Stub : génère un fichier de démo avec header HCV16 valide
  const tmpPath = path.join(os.tmpdir(), id + '.hcv16');
  if (!fs.existsSync(tmpPath)) {
    // Header HCV16 : magic bytes + metadata JSON
    const magic = Buffer.from('HCV16\x00\x01\x00'); // 8 bytes magic
    const meta = Buffer.from(JSON.stringify({
      version: 16,
      id,
      mode: 'HCV_SDI',
      ratio: 11.85,
      psnr: 'Infinity',
      created: new Date().toISOString(),
      codec: 'zstd-11',
      colorspace: 'BT.709',
      resolution: '1920x1080',
      fps: 60
    }));
    const metaLen = Buffer.alloc(4);
    metaLen.writeUInt32LE(meta.length, 0);
    // Payload simulé (en prod : données compressées réelles)
    const payload = crypto.randomBytes(1024);
    const crc = crypto.createHash('sha256').update(payload).digest();
    fs.writeFileSync(tmpPath, Buffer.concat([magic, metaLen, meta, crc, payload]));
  }
  return { path: tmpPath, name: `archive_${id.slice(0,8)}.hcv16` };
}

module.exports = async function handler(req, res) {
  // Auth obligatoire
  const payload = verifyToken(req);
  if (!payload) {
    return res.status(401).json({ error: 'Non authentifié' });
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Méthode non autorisée' });
  }

  const { id } = req.query;
  if (!id) return res.status(400).json({ error: 'ID manquant' });

  const file = getCompressedFile(id);
  if (!file) {
    return res.status(404).json({ error: 'Archive introuvable' });
  }

  const stat = fs.statSync(file.path);
  res.setHeader('Content-Type', 'application/octet-stream');
  res.setHeader('Content-Disposition', `attachment; filename="${file.name}"`);
  res.setHeader('Content-Length', stat.size);
  res.setHeader('X-HCV-Version', '16');
  res.setHeader('Cache-Control', 'no-store');

  const stream = fs.createReadStream(file.path);
  stream.pipe(res);
};
