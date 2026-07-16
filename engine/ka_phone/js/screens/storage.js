/**
 * KA Phone — Storage Optimizer
 */

/* global API_URL, fmtSize */

let stoQuality = 'standard';
let stoFiles = [];
let stoUpscale4K = false;

function storageSetQuality(q) {
  stoQuality = q;
  ['arc','std','eco'].forEach(function(id) {
    var el = document.getElementById('sto-q-' + id);
    if (!el) return;
    el.className = 'pill';
    el.style.background = ''; el.style.borderColor = ''; el.style.color = '';
  });
  var sel = document.getElementById('sto-q-' + (q === 'archive' ? 'arc' : q === 'standard' ? 'std' : 'eco'));
  if (sel) {
    if (q === 'standard') sel.className = 'pill pill--life';
    else if (q === 'eco') { sel.style.background = 'rgba(240,149,149,.12)'; sel.style.borderColor = 'rgba(240,149,149,.3)'; sel.style.color = 'var(--coral)'; }
    else { sel.style.background = 'rgba(139,131,255,.12)'; sel.style.borderColor = 'rgba(139,131,255,.3)'; sel.style.color = 'var(--soul-l)'; }
  }
}

function storageToggle4K() {
  stoUpscale4K = !stoUpscale4K;
  var bg = document.getElementById('sto-4k-toggle');
  var knob = document.getElementById('sto-4k-knob');
  var label = document.getElementById('sto-4k-label');
  if (stoUpscale4K) {
    bg.style.background = 'var(--life)'; knob.style.left = '22px';
    label.textContent = '4K'; label.style.color = 'var(--life)';
  } else {
    bg.style.background = 'var(--g1)'; knob.style.left = '2px';
    label.textContent = 'OFF'; label.style.color = 'var(--t4)';
  }
}

function fmtSize(bytes) {
  if (bytes < 1024) return bytes + ' o';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' Ko';
  return (bytes / 1048576).toFixed(1) + ' Mo';
}

var _storageSetQuality = storageSetQuality;

function storageSelectFiles(fileList) {
  stoFiles = Array.from(fileList);
  var gauge = document.getElementById('sto-gauge');
  var results = document.getElementById('sto-results');
  var btn = document.getElementById('sto-optimize-btn');
  if (!stoFiles.length) { gauge.style.display = 'none'; btn.style.opacity = '.5'; btn.style.pointerEvents = 'none'; return; }

  var fd = new FormData();
  stoFiles.forEach(function(f) { fd.append('files', f); });
  results.innerHTML = '<div style="text-align:center;padding:14px;color:var(--t4);font-size:12px"><span style="animation:pulse 1.2s ease-in-out infinite">●</span> Analyse…</div>';

  fetch(API_URL + '/api/storage/optimize-batch', { method: 'POST', body: fd, signal: AbortSignal.timeout(30000) })
    .then(function(r) { return r.json(); })
    .then(function(d) {
      if (d.error) { results.innerHTML = '<span style="color:var(--coral)">⚠️ ' + d.error + '</span>'; return; }
      gauge.style.display = 'block';
      btn.style.opacity = '1'; btn.style.pointerEvents = 'auto';

      var pct = d.total_original > 0 ? Math.round(d.total_saved / d.total_original * 100) : 0;
      document.getElementById('sto-saved-total').textContent = fmtSize(d.total_saved);
      document.getElementById('sto-orig-total').textContent = fmtSize(d.total_original);
      document.getElementById('sto-after-total').textContent = fmtSize(d.total_estimated_after);
      document.getElementById('sto-bar').style.width = Math.min(pct, 100) + '%';

      var html = '<div class="sec-lbl" style="margin-bottom:6px">FICHIERS (' + d.n_files + ')</div>';
      d.files.forEach(function(f) {
        var icon = f.media_type.indexOf('image') >= 0 ? '🖼️' : f.media_type.indexOf('video') >= 0 ? '🎬' : f.media_type.indexOf('voice') >= 0 ? '🎤' : '📄';
        html += '<div class="card" style="display:flex;align-items:center;gap:10px;margin-bottom:6px;padding:10px 12px"><span style="font-size:16px">' + icon + '</span>';
        html += '<div style="flex:1;min-width:0"><div style="font-size:12px;color:var(--t1);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">' + f.filename + '</div>';
        html += '<div style="font-size:10px;color:var(--t4)">' + fmtSize(f.original_size) + ' → <span style="color:var(--life)">' + fmtSize(f.estimated_after) + '</span> (' + f.estimated_ratio + '×)</div></div>';
        html += '<span style="font-size:13px;font-weight:700;color:var(--life)">−' + Math.round(f.estimated_saved / f.original_size * 100) + '%</span></div>';
      });
      results.innerHTML = html;
    })
    .catch(function(e) {
      results.innerHTML = '<span style="color:var(--coral)">⚠️ API inaccessible — réessayez plus tard</span>';
      gauge.style.display = 'none';
    });
}

function storageOptimize() {
  if (!stoFiles.length) return;
  var results = document.getElementById('sto-results');
  var btn = document.getElementById('sto-optimize-btn');
  btn.style.opacity = '.5'; btn.style.pointerEvents = 'none';
  btn.textContent = '⏳ Optimisation…';

  var done = 0;
  var totalSaved = 0;

  stoFiles.forEach(function(f, idx) {
    var fd = new FormData();
    fd.append('file', f);
    fd.append('quality', stoQuality);

    fetch(API_URL + '/api/storage/optimize', { method: 'POST', body: fd, signal: AbortSignal.timeout(60000) })
      .then(function(r) {
        var saved = parseInt(r.headers.get('X-Saved') || '0');
        totalSaved += saved; done++;

        var cards = results.querySelectorAll('.card');
        if (cards[idx]) {
          var badge = cards[idx].querySelector('span:last-child');
          if (badge) { badge.textContent = r.headers.get('X-Warning') ? '⚠️' : '✅'; badge.style.color = r.headers.get('X-Warning') ? 'var(--coral)' : 'var(--life)'; }
        }

        if (done === stoFiles.length) {
          btn.textContent = '✅ Terminé';
          document.getElementById('sto-saved-total').textContent = fmtSize(totalSaved);
        }
      })
      .catch(function() {
        done++;
        if (done === stoFiles.length) btn.textContent = '✅ Terminé';
      });
  });
}
