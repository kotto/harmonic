// Harmonic AI SaaS Dashboard - Real API Integration
// Used by index.html via: <script src="app.js"></script>

const API_BASE = (window.HarmonicConfig && window.HarmonicConfig.API_BASE_URL) || 'http://localhost:9000/api/v1';
const AUTH_TOKEN = localStorage.getItem('harmonic_token') || '';

class HarmonicDashboard {
    constructor() {
        this.currentUser = null;
        this.audioJobs = [];
        this.videoJobs = [];
        this.stats = { audioJobsCount: 0, videoJobsCount: 0, monthlyUsage: 0, currentPlan: 'Free' };
        this.init();
    }

    // ---- HTTP helpers ----
    async api(method, path, body) {
        const url = `${API_BASE}${path}`;
        const headers = { 'Content-Type': 'application/json' };
        if (AUTH_TOKEN) headers['Authorization'] = `Bearer ${AUTH_TOKEN}`;
        const opts = { method, headers };
        if (body) opts.body = JSON.stringify(body);
        const res = await fetch(url, opts);
        if (!res.ok) {
            const err = await res.text();
            throw new Error(`API ${method} ${path} → ${res.status}: ${err}`);
        }
        return res.json();
    }

    // ---- Init ----
    async init() {
        this.setupEventListeners();
        this.loadTheme();
        try {
            await this.loadStats();
        } catch (e) {
            console.warn('Backend unreachable – showing empty state', e);
        }
        try {
            await this.loadAudioJobs();
        } catch (e) {
            console.warn('Could not load audio jobs', e);
        }
        try {
            await this.loadVideoJobs();
        } catch (e) {
            console.warn('Could not load video jobs', e);
        }
    }

    setupEventListeners() {
        document.getElementById('themeToggle').addEventListener('click', () => this.toggleTheme());
        document.getElementById('refreshAudioJobs').addEventListener('click', () => this.refreshAudioJobs());
        document.getElementById('refreshVideoJobs').addEventListener('click', () => this.refreshVideoJobs());
        document.getElementById('newAudioJob').addEventListener('click', () => this.showProcessingModal('audio'));
        document.getElementById('newVideoJob').addEventListener('click', () => this.showProcessingModal('video'));
        document.getElementById('audioFileInput').addEventListener('change', (e) => this.handleUpload(e, 'audio'));
        document.getElementById('videoFileInput').addEventListener('change', (e) => this.handleUpload(e, 'video'));
    }

    // ---- Theme ----
    loadTheme() {
        const saved = localStorage.getItem('harmonic_theme');
        if (saved === 'light') {
            document.body.classList.add('light-mode');
            const icon = document.querySelector('#themeToggle i');
            if (icon) icon.className = 'fas fa-sun';
        }
    }

    toggleTheme() {
        const icon = document.querySelector('#themeToggle i');
        const isLight = document.body.classList.toggle('light-mode');
        if (isLight) {
            icon.className = 'fas fa-sun';
            localStorage.setItem('harmonic_theme', 'light');
        } else {
            icon.className = 'fas fa-moon';
            localStorage.setItem('harmonic_theme', 'dark');
        }
    }

    // ---- Stats (status endpoint) ----
    async loadStats() {
        try {
            const data = await this.api('GET', '/chat/status');
            this.stats.audioJobsCount = (data.recent_audio_jobs || []).length;
            this.stats.videoJobsCount = (data.recent_video_jobs || []).length;
            this.stats.monthlyUsage = data.usage_metrics?.usage_percent || 0;
            this.stats.currentPlan = data.usage_metrics?.plan || 'Free';
        } catch {
            // fallback to 0
            this.stats = { audioJobsCount: 0, videoJobsCount: 0, monthlyUsage: 0, currentPlan: 'Free' };
        }
        this._renderStats();
    }

    _renderStats() {
        document.getElementById('audioJobsCount').textContent = this.stats.audioJobsCount;
        document.getElementById('videoJobsCount').textContent = this.stats.videoJobsCount;
        document.getElementById('monthlyUsage').textContent = `${this.stats.monthlyUsage}%`;
        document.getElementById('currentPlan').textContent = this.stats.currentPlan;
    }

    // ---- Audio jobs ----
    async loadAudioJobs() {
        try {
            const jobs = await this.api('GET', '/chat/audio/jobs');
            this.audioJobs = Array.isArray(jobs) ? jobs : [];
        } catch {
            this.audioJobs = [];
        }
        this._renderJobs('audio');
    }

    async loadVideoJobs() {
        try {
            const jobs = await this.api('GET', '/chat/video/jobs');
            this.videoJobs = Array.isArray(jobs) ? jobs : [];
        } catch {
            this.videoJobs = [];
        }
        this._renderJobs('video');
    }

    _renderJobs(type) {
        const list = this.audioJobs; // use the correct list
        if (type === 'video') list = this.videoJobs;
        const container = document.getElementById(`${type}JobsList`);
        if (!list || list.length === 0) {
            container.innerHTML = `
                <div class="job-item">
                    <div class="job-info">
                        <h3>No ${type} jobs yet</h3>
                        <div class="job-meta"><span>Upload a file to get started</span></div>
                    </div>
                    <div class="job-status status-pending">Pending</div>
                </div>`;
            return;
        }
        container.innerHTML = list.map(job => `
            <div class="job-item" data-job-id="${job.job_id || job.id}">
                <div class="job-info">
                    <h3>${job.name || (job.job_id || 'Job')}</h3>
                    <div class="job-meta">
                        <span><i class="far fa-clock"></i> ${job.created_at ? new Date(job.created_at).toLocaleString() : 'N/A'}</span>
                        <span><i class="fas fa-tag"></i> ${(job.processing_mode || 'standard').replace(/^hcs_/, '').toUpperCase()}</span>
                        ${job.processing_time_ms ? `<span><i class="fas fa-stopwatch"></i> ${(job.processing_time_ms/1000).toFixed(1)}s</span>` : ''}
                        ${job.quality_improvement ? `<span><i class="fas fa-chart-line"></i> +${job.quality_improvement}</span>` : ''}
                        ${job.error_message ? `<span><i class="fas fa-exclamation-circle"></i> ${job.error_message}</span>` : ''}
                    </div>
                </div>
                <div class="job-status status-${(job.status || 'pending').toLowerCase()}">
                    ${(job.status || 'Pending').charAt(0).toUpperCase() + (job.status || 'Pending').slice(1)}
                </div>
            </div>
        `).join('');
    }

    // ---- Upload with real API ----
    async handleUpload(event, type) {
        const file = event.target.files[0];
        if (!file) return;

        const maxSize = 100 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showNotification('File too large (max 100 MB).', 'error');
            return;
        }

        const uploadArea = document.getElementById(`${type}UploadArea`);
        const originalHTML = uploadArea.innerHTML;
        uploadArea.innerHTML = `
            <div class="upload-progress">
                <i class="fas fa-spinner fa-spin"></i>
                <h3>Uploading ${file.name}…</h3>
                <div class="progress-bar"><div class="progress-fill" id="${type}ProgressFill" style="width:10%"></div></div>
                <p>Please wait…</p>
            </div>`;

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('processing_mode', type === 'audio' ? 'hcs_clarity' : 'hcs_4k_clarity');

            const headers = {};
            if (AUTH_TOKEN) headers['Authorization'] = `Bearer ${AUTH_TOKEN}`;

            const res = await fetch(`${API_BASE}/chat/${type}/process`, {
                method: 'POST',
                headers,
                body: formData
            });
            if (!res.ok) throw new Error(`Upload failed: ${res.status}`);

            // Simulate progressive fill
            const fill = document.getElementById(`${type}ProgressFill`);
            if (fill) fill.style.width = '100%';

            await this.loadStats();
            await this[type === 'audio' ? 'loadAudioJobs' : 'loadVideoJobs']();

            uploadArea.innerHTML = `
                <i class="fas fa-check-circle" style="color:#10b981;"></i>
                <h3>Upload Complete!</h3>
                <p>${file.name} sent to processing.</p>`;
            this.showNotification(`${type} file uploaded successfully.`, 'success');
        } catch (err) {
            console.error('Upload error:', err);
            uploadArea.innerHTML = originalHTML;
            this.showNotification(`Upload failed: ${err.message}`, 'error');
        }
    }

    // ---- Refresh ----
    async refreshAudioJobs() {
        const btn = document.getElementById('refreshAudioJobs');
        btn.disabled = true; btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Refreshing…`;
        try { await this.loadAudioJobs(); this.showNotification('Audio jobs refreshed', 'success'); }
        catch (e) { this.showNotification('Refresh failed', 'error'); }
        finally { btn.disabled = false; btn.innerHTML = `<i class="fas fa-sync-alt"></i> Refresh`; }
    }

    async refreshVideoJobs() {
        const btn = document.getElementById('refreshVideoJobs');
        btn.disabled = true; btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Refreshing…`;
        try { await this.loadVideoJobs(); this.showNotification('Video jobs refreshed', 'success'); }
        catch (e) { this.showNotification('Refresh failed', 'error'); }
        finally { btn.disabled = false; btn.innerHTML = `<i class="fas fa-sync-alt"></i> Refresh`; }
    }

    // ---- New job modal ----
    showProcessingModal(type) {
        const exists = document.getElementById('processingModal');
        if (exists) exists.remove();

        const modes = type === 'audio'
            ? ['hcs_restore','hcs_spatial','hcs_clarity','hcs_dynamic']
            : ['hcs_4k_clarity','hcs_8k_master','hcs_hdr_vision','hcs_frame_gen','hcs_movie_continuous'];

        const html = `
        <div class="modal-overlay" id="processingModal">
          <div class="modal">
            <div class="modal-header">
              <h3>New ${type} Processing Job</h3>
              <button class="modal-close">&times;</button>
            </div>
            <div class="modal-body">
              <div class="form-group">
                <label>Job Name</label>
                <input type="text" id="modalJobName" class="form-control" placeholder="Enter job name">
              </div>
              <div class="form-group">
                <label>Processing Mode</label>
                <select id="modalMode" class="form-control">
                  ${modes.map(m => `<option value="${m}">${m.replace('hcs_','').toUpperCase()}</option>`).join('')}
                </select>
              </div>
            </div>
            <div class="modal-footer">
              <button class="btn btn-secondary modal-cancel">Cancel</button>
              <button class="btn btn-primary" id="modalSubmit">Create Job</button>
            </div>
          </div>
        </div>`;

        document.body.insertAdjacentHTML('beforeend', html);
        const modal = document.getElementById('processingModal');

        const close = () => {
            modal.style.opacity = '0'; modal.style.pointerEvents = 'none';
            setTimeout(() => modal.remove(), 300);
        };

        modal.querySelector('.modal-close').addEventListener('click', close);
        modal.querySelector('.modal-cancel').addEventListener('click', close);
        modal.addEventListener('click', e => { if (e.target === modal) close(); });

        document.getElementById('modalSubmit').addEventListener('click', async () => {
            const name = document.getElementById('modalJobName').value || `New ${type} job`;
            const mode = document.getElementById('modalMode').value;
            try {
                await this.api('POST', `/chat/${type}/process`, {
                    processing_mode: mode,
                    duration_seconds: 60,
                    job_name: name
                });
                close();
                await this[type === 'audio' ? 'loadAudioJobs' : 'loadVideoJobs']();
                this.showNotification(`${type} job created successfully`, 'success');
            } catch (err) {
                this.showNotification(`Failed to create job: ${err.message}`, 'error');
            }
        });

        setTimeout(() => { modal.style.opacity = '1'; modal.style.pointerEvents = 'all'; }, 10);
    }

    // ---- Notification ----
    showNotification(message, type = 'info') {
        const existing = document.querySelectorAll('.notification');
        existing.forEach(n => n.remove());

        const n = document.createElement('div');
        n.className = `notification notification-${type}`;
        const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle';
        n.innerHTML = `
            <div class="notification-content"><i class="fas fa-${icon}"></i><span>${message}</span></div>
            <button class="notification-close">&times;</button>`;

        if (!document.getElementById('notif-styles')) {
            const s = document.createElement('style');
            s.id = 'notif-styles';
            s.textContent = `
                .notification {
                    position: fixed; top:20px; right:20px;
                    background:#1e293b; color:white; padding:15px 20px;
                    border-radius:8px; box-shadow:0 4px 12px rgba(0,0,0,.15);
                    display:flex; align-items:center; justify-content:space-between; gap:15px;
                    z-index:1000; transform:translateX(120%); transition:transform .3s ease; max-width:400px;
                }
                .light-mode .notification { background:#fff; color:#1e293b; border:1px solid #e2e8f0; }
                .notification-success { border-left:4px solid #10b981; }
                .notification-error { border-left:4px solid #ef4444; }
                .notification-info { border-left:4px solid #3b82f6; }
                .notification-close { background:none; border:none; color:inherit; font-size:20px; cursor:pointer; opacity:.7; }
                .notification-close:hover { opacity:1; }`;
            document.head.appendChild(s);
        }

        document.body.appendChild(n);
        setTimeout(() => n.style.transform = 'translateX(0)', 10);
        setTimeout(() => { n.style.transform = 'translateX(120%)'; setTimeout(() => n.remove(), 300); }, 5000);
        n.querySelector('.notification-close').addEventListener('click', () => {
            n.style.transform = 'translateX(120%)'; setTimeout(() => n.remove(), 300);
        });
    }
}

// Start dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.harmonicDashboard = new HarmonicDashboard();
});