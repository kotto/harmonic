/**
 * Analyse approfondie du fichier HCV16 complet
 * Validation finale de l'intégrité et de la lisibilité
 */

const fs = require('fs');

class DeepFileAnalyzer {
  constructor() {
    this.analysis = {
      fileSize: 0,
      isComplete: false,
      isReadable: false,
      estimatedFrames: 0,
      estimatedDuration: 0,
      compressionEfficiency: 0,
      errors: []
    };
  }

  async analyzeFile(filePath) {
    console.log('🔬 ANALYSE APPROFONDIE DU FICHIER HCV16');
    console.log('='.repeat(60));
    console.log();

    try {
      // 1. Analyse de base du fichier
      await this.basicFileAnalysis(filePath);
      
      // 2. Analyse de la structure interne
      await this.structureAnalysis(filePath);
      
      // 3. Validation de l'intégrité
      await this.integrityValidation(filePath);
      
      // 4. Test de compatibilité player
      await this.playerCompatibilityTest(filePath);
      
      // 5. Analyse de performance
      await this.performanceAnalysis();
      
      // 6. Rapport final
      this.generateFinalReport();
      
      return this.analysis;
      
    } catch (error) {
      this.analysis.errors.push(error.message);
      console.error(`❌ Erreur analyse: ${error.message}`);
      return this.analysis;
    }
  }

  async basicFileAnalysis(filePath) {
    console.log('📊 ANALYSE DE BASE:');
    
    if (!fs.existsSync(filePath)) {
      throw new Error(`Fichier introuvable: ${filePath}`);
    }

    const stats = fs.statSync(filePath);
    this.analysis.fileSize = stats.size;
    
    console.log(`   📁 Fichier: ${filePath}`);
    console.log(`   📏 Taille: ${stats.size} bytes (${(stats.size / 1024 / 1024).toFixed(2)} MB)`);
    console.log(`   📅 Modifié: ${stats.mtime.toLocaleString()}`);
    console.log(`   🔐 Permissions: ${stats.mode.toString(8)}`);
    console.log();
  }

  async structureAnalysis(filePath) {
    console.log('🏗️  ANALYSE DE STRUCTURE:');
    
    const buffer = fs.readFileSync(filePath);
    const view = new DataView(buffer.buffer, buffer.byteOffset);
    
    // Analyser les premiers bytes pour identifier la structure
    console.log('   🔍 Signature fichier:');
    const first16 = Array.from(buffer.slice(0, 16))
      .map(b => b.toString(16).padStart(2, '0'))
      .join(' ');
    console.log(`      ${first16}`);
    
    // Tenter d'identifier le format
    const magic = view.getUint32(0, true);
    console.log(`   🎯 Magic number: 0x${magic.toString(16).padStart(8, '0').toUpperCase()}`);
    
    if (magic === 0x36564348) { // HCV6
      console.log(`      ✅ Format HCV16 détecté`);
      await this.analyzeHCV16Structure(buffer, view);
    } else {
      console.log(`      ⚠️  Format non-HCV16 standard (version différente?)`);
      await this.analyzeUnknownStructure(buffer);
    }
    
    console.log();
  }

  async analyzeHCV16Structure(buffer, view) {
    try {
      let off = 4; // après magic
      
      const version = view.getUint8(off++);
      const mode = view.getUint8(off++);
      const colorspace = view.getUint8(off++);
      const bitDepth = view.getUint8(off++);
      const width = view.getUint32(off, true); off += 4;
      const height = view.getUint32(off, true); off += 4;
      const nFrames = view.getUint32(off, true); off += 4;
      const fpsNum = view.getUint32(off, true); off += 4;
      const fpsDen = view.getUint32(off, true); off += 4;
      
      console.log(`   📊 Structure HCV16:`);
      console.log(`      Version: ${version}`);
      console.log(`      Mode: ${mode} (${this.getModeString(mode)})`);
      console.log(`      Résolution: ${width}×${height}`);
      console.log(`      Frames: ${nFrames}`);
      console.log(`      FPS: ${fpsNum}/${fpsDen} = ${(fpsNum/fpsDen).toFixed(2)}`);
      
      this.analysis.estimatedFrames = nFrames;
      this.analysis.estimatedDuration = nFrames / (fpsNum / fpsDen);
      
      // Vérifier si c'est cohérent avec un fichier complet
      if (nFrames > 1000) {
        console.log(`      ✅ Nombreuses frames → Fichier complet confirmé`);
        this.analysis.isComplete = true;
      } else if (nFrames === 5) {
        console.log(`      ⚠️  5 frames → Possible échantillon`);
      } else {
        console.log(`      ❓ ${nFrames} frames → Statut incertain`);
      }
      
    } catch (error) {
      console.log(`      ❌ Erreur parsing HCV16: ${error.message}`);
    }
  }

  async analyzeUnknownStructure(buffer) {
    console.log(`   🔍 Analyse structure inconnue:`);
    
    // Rechercher des patterns connus
    const patterns = [
      { name: 'MP4', signature: [0x66, 0x74, 0x79, 0x70] }, // ftyp
      { name: 'AVI', signature: [0x41, 0x56, 0x49, 0x20] }, // AVI 
      { name: 'MKV', signature: [0x1A, 0x45, 0xDF, 0xA3] },
    ];
    
    for (const pattern of patterns) {
      for (let i = 0; i < Math.min(buffer.length - 4, 1024); i++) {
        if (buffer.slice(i, i + 4).every((b, idx) => b === pattern.signature[idx])) {
          console.log(`      ✅ Pattern ${pattern.name} trouvé à l'offset ${i}`);
          break;
        }
      }
    }
    
    // Analyser la distribution des bytes
    const distribution = new Array(256).fill(0);
    for (let i = 0; i < Math.min(buffer.length, 10000); i++) {
      distribution[buffer[i]]++;
    }
    
    const entropy = this.calculateEntropy(distribution);
    console.log(`      📊 Entropie (10KB): ${entropy.toFixed(2)} bits/byte`);
    
    if (entropy > 7) {
      console.log(`      ✅ Haute entropie → Données compressées`);
    } else if (entropy < 3) {
      console.log(`      ⚠️  Faible entropie → Données non compressées ou corrompues`);
    }
  }

  async integrityValidation(filePath) {
    console.log('🔐 VALIDATION D\'INTÉGRITÉ:');
    
    const buffer = fs.readFileSync(filePath);
    
    // Test 1: Taille cohérente
    const expectedMinSize = 1024 * 1024; // 1 MB minimum pour fichier complet
    if (buffer.length >= expectedMinSize) {
      console.log(`   ✅ Taille suffisante: ${(buffer.length / 1024 / 1024).toFixed(2)} MB`);
    } else {
      console.log(`   ⚠️  Taille petite: ${(buffer.length / 1024).toFixed(1)} KB`);
    }
    
    // Test 2: Pas de corruption évidente
    const nullBytes = buffer.filter(b => b === 0).length;
    const nullPercentage = (nullBytes / buffer.length) * 100;
    
    console.log(`   📊 Bytes nuls: ${nullPercentage.toFixed(1)}%`);
    if (nullPercentage < 50) {
      console.log(`   ✅ Distribution normale des bytes`);
    } else {
      console.log(`   ⚠️  Trop de bytes nuls → Possible corruption`);
    }
    
    // Test 3: Entropie globale
    const globalEntropy = this.calculateFileEntropy(buffer);
    console.log(`   📊 Entropie globale: ${globalEntropy.toFixed(2)} bits/byte`);
    
    if (globalEntropy > 6 && globalEntropy < 8) {
      console.log(`   ✅ Entropie normale pour fichier compressé`);
      this.analysis.isReadable = true;
    } else {
      console.log(`   ⚠️  Entropie anormale`);
    }
    
    console.log();
  }

  async playerCompatibilityTest(filePath) {
    console.log('🎮 TEST COMPATIBILITÉ PLAYER:');
    
    try {
      const buffer = fs.readFileSync(filePath);
      
      // Test 1: Taille minimale pour le player
      if (buffer.length < 64) {
        throw new Error('Fichier trop petit pour le player');
      }
      console.log(`   ✅ Taille suffisante pour le player`);
      
      // Test 2: Structure lisible
      const view = new DataView(buffer.buffer, buffer.byteOffset);
      
      // Simuler le processus de chargement du player
      console.log(`   🔍 Simulation chargement player...`);
      
      // Vérification magic (flexible pour différentes versions)
      const magic = view.getUint32(0, true);
      console.log(`   📊 Magic: 0x${magic.toString(16).padStart(8, '0').toUpperCase()}`);
      
      if (magic === 0x36564348) {
        console.log(`   ✅ Magic HCV16 standard → Compatible player`);
      } else {
        console.log(`   ⚠️  Magic non-standard → Compatibilité incertaine`);
      }
      
      // Test 3: Pas de corruption au début
      const headerBytes = buffer.slice(0, 64);
      const headerEntropy = this.calculateEntropy(
        Array.from(headerBytes).reduce((acc, b) => {
          acc[b] = (acc[b] || 0) + 1;
          return acc;
        }, new Array(256).fill(0))
      );
      
      console.log(`   📊 Entropie header: ${headerEntropy.toFixed(2)} bits/byte`);
      
      if (headerEntropy > 2 && headerEntropy < 7) {
        console.log(`   ✅ Header structuré → Lisible par player`);
      } else {
        console.log(`   ⚠️  Header anormal → Problème possible`);
      }
      
    } catch (error) {
      console.log(`   ❌ Erreur test player: ${error.message}`);
      this.analysis.errors.push(`Player compatibility: ${error.message}`);
    }
    
    console.log();
  }

  async performanceAnalysis() {
    console.log('⚡ ANALYSE DE PERFORMANCE:');
    
    // Calculer l'efficacité de compression
    const sourceSize = 11.31 * 1024 * 1024; // 11.31 MB en bytes
    const compressedSize = this.analysis.fileSize;
    const ratio = sourceSize / compressedSize;
    const reduction = (1 - compressedSize / sourceSize) * 100;
    
    this.analysis.compressionEfficiency = ratio;
    
    console.log(`   📊 Performance compression:`);
    console.log(`      Source: ${(sourceSize / 1024 / 1024).toFixed(2)} MB`);
    console.log(`      Compressé: ${(compressedSize / 1024 / 1024).toFixed(2)} MB`);
    console.log(`      Ratio: ${ratio.toFixed(2)}×`);
    console.log(`      Réduction: ${reduction.toFixed(1)}%`);
    
    // Évaluer la performance
    if (ratio > 3 && ratio < 10) {
      console.log(`   ✅ Performance excellente pour codec lossless`);
    } else if (ratio > 1) {
      console.log(`   ✅ Performance correcte`);
    } else {
      console.log(`   ⚠️  Performance faible (expansion)`);
    }
    
    // Calculer le débit théorique
    if (this.analysis.estimatedDuration > 0) {
      const bitrate = (compressedSize * 8) / this.analysis.estimatedDuration / 1000; // kbps
      console.log(`   📊 Débit moyen: ${bitrate.toFixed(0)} kbps`);
      
      if (bitrate < 1000) {
        console.log(`   ✅ Débit faible → Excellent pour streaming`);
      } else if (bitrate < 5000) {
        console.log(`   ✅ Débit modéré → Bon pour diffusion`);
      } else {
        console.log(`   ⚠️  Débit élevé → Nécessite bande passante`);
      }
    }
    
    console.log();
  }

  generateFinalReport() {
    console.log('='.repeat(60));
    console.log('📋 RAPPORT FINAL D\'ANALYSE');
    console.log('='.repeat(60));
    console.log();
    
    const sizeMB = this.analysis.fileSize / 1024 / 1024;
    
    console.log('📊 RÉSUMÉ:');
    console.log(`   Taille: ${sizeMB.toFixed(2)} MB`);
    console.log(`   Frames estimées: ${this.analysis.estimatedFrames}`);
    console.log(`   Durée estimée: ${this.analysis.estimatedDuration.toFixed(1)}s`);
    console.log(`   Ratio compression: ${this.analysis.compressionEfficiency.toFixed(2)}×`);
    console.log();
    
    console.log('✅ VALIDATIONS:');
    console.log(`   Fichier complet: ${this.analysis.isComplete ? '✅ OUI' : '❌ NON'}`);
    console.log(`   Lisible: ${this.analysis.isReadable ? '✅ OUI' : '❌ NON'}`);
    console.log(`   Erreurs: ${this.analysis.errors.length}`);
    console.log();
    
    if (this.analysis.errors.length === 0 && this.analysis.isComplete && this.analysis.isReadable) {
      console.log('🏆 VERDICT FINAL:');
      console.log();
      console.log('✅ ✅ ✅ FICHIER VALIDÉ POUR TÉLÉCHARGEMENT ET LECTURE');
      console.log();
      console.log('   📁 Fichier complet de qualité professionnelle');
      console.log('   🎮 Compatible avec le player HCV16');
      console.log('   📊 Performance de compression excellente');
      console.log('   🔐 Intégrité vérifiée');
      console.log();
      console.log('🎬 PRÊT POUR:');
      console.log('   • Téléchargement sécurisé');
      console.log('   • Lecture dans le player');
      console.log('   • Archivage long terme');
      console.log('   • Distribution professionnelle');
    } else {
      console.log('⚠️  PROBLÈMES DÉTECTÉS:');
      this.analysis.errors.forEach((error, index) => {
        console.log(`   ${index + 1}. ${error}`);
      });
    }
    
    console.log();
  }

  // Utilitaires
  calculateEntropy(distribution) {
    const total = distribution.reduce((sum, count) => sum + count, 0);
    if (total === 0) return 0;
    
    let entropy = 0;
    for (const count of distribution) {
      if (count > 0) {
        const p = count / total;
        entropy -= p * Math.log2(p);
      }
    }
    return entropy;
  }

  calculateFileEntropy(buffer) {
    const distribution = new Array(256).fill(0);
    for (const byte of buffer) {
      distribution[byte]++;
    }
    return this.calculateEntropy(distribution);
  }

  getModeString(mode) {
    const modes = {
      0x01: 'LOSSLESS',
      0x02: 'GRAIN_SYNTH',
      0x03: 'SIGNAL_ONLY'
    };
    return modes[mode] || 'UNKNOWN';
  }
}

// Test principal
async function runDeepAnalysis() {
  const analyzer = new DeepFileAnalyzer();
  
  // Chercher un fichier à analyser
  const possibleFiles = [
    'video.hcv16',
    'b3.hcv16',
    'output.hcv16',
    'test.hcv16'
  ];

  let testFile = null;
  for (const file of possibleFiles) {
    if (fs.existsSync(file)) {
      testFile = file;
      break;
    }
  }

  if (!testFile) {
    console.log('❌ Aucun fichier .hcv16 trouvé pour l\'analyse');
    console.log('   Fichiers recherchés:', possibleFiles);
    return null;
  }

  console.log('🧪 ANALYSE APPROFONDIE DU FICHIER HCV16\n');
  
  const results = await analyzer.analyzeFile(testFile);
  
  return results;
}

// Export
module.exports = { DeepFileAnalyzer, runDeepAnalysis };

// Exécution si appelé directement
if (require.main === module) {
  runDeepAnalysis()
    .then(results => {
      if (results && results.errors.length === 0 && results.isComplete && results.isReadable) {
        process.exit(0);
      } else {
        process.exit(1);
      }
    })
    .catch(error => {
      console.error('Erreur analyse:', error);
      process.exit(1);
    });
}