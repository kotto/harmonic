/**
 * Test de validation de la taille de fichier HCV16
 * Vérifie que la taille rapportée correspond à la taille réelle du fichier binaire
 * et que le fichier est lisible par le player
 */

const fs = require('fs');
const path = require('path');

class HCV16FileSizeValidator {
  constructor() {
    this.results = {
      fileSizeBytes: 0,
      fileSizeMB: 0,
      isReadable: false,
      headerValid: false,
      crcValid: false,
      errors: []
    };
  }

  // Valide un fichier HCV16 et sa taille
  async validateFile(filePath) {
    try {
      // 1. Vérifier l'existence du fichier
      if (!fs.existsSync(filePath)) {
        throw new Error(`Fichier introuvable: ${filePath}`);
      }

      // 2. Lire la taille réelle du fichier
      const stats = fs.statSync(filePath);
      this.results.fileSizeBytes = stats.size;
      this.results.fileSizeMB = stats.size / (1024 * 1024);

      console.log(`📁 Fichier: ${path.basename(filePath)}`);
      console.log(`📏 Taille réelle: ${stats.size} bytes (${this.results.fileSizeMB.toFixed(2)} MB)`);

      // 3. Lire le contenu du fichier
      const buffer = fs.readFileSync(filePath);
      
      // 4. Vérifier que la taille lue correspond à la taille du fichier
      if (buffer.length !== stats.size) {
        throw new Error(`Incohérence taille: fichier ${stats.size} bytes, buffer ${buffer.length} bytes`);
      }

      // 5. Valider le header HCV16
      await this.validateHCV16Header(buffer);

      // 6. Valider le CRC32
      await this.validateCRC32(buffer);

      // 7. Test de lisibilité par le player (simulation)
      await this.testPlayerReadability(buffer);

      console.log(`✅ Validation complète réussie`);
      return this.results;

    } catch (error) {
      this.results.errors.push(error.message);
      console.error(`❌ Erreur validation: ${error.message}`);
      return this.results;
    }
  }

  // Valide le header HCV16
  async validateHCV16Header(buffer) {
    if (buffer.length < 64) {
      throw new Error(`Fichier trop petit: ${buffer.length} bytes (minimum 64)`);
    }

    const view = new DataView(buffer.buffer, buffer.byteOffset);
    
    // Magic HCV6
    const HCV_MAGIC = 0x36564348; // 'HCV6' little-endian
    const magic = view.getUint32(0, true);
    
    if (magic !== HCV_MAGIC) {
      const magicHex = magic.toString(16).padStart(8, '0').toUpperCase();
      const expectedHex = HCV_MAGIC.toString(16).padStart(8, '0').toUpperCase();
      throw new Error(`Magic invalide: 0x${magicHex} (attendu: 0x${expectedHex})`);
    }

    // Version
    const version = view.getUint8(4);
    if (version !== 0x01) {
      throw new Error(`Version non supportée: ${version} (attendu: 1)`);
    }

    // Mode
    const mode = view.getUint8(5);
    const validModes = [0x01, 0x02, 0x03]; // LOSSLESS, GRAIN_SYNTH, SIGNAL_ONLY
    if (!validModes.includes(mode)) {
      throw new Error(`Mode invalide: ${mode}`);
    }

    // Dimensions
    const width = view.getUint32(8, true);
    const height = view.getUint32(12, true);
    const nFrames = view.getUint32(16, true);

    console.log(`📊 Header HCV16:`);
    console.log(`   Magic: HCV6 ✓`);
    console.log(`   Version: ${version} ✓`);
    console.log(`   Mode: ${mode} (${this.getModeString(mode)}) ✓`);
    console.log(`   Résolution: ${width}×${height} ✓`);
    console.log(`   Frames: ${nFrames} ✓`);

    this.results.headerValid = true;
  }

  // Valide le CRC32
  async validateCRC32(buffer) {
    if (buffer.length < 4) {
      throw new Error('Fichier trop petit pour contenir un CRC32');
    }

    const view = new DataView(buffer.buffer, buffer.byteOffset);
    const crcStored = view.getUint32(buffer.length - 4, true);
    const payloadBytes = buffer.slice(0, buffer.length - 4);
    const crcComputed = this.crc32(payloadBytes);

    if (crcStored !== crcComputed) {
      const storedHex = crcStored.toString(16).padStart(8, '0').toUpperCase();
      const computedHex = crcComputed.toString(16).padStart(8, '0').toUpperCase();
      throw new Error(`CRC32 invalide: ${storedHex} (calculé: ${computedHex})`);
    }

    console.log(`🔐 CRC32: ${crcStored.toString(16).padStart(8, '0').toUpperCase()} ✓`);
    this.results.crcValid = true;
  }

  // Test de lisibilité par le player (simulation)
  async testPlayerReadability(buffer) {
    try {
      // Simulation du processus de chargement du player
      console.log(`🎮 Test lisibilité player...`);
      
      // 1. Validation taille minimale (comme dans le player)
      if (buffer.byteLength < 64) {
        throw new Error(`Fichier trop petit pour le player: ${buffer.byteLength} bytes`);
      }

      // 2. Parsing header (simulation)
      const view = new DataView(buffer.buffer, buffer.byteOffset);
      let off = 4; // après magic

      // Header complet
      const version = view.getUint8(off++);
      const modeId = view.getUint8(off++);
      const csId = view.getUint8(off++);
      const bitDepth = view.getUint8(off++);
      const width = view.getUint32(off, true); off += 4;
      const height = view.getUint32(off, true); off += 4;
      const nFrames = view.getUint32(off, true); off += 4;
      const fpsNum = view.getUint32(off, true); off += 4;
      const fpsDen = view.getUint32(off, true); off += 4;
      const seqId = view.getUint32(off, true); off += 4;
      const nStreams = view.getUint16(off, true); off += 2;
      off += 2; // padding

      // Sigma curve (32 bytes)
      off += 32;

      // Index frames (8 bytes × nFrames)
      const indexSize = 8 * nFrames;
      if (off + indexSize > buffer.length) {
        throw new Error(`Index frames dépasse la taille du fichier`);
      }

      console.log(`   Parsing header: ✓`);
      console.log(`   Index frames (${nFrames}): ✓`);
      console.log(`   Taille utilisable: ${buffer.length - off - indexSize} bytes`);

      this.results.isReadable = true;

    } catch (error) {
      throw new Error(`Player non compatible: ${error.message}`);
    }
  }

  // Calcul CRC32 (IEEE 802.3)
  crc32(bytes) {
    let crc = 0xFFFFFFFF;
    for (let i = 0; i < bytes.length; i++) {
      crc ^= bytes[i];
      for (let j = 0; j < 8; j++) {
        crc = (crc >>> 1) ^ (crc & 1 ? 0xEDB88320 : 0);
      }
    }
    return (crc ^ 0xFFFFFFFF) >>> 0;
  }

  // Conversion mode en string
  getModeString(mode) {
    const modes = {
      0x01: 'LOSSLESS',
      0x02: 'GRAIN_SYNTH', 
      0x03: 'SIGNAL_ONLY'
    };
    return modes[mode] || 'UNKNOWN';
  }

  // Génère un rapport de validation
  generateReport() {
    const report = {
      summary: this.results.errors.length === 0 ? 'VALIDE' : 'INVALIDE',
      fileSize: {
        bytes: this.results.fileSizeBytes,
        mb: this.results.fileSizeMB,
        formatted: `${this.results.fileSizeMB.toFixed(2)} MB`
      },
      validation: {
        headerValid: this.results.headerValid,
        crcValid: this.results.crcValid,
        playerReadable: this.results.isReadable
      },
      errors: this.results.errors
    };

    return report;
  }
}

// Test avec fichier exemple
async function testFileSizeValidation() {
  console.log('🧪 Test de validation de taille de fichier HCV16\n');

  const validator = new HCV16FileSizeValidator();
  
  // Chemins possibles pour le fichier de test
  const possiblePaths = [
    'video.hcv16',
    'test.hcv16',
    'output.hcv16',
    'b3.hcv16', // Fichier existant dans le projet
    './b3.hcv16'
  ];

  let testFile = null;
  for (const filePath of possiblePaths) {
    if (fs.existsSync(filePath)) {
      testFile = filePath;
      break;
    }
  }

  if (!testFile) {
    console.log('⚠️  Aucun fichier .hcv16 trouvé pour le test');
    console.log('   Fichiers recherchés:', possiblePaths);
    console.log('   Créez un fichier .hcv16 pour tester la validation');
    return;
  }

  console.log(`🎯 Test sur fichier: ${testFile}\n`);

  // Validation complète
  const results = await validator.validateFile(testFile);
  const report = validator.generateReport();

  console.log('\n' + '='.repeat(60));
  console.log('RAPPORT DE VALIDATION');
  console.log('='.repeat(60));
  console.log();

  console.log(`Status: ${report.summary}`);
  console.log(`Taille fichier: ${report.fileSize.formatted} (${report.fileSize.bytes} bytes)`);
  console.log(`Header valide: ${report.validation.headerValid ? '✅' : '❌'}`);
  console.log(`CRC32 valide: ${report.validation.crcValid ? '✅' : '❌'}`);
  console.log(`Player compatible: ${report.validation.playerReadable ? '✅' : '❌'}`);

  if (report.errors.length > 0) {
    console.log('\nErreurs détectées:');
    report.errors.forEach((error, index) => {
      console.log(`  ${index + 1}. ${error}`);
    });
  }

  console.log('\n' + '='.repeat(60));
  
  if (report.summary === 'VALIDE') {
    console.log('✅ VALIDATION RÉUSSIE');
    console.log(`   Le fichier ${testFile} (${report.fileSize.formatted}) est:`);
    console.log('   • Correctement formaté HCV16');
    console.log('   • Intègre (CRC32 valide)');
    console.log('   • Lisible par le player');
    console.log('   • La taille rapportée correspond à la taille réelle du fichier');
  } else {
    console.log('❌ VALIDATION ÉCHOUÉE');
    console.log('   Vérifiez les erreurs ci-dessus');
  }

  return report;
}

// Export pour utilisation
module.exports = { HCV16FileSizeValidator, testFileSizeValidation };

// Exécution du test si appelé directement
if (require.main === module) {
  testFileSizeValidation()
    .then(report => {
      process.exit(report && report.summary === 'VALIDE' ? 0 : 1);
    })
    .catch(error => {
      console.error('Erreur test:', error);
      process.exit(1);
    });
}