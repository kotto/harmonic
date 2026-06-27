/**
 * Tests de validation des métriques HCV16
 * Vérifie la cohérence mathématique et détecte les incohérences
 */

const assert = require('assert');

class MetricsValidator {
  constructor() {
    this.errors = [];
    this.warnings = [];
  }

  // Valide un ensemble de métriques HCV16
  validateMetrics(metrics) {
    this.errors = [];
    this.warnings = [];

    this._validateSizes(metrics);
    this._validateRatio(metrics);
    this._validateReduction(metrics);
    this._validateBPP(metrics);
    this._validateEntropy(metrics);
    this._validateQuality(metrics);
    this._validateCRC32(metrics);

    return {
      isValid: this.errors.length === 0,
      errors: this.errors,
      warnings: this.warnings,
      correctedMetrics: this._generateCorrectedMetrics(metrics)
    };
  }

  _validateSizes(metrics) {
    const { sourceSize, compressedSize, rawSize } = metrics;

    // Vérifier que les tailles sont cohérentes
    if (sourceSize && rawSize && Math.abs(sourceSize - rawSize) > 0.01) {
      this.errors.push({
        type: 'SIZE_INCONSISTENCY',
        message: `Taille source (${sourceSize} MB) != taille brute (${rawSize} MB)`,
        severity: 'CRITICAL'
      });
    }

    // Vérifier que la taille compressée est positive
    if (!compressedSize || compressedSize <= 0) {
      this.errors.push({
        type: 'INVALID_COMPRESSED_SIZE',
        message: `Taille compressée invalide: ${compressedSize}`,
        severity: 'CRITICAL'
      });
    }
  }

  _validateRatio(metrics) {
    const { sourceSize, compressedSize, ratio } = metrics;

    if (sourceSize && compressedSize) {
      const calculatedRatio = sourceSize / compressedSize;
      const tolerance = 0.1; // 10% de tolérance

      if (Math.abs(calculatedRatio - ratio) > tolerance) {
        this.errors.push({
          type: 'RATIO_MISMATCH',
          message: `Ratio calculé (${calculatedRatio.toFixed(2)}×) != ratio rapporté (${ratio}×)`,
          severity: 'HIGH',
          calculated: calculatedRatio,
          reported: ratio
        });
      }
    }
  }

  _validateReduction(metrics) {
    const { sourceSize, compressedSize, reduction } = metrics;

    if (sourceSize && compressedSize) {
      const calculatedReduction = (1 - compressedSize / sourceSize) * 100;
      const tolerance = 0.5; // 0.5% de tolérance

      if (Math.abs(calculatedReduction - reduction) > tolerance) {
        this.errors.push({
          type: 'REDUCTION_MISMATCH',
          message: `Réduction calculée (${calculatedReduction.toFixed(2)}%) != réduction rapportée (${reduction}%)`,
          severity: 'HIGH',
          calculated: calculatedReduction,
          reported: reduction
        });
      }
    }
  }

  _validateBPP(metrics) {
    const { compressedSize, width, height, frames, bpp } = metrics;

    if (compressedSize && width && height && frames) {
      const totalPixels = width * height * frames;
      const totalBits = compressedSize * 1024 * 8; // KB to bits
      const calculatedBPP = totalBits / totalPixels;
      const tolerance = 0.001;

      if (Math.abs(calculatedBPP - bpp) > tolerance) {
        this.warnings.push({
          type: 'BPP_MISMATCH',
          message: `BPP calculé (${calculatedBPP.toFixed(6)}) != BPP rapporté (${bpp})`,
          severity: 'MEDIUM',
          calculated: calculatedBPP,
          reported: bpp
        });
      }
    }
  }

  _validateEntropy(metrics) {
    const { entropy } = metrics;

    // L'entropie ne peut pas être 0 pour un fichier compressé
    if (entropy === 0) {
      this.errors.push({
        type: 'IMPOSSIBLE_ENTROPY',
        message: 'Entropie = 0 est impossible pour un fichier compressé',
        severity: 'CRITICAL',
        expectedRange: '7.0-8.0 bits/byte'
      });
    }

    // L'entropie doit être dans une plage réaliste
    if (entropy && (entropy < 1 || entropy > 8)) {
      this.warnings.push({
        type: 'ENTROPY_OUT_OF_RANGE',
        message: `Entropie ${entropy} hors plage normale (1-8 bits/byte)`,
        severity: 'MEDIUM'
      });
    }
  }

  _validateQuality(metrics) {
    const { mode, psnr, ssim } = metrics;

    if (mode === 'LOSSLESS') {
      if (psnr !== Infinity && psnr !== 'Infinity') {
        this.errors.push({
          type: 'LOSSLESS_PSNR_ERROR',
          message: `Mode LOSSLESS doit avoir PSNR = ∞, trouvé: ${psnr}`,
          severity: 'HIGH'
        });
      }

      if (ssim !== 1.0) {
        this.errors.push({
          type: 'LOSSLESS_SSIM_ERROR',
          message: `Mode LOSSLESS doit avoir SSIM = 1.0, trouvé: ${ssim}`,
          severity: 'HIGH'
        });
      }
    }
  }

  _validateCRC32(metrics) {
    const { crc32 } = metrics;

    if (crc32) {
      // Vérifier le format hexadécimal 8 caractères
      const crc32Regex = /^[0-9A-Fa-f]{8}$/;
      if (!crc32Regex.test(crc32)) {
        this.errors.push({
          type: 'INVALID_CRC32_FORMAT',
          message: `CRC32 format invalide: ${crc32} (attendu: 8 caractères hex)`,
          severity: 'MEDIUM'
        });
      }
    }
  }

  _generateCorrectedMetrics(metrics) {
    const corrected = { ...metrics };

    // Corriger les incohérences de taille
    if (metrics.sourceSize && metrics.rawSize) {
      // Utiliser la plus grande valeur comme source de vérité
      const actualSource = Math.max(metrics.sourceSize, metrics.rawSize);
      corrected.sourceSize = actualSource;
      delete corrected.rawSize; // Supprimer le champ redondant
    }

    // Recalculer ratio et réduction avec la taille corrigée
    if (corrected.sourceSize && corrected.compressedSize) {
      corrected.ratio = corrected.sourceSize / corrected.compressedSize;
      corrected.reduction = (1 - corrected.compressedSize / corrected.sourceSize) * 100;
    }

    // Corriger l'entropie si elle est 0
    if (corrected.entropy === 0) {
      corrected.entropy = 7.8; // Valeur typique pour données compressées
      corrected.entropyNote = 'Valeur estimée (entropie 0 impossible)';
    }

    return corrected;
  }
}

// Tests unitaires
function runTests() {
  console.log('🧪 Tests de validation des métriques HCV16\n');

  const validator = new MetricsValidator();

  // Test 1: Métriques cohérentes
  console.log('Test 1: Métriques cohérentes');
  const validMetrics = {
    sourceSize: 11, // MB
    compressedSize: 0.049, // MB (49.1 KB)
    ratio: 224.49,
    reduction: 99.56,
    width: 1920,
    height: 1080,
    frames: 5,
    bpp: 0.039,
    entropy: 7.8,
    mode: 'LOSSLESS',
    psnr: Infinity,
    ssim: 1.0,
    crc32: '207055BE'
  };

  const result1 = validator.validateMetrics(validMetrics);
  console.log(`✓ Résultat: ${result1.isValid ? 'VALIDE' : 'INVALIDE'}`);
  if (result1.errors.length > 0) {
    console.log('Erreurs:', result1.errors.map(e => e.message));
  }
  console.log();

  // Test 2: Métriques incohérentes (cas original)
  console.log('Test 2: Métriques incohérentes (problème original)');
  const invalidMetrics = {
    sourceSize: 11, // MB
    rawSize: 29.66, // MB - INCOHÉRENCE
    compressedSize: 0.049, // MB
    ratio: 619.17, // INCORRECT
    reduction: 99.8, // INCORRECT
    width: 1920,
    height: 1080,
    frames: 5,
    bpp: 0.039,
    entropy: 0, // IMPOSSIBLE
    mode: 'LOSSLESS',
    psnr: Infinity,
    ssim: 1.0,
    crc32: '207055BE'
  };

  const result2 = validator.validateMetrics(invalidMetrics);
  console.log(`✓ Résultat: ${result2.isValid ? 'VALIDE' : 'INVALIDE'}`);
  console.log('Erreurs détectées:');
  result2.errors.forEach(error => {
    console.log(`  - ${error.type}: ${error.message}`);
  });
  console.log();

  // Test 3: Métriques corrigées
  console.log('Test 3: Métriques corrigées');
  const corrected = result2.correctedMetrics;
  console.log('Métriques corrigées:');
  console.log(`  Source: ${corrected.sourceSize} MB`);
  console.log(`  Ratio: ${corrected.ratio.toFixed(2)}×`);
  console.log(`  Réduction: ${corrected.reduction.toFixed(2)}%`);
  console.log(`  Entropie: ${corrected.entropy} bits/byte`);
  console.log();

  const result3 = validator.validateMetrics(corrected);
  console.log(`✓ Métriques corrigées: ${result3.isValid ? 'VALIDES' : 'INVALIDES'}`);
  
  return {
    allTestsPassed: result1.isValid && !result2.isValid && result3.isValid,
    results: [result1, result2, result3]
  };
}

// Export pour utilisation dans d'autres modules
module.exports = { MetricsValidator, runTests };

// Exécution des tests si appelé directement
if (require.main === module) {
  const testResults = runTests();
  console.log(`\n🎯 Résumé: ${testResults.allTestsPassed ? 'TOUS LES TESTS PASSENT' : 'CERTAINS TESTS ÉCHOUENT'}`);
  process.exit(testResults.allTestsPassed ? 0 : 1);
}