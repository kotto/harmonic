# SPÉCIFICATION FORMAT HCV16
## Container Binaire pour Compression Lossless Broadcast

### STRUCTURE GÉNÉRALE

```
Fichier .hcv16 :
┌─────────────────┐
│ Header Fixe     │ 256 bytes
├─────────────────┤
│ Grain Model     │ Variable (64-1024 bytes)
├─────────────────┤
│ Frame Index     │ Variable (frames × 16 bytes)
├─────────────────┤
│ Audio Stream    │ Variable (optionnel)
├─────────────────┤
│ Frame Data      │ Variable (données compressées)
├─────────────────┤
│ CRC32 Global    │ 4 bytes
└─────────────────┘
```

### HEADER FIXE (256 bytes)

```c
typedef struct {
    uint32_t magic;           // 'HCV1' (0x31564348)
    uint16_t version_major;   // Version majeure (1)
    uint16_t version_minor;   // Version mineure (6)
    
    // Propriétés vidéo
    uint16_t width;           // Largeur frame
    uint16_t height;          // Hauteur frame
    uint32_t frame_count;     // Nombre total frames
    uint32_t fps_numerator;   // FPS numérateur
    uint32_t fps_denominator; // FPS dénominateur
    
    // Configuration compression
    uint8_t compression_mode; // 0=FAST, 1=SDI, 2=ARCHIVE
    uint8_t bit_depth;        // Profondeur bits (10)
    uint8_t chroma_format;    // Format chroma (1=4:2:2)
    uint8_t color_space;      // Espace couleur (0=YCbCr)
    
    // Modèle de grain
    uint16_t grain_model_size; // Taille modèle grain
    uint16_t grain_model_type; // Type modèle (0=global, 1=adaptatif)
    
    // Index et métadonnées
    uint64_t frame_index_offset; // Offset index frames
    uint64_t audio_offset;       // Offset données audio
    uint64_t video_offset;       // Offset données vidéo
    
    // Checksums et validation
    uint32_t header_crc32;    // CRC32 du header
    uint32_t metadata_crc32;  // CRC32 métadonnées
    
    // Réservé pour extensions futures
    uint8_t reserved[200];    // Padding à 256 bytes
} hcv16_header_t;
```

### MODÈLE DE GRAIN

```c
typedef struct {
    uint16_t model_type;      // Type modèle
    uint16_t parameters_count; // Nombre paramètres
    
    union {
        struct {              // Modèle global simple
            float sigma;      // Écart-type grain
            float correlation; // Corrélation spatiale
        } global;
        
        struct {              // Modèle adaptatif
            uint16_t zones_count; // Nombre zones
            struct {
                uint16_t x, y, w, h; // Zone rectangle
                float sigma;         // Sigma local
                float pattern[16];   // Pattern grain 4×4
            } zones[64];
        } adaptive;
    } params;
} hcv16_grain_model_t;
```

### INDEX FRAMES

```c
typedef struct {
    uint64_t offset;          // Offset données frame
    uint32_t compressed_size; // Taille compressée
    uint32_t original_size;   // Taille originale
    uint16_t frame_type;      // Type frame (I/P)
    uint16_t quality_metric;  // Métrique qualité
} hcv16_frame_index_t;
```

### DONNÉES FRAME

```c
typedef struct {
    uint32_t frame_number;    // Numéro frame
    uint16_t compression_flags; // Flags compression
    uint16_t prediction_mode; // Mode prédiction
    
    // Tailles composantes
    uint32_t y_compressed_size;
    uint32_t cb_compressed_size;
    uint32_t cr_compressed_size;
    uint32_t grain_compressed_size;
    
    // Données compressées
    uint8_t y_data[];         // Données Y compressées
    uint8_t cb_data[];        // Données Cb compressées
    uint8_t cr_data[];        // Données Cr compressées
    uint8_t grain_data[];     // Données grain compressées
    
    uint32_t frame_crc32;     // CRC32 frame
} hcv16_frame_data_t;
```