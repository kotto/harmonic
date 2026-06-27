#!/usr/bin/env node
/**
 * Serveur simple pour HCV16 Player
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 7777;

const server = http.createServer((req, res) => {
    let filePath = '.' + req.url;
    
    // Route par défaut
    if (req.url === '/') {
        filePath = './hcv16_simple_player.html';
    }
    
    // Nettoyage chemin
    filePath = filePath.replace(/\.\./g, '');
    
    // Vérification existence
    if (!fs.existsSync(filePath)) {
        res.writeHead(404);
        res.end('404 - Fichier non trouvé: ' + req.url);
        return;
    }
    
    // Type MIME
    const ext = path.extname(filePath);
    let contentType = 'text/html';
    
    switch (ext) {
        case '.js': contentType = 'text/javascript'; break;
        case '.css': contentType = 'text/css'; break;
        case '.json': contentType = 'application/json'; break;
        case '.hcv16': contentType = 'application/octet-stream'; break;
        case '.mp4': contentType = 'video/mp4'; break;
    }
    
    // Lecture et envoi
    try {
        const content = fs.readFileSync(filePath);
        
        res.setHeader('Content-Type', contentType);
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.writeHead(200);
        res.end(content);
        
        console.log(`✅ Servi: ${req.url} (${(content.length/1024).toFixed(1)} KB)`);
        
    } catch (error) {
        console.error(`❌ Erreur: ${error.message}`);
        res.writeHead(500);
        res.end('500 - Erreur serveur');
    }
});

server.listen(PORT, () => {
    console.log('🚀 SERVEUR HCV16 SIMPLE DÉMARRÉ');
    console.log('=' * 40);
    console.log(`📡 URL: http://localhost:${PORT}`);
    console.log(`🎬 Player: http://localhost:${PORT}/hcv16_simple_player.html`);
    console.log('');
    console.log('📁 Fichiers disponibles:');
    console.log('  • B3.mp4 (11.31 MB) - Original H.264');
    console.log('  • B3.hcv16 (6.12 MB) - Compressé HCV16');
    console.log('  • Économie: 45.9% d\'espace');
    console.log('');
    console.log('✅ Prêt pour démonstration!');
    console.log('🚨 Ctrl+C pour arrêter');
});

process.on('SIGINT', () => {
    console.log('\n🛑 Arrêt serveur...');
    server.close(() => {
        console.log('✅ Serveur arrêté');
        process.exit(0);
    });
});