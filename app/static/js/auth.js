(function() {
    'use strict';
    
    // Public pages that don't need auth
    const PUBLIC_PAGES = ['/login', '/register', '/health'];
    
    /**
     * Get access token from cookie
     */
    function getAccessTokenFromCookie() {
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'access_token') {
                return value;
            }
        }
        return null;
    }
    
    /**
     * Parse JWT expiry without decoding the signature
     */
    function parseJwtExpiry(token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            return payload.exp;
        } catch (e) {
            return null;
        }
    }
    
    /**
     * Show toast notification
     */
    function showToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 5000);
    }
    
    /**
     * Refresh access token
     */
    async function refreshAccessToken() {
        try {
            const response = await fetch('/api/v1/auth/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',  // Include cookies automatically
            });
            
            if (!response.ok) throw new Error('Refresh failed');
            return true;
        } catch (error) {
            console.error('Token refresh failed:', error);
            return false;
        }
    }
    
    /**
     * Initialize authentication on page load
     */
    async function initAuth() {
        // Check if we're on a public page (no auth needed)
        if (PUBLIC_PAGES.includes(window.location.pathname)) return;
        
        // Check for logged out session message
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('logged_out') === '1') {
            showToast('You have been logged out successfully.', 'info');
            window.history.replaceState({}, '', window.location.pathname);
        }
        
        // Check for expired session message
        if (urlParams.get('expired') === '1') {
            showToast('Your session has expired. Please log in again.', 'info');
            window.history.replaceState({}, '', window.location.pathname);
        }
        
        // Proactively refresh token if it expires soon (5 min buffer)
        const token = getAccessTokenFromCookie();
        if (token) {
            const expiry = parseJwtExpiry(token);
            const now = Date.now() / 1000;
            const bufferSeconds = 300; // 5 minutes
            
            if (expiry && expiry - now < bufferSeconds) {
                const refreshed = await refreshAccessToken();
                if (!refreshed) {
                    window.location.href = '/login';
                    return;
                }
            }
        }
    }
    
    // Run on every page load
    initAuth();
    
    // Expose functions globally for manual use
    window.auth = {
        refreshAccessToken,
        getAccessTokenFromCookie,
        showToast
    };
})();