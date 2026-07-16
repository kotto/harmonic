/**
 * KA Phone — Camera (Photo + Video + Compression auto)
 */
/* global API_URL */

var camStream = null;
var camRecorder = null;
var camRecording = false;
var camChunks = [];
var camGallery = JSON.parse(localStorage.getItem('ka_cam_gallery') || '[]');

function camCapture() {
  var video = document.getElementById('cam-video');
  var canvas = document.getElementById('cam-canvas');
  var placeholder = document.getElementById('cam-placeholder');
  
  if (!camStream) {
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment', width: 1920, height: 1080 }, audio: false })
      .then(function(s) {
        camStream = s;
        video.srcObject = s;
        video.style.display = 'block';
        placeholder.style.display = 'none';
        setTimeout(function() { camCapture(); }, 800);
      })
      .catch(function(e) { alert('Caméra non disponible: ' + e.message); });
    return;
  }

  canvas.width = video.videoWidth || 1920;
  canvas.height = video.videoHeight || 1080;
  var ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0);
  
  var dataUrl = canvas.toDataURL('image/jpeg', 0.9);
  camAddToGallery(dataUrl, 'photo');
  
  // Compression automatique si API dispo
  canvas.toBlob(function(blob) {
    var fd = new FormData();
    fd.append('file', blob, 'photo_' + Date.now() + '.jpg');
    fd.append('quality', 'standard');
    fetch(API_URL + '/api/storage/optimize', { method: 'POST', body: fd })
      .then(function(r) {
        var ratio = r.headers.get('X-Ratio');
        if (ratio) console.log('📸 Photo compressée ' + ratio + '×');
      }).catch(function() {});
  }, 'image/jpeg', 0.9);
}

function camRecord() {
  if (camRecording) { camStopRecord(); return; }
  if (!camStream) {
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: true })
      .then(function(s) {
        camStream = s;
        document.getElementById('cam-video').srcObject = s;
        document.getElementById('cam-video').style.display = 'block';
        document.getElementById('cam-placeholder').style.display = 'none';
        camStartRecord();
      }).catch(function(e) { alert('Caméra non disponible'); });
    return;
  }
  camStartRecord();
}

function camStartRecord() {
  camChunks = [];
  camRecorder = new MediaRecorder(camStream, { mimeType: 'video/webm' });
  camRecorder.ondataavailable = function(e) { if (e.data.size) camChunks.push(e.data); };
  camRecorder.onstop = function() {
    var blob = new Blob(camChunks, { type: 'video/webm' });
    var url = URL.createObjectURL(blob);
    camAddToGallery(url, 'video');
    camRecording = false;
  };
  camRecorder.start();
  camRecording = true;
  document.querySelector('#s-camera .btn--soul').textContent = '⏹ Stop';
}

function camStopRecord() {
  if (camRecorder) camRecorder.stop();
  document.querySelector('#s-camera .btn--soul').textContent = '🎬 Vidéo';
}

function camAddToGallery(url, type) {
  camGallery.unshift({ url: url, type: type, date: Date.now() });
  if (camGallery.length > 12) camGallery = camGallery.slice(0, 12);
  localStorage.setItem('ka_cam_gallery', JSON.stringify(camGallery));
  camRenderGallery();
}

function camRenderGallery() {
  var el = document.getElementById('cam-gallery');
  var html = '';
  camGallery.forEach(function(item, i) {
    var icon = item.type === 'video' ? '🎬' : '';
    html += '<div style=\"position:relative;aspect-ratio:1;border-radius:8px;overflow:hidden;background:var(--g1);cursor:pointer\" onclick=\"camView(' + i + ')\"><img src=\"' + item.url + '\" style=\"width:100%;height:100%;object-fit:cover\" onerror=\"this.parentElement.innerHTML=\'<div style=display:flex;align-items:center;justify-content:center;height:100%;font-size:24px>\' + icon + '\'</div>\'\">' + (item.type === 'video' ? '<div style=\"position:absolute;top:4px;right:4px;font-size:12px\">🎬</div>' : '') + '</div>';
  });
  el.innerHTML = html || '<div style=\"text-align:center;color:var(--t4);font-size:12px;grid-column:1/-1\">Aucune capture</div>';
}

function camView(i) {
  var item = camGallery[i];
  if (!item) return;
  window.open(item.url, '_blank');
}

function camStop() {
  if (camStream) { camStream.getTracks().forEach(function(t) { t.stop(); }); camStream = null; }
  if (camRecorder && camRecording) camRecorder.stop();
  camRecording = false;
  document.getElementById('cam-video').style.display = 'none';
  document.getElementById('cam-placeholder').style.display = 'block';
}

camRenderGallery();
