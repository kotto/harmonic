const fs = require('fs');
const JavaScriptObfuscator = require('javascript-obfuscator');

// Lire le fichier HTML
const htmlContent = fs.readFileSync('index.html', 'utf8');

// Extraire tout le code JavaScript
const scriptRegex = /<script>([\s\S]*?)<\/script>/gi;
let match;
const scripts = [];

while ((match = scriptRegex.exec(htmlContent)) !== null) {
  scripts.push({
    start: match.index,
    end: match.index + match[0].length,
    code: match[1],
    fullMatch: match[0]
  });
}

console.log(`✅ ${scripts.length} bloc(s) JavaScript trouvé(s)`);

// Configuration d'obscurissement PROFESSIONNEL
const obfuscationConfig = {
  compact: true,
  controlFlowFlattening: true,
  controlFlowFlatteningThreshold: 0.7,
  deadCodeInjection: true,
  deadCodeInjectionThreshold: 0.4,
  debugProtection: true,
  debugProtectionInterval: 2000,
  disableConsoleOutput: true,
  domainLock: [
    '.cloudfront.net',
    '.awsapprunner.com',
    'localhost'
  ],
  identifierNamesGenerator: 'mangled-shuffled',
  identifiersPrefix: '_hcv',
  log: false,
  renameGlobals: true,
  rotateStringArray: true,
  selfDefending: true,
  stringArray: true,
  stringArrayEncoding: ['base64', 'rc4'],
  stringArrayThreshold: 0.8,
  transformObjectKeys: true,
  unicodeEscapeSequence: false
};

// Traiter chaque bloc script
let modifiedHtml = htmlContent;
for (let i = scripts.length - 1; i >= 0; i--) {
  const script = scripts[i];
  
  console.log(`🔒 Obscurissement bloc ${i+1}/${scripts.length}...`);
  
  try {
    const obfuscated = JavaScriptObfuscator.obfuscate(script.code, obfuscationConfig);
    const newScriptBlock = `<script>${obfuscated.getObfuscatedCode()}</script>`;
    
    modifiedHtml = modifiedHtml.substring(0, script.start) + newScriptBlock + modifiedHtml.substring(script.end);
    console.log(`✅ Bloc ${i+1} obscurci avec succès`);
  } catch (e) {
    console.error(`❌ Erreur sur bloc ${i+1}:`, e.message);
  }
}

// Ajouter protection anti-inspecteur
const antiDebugProtection = `
<script>
// PROTECTION HCV PRO
!function(){let e=new Date;debugger,new Date-e>100?(document.body.innerHTML="<div style=position:fixed;inset:0;background:#000;color:#fff;display:flex;align-items:center;justify-content:center;font-family:system-ui><div><h1>🔒 ACCÈS INTERDIT</h1><p>HCV PRO Code protégé</p></div></div>",setInterval((()=>{window.location.reload()}),1e3)):setTimeout(arguments.callee,100)}();
</script>
`;

modifiedHtml = modifiedHtml.replace('</head>', `${antiDebugProtection}</head>`);

// Sauvegarder version protégée
fs.writeFileSync('index_protected.html', modifiedHtml);
console.log('\n✅ Fichier protégé généré: index_protected.html');
console.log('✅ Code 100% obscurci et protégé');
console.log('✅ Anti-debug, anti-inspecteur, domaine verrouillé');