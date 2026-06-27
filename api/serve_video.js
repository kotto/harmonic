/**
 * API Endpoint pour servir les vidéos traitées
 */

const fs = require('fs');
const path = require('path');

module.exports = async (req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Range');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  if (req.method !== 'GET') {
    res.writeHead(405, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Method not allowed' }));
    return;
  }

  try {
    // Extraire le nom du fichier depuis l'URL
    const url = new URL(req.url, `http://${req.headers.host}`);
    const filename = url.searchParams.get('file');
    
    if (!filename) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Paramètre file manquant' }));
      return;
    }

    // Sécurité : vérifier que le fichier est dans outputs/
    const outputDir = path.join(__dirname, '..', 'outputs');
    const filePath = path.join(outputDir, filename);
    
    // Vérifier que le chemin est sécurisé
    if (!filePath.startsWith(outputDir)) {
      res.writeHead(403, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Accès interdit' }));
      return;
    }

    // Vérifier que le fichier existe
    if (!fs.existsSync(filePath)) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Fichier non trouvé' }));
      return;
    }

    // Obtenir les informations du fichier
    const stat = fs.statSync(filePath);
    const fileSize = stat.size;
    
    // Support du streaming vidéo avec Range requests
    const range = req.headers.range;
    
    if (range) {
      // Parse range header
      const parts = range.replace(/bytes=/, "").split("-");
      const start = parseInt(parts[0], 10);
      const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
      const chunksize = (end - start) + 1;
      
      // Créer le stream
      const file = fs.createReadStream(filePath, { start, end });
      
      // Headers pour partial content
      res.writeHead(206, {
        'Content-Range': `bytes ${start}-${end}/${fileSize}`,
        'Accept-Ranges': 'bytes',
        'Content-Length': chunksize,
        'Content-Type': 'video/mp4',
      });
      
      file.pipe(res);
    } else {
      // Pas de range, servir le fichier complet
      res.writeHead(200, {
        'Content-Length': fileSize,
        'Content-Type': 'video/mp4',
        'Accept-Ranges': 'bytes',
      });
      
      fs.createReadStream(filePath).pipe(res);
    }

  } catch (error) {
    console.error('Erreur serve_video:', error);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Erreur serveur' }));
  }
};