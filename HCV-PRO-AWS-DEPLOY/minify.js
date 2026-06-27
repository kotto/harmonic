#!/usr/bin/env node
/**
 * Script de minification pour HCV PRO
 * Minifie le HTML et extrait le JavaScript
 */

const fs = require('fs');
const path = require('path');

const INPUT_FILE = 'web/templates/hcv_pro.html';
const OUTPUT_FILE = 'web/templates/hcv_pro.min.html';

function minifyHTML(html) {
    // Supprimer les commentaires
    html = html.replace(/<!--[\s\S]*?-->/g, '');
    
    // Minifier les attributs HTML
    html = html.replace(/\s+/g, ' ');
    html = html.replace(/>\s+</g, '><');
    
    // Minifier le JavaScript interne
    html = html.replace(/<script>([\s\S]*?)<\/script>/g, (match, js) => {
        // Minifier le JS (simplifié)
        js = js.replace(/\s+/g, ' ');
        js = js.replace(/;\s*/g, ';');
        return `<script>${js}</script>`;
    });
    
    return html.trim();
}

function extractJavaScript(html) {
    // Extraire tout le JavaScript
    const scriptMatches = html.match(/<script>([\s\S]*?)<\/script>/g);
    if (!scriptMatches) return '';
    
    let combinedJS = '';
    scriptMatches.forEach(script => {
        const content = script.replace(/<script>|<\/script>/g, '');
        combinedJS += content + '\n';
    });
    
    return combinedJS;
}

function main() {
    console.log('Minification HCV PRO...');
    
    // Lire le fichier source
    const inputPath = path.join(__dirname, INPUT_FILE);
    const html = fs.readFileSync(inputPath, 'utf8');
    
    console.log(`Fichier source: ${inputPath}`);
    console.log(`Taille originale: ${(html.length / 1024).toFixed(2)} KB`);
    
    // Minifier
    const minified = minifyHTML(html);
    console.log(`Taille minifiée: ${(minified.length / 1024).toFixed(2)} KB`);
    console.log(`Réduction: ${((1 - minified.length / html.length) * 100).toFixed(1)}%`);
    
    // Écrire le fichier minifié
    const outputPath = path.join(__dirname, OUTPUT_FILE);
    fs.writeFileSync(outputPath, minified, 'utf8');
    console.log(`Fichier minifié: ${outputPath}`);
    
    // Extraire le JavaScript pour fichier externe
    const js = extractJavaScript(html);
    const jsOutputPath = path.join(__dirname, 'web/static/app.js');
    fs.writeFileSync(jsOutputPath, js, 'utf8');
    console.log(`Fichier JS extrait: ${jsOutputPath}`);
    
    console.log('Minification terminée!');
}

main();
