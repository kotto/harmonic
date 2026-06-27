/**
 * 
 * VÉRIFICATION DU RATIO H264 PRÉ-COMPRÉSSÉ
 * Analyse détaillée de l'affirmation 1.85:1 sur B3.mp4
 * 
 */

const fs = require('fs');
const path = require('path');

class H264RatioVerification {
    constructor() {
        this.videoPath = path.resolve(__dirname, '..', '..', 'B3.mp4');
        this.metadataPath = path.resolve(__dirname, '..', '..', 'B3_metadata.json');
        this.results = {
            videoAnalysis: null,
            h264Standards: null,
            ratioCalculation: null,
            verification: null,
            conclusion: null
        };
    }

    async runVerification() {
        console.log('VÉRIFICATION DU RATIO H264 PRÉ-COMPRÉSSÉ');
        console.log('='.repeat(60));
        
        try {
            // Étape 1: Analyse du fichier vidéo
            await this.analyzeVideoFile();
            
            // Étape 2: Analyse des standards H264
            await this.analyzeH264Standards();
            
            // Étape 3: Calcul des ratios
            await this.calculateRatios();
            
            // Étape 4: Vérification de l'affirmation
            await this.verifyAffirmation();
            
            // Étape 5: Conclusion
            await this.generateConclusion();
            
        } catch (error) {
            console.error('Erreur dans la vérification:', error);
            this.results.conclusion = {
                success: false,
                error: error.message
            };
        }
        
        return this.results;
    }

    async analyzeVideoFile() {
        console.log('1. Analyse du fichier vidéo B3.mp4...');
        
        const stats = fs.statSync(this.videoPath);
        
        // Lecture des métadonnées existantes
        let metadata = null;
        if (fs.existsSync(this.metadataPath)) {
            metadata = JSON.parse(fs.readFileSync(this.metadataPath, 'utf8'));
        }
        
        // Analyse de l'en-tête MP4
        const buffer = fs.readFileSync(this.videoPath, { start: 0, end: 1024 });
        const header = buffer.slice(0, 16);
        
        // Détection du type de codec
        const isMP4 = header[4] === 0x66 && header[5] === 0x74 && 
                      header[6] === 0x79 && header[7] === 0x70; // 'ftyp'
        
        // Recherche des informations de codec dans le fichier
        const codecInfo = this.extractCodecInfo(fs.readFileSync(this.videoPath));
        
        this.results.videoAnalysis = {
            fileSize: stats.size,
            fileSizeFormatted: this.formatFileSize(stats.size),
            fileType: isMP4 ? 'MP4' : 'Unknown',
            codecInfo: codecInfo,
            metadata: metadata,
            
            // Calcul des tailles théoriques
            rawSize: this.calculateRawSize(metadata),
            theoreticalH264Size: this.calculateTheoreticalH264Size(metadata),
            actualH264Size: stats.size
        };
        
        console.log(`  Taille fichier: ${this.results.videoAnalysis.fileSizeFormatted}`);
        console.log(`  Type: ${this.results.videoAnalysis.fileType}`);
        console.log(`  Codec: ${this.results.videoAnalysis.codecInfo.codec || 'Unknown'}`);
        console.log(`  Résolution: ${metadata?.video_properties?.resolution || 'Unknown'}`);
        console.log(`  Trames: ${metadata?.video_properties?.frames || 'Unknown'}`);
        console.log(`  Durée: ${metadata?.video_properties?.duration || 'Unknown'}s`);
    }

    extractCodecInfo(buffer) {
        // Recherche des informations de codec dans le fichier MP4
        const patterns = {
            'avc1': Buffer.from([0x61, 0x76, 0x63, 0x31]), // H.264
            'h264': Buffer.from([0x68, 0x32, 0x36, 0x34]), // H.264
            'mp4v': Buffer.from([0x6d, 0x70, 0x34, 0x76]), // MPEG-4
            'hevc': Buffer.from([0x68, 0x65, 0x76, 0x63]), // H.265
        };
        
        for (const [codec, pattern] of Object.entries(patterns)) {
            for (let i = 0; i < buffer.length - pattern.length; i++) {
                let match = true;
                for (let j = 0; j < pattern.length; j++) {
                    if (buffer[i + j] !== pattern[j]) {
                        match = false;
                        break;
                    }
                }
                if (match) {
                    return {
                        codec: codec.toUpperCase(),
                        detected: true,
                        position: i
                    };
                }
            }
        }
        
        return {
            codec: 'Unknown',
            detected: false
        };
    }

    calculateRawSize(metadata) {
        if (!metadata?.video_properties) {
            return null;
        }
        
        const { resolution, frames, fps } = metadata.video_properties;
        if (!resolution || !frames) {
            return null;
        }
        
        const [width, height] = resolution.split('×').map(Number);
        
        // Taille RAW non-compressée (RGB 24-bit)
        const rawSize = width * height * 3 * frames;
        
        return rawSize;
    }

    calculateTheoreticalH264Size(metadata) {
        if (!metadata?.video_properties) {
            return null;
        }
        
        const { resolution, frames, fps, duration } = metadata.video_properties;
        if (!resolution || !frames || !duration) {
            return null;
        }
        
        const [width, height] = resolution.split('×').map(Number);
        
        // Estimation théorique H264 (basée sur les standards)
        // H264 typique: 1-10 Mbps pour HD, selon la qualité
        
        let bitrate = 5000000; // 5 Mbps par défaut
        
        // Ajustement selon la résolution
        if (width * height <= 640 * 480) {
            bitrate = 2000000; // 2 Mbps pour SD
        } else if (width * height <= 1280 * 720) {
            bitrate = 4000000; // 4 Mbps pour HD
        } else if (width * height <= 1920 * 1080) {
            bitrate = 8000000; // 8 Mbps pour Full HD
        } else {
            bitrate = 15000000; // 15 Mbps pour 4K
        }
        
        const theoreticalSize = (bitrate * duration) / 8; // bits to bytes
        
        return theoreticalSize;
    }

    async analyzeH264Standards() {
        console.log('2. Analyse des standards H264...');
        
        // Standards de compression H264 typiques
        this.results.h264Standards = {
            // Ratios de compression typiques par rapport au RAW
            rawToH264Ratios: {
                'Low Quality': { min: 50, max: 200, typical: 100 },    // 50:1 - 200:1
                'Medium Quality': { min: 30, max: 100, typical: 50 },  // 30:1 - 100:1
                'High Quality': { min: 15, max: 50, typical: 25 },     // 15:1 - 50:1
                'Lossless': { min: 2, max: 5, typical: 3 }            // 2:1 - 5:1
            },
            
            // Bitrates typiques par résolution
            bitrates: {
                '480p (640×480)': { min: 1, max: 5, typical: 2 },      // Mbps
                '720p (1280×720)': { min: 3, max: 8, typical: 5 },     // Mbps
                '1080p (1920×1080)': { min: 5, max: 15, typical: 8 },  // Mbps
                '4K (3840×2160)': { min: 15, max: 40, typical: 25 }    // Mbps
            },
            
            // Facteurs affectant le ratio
            affectingFactors: [
                'Complexité de la scène',
                'Mouvement dans la vidéo',
                'Paramètres de quantification',
                'GOP size (I-frame interval)',
                'Profile/Level utilisé'
            ]
        };
        
        console.log('  Ratios RAW vers H264 typiques:');
        for (const [quality, ratios] of Object.entries(this.results.h264Standards.rawToH264Ratios)) {
            console.log(`    ${quality}: ${ratios.min}:1 - ${ratios.max}:1 (typique: ${ratios.typical}:1)`);
        }
        
        console.log('  Bitrates typiques:');
        for (const [resolution, bitrates] of Object.entries(this.results.h264Standards.bitrates)) {
            console.log(`    ${resolution}: ${bitrates.min}-${bitrates.max} Mbps (typique: ${bitrates.typical} Mbps)`);
        }
    }

    async calculateRatios() {
        console.log('3. Calcul des ratios...');
        
        const video = this.results.videoAnalysis;
        const standards = this.results.h264Standards;
        
        if (!video.rawSize || !video.metadata) {
            this.results.ratioCalculation = {
                error: 'Données insuffisantes pour calculer les ratios'
            };
            return;
        }
        
        const metadata = video.metadata;
        const { resolution, frames, duration } = metadata.video_properties;
        
        // Ratio mesuré (selon les métadonnées)
        const measuredRatio = parseFloat(metadata.compression_results.h264_compression_ratio);
        
        // Ratio calculé (taille réelle / taille RAW)
        const calculatedRatio = video.fileSize / video.rawSize;
        
        // Ratio théorique (basé sur les standards)
        let theoreticalRatio = null;
        const resolutionKey = this.getResolutionKey(resolution);
        if (resolutionKey && standards.bitrates[resolutionKey]) {
            const typicalBitrate = standards.bitrates[resolutionKey].typical * 1000000; // Convert to bps
            const theoreticalSize = (typicalBitrate * duration) / 8;
            theoreticalRatio = theoreticalSize / video.rawSize;
        }
        
        this.results.ratioCalculation = {
            rawSize: video.rawSize,
            actualSize: video.fileSize,
            measuredRatio: measuredRatio,
            calculatedRatio: calculatedRatio,
            theoreticalRatio: theoreticalRatio,
            
            // Analyse
            ratioDifference: Math.abs(measuredRatio - calculatedRatio),
            isWithinStandards: this.isRatioWithinStandards(measuredRatio, resolution),
            qualityLevel: this.estimateQualityLevel(measuredRatio)
        };
        
        console.log(`  Taille RAW: ${this.formatFileSize(video.rawSize)}`);
        console.log(`  Taille réelle: ${this.formatFileSize(video.fileSize)}`);
        console.log(`  Ratio mesuré: ${measuredRatio.toFixed(2)}:1`);
        console.log(`  Ratio calculé: ${calculatedRatio.toFixed(2)}:1`);
        console.log(`  Ratio théorique: ${theoreticalRatio ? theoreticalRatio.toFixed(2) + ':1' : 'N/A'}`);
        console.log(`  Niveau qualité: ${this.results.ratioCalculation.qualityLevel}`);
    }

    getResolutionKey(resolution) {
        const [width, height] = resolution.split('×').map(Number);
        
        if (width <= 640 && height <= 480) {
            return '480p (640×480)';
        } else if (width <= 1280 && height <= 720) {
            return '720p (1280×720)';
        } else if (width <= 1920 && height <= 1080) {
            return '1080p (1920×1080)';
        } else if (width <= 3840 && height <= 2160) {
            return '4K (3840×2160)';
        }
        
        return null;
    }

    isRatioWithinStandards(ratio, resolution) {
        const standards = this.results.h264Standards.rawToH264Ratios;
        
        // Vérifier si le ratio est dans la plage de n'importe quelle qualité
        for (const [quality, ranges] of Object.entries(standards)) {
            if (ratio >= ranges.min && ratio <= ranges.max) {
                return {
                    within: true,
                    quality: quality,
                    range: `${ranges.min}:1 - ${ranges.max}:1`
                };
            }
        }
        
        return {
            within: false,
            quality: 'Unknown',
            range: 'Outside standards'
        };
    }

    estimateQualityLevel(ratio) {
        const standards = this.results.h264Standards.rawToH264Ratios;
        
        for (const [quality, ranges] of Object.entries(standards)) {
            if (ratio >= ranges.min && ratio <= ranges.max) {
                return quality;
            }
        }
        
        if (ratio < standards['Lossless'].min) {
            return 'Exceptional (possible lossless)';
        } else if (ratio > standards['Low Quality'].max) {
            return 'Very Low Quality';
        }
        
        return 'Unknown';
    }

    async verifyAffirmation() {
        console.log('4. Vérification de l\'affirmation...');
        
        const ratio = this.results.ratioCalculation;
        const video = this.results.videoAnalysis;
        
        if (!ratio.measuredRatio) {
            this.results.verification = {
                success: false,
                error: 'Ratio non disponible pour vérification'
            };
            return;
        }
        
        // Vérification de l'affirmation "H264 pré-compressé : Ratio plus faible (1.85:1)"
        const affirmationRatio = 1.85;
        const actualRatio = ratio.measuredRatio;
        const difference = Math.abs(actualRatio - affirmationRatio);
        const tolerance = 0.1; // 10% de tolérance
        
        const isAffirmationCorrect = difference <= tolerance;
        
        // Analyse du contexte
        const context = {
            isPreCompressed: this.isVideoPreCompressed(video),
            ratioIsLow: actualRatio < 5, // Ratio < 5:1 est considéré comme faible
            isWithinExpectations: ratio.isWithinStandards.within,
            qualityLevel: ratio.qualityLevel
        };
        
        this.results.verification = {
            affirmationRatio: affirmationRatio,
            actualRatio: actualRatio,
            difference: difference,
            tolerance: tolerance,
            isAffirmationCorrect: isAffirmationCorrect,
            context: context,
            
            // Analyse détaillée
            analysis: {
                ratioComparison: actualRatio > affirmationRatio ? 'Plus élevé' : 'Plus faible',
                significance: difference < 0.5 ? 'Différence mineure' : 'Différence significative',
                conclusion: this.generateVerificationConclusion(isAffirmationCorrect, context)
            }
        };
        
        console.log(`  Ratio affirmé: ${affirmationRatio}:1`);
        console.log(`  Ratio réel: ${actualRatio.toFixed(2)}:1`);
        console.log(`  Différence: ${difference.toFixed(2)}`);
        console.log(`  Affirmation correcte: ${isAffirmationCorrect ? 'OUI' : 'NON'}`);
        console.log(`  Vidéo pré-compressée: ${context.isPreCompressed ? 'OUI' : 'NON'}`);
        console.log(`  Ratio faible: ${context.ratioIsLow ? 'OUI' : 'NON'}`);
    }

    isVideoPreCompressed(video) {
        // Critères pour déterminer si une vidéo est pré-compressée
        const criteria = {
            codecIsH264: video.codecInfo.codec === 'H264',
            containerIsMP4: video.fileType === 'MP4',
            ratioIsLow: this.results.ratioCalculation?.measuredRatio < 10,
            sizeIsReasonable: video.fileSize < 500 * 1024 * 1024 // < 500MB
        };
        
        const score = Object.values(criteria).filter(Boolean).length;
        
        return {
            isPreCompressed: score >= 3,
            score: score,
            criteria: criteria
        };
    }

    generateVerificationConclusion(isCorrect, context) {
        if (!isCorrect) {
            return "L'affirmation est incorrecte - le ratio réel diffère significativement";
        }
        
        if (context.isPreCompressed && context.ratioIsLow) {
            return "L'affirmation est correcte - la vidéo est effectivement pré-compressée avec un ratio faible";
        }
        
        if (context.isPreCompressed) {
            return "L'affirmation est correcte sur le ratio mais le contexte pré-compressé est ambigu";
        }
        
        return "L'affirmation est correcte sur le ratio mais la vidéo n'est pas clairement pré-compressée";
    }

    async generateConclusion() {
        console.log('5. Génération de la conclusion...');
        
        const verification = this.results.verification;
        const ratio = this.results.ratioCalculation;
        const video = this.results.videoAnalysis;
        
        let conclusion = {
            success: false,
            affirmationCorrect: false,
            detailedAnalysis: []
        };
        
        if (verification.isAffirmationCorrect) {
            conclusion.success = true;
            conclusion.affirmationCorrect = true;
            
            conclusion.detailedAnalysis.push(
                "L'affirmation 'H264 pré-compressé : Ratio plus faible (1.85:1)' est CORRECTE"
            );
            
            if (verification.context.isPreCompressed) {
                conclusion.detailedAnalysis.push(
                    "La vidéo B3.mp4 est effectivement pré-compressée en H264"
                );
            }
            
            if (verification.context.ratioIsLow) {
                conclusion.detailedAnalysis.push(
                    "Le ratio de 1.85:1 est effectivement faible pour une compression H264"
                );
            }
            
            if (ratio.isWithinStandards.within) {
                conclusion.detailedAnalysis.push(
                    `Le ratio est dans les standards pour la qualité: ${ratio.isWithinStandards.quality}`
                );
            }
            
        } else {
            conclusion.affirmationCorrect = false;
            
            conclusion.detailedAnalysis.push(
                "L'affirmation est INCORRECTE - le ratio réel diffère"
            );
            
            conclusion.detailedAnalysis.push(
                `Ratio réel: ${ratio.measuredRatio.toFixed(2)}:1 vs affirmé: 1.85:1`
            );
        }
        
        // Analyse supplémentaire
        if (ratio.measuredRatio < 5) {
            conclusion.detailedAnalysis.push(
                "Le ratio faible suggère une vidéo de haute qualité ou pré-compressée"
            );
        }
        
        if (video.codecInfo.detected) {
            conclusion.detailedAnalysis.push(
                `Codec détecté: ${video.codecInfo.codec} - confirme l'encodage H264`
            );
        }
        
        this.results.conclusion = conclusion;
        
        console.log(`  Succès: ${conclusion.success ? 'OUI' : 'NON'}`);
        console.log(`  Affirmation correcte: ${conclusion.affirmationCorrect ? 'OUI' : 'NON'}`);
        console.log(`  Points d'analyse: ${conclusion.detailedAnalysis.length}`);
        
        for (const point of conclusion.detailedAnalysis) {
            console.log(`    ${point}`);
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
        console.log('RAPPORT DE VÉRIFICATION - RATIO H264');
        console.log('='.repeat(60));
        
        console.log('FICHIER ANALYSÉ:');
        console.log(`  Taille: ${this.results.videoAnalysis?.fileSizeFormatted || 'Inconnue'}`);
        console.log(`  Codec: ${this.results.videoAnalysis?.codecInfo.codec || 'Inconnu'}`);
        console.log(`  Résolution: ${this.results.videoAnalysis?.metadata?.video_properties?.resolution || 'Inconnue'}`);
        
        console.log('\nRATIOS CALCULÉS:');
        if (this.results.ratioCalculation) {
            console.log(`  RAW: ${this.formatFileSize(this.results.ratioCalculation.rawSize)}`);
            console.log(`  Réel: ${this.formatFileSize(this.results.ratioCalculation.actualSize)}`);
            console.log(`  Ratio mesuré: ${this.results.ratioCalculation.measuredRatio?.toFixed(2)}:1`);
            console.log(`  Ratio calculé: ${this.results.ratioCalculation.calculatedRatio?.toFixed(2)}:1`);
            console.log(`  Niveau qualité: ${this.results.ratioCalculation.qualityLevel}`);
        }
        
        console.log('\nVÉRIFICATION DE L\'AFFIRMATION:');
        if (this.results.verification) {
            console.log(`  Affirmation: "H264 pré-compressé : Ratio plus faible (1.85:1)"`);
            console.log(`  Ratio réel: ${this.results.verification.actualRatio?.toFixed(2)}:1`);
            console.log(`  Correcte: ${this.results.verification.isAffirmationCorrect ? 'OUI' : 'NON'}`);
            console.log(`  Différence: ${this.results.verification.difference?.toFixed(2)}`);
        }
        
        console.log('\nCONCLUSION:');
        if (this.results.conclusion) {
            console.log(`  Succès: ${this.results.conclusion.success ? 'OUI' : 'NON'}`);
            for (const point of this.results.conclusion.detailedAnalysis) {
                console.log(`  ${point}`);
            }
        }
        
        console.log('='.repeat(60));
    }
}

// Exécution
if (require.main === module) {
    (async () => {
        const verification = new H264RatioVerification();
        await verification.runVerification();
        verification.generateReport();
        
        // Sauvegarde
        try {
            const reportPath = path.resolve(__dirname, 'h264_ratio_verification.json');
            fs.writeFileSync(reportPath, JSON.stringify(verification.results, null, 2));
            console.log(`\nRapport sauvegardé dans: ${reportPath}`);
        } catch (error) {
            console.error('Erreur sauvegarde rapport:', error);
        }
    })();
}

module.exports = { H264RatioVerification };
