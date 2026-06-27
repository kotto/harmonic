/**
 * 
 * ANALYSE PROFONDE DES RÉSULTATS DE COMPRESSION
 * Vérification détaillée de l'intégrité et de la cohérence
 * 
 */

const fs = require('fs');
const path = require('path');

class DeepAnalysis {
    constructor() {
        this.videoPath = path.resolve(__dirname, '..', '..', 'B3.mp4');
        this.metadataPath = path.resolve(__dirname, '..', '..', 'B3_metadata.json');
        this.results = {
            fileAnalysis: null,
            metadataAnalysis: null,
            compressionAnalysis: null,
            integrityCheck: null,
            conclusion: null
        };
    }

    async runDeepAnalysis() {
        console.log('ANALYSE PROFONDE DES RÉSULTATS');
        console.log('='.repeat(60));
        
        try {
            // Étape 1: Analyse du fichier original
            await this.analyzeOriginalFile();
            
            // Étape 2: Analyse des métadonnées existantes
            await this.analyzeExistingMetadata();
            
            // Étape 3: Analyse de notre compression
            await this.analyzeOurCompression();
            
            // Étape 4: Vérification d'intégrité
            await this.verifyIntegrity();
            
            // Étape 5: Conclusion
            await this.generateConclusion();
            
        } catch (error) {
            console.error('Erreur dans l\'analyse profonde:', error);
            this.results.conclusion = {
                success: false,
                error: error.message
            };
        }
        
        return this.results;
    }

    async analyzeOriginalFile() {
        console.log('1. Analyse du fichier original B3.mp4...');
        
        const stats = fs.statSync(this.videoPath);
        const buffer = fs.readFileSync(this.videoPath, { start: 0, end: 1024 });
        
        // Analyse de l'en-tête MP4
        const header = buffer.slice(0, 16);
        const isMP4 = header[4] === 0x66 && header[5] === 0x74 && 
                      header[6] === 0x79 && header[7] === 0x70; // 'ftyp'
        
        // Recherche de la durée réelle dans le fichier MP4
        const duration = this.extractDurationFromMP4(fs.readFileSync(this.videoPath));
        
        this.results.fileAnalysis = {
            path: this.videoPath,
            size: stats.size,
            sizeFormatted: this.formatFileSize(stats.size),
            lastModified: stats.mtime,
            fileType: isMP4 ? 'MP4' : 'Unknown',
            header: header.map(b => b.toString(16).padStart(2, '0')).join(' '),
            estimatedDuration: duration,
            estimatedFrames: duration ? Math.floor(duration * 30) : null
        };
        
        console.log(`  Taille: ${this.results.fileAnalysis.sizeFormatted}`);
        console.log(`  Type: ${this.results.fileAnalysis.fileType}`);
        console.log(`  Durée estimée: ${this.results.fileAnalysis.estimatedDuration}s`);
        console.log(`  Trames estimées: ${this.results.fileAnalysis.estimatedFrames}`);
    }

    extractDurationFromMP4(buffer) {
        // Recherche simplifiée de la durée dans un fichier MP4
        // Dans une vraie implémentation, il faudrait parser le conteneur MP4
        
        // Recherche de 'mvhd' (movie header)
        const mvhdPattern = Buffer.from([0x6D, 0x76, 0x68, 0x64]);
        
        for (let i = 0; i < buffer.length - mvhdPattern.length; i++) {
            let match = true;
            for (let j = 0; j < mvhdPattern.length; j++) {
                if (buffer[i + j] !== mvhdPattern[j]) {
                    match = false;
                    break;
                }
            }
            
            if (match) {
                // Durée se trouve généralement à offset + 20 (version 0) ou + 24 (version 1)
                const offset = i + 20;
                if (offset + 4 <= buffer.length) {
                    const duration = buffer.readUInt32BE(offset);
                    return duration / 1000; // Conversion en secondes (timescale/1000)
                }
            }
        }
        
        return null; // Non trouvé
    }

    async analyzeExistingMetadata() {
        console.log('2. Analyse des métadonnées existantes...');
        
        if (!fs.existsSync(this.metadataPath)) {
            this.results.metadataAnalysis = {
                exists: false,
                error: 'Fichier de métadonnées non trouvé'
            };
            return;
        }
        
        const metadata = JSON.parse(fs.readFileSync(this.metadataPath, 'utf8'));
        
        this.results.metadataAnalysis = {
            exists: true,
            format: metadata.file_info?.format || 'Unknown',
            version: metadata.file_info?.version || 'Unknown',
            source: metadata.file_info?.source || 'Unknown',
            generator: metadata.file_info?.generator || 'Unknown',
            
            videoProperties: {
                resolution: metadata.video_properties?.resolution || 'Unknown',
                fps: metadata.video_properties?.fps || null,
                frames: metadata.video_properties?.frames || null,
                duration: metadata.video_properties?.duration || null
            },
            
            compressionResults: {
                mode: metadata.compression_results?.mode || 'Unknown',
                originalSize: metadata.compression_results?.original_size_mb || null,
                compressedSize: metadata.compression_results?.compressed_size_mb || null,
                ratioVsRaw: metadata.compression_results?.compression_ratio_vs_raw || null,
                h264Ratio: metadata.compression_results?.h264_compression_ratio || null,
                economy: metadata.compression_results?.space_economy_percent || null,
                quality: metadata.compression_results?.quality || 'Unknown'
            }
        };
        
        console.log(`  Format: ${this.results.metadataAnalysis.format}`);
        console.log(`  Résolution: ${this.results.metadataAnalysis.videoProperties.resolution}`);
        console.log(`  Trames: ${this.results.metadataAnalysis.videoProperties.frames}`);
        console.log(`  Durée: ${this.results.metadataAnalysis.videoProperties.duration}s`);
        console.log(`  Ratio H264: ${this.results.metadataAnalysis.compressionResults.h264Ratio}:1`);
        console.log(`  Taille compressée: ${this.results.metadataAnalysis.compressionResults.compressedSize} MB`);
    }

    async analyzeOurCompression() {
        console.log('3. Analyse de notre compression...');
        
        // Lecture de nos résultats de test
        const testResultsPath = path.resolve(__dirname, 'real_video_test_results.json');
        
        if (!fs.existsSync(testResultsPath)) {
            this.results.compressionAnalysis = {
                exists: false,
                error: 'Résultats de test non trouvés'
            };
            return;
        }
        
        const testResults = JSON.parse(fs.readFileSync(testResultsPath, 'utf8'));
        
        this.results.compressionAnalysis = {
            exists: true,
            originalSize: testResults.overall?.originalSize || null,
            finalSize: testResults.overall?.finalSize || null,
            totalRatio: testResults.overall?.totalCompressionRatio || null,
            reduction: testResults.overall?.sizeReduction || null,
            quality: testResults.overall?.quality || 'Unknown',
            psnr: testResults.overall?.estimatedPSNR || null,
            processingTime: testResults.overall?.processingTime || null,
            fps: testResults.overall?.fps || null,
            
            // Analyse détaillée
            h264Analysis: testResults.h264Analysis || null,
            sdiConversion: testResults.sdiConversion || null,
            compression: testResults.compression || null
        };
        
        console.log(`  Taille originale: ${this.formatFileSize(this.results.compressionAnalysis.originalSize)}`);
        console.log(`  Taille finale: ${this.formatFileSize(this.results.compressionAnalysis.finalSize)}`);
        console.log(`  Ratio total: ${this.results.compressionAnalysis.totalRatio?.toFixed(2)}:1`);
        console.log(`  Réduction: ${this.results.compressionAnalysis.reduction}%`);
        console.log(`  Qualité: ${this.results.compressionAnalysis.quality}`);
        console.log(`  PSNR: ${this.results.compressionAnalysis.psnr} dB`);
    }

    async verifyIntegrity() {
        console.log('4. Vérification d\'intégrité...');
        
        if (!this.results.fileAnalysis || !this.results.metadataAnalysis || !this.results.compressionAnalysis) {
            this.results.integrityCheck = {
                success: false,
                error: 'Données manquantes pour la vérification'
            };
            return;
        }
        
        const checks = [];
        
        // Vérification 1: Cohérence des tailles
        const originalSize1 = this.results.fileAnalysis.size;
        const originalSize2 = this.results.metadataAnalysis.compressionResults.originalSize * 1024 * 1024;
        const originalSize3 = this.results.compressionAnalysis.originalSize;
        
        const sizeConsistency = Math.abs(originalSize1 - originalSize2) < (1024 * 1024) && // 1MB tolerance
                                 Math.abs(originalSize1 - originalSize3) < (1024 * 1024);
        
        checks.push({
            name: 'Cohérence des tailles originales',
            passed: sizeConsistency,
            details: {
                fileAnalysis: this.formatFileSize(originalSize1),
                metadata: this.formatFileSize(originalSize2),
                compression: this.formatFileSize(originalSize3)
            }
        });
        
        // Vérification 2: Cohérence des ratios
        const metadataRatio = parseFloat(this.results.metadataAnalysis.compressionResults.h264Ratio);
        const ourRatio = this.results.compressionAnalysis.totalRatio;
        
        const ratioReasonableness = ourRatio > 1 && ourRatio < 1000; // Ratio plausible
        
        checks.push({
            name: 'Plausibilité des ratios',
            passed: ratioReasonableness,
            details: {
                metadataRatio: metadataRatio,
                ourRatio: ourRatio,
                difference: Math.abs(metadataRatio - ourRatio) / metadataRatio * 100
            }
        });
        
        // Vérification 3: Cohérence des durées/trames
        const metadataFrames = this.results.metadataAnalysis.videoProperties.frames;
        const metadataDuration = this.results.metadataAnalysis.videoProperties.duration;
        const estimatedFrames = this.results.fileAnalysis.estimatedFrames;
        
        const frameConsistency = metadataFrames && estimatedFrames && 
                                Math.abs(metadataFrames - estimatedFrames) < (metadataFrames * 0.1); // 10% tolerance
        
        checks.push({
            name: 'Cohérence des trames',
            passed: frameConsistency,
            details: {
                metadataFrames: metadataFrames,
                estimatedFrames: estimatedFrames,
                metadataDuration: metadataDuration
            }
        });
        
        // Vérification 4: Vérification de notre processus
        const h264DataSize = this.results.compressionAnalysis.h264Analysis?.dataSize;
        const sdiSize = this.results.compressionAnalysis.sdiConversion?.sdiSize;
        const compressedSize = this.results.compressionAnalysis.finalSize;
        
        const processIntegrity = h264DataSize && sdiSize && compressedSize &&
                                sdiSize > h264DataSize && // Expansion SDI normale
                                compressedSize < sdiSize; // Compression effective
        
        checks.push({
            name: 'Intégrité du processus',
            passed: processIntegrity,
            details: {
                h264DataSize: this.formatFileSize(h264DataSize),
                sdiSize: this.formatFileSize(sdiSize),
                compressedSize: this.formatFileSize(compressedSize),
                expansionRatio: sdiSize / h264DataSize,
                compressionRatio: sdiSize / compressedSize
            }
        });
        
        this.results.integrityCheck = {
            success: checks.filter(c => c.passed).length >= 3, // Au moins 3/4 checks
            checks: checks,
            summary: {
                passed: checks.filter(c => c.passed).length,
                total: checks.length,
                percentage: (checks.filter(c => c.passed).length / checks.length * 100).toFixed(1)
            }
        };
        
        console.log(`  Checks passés: ${this.results.integrityCheck.summary.passed}/${this.results.integrityCheck.summary.total}`);
        console.log(`  Score d\'intégrité: ${this.results.integrityCheck.summary.percentage}%`);
        
        // Détail des checks
        for (const check of checks) {
            console.log(`  ${check.passed ? '✅' : '❌'} ${check.name}`);
            if (!check.passed) {
                console.log(`    Détails: ${JSON.stringify(check.details)}`);
            }
        }
    }

    async generateConclusion() {
        console.log('5. Génération de la conclusion...');
        
        const integrity = this.results.integrityCheck;
        const metadata = this.results.metadataAnalysis;
        const compression = this.results.compressionAnalysis;
        const file = this.results.fileAnalysis;
        
        let conclusion = {
            success: false,
            reliability: 'UNKNOWN',
            recommendations: []
        };
        
        if (integrity.success && integrity.summary.percentage >= 75) {
            conclusion.success = true;
            conclusion.reliability = 'HIGH';
        } else if (integrity.summary.percentage >= 50) {
            conclusion.success = true;
            conclusion.reliability = 'MEDIUM';
        } else {
            conclusion.success = false;
            conclusion.reliability = 'LOW';
        }
        
        // Analyse comparative
        if (metadata.exists && compression.exists) {
            const metadataRatio = parseFloat(metadata.compressionResults.h264Ratio);
            const ourRatio = compression.totalRatio;
            
            if (ourRatio > metadataRatio) {
                conclusion.recommendations.push('NOTRE COMPRESSION EST PLUS EFFICACE');
            } else {
                conclusion.recommendations.push('MÉTHODE EXISTANTE PLUS EFFICACE');
            }
        }
        
        // Analyse de la qualité
        if (compression.psnr && compression.psnr > 40) {
            conclusion.recommendations.push('QUALITÉ NEAR-LOSSLESS CONFIRMÉE');
        } else if (compression.psnr) {
            conclusion.recommendations.push('QUALITÉ ACCEPTABLE MAIS PERFECTIBLE');
        }
        
        // Analyse de la performance
        if (compression.fps && compression.fps > 30) {
            conclusion.recommendations.push('PERFORMANCE TEMPS RÉEL ATTEINTE');
        } else if (compression.fps) {
            conclusion.recommendations.push('PERFORMANCE AMÉLIORABLE');
        }
        
        this.results.conclusion = conclusion;
        
        console.log(`  Succès: ${conclusion.success ? 'OUI' : 'NON'}`);
        console.log(`  Fiabilité: ${conclusion.reliability}`);
        console.log(`  Recommandations: ${conclusion.recommendations.length}`);
        
        for (const rec of conclusion.recommendations) {
            console.log(`    • ${rec}`);
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    generateReport() {
        console.log('='.repeat(60));
        console.log('RAPPORT D\'ANALYSE PROFONDE');
        console.log('='.repeat(60));
        
        console.log('FICHIER ORIGINAL:');
        console.log(`  Taille: ${this.results.fileAnalysis?.sizeFormatted || 'Inconnue'}`);
        console.log(`  Type: ${this.results.fileAnalysis?.fileType || 'Inconnu'}`);
        console.log(`  Durée: ${this.results.fileAnalysis?.estimatedDuration || 'Inconnue'}s`);
        
        console.log('\nMÉTADONNÉES EXISTANTES:');
        if (this.results.metadataAnalysis?.exists) {
            console.log(`  Ratio H264: ${this.results.metadataAnalysis.compressionResults.h264Ratio}:1`);
            console.log(`  Taille compressée: ${this.results.metadataAnalysis.compressionResults.compressedSize} MB`);
            console.log(`  Qualité: ${this.results.metadataAnalysis.compressionResults.quality}`);
        } else {
            console.log('  Non disponibles');
        }
        
        console.log('\nNOTRE COMPRESSION:');
        if (this.results.compressionAnalysis?.exists) {
            console.log(`  Ratio total: ${this.results.compressionAnalysis.totalRatio?.toFixed(2)}:1`);
            console.log(`  Taille finale: ${this.formatFileSize(this.results.compressionAnalysis.finalSize)}`);
            console.log(`  Qualité: ${this.results.compressionAnalysis.quality}`);
            console.log(`  PSNR: ${this.results.compressionAnalysis.psnr} dB`);
        } else {
            console.log('  Non disponibles');
        }
        
        console.log('\nVÉRIFICATION D\'INTÉGRITÉ:');
        console.log(`  Score: ${this.results.integrityCheck?.summary.percentage || 'N/A'}%`);
        console.log(`  Checks passés: ${this.results.integrityCheck?.summary.passed || 0}/${this.results.integrityCheck?.summary.total || 0}`);
        
        console.log('\nCONCLUSION:');
        console.log(`  Fiabilité: ${this.results.conclusion?.reliability || 'INCONNUE'}`);
        console.log(`  Recommandations:`);
        for (const rec of this.results.conclusion?.recommendations || []) {
            console.log(`    • ${rec}`);
        }
        
        console.log('='.repeat(60));
    }
}

// Exécution
if (require.main === module) {
    (async () => {
        const analysis = new DeepAnalysis();
        await analysis.runDeepAnalysis();
        analysis.generateReport();
        
        // Sauvegarde
        try {
            const reportPath = path.resolve(__dirname, 'deep_analysis_results.json');
            fs.writeFileSync(reportPath, JSON.stringify(analysis.results, null, 2));
            console.log(`\nRapport sauvegardé dans: ${reportPath}`);
        } catch (error) {
            console.error('Erreur sauvegarde rapport:', error);
        }
    })();
}

module.exports = { DeepAnalysis };
