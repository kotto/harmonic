/**
 * Test de techniques d'optimisation avancées pour HCV16
 */

const fs = require('fs');
const { execSync } = require('child_process');

class CodecBenchmark {
  constructor() {
    this.results = [];
    this.sourceFile = 'B3.mp4';
    this.sourceSize = 11.31; // MB
    this.targetSize = 11.31; // MB (objectif)
  }

  async runAdvancedOptimizations() {
    console.log('🚀 TECHNIQUES D\'OPTIMISATION AVANCÉES');
    console.log('=====================================');
    console.log('');

    // 1. Analyse de la source
    await this.analyzeSource();
    
    // 2. Test de résolutions multiples
    await this.testMultipleResolutions();
    
    // 3. Test de frame rates
    await this.testFrameRates();
    
    // 4. Test de ROI (Region of Interest)
    await this.testROICompression();
    
    // 5. Test de techniques hybrides
    await this.testHybridTechniques();
    
    return this.results;
  }

  async analyzeSource() {
    console.log('🔍 ANALYSE DÉTAILLÉE DE LA SOURCE');
    console.log('----------------------------------');
    
    try {
      // Utilisation de ffprobe pour analyser la vidéo
      const ffprobeCmd = `ffprobe -v quiet -print_format json -show_format -show_streams "${this.sourceFile}"`;
      const output = execSync(ffprobeCmd, { encoding: 'utf8' });
      const info = JSON.parse(output);
      
      const videoStream = info.streams.find(s => s.codec_type === 'video');
      
      if (videoStream) {
        console.log(`📊 Informations source:`);
        console.log(`   Codec: ${videoStream.codec_name}`);
        console.log(`   Résolution: ${videoStream.width}×${videoStream.height}`);
        console.log(`   FPS: ${eval(videoStream.r_frame_rate)?.toFixed(2) || 'N/A'}`);
        console.log(`   Bitrate: ${(videoStream.bit_rate / 1000000)?.toFixed(2) || 'N/A'} Mbps`);
        console.log(`   Durée: ${parseFloat(videoStream.duration)?.toFixed(1) || 'N/A'}s`);
        console.log(`   Frames: ${videoStream.nb_frames || 'N/A'}`);
        
        // Calcul de la densité de données
        const pixelsPerSecond = videoStream.width * videoStream.height * eval(videoStream.r_frame_rate);
        const bitsPerPixel = videoStream.bit_rate / pixelsPerSecond;
        console.log(`   Bits/pixel: ${bitsPerPixel?.toFixed(4) || 'N/A'}`);
        
        // Recommandations basées sur l'analyse
        console.log('');
        console.log('💡 RECOMMANDATIONS:');
        
        if (videoStream.width * videoStream.height > 500000) {
          console.log('   ⚠️  Résolution élevée → Considérer downscaling');
        }
        
        if (eval(videoStream.r_frame_rate) > 30) {
          console.log('   ⚠️  FPS élevé → Considérer réduction frame rate');
        }
        
        if (bitsPerPixel < 0.1) {
          console.log('   ✅ Source déjà très compressée → Défi technique élevé');
        }
      }
      
    } catch (error) {
      console.log('   ⚠️  Analyse ffprobe échouée, utilisation des données connues');
      console.log(`   Résolution: 478×850 (vertical)`);
      console.log(`   Taille: ${this.sourceSize} MB`);
    }
  }

  async testMultipleResolutions() {
    console.log('\n📐 TEST RÉSOLUTIONS MULTIPLES');
    console.log('------------------------------');
    
    const resolutions = [
      { name: '100% (478×850)', scale: 1.0, width: 478, height: 850 },
      { name: '75% (358×637)', scale: 0.75, width: 358, height: 637 },
      { name: '50% (239×425)', scale: 0.5, width: 239, height: 425 },
      { name: '25% (119×212)', scale: 0.25, width: 119, height: 212 }
    ];
    
    console.log('🧪 Estimation impact résolution sur taille HCV16:');
    console.log('');
    
    const baselineSize = 578.4; // MB (de nos tests précédents)
    
    resolutions.forEach(res => {
      // Estimation basée sur le nombre de pixels
      const pixelRatio = res.scale * res.scale;
      const estimatedSize = baselineSize * pixelRatio;
      const success = estimatedSize < this.targetSize;
      
      console.log(`   ${res.name}:`);
      console.log(`     Pixels: ${(pixelRatio * 100).toFixed(1)}% de l'original`);
      console.log(`     Taille estimée: ${estimatedSize.toFixed(1)} MB`);
      console.log(`     Objectif atteint: ${success ? '✅' : '❌'}`);
      console.log('');
      
      this.results.push({
        technique: `Résolution ${res.name}`,
        estimatedSize: estimatedSize,
        success: success,
        tradeoff: `Qualité visuelle ${res.scale < 1 ? 'réduite' : 'originale'}`
      });
    });
  }

  async testFrameRates() {
    console.log('🎬 TEST RÉDUCTION FRAME RATE');
    console.log('-----------------------------');
    
    const frameRates = [
      { name: '30 fps (original)', ratio: 1.0 },
      { name: '25 fps (-17%)', ratio: 25/30 },
      { name: '20 fps (-33%)', ratio: 20/30 },
      { name: '15 fps (-50%)', ratio: 15/30 },
      { name: '12 fps (-60%)', ratio: 12/30 }
    ];
    
    console.log('🧪 Estimation impact frame rate sur taille:');
    console.log('');
    
    const baselineSize = 578.4; // MB
    
    frameRates.forEach(fr => {
      const estimatedSize = baselineSize * fr.ratio;
      const success = estimatedSize < this.targetSize;
      
      console.log(`   ${fr.name}:`);
      console.log(`     Frames: ${(fr.ratio * 100).toFixed(1)}% de l'original`);
      console.log(`     Taille estimée: ${estimatedSize.toFixed(1)} MB`);
      console.log(`     Objectif atteint: ${success ? '✅' : '❌'}`);
      console.log(`     Fluidité: ${fr.ratio >= 0.8 ? 'Excellente' : fr.ratio >= 0.6 ? 'Bonne' : 'Réduite'}`);
      console.log('');
      
      this.results.push({
        technique: `Frame rate ${fr.name}`,
        estimatedSize: estimatedSize,
        success: success,
        tradeoff: `Fluidité ${fr.ratio < 1 ? 'réduite' : 'originale'}`
      });
    });
  }

  async testROICompression() {
    console.log('🎯 TEST COMPRESSION ROI (REGION OF INTEREST)');
    console.log('---------------------------------------------');
    
    console.log('💡 Concept: Compression différentielle par zones');
    console.log('   • Zones importantes: Qualité maximale');
    console.log('   • Zones secondaires: Compression agressive');
    console.log('');
    
    const roiStrategies = [
      {
        name: 'ROI Centre (50% haute qualité)',
        centerQuality: 1.0,
        edgeQuality: 0.3,
        estimatedReduction: 0.4
      },
      {
        name: 'ROI Adaptatif (détection mouvement)',
        centerQuality: 1.0,
        edgeQuality: 0.2,
        estimatedReduction: 0.5
      },
      {
        name: 'ROI Agressif (25% haute qualité)',
        centerQuality: 1.0,
        edgeQuality: 0.1,
        estimatedReduction: 0.7
      }
    ];
    
    const baselineSize = 578.4; // MB
    
    roiStrategies.forEach(roi => {
      const estimatedSize = baselineSize * roi.estimatedReduction;
      const success = estimatedSize < this.targetSize;
      
      console.log(`🧪 ${roi.name}:`);
      console.log(`   Réduction estimée: ${((1 - roi.estimatedReduction) * 100).toFixed(0)}%`);
      console.log(`   Taille estimée: ${estimatedSize.toFixed(1)} MB`);
      console.log(`   Objectif atteint: ${success ? '✅' : '❌'}`);
      console.log(`   Qualité centre: ${(roi.centerQuality * 100).toFixed(0)}%`);
      console.log(`   Qualité bords: ${(roi.edgeQuality * 100).toFixed(0)}%`);
      console.log('');
      
      this.results.push({
        technique: roi.name,
        estimatedSize: estimatedSize,
        success: success,
        tradeoff: `Qualité non-uniforme (centre ${(roi.centerQuality * 100).toFixed(0)}%, bords ${(roi.edgeQuality * 100).toFixed(0)}%)`
      });
    });
  }

  async testHybridTechniques() {
    console.log('🔬 TEST TECHNIQUES HYBRIDES');
    console.log('----------------------------');
    
    const hybridApproaches = [
      {
        name: 'Résolution 75% + Frame rate 25fps',
        pixelReduction: 0.75 * 0.75,
        frameReduction: 25/30,
        qualityImpact: 'Modéré'
      },
      {
        name: 'Résolution 50% + Frame rate 20fps',
        pixelReduction: 0.5 * 0.5,
        frameReduction: 20/30,
        qualityImpact: 'Significatif'
      },
      {
        name: 'ROI Centre + Résolution 75%',
        pixelReduction: 0.75 * 0.75,
        frameReduction: 1.0,
        roiReduction: 0.6,
        qualityImpact: 'Modéré (non-uniforme)'
      },
      {
        name: 'Triple optimisation (Res 50% + FPS 15 + ROI)',
        pixelReduction: 0.5 * 0.5,
        frameReduction: 15/30,
        roiReduction: 0.4,
        qualityImpact: 'Élevé'
      }
    ];
    
    const baselineSize = 578.4; // MB
    
    console.log('🧪 Combinaisons d\'optimisations:');
    console.log('');
    
    hybridApproaches.forEach(hybrid => {
      let estimatedSize = baselineSize;
      
      // Application des réductions
      estimatedSize *= hybrid.pixelReduction;
      estimatedSize *= hybrid.frameReduction;
      if (hybrid.roiReduction) {
        estimatedSize *= hybrid.roiReduction;
      }
      
      const success = estimatedSize < this.targetSize;
      const totalReduction = ((baselineSize - estimatedSize) / baselineSize * 100);
      
      console.log(`   ${hybrid.name}:`);
      console.log(`     Réduction totale: ${totalReduction.toFixed(1)}%`);
      console.log(`     Taille estimée: ${estimatedSize.toFixed(1)} MB`);
      console.log(`     Objectif atteint: ${success ? '✅' : '❌'}`);
      console.log(`     Impact qualité: ${hybrid.qualityImpact}`);
      console.log('');
      
      this.results.push({
        technique: hybrid.name,
        estimatedSize: estimatedSize,
        success: success,
        tradeoff: `Impact qualité: ${hybrid.qualityImpact}`
      });
    });
  }

  generateSummary() {
    console.log('📊 RÉSUMÉ TOUTES TECHNIQUES');
    console.log('============================');
    
    const successfulTechniques = this.results.filter(r => r.success);
    
    if (successfulTechniques.length > 0) {
      console.log('✅ TECHNIQUES ATTEIGNANT L\'OBJECTIF < 11.31 MB:');
      console.log('');
      
      successfulTechniques
        .sort((a, b) => a.estimatedSize - b.estimatedSize)
        .forEach((tech, index) => {
          console.log(`${index + 1}. ${tech.technique}`);
          console.log(`   Taille: ${tech.estimatedSize.toFixed(1)} MB`);
          console.log(`   Économie: ${(this.sourceSize - tech.estimatedSize).toFixed(1)} MB`);
          console.log(`   Compromis: ${tech.tradeoff}`);
          console.log('');
        });
      
      const best = successfulTechniques[0];
      console.log('🏆 RECOMMANDATION OPTIMALE:');
      console.log(`   Technique: ${best.technique}`);
      console.log(`   Taille finale: ${best.estimatedSize.toFixed(1)} MB`);
      console.log(`   Économie: ${(this.sourceSize - best.estimatedSize).toFixed(1)} MB`);
      console.log(`   Compromis: ${best.tradeoff}`);
      
    } else {
      console.log('❌ AUCUNE TECHNIQUE N\'ATTEINT L\'OBJECTIF < 11.31 MB');
      console.log('');
      console.log('💡 MEILLEURES TENTATIVES:');
      
      this.results
        .sort((a, b) => a.estimatedSize - b.estimatedSize)
        .slice(0, 3)
        .forEach((tech, index) => {
          console.log(`${index + 1}. ${tech.technique}: ${tech.estimatedSize.toFixed(1)} MB`);
        });
    }
  }
}

// Exécution
async function runBenchmark() {
  const benchmark = new CodecBenchmark();
  
  try {
    await benchmark.runAdvancedOptimizations();
    benchmark.generateSummary();
    
  } catch (error) {
    console.error('❌ Erreur benchmark:', error.message);
  }
}

// Export pour utilisation en module
module.exports = { CodecBenchmark };

// Exécution si appelé directement
if (require.main === module) {
  runBenchmark();
}