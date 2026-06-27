// Harmonic AI SaaS Dashboard - Main Application Script

class HarmonicDashboard {
    constructor() {
        this.apiBaseUrl = 'http://localhost:9000/api/v1';
        this.currentUser = null;
        this.audioJobs = [];
        this.videoJobs = [];
        this.stats = {
            audioJobsCount: 0,
            videoJobsCount: 0,
            monthlyUsage: 0,
            currentPlan: 'Free'
        };
        
        this.init();
    }
    
    async init() {
        this.setupEventListeners();
        this.loadTheme();
        await this.loadUserData();
        await this.loadStats();
        await this.loadAudioJobs();
        await this.loadVideoJobs();
        this.setupRealTimeUpdates();
    }
    
    setupEventListeners() {
        // Theme toggle
        document.getElementById('themeToggle').addEventListener('click', () => this.toggleTheme());
        
        // Refresh buttons
        document.getElementById('refreshAudioJobs').addEventListener('click', () => this.refreshAudioJobs());
        document.getElementById('refreshVideoJobs').addEventListener('click', () => this.refreshVideoJobs());
        
        // New job buttons
        document.getElementById('newAudioJob').addEventListener('click', () => this.showAudioJobModal());
        document.getElementById('newVideoJob').addEventListener('click', () => this.showVideoJobModal());
        
        // File uploads
        document.getElementById('audioFileInput').addEventListener('change', (e) => this.handleAudioUpload(e));
        document.getElementById('videoFileInput').addEventListener('change', (e) => this.handleVideoUpload(e));
        
        // User profile dropdown
        document.getElementById('userProfile').addEventListener('click', () => this.toggleUserMenu());
    }
    
    loadTheme() {
        const savedTheme = localStorage.getItem('harmonic_theme');
        if (savedTheme === 'light') {
            document.body.classList.add('light-mode');
            document.getElementById('themeToggle').querySelector('i').className = 'fas fa-sun';
        }
    }
    
    toggleTheme() {
        const themeIcon = document.getElementById('themeToggle').querySelector('i');
        const isLightMode = document.body.classList.toggle('light-mode');
        
        if (isLightMode) {
            themeIcon.className = 'fas fa-sun';
            localStorage.setItem('harmonic_theme', 'light');
        } else {
            themeIcon.className = 'fas fa-moon';
            localStorage.setItem('harmonic_theme', 'dark');
        }
    }
    
    async loadUserData() {
        try {
            // In a real app, this would be an API call
            // For now, simulate user data
            this.currentUser = {
                id: 'user_001',
                name: 'Alain KOTTO',
                email: 'alain@harmonic-ai.com',
                role: 'Administrator',
                subscription: 'Pro',
                joined: '2026-01-15'
            };
            
            // Update UI
            document.querySelector('.user-name').textContent = this.currentUser.name;
            document.querySelector('.user-role').textContent = this.currentUser.role;
            
        } catch (error) {
            console.error('Failed to load user data:', error);
            this.showNotification('Failed to load user data', 'error');
        }
    }
    
    async loadStats() {
        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 500));
            
            this.stats = {
                audioJobsCount: 24,
                videoJobsCount: 12,
                monthlyUsage: 36,
                currentPlan: 'Pro'
            };
            
            // Update UI
            document.getElementById('audioJobsCount').textContent = this.stats.audioJobsCount;
            document.getElementById('videoJobsCount').textContent = this.stats.videoJobsCount;
            document.getElementById('monthlyUsage').textContent = `${this.stats.monthlyUsage}%`;
            document.getElementById('currentPlan').textContent = this.stats.currentPlan;
            
        } catch (error) {
            console.error('Failed to load stats:', error);
            this.showNotification('Failed to load statistics', 'error');
        }
    }
    
    async loadAudioJobs() {
        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 300));
            
            this.audioJobs = [
                {
                    id: 'audio_001',
                    name: 'Podcast Episode 1',
                    status: 'completed',
                    created: '2026-05-15 14:30',
                    processingMode: 'hcs_restore',
                    processingTime: '45s',
                    qualityImprovement: '28%'
                },
                {
                    id: 'audio_002',
                    name: 'Interview Recording',
                    status: 'processing',
                    created: '2026-05-16 09:15',
                    processingMode: 'hcs_clarity',
                    processingTime: null,
                    qualityImprovement: null
                },
                {
                    id: 'audio_003',
                    name: 'Music Track Master',
                    status: 'pending',
                    created: '2026-05-17 11:45',
                    processingMode: 'hcs_dynamic',
                    processingTime: null,
                    qualityImprovement: null
                }
            ];
            
            this.renderAudioJobs();
            
        } catch (error) {
            console.error('Failed to load audio jobs:', error);
            this.showNotification('Failed to load audio jobs', 'error');
        }
    }
    
    async loadVideoJobs() {
        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 300));
            
            this.videoJobs = [
                {
                    id: 'video_001',
                    name: 'Product Demo 4K',
                    status: 'completed',
                    created: '2026-05-14 16:20',
                    processingMode: 'hcs_4k_clarity',
                    processingTime: '3m 15s',
                    qualityImprovement: '42%'
                },
                {
                    id: 'video_002',
                    name: 'Training Video',
                    status: 'failed',
                    created: '2026-05-16 13:10',
                    processingMode: 'hcs_hdr_vision',
                    processingTime: null,
                    qualityImprovement: null,
                    error: 'File format not supported'
                },
                {
                    id: 'video_003',
                    name: 'Event Recording',
                    status: 'pending',
                    created: '2026-05-17 10:05',
                    processingMode: 'hcs_frame_gen',
                    processingTime: null,
                    qualityImprovement: null
                }
            ];
            
            this.renderVideoJobs();
            
        } catch (error) {
            console.error('Failed to load video jobs:', error);
            this.showNotification('Failed to load video jobs', 'error');
        }
    }
    
    renderAudioJobs() {
        const container = document.getElementById('audioJobsList');
        
        if (this.audioJobs.length === 0) {
            container.innerHTML = `
                <div class="job-item">
                    <div class="job-info">
                        <h3>No audio jobs yet</h3>
                        <div class="job-meta">
                            <span>Upload a file to get started</span>
                        </div>
                    </div>
                    <div class="job-status status-pending">Pending</div>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.audioJobs.map(job => `
            <div class="job-item" data-job-id="${job.id}">
                <div class="job-info">
                    <h3>${job.name}</h3>
                    <div class="job-meta">
                        <span><i class="far fa-clock"></i> ${this.formatDate(job.created)}</span>
                        <span><i class="fas fa-tag"></i> ${job.processingMode.replace('hcs_', '').toUpperCase()}</span>
                        ${job.processingTime ? `<span><i class="fas fa-stopwatch"></i> ${job.processingTime}</span>` : ''}
                        ${job.qualityImprovement ? `<span><i class="fas fa-chart-line"></i> +${job.qualityImprovement}</span>` : ''}
                    </div>
                </div>
                <div class="job-status status-${job.status}">
                    ${job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                </div>
            </div>
        `).join('');
    }
    
    renderVideoJobs() {
        const container = document.getElementById('videoJobsList');
        
        if (this.videoJobs.length === 0) {
            container.innerHTML = `
                <div class="job-item">
                    <div class="job-info">
                        <h3>No video jobs yet</h3>
                        <div class="job-meta">
                            <span>Upload a file to get started</span>
                        </div>
                    </div>
                    <div class="job-status status-pending">Pending</div>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.videoJobs.map(job => `
            <div class="job-item" data-job-id="${job.id}">
                <div class="job-info">
                    <h3>${job.name}</h3>
                    <div class="job-meta">
                        <span><i class="far fa-clock"></i> ${this.formatDate(job.created)}</span>
                        <span><i class="fas fa-tag"></i> ${job.processingMode.replace('hcs_', '').toUpperCase()}</span>
                        ${job.processingTime ? `<span><i class="fas fa-stopwatch"></i> ${job.processingTime}</span>` : ''}
                        ${job.qualityImprovement ? `<span><i class="fas fa-chart-line"></i> +${job.qualityImprovement}</span>` : ''}
                        ${job.error ? `<span><i class="fas fa-exclamation-circle"></i> ${job.error}</span>` : ''}
                    </div>
                </div>
                <div class="job-status status-${job.status}">
                    ${job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                </div>
            </div>
        `).join('');
    }
    
    async handleAudioUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Validate file
        const maxSize = 100 * 1024 * 1024; // 100MB
        if (file.size > maxSize) {
            this.showNotification('File too large. Maximum size is 100MB.', 'error');
            return;
        }
        
        const allowedExtensions = ['.mp3', '.wav', '.flac', '.m4a', '.aac'];
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedExtensions.includes(fileExt)) {
            this.showNotification(`Invalid file type. Allowed: ${allowedExtensions.join(', ')}`, 'error');
            return;
        }
        
        // Show upload progress
        const uploadArea = document.getElementById('audioUploadArea');
        const originalHTML = uploadArea.innerHTML;
        
        uploadArea.innerHTML = `
            <div class="upload-progress">
                <i class="fas fa-spinner fa-spin"></i>
                <h3>Uploading ${file.name}</h3>
                <div class="progress-bar">
                    <div class="progress-fill" id="audioProgressFill"></div>
                </div>
                <p>Please wait...</p>
            </div>
        `;
        
        // Simulate upload
        try {
            // In a real app, this would be an API call
            await this.simulateUpload(file, 'audio');
            
            // Create job
            const newJob = {
                id: `audio_${Date.now()}`,
                name: file.name,
                status: 'pending',
                created: new Date().toISOString(),
                processingMode: 'hcs_restore'
            };
            
            this.audioJobs.unshift(newJob);
            this.renderAudioJobs();
            
            // Update stats
            this.stats.audioJobsCount++;
            document.getElementById('audioJobsCount').textContent = this.stats.audioJobsCount;
            
            this.showNotification('Audio file uploaded successfully. Processing will start shortly.', 'success');
            
        } catch (error) {
            console.error('Upload failed:', error);
            this.showNotification('Upload failed. Please try again.', 'error');
        } finally {
            // Reset upload area
            setTimeout(() => {
                uploadArea.innerHTML = originalHTML;
            }, 2000);
        }
    }
    
    async handleVideoUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Validate file
        const maxSize = 100 * 1024 * 1024; // 100MB
        if (file.size > maxSize) {
            this.showNotification('File too large. Maximum size is 100MB.', 'error');
            return;
        }
        
        const allowedExtensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm'];
        const fileExt = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedExtensions.includes(fileExt)) {
            this.showNotification(`Invalid file type. Allowed: ${allowedExtensions.join(', ')}`, 'error');
            return;
        }
        
        // Show upload progress
        const uploadArea = document.getElementById('videoUploadArea');
        const originalHTML = uploadArea.innerHTML;
        
        uploadArea.innerHTML = `
            <div class="upload-progress">
                <i class="fas fa-spinner fa-spin"></i>
                <h3>Uploading ${file.name}</h3>
                <div class="progress-bar">
                    <div class="progress-fill" id="videoProgressFill"></div>
                </div>
                <p>Please wait...</p>
            </div>
        `;
        
        // Simulate upload
        try {
            // In a real app, this would be an API call
            await this.simulateUpload(file, 'video');
            
            // Create job
            const newJob = {
                id: `video_${Date.now()}`,
                name: file.name,
                status: 'pending',
                created: new Date().toISOString(),
                processingMode: 'hcs_4k_clarity'
            };
            
            this.videoJobs.unshift(newJob);
            this.renderVideoJobs();
            
            // Update stats
            this.stats.videoJobsCount++;
            document.getElementById('videoJobsCount').textContent = this.stats.videoJobsCount;
            
            this.showNotification('Video file uploaded successfully. Processing will start shortly.', 'success');
            
        } catch (error) {
            console.error('Upload failed:', error);
            this.showNotification('Upload failed. Please try again.', 'error');
        } finally {
            // Reset upload area
            setTimeout(() => {
                uploadArea.innerHTML = originalHTML;
            }, 2000);
        }
    }
    
    async simulateUpload(file, type) {
        return new Promise((resolve, reject) => {
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += 10;
                const progressFill = document.getElementById(`${type}ProgressFill`);
                
                if (progressFill) {
                    progressFill.style.width = `${progress}%`;
                }
                
                if (progress >= 100) {
                    clearInterval(progressInterval);
                    setTimeout(() => resolve(), 500);
                }
            }, 100);
        });
    }
    
    async refreshAudioJobs() {
        const refreshBtn = document.getElementById('refreshAudioJobs');
        const originalHTML = refreshBtn.innerHTML;
        
        refreshBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Refreshing...`;
        refreshBtn.disabled = true;
        
        try {
            await this.loadAudioJobs();
            this.showNotification('Audio jobs refreshed successfully', 'success');
        } catch (error) {
            console.error('Refresh failed:', error);
            this.showNotification('Failed to refresh audio jobs', 'error');
        } finally {
            refreshBtn.innerHTML = originalHTML;
            refreshBtn.disabled = false;
        }
    }
    
    async refreshVideoJobs() {
        const refreshBtn = document.getElementById('refreshVideoJobs');
        const originalHTML = refreshBtn.innerHTML;
        
        refreshBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Refreshing...`;
        refreshBtn.disabled = true;
        
        try {
            await this.loadVideoJobs();
            this.showNotification('Video jobs refreshed successfully', 'success');
        } catch (error) {
            console.error('Refresh failed:', error);
            this.showNotification('Failed to refresh video jobs', 'error');
        } finally {
            refreshBtn.innerHTML = originalHTML;
            refreshBtn.disabled = false;
        }
    }
    
    showAudioJobModal() {
        this.showProcessingModal('audio');
    }
    
    showVideoJobModal() {
        this.showProcessingModal('video');
    }
    
    showProcessingModal(type) {
        const modalId = `${type}ProcessingModal`;
        
        // Remove existing modal
        const existingModal = document.getElementById(modalId);
        if (existingModal) existingModal.remove();
        
        const modalHTML = `
            <div class="modal-overlay" id="${modalId}">
                <div class="modal">
                    <div class="modal-header">
                        <h3>New ${type.charAt(0).toUpperCase() + type.slice(1)} Processing Job</h3>
                        <button class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label for="${type}JobName">Job Name</label>
                            <input type="text" id="${type}JobName" class="form-control" placeholder="Enter job name">
                        </div>
                        
                        <div class="form-group">
                            <label for="${type}ProcessingMode">Processing Mode</label>
                            <select id="${type}ProcessingMode" class="form-control">
                                ${type === 'audio' ? `
                                    <option value="hcs_restore">HCS Restore</option>
                                    <option value="hcs_spatial">HCS Spatial</option>
                                    <option value="hcs_clarity">HCS Clarity</option>
                                    <option value="hcs_dynamic">HCS Dynamic</option>
                                ` : `
                                    <option value="hcs_4k_clarity">HCS 4K Clarity</option>
                                    <option value="hcs_8k_master">HCS 8K Master</option>
                                    <option value="hcs_hdr_vision">HCS HDR Vision</option>
                                    <option value="hcs_frame_gen">HCS Frame Generation</option>
                                    <option value="hcs_movie_continuous">HCS Continuous Movie</option>
                                `}
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="${type}CustomParams">Custom Parameters (JSON)</label>
                            <textarea id="${type}CustomParams" class="form-control" rows="3" placeholder='{"param1": "value1", "param2": "value2"}'></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary modal-cancel">Cancel</button>
                        <button class="btn btn-primary modal-submit">Create Job</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        const modal = document.getElementById(modalId);
        
        // Show modal
        setTimeout(() => {
            modal.style.opacity = '1';
            modal.style.pointerEvents = 'all';
        }, 10);
        
        // Setup event listeners
        const closeModal = () => {
            modal.style.opacity = '0';
            modal.style.pointerEvents = 'none';
            
            setTimeout(() => {
                modal.remove();
            }, 300);
        };
        
        modal.querySelector('.modal-close').addEventListener('click', closeModal);
        modal.querySelector('.modal-cancel').addEventListener('click', closeModal);
        
        modal.querySelector('.modal-submit').addEventListener('click', async () => {
            const jobName = document.getElementById(`${type}JobName`).value || `New ${type} job`;
            const processingMode = document.getElementById(`${type}ProcessingMode`).value;
            const customParams = document.getElementById(`${type}CustomParams`).value;
            
            try {
                // Create job
                const newJob = {
                    id: `${type}_${Date.now()}`,
                    name: jobName,
                    status: 'pending',
                    created: new Date().toISOString(),
                    processingMode: processingMode,
                    customParams: customParams ? JSON.parse(customParams) : {}
                };
                
                if (type === 'audio') {
                    this.audioJobs.unshift(newJob);
                    this.renderAudioJobs();
                    this.stats.audioJobsCount++;
                    document.getElementById('audioJobsCount').textContent = this.stats.audioJobsCount;
                } else {
                    this.videoJobs.unshift(newJob);
                    this.renderVideoJobs();
                    this.stats.videoJobsCount++;
                    document.getElementById('videoJobsCount').textContent = this.stats.videoJobsCount;
                }
                
                closeModal();
                this.showNotification(`${type.charAt(0).toUpperCase() + type.slice(1)} job created successfully`, 'success');
                
            } catch (error) {
                console.error('Failed to create job:', error);
                this.showNotification('Failed to create job. Invalid JSON parameters.', 'error');
            }
        });
        
        // Close on overlay click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
    
    toggleUserMenu() {
        // In a real app, this would show a dropdown menu
        console.log('User menu clicked');
    }
    
    setupRealTimeUpdates() {
        // Simulate real-time updates
        setInterval(() => {
            this.updateJobStatuses();
        }, 10000); // Update every 10 seconds
    }
    
    updateJobStatuses() {
        // Simulate status updates
        this.audioJobs.forEach(job => {
            if (job.status === 'pending') {
                job.status = 'processing';
            } else if (job.status === 'processing') {
                job.status = 'completed';
                job.processingTime = `${Math.floor(Math.random() * 60) + 30}s`;
                job.qualityImprovement = `${Math.floor(Math.random() * 30) + 10}%`;
            }
        });
        
        this.videoJobs.forEach(job => {
            if (job.status === 'pending') {
                job.status = 'processing';
            } else if (job.status === 'processing') {
                job.status = 'completed';
                job.processingTime = `${Math.floor(Math.random() * 5) + 1}m ${Math.floor(Math.random() * 60)}s`;
                job.qualityImprovement = `${Math.floor(Math.random() * 50) + 20}%`;
            }
        });
        
        this.renderAudioJobs();
        this.renderVideoJobs();
    }
    
    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close">&times;</button>
        `;
        
        // Add styles if not already present
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background-color: #1e293b;
                    color: white;
                    padding: 15px 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 15px;
                    z-index: 1000;
                    transform: translateX(120%);
                    transition: transform 0.3s ease;
                    max-width: 400px;
                }
                
                .light-mode .notification {
                    background-color: #ffffff;
                    color: #1e293b;
                    border: 1px solid #e2e8f0;
                }
                
                .notification-success {
                    border-left: 4px solid #10b981;
                }
                
                .notification-error {
                    border-left: 4px solid #ef4444;
                }
                
                .notification-info {
                    border-left: 4px solid #3b82f6;
                }
                
                .notification-content {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .notification-close {
                    background: none;
                    border: none;
                    color: inherit;
                    font-size: 20px;
                    cursor: pointer;
                    opacity: 0.7;
                    transition: opacity 0.2s;
                }
                
                .notification-close:hover {
                    opacity: 1;
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(120%)';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
        
        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.style.transform = 'translateX(120%)';
            setTimeout(() => {
                notification.remove();
            }, 300);
        });
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.harmonicDashboard = new HarmonicDashboard();
});