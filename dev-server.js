#!/usr/bin/env node
/**
 * Serveur de développement simple pour HCV16 Web Player
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

class SimpleHCV16Server {
    constructor() {
        this.port = 8080;
        this.mimeTypes = {
            '.html': 'text/html',
            '.js': 'text/javascript',
            '.css': 'text/css',
            '.json': 'application/json',
            '.hcv16': 'application/octet-stream',
            '.mp4': 'video/mp4'
        };
    }

    start() {
        const server = http.createServer((req, res) => {
            this.handleRequest(req, res);
        });

        server.listen(this.port, () => {
            console.log('🚀 HCV16 WEB SERVER DÉMARRÉ');
            console.log('=' * 40);
            console.log(`📡 Serveur: http://localhost:${this.port}`);
            console.log(`🎬 Player: http://localhost:${this.port}/hcv16_web_player.html`);
            console.log(`🚀 Démo: http://localhost:${this.port}/hcv16_library.html`);
            console.log('');
            console.log('✅ Prêt pour test HCV16!');
            console.log('🚨 Ctrl+C pour arrêter');
        });

        // Gestion arrêt propre
        process.on('SIGINT', () => {
            console.log('\n🛑 Arrêt serveur HCV16...');
            server.close(() => {
                console.log('✅ Serveur arrêté');
                process.exit(0);
            });
        });
    }

    handleRequest(req, res) {
        const parsedUrl = url.parse(req.url, true);
        let pathname = parsedUrl.pathname;

        // Route par défaut
        if (pathname === '/') {
            pathname = '/hcv16_library.html';
        }

        // API simple pour fichiers
        if (pathname.startsWith('/api/')) {
            this.handleAPI(req, res, pathname);
            return;
        }

        // Fichiers statiques
        this.serveStaticFile(req, res, pathname);
    }

    handleAPI(req, res, pathname) {
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Content-Type', 'application/json');

        if (pathname === '/api/files') {
            // Liste fichiers HCV16
            const files = [];
            
            if (fs.existsSync('B3.hcv16')) {
                const stats = fs.statSync('B3.hcv16');
                files.push({
                    name: 'B3.hcv16',
                    size: stats.size,
                    sizeMB: (stats.size / 1024 / 1024).toFixed(2)
                });
            }

            res.writeHead(200);
            res.end(JSON.stringify({ success: true, files }));

        } else if (pathname === '/api/info/B3.hcv16') {
            // Informations B3.hcv16
            if (fs.existsSync('B3.hcv16') && fs.existsSync('B3_metadata.json')) {
                const metadata = JSON.parse(fs.readFileSync('B3_metadata.json', 'utf8'));
                res.writeHead(200);
                res.end(JSON.stringify({ success: true, info: metadata }));
            } else {
                res.writeHead(404);
                res.end(JSON.stringify({ success: false, error: 'Fichier non trouvé' }));
            }

        } else {
            res.writeHead(404);
            res.end(JSON.stringify({ success: false, error: 'API non trouvée' }));
        }
    }

    serveStaticFile(req, res, pathname) {
        // Nettoyage chemin
        pathname = pathname.replace(/\.\./g, '');
        const filePath = path.join('.', pathname);

        // Vérification existence
        if (!fs.existsSync(filePath)) {
            res.writeHead(404);
            res.end('404 - Fichier non trouvé');
            return;
        }

        // Type MIME
        const ext = path.extname(filePath);
        const mimeType = this.mimeTypes[ext] || 'application/octet-stream';

        // Lecture et envoi
        try {
            const content = fs.readFileSync(filePath);
            
            res.setHeader('Content-Type', mimeType);
            res.setHeader('Access-Control-Allow-Origin', '*');
            
            // Headers spéciaux pour HCV16
            if (ext === '.hcv16') {
                res.setHeader('Content-Disposition', `attachment; filename="${path.basename(filePath)}"`);
            }
            
            res.writeHead(200);
            res.end(content);
            
            console.log(`📁 Servi: ${pathname} (${(content.length/1024).toFixed(1)} KB)`);
            
        } catch (error) {
            console.error(`❌ Erreur lecture ${pathname}:`, error.message);
            res.writeHead(500);
            res.end('500 - Erreur serveur');
        }
    }
}

// Démarrage
const server = new SimpleHCV16Server();
server.start();