#!/usr/bin/env node
/**
 * API HCV16 Player - Serveur pour fichiers .hcv16
 * Fournit les endpoints pour le player web
 */

const express = require('express');
const fs = require('fs');
const path = require('path');
const cors = require('cors');

class HCV16PlayerAPI {
    constructor() {
        this.app = express();
        this.port = 3000;
        this.setupMiddleware();
        this.setupRoutes();
    }

    setupMiddleware() {
        this.app.use(cors());
        this.app.use(express.json());
        this.app.use(express.static('.'));
    }

    setupRoutes() {
        // Route principale - Player web
        this.app.get('/', (req, res) => {
            res.sendFile(path.join(__dirname, '..', 'hcv16_web_player.html'));
        });

        // API - Liste des fichiers HCV16
        this.app.get('/api/files', (req, res) => {
            try {
                const files = fs.readdirSync('.')
                    .filter(file => file.endsWith('.hcv16'))
                    .map(file => {
                        const stats = fs.statSync(file);
                        return {
                            name: file,
                            size: stats.size,
                            sizeMB: (stats.size / 1024 / 1024).toFixed(2),
                            modified: stats.mtime
                        };
                    });

                res.json({
                    success: true,
                    files: files
                });
            } catch (error) {
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });

        // API - Informations fichier HCV16
        this.app.get('/api/info/:filename', (req, res) => {
            try {
                const filename = req.params.filename;
                
                if (!filename.endsWith('.hcv16')) {
                    return res.status(400).json({
                        success: false,
                        error: 'Fichier doit être .hcv16'
                    });
                }

                if (!fs.existsSync(filename)) {
                    return res.status(404).json({
                        success: false,
                        error: 'Fichier non trouvé'
                    });
                }

                const fileInfo = this.parseHCV16Info(filename);
                res.json({
                    success: true,
                    info: fileInfo
                });

            } catch (error) {
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });

        // API - Téléchargement fichier HCV16
        this.app.get('/api/download/:filename', (req, res) => {
            try {
                const filename = req.params.filename;
                
                if (!filename.endsWith('.hcv16')) {
                    return res.status(400).json({
                        success: false,
                        error: 'Fichier doit être .hcv16'
                    });
                }

                if (!fs.existsSync(filename)) {
                    return res.status(404).json({
                        success: false,
                        error: 'Fichier non trouvé'
                    });
                }

                res.setHeader('Content-Type', 'application/octet-stream');
                res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
                
                const fileStream = fs.createReadStream(filename);
                fileStream.pipe(res);

            } catch (error) {
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });

        // API - Métadonnées associées
        this.app.get('/api/metadata/:filename', (req, res) => {
            try {
                const filename = req.params.filename;
                const metadataFile = filename.replace('.hcv16', '_metadata.json');
                
                if (fs.existsSync(metadataFile)) {
                    const metadata = JSON.parse(fs.readFileSync(metadataFile, 'utf8'));
                    res.json({
                        success: true,
                        metadata: metadata
                    });
                } else {
                    res.json({
                        success: false,
                        error: 'Métadonnées non trouvées'
                    });
                }

            } catch (error) {
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });

        // API - Streaming partiel (pour gros fichiers)
        this.app.get('/api/stream/:filename', (req, res) => {
            try {
                const filename = req.params.filename;
                
                if (!fs.existsSync(filename)) {
                    return res.status(404).json({
                        success: false,
                        error: 'Fichier non trouvé'
                    });
                }

                const stat = fs.statSync(filename);
                const fileSize = stat.size;
                const range = req.headers.range;

                if (range) {
                    // Streaming partiel
                    const parts = range.replace(/bytes=/, "").split("-");
                    const start = parseInt(parts[0], 10);
                    const end = parts[1] ? parseInt(parts[1], 10) : fileSize - 1;
                    const chunksize = (end - start) + 1;
                    
                    const file = fs.createReadStream(filename, { start, end });
                    
                    res.writeHead(206, {
                        'Content-Range': `bytes ${start}-${end}/${fileSize}`,
                        'Accept-Ranges': 'bytes',
                        'Content-Length': chunksize,
                        'Content-Type': 'application/octet-stream',
                    });
                    
                    file.pipe(res);
                } else {
                    // Fichier complet
                    res.writeHead(200, {
                        'Content-Length': fileSize,
                        'Content-Type': 'application/octet-stream',
                    });
                    
                    fs.createReadStream(filename).pipe(res);
                }

            } catch (error) {
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });

        // Route 404
        this.app.use('*', (req, res) => {
            res.status(404).json({
                success: false,
                error: 'Endpoint non trouvé'
            });
        });
    }

    parseHCV16Info(filename) {
        const fileData = fs.readFileSync(filename);
        let offset = 0;

        // Vérification signature
        const signature = fileData.slice(0, 5).toString();
        if (signature !== 'HCV16') {
            throw new Error('Signature HCV16 invalide');
        }
        offset += 8; // Signature + padding

        // Lecture header
        const headerSize = fileData.readUInt32LE(offset);
        offset += 4;

        const headerJson = fileData.slice(offset, offset + headerSize).toString('utf8');
        const header = JSON.parse(headerJson);

        // Informations fichier
        const stats = fs.statSync(filename);

        return {
            filename: filename,
            fileSize: stats.size,
            fileSizeMB: (stats.size / 1024 / 1024).toFixed(2),
            modified: stats.mtime,
            header: header,
            format: 'HCV16',
            version: header.version || 'N/A',
            resolution: `${header.width || 0}×${header.height || 0}`,
            frames: header.frames || 0,
            fps: header.fps || 0,
            duration: header.duration || 0,
            quality: header.quality || 'N/A',
            mode: header.mode || 'N/A',
            simd_level: header.simd_level || 'N/A'
        };
    }

    start() {
        this.app.listen(this.port, () => {
            console.log('🚀 HCV16 PLAYER API DÉMARRÉE');
            console.log('=' * 40);
            console.log(`📡 Serveur: http://localhost:${this.port}`);
            console.log(`🎬 Player Web: http://localhost:${this.port}`);
            console.log(`📊 API Files: http://localhost:${this.port}/api/files`);
            console.log(`📋 API Info: http://localhost:${this.port}/api/info/B3.hcv16`);
            console.log('');
            console.log('✅ Prêt pour lecture fichiers HCV16!');
        });
    }
}

// Démarrage si exécuté directement
if (require.main === module) {
    const api = new HCV16PlayerAPI();
    api.start();
}

module.exports = HCV16PlayerAPI;