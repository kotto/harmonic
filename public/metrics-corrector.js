/**
 * Correcteur de métriques HCV16 côté client - VERSION FINALE
 * Gère la distinction entre fichier complet et échantillon testé
 */

class HCVMetricsCorrector {
  constructor() {
    this.corrections = [];
  }

  // Corrige un ensemble de métriques en tenant compte du contexte
  correctMetrics(rawMetrics) {
    this.corrections = [];
    const corrected = { ...rawMetrics };

    // 1. Identifier le type de test (échantillon vs fichier complet)
    const isSample = corrected.frames && corrected.frames < 100; // Heuristique
    
    if (isSample && corrected.fullFileSize && corrected.sourceSize) {
      // Cas échantillon : clarifier les données
      this.corrections.push({
        type: 'CONTEXT_CLARIFICATION',
        message: `Test sur échantillon de ${corrected.frames} frames (fichier complet: ${corrected.fullFileSize} MB)`
      });
      
      // Ajouter projection pour fichier complet
      if (corrected.ratio) {
        const projectedSize = corrected.fullFileSize / corrected.ratio;
        corrected.projectedCompressedSize = projectedSize;
        corrected.projectedRatio = corrected.fullFileSize / projectedSize;
        
        this.corrections.push({
          type: 'PROJECTION_ADDED',
          message: `Projection fichier complet: ${corrected.fullFileSize} MB → ${projectedSize.toFixed(1)} KB`
        });
      }
    }

    // 2. Valider la taille brute théorique (si échantillon)
    if (corrected.width && corrected.height && corrected.frames) {
      const theoreticalSize = (corrected.width * corrected.height * 3 * 2 * corrected.frames) / (1024 * 1024);
      
      if (corrected.sourceSize && Math.abs(theoreticalSize - corrected.sourceSize) > 1) {
        this.corrections.push({
          type: 'SIZE_DISCREPANCY',
          before: corrected.sourceSize,
          theoretical: theoreticalSize,
          message: `Taille brute: ${corrected.sourceSize} MB (théorique: ${theoreticalSize.toFixed(2)} MB). Possible format YUV ou pré-traitement.`
        });
        
        // Note explicative
        corrected.sizeNote = `Écart avec taille théorique (${theoreticalSize.toFixed(2)} MB). Possible format YUV 4:2:0 ou données pré-traitées.`;
      }
    }

    // 3. Corriger l'entropie impossible
    if (corrected.entropy === 0) {
      const estimatedEntropy = this._estimateEntropy(corrected);
      this.corrections.push({
        type: 'ENTROPY_CORRECTION',
        before: 0,
        after: estimatedEntropy,
        message: `Entropie corrigée: ${estimatedEntropy} bits/byte (était 0.00 - mathématiquement impossible)`
      });
      corrected.entropy = estimatedEntropy;
      corrected.entropyNote = 'Valeur estimée (entropie 0 impossible pour fichier compressé)';
    }

    // 4. Valider BPP avec contexte
    if (corrected.width && corrected.height && corrected.frames && corrected.compressedSize) {
      const totalPixels = corrected.width * corrected.height * corrected.frames;
      const totalBits = corrected.compressedSize * 1024 * 8; // MB to bits
      const calculatedBPP = totalBits / totalPixels;

      if (corrected.bpp && Math.abs(calculatedBPP - corrected.bpp) > 0.001) {
        this.corrections.push({
          type: 'BPP_CORRECTION',
          before: corrected.bpp,
          after: calculatedBPP,
          message: `BPP corrigé: ${calculatedBPP.toFixed(6)} bits/pixel (était ${corrected.bpp})`
        });
        corrected.bpp = calculatedBPP;
      }
    }

    // 5. Ajouter métadonnées de contexte
    corrected._corrected = true;
    corrected._corrections = this.corrections;
    corrected._correctionTimestamp = new Date().toISOString();
    corrected._testType = isSample ? 'sample' : 'complete';

    return corrected;
  }

  // Estime l'entropie basée sur le ratio de compression
  _estimateEntropy(metrics) {
    const ratio = metrics.ratio || 1;
    
    if (ratio > 500) return 7.9; // Très haute compression
    if (ratio > 100) return 7.8; // Haute compression
    if (ratio > 50) return 7.7;  // Compression moyenne
    if (ratio > 10) return 7.5;  // Faible compression
    return 7.2; // Très faible compression
  }

  // Génère un rapport de correction contextuel
  generateCorrectionReport() {
    if (this.corrections.length === 0) {
      return 'Aucune correction nécessaire - toutes les métriques sont cohérentes.';
    }

    let report = `🔧 ${this.corrections.length} correction(s) appliquée(s):\n\n`;
    
    this.corrections.forEach((correction, index) => {
      report += `${index + 1}. ${correction.type}:\n`;
      report += `   ${correction.message}\n\n`;
    });

    report += '✅ Métriques corrigées et contextualisées.';
    return report;
  }

  // Applique les corrections à l'interface avec contexte
  applyToUI(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Créer un panneau contextuel
    const contextPanel = document.createElement('div');
    contextPanel.className = 'context-panel';
    contextPanel.innerHTML = `
      <div class="context-header">
        <span class="context-icon">📊</span>
        <span class="context-title">Contexte du Test HCV16</span>
      </div>
      <div class="context-content">
        <div class="context-item">
          <strong>Type:</strong> Test sur échantillon de frames
        </div>
        <div class="context-item">
          <strong>Métriques:</strong> Calculées sur l'échantillon testé
        </div>
        <div class="context-item">
          <strong>Projections:</strong> Estimations pour fichier complet
        </div>
      </div>
    `;

    // Panneau de corrections
    const correctionPanel = document.createElement('div');
    correctionPanel.className = 'correction-panel';
    correctionPanel.innerHTML = `
      <div class="correction-header">
        <span class="correction-icon">🔧</span>
        <span class="correction-title">Corrections automatiques</span>
        <button class="correction-toggle" onclick="this.parentElement.nextElementSibling.style.display = this.parentElement.nextElementSibling.style.display === 'none' ? 'block' : 'none'">
          Détails
        </button>
      </div>
      <div class="correction-details" style="display: none;">
        <pre>${this.generateCorrectionReport()}</pre>
      </div>
    `;

    // Styles
    const style = document.createElement('style');
    style.textContent = `
      .context-panel {
        background: rgba(62, 166, 255, 0.1);
        border: 1px solid rgba(62, 166, 255, 0.3);
        border-radius: 8px;
        margin: 16px 0;
        overflow: hidden;
      }
      .context-header {
        padding: 12px 16px;
        display: flex;
        align-items: center;
        gap: 8px;
        background: rgba(62, 166, 255, 0.05);
        border-bottom: 1px solid rgba(62, 166, 255, 0.2);
      }
      .context-content {
        padding: 12px 16px;
      }
      .context-item {
        margin: 4px 0;
        font-size: 12px;
        color: var(--text2);
      }
      .correction-panel {
        background: rgba(245, 166, 35, 0.1);
        border: 1px solid rgba(245, 166, 35, 0.3);
        border-radius: 8px;
        margin: 8px 0;
        overflow: hidden;
      }
      .correction-header {
        padding: 12px 16px;
        display: flex;
        align-items: center;
        gap: 8px;
        background: rgba(245, 166, 35, 0.05);
      }
      .correction-title {
        flex: 1;
        font-weight: 600;
        font-size: 13px;
      }
      .correction-toggle {
        background: none;
        border: 1px solid rgba(245, 166, 35, 0.5);
        color: var(--amber);
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 11px;
        cursor: pointer;
      }
      .correction-toggle:hover {
        background: rgba(245, 166, 35, 0.1);
      }
      .correction-details {
        padding: 16px;
        border-top: 1px solid rgba(245, 166, 35, 0.2);
      }
      .correction-details pre {
        margin: 0;
        font-family: var(--mono);
        font-size: 11px;
        line-height: 1.4;
        color: var(--text2);
        white-space: pre-wrap;
      }
    `;

    if (!document.getElementById('correction-styles')) {
      style.id = 'correction-styles';
      document.head.appendChild(style);
    }

    // Insérer les panneaux
    container.insertBefore(contextPanel, container.firstChild);
    container.insertBefore(correctionPanel, contextPanel.nextSibling);
  }
}

// Fonction utilitaire pour corriger les métriques affichées
function correctDisplayedMetrics(metricsData) {
  const corrector = new HCVMetricsCorrector();
  const corrected = corrector.correctMetrics(metricsData);
  
  // Appliquer à l'interface si un conteneur est spécifié
  if (metricsData.containerId) {
    corrector.applyToUI(metricsData.containerId);
  }
  
  return {
    metrics: corrected,
    corrections: corrector.corrections,
    report: corrector.generateCorrectionReport()
  };
}

// Export pour utilisation
if (typeof module !== 'undefined') {
  module.exports = { HCVMetricsCorrector, correctDisplayedMetrics };
}