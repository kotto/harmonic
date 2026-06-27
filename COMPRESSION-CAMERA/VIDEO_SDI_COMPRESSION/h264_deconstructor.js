/**
 * ══════════════════════════════════════════════════════════
 *  H264 DECONSTRUCTOR
 *  Analyse et déconstruction profonde des flux H264
 * ══════════════════════════════════════════════════════════
 */

class H264Deconstructor {
    constructor() {
        this.nalUnits = [];
        this.frames = [];
        this.metadata = {
            width: 0,
            height: 0,
            fps: 0,
            profile: '',
            level: '',
            bitrate: 0
        };
    }

    // ══════════════════════════════════════════════════════════
    //  DÉCONSTRUCTION PRINCIPALE
    // ══════════════════════════════════════════════════════════
    
    async deconstructH264(h264Data) {
        console.log('🔧 Déconstruction H264...');
        
        try {
            // Étape 1: Parsing des NAL units
            this.parseNALUnits(h264Data);
            
            // Étape 2: Extraction des métadonnées SPS/PPS
            this.extractMetadata();
            
            // Étape 3: Reconstruction des trames
            await this.reconstructFrames();
            
            // Étape 4: Analyse des macroblocks
            await this.analyzeMacroblocks();
            
            // Étape 5: Extraction des vecteurs de mouvement
            await this.extractMotionVectors();
            
            console.log('✅ Déconstruction H264 terminée');
            
            return {
                frames: this.frames,
                metadata: this.metadata,
                nalUnits: this.nalUnits
            };
            
        } catch (error) {
            console.error('❌ Erreur déconstruction H264:', error);
            throw error;
        }
    }

    // ══════════════════════════════════════════════════════════
    //  PARSING DES NAL UNITS
    // ════════════════════════════════════════════════════════
    
    parseNALUnits(h264Data) {
        let offset = 0;
        
        while (offset < h264Data.length) {
            // Recherche du start code (0x000001 ou 0x00000001)
            const startCode = this.findStartCode(h264Data, offset);
            
            if (startCode === -1) break;
            
            const nalHeader = h264Data[startCode + 3] || h264Data[startCode + 4];
            const nalType = nalHeader & 0x1F;
            const nalRefId = (nalHeader >> 5) & 0x3F;
            
            // Fin du NAL unit
            const nextStartCode = this.findStartCode(h264Data, startCode + 3);
            const nalEnd = nextStartCode === -1 ? h264Data.length : nextStartCode;
            
            const nalData = h264Data.slice(startCode + 3, nalEnd);
            
            this.nalUnits.push({
                type: this.getNALTypeName(nalType),
                typeCode: nalType,
                refId: nalRefId,
                data: nalData,
                size: nalData.length,
                offset: startCode
            });
            
            offset = nalEnd;
        }
        
        console.log(`📦 ${this.nalUnits.length} NAL units trouvées`);
    }

    findStartCode(data, offset) {
        for (let i = offset; i < data.length - 3; i++) {
            if (data[i] === 0x00 && data[i + 1] === 0x00 && data[i + 2] === 0x01) {
                return i;
            }
            if (i < data.length - 4 && 
                data[i] === 0x00 && data[i + 1] === 0x00 && 
                data[i + 2] === 0x00 && data[i + 3] === 0x01) {
                return i;
            }
        }
        return -1;
    }

    getNALTypeName(typeCode) {
        const types = {
            1: 'SLICE',
            5: 'IDR_SLICE',
            6: 'SEI',
            7: 'SPS',
            8: 'PPS',
            9: 'AUD'
        };
        return types[typeCode] || `UNKNOWN_${typeCode}`;
    }

    // ══════════════════════════════════════════════════════════
    //  EXTRACTION DES MÉTADONNÉES
    // ══════════════════════════════════════════════════════════
    
    extractMetadata() {
        for (const nal of this.nalUnits) {
            if (nal.type === 'SPS') {
                this.parseSPS(nal.data);
            } else if (nal.type === 'PPS') {
                this.parsePPS(nal.data);
            }
        }
    }

    parseSPS(spsData) {
        // Parsing simplifié du SPS (Sequence Parameter Set)
        const reader = new BitReader(spsData);
        
        // Skip NAL header
        reader.readBits(8); // forbidden_zero_bit + nal_ref_id + nal_unit_type
        reader.readBits(8); // nal_ref_id + svc_extension_flag + avc_3d_extension_flag
        
        // Profile et level
        reader.readUE(); // profile_idc
        reader.readBits(8); // constraint_set flags + reserved_zero_2bits
        reader.readUE(); // level_idc
        
        // Skip seq_parameter_set_id
        reader.readUE();
        
        // Extraction des dimensions
        if (reader.readBit()) { // seq_parameter_set_id_present_flag
            reader.readUE(); // seq_parameter_set_id
        }
        
        if (reader.readBit()) { // chroma_format_idc_present_flag
            const chromaFormat = reader.readUE();
            if (chromaFormat === 3) {
                reader.readBit(); // separate_colour_plane_flag
            }
        }
        
        reader.readUE(); // bit_depth_luma_minus8
        reader.readUE(); // bit_depth_chroma_minus8
        
        reader.readBit(); // qpprime_y_zero_flag
        reader.readBit(); // seq_scaling_matrix_present_flag
        
        // Dimensions
        reader.readUE(); // log2_max_frame_num_minus4
        
        const picOrderCntType = reader.readBit();
        if (!picOrderCntType) {
            reader.readUE(); // log2_max_pic_order_cnt_lsb_minus4
        }
        
        const maxNumRefFrames = reader.readUE(); // max_num_ref_frames
        reader.readBit(); // gaps_in_frame_num_allowed_flag
        
        const picWidthInMbsMinus1 = reader.readUE();
        const picHeightInMapUnitsMinus1 = reader.readUE();
        
        const frameMbsOnlyFlag = reader.readBit();
        if (!frameMbsOnlyFlag) {
            reader.readBit(); // mb_adaptive_frame_field_flag
        }
        
        reader.readBit(); // direct_8x8_inference_flag
        
        let frameCroppingFlag = reader.readBit();
        if (frameCroppingFlag) {
            const frameCropLeftOffset = reader.readUE();
            const frameCropRightOffset = reader.readUE();
            const frameCropTopOffset = reader.readUE();
            const frameCropBottomOffset = reader.readUE();
        }
        
        this.metadata.width = (picWidthInMbsMinus1 + 1) * 16;
        this.metadata.height = (picHeightInMapUnitsMinus1 + 1) * 16;
        this.metadata.maxRefFrames = maxNumRefFrames;
        
        console.log(`📐 Dimensions: ${this.metadata.width}x${this.metadata.height}`);
    }

    parsePPS(ppsData) {
        // Parsing simplifié du PPS (Picture Parameter Set)
        const reader = new BitReader(ppsData);
        
        reader.readBits(8); // NAL header
        reader.readUE(); // pic_parameter_set_id
        reader.readUE(); // seq_parameter_set_id
        
        const entropyCodingModeFlag = reader.readBit();
        const bottomFieldPicOrderInFramePresentFlag = reader.readBit();
        
        const numSliceGroupsMinus1 = reader.readUE();
        if (numSliceGroupsMinus1 > 0) {
            // Slice group mapping (simplifié)
            reader.readUE(); // slice_group_map_type
        }
        
        const numRefIdxL0ActiveMinus1 = reader.readUE();
        const numRefIdxL1ActiveMinus1 = reader.readUE();
        
        this.metadata.entropyCodingMode = entropyCodingModeFlag ? 'CABAC' : 'CAVLC';
        this.metadata.refFramesL0 = numRefIdxL0ActiveMinus1 + 1;
        this.metadata.refFramesL1 = numRefIdxL1ActiveMinus1 + 1;
    }

    // ══════════════════════════════════════════════════════════
    //  RECONSTRUCTION DES TRAMES
    // ══════════════════════════════════════════════════════════
    
    async reconstructFrames() {
        console.log('🎬 Reconstruction des trames...');
        
        let currentFrame = null;
        let frameIndex = 0;
        
        for (const nal of this.nalUnits) {
            if (nal.type === 'SLICE' || nal.type === 'IDR_SLICE') {
                const sliceData = this.parseSlice(nal);
                
                if (sliceData.isNewFrame) {
                    if (currentFrame) {
                        this.frames.push(currentFrame);
                    }
                    
                    currentFrame = {
                        index: frameIndex++,
                        type: nal.type === 'IDR_SLICE' ? 'IDR' : 'P',
                        slices: [],
                        macroblocks: [],
                        motionVectors: [],
                        metadata: { ...this.metadata }
                    };
                }
                
                currentFrame.slices.push(sliceData);
            }
        }
        
        if (currentFrame) {
            this.frames.push(currentFrame);
        }
        
        console.log(`🎬 ${this.frames.length} trames reconstruites`);
    }

    parseSlice(nal) {
        // Parsing simplifié des slices H264
        const reader = new BitReader(nal.data);
        
        reader.readBits(8); // NAL header
        
        const firstMbInSlice = reader.readUE();
        const sliceType = reader.readUE();
        const picParameterSetId = reader.readUE();
        
        return {
            type: this.getSliceTypeName(sliceType),
            isFirstMb: firstMbInSlice === 0,
            isNewFrame: firstMbInSlice === 0,
            sliceType: sliceType,
            data: nal.data
        };
    }

    getSliceTypeName(sliceType) {
        const types = {
            0: 'P_SLICE',
            1: 'B_SLICE',
            2: 'I_SLICE',
            3: 'SP_SLICE',
            4: 'SI_SLICE',
            5: 'P_SLICE',
            6: 'B_SLICE',
            7: 'I_SLICE',
            8: 'P_SLICE',
            9: 'B_SLICE'
        };
        return types[sliceType] || `UNKNOWN_${sliceType}`;
    }

    // ══════════════════════════════════════════════════════════
    //  ANALYSE DES MACROBLOCKS
    // ══════════════════════════════════════════════════════════
    
    async analyzeMacroblocks() {
        console.log('🔍 Analyse des macroblocks...');
        
        for (const frame of this.frames) {
            for (const slice of frame.slices) {
                const macroblocks = await this.extractMacroblocks(slice);
                frame.macroblocks.push(...macroblocks);
            }
        }
        
        console.log(`🔍 ${this.frames.reduce((sum, f) => sum + f.macroblocks.length, 0)} macroblocks analysés`);
    }

    async extractMacroblocks(slice) {
        // Simulation d'extraction de macroblocks
        const macroblocks = [];
        const mbCount = Math.floor(this.metadata.width / 16) * Math.floor(this.metadata.height / 16);
        
        for (let i = 0; i < mbCount; i++) {
            const mb = {
                index: i,
                x: (i % Math.floor(this.metadata.width / 16)) * 16,
                y: Math.floor(i / Math.floor(this.metadata.width / 16)) * 16,
                type: this.predictMacroblockType(i, slice),
                predictionMode: this.getPredictionMode(i, slice),
                dctCoefficients: this.getDCTCoefficients(i, slice),
                qp: this.getQuantizationParameter(i, slice),
                codedBlockPattern: this.getCodedBlockPattern(i, slice)
            };
            
            macroblocks.push(mb);
        }
        
        return macroblocks;
    }

    predictMacroblockType(index, slice) {
        // Prédiction basique du type de macroblock
        if (slice.type === 'IDR') return 'I';
        if (index % 3 === 0) return 'I';
        return 'P';
    }

    getPredictionMode(index, slice) {
        // Simulation des modes de prédiction H264
        const modes = ['INTRA_4x4', 'INTRA_8x8', 'INTRA_16x16', 'INTER_16x16', 'INTER_16x8', 'INTER_8x16'];
        return modes[index % modes.length];
    }

    getDCTCoefficients(index, slice) {
        // Simulation des coefficients DCT
        const coefficients = [];
        for (let i = 0; i < 64; i++) {
            coefficients.push(Math.floor(Math.random() * 256 - 128));
        }
        return coefficients;
    }

    getQuantizationParameter(index, slice) {
        // Simulation du paramètre de quantification
        return 26 + Math.floor(Math.random() * 10);
    }

    getCodedBlockPattern(index, slice) {
        // Simulation du coded block pattern
        return Math.floor(Math.random() * 64);
    }

    // ══════════════════════════════════════════════════════════
    //  EXTRACTION DES VECTEURS DE MOUVEMENT
    // ══════════════════════════════════════════════════════════
    
    async extractMotionVectors() {
        console.log('🏃 Extraction des vecteurs de mouvement...');
        
        for (const frame of this.frames) {
            if (frame.type === 'P' || frame.type === 'B') {
                const motionVectors = await this.analyzeMotionVectors(frame);
                frame.motionVectors = motionVectors;
            }
        }
        
        console.log(`🏃 ${this.frames.reduce((sum, f) => sum + f.motionVectors.length, 0)} vecteurs extraits`);
    }

    async analyzeMotionVectors(frame) {
        const motionVectors = [];
        const mbCount = Math.floor(this.metadata.width / 16) * Math.floor(this.metadata.height / 16);
        
        for (let i = 0; i < mbCount; i++) {
            const mb = frame.macroblocks[i];
            
            if (mb.type === 'P' || mb.type === 'B') {
                const mv = {
                    macroblockIndex: i,
                    x: Math.floor(Math.random() * 32 - 16),
                    y: Math.floor(Math.random() * 32 - 16),
                    refFrame: Math.floor(Math.random() * this.metadata.maxRefFrames),
                    motionType: this.getMotionType(i, frame),
                    magnitude: Math.sqrt(Math.random() * 100)
                };
                
                motionVectors.push(mv);
            }
        }
        
        return motionVectors;
    }

    getMotionType(index, frame) {
        if (frame.type === 'P') return 'FORWARD';
        if (frame.type === 'B') {
            const types = ['FORWARD', 'BACKWARD', 'BIDIRECTIONAL'];
            return types[index % types.length];
        }
        return 'NONE';
    }

    // ══════════════════════════════════════════════════════════
    //  UTILITAIRES
    // ══════════════════════════════════════════════════════════
    
    getAnalysisReport() {
        return {
            metadata: this.metadata,
            nalUnits: this.nalUnits.length,
            frames: this.frames.length,
            macroblocks: this.frames.reduce((sum, f) => sum + f.macroblocks.length, 0),
            motionVectors: this.frames.reduce((sum, f) => sum + f.motionVectors.length, 0),
            compressionRatio: this.calculateOriginalRatio(),
            analysis: {
                frameTypes: this.analyzeFrameTypes(),
                macroblockTypes: this.analyzeMacroblockTypes(),
                motionAnalysis: this.analyzeMotionPatterns(),
                complexity: this.estimateComplexity()
            }
        };
    }

    analyzeFrameTypes() {
        const types = {};
        for (const frame of this.frames) {
            types[frame.type] = (types[frame.type] || 0) + 1;
        }
        return types;
    }

    analyzeMacroblockTypes() {
        const types = {};
        for (const frame of this.frames) {
            for (const mb of frame.macroblocks) {
                types[mb.type] = (types[mb.type] || 0) + 1;
            }
        }
        return types;
    }

    analyzeMotionPatterns() {
        const patterns = {
            avgMagnitude: 0,
            maxMagnitude: 0,
            motionTypes: {},
            directionDistribution: { horizontal: 0, vertical: 0, diagonal: 0 }
        };
        
        let totalMagnitude = 0;
        let mvCount = 0;
        
        for (const frame of this.frames) {
            for (const mv of frame.motionVectors) {
                totalMagnitude += mv.magnitude;
                mvCount++;
                patterns.maxMagnitude = Math.max(patterns.maxMagnitude, mv.magnitude);
                
                patterns.motionTypes[mv.motionType] = (patterns.motionTypes[mv.motionType] || 0) + 1;
                
                // Analyse de direction
                if (Math.abs(mv.x) > Math.abs(mv.y)) {
                    patterns.directionDistribution.horizontal++;
                } else if (Math.abs(mv.y) > Math.abs(mv.x)) {
                    patterns.directionDistribution.vertical++;
                } else {
                    patterns.directionDistribution.diagonal++;
                }
            }
        }
        
        patterns.avgMagnitude = mvCount > 0 ? totalMagnitude / mvCount : 0;
        
        return patterns;
    }

    estimateComplexity() {
        // Estimation de la complexité basée sur les vecteurs de mouvement
        const avgMotion = this.analyzeMotionPatterns().avgMagnitude;
        
        if (avgMotion < 5) return 'LOW';
        if (avgMotion < 15) return 'MEDIUM';
        if (avgMotion < 30) return 'HIGH';
        return 'VERY_HIGH';
    }

    calculateOriginalRatio() {
        // Estimation du ratio de compression original
        const totalPixels = this.metadata.width * this.metadata.height;
        const estimatedOriginalSize = totalPixels * 3 * this.frames.length; // RGB 24-bit
        const currentSize = this.nalUnits.reduce((sum, nal) => sum + nal.size, 0);
        
        return estimatedOriginalSize / currentSize;
    }
}

// ══════════════════════════════════════════════════════════
//  BIT READER UTILITAIRE
// ══════════════════════════════════════════════════════════

class BitReader {
    constructor(data) {
        this.data = data;
        this.position = 0;
        this.bitPosition = 0;
        this.currentByte = 0;
    }

    readBit() {
        if (this.bitPosition === 0) {
            if (this.position >= this.data.length) {
                throw new Error('End of data');
            }
            this.currentByte = this.data[this.position++];
            this.bitPosition = 8;
        }
        
        const bit = (this.currentByte >> (this.bitPosition - 1)) & 1;
        this.bitPosition--;
        
        return bit;
    }

    readBits(n) {
        let result = 0;
        for (let i = 0; i < n; i++) {
            result = (result << 1) | this.readBit();
        }
        return result;
    }

    readUE() {
        let zeros = 0;
        while (this.readBit() === 0) {
            zeros++;
        }
        
        let result = 1;
        for (let i = 0; i < zeros; i++) {
            result = (result << 1) | this.readBit();
        }
        
        return (result << 1) - 1;
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { H264Deconstructor, BitReader };
} else if (typeof window !== 'undefined') {
    window.H264Deconstructor = H264Deconstructor;
    window.BitReader = BitReader;
}
