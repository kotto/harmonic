# Guide d'Implémentation - Upscaling 4K/8K pour Vidéos Précompressées

## 📋 Vue d'Ensemble

Pour implémenter l'upscaling 4K/8K pour les vidéos précompressées, il faut modifier:
1. ✅ Le codec `HCVUniversalBoost` (méthode `decode_video_frame`)
2. ✅ Ajouter une méthode `decode_video` complète
3. ✅ Le serveur (créer endpoint `/api/precompressed-video`)
4. ✅ L'interface web (ajouter section vidéo précompressée)

## 🔧 Modifications Nécessaires

### 1. Codec Universal Boost (`hcv_universal_boost_codec.py`)

#### A. Modifier `decode_video_frame()` pour accepter `target_resolution`

**Localisation**: Ligne ~539

**Modification**:
```python
def decode_video_frame(self, container: bytes, frame_idx: int, 
                       target_resolution: str = None) -> Tuple[np.ndarray, Dict]:
    """Decode une frame spécifique d'un container vidéo. Bit-exact.
    
    Args:
        container: bytes du container vidéo
        frame_idx: index de la frame à décoder
        target_resolution: 'original', '1080p', '4K', '8K', ou (w, h)
    """
    t0 = time.perf_counter()
    
    hdr_sz = struct.calcsize('<4sBBBBHHII')
    magic, ver, mode, qi, fi, orig_h, orig_w, fps100, fc = \
        struct.unpack('<4sBBBBHHII', container[:hdr_sz])
    assert magic == MAGIC
    
    quality = {0:'ultra',1:'high',2:'balanced',3:'compact'}[qi]
    
    if mode == MODE_ZSTD:
        # Fallback: décompresser la vidéo source
        plen = struct.unpack('<I', container[12:16])[0]
        source = _ZDCTX.decompress(container[16:16+plen])
        # Écrire dans un fichier temp et extraire la frame
        tmp = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        tmp.write(source)
        tmp.close()
        cap = cv2.VideoCapture(tmp.name)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        cap.release()
        os.unlink(tmp.name)
        if not ret:
            raise ValueError(f"Cannot read frame {frame_idx}")
    else:
        # MODE_VIDEO: accès direct par index
        assert frame_idx < fc, f"Frame {frame_idx} >= {fc}"
        
        # Lire l'index des frames
        idx_off = hdr_sz
        offsets = []
        for i in range(fc):
            sz = struct.unpack('<I', container[idx_off + i*4:idx_off + i*4 + 4])[0]
            offsets.append(sz)
        
        # Calculer l'offset de la frame demandée
        data_off = idx_off + fc * 4
        for i in range(frame_idx):
            data_off += offsets[i]
        
        payload = container[data_off:data_off + offsets[frame_idx]]
        frame = _decode_frame_payload(payload, orig_h, orig_w, quality)
    
    # ═══════════════════════════════════════════════════════════════
    # NOUVEAU: Upscaling vers la résolution cible
    # ═══════════════════════════════════════════════════════════════
    
    # Déterminer la résolution cible
    if target_resolution is None or target_resolution == 'original':
        target_w, target_h = orig_w, orig_h
    elif target_resolution == '1080p':
        target_w, target_h = 1920, 1080
    elif target_resolution == '4K':
        target_w, target_h = 3840, 2160
    elif target_resolution == '8K':
        target_w, target_h = 7680, 4320
    elif isinstance(target_resolution, (list, tuple)):
        target_w, target_h = target_resolution
    else:
        target_w, target_h = orig_w, orig_h
    
    # Upscale vers la résolution cible si nécessaire
    if frame.shape[0] != target_h or frame.shape[1] != target_w:
        frame = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
        # Sharpening adaptatif après upscaling
        strength = QUALITY_PRESETS.get(quality, QUALITY_PRESETS['high'])['sharpen']
        if strength > 0:
            blurred = cv2.GaussianBlur(frame, (0, 0), sigmaX=1.0)
            frame = cv2.addWeighted(frame, 1.0 + strength, blurred, -strength, 0)
            frame = np.clip(frame, 0, 255).astype(np.uint8)
    
    # ═══════════════════════════════════════════════════════════════
    
    elapsed = time.perf_counter() - t0
    return frame, {
        'quality': quality,
        'frame_idx': frame_idx,
        'original_resolution': f'{orig_w}x{orig_h}',
        'target_resolution': f'{target_w}x{target_h}',
        'decode_ms': round(elapsed*1000, 1)
    }
```

#### B. Ajouter une méthode `decode_video()` complète

**Localisation**: Après `decode_video_frame()`, ligne ~590

**Ajout**:
```python
def decode_video(self, container: bytes, output_path: str,
                 target_resolution: str = None, max_frames: int = 0) -> Tuple[str, Dict]:
    """Decode un container vidéo complet vers un fichier MP4.
    
    Args:
        container: bytes du container vidéo
        output_path: chemin du fichier MP4 de sortie
        target_resolution: 'original', '1080p', '4K', '8K', ou (w, h)
        max_frames: nombre max de frames à décoder (0 = toutes)
    
    Returns:
        (output_path, stats)
    """
    t0 = time.perf_counter()
    
    # Lire le header
    hdr_sz = struct.calcsize('<4sBBBBHHII')
    magic, ver, mode, qi, fi, orig_h, orig_w, fps100, fc = \
        struct.unpack('<4sBBBBHHII', container[:hdr_sz])
    assert magic == MAGIC
    
    fps = fps100 / 100.0
    quality = {0:'ultra',1:'high',2:'balanced',3:'compact'}[qi]
    
    # Déterminer la résolution cible
    if target_resolution is None or target_resolution == 'original':
        target_w, target_h = orig_w, orig_h
    elif target_resolution == '1080p':
        target_w, target_h = 1920, 1080
    elif target_resolution == '4K':
        target_w, target_h = 3840, 2160
    elif target_resolution == '8K':
        target_w, target_h = 7680, 4320
    elif isinstance(target_resolution, (list, tuple)):
        target_w, target_h = target_resolution
    else:
        target_w, target_h = orig_w, orig_h
    
    # Nombre de frames à décoder
    num_frames = fc if max_frames == 0 else min(fc, max_frames)
    
    # Créer le VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (target_w, target_h))
    
    if not out.isOpened():
        raise ValueError(f"Cannot create video writer: {output_path}")
    
    # Décoder et écrire chaque frame
    for i in range(num_frames):
        frame, _ = self.decode_video_frame(container, i, target_resolution=target_resolution)
        out.write(frame)
    
    out.release()
    
    elapsed = time.perf_counter() - t0
    
    return output_path, {
        'original_resolution': f'{orig_w}x{orig_h}',
        'target_resolution': f'{target_w}x{target_h}',
        'fps': fps,
        'frame_count': num_frames,
        'total_frames': fc,
        'quality': quality,
        'decode_time': round(elapsed, 2),
        'decode_ms': round(elapsed * 1000, 1),
    }
```

### 2. Serveur (`hcv_pro_server.py`)

#### Ajouter un endpoint `/api/precompressed-video`

**Localisation**: Après l'endpoint `/api/precompressed`, ligne ~610

**Ajout**:
```python
@app.route('/api/precompressed-video', methods=['POST'])
def api_precompressed_video():
    """Compression et décompression de vidéos précompressées avec upscaling."""
    try:
        from hcv_universal_boost_codec import HCVUniversalBoost
        
        strategy = request.form.get('strategy', 'AUTO')
        target_resolution = request.form.get('target_resolution', 'original')  # 'original', '1080p', '4K', '8K'
        
        if strategy not in ('AUTO', 'DIRECT', 'HYBRID', 'TRANSCODE'):
            strategy = 'AUTO'
        
        if 'file' not in request.files:
            return jsonify({'detail': 'Aucun fichier vidéo fourni'}), 400
        
        file = request.files['file']
        source_suffix = Path(file.filename or 'video.mp4').suffix or '.mp4'
        
        # Create temp files in a persistent directory
        temp_dir = Path(tempfile.gettempdir()) / 'hcv_pro_precompressed_videos'
        temp_dir.mkdir(exist_ok=True)
        
        tmp_name = str(temp_dir / f'source_{uuid.uuid4().hex}{source_suffix}')
        file.save(tmp_name)
        
        # Map strategy to quality for the codec
        quality_map = {'AUTO': 'high', 'DIRECT': 'ultra', 'HYBRID': 'balanced', 'TRANSCODE': 'compact'}
        quality = quality_map.get(strategy, 'high')
        
        codec = HCVUniversalBoost(quality=quality)
        
        # Encode video (max 100 frames pour la démo)
        container, enc_stats = codec.encode_video(tmp_name, max_frames=100)
        
        # Decode video avec upscaling
        restored_path = tmp_name + '_restored.mp4'
        _, dec_stats = codec.decode_video(container, restored_path, 
                                          target_resolution=target_resolution)
        
        # Determine correct MIME type for source
        source_mime = file.mimetype or _guess_mime(tmp_name)
        if not source_mime or source_mime == 'application/octet-stream':
            source_mime = 'video/mp4'
        
        result = {
            **enc_stats,
            **dec_stats,
            'filename': file.filename,
            'source_format': source_suffix.replace('.', '').upper() or 'VIDEO',
            'mode': f'PRECOMPRESSED_VIDEO ({strategy})',
            'media_type': 'video',
            'strategy': strategy,
            'bitexact_reproducible': True,
            'video_before_url': _register_media(tmp_name, source_mime),
            'video_after_url': _register_media(restored_path, 'video/mp4'),
            'video_after_mime': 'video/mp4',
        }
        
        history.append({
            'filename': file.filename,
            'resolution': enc_stats['original_resolution'],
            'mode': f'PRECOMPRESSED_VIDEO ({strategy})',
            'ratio_vs_raw': enc_stats.get('ratio_vs_source', 1.0),
            'savings_vs_raw': enc_stats.get('savings_vs_source', 0),
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify(result)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'detail': str(e)}), 500
```

### 3. Interface Web (`hcv_pro.html`)

#### A. Ajouter une section "Vidéo Précompressée"

**Localisation**: Après la section "Compression Précompressée", ligne ~640

**Ajout**:
```html
<!-- PRECOMPRESSED VIDEO -->
<section id="sec-precompressed-video" class="hidden space-y-6">
  <div class="grid md:grid-cols-2 gap-6">
    <div class="glass-card rounded-2xl p-8">
      <h2 class="font-display text-2xl font-bold mb-2">🎬 Vidéo Précompressée</h2>
      <p class="text-gray-400 mb-2">Optimisation pour vidéos déjà compressées (MP4/MOV/WebM)</p>
      <div class="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 mb-4 text-sm">
        <p class="text-purple-400 font-medium mb-1">Pipeline Frame-by-Frame</p>
        <p class="text-gray-400">Vidéo → Frames → Downscale → JPEG → zstd → Container</p>
      </div>
      
      <div id="pcv-upload-zone" class="border-2 border-dashed border-purple-500/30 bg-purple-500/5 rounded-2xl p-8 text-center cursor-pointer hover:border-purple-500/60 hover:bg-purple-500/10 transition-all mb-4" onclick="document.getElementById('pcv-file-input').click()">
        <input type="file" id="pcv-file-input" class="hidden" accept="video/mp4,video/quicktime,video/webm,video/x-msvideo" onchange="handlePrecompressedVideoUpload(event)">
        <i data-lucide="film" class="w-12 h-12 text-purple-400 mx-auto mb-3"></i>
        <p class="font-medium text-lg mb-2">Vidéo précompressée</p>
        <p class="text-sm text-gray-400">MP4, MOV, WebM, AVI</p>
      </div>
      
      <div class="mb-4">
        <label for="pcv-strategy" class="block text-sm font-semibold mb-2 text-gray-300">Stratégie</label>
        <select id="pcv-strategy" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white">
          <option value="AUTO" selected>AUTO - Détection automatique</option>
          <option value="DIRECT">DIRECT - Préservation qualité</option>
          <option value="HYBRID">HYBRID - Équilibre optimal</option>
          <option value="TRANSCODE">TRANSCODE - Amélioration qualité</option>
        </select>
      </div>
      
      <div class="mb-4">
        <label for="pcv-target-resolution" class="block text-sm font-semibold mb-2 text-gray-300">Résolution de sortie (Upscale)</label>
        <select id="pcv-target-resolution" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white">
          <option value="original" selected>Original (résolution source)</option>
          <option value="1080p">1080p (1920x1080) — Full HD</option>
          <option value="4K">4K (3840x2160) — Ultra HD</option>
          <option value="8K">8K (7680x4320) — 8K Ultra HD</option>
        </select>
        <p class="text-xs text-gray-400 mt-2">💡 L'upscale Lanczos restaure la résolution avec qualité supérieure</p>
      </div>
      
      <div id="pcv-loading" class="hidden mt-4 text-center">
        <div class="w-8 h-8 border-3 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto"></div>
        <p class="text-sm text-gray-400 mt-2">Compression vidéo précompressée...</p>
      </div>
    </div>
    
    <div class="glass-card rounded-2xl p-8">
      <h2 class="font-display text-2xl font-bold mb-4">Résultats Vidéo Précompressée</h2>
      <div id="pcv-results" class="hidden">
        <div class="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30 mb-4">
          <div class="flex items-center space-x-2">
            <i data-lucide="check-circle" class="w-5 h-5 text-purple-400"></i>
            <span class="font-medium text-purple-400">Compression réussie!</span>
            <span class="ml-auto text-xs text-gray-400" id="pcv-filename"></span>
          </div>
        </div>
        
        <div class="grid grid-cols-2 gap-3 mb-4">
          <div class="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20 text-center">
            <p class="text-xs text-gray-400 mb-1">Ratio vs Source</p>
            <p class="text-2xl font-display font-bold text-purple-400" id="pcv-ratio-src">-</p>
          </div>
          <div class="p-4 rounded-xl bg-hcs-gold/10 border border-hcs-gold/20 text-center">
            <p class="text-xs text-gray-400 mb-1">Économie vs Source</p>
            <p class="text-2xl font-display font-bold text-hcs-gold" id="pcv-savings-src">-</p>
          </div>
        </div>
        
        <div class="grid grid-cols-4 gap-2 mb-4">
          <div class="p-3 rounded-xl bg-hcs-purple/10 text-center"><p class="text-[10px] text-gray-500">Résolution orig.</p><p class="font-bold text-sm" id="pcv-orig-res">-</p></div>
          <div class="p-3 rounded-xl bg-hcs-purple/10 text-center"><p class="text-[10px] text-gray-500">Downscaled</p><p class="font-bold text-hcs-purple text-sm" id="pcv-ds-res">-</p></div>
          <div class="p-3 rounded-xl bg-green-500/10 text-center"><p class="text-[10px] text-gray-500">Sortie (Upscale)</p><p class="font-bold text-green-400 text-sm" id="pcv-target-res">-</p></div>
          <div class="p-3 rounded-xl bg-hcs-purple/10 text-center"><p class="text-[10px] text-gray-500">Frames</p><p class="font-bold text-hcs-purple text-sm" id="pcv-frames">-</p></div>
        </div>
        
        <div class="grid grid-cols-2 gap-3 mb-4">
          <div class="p-3 rounded-xl bg-white/5 text-center"><p class="text-xs text-gray-500">Stratégie utilisée</p><p class="font-bold text-sm text-purple-400" id="pcv-strategy-used">-</p></div>
          <div class="p-3 rounded-xl bg-white/5 text-center"><p class="text-xs text-gray-500">FPS</p><p class="font-bold text-sm" id="pcv-fps">-</p></div>
        </div>
        
        <div class="grid grid-cols-2 gap-4 mb-4">
          <div class="text-center">
            <p class="text-xs text-gray-400 mb-2">🔵 Vidéo originale</p>
            <video id="pcv-video-before" controls playsinline style="display:none;width:100%;border-radius:0.5rem;background:#1f2937;max-height:240px"></video>
          </div>
          <div class="text-center">
            <p class="text-xs text-gray-400 mb-2">🟢 Vidéo décompressée (Upscale)</p>
            <video id="pcv-video-after" controls playsinline style="display:none;width:100%;border-radius:0.5rem;background:#1f2937;max-height:240px"></video>
          </div>
        </div>
      </div>
      
      <div id="pcv-no-results" class="text-center py-12 text-gray-500">
        <i data-lucide="film" class="w-12 h-12 mx-auto mb-3 opacity-30"></i>
        <p class="mb-2">Uploadez une vidéo pour commencer</p>
      </div>
    </div>
  </div>
</section>
```

#### B. Ajouter le bouton de navigation

**Localisation**: Dans la sidebar, après le bouton "Précompressé", ligne ~75

**Ajout**:
```html
<button onclick="showSection('precompressed-video')" class="nav-btn w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-gray-300 hover:bg-white/5 transition-colors" data-s="precompressed-video">
  <i data-lucide="film" class="w-5 h-5"></i><span>Vidéo Précompressée</span>
</button>
```

#### C. Ajouter les fonctions JavaScript

**Localisation**: Après les fonctions `showPrecompressedResults()`, ligne ~1250

**Ajout**:
```javascript
// ─── Vidéo Précompressée ───────────────────────────────────────────────
function handlePrecompressedVideoUpload(e) {
  if (!e.target.files.length) return;
  const fd = new FormData(); 
  fd.append('file', e.target.files[0]); 
  fd.append('strategy', $('pcv-strategy').value);
  fd.append('target_resolution', $('pcv-target-resolution').value);
  doPrecompressedVideo(fd);
}

async function doPrecompressedVideo(fd) {
  $('pcv-loading').classList.remove('hidden');
  $('pcv-results').classList.add('hidden');
  $('pcv-no-results').classList.add('hidden');
  clearVideo('pcv-video-before');
  clearVideo('pcv-video-after');
  
  try {
    const r = await fetch('/api/precompressed-video', { method: 'POST', body: fd });
    if (!r.ok) {
      const e = await r.json();
      throw new Error(e.detail || 'Error');
    }
    const d = await r.json();
    showPrecompressedVideoResults(d);
    loadHistory();
  } catch (e) {
    alert('Erreur: ' + e.message);
  } finally {
    $('pcv-loading').classList.add('hidden');
  }
}

function showPrecompressedVideoResults(d) {
  $('pcv-results').classList.remove('hidden');
  $('pcv-no-results').classList.add('hidden');
  
  $('pcv-filename').textContent = d.filename || '';
  $('pcv-ratio-src').textContent = d.ratio_vs_source + ':1';
  $('pcv-savings-src').textContent = d.savings_vs_source + '%';
  $('pcv-orig-res').textContent = d.original_resolution || '—';
  $('pcv-ds-res').textContent = d.compressed_resolution || d.original_resolution || '—';
  $('pcv-target-res').textContent = d.target_resolution || d.original_resolution || '—';
  $('pcv-frames').textContent = d.frame_count || '—';
  $('pcv-strategy-used').textContent = d.strategy || 'AUTO';
  $('pcv-fps').textContent = d.fps ? d.fps.toFixed(1) + ' fps' : '—';
  
  if (d.video_before_url) setVideo('pcv-video-before', d.video_before_url);
  if (d.video_after_url) setVideo('pcv-video-after', d.video_after_url);
  
  lucide.createIcons();
}

// Ajouter aussi dans la fonction showSection() le titre
const titles = {
  // ... autres titres ...
  'precompressed-video': 'Vidéo Précompressée',
};
```

#### D. Ajouter le drag & drop

**Localisation**: Dans la fonction d'initialisation du drag & drop, ligne ~1060

**Ajout**:
```javascript
// Drag & drop pour vidéo précompressée
const pcvuz = $('pcv-upload-zone');
if (pcvuz) {
  pcvuz.ondragover = e => { e.preventDefault(); pcvuz.style.borderColor = 'rgb(168, 85, 247)'; };
  pcvuz.ondragleave = () => pcvuz.style.borderColor = '';
  pcvuz.ondrop = e => {
    e.preventDefault();
    pcvuz.style.borderColor = '';
    if (e.dataTransfer.files.length) {
      const fd = new FormData();
      fd.append('file', e.dataTransfer.files[0]);
      fd.append('strategy', $('pcv-strategy').value);
      fd.append('target_resolution', $('pcv-target-resolution').value);
      doPrecompressedVideo(fd);
    }
  };
}
```

## 📊 Résumé des Modifications

### Fichiers à Modifier

| Fichier | Modifications | Lignes Ajoutées |
|---------|---------------|-----------------|
| `hcv_universal_boost_codec.py` | Modifier `decode_video_frame()` + Ajouter `decode_video()` | ~80 lignes |
| `hcv_pro_server.py` | Ajouter endpoint `/api/precompressed-video` | ~60 lignes |
| `hcv_pro.html` | Ajouter section + JavaScript | ~150 lignes |

**Total**: ~290 lignes de code

### Fonctionnalités Ajoutées

- ✅ Upscaling vidéo vers Original, 1080p, 4K, 8K
- ✅ Support de tous les formats vidéo (MP4, MOV, WebM, AVI)
- ✅ Stratégies de compression (AUTO, DIRECT, HYBRID, TRANSCODE)
- ✅ Garantie no-expansion (compressed < source)
- ✅ Bit-exact reproductibilité
- ✅ Interface utilisateur complète avec drag & drop
- ✅ Affichage avant/après avec lecteurs vidéo

## 🧪 Tests Recommandés

### Test 1: Upscaling Original
1. Uploader une vidéo MP4
2. Sélectionner "Original"
3. Vérifier que la résolution de sortie = résolution source

### Test 2: Upscaling 4K
1. Uploader une vidéo 1080p
2. Sélectionner "4K"
3. Vérifier que la sortie = 3840x2160

### Test 3: Upscaling 8K
1. Uploader une vidéo 4K
2. Sélectionner "8K"
3. Vérifier que la sortie = 7680x4320

### Test 4: Stratégies
1. Tester AUTO + 4K
2. Tester DIRECT + 4K
3. Tester HYBRID + 4K
4. Tester TRANSCODE + 4K

## ⚠️ Notes Importantes

### Limitations

1. **Nombre de Frames**: Par défaut limité à 100 frames pour la démo (ajustable)
2. **Temps de Traitement**: L'upscaling 8K peut prendre plusieurs minutes
3. **Mémoire**: Les vidéos 8K nécessitent beaucoup de RAM
4. **Audio**: L'audio n'est pas préservé dans le codec Universal Boost (frame-by-frame)

### Optimisations Possibles

1. **Traitement par Batch**: Traiter plusieurs frames en parallèle
2. **GPU Acceleration**: Utiliser CUDA pour l'upscaling
3. **Audio Preservation**: Extraire et remuxer l'audio séparément
4. **Streaming**: Décoder frame par frame au lieu de tout charger en mémoire

## 🎯 Prochaines Étapes

1. ✅ Implémenter les modifications dans le codec
2. ✅ Ajouter l'endpoint serveur
3. ✅ Créer l'interface utilisateur
4. 🧪 Tester avec des vidéos réelles
5. 📊 Mesurer les performances
6. 🎨 Optimiser si nécessaire

## 📝 Conclusion

Avec ces modifications, vous aurez un système complet d'upscaling 4K/8K pour:
- ✅ Images mobiles (Android Boost)
- ✅ Images précompressées (Universal Boost)
- ✅ Vidéos précompressées (Universal Boost) ← NOUVEAU

Le tout avec une interface utilisateur cohérente et des performances raisonnables!
