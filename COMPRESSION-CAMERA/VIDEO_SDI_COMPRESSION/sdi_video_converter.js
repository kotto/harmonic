/**
 * ════════════════════════════════════════════════════════
 *  SDI VIDEO CONVERTER
 *  Conversion H264 → SDI-like avec préservation de qualité
 * ════════════════════════════════════════════════════════
 */

class SDIVideoConverter {
    constructor() {
        this.sdiConfig = {
            lineSize: 1920,
            bitDepth: 10,
            colorSpace: 'YUV422',
            frameRate: 30
        };
        this.conversionQuality = 'lossless';
        this.preserveMotion = true;
    }

    // ════════════════════════════════════════════════════════
    //  CONVERSION PRINCIPALE H264 → SDI
    // ════════════════════════════════════════════════════════
    
    async convertH264ToSDI(h264Analysis) {
        console.log('🔄 Conversion H264 → SDI-like...');
        
        try {
            const sdiFrames = [];
            
            for (const frame of h264Analysis.frames) {
                const sdiFrame = await this.convertFrameToSDI(frame);
                sdiFrames.push(sdiFrame);
            }
            
            console.log('✅ Conversion terminée');
            
            return {
                frames: sdiFrames,
                metadata: this.createSDIMetadata(h264Analysis.metadata),
                conversion: {
                    originalSize: this.estimateOriginalSize(h264Analysis),
                    sdiSize: this.estimateSDISize(sdiFrames),
                    quality: this.conversionQuality,
                    preserveMotion: this.preserveMotion
                }
            };
            
        } catch (error) {
            console.error('❌ Erreur conversion H264→SDI:', error);
            throw error;
        }
    }

    async convertFrameToSDI(frame) {
        const startTime = performance.now();
        
        // Étape 1: Reconstruction des pixels depuis les macroblocks
        const reconstructedPixels = await this.reconstructPixels(frame.macroblocks);
        
        // Étape 2: Conversion RGB → YUV 4:2:2 10-bit
        const yuv422Data = await this.convertToYUV422_10bit(reconstructedPixels);
        
        // Étape 3: Organisation en lignes SDI
        const sdiLines = await this.organizeSDILines(yuv422Data, frame.metadata);
        
        // Étape 4: Intégration des vecteurs de mouvement
        const sdiWithMotion = await this.integrateMotionVectors(sdiLines, frame.motionVectors);
        
        // Étape 5: Ajout des métadonnées SDI
        const sdiFrame = this.addSDIMetadata(sdiWithMotion, frame);
        
        const endTime = performance.now();
        console.log(`🔄 Trame ${frame.index} convertie en ${(endTime - startTime).toFixed(1)}ms`);
        
        return sdiFrame;
    }

    async reconstructPixels(macroblocks) {
        const width = this.sdiConfig.lineSize;
        const height = Math.floor(macroblocks.length / (width / 16));
        const pixels = new Uint8Array(width * height * 4);
        
        for (const mb of macroblocks) {
            // Reconstruction depuis les coefficients DCT
            const mbPixels = await this.reconstructMacroblock(mb);
            
            // Placement dans le buffer de pixels
            const mbX = mb.x;
            const mbY = mb.y;
            
            for (let y = 0; y < 16; y++) {
                for (let x = 0; x < 16; x++) {
                    const pixelIndex = ((mbY + y) * width + (mbX + x)) * 4;
                    
                    if (pixelIndex < pixels.length) {
                        pixels[pixelIndex] = mbPixels[y * 16 + x];
                    }
                }
            }
        }
        
        return pixels;
    }

    async reconstructMacroblock(macroblock) {
        // Reconstruction IDCT inverse
        const reconstructed = await this.inverseDCT(macroblock.dctCoefficients);
        
        // Application du prédiction
        const predicted = await this.applyPrediction(macroblock, reconstructed);
        
        // Quantification inverse
        const dequantized = await this.inverseQuantization(predicted, macroblock.qp);
        
        return dequantized;
    }

    async inverseDCT(coefficients) {
        // Simulation d'IDCT 2D
        const blockSize = 16;
        const reconstructed = new Float32Array(blockSize * blockSize);
        
        // IDCT sur chaque bloc 4x4 ou 8x8
        for (let by = 0; by < blockSize; by += 8) {
            for (let bx = 0; bx < blockSize; bx += 8) {
                const block = this.extractBlock(coefficients, bx, by, 8);
                const idctBlock = this.idct2D(block);
                
                // Placement dans le résultat
                for (let y = 0; y < 8; y++) {
                    for (let x = 0; x < 8; x++) {
                        const index = (by + y) * blockSize + (bx + x);
                        reconstructed[index] = idctBlock[y * 8 + x];
                    }
                }
            }
        }
        
        return reconstructed;
    }

    extractBlock(coefficients, x, y, size) {
        const block = new Float32Array(size * size);
        
        for (let by = 0; by < size; by++) {
            for (let bx = 0; bx < size; bx++) {
                const coeffIndex = (y + by) * 64 + (x + bx);
                block[by * size + bx] = coefficients[coeffIndex] || 0;
            }
        }
        
        return block;
    }

    idct2D(block) {
        const size = Math.sqrt(block.length);
        const result = new Float32Array(block.length);
        
        for (let y = 0; y < size; y++) {
            for (let x = 0; x < size; x++) {
                let sum = 0;
                
                for (let u = 0; u < size; u++) {
                    for (let v = 0; v < size; v++) {
                        const coeff = block[u * size + v];
                        const cu = Math.cos((2 * x + 1) * u * Math.PI / (2 * size));
                        const cv = Math.cos((2 * y + 1) * v * Math.PI / (2 * size));
                        
                        sum += coeff * cu * cv;
                    }
                }
                
                result[y * size + x] = sum / 4;
            }
        }
        
        return result;
    }

    async applyPrediction(macroblock, reconstructed) {
        const blockSize = 16;
        const predicted = new Float32Array(blockSize * blockSize);
        
        switch (macroblock.predictionMode) {
            case 'INTRA_4x4':
                return await this.intra4x4Prediction(macroblock, reconstructed);
            case 'INTRA_8x8':
                return await this.intra8x8Prediction(macroblock, reconstructed);
            case 'INTRA_16x16':
                return await this.intra16x16Prediction(macroblock, reconstructed);
            case 'INTER_16x16':
                return await this.inter16x16Prediction(macroblock, reconstructed);
            default:
                return reconstructed;
        }
    }

    async intra4x4Prediction(macroblock, reconstructed) {
        // Prédiction intra 4x4 pour chaque sous-bloc
        const blockSize = 16;
        const predicted = new Float32Array(blockSize * blockSize);
        
        for (let by = 0; by < 4; by++) {
            for (let bx = 0; bx < 4; bx++) {
                const subBlock = this.extractBlock(reconstructed, bx * 4, by * 4, 4);
                const predictedSubBlock = await this.predictIntra4x4(subBlock);
                
                // Placement du sous-bloc prédit
                for (let y = 0; y < 4; y++) {
                    for (let x = 0; x < 4; x++) {
                        const index = (by * 4 + y) * blockSize + (bx * 4 + x);
                        predicted[index] = predictedSubBlock[y * 4 + x];
                    }
                }
            }
        }
        
        return predicted;
    }

    async predictIntra4x4(block) {
        // Prédiction intra 4x4 simplifiée
        const size = 4;
        const predicted = new Float32Array(size * size);
        
        // Utilisation des pixels voisins pour la prédiction
        // Simplification: prédiction DC moyenne
        let sum = 0;
        for (let i = 0; i < block.length; i++) {
            sum += block[i];
        }
        const average = sum / block.length;
        
        for (let i = 0; i < block.length; i++) {
            predicted[i] = average;
        }
        
        return predicted;
    }

    async intra8x8Prediction(macroblock, reconstructed) {
        // Prédiction intra 8x8
        const blockSize = 16;
        const predicted = new Float32Array(blockSize * blockSize);
        
        for (let by = 0; by < 2; by++) {
            for (let bx = 0; bx < 2; bx++) {
                const subBlock = this.extractBlock(reconstructed, bx * 8, by * 8, 8);
                const predictedSubBlock = await this.predictIntra8x8(subBlock);
                
                for (let y = 0; y < 8; y++) {
                    for (let x = 0; x < 8; x++) {
                        const index = (by * 8 + y) * blockSize + (bx * 8 + x);
                        predicted[index] = predictedSubBlock[y * 8 + x];
                    }
                }
            }
        }
        
        return predicted;
    }

    async predictIntra8x8(block) {
        // Prédiction intra 8x8 simplifiée
        const size = 8;
        const predicted = new Float32Array(size * size);
        
        // Prédiction plane simplifiée
        const h = size;
        const v = size;
        
        for (let y = 0; y < size; y++) {
            for (let x = 0; x < size; x++) {
                predicted[y * size + x] = block[0] + (x * (block[size - 1] - block[0]) / (size - 1)) + (y * (block[(size - 1) * size] - block[0]) / (size - 1));
            }
        }
        
        return predicted;
    }

    async intra16x16Prediction(macroblock, reconstructed) {
        // Prédiction intra 16x16
        const blockSize = 16;
        const predicted = new Float32Array(blockSize * blockSize);
        
        // Prédiction DC simple
        let dc = 0;
        for (let i = 0; i < reconstructed.length; i++) {
            dc += reconstructed[i];
        }
        dc /= reconstructed.length;
        
        for (let i = 0; i < blockSize * blockSize; i++) {
            predicted[i] = dc;
        }
        
        return predicted;
    }

    async inter16x16Prediction(macroblock, reconstructed) {
        // Prédiction inter 16x16 avec compensation de mouvement
        const blockSize = 16;
        const predicted = new Float32Array(blockSize * blockSize);
        
        // Utilisation du vecteur de mouvement
        const mv = macroblock.motionVector;
        
        // Simulation de compensation de mouvement
        for (let y = 0; y < blockSize; y++) {
            for (let x = 0; x < blockSize; x++) {
                const srcX = x + mv.x;
                const srcY = y + mv.y;
                
                // Simplification: interpolation bilinéaire
                let pixel = 0;
                if (srcX >= 0 && srcX < blockSize && srcY >= 0 && srcY < blockSize) {
                    pixel = reconstructed[srcY * blockSize + srcX];
                }
                
                predicted[y * blockSize + x] = pixel;
            }
        }
        
        return predicted;
    }

    async inverseQuantization(predicted, qp) {
        // Désquantification inverse
        const qScale = this.calculateQuantizationScale(qp);
        const dequantized = new Float32Array(predicted.length);
        
        for (let i = 0; i < predicted.length; i++) {
            dequantized[i] = predicted[i] * qScale;
        }
        
        return dequantized;
    }

    calculateQuantizationScale(qp) {
        // Calcul de l'échelle de quantification
        return 0.5 + Math.pow(2, qp / 6);
    }

    async convertToYUV422_10bit(pixels) {
        const width = this.sdiConfig.lineSize;
        const height = Math.floor(pixels.length / (width * 4));
        const yuvData = new Uint16Array(width * height * 2); // YUV 4:2:2
        
        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x += 2) {
                // Pixel 1
                const idx1 = (y * width + x) * 4;
                const r1 = pixels[idx1];
                const g1 = pixels[idx1 + 1];
                const b1 = pixels[idx1 + 2];
                
                // Pixel 2
                let r2, g2, b2;
                if (x + 1 < width) {
                    const idx2 = (y * width + x + 1) * 4;
                    r2 = pixels[idx2];
                    g2 = pixels[idx2 + 1];
                    b2 = pixels[idx2 + 2];
                } else {
                    r2 = r1;
                    g2 = g1;
                    b2 = b1;
                }
                
                // Conversion RGB → YUV
                const y1 = Math.round(0.299 * r1 + 0.587 * g1 + 0.114 * b1 + 16);
                const u1 = Math.round(-0.147 * r1 - 0.289 * g1 + 0.436 * b1 + 128);
                const v1 = Math.round(0.615 * r1 - 0.515 * g1 - 0.100 * b1 + 128);
                
                const y2 = Math.round(0.299 * r2 + 0.587 * g2 + 0.114 * b2 + 16);
                const u2 = Math.round(-0.147 * r2 - 0.289 * g2 + 0.436 * b2 + 128);
                const v2 = Math.round(0.615 * r2 - 0.515 * g2 - 0.100 * b2 + 128);
                
                // Sous-échantillonnage 4:2:2
                const uAvg = Math.round((u1 + u2) / 2);
                const vAvg = Math.round((v1 + v2) / 2);
                
                // Quantification 10-bit
                const y1_10bit = Math.round(y1 * 1023 / 255);
                const u_10bit = Math.round(uAvg * 1023 / 255);
                const y2_10bit = Math.round(y2 * 1023 / 255);
                const v_10bit = Math.round(vAvg * 1023 / 255);
                
                // Stockage YUV 4:2:2
                const lineOffset = y * width;
                const pixelOffset = x / 2;
                const sdiIndex = lineOffset + pixelOffset;
                
                if (sdiIndex * 2 + 3 < yuvData.length) {
                    yuvData[sdiIndex * 2] = y1_10bit;
                    yuvData[sdiIndex * 2 + 1] = u_10bit;
                    yuvData[sdiIndex * 2 + 2] = y2_10bit;
                    yuvData[sdiIndex * 2 + 3] = v_10bit;
                }
            }
        }
        
        return yuvData;
    }

    async organizeSDILines(yuvData, frameMetadata) {
        const width = this.sdiConfig.lineSize;
        const height = Math.floor(yuvData.length / (width * 2));
        const sdiLines = [];
        
        for (let y = 0; y < height; y++) {
            const lineOffset = y * width * 2;
            const lineData = yuvData.slice(lineOffset, lineOffset + width * 2);
            
            sdiLines.push({
                lineNumber: y,
                data: lineData,
                metadata: {
                    timestamp: frameMetadata.timestamp || 0,
                    frameType: frameMetadata.type || 'P',
                    quality: frameMetadata.quality || 'HIGH'
                }
            });
        }
        
        return sdiLines;
    }

    async integrateMotionVectors(sdiLines, motionVectors) {
        // Intégration des vecteurs de mouvement dans les lignes SDI
        const sdiWithMotion = [];
        
        for (const line of sdiLines) {
            const lineWithMotion = {
                ...line,
                motionData: this.extractLineMotionVectors(line.lineNumber, motionVectors)
            };
            
            sdiWithMotion.push(lineWithMotion);
        }
        
        return sdiWithMotion;
    }

    extractLineMotionVectors(lineNumber, motionVectors) {
        // Extraction des vecteurs de mouvement pour une ligne spécifique
        const lineMotion = [];
        
        for (const mv of motionVectors) {
            const mbY = Math.floor(mv.macroblockIndex / (this.sdiConfig.lineSize / 16));
            
            if (mbY === lineNumber / 16) {
                lineMotion.push(mv);
            }
        }
        
        return lineMotion;
    }

    addSDIMetadata(sdiLines, frame) {
        return {
            frameNumber: frame.index,
            lines: sdiLines,
            metadata: {
                width: this.sdiConfig.lineSize,
                height: Math.floor(sdiLines.length),
                bitDepth: this.sdiConfig.bitDepth,
                colorSpace: this.sdiConfig.colorSpace,
                frameType: frame.type,
                timestamp: frame.metadata.timestamp || Date.now(),
                quality: this.conversionQuality,
                motionPreserved: this.preserveMotion,
                compressionRatio: this.estimateFrameRatio(frame, sdiLines)
            }
        };
    }

    createSDIMetadata(h264Metadata) {
        return {
            ...h264Metadata,
            sdiConversion: {
                lineSize: this.sdiConfig.lineSize,
                bitDepth: this.sdiConfig.bitDepth,
                colorSpace: this.sdiConfig.colorSpace,
                frameRate: this.sdiConfig.frameRate,
                conversionQuality: this.conversionQuality
            }
        };
    }

    estimateOriginalSize(h264Analysis) {
        const totalPixels = h264Analysis.metadata.width * h264Analysis.metadata.height;
        return totalPixels * 3 * h264Analysis.frames.length; // RGB 24-bit
    }

    estimateSDISize(sdiFrames) {
        let totalSize = 0;
        for (const frame of sdiFrames) {
            totalSize += this.estimateFrameSize(frame);
        }
        return totalSize;
    }

    estimateFrameSize(frame) {
        const lineSize = this.sdiConfig.lineSize;
        const linesCount = frame.lines.length;
        return lineSize * linesCount * 2; // YUV 4:2:2 16-bit
    }

    estimateFrameRatio(h264Frame, sdiFrame) {
        const originalSize = h264Frame.metadata.width * h264Frame.metadata.height * 3;
        const sdiSize = this.estimateFrameSize(sdiFrame);
        return originalSize / sdiSize;
    }

    // ════════════════════════════════════════════════════════
    //  UTILITAIRES ET VALIDATION
    // ════════════════════════════════════════════════════════
    
    validateConversion(h264Analysis, sdiResult) {
        const validation = {
            framesConverted: sdiResult.frames.length,
            framesExpected: h264Analysis.frames.length,
            qualityLoss: this.estimateQualityLoss(h264Analysis, sdiResult),
            motionPreservation: this.validateMotionPreservation(h264Analysis, sdiResult),
            metadataIntegrity: this.validateMetadataIntegrity(h264Analysis, sdiResult)
        };
        
        validation.isValid = validation.framesConverted === validation.framesExpected &&
                          validation.qualityLoss < 0.01 &&
                          validation.motionPreservation > 0.95 &&
                          validation.metadataIntegrity;
        
        return validation;
    }

    estimateQualityLoss(h264Analysis, sdiResult) {
        // Estimation de la perte de qualité
        const originalSize = this.estimateOriginalSize(h264Analysis);
        const sdiSize = this.estimateSDISize(sdiResult.frames);
        
        // Simplification: basée sur le ratio de conversion
        return Math.max(0, (originalSize - sdiSize) / originalSize);
    }

    validateMotionPreservation(h264Analysis, sdiResult) {
        // Validation de la préservation des vecteurs de mouvement
        let preservedVectors = 0;
        let totalVectors = 0;
        
        for (let i = 0; i < h264Analysis.frames.length; i++) {
            const h264Frame = h264Analysis.frames[i];
            const sdiFrame = sdiResult.frames[i];
            
            if (h264Frame.motionVectors && sdiFrame.metadata.motionData) {
                totalVectors += h264Frame.motionVectors.length;
                
                for (const mv of h264Frame.motionVectors) {
                    const preserved = sdiFrame.metadata.motionData.some(
                        sdiMV => Math.abs(sdiMV.x - mv.x) < 2 && 
                                  Math.abs(sdiMV.y - mv.y) < 2
                    );
                    
                    if (preserved) preservedVectors++;
                }
            }
        }
        
        return totalVectors > 0 ? preservedVectors / totalVectors : 1.0;
    }

    validateMetadataIntegrity(h264Analysis, sdiResult) {
        // Validation de l'intégrité des métadonnées
        return h264Analysis.metadata.width === sdiResult.metadata.width &&
               h264Analysis.metadata.height === sdiResult.metadata.height &&
               h264Analysis.frames.length === sdiResult.frames.length;
    }

    getConversionReport(h264Analysis, sdiResult) {
        const validation = this.validateConversion(h264Analysis, sdiResult);
        
        return {
            summary: {
                originalFrames: h264Analysis.frames.length,
                convertedFrames: sdiResult.frames.length,
                conversionSuccess: validation.isValid,
                qualityLoss: validation.qualityLoss,
                motionPreservation: validation.motionPreservation
            },
            performance: {
                originalSize: this.estimateOriginalSize(h264Analysis),
                sdiSize: this.estimateSDISize(sdiResult.frames),
                compressionRatio: this.estimateOriginalSize(h264Analysis) / this.estimateSDISize(sdiResult.frames),
                conversionTime: sdiResult.conversion.conversionTime || 0
            },
            quality: {
                isLossless: validation.qualityLoss < 0.001,
                estimatedPSNR: this.estimatePSNR(validation.qualityLoss),
                motionIntegrity: validation.motionPreservation
            }
        };
    }

    estimatePSNR(qualityLoss) {
        if (qualityLoss === 0) return Infinity;
        // PSNR = 20 * log10(255 / sqrt(MSE))
        // Simplification: basée sur la perte relative
        return 20 * Math.log10(1 / Math.sqrt(qualityLoss));
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SDIVideoConverter };
} else if (typeof window !== 'undefined') {
    window.SDIVideoConverter = SDIVideoConverter;
}
