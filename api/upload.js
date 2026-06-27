// api/upload.js — Upload distant sécurisé (multipart/form-data)
// Le moteur HCV tourne côté serveur, jamais exposé au client

const { verifyToken } = require('./_middleware');
const Busboy = require('busboy');
const crypto = require('crypto');
const path = require('path');
const os = require('os');
const fs = require('fs');

// Extensions autorisées pour l'upload
const ALLOWED_EXT = new Set(['.mxf', '.mov', '.ts', '.mp4', '.hcv16', '.avi', '.h264', '.h265', '.hevc', '.sdi', '.yuv']);
const MAX_SIZE_BYTES = 10 * 1024 * 1024 * 1024; // 10 GB

// Lance le moteur HCV Python côté serveur avec gestion d'erreurs robuste
function runHCVEngine(inputPath, mode, options = {}) {
  return new Promise((resolve, reject) => {
    const { spawn } = require('child_process');
    const outputId  = crypto.randomUUID();
    const outputPath = path.join(os.tmpdir(), outputId + '.hcv16');

    // Validation des paramètres
    if (!fs.existsSync(inputPath)) {
      return reject(new Error(`Fichier d'entrée introuvable: ${inputPath}`));
    }

    // Mapping mode UI → mode Python avec validation
    const modeMap = { 
      fast: 'LOSSLESS', 
      sdi: 'GRAIN_SYNTH', 
      arch: 'SIGNAL_ONLY' 
    };
    const hcvMode = modeMap[mode];
    if (!hcvMode) {
      return reject(new Error(`Mode invalide: ${mode}. Modes supportés: ${Object.keys(modeMap).join(', ')}`));
    }

    // Chemin vers le wrapper Python avec fallbacks
    const possiblePaths = [
      path.join(process.cwd(), 'api', 'hcv_engine.py'),
      path.join(__dirname, 'hcv_engine.py'),
      './hcv_engine.py'
    ];
    
    let scriptPath = null;
    for (const p of possiblePaths) {
      if (fs.existsSync(p)) {
        scriptPath = p;
        break;
      }
    }
    
    if (!scriptPath) {
      return reject(new Error(`Script hcv_engine.py introuvable. Chemins testés: ${possiblePaths.join(', ')}`));
    }

    // Commandes Python avec fallbacks
    const pythonCommands = ['python3', 'python', 'py'];
    let pythonCmd = 'python3';
    
    // Test rapide de disponibilité Python (optionnel)
    if (options.validatePython !== false) {
      for (const cmd of pythonCommands) {
        try {
          require('child_process').execSync(`${cmd} --version`, { timeout: 5000, stdio: 'ignore' });
          pythonCmd = cmd;
          break;
        } catch {
          continue;
        }
      }
    }

    const timeout = options.timeout || 300000; // 5 min par défaut
    const proc = spawn(pythonCmd, [
      scriptPath,
      '--input',  inputPath,
      '--output', outputPath,
      '--mode',   hcvMode
    ], { 
      timeout,
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, PYTHONUNBUFFERED: '1' }
    });

    let stdout = '', stderr = '';
    let isTimedOut = false;

    // Timeout manuel pour plus de contrôle
    const timeoutId = setTimeout(() => {
      isTimedOut = true;
      proc.kill('SIGTERM');
      setTimeout(() => proc.kill('SIGKILL'), 5000); // Force kill après 5s
    }, timeout);

    proc.stdout.on('data', d => { 
      stdout += d.toString(); 
      // Log progressif pour debug (optionnel)
      if (options.verbose) console.log('HCV stdout:', d.toString().trim());
    });
    
    proc.stderr.on('data', d => { 
      stderr += d.toString();
      if (options.verbose) console.error('HCV stderr:', d.toString().trim());
    });

    proc.on('close', (code, signal) => {
      clearTimeout(timeoutId);
      
      if (isTimedOut) {
        return reject(new Error(`Timeout HCV engine (${timeout}ms). Fichier trop volumineux ou système surchargé.`));
      }
      
      if (signal) {
        return reject(new Error(`HCV engine tué par signal ${signal}`));
      }
      
      if (code !== 0) {
        const errorMsg = stderr.slice(0, 1000) || `Exit code ${code}`;
        return reject(new Error(`HCV engine échoué (code ${code}): ${errorMsg}`));
      }

      // Validation du fichier de sortie
      if (!fs.existsSync(outputPath)) {
        return reject(new Error(`Fichier de sortie non créé: ${outputPath}`));
      }

      try {
        const result = JSON.parse(stdout.trim());
        
        // Validation du résultat
        if (!result.ok) {
          return reject(new Error(`HCV engine erreur: ${result.error || 'Erreur inconnue'}`));
        }
        
        // Ajout des métadonnées
        result.outputPath = outputPath;
        result.id = outputId;
        result.inputSize = fs.statSync(inputPath).size;
        result.outputSize = fs.statSync(outputPath).size;
        result.actualRatio = result.inputSize / result.outputSize;
        
        resolve(result);
      } catch (parseError) {
        reject(new Error(`Réponse moteur invalide: ${parseError.message}. Stdout: ${stdout.slice(0, 500)}`));
      }
    });

    proc.on('error', (err) => {
      clearTimeout(timeoutId);
      if (err.code === 'ENOENT') {
        reject(new Error(`Python non trouvé. Installez Python 3 et ajoutez-le au PATH. Commande testée: ${pythonCmd}`));
      } else {
        reject(new Error(`Erreur spawn HCV engine: ${err.message}`));
      }
    });
  });
}

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

    let mode = 'sdi';
    let fileReceived = false;
    let uploadError = null;
    let tmpPath = null;
    let originalName = '';

    bb.on('field', (name, val) => {
      if (name === 'mode' && ['fast', 'sdi', 'arch'].includes(val)) mode = val;
    });

    bb.on('file', (fieldname, stream, info) => {
      const { filename, mimeType } = info;
      const ext = path.extname(filename).toLowerCase();

      if (!ALLOWED_EXT.has(ext)) {
        stream.resume(); // drain
        uploadError = `Extension non autorisée : ${ext}`;
        return;
      }

      fileReceived = true;
      originalName = filename;
      // Nom temporaire aléatoire pour éviter path traversal
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
      if (!fileReceived || !tmpPath) {
        res.status(400).json({ error: 'Aucun fichier reçu' });
        return resolve();
      }

      try {
        // Lance le moteur HCV côté serveur
        const result = await runHCVEngine(tmpPath, mode);

        // Stocker le chemin de sortie pour le téléchargement (en prod : S3)
        // Ici on garde le fichier en /tmp avec l'ID comme clé
        // Le fichier sera récupéré par /api/download/[id]

        // Nettoyage du fichier source temporaire uniquement
        if (fs.existsSync(tmpPath)) fs.unlinkSync(tmpPath);

        res.status(200).json({
          ok: true,
          jobId: result.id,
          originalFile: originalName,
          mode: result.mode || mode.toUpperCase(),
          ratio: result.ratio,
          psnr: result.psnr,
          fileSize: result.fileSize,
          hasAudio: result.hasAudio,
          downloadUrl: `/api/download/${result.id}`
        });
      } catch (err) {
        if (tmpPath && fs.existsSync(tmpPath)) fs.unlinkSync(tmpPath);
        res.status(500).json({ error: 'Erreur moteur HCV', detail: err.message });
      }
      resolve();
    });

    bb.on('error', (err) => {
      res.status(500).json({ error: 'Erreur parsing upload', detail: err.message });
      resolve();
    });

    req.pipe(bb);
  });
};
