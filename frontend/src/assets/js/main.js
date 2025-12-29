// DrugTox-AI Enhanced Dashboard JavaScript

// Global variables
let currentUser = 'Researcher';
let isLoading = false;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    updateLastActivity();
});

// Initialize dashboard components
function initializeDashboard() {
    // Check if we're on the dashboard page
    if (window.location.pathname === '/') {
        loadDashboardStats();
        loadRecentActivity();
    }
    
    // Setup navigation active states
    updateNavigationStates();
    
    // Setup tooltips
    setupTooltips();
}

// Setup global event listeners
function setupEventListeners() {
    // Navigation links
    document.querySelectorAll('.nav a').forEach(link => {
        link.addEventListener('click', function(e) {
            // Add loading state for navigation
            showPageLoader();
        });
    });
    
    // Global keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            focusSearch();
        }
        
        // Ctrl/Cmd + N for new prediction
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            window.location.href = '/predict';
        }
    });
    
    // Window resize handler
    window.addEventListener('resize', debounce(handleResize, 250));
}

// Load dashboard statistics
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        updateStatCards(stats);
        updateSystemStatus(stats);
        
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
        showNotification('Failed to load dashboard statistics', 'error');
    }
}

// Update stat cards
function updateStatCards(stats) {
    const statElements = {
        'total_predictions': stats.total_predictions || 0,
        'predictions_24h': stats.predictions_24h || 0,
        'predictions_7d': stats.predictions_7d || 0,
        'active_endpoints': stats.active_endpoints || 0
    };
    
    for (const [key, value] of Object.entries(statElements)) {
        const element = document.querySelector(`[data-stat="${key}"]`);
        if (element) {
            animateCounter(element, value);
        }
    }
}

// Animate counter
function animateCounter(element, target) {
    const start = parseInt(element.textContent) || 0;
    const duration = 1000;
    const startTime = performance.now();
    
    function updateCounter(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = Math.floor(start + (target - start) * easeOutCubic(progress));
        element.textContent = current.toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        }
    }
    
    requestAnimationFrame(updateCounter);
}

// Easing function
function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
}

// Update system status
function updateSystemStatus(stats) {
    const statusElement = document.querySelector('.status-indicator');
    if (statusElement) {
        const dot = statusElement.querySelector('.status-dot');
        const text = statusElement.querySelector('span:last-child');
        
        if (stats.model_status === 'Active') {
            dot.style.backgroundColor = 'var(--success-color)';
            text.textContent = 'System Active';
        } else {
            dot.style.backgroundColor = 'var(--warning-color)';
            text.textContent = 'Mock Mode';
        }
    }
}

// Show page loader
function showPageLoader() {
    if (document.querySelector('.page-loader')) return;
    
    const loader = document.createElement('div');
    loader.className = 'page-loader';
    loader.innerHTML = `
        <div class="page-loader-content">
            <div class="spinner"></div>
            <div>Loading...</div>
        </div>
    `;
    
    document.body.appendChild(loader);
    
    // Remove loader after navigation or timeout
    setTimeout(() => {
        const loaderElement = document.querySelector('.page-loader');
        if (loaderElement) {
            loaderElement.remove();
        }
    }, 2000);
}

// Update navigation states
function updateNavigationStates() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav a');
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === currentPath || 
            (currentPath === '/' && link.getAttribute('href') === '/')) {
            link.classList.add('active');
        }
    });
}

// Setup tooltips
function setupTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

// Show tooltip
function showTooltip(e) {
    const text = e.target.getAttribute('data-tooltip');
    if (!text) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    
    document.body.appendChild(tooltip);
    
    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
    
    e.target._tooltip = tooltip;
}

// Hide tooltip
function hideTooltip(e) {
    if (e.target._tooltip) {
        e.target._tooltip.remove();
        delete e.target._tooltip;
    }
}

// Show notification
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span>${message}</span>
            <button class="notification-close">&times;</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove
    setTimeout(() => {
        notification.classList.add('notification-fade-out');
        setTimeout(() => notification.remove(), 300);
    }, duration);
    
    // Manual close
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.classList.add('notification-fade-out');
        setTimeout(() => notification.remove(), 300);
    });
}

// Focus search (if search exists)
function focusSearch() {
    const searchInput = document.querySelector('input[type="search"], input[placeholder*="search" i]');
    if (searchInput) {
        searchInput.focus();
        searchInput.select();
    }
}

// Handle window resize
function handleResize() {
    // Update any responsive components
    updateChartSizes();
    adjustMobileLayout();
}

// Update chart sizes (placeholder)
function updateChartSizes() {
    // Placeholder for chart resize logic
}

// Adjust mobile layout
function adjustMobileLayout() {
    const isMobile = window.innerWidth < 768;
    const header = document.querySelector('.header-content');
    
    if (header) {
        if (isMobile) {
            header.classList.add('mobile-layout');
        } else {
            header.classList.remove('mobile-layout');
        }
    }
}

// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Update last activity
function updateLastActivity() {
    const lastUpdateElements = document.querySelectorAll('#lastUpdate, [data-last-update]');
    
    function updateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        
        lastUpdateElements.forEach(element => {
            element.textContent = timeString;
        });
    }
    
    updateTime();
    setInterval(updateTime, 60000); // Update every minute
}

// Load recent activity (placeholder)
function loadRecentActivity() {
    // This would load recent predictions, system events, etc.
}

// API helper functions
const API = {
    async get(endpoint) {
        const response = await fetch(endpoint);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    },
    
    async post(endpoint, data) {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    },
    
    async uploadFile(endpoint, file, onProgress = null) {
        const formData = new FormData();
        formData.append('file', file);
        
        const xhr = new XMLHttpRequest();
        
        return new Promise((resolve, reject) => {
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    onProgress(percentComplete);
                }
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    reject(new Error(`Upload failed: ${xhr.statusText}`));
                }
            });
            
            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed'));
            });
            
            xhr.open('POST', endpoint);
            xhr.send(formData);
        });
    }
};

// Export API for global use
window.DrugToxAPI = API;

// Utility functions
const Utils = {
    formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    },
    
    formatDate(date) {
        return new Intl.DateTimeFormat().format(new Date(date));
    },
    
    formatDateTime(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    },
    
    copyToClipboard(text) {
        return navigator.clipboard.writeText(text);
    },
    
    downloadBlob(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
};

// Export Utils for global use
window.DrugToxUtils = Utils;

// Initialize theme handling
function initializeTheme() {
    const savedTheme = localStorage.getItem('drugtox-theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

// Toggle theme (for future dark mode support)
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('drugtox-theme', newTheme);
}

// Initialize theme on load
initializeTheme();

// Console welcome message
console.log('%c🧬 DrugTox-AI Enhanced Dashboard', 'color: #00A651; font-size: 16px; font-weight: bold;');
console.log('%cWelcome to the DrugTox-AI Enhanced web interface!', 'color: #2D3748; font-size: 12px;');
console.log('%cDeveloped by Gaurav Patil (@GauravPatil2515)', 'color: #718096; font-size: 10px;');