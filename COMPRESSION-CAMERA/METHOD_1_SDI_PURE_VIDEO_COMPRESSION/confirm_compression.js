/**
 * 
 * CONFIRMATION DE LA COMPRESSION RÉELLE
 * Vérification des tailles et confirmation compression vs expansion
 * 
 */

const fs = require('fs');
const path = require('path');

class CompressionConfirmation {
    constructor() {
        this.originalPath = path.resolve(__dirname, '..', '..', 'B3.mp4');
        this.compressedPath = path.resolve(__dirname, '..', '..', 'b3.hcv16');
        this.metadataPath = path.resolve(__dirname, '..', '..', 'B3_metadata.json');
        this.results = {
            fileSizes: null,
            compressionAnalysis: null,
            verification: null,
            conclusion: null
        };
    }

    async runConfirmation() {
        console.log('CONFIRMATION DE LA COMPRESSION RÉELLE');
        console.log('='.repeat(60));
        
        try {
            // Étape 1: Vérification des tailles de fichiers
            await this.verifyFileSizes();
            
            // Étape 2: Analyse de la compression
            await this.analyzeCompression();
            
            // Étape 3: Vérification avec métadonnées
            await this.verifyWithMetadata();
            
            // Étape 4: Conclusion finale
            await this.generateConclusion();
            
        } catch (error) {
            console.error('Erreur dans la confirmation:', error);
            this.results.conclusion = {
                success: false,
                error: error.message
            };
        }
        
        return this.results;
    }

    async verifyFileSizes() {
        console.log('1. Vérification des tailles de fichiers...');
        
        // Vérification fichier original
        if (!fs.existsSync(this.originalPath)) {
            throw new Error(`Fichier original non trouvé: ${this.originalPath}`);
        }
        
        const originalStats = fs.statSync(this.originalPath);
        
        // Vérification fichier compressé
        if (!fs.existsSync(this.compressedPath)) {
            throw new Error(`Fichier compressé non trouvé: ${this.compressedPath}`);
        }
        
        const compressedStats = fs.statSync(this.compressedPath);
        
        // Calcul des ratios
        const originalSize = originalStats.size;
        const compressedSize = compressedStats.size;
        const ratio = originalSize / compressedSize;
        const reduction = ((originalSize - compressedSize) / originalSize) * 100;
        
        this.results.fileSizes = {
            original: {
                path: this.originalPath,
                size: originalSize,
                sizeFormatted: this.formatFileSize(originalSize),
                lastModified: originalStats.mtime
            },
            compressed: {
                path: this.compressedPath,
                size: compressedSize,
                sizeFormatted: this.formatFileSize(compressedSize),
                lastModified: compressedStats.mtime
            },
            compression: {
                ratio: ratio,
                reduction: reduction,
                isCompression: ratio > 1,
                isExpansion: ratio < 1,
                isNeutral: ratio === 1
            }
        };
        
        console.log(`  Fichier original: ${this.results.fileSizes.original.sizeFormatted}`);
        console.log(`  Fichier compressé: ${this.results.fileSizes.compressed.sizeFormatted}`);
        console.log(`  Ratio: ${ratio.toFixed(2)}:1`);
        console.log(`  Réduction: ${reduction.toFixed(2)}%`);
        console.log(`  Type: ${this.results.fileSizes.compression.isCompression ? 'COMPRESSION' : (this.results.fileSizes.compression.isExpansion ? 'EXPANSION' : 'NEUTRE')}`);
    }

    async analyzeCompression() {
        console.log('2. Analyse de la compression...');
        
        const fileSizes = this.results.fileSizes;
        
        // Analyse détaillée
        const analysis = {
            compressionLevel: this.determineCompressionLevel(fileSizes.compression.ratio),
            efficiency: this.calculateEfficiency(fileSizes.compression.ratio),
            spaceSaved: fileSizes.original.size - fileSizes.compressed.size,
            spaceSavedFormatted: this.formatFileSize(fileSizes.original.size - fileSizes.compressed.size),
            validation: this.validateCompression(fileSizes.compression)
        };
        
        this.results.compressionAnalysis = analysis;
        
        console.log(`  Niveau de compression: ${analysis.compressionLevel}`);
        console.log(`  Efficacité: ${analysis.efficiency}`);
        console.log(`  Espace sauvé: ${analysis.spaceSavedFormatted}`);
        console.log(`  Validation: ${analysis.validation.isValid ? 'VALIDE' : 'INVALIDE'}`);
    }

    determineCompressionLevel(ratio) {
        if (ratio < 1) return 'EXPANSION';
        if (ratio < 1.5) return 'TRÈS FAIBLE';
        if (ratio < 2) return 'FAIBLE';
        if (ratio < 5) return 'MODÉRÉE';
        if (ratio < 10) return 'BONNE';
        if (ratio < 20) return 'EXCELLENTE';
        if (ratio < 50) return 'EXCEPTIONNELLE';
        return 'RÉVOLUTIONNAIRE';
    }

    calculateEfficiency(ratio) {
        if (ratio < 1) return 'INEFFICACE (expansion)';
        if (ratio < 1.5) return 'TRÈS FAIBLE';
        if (ratio < 2) return 'FAIBLE';
        if (ratio < 5) return 'MODÉRÉE';
        if (ratio < 10) return 'BONNE';
        if (ratio < 20) return 'EXCELLENTE';
        return 'EXCEPTIONNELLE';
    }

    validateCompression(compression) {
        return {
            isValid: compression.isCompression,
            ratio: compression.ratio,
            reduction: compression.reduction,
            isSignificant: compression.ratio > 1.1, // Au moins 10% de réduction
            isReasonable: compression.ratio < 1000, // Moins de 1000:1
            isPossible: compression.ratio > 1 && compression.ratio < 10000
        };
    }

    async verifyWithMetadata() {
        console.log('3. Vérification avec les métadonnées...');
        
        let metadata = null;
        if (fs.existsSync(this.metadataPath)) {
            metadata = JSON.parse(fs.readFileSync(this.metadataPath, 'utf8'));
        }
        
        const verification = {
            metadataExists: metadata !== null,
            metadataConsistent: false,
            sizeConsistent: false,
            ratioConsistent: false,
            details: {}
        };
        
        if (metadata) {
            const originalSize = parseFloat(metadata.compression_results.original_size_mb) * 1024 * 1024;
            const compressedSize = parseFloat(metadata.compression_results.compressed_size_mb) * 1024 * 1024;
            const metadataRatio = parseFloat(metadata.compression_results.h264_compression_ratio);
            
            verification.details = {
                metadataOriginalSize: this.formatFileSize(originalSize),
                metadataCompressedSize: this.formatFileSize(compressedSize),
                metadataRatio: metadataRatio,
                actualOriginalSize: this.formatFileSize(this.results.fileSizes.original.size),
                actualCompressedSize: this.formatFileSize(this.results.fileSizes.compressed.size),
                actualRatio: this.results.fileSizes.compression.ratio
            };
            
            // Vérification de cohérence
            verification.sizeConsistent = Math.abs(originalSize - this.results.fileSizes.original.size) < (1024 * 1024); // 1MB tolerance
            verification.ratioConsistent = Math.abs(metadataRatio - this.results.fileSizes.compression.ratio) < 0.1; // 0.1 tolerance
            verification.metadataConsistent = verification.sizeConsistent && verification.ratioConsistent;
        }
        
        this.results.verification = verification;
        
        console.log(`  Métadonnées existantes: ${verification.metadataExists ? 'OUI' : 'NON'}`);
        if (verification.metadataExists) {
            console.log(`  Cohérence des tailles: ${verification.sizeConsistent ? 'OUI' : 'NON'}`);
            console.log(`  Cohérence des ratios: ${verification.ratioConsistent ? 'OUI' : 'NON'}`);
            console.log(`  Métadonnées cohérentes: ${verification.metadataConsistent ? 'OUI' : 'NON'}`);
        }
    }

    async generateConclusion() {
        console.log('4. Génération de la conclusion...');
        
        const fileSizes = this.results.fileSizes;
        const compression = this.results.compressionAnalysis;
        const verification = this.results.verification;
        
        let conclusion = {
            success: false,
            isCompression: false,
            isExpansion: false,
            summary: '',
            details: []
        };
        
        // Détermination du type
        if (fileSizes.compression.isCompression) {
            conclusion.success = true;
            conclusion.isCompression = true;
            conclusion.summary = `COMPRESSION CONFIRMÉE - Ratio ${fileSizes.compression.ratio.toFixed(2)}:1`;
            
            conclusion.details.push(
                `Le fichier b3.hcv16 est bien plus petit que B3.mp4`,
                `Taille originale: ${fileSizes.original.sizeFormatted}`,
                `Taille compressée: ${fileSizes.compressed.sizeFormatted}`,
                `Ratio de compression: ${fileSizes.compression.ratio.toFixed(2)}:1`,
                `Réduction de taille: ${fileSizes.compression.reduction.toFixed(2)}%`,
                `Niveau de compression: ${compression.compressionLevel}`
            );
            
            if (compression.validation.isValid) {
                conclusion.details.push('La compression est valide et significative');
            }
            
            if (verification.metadataExists && verification.metadataConsistent) {
                conclusion.details.push('Les métadonnées sont cohérentes avec les tailles réelles');
            } else if (verification.metadataExists) {
                conclusion.details.push('Attention: incohérence détectée avec les métadonnées');
            }
            
        } else if (fileSizes.compression.isExpansion) {
            conclusion.isExpansion = true;
            conclusion.summary = `EXPANSION DÉTECTÉE - Ratio ${fileSizes.compression.ratio.toFixed(2)}:1`;
            
            conclusion.details.push(
                `Le fichier b3.hcv16 est PLUS GRAND que B3.mp4`,
                `Taille originale: ${fileSizes.original.sizeFormatted}`,
                `Taille compressée: ${fileSizes.compressed.sizeFormatted}`,
                `Ratio d'expansion: ${fileSizes.compression.ratio.toFixed(2)}:1`,
                `Augmentation de taille: ${Math.abs(fileSizes.compression.reduction).toFixed(2)}%`
            );
            
        } else {
            conclusion.summary = 'TAILLE IDENTIQUE - Pas de compression ni expansion';
            conclusion.details.push(
                'Les fichiers ont la même taille',
                `Taille: ${fileSizes.original.sizeFormatted}`
            );
        }
        
        this.results.conclusion = conclusion;
        
        console.log(`  Succès: ${conclusion.success ? 'OUI' : 'NON'}`);
        console.log(`  Type: ${conclusion.isCompression ? 'COMPRESSION' : (conclusion.isExpansion ? 'EXPANSION' : 'NEUTRE')}`);
        console.log(`  Résumé: ${conclusion.summary}`);
        console.log(`  Détails: ${conclusion.details.length} points`);
        
        for (const detail of conclusion.details) {
            console.log(`    ${detail}`);
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
        console.log('RAPPORT DE CONFIRMATION - COMPRESSION RÉELLE');
        console.log('='.repeat(60));
        
        console.log('TAILLES DES FICHIERS:');
        console.log(`  Original (B3.mp4): ${this.results.fileSizes?.original.sizeFormatted || 'Inconnue'}`);
        console.log(`  Compressé (b3.hcv16): ${this.results.fileSizes?.compressed.sizeFormatted || 'Inconnue'}`);
        
        if (this.results.fileSizes?.compression) {
            console.log(`  Ratio: ${this.results.fileSizes.compression.ratio.toFixed(2)}:1`);
            console.log(`  Réduction: ${this.results.fileSizes.compression.reduction.toFixed(2)}%`);
            console.log(`  Type: ${this.results.fileSizes.compression.isCompression ? 'COMPRESSION' : (this.results.fileSizes.compression.isExpansion ? 'EXPANSION' : 'NEUTRE')}`);
        }
        
        console.log('\nANALYSE DE LA COMPRESSION:');
        if (this.results.compressionAnalysis) {
            console.log(`  Niveau: ${this.results.compressionAnalysis.compressionLevel}`);
            console.log(`  Efficacité: ${this.results.compressionAnalysis.efficiency}`);
            console.log(`  Espace sauvé: ${this.results.compressionAnalysis.spaceSavedFormatted}`);
            console.log(`  Validation: ${this.results.compressionAnalysis.validation.isValid ? 'VALIDE' : 'INVALIDE'}`);
        }
        
        console.log('\nVÉRIFICATION:');
        if (this.results.verification) {
            console.log(`  Métadonnées: ${this.results.verification.metadataExists ? 'Disponibles' : 'Non disponibles'}`);
            if (this.results.verification.metadataExists) {
                console.log(`  Cohérence: ${this.results.verification.metadataConsistent ? 'OUI' : 'NON'}`);
            }
        }
        
        console.log('\nCONCLUSION:');
        if (this.results.conclusion) {
            console.log(`  Résumé: ${this.results.conclusion.summary}`);
            for (const detail of this.results.conclusion.details) {
                console.log(`  ${detail}`);
            }
        }
        
        console.log('='.repeat(60));
    }
}

// Exécution
if (require.main === module) {
    (async () => {
        const confirmation = new CompressionConfirmation();
        await confirmation.runConfirmation();
        confirmation.generateReport();
        
        // Sauvegarde
        try {
            const reportPath = path.resolve(__dirname, 'compression_confirmation.json');
            fs.writeFileSync(reportPath, JSON.stringify(confirmation.results, null, 2));
            console.log(`\nRapport sauvegardé dans: ${reportPath}`);
        } catch (error) {
            console.error('Erreur sauvegarde rapport:', error);
        }
    })();
}

module.exports = { CompressionConfirmation };
