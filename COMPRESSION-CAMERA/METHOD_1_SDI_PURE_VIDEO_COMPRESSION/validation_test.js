/**
 * 
 * VALIDATION TEST - PIPELINE VIDÉO SDI-LIKE
 * Test complet du pipeline de compression vidéo
 * 
 */

class VideoValidationTest {
    constructor() {
        this.testResults = {
            pipeline: null,
            deconstruction: null,
            conversion: null,
            compression: null,
            overall: null
        };
        this.testData = this.generateTestData();
    }

    // 
    //  GÉNÉRATION DE DONNÉES DE TEST
    // 
    
    generateTestData() {
        console.log('Génération des données de test...');
        
        // Simulation de données H264 de test
        const h264Data = this.createMockH264Data();
        
        return {
            name: 'Test Video 1920x1080',
            resolution: '1920x1080',
            fps: 30,
            frames: 60, // 2 secondes de vidéo
            data: h264Data,
            expectedSize: 1920 * 1080 * 3 * 60, // RGB 24-bit
            metadata: {
                width: 1920,
                height: 1080,
                fps: 30,
                profile: 'High',
                level: '4.0',
                bitrate: 5000000 // 5 Mbps
            }
        };
    }

    createMockH264Data() {
        // Création de données H264 simulées
        const data = new Uint8Array(1024 * 1024); // 1MB de données
        
        // Ajout des NAL units de base
        let offset = 0;
        
        // SPS (Sequence Parameter Set)
        data[offset++] = 0x00; data[offset++] = 0x00; data[offset++] = 0x01;
        data[offset++] = 0x67; // SPS NAL unit
        data[offset++] = 0x42; // Profile High
        data[offset++] = 0x00; // Constraint set
        data[offset++] = 0x1E; // Level 4.0
        data[offset++] = 0x8D; // Seq parameter set id
        offset += 4; // Données SPS supplémentaires
        
        // PPS (Picture Parameter Set)
        data[offset++] = 0x00; data[offset++] = 0x00; data[offset++] = 0x01;
        data[offset++] = 0x68; // PPS NAL unit
        data[offset++] = 0xCE; // Pic parameter set id
        data[offset++] = 0x3C; // Seq parameter set id
        offset += 6; // Données PPS supplémentaires
        
        // Slices (trames vidéo)
        for (let frame = 0; frame < 60; frame++) {
            data[offset++] = 0x00; data[offset++] = 0x00; data[offset++] = 0x01;
            
            // IDR frame toutes les 30 frames
            if (frame % 30 === 0) {
                data[offset++] = 0x65; // IDR slice
            } else {
                data[offset++] = 0x41; // P slice
            }
            
            // Données de slice simulées
            const sliceSize = Math.floor(Math.random() * 1000) + 500;
            for (let i = 0; i < sliceSize && offset < data.length; i++) {
                data[offset++] = Math.floor(Math.random() * 256);
            }
        }
        
        return data.slice(0, offset);
    }

    // 
    //  TEST PRINCIPAL DU PIPELINE
    // 
    
    async runFullValidation() {
        console.log('Démarrage du test de validation complet...');
        
        try {
            // Initialisation du pipeline
            console.log('Initialisation du pipeline...');
            this.initializePipeline();
            
            // Test 1: Déconstruction H264
            console.log('Test 1: Déconstruction H264...');
            await this.testDeconstruction();
            
            // Test 2: Conversion SDI-like
            console.log('Test 2: Conversion SDI-like...');
            await this.testConversion();
            
            // Test 3: Compression SDI-like
            console.log('Test 3: Compression SDI-like...');
            await this.testCompression();
            
            // Test 4: Pipeline complet
            console.log('Test 4: Pipeline complet...');
            await this.testFullPipeline();
            
            // Validation finale
            console.log('Validation finale...');
            this.validateOverallResults();
            
            // Génération du rapport
            this.generateValidationReport();
            
            console.log('Test de validation terminé avec succès!');
            
        } catch (error) {
            console.error('Erreur dans le test de validation:', error);
            this.testResults.overall = {
                success: false,
                error: error.message
            };
        }
        
        return this.testResults;
    }

    initializePipeline() {
        // Vérification que les classes sont disponibles
        if (typeof H264Deconstructor === 'undefined') {
            throw new Error('H264Deconstructor non disponible');
        }
        if (typeof SDIVideoConverter === 'undefined') {
            throw new Error('SDIVideoConverter non disponible');
        }
        if (typeof SDIVideoCompressor === 'undefined') {
            throw new Error('SDIVideoCompressor non disponible');
        }
        if (typeof VideoSDIPipeline === 'undefined') {
            throw new Error('VideoSDIPipeline non disponible');
        }
        
        // Initialisation des composants
        this.deconstructor = new H264Deconstructor();
        this.converter = new SDIVideoConverter();
        this.compressor = new SDIVideoCompressor();
        this.pipeline = new VideoSDIPipeline();
        
        console.log('Pipeline initialisé avec succès');
    }

    // 
    //  TEST 1: DÉCONSTRUCTION H264
    // 
    
    async testDeconstruction() {
        const startTime = performance.now();
        
        try {
            const result = await this.deconstructor.deconstructH264(this.testData.data);
            const endTime = performance.now();
            
            const deconstructionTime = endTime - startTime;
            const expectedFrames = this.testData.frames;
            const actualFrames = result.frames.length;
            
            this.testResults.deconstruction = {
                success: true,
                framesProcessed: actualFrames,
                framesExpected: expectedFrames,
                frameAccuracy: actualFrames / expectedFrames,
                processingTime: deconstructionTime,
                nalUnits: result.nalUnits.length,
                metadata: result.metadata,
                analysis: result.analysis || {}
            };
            
            console.log(`Déconstruction: ${actualFrames}/${expectedFrames} trames en ${deconstructionTime.toFixed(1)}ms`);
            
        } catch (error) {
            this.testResults.deconstruction = {
                success: false,
                error: error.message
            };
            throw error;
        }
    }

    // 
    //  TEST 2: CONVERSION SDI-LIKE
    // 
    
    async testConversion() {
        const startTime = performance.now();
        
        try {
            // Utilisation des résultats de la déconstruction
            const h264Analysis = {
                frames: this.testResults.deconstruction.framesProcessed ? 
                    this.generateMockFrames(this.testResults.deconstruction.framesProcessed) : [],
                metadata: this.testData.metadata
            };
            
            const result = await this.converter.convertH264ToSDI(h264Analysis);
            const endTime = performance.now();
            
            const conversionTime = endTime - startTime;
            const originalSize = result.conversion.originalSize;
            const sdiSize = result.conversion.sdiSize;
            const conversionRatio = originalSize / sdiSize;
            
            this.testResults.conversion = {
                success: true,
                framesConverted: result.frames.length,
                originalSize: originalSize,
                sdiSize: sdiSize,
                conversionRatio: conversionRatio,
                processingTime: conversionTime,
                quality: result.conversion.quality,
                preserveMotion: result.conversion.preserveMotion
            };
            
            console.log(`Conversion: ${result.frames.length} trames, ratio ${conversionRatio.toFixed(2)}:1 en ${conversionTime.toFixed(1)}ms`);
            
        } catch (error) {
            this.testResults.conversion = {
                success: false,
                error: error.message
            };
            throw error;
        }
    }

    generateMockFrames(frameCount) {
        const frames = [];
        
        for (let i = 0; i < frameCount; i++) {
            frames.push({
                index: i,
                type: i % 30 === 0 ? 'IDR' : 'P',
                slices: [],
                macroblocks: this.generateMockMacroblocks(),
                motionVectors: i % 30 !== 0 ? this.generateMockMotionVectors() : [],
                metadata: {
                    width: this.testData.metadata.width,
                    height: this.testData.metadata.height,
                    timestamp: i * (1000 / this.testData.metadata.fps)
                }
            });
        }
        
        return frames;
    }

    generateMockMacroblocks() {
        const macroblocks = [];
        const mbCount = Math.floor(this.testData.metadata.width / 16) * Math.floor(this.testData.metadata.height / 16);
        
        for (let i = 0; i < mbCount; i++) {
            macroblocks.push({
                index: i,
                x: (i % Math.floor(this.testData.metadata.width / 16)) * 16,
                y: Math.floor(i / Math.floor(this.testData.metadata.width / 16)) * 16,
                type: 'P',
                predictionMode: 'INTER_16x16',
                dctCoefficients: this.generateMockDCTCoefficients(),
                qp: 26,
                codedBlockPattern: 63
            });
        }
        
        return macroblocks;
    }

    generateMockDCTCoefficients() {
        const coefficients = [];
        for (let i = 0; i < 64; i++) {
            coefficients.push(Math.floor(Math.random() * 256 - 128));
        }
        return coefficients;
    }

    generateMockMotionVectors() {
        const motionVectors = [];
        const mbCount = Math.floor(this.testData.metadata.width / 16) * Math.floor(this.testData.metadata.height / 16);
        
        for (let i = 0; i < mbCount; i += 4) { // 1/4 des macroblocks ont des vecteurs
            motionVectors.push({
                macroblockIndex: i,
                x: Math.floor(Math.random() * 32 - 16),
                y: Math.floor(Math.random() * 32 - 16),
                refFrame: 0,
                motionType: 'FORWARD',
                magnitude: Math.random() * 20
            });
        }
        
        return motionVectors;
    }

    // 
    //  TEST 3: COMPRESSION SDI-LIKE
    // 
    
    async testCompression() {
        const startTime = performance.now();
        
        try {
            // Génération de trames SDI simulées
            const sdiFrames = this.generateMockSDIFrames();
            
            const result = await this.compressor.compressVideo(sdiFrames);
            const endTime = performance.now();
            
            const compressionTime = endTime - startTime;
            const originalSize = result.originalSize;
            const compressedSize = result.compressedSize;
            const compressionRatio = result.ratio;
            
            this.testResults.compression = {
                success: true,
                framesProcessed: result.metadata.frames,
                originalSize: originalSize,
                compressedSize: compressedSize,
                compressionRatio: compressionRatio,
                processingTime: compressionTime,
                fps: result.fps,
                quality: result.metadata.quality,
                stats: result.metadata.stats
            };
            
            console.log(`Compression: ${result.metadata.frames} trames, ratio ${compressionRatio.toFixed(2)}:1 en ${compressionTime.toFixed(1)}ms`);
            
        } catch (error) {
            this.testResults.compression = {
                success: false,
                error: error.message
            };
            throw error;
        }
    }

    generateMockSDIFrames() {
        const frames = [];
        const frameCount = this.testResults.deconstruction?.framesProcessed || this.testData.frames;
        
        for (let i = 0; i < frameCount; i++) {
            const lines = [];
            const lineCount = this.testData.metadata.height;
            
            for (let y = 0; y < lineCount; y++) {
                const lineData = new Uint16Array(this.testData.metadata.width * 2); // YUV 4:2:2
                
                // Génération de données SDI simulées
                for (let x = 0; x < this.testData.metadata.width * 2; x++) {
                    lineData[x] = Math.floor(Math.random() * 1024); // 10-bit
                }
                
                lines.push({
                    lineNumber: y,
                    data: lineData,
                    metadata: {
                        timestamp: i * (1000 / this.testData.metadata.fps),
                        frameType: i % 30 === 0 ? 'IDR' : 'P'
                    }
                });
            }
            
            frames.push({
                frameNumber: i,
                lines: lines,
                metadata: {
                    width: this.testData.metadata.width,
                    height: this.testData.metadata.height,
                    bitDepth: 10,
                    colorSpace: 'YUV422',
                    frameType: i % 30 === 0 ? 'IDR' : 'P'
                }
            });
        }
        
        return frames;
    }

    // 
    //  TEST 4: PIPELINE COMPLET
    // 
    
    async testFullPipeline() {
        const startTime = performance.now();
        
        try {
            const result = await this.pipeline.processVideo(this.testData.data, {
                preserveQuality: true,
                preserveMotion: true,
                compressionLevel: 'high'
            });
            
            const endTime = performance.now();
            const processingTime = endTime - startTime;
            
            if (result.success) {
                this.testResults.pipeline = {
                    success: true,
                    originalSize: result.stats.originalSize,
                    compressedSize: result.stats.compressedSize,
                    compressionRatio: result.stats.compressionRatio,
                    processingTime: processingTime,
                    fps: result.stats.fps,
                    quality: result.stats.quality,
                    framesProcessed: result.stats.framesProcessed
                };
                
                console.log(`Pipeline complet: ratio ${result.stats.compressionRatio.toFixed(2)}:1 en ${processingTime.toFixed(1)}ms`);
            } else {
                this.testResults.pipeline = {
                    success: false,
                    error: result.error
                };
            }
            
        } catch (error) {
            this.testResults.pipeline = {
                success: false,
                error: error.message
            };
            throw error;
        }
    }

    // 
    //  VALIDATION FINALE
    // 
    
    validateOverallResults() {
        const results = this.testResults;
        
        // Vérification que tous les tests ont réussi
        const allTestsPassed = results.deconstruction?.success &&
                              results.conversion?.success &&
                              results.compression?.success &&
                              results.pipeline?.success;
        
        // Calcul des métriques globales
        const totalCompressionRatio = results.pipeline?.compressionRatio || 0;
        const totalProcessingTime = results.pipeline?.processingTime || 0;
        const totalFPS = results.pipeline?.fps || 0;
        
        // Validation des ratios attendus
        const expectedMinRatio = 10; // Minimum 10:1
        const expectedMaxFPS = 30; // Maximum 30 FPS
        const expectedMaxTime = 5000; // Maximum 5 secondes
        
        const ratioValid = totalCompressionRatio >= expectedMinRatio;
        const fpsValid = totalFPS >= expectedMaxFPS / 2; // Au moins 15 FPS
        const timeValid = totalProcessingTime <= expectedMaxTime;
        
        this.testResults.overall = {
            success: allTestsPassed && ratioValid && fpsValid && timeValid,
            allTestsPassed: allTestsPassed,
            compressionRatio: totalCompressionRatio,
            processingTime: totalProcessingTime,
            fps: totalFPS,
            ratioValid: ratioValid,
            fpsValid: fpsValid,
            timeValid: timeValid,
            score: this.calculateOverallScore(results)
        };
        
        console.log(`Validation finale: ${this.testResults.overall.success ? 'RÉUSSIE' : 'ÉCHOUÉE'}`);
        console.log(`Score global: ${this.testResults.overall.score}/100`);
    }

    calculateOverallScore(results) {
        let score = 0;
        
        // Déconstruction (20 points)
        if (results.deconstruction?.success) {
            score += 20;
            if (results.deconstruction.frameAccuracy >= 0.95) score += 5;
        }
        
        // Conversion (25 points)
        if (results.conversion?.success) {
            score += 25;
            if (results.conversion.conversionRatio >= 1.5) score += 5;
        }
        
        // Compression (30 points)
        if (results.compression?.success) {
            score += 30;
            if (results.compression.compressionRatio >= 10) score += 10;
        }
        
        // Pipeline (25 points)
        if (results.pipeline?.success) {
            score += 25;
            if (results.pipeline.compressionRatio >= 10) score += 5;
        }
        
        return Math.min(100, score);
    }

    // 
    //  GÉNÉRATION DU RAPPORT
    // 
    
    generateValidationReport() {
        const results = this.testResults;
        
        const report = {
            testInfo: {
                name: 'SDI Video Compression Validation Test',
                timestamp: new Date().toISOString(),
                testData: this.testData.name,
                resolution: this.testData.resolution,
                frames: this.testData.frames
            },
            summary: {
                overallSuccess: results.overall?.success || false,
                overallScore: results.overall?.score || 0,
                totalCompressionRatio: results.overall?.compressionRatio || 0,
                totalProcessingTime: results.overall?.processingTime || 0,
                averageFPS: results.overall?.fps || 0
            },
            detailedResults: results,
            validation: {
                deconstructionValid: results.deconstruction?.success || false,
                conversionValid: results.conversion?.success || false,
                compressionValid: results.compression?.success || false,
                pipelineValid: results.pipeline?.success || false,
                ratiosMet: results.overall?.ratioValid || false,
                performanceMet: results.overall?.fpsValid && results.overall?.timeValid
            },
            conclusions: this.generateConclusions()
        };
        
        console.log('RAPPORT DE VALIDATION:');
        console.log('='.repeat(50));
        console.log(`Succès global: ${report.summary.overallSuccess ? 'OUI' : 'NON'}`);
        console.log(`Score: ${report.summary.overallScore}/100`);
        console.log(`Ratio de compression: ${report.summary.totalCompressionRatio.toFixed(2)}:1`);
        console.log(`Temps de traitement: ${(report.summary.totalProcessingTime / 1000).toFixed(2)}s`);
        console.log(`FPS moyen: ${report.summary.averageFPS.toFixed(1)}`);
        console.log('='.repeat(50));
        
        return report;
    }

    generateConclusions() {
        const results = this.testResults;
        
        let conclusions = [];
        
        if (results.overall?.success) {
            conclusions.push('Test de validation RÉUSSI');
            conclusions.push('Pipeline vidéo SDI-like fonctionnel');
            
            if (results.overall.compressionRatio >= 50) {
                conclusions.push('Ratio de compression EXCEPTIONNEL (>50:1)');
            } else if (results.overall.compressionRatio >= 20) {
                conclusions.push('Ratio de compression EXCELLENT (>20:1)');
            } else if (results.overall.compressionRatio >= 10) {
                conclusions.push('Ratio de compression BON (>10:1)');
            }
            
            if (results.overall.fps >= 30) {
                conclusions.push('Performance temps réel atteinte');
            } else if (results.overall.fps >= 15) {
                conclusions.push('Performance acceptable');
            }
        } else {
            conclusions.push('Test de validation ÉCHOUÉ');
            
            if (!results.deconstruction?.success) {
                conclusions.push('Échec de la déconstruction H264');
            }
            if (!results.conversion?.success) {
                conclusions.push('Échec de la conversion SDI-like');
            }
            if (!results.compression?.success) {
                conclusions.push('Échec de la compression SDI-like');
            }
            if (!results.pipeline?.success) {
                conclusions.push('Échec du pipeline complet');
            }
        }
        
        return conclusions;
    }
}

// 
//  EXÉCUTION DU TEST
// 

// Auto-exécution si le script est chargé directement
if (typeof window !== 'undefined') {
    // Dans un navigateur
    window.VideoValidationTest = VideoValidationTest;
    
    // Exécution automatique pour test
    window.runValidationTest = async function() {
        const test = new VideoValidationTest();
        return await test.runFullValidation();
    };
} else if (typeof module !== 'undefined' && module.exports) {
    // Dans Node.js
    module.exports = { VideoValidationTest };
    
    // Exécution si appelé directement
    if (require.main === module) {
        (async () => {
            const test = new VideoValidationTest();
            const results = await test.runFullValidation();
            console.log('Résultats du test:', results);
        })();
    }
}

console.log('Test de validation vidéo SDI-like prêt');
