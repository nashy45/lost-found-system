/**
 * Auto-Update Statistics Module
 * Automatically fetches and updates statistics on the page
 */

class StatsUpdater {
    constructor(config = {}) {
        this.updateInterval = config.updateInterval || 10000; // Default 10 seconds
        this.apiEndpoint = config.apiEndpoint || '/api/stats/global';
        this.intervalId = null;
        this.isUpdating = false;
        this.lastUpdate = null;
        
        // Animation settings
        this.animationDuration = 600;
        
        // Initialize
        this.init();
    }
    
    init() {
        // Start auto-update
        this.startAutoUpdate();
        
        // Update immediately on page load
        this.updateStats();
        
        // Pause updates when tab is not visible
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAutoUpdate();
            } else {
                this.startAutoUpdate();
                this.updateStats(); // Update immediately when returning
            }
        });
        
        // Update on window focus
        window.addEventListener('focus', () => {
            this.updateStats();
        });
    }
    
    startAutoUpdate() {
        if (this.intervalId) return; // Already running
        
        this.intervalId = setInterval(() => {
            this.updateStats();
        }, this.updateInterval);
        
        console.log('Stats auto-update started');
    }
    
    pauseAutoUpdate() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            console.log('Stats auto-update paused');
        }
    }
    
    stopAutoUpdate() {
        this.pauseAutoUpdate();
    }
    
    async updateStats() {
        if (this.isUpdating) return; // Prevent concurrent updates
        
        this.isUpdating = true;
        
        try {
            const response = await fetch(this.apiEndpoint);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.applyUpdates(data);
            this.lastUpdate = new Date();
            
            // Update "Last updated" text if element exists
            this.updateTimestamp();
            
        } catch (error) {
            console.error('Error updating stats:', error);
        } finally {
            this.isUpdating = false;
        }
    }
    
    applyUpdates(data) {
        // Update each stat with animation
        Object.keys(data).forEach(key => {
            const elements = document.querySelectorAll(`[data-stat="${key}"]`);
            
            elements.forEach(element => {
                const currentValue = parseInt(element.textContent) || 0;
                const newValue = data[key];
                
                if (currentValue !== newValue) {
                    this.animateValue(element, currentValue, newValue);
                    
                    // Add pulse animation
                    element.classList.add('stat-updated');
                    setTimeout(() => {
                        element.classList.remove('stat-updated');
                    }, this.animationDuration);
                }
            });
        });
    }
    
    animateValue(element, start, end) {
        const duration = this.animationDuration;
        const startTime = performance.now();
        
        const step = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function (ease-out)
            const easeOut = 1 - Math.pow(1 - progress, 3);
            
            const current = Math.floor(start + (end - start) * easeOut);
            
            // Handle percentage values
            if (element.dataset.statType === 'percentage') {
                element.textContent = current + '%';
            } else {
                element.textContent = current;
            }
            
            if (progress < 1) {
                requestAnimationFrame(step);
            } else {
                // Ensure final value is set
                if (element.dataset.statType === 'percentage') {
                    element.textContent = end + '%';
                } else {
                    element.textContent = end;
                }
            }
        };
        
        requestAnimationFrame(step);
    }
    
    updateTimestamp() {
        const timestampElements = document.querySelectorAll('[data-last-update]');
        
        if (this.lastUpdate && timestampElements.length > 0) {
            const timeString = this.lastUpdate.toLocaleTimeString();
            
            timestampElements.forEach(element => {
                element.textContent = `Last updated: ${timeString}`;
            });
        }
    }
    
    forceUpdate() {
        return this.updateStats();
    }
}

// Initialize based on page context
let statsUpdater = null;

// Wait for DOM to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStatsUpdater);
} else {
    initStatsUpdater();
}

function initStatsUpdater() {
    // Detect which page we're on and use appropriate endpoint
    const body = document.body;
    let apiEndpoint = '/api/stats/global';
    let updateInterval = 10000; // 10 seconds default
    
    if (body.classList.contains('admin-body') || body.querySelector('.admin-dashboard')) {
        // Admin pages
        apiEndpoint = '/api/stats/admin';
        updateInterval = 5000; // 5 seconds for admin
    } else if (body.querySelector('.user-dashboard')) {
        // User dashboard
        apiEndpoint = '/api/stats/user';
        updateInterval = 10000; // 10 seconds
    }
    
    // Initialize updater
    statsUpdater = new StatsUpdater({
        apiEndpoint: apiEndpoint,
        updateInterval: updateInterval
    });
    
    // Make it globally accessible
    window.statsUpdater = statsUpdater;
    
    console.log(`Stats updater initialized with endpoint: ${apiEndpoint}`);
}

// Add CSS for update animation
const style = document.createElement('style');
style.textContent = `
    @keyframes statPulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.1);
        }
    }
    
    .stat-updated {
        animation: statPulse 0.6s ease-in-out;
        color: #2563eb !important;
    }
    
    [data-last-update] {
        font-size: 12px;
        color: #6b7280;
        font-style: italic;
        margin-top: 8px;
        display: block;
    }
    
    .stats-refresh-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #10b981;
        border-radius: 50%;
        margin-left: 8px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.3;
        }
    }
`;
document.head.appendChild(style);
