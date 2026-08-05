/**
 * KA Telemedecine — Consultation vidéo avec compression HCV
 * ============================================================
 * Pipeline WebRTC + HCV Delta-H pour la télémédecine.
 * 
 * Architecture hybride :
 *   - Audio : piste WebRTC native (Opus) — latence minimale
 *   - Vidéo : canvas → HCV Delta-H compress → DataChannel → HCV decompress → canvas
 *   - Signaling : QR codes (via KA_BRIDGE) — aucun serveur requis
 * 
 * Usage médecin :
 *   KATelemedecine.startCall('doctor'); // montre QR offer
 * 
 * Usage patient :
 *   KATelemedecine.startCall('patient'); // scanne QR, montre QR answer
 */

const KATelemedecine = {
  // État
  _state: 'idle',           // idle | calling | ringing | connected | ended
  _role: null,              // 'doctor' | 'patient'
  _pc: null,                // RTCPeerConnection
  _localStream: null,       // MediaStream local
  _dataChannel: null,       // DataChannel pour frames HCV
  _sendInterval: null,      // Interval d'envoi des frames
  _remoteCanvas: null,      // Canvas distant
  _localVideo: null,        // Élément vidéo local
  _fps: 15,                 // Frames par seconde
  _quality: 75,             // Qualité HCV (0-100)
  _stats: { sent: 0, received: 0, bytesSent: 0, bytesReceived: 0 },
  
  // Config STUN (Google, gratuit)
  _iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' }
  ],
  
  // Callbacks
  onStateChange: null,
  onStatsUpdate: null,
  onError: null,
  
  /**
   * Initialise les éléments vidéo
   * @param {string} localVideoId - ID de l'élément <video> local
   * @param {string} remoteCanvasId - ID du <canvas> distant
   */
  init(localVideoId, remoteCanvasId) {
    this._localVideo = document.getElementById(localVideoId);
    this._remoteCanvas = document.getElementById(remoteCanvasId);
    if (this._remoteCanvas) {
      this._remoteCanvas.width = 320;
      this._remoteCanvas.height = 240;
    }
  },
  
  /**
   * Vérifie si la caméra est disponible
   * @returns {Promise<{ok: boolean, error: string}>}
   */
  async checkCamera() {
    try {
      // Vérifier si on est dans un contexte sécurisé (HTTPS ou localhost)
      if (window.location.protocol === 'http:' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        return { ok: false, error: 'Contexte non securise. La camera necessite HTTPS ou localhost.\n\nSolution : accedez via http://localhost:8765' };
      }
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        return { ok: false, error: 'getUserMedia non supporte sur ce navigateur.' };
      }
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240, facingMode: 'user' }, audio: false });
      stream.getTracks().forEach(t => t.stop());
      return { ok: true, error: null };
    } catch (e) {
      if (e.name === 'NotAllowedError') return { ok: false, error: 'Permission camera refusee.' };
      if (e.name === 'NotFoundError') return { ok: false, error: 'Aucune camera detectee.' };
      return { ok: false, error: e.message };
    }
  },
  
  /**
   * Affiche un aperçu caméra (sans démarrer l'appel)
   */
  async previewCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 320, height: 240, facingMode: 'user' },
        audio: false
      });
      if (this._localVideo) {
        this._localVideo.srcObject = stream;
      }
      return { ok: true, stream };
    } catch (e) {
      return { ok: false, error: e.message };
    }
  },
  
  /**
   * Démarre une consultation
   * @param {'doctor'|'patient'} role
   */
  async startCall(role) {
    this._role = role;
    this._state = 'calling';
    this._setStatus('calling');
    
    try {
      // 1. Accès caméra + micro
      this._localStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 320, height: 240, facingMode: 'user' },
        audio: true
      });
      
      if (this._localVideo) {
        this._localVideo.srcObject = this._localStream;
      }
      
      // 2. Créer PeerConnection
      await this._createPeerConnection();
      
      // 3. Ajouter pistes audio
      this._localStream.getAudioTracks().forEach(track => {
        this._pc.addTrack(track, this._localStream);
      });
      
      // 4. Créer DataChannel pour frames HCV
      if (role === 'doctor') {
        this._dataChannel = this._pc.createDataChannel('hcv-video', {
          ordered: false,
          maxRetransmits: 0
        });
        this._setupDataChannel(this._dataChannel);
      }
      
      // 5. Créer offre/réponse
      if (role === 'doctor') {
        const offer = await this._pc.createOffer();
        await this._pc.setLocalDescription(offer);
        this._showSignalingQR(offer.sdp, 'offer');
        this._state = 'ringing';
      } else {
        // Patient : attend l'offre
        this._state = 'ringing';
        this._showSignalingPrompt();
      }
      
    } catch (err) {
      this._onError('Erreur démarrage : ' + err.message);
    }
  },
  
  /**
   * Accepte un appel entrant (côté patient)
   * @param {string} offerSdp - SDP de l'offre scannée depuis le QR
   */
  async acceptCall(offerSdp) {
    try {
      if (!this._pc) {
        await this._createPeerConnection();
        
        // Caméra patient
        this._localStream = await navigator.mediaDevices.getUserMedia({
          video: { width: 320, height: 240, facingMode: 'user' },
          audio: true
        });
        if (this._localVideo) {
          this._localVideo.srcObject = this._localStream;
        }
        this._localStream.getAudioTracks().forEach(track => {
          this._pc.addTrack(track, this._localStream);
        });
      }
      
      const offer = new RTCSessionDescription({ type: 'offer', sdp: offerSdp });
      await this._pc.setRemoteDescription(offer);
      
      const answer = await this._pc.createAnswer();
      await this._pc.setLocalDescription(answer);
      
      this._showSignalingQR(answer.sdp, 'answer');
      this._state = 'connected';
      this._setStatus('connected');
      this._startSendingFrames();
      
    } catch (err) {
      this._onError('Erreur acceptation : ' + err.message);
    }
  },
  
  /**
   * Finalise l'appel (côté médecin) après scan de la réponse
   * @param {string} answerSdp - SDP de la réponse
   */
  async finalizeCall(answerSdp) {
    try {
      const answer = new RTCSessionDescription({ type: 'answer', sdp: answerSdp });
      await this._pc.setRemoteDescription(answer);
      this._state = 'connected';
      this._setStatus('connected');
      this._startSendingFrames();
    } catch (err) {
      this._onError('Erreur finalisation : ' + err.message);
    }
  },
  
  /**
   * Raccroche
   */
  hangUp() {
    this._stopSendingFrames();
    if (this._dataChannel) { this._dataChannel.close(); }
    if (this._pc) { this._pc.close(); this._pc = null; }
    if (this._localStream) {
      this._localStream.getTracks().forEach(t => t.stop());
      this._localStream = null;
    }
    if (this._localVideo) { this._localVideo.srcObject = null; }
    this._state = 'ended';
    this._setStatus('ended');
  },
  
  /**
   * Active/désactive le micro
   */
  toggleMute() {
    if (this._localStream) {
      const audioTrack = this._localStream.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        return audioTrack.enabled;
      }
    }
    return true;
  },
  
  /**
   * Active/désactive la caméra
   */
  toggleVideo() {
    if (this._localStream) {
      const videoTrack = this._localStream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        return videoTrack.enabled;
      }
    }
    return true;
  },
  
  /**
   * Ajuste la qualité HCV
   * @param {number} q - 0-100
   */
  setQuality(q) {
    this._quality = Math.max(10, Math.min(100, q));
  },
  
  // ═══════════════════════════════════════════════
  // INTERNE
  // ═══════════════════════════════════════════════
  
  async _createPeerConnection() {
    const iceConfig = (typeof KA_Network !== 'undefined') 
      ? KA_Network.getIceConfig() 
      : { iceServers: this._iceServers };
    this._pc = new RTCPeerConnection(iceConfig);
    
    // Réception DataChannel (côté patient)
    this._pc.ondatachannel = (event) => {
      this._dataChannel = event.channel;
      this._setupDataChannel(this._dataChannel);
    };
    
    // Log ICE
    this._pc.oniceconnectionstatechange = () => {
      console.log('ICE:', this._pc.iceConnectionState);
      if (this._pc.iceConnectionState === 'disconnected' ||
          this._pc.iceConnectionState === 'failed') {
        this._onError('Connexion perdue');
      }
    };
    
    // Gestion pistes distantes
    this._pc.ontrack = (event) => {
      // Audio distant : créer un élément audio
      if (event.track.kind === 'audio') {
        const remoteAudio = document.createElement('audio');
        remoteAudio.id = 'remoteAudio';
        remoteAudio.autoplay = true;
        remoteAudio.srcObject = event.streams[0];
        document.body.appendChild(remoteAudio);
      }
    };
  },
  
  _setupDataChannel(channel) {
    channel.binaryType = 'arraybuffer';
    channel.onmessage = (event) => {
      this._receiveFrame(new Uint8Array(event.data));
    };
  },
  
  /**
   * Boucle d'envoi des frames compressées via HCV
   */
  _startSendingFrames() {
    if (this._sendInterval) return;
    
    const captureCanvas = document.createElement('canvas');
    captureCanvas.width = 320;
    captureCanvas.height = 240;
    const ctx = captureCanvas.getContext('2d');
    
    const sendFrame = () => {
      if (this._state !== 'connected') return;
      if (!this._dataChannel || this._dataChannel.readyState !== 'open') return;
      if (!this._localVideo || !this._localVideo.srcObject) return;
      
      try {
        // Capturer la frame depuis la vidéo locale
        ctx.drawImage(this._localVideo, 0, 0, 320, 240);
        
        // Compression HCV
        const compressed = HCV.compressFrame(captureCanvas, { quality: this._quality });
        
        // Envoyer via DataChannel
        if (compressed.data.length < 320 * 240 * 3) { // seulement si compression efficace
          this._dataChannel.send(compressed.data);
          this._stats.sent++;
          this._stats.bytesSent += compressed.data.length;
        }
        
        if (this.onStatsUpdate) {
          this.onStatsUpdate({ ...this._stats });
        }
      } catch (e) {
        // Silencieux — évite de flooder la console
      }
    };
    
    this._sendInterval = setInterval(sendFrame, 1000 / this._fps);
  },
  
  _stopSendingFrames() {
    if (this._sendInterval) {
      clearInterval(this._sendInterval);
      this._sendInterval = null;
    }
  },
  
  /**
   * Réception et décompression d'une frame HCV
   */
  _receiveFrame(compressedData) {
    if (!this._remoteCanvas) return;
    
    try {
      const compressed = { data: compressedData };
      const imageData = HCV.decompressFrame(compressed);
      
      const ctx = this._remoteCanvas.getContext('2d');
      this._remoteCanvas.width = imageData.width;
      this._remoteCanvas.height = imageData.height;
      ctx.putImageData(imageData, 0, 0);
      
      this._stats.received++;
      this._stats.bytesReceived += compressedData.length;
    } catch (e) {
      // Frame corrompue, ignorer
    }
  },
  
  /**
   * Affiche le QR code de signaling
   */
  _showSignalingQR(sdp, type) {
    // Utiliser KA_SECURE pour générer le QR
    if (typeof KA_SECURE !== 'undefined' && KA_SECURE.generateQR) {
      const data = { type: 'webrtc-signal', sdpType: type, sdp: sdp };
      KA_SECURE.generateQR('qrSignal', data);
      document.getElementById('signalQRContainer').style.display = 'block';
      document.getElementById('signalLabel').textContent = 
        type === 'offer' ? '📋 QR Code — Le patient doit scanner ce code' :
                           '📋 QR Code — Le médecin doit scanner ce code';
    }
  },
  
  _showSignalingPrompt() {
    // Afficher le champ de saisie pour coller/taper le code SDP
    document.getElementById('signalPromptContainer').style.display = 'block';
  },
  
  _setStatus(status) {
    if (this.onStateChange) {
      this.onStateChange(status);
    }
  },
  
  _onError(msg) {
    console.error('KATelemedecine:', msg);
    if (this.onError) {
      this.onError(msg);
    }
  }
};

// Export global
if (typeof window !== 'undefined') {
  window.KATelemedecine = KATelemedecine;
}
