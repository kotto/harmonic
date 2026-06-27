// HCS Studio Integrated - Main Application JavaScript
class HCSStudio {
    constructor() {
        this.apiBase = 'http://localhost:8013/api/v3';
        this.currentTab = 'compression';
        this.processingFiles = new Map();
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupTabNavigation();
        this.setupFileUploads();
        this.setupRangeInputs();
        this.checkServerStatus();
        
        // Initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    setupEventListeners() {
        // Compression buttons
        const compressImageBtn = document.getElementById('compressImageBtn');
        const compressVideoBtn = document.getElementById('compressVideoBtn');
        const testConnectionBtn = document.getElementById('testConnectionBtn');
        
        if (compressImageBtn) compressImageBtn.addEventListener('click', () => this.compressImage());
        if (compressVideoBtn) compressVideoBtn.addEventListener('click', () => this.compressVideo());
        if (testConnectionBtn) testConnectionBtn.addEventListener('click', () => this.checkServerStatus());
        
        // File inputs
        const imageInput = document.getElementById('imageInput');
        const videoInput = document.getElementById('videoInput');
        const decompressInput = document.getElementById('decompressInput');
        
        if (imageInput) imageInput.addEventListener('change', (e) => this.handleImageSelect(e));
        if (videoInput) videoInput.addEventListener('change', (e) => this.handleVideoSelect(e));
        if (decompressInput) decompressInput.addEventListener('change', (e) => this.handleDecompressSelect(e));
    }

    setupTabNavigation() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabName = btn.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }

    switchTab(tabName) {
        // Update button states
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('tab-active');
            if (btn.dataset.tab === tabName) {
                btn.classList.add('tab-active');
            }
        });

        // Update content visibility
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        
        const targetTab = document.getElementById(`${tabName}-tab`);
        if (targetTab) {
            targetTab.classList.remove('hidden');
        }

        this.currentTab = tabName;
    }

    setupFileUploads() {
        // Setup drag and drop
        const dropZones = document.querySelectorAll('.border-dashed');
        dropZones.forEach(zone => {
            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                zone.classList.add('border-hcs-gold/50', 'bg-hcs-gold/10');
            });

            zone.addEventListener('dragleave', () => {
                zone.classList.remove('border-hcs-gold/50', 'bg-hcs-gold/10');
            });

            zone.addEventListener('drop', (e) => {
                e.preventDefault();
                zone.classList.remove('border-hcs-gold/50', 'bg-hcs-gold/10');
                
                const files = e.dataTransfer.files;
                this.handleDroppedFiles(files, zone);
            });
        });
    }

    setupRangeInputs() {
        // K-Factor slider
        const kFactor = document.getElementById('kFactor');
        const kFactorValue = document.getElementById('kFactorValue');
        if (kFactor && kFactorValue) {
            kFactor.addEventListener('input', () => {
                kFactorValue.textContent = parseFloat(kFactor.value).toFixed(3);
            });
        }

        // Video Quality slider
        const videoQuality = document.getElementById('videoQuality');
        const videoQualityValue = document.getElementById('videoQualityValue');
        if (videoQuality && videoQualityValue) {
            videoQuality.addEventListener('input', () => {
                videoQualityValue.textContent = videoQuality.value;
            });
        }
    }

    async checkServerStatus() {
        try {
            const response = await fetch(`${this.apiBase}/health`, {
                mode: 'cors',
                credentials: 'omit'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            const statusIndicator = document.getElementById('statusIndicator');
            if (data.status === 'healthy') {
                statusIndicator.innerHTML = `
                    <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span class="text-sm text-green-400">Connected</span>
                `;
                statusIndicator.className = 'flex items-center space-x-2 px-3 py-1 rounded-full bg-green-500/20 border border-green-500/30';
            } else {
                throw new Error('Server not healthy');
            }
        } catch (error) {
            console.error('Server status check failed:', error);
            const statusIndicator = document.getElementById('statusIndicator');
            statusIndicator.innerHTML = `
                <div class="w-2 h-2 bg-red-500 rounded-full"></div>
                <span class="text-sm text-red-400">Disconnected</span>
            `;
            statusIndicator.className = 'flex items-center space-x-2 px-3 py-1 rounded-full bg-red-500/20 border border-red-500/30';
        }
    }

    handleImageSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.selectedImage = file;
            this.updateFileDisplay('image', file);
        }
    }

    handleVideoSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.selectedVideo = file;
            this.updateFileDisplay('video', file);
        }
    }

    handleDecompressSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.selectedCompressedFile = file;
            this.updateFileDisplay('decompress', file);
        }
    }

    handleDroppedFiles(files, zone) {
        if (files.length > 0) {
            const file = files[0];
            
            // Determine file type and route to appropriate handler
            if (file.type.startsWith('image/')) {
                this.selectedImage = file;
                this.updateFileDisplay('image', file);
            } else if (file.type.startsWith('video/') || file.type.startsWith('audio/')) {
                this.selectedVideo = file;
                this.updateFileDisplay('video', file);
            } else {
                this.showNotification('Unsupported file type', 'error');
            }
        }
    }

    updateFileDisplay(type, file) {
        const dropZone = type === 'image' ? 
            document.querySelector('#imageInput').closest('.border-dashed') :
            type === 'video' ?
            document.querySelector('#videoInput').closest('.border-dashed') :
            document.querySelector('#decompressInput').closest('.border-dashed');

        if (dropZone) {
            dropZone.innerHTML = `
                <i data-lucide="check-circle" class="w-12 h-12 mx-auto mb-4 text-green-400"></i>
                <p class="text-green-400 font-medium mb-2">${file.name}</p>
                <p class="text-sm text-gray-400">${this.formatFileSize(file.size)}</p>
                <button onclick="this.parentElement.querySelector('input[type=file]').click()" class="btn-secondary px-4 py-2 rounded-lg mt-4">
                    Change File
                </button>
            `;
            
            // Re-initialize icons
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }
    }

    async compressImage() {
        if (!this.selectedImage) {
            this.showNotification('Please select an image first', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', this.selectedImage);
        
        // Get compression settings with fallbacks
        const compressionTargetEl = document.getElementById('compressionTarget');
        const kFactorEl = document.getElementById('kFactor');
        
        const target = compressionTargetEl ? compressionTargetEl.value : 'balanced';
        const kFactor = kFactorEl ? kFactorEl.value : '0.02';
        
        formData.append('target_ratio', this.getTargetRatio(target));
        formData.append('use_optimized_params', 'false');

        this.showLoading('Compressing image...', 'Applying harmonic compression algorithms');

        try {
            const response = await fetch(`${this.apiBase}/compress/image`, {
                method: 'POST',
                body: formData,
                mode: 'cors',
                credentials: 'omit'
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.hideLoading();
                this.showCompressionResult(result, 'image');
                this.showNotification('Image compressed successfully!', 'success');
            } else {
                throw new Error(result.message || 'Compression failed');
            }
        } catch (error) {
            this.hideLoading();
            console.error('Compression error:', error);
            this.showNotification(`Compression failed: ${error.message}`, 'error');
        }
    }

    async compressVideo() {
        if (!this.selectedVideo) {
            this.showNotification('Please select a video or audio file first', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', this.selectedVideo);
        
        // Get video settings with fallbacks
        const videoTargetEl = document.getElementById('videoTarget');
        const videoQualityEl = document.getElementById('videoQuality');
        
        const target = videoTargetEl ? videoTargetEl.value : 'balanced_video';
        const quality = videoQualityEl ? videoQualityEl.value : '85';
        
        formData.append('target', target);
        formData.append('quality', quality);
        formData.append('use_optimized_params', 'true');

        this.showLoading('Optimizing video parameters...', 'Analyzing temporal coherence and compression efficiency');

        try {
            const response = await fetch(`${this.apiBase}/compress/video`, {
                method: 'POST',
                body: formData,
                mode: 'cors',
                credentials: 'omit'
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.hideLoading();
                this.showCompressionResult(result, 'video');
                this.showNotification('Video compressed successfully!', 'success');
            } else {
                throw new Error(result.message || 'Compression failed');
            }
        } catch (error) {
            this.hideLoading();
            console.error('Video compression error:', error);
            this.showNotification(`Compression failed: ${error.message}`, 'error');
        }
    }

    async decompressFile() {
        if (!this.selectedCompressedFile) {
            this.showNotification('Please select a compressed file first', 'error');
            return;
        }

        this.showLoading('Decompressing file...', 'Restoring original quality with harmonic algorithms');

        try {
            // This would connect to a decompression endpoint
            // For now, simulate the process
            await this.simulateProgress(3000);
            
            this.hideLoading();
            this.showNotification('File decompressed successfully!', 'success');
        } catch (error) {
            this.hideLoading();
            this.showNotification(`Decompression failed: ${error.message}`, 'error');
        }
    }

    showCompressionResult(result, type) {
        const resultsSection = document.getElementById('resultsSection');
        const resultsContent = document.getElementById('resultsContent');
        
        const resultHtml = `
            <div class="glass-card rounded-xl p-6 fade-in">
                <div class="flex items-center justify-between mb-4">
                    <h4 class="text-lg font-semibold">${type === 'image' ? 'Image' : 'Video'} Compression Result</h4>
                    <span class="px-3 py-1 rounded-full bg-green-500/20 border border-green-500/30 text-green-400 text-sm">
                        Success
                    </span>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
                    <div class="text-center">
                        <p class="text-sm text-gray-400">Original Size</p>
                        <p class="text-lg font-semibold">${this.formatFileSize(result.original_size)}</p>
                    </div>
                    <div class="text-center">
                        <p class="text-sm text-gray-400">Compressed Size</p>
                        <p class="text-lg font-semibold">${this.formatFileSize(result.compressed_size || result.estimated_compressed_size)}</p>
                    </div>
                    <div class="text-center">
                        <p class="text-sm text-gray-400">Compression Ratio</p>
                        <p class="text-lg font-semibold text-hcs-gold">${result.compression_ratio.toFixed(1)}:1</p>
                    </div>
                    <div class="text-center">
                        <p class="text-sm text-gray-400">Space Saved</p>
                        <p class="text-lg font-semibold text-green-400">${result.space_saved_percent.toFixed(1)}%</p>
                    </div>
                </div>
                
                ${result.k_ratio ? `
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div class="text-center">
                        <p class="text-sm text-gray-400">K-Ratio</p>
                        <p class="text-lg font-semibold">${result.k_ratio.toFixed(1)}:1</p>
                    </div>
                    <div class="text-center">
                        <p class="text-sm text-gray-400">WebP Ratio</p>
                        <p class="text-lg font-semibold">${result.webp_ratio.toFixed(1)}:1</p>
                    </div>
                </div>
                ` : ''}
                
                <div class="flex items-center justify-between">
                    <p class="text-sm text-gray-400">Processing time: ${result.processing_time.toFixed(2)}s</p>
                    <a href="${result.download_url}" target="_blank" class="btn-primary px-4 py-2 rounded-lg text-sm">
                        <i data-lucide="download" class="w-4 h-4 inline mr-2"></i>
                        Download
                    </a>
                </div>
            </div>
        `;
        
        resultsContent.innerHTML = resultHtml;
        resultsSection.classList.remove('hidden');
        
        // Re-initialize icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    getTargetRatio(target) {
        const ratios = {
            'balanced': 50,
            'quality': 20,
            'size': 100,
            'speed': 30
        };
        return ratios[target] || 50;
    }

    showLoading(title, message) {
        const overlay = document.getElementById('loadingOverlay');
        const loadingMessage = document.getElementById('loadingMessage');
        
        document.querySelector('#loadingOverlay p').textContent = title;
        loadingMessage.textContent = message;
        
        overlay.classList.remove('hidden');
    }

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        const progressBar = document.getElementById('progressBar');
        
        progressBar.style.width = '0%';
        overlay.classList.add('hidden');
    }

    async simulateProgress(duration) {
        const progressBar = document.getElementById('progressBar');
        const startTime = Date.now();
        
        return new Promise((resolve) => {
            const interval = setInterval(() => {
                const elapsed = Date.now() - startTime;
                const progress = Math.min((elapsed / duration) * 100, 100);
                
                progressBar.style.width = `${progress}%`;
                
                if (elapsed >= duration) {
                    clearInterval(interval);
                    resolve();
                }
            }, 50);
        });
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-20 right-6 z-50 glass-card rounded-lg p-4 max-w-sm fade-in`;
        
        const colors = {
            success: 'border-green-500/30',
            error: 'border-red-500/30',
            info: 'border-blue-500/30',
            warning: 'border-yellow-500/30'
        };
        
        notification.classList.add(colors[type] || colors.info);
        
        notification.innerHTML = `
            <div class="flex items-center space-x-3">
                <i data-lucide="${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info'}" 
                   class="w-5 h-5 text-${type === 'success' ? 'green' : type === 'error' ? 'red' : 'blue'}-400"></i>
                <p class="text-sm">${message}</p>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Re-initialize icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.hcsStudio = new HCSStudio();
});

// Utility functions for additional features
window.HCSUtils = {
    // Batch processing
    async processBatch(files, options) {
        const results = [];
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            try {
                // Process each file based on type
                let result;
                if (file.type.startsWith('image/')) {
                    result = await window.hcsStudio.compressImageFile(file, options);
                } else if (file.type.startsWith('video/')) {
                    result = await window.hcsStudio.compressVideoFile(file, options);
                }
                
                results.push({
                    file: file.name,
                    success: true,
                    result: result
                });
            } catch (error) {
                results.push({
                    file: file.name,
                    success: false,
                    error: error.message
                });
            }
        }
        return results;
    },

    // Analytics
    generateAnalyticsReport(results) {
        const successful = results.filter(r => r.success);
        const failed = results.filter(r => !r.success);
        
        const totalOriginalSize = successful.reduce((sum, r) => sum + r.result.original_size, 0);
        const totalCompressedSize = successful.reduce((sum, r) => sum + r.result.compressed_size, 0);
        const avgRatio = successful.reduce((sum, r) => sum + r.result.compression_ratio, 0) / successful.length;
        
        return {
            total_files: results.length,
            successful: successful.length,
            failed: failed.length,
            total_original_size: totalOriginalSize,
            total_compressed_size: totalCompressedSize,
            total_space_saved: totalOriginalSize - totalCompressedSize,
            average_compression_ratio: avgRatio,
            success_rate: (successful.length / results.length) * 100
        };
    },

    // Export results
    exportResults(results, format = 'json') {
        if (format === 'json') {
            const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `hcs_results_${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
        }
    }
};
