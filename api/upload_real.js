/**
 * API Upload Réel pour HCV Studio Cascade
 * Gestion upload de fichiers vidéo avec traitement multipart
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Configuration
const UPLOAD_DIR = path.join(__dirname, '..', 'uploads');
const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB

// Créer le dossier uploads
if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true });
}

module.exports = async (req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  if (req.method !== 'POST') {
    res.writeHead(405, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Method not allowed' }));
    return;
  }

  try {
    const contentType = req.headers['content-type'] || '';
    
    if (contentType.includes('multipart/form-data')) {
      // Traitement multipart
      return await handleMultipartUpload(req, res);
    } else {
      // Upload direct
      return await handleDirectUpload(req, res);
    }

  } catch (error) {
    console.error('Upload error:', error);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Upload failed', message: error.message }));
  }
};

async function handleMultipartUpload(req, res) {
  const boundary = req.headers['content-type'].split('boundary=')[1];
  if (!boundary) {
    throw new Error('No boundary found in multipart data');
  }

  let buffer = Buffer.alloc(0);
  let totalSize = 0;

  return new Promise((resolve, reject) => {
    req.on('data', (chunk) => {
      totalSize += chunk.length;
      
      if (totalSize > MAX_FILE_SIZE) {
        reject(new Error('File too large'));
        return;
      }
      
      buffer = Buffer.concat([buffer, chunk]);
    });

    req.on('end', () => {
      try {
        const result = parseMultipartData(buffer, boundary);
        
        if (!result.file) {
          reject(new Error('No file found in upload'));
          return;
        }

        // Générer nom de fichier unique
        const fileId = crypto.randomUUID();
        const originalName = result.filename || 'video.mp4';
        const ext = path.extname(originalName);
        const filename = `${fileId}${ext}`;
        const filepath = path.join(UPLOAD_DIR, filename);

        // Sauvegarder le fichier
        fs.writeFileSync(filepath, result.file);

        console.log(`✅ Fichier uploadé: ${filename} (${result.file.length} bytes)`);

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          success: true,
          file_id: fileId,
          filename: filename,
          original_name: originalName,
          size: result.file.length,
          path: filepath
        }));

        resolve();

      } catch (error) {
        reject(error);
      }
    });

    req.on('error', reject);
  });
}

async function handleDirectUpload(req, res) {
  let buffer = Buffer.alloc(0);
  let totalSize = 0;

  return new Promise((resolve, reject) => {
    req.on('data', (chunk) => {
      totalSize += chunk.length;
      
      if (totalSize > MAX_FILE_SIZE) {
        reject(new Error('File too large'));
        return;
      }
      
      buffer = Buffer.concat([buffer, chunk]);
    });

    req.on('end', () => {
      try {
        // Générer nom de fichier unique
        const fileId = crypto.randomUUID();
        const filename = `${fileId}.mp4`;
        const filepath = path.join(UPLOAD_DIR, filename);

        // Sauvegarder le fichier
        fs.writeFileSync(filepath, buffer);

        console.log(`✅ Fichier uploadé: ${filename} (${buffer.length} bytes)`);

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          success: true,
          file_id: fileId,
          filename: filename,
          size: buffer.length,
          path: filepath
        }));

        resolve();

      } catch (error) {
        reject(error);
      }
    });

    req.on('error', reject);
  });
}

function parseMultipartData(buffer, boundary) {
  const boundaryBuffer = Buffer.from(`--${boundary}`);
  const parts = [];
  let start = 0;

  // Trouver toutes les parties
  while (true) {
    const boundaryIndex = buffer.indexOf(boundaryBuffer, start);
    if (boundaryIndex === -1) break;

    if (start > 0) {
      parts.push(buffer.slice(start, boundaryIndex));
    }

    start = boundaryIndex + boundaryBuffer.length;
  }

  // Parser chaque partie
  for (const part of parts) {
    const headerEnd = part.indexOf('\r\n\r\n');
    if (headerEnd === -1) continue;

    const headers = part.slice(0, headerEnd).toString();
    const content = part.slice(headerEnd + 4);

    // Vérifier si c'est un fichier
    if (headers.includes('Content-Disposition: form-data') && headers.includes('filename=')) {
      const filenameMatch = headers.match(/filename="([^"]+)"/);
      const filename = filenameMatch ? filenameMatch[1] : 'unknown';

      return {
        file: content.slice(0, -2), // Enlever \r\n final
        filename: filename
      };
    }
  }

  throw new Error('No file found in multipart data');
}