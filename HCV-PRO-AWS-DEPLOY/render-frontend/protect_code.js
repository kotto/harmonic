const fs = require('fs');
const JavaScriptObfuscator = require('javascript-obfuscator');

console.log('🔒 Protection du code HCV PRO Frontend...');

// Lire le fichier index.html
const htmlContent = fs.readFileSync('index.html', 'utf8');

// Extraire tout le code JavaScript
const scriptStart = htmlContent.indexOf('<script>');
const scriptEnd = htmlContent.lastIndexOf('</script>');

if (scriptStart === -1 || scriptEnd === -1) {
    console.error('❌ Balises script non trouvées');
    process.exit(1);
}

const jsCode = htmlContent.substring(scriptStart + 8, scriptEnd);

console.log('✅ Code JavaScript extrait:', jsCode.length, 'caractères');

// Appliquer obscurissement professionnel
const obfuscationResult = JavaScriptObfuscator.obfuscate(jsCode, {
    compact: true,
    controlFlowFlattening: true,
    controlFlowFlatteningThreshold: 0.75,
    deadCodeInjection: true,
    deadCodeInjectionThreshold: 0.4,
    debugProtection: true,
    debugProtectionInterval: 2000,
    disableConsoleOutput: true,
    identifierNamesGenerator: 'hexadecimal',
    log: false,
    renameGlobals: false,
    rotateStringArray: true,
    selfDefending: true,
    stringArray: true,
    stringArrayEncoding: ['base64'],
    stringArrayThreshold: 0.8,
    transformObjectKeys: true,
    unicodeEscapeSequence: false
});

const protectedCode = obfuscationResult.getObfuscatedCode();

console.log('✅ Code obscurci généré:', protectedCode.length, 'caractères');

// Reconstruire le fichier HTML
const newHtmlContent = 
    htmlContent.substring(0, scriptStart + 8) + 
    '\n' + protectedCode + '\n' +
    htmlContent.substring(scriptEnd);

// Sauvegarder version originale
fs.writeFileSync('index.html.original', htmlContent);
console.log('✅ Version originale sauvegardée: index.html.original');

// Écrire nouveau fichier protégé
fs.writeFileSync('index.html', newHtmlContent);

console.log('\n🎉 Protection terminée avec succès!');
console.log('✅ Toutes les fonctionnalités sont conservées');
console.log('✅ Anti-debug activé');
console.log('✅ Console désactivée');
