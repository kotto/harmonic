/**
 * hcv2_ofx.c — OpenFX plugin for DaVinci Resolve
 * ================================================
 * Plugin OpenFX (OFX) qui décode les fichiers .hcv2
 * dans le Color Page et Fusion de DaVinci Resolve.
 *
 * Architecture :
 *   - Enregistre une classe OFX "HCV2.Pro.Decoder"
 *   - Le plugin apparaît comme un node dans Fusion
 *   - Accepte un fichier .hcv2 en entrée (string param)
 *   - Sort une image RGB décompressée
 *
 * Compilation (avec OpenFX SDK) :
 *   gcc -O2 -shared -fPIC -o HCV2Decoder.ofx.bundle/Contents/Linux-x86_64/HCV2Decoder.ofx \
 *       hcv2_ofx.c hcv2_av.c -I/opt/openfx/Support -lz -lm
 *
 * Installation :
 *   Linux : ~/.local/share/DaVinciResolve/Fusion/Plugins/HCV2Decoder.ofx.bundle
 *   Win   : %PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Plugins\HCV2Decoder.ofx.bundle
 *   Mac   : /Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Plugins/HCV2Decoder.ofx.bundle
 *
 * Note : Ce fichier est un squelette fonctionnel. L'intégration OFX
 * complète nécessite le SDK OpenFX (ofxCore.h, ofxImageEffect.h).
 */

#ifdef HAVE_OFX_SDK
#include "ofxCore.h"
#include "ofxImageEffect.h"
#include "ofxOpenGLRender.h"
#include "ofxMemory.h"
#else
/* Déclarations minimales pour compilation hors SDK */
typedef void* OfxImageEffectHandle;
typedef void* OfxPropertySetHandle;
typedef void* OfxImageEffectSuiteV1;
typedef int OfxStatus;
#define kOfxImageEffectPluginApi "OfxImageEffectPluginAPI"
#define kOfxImageEffectPluginApiVersion 1
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <complex.h>
#include <zlib.h>

/* Import du décodeur .hcv2 */
extern int hcv2_decode(const uint8_t *blob, int blob_len,
                       uint8_t *out, int *out_w, int *out_h);
extern int hcv2_probe(const uint8_t *buf, int buf_size);

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

/* ─── Structure de l'instance du plugin ────────────────────────────── */

typedef struct {
    void *userData;
    char input_path[4096];    /* Chemin du fichier .hcv2 */
    int width, height;        /* Dimensions de l'image décodée */
    uint8_t *decoded;         /* Image décodée en RGB */
    int decoded_size;
} HCV2Instance;

/* ─── Fonctions de l'instance ──────────────────────────────────────── */

static HCV2Instance *instance_new(void) {
    HCV2Instance *inst = (HCV2Instance *)calloc(1, sizeof(HCV2Instance));
    if (inst) {
        inst->width = 0;
        inst->height = 0;
        inst->decoded = NULL;
        inst->decoded_size = 0;
    }
    return inst;
}

static void instance_free(HCV2Instance *inst) {
    if (!inst) return;
    if (inst->decoded) free(inst->decoded);
    free(inst);
}

/* ─── Lecture d'un fichier .hcv2 ───────────────────────────────────── */

static int load_hcv2_file(HCV2Instance *inst, const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) return -1;
    
    fseek(f, 0, SEEK_END);
    long len = ftell(f);
    fseek(f, 0, SEEK_SET);
    
    uint8_t *blob = (uint8_t *)malloc(len);
    if (!blob) { fclose(f); return -1; }
    fread(blob, 1, len, f);
    fclose(f);
    
    /* Décoder */
    if (inst->decoded) free(inst->decoded);
    inst->decoded = (uint8_t *)malloc(8192 * 8192 * 3);
    int w, h;
    if (hcv2_decode(blob, (int)len, inst->decoded, &w, &h) != 0) {
        free(blob);
        free(inst->decoded);
        inst->decoded = NULL;
        return -1;
    }
    inst->width = w;
    inst->height = h;
    inst->decoded_size = w * h * 3;
    strncpy(inst->input_path, path, sizeof(inst->input_path) - 1);
    
    free(blob);
    return 0;
}

/* ─── API OpenFX (squelette) ───────────────────────────────────────── */

OfxStatus ofxMainEntry(const char *action, const void *handle,
                       OfxPropertySetHandle inArgs, OfxPropertySetHandle outArgs) {
    (void)handle; (void)inArgs; (void)outArgs;
    
    if (strcmp(action, "Load") == 0) {
        return 0;
    }
    if (strcmp(action, "Unload") == 0) {
        return 0;
    }
    if (strcmp(action, "Describe") == 0) {
        fprintf(stderr, "HCV2 Pro OpenFX plugin — describe\n");
        return 0;
    }
    if (strcmp(action, "DescribeInContext") == 0) {
        return 0;
    }
    if (strcmp(action, "CreateInstance") == 0) {
        HCV2Instance *inst = instance_new();
        /* Stocker l'instance dans le handle */
        return 0;
    }
    if (strcmp(action, "DestroyInstance") == 0) {
        /* Récupérer l'instance et libérer */
        return 0;
    }
    if (strcmp(action, "GetRegionOfDefinition") == 0) {
        return 0;
    }
    if (strcmp(action, "GetClipPreferences") == 0) {
        return 0;
    }
    if (strcmp(action, "GetTimeDomain") == 0) {
        return 0;
    }
    if (strcmp(action, "IsIdentity") == 0) {
        return 0;
    }
    if (strcmp(action, "Render") == 0) {
        /* Le rendu de l'image .hcv2 vers la sortie OFX */
        return 0;
    }
    return 0;
}

/* ─── Point d'entrée CLI pour test ─────────────────────────────────── */

#ifdef BUILD_CLI
int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "HCV2 Pro OpenFX — test\n");
        fprintf(stderr, "Usage: %s <input.hcv2> <output.ppm>\n", argv[0]);
        return 1;
    }
    
    HCV2Instance *inst = instance_new();
    if (load_hcv2_file(inst, argv[1]) != 0) {
        fprintf(stderr, "Erreur chargement\n");
        instance_free(inst);
        return 1;
    }
    
    FILE *f = fopen(argv[2], "wb");
    if (!f) { instance_free(inst); return 1; }
    fprintf(f, "P6\n%d %d\n255\n", inst->width, inst->height);
    fwrite(inst->decoded, 1, inst->decoded_size, f);
    fclose(f);
    fprintf(stderr, "✅ %s → %s (%dx%d)\n", argv[1], argv[2],
            inst->width, inst->height);
    
    instance_free(inst);
    return 0;
}
#endif /* BUILD_CLI */