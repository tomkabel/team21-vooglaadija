(function() {
    'use strict';
    
    /**
     * Show toast notification
     */
    function showToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            bottom: 1rem;
            right: 1rem;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            color: white;
            font-weight: 500;
            z-index: 9999;
            animation: slideIn 0.3s ease-out;
        `;
        
        // Set background color based on type
        switch (type) {
            case 'error':
                toast.style.backgroundColor = '#dc2626';
                break;
            case 'warning':
                toast.style.backgroundColor = '#f59e0b';
                break;
            case 'success':
                toast.style.backgroundColor = '#16a34a';
                break;
            default:
                toast.style.backgroundColor = '#3b82f6';
        }
        
        document.body.appendChild(toast);
        
        // Add animation keyframes if not already present
        if (!document.getElementById('toast-animations')) {
            const style = document.createElement('style');
            style.id = 'toast-animations';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
        
        // Remove after 5 seconds with animation
        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-out forwards';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
    
    /**
     * Initialize HTMX error handlers
     */
    function initHtmxErrorHandlers() {
        // Global HTMX error handler
        document.body.addEventListener('htmx:responseError', function(evt) {
            const xhr = evt.detail.xhr;
            
            switch (xhr.status) {
                case 401:
                    // Token expired or invalid
                    document.body.dispatchEvent(
                        new CustomEvent('auth:expired', {bubbles: true})
                    );
                    window.location.href = '/web/login?expired=1';
                    break;
                    
                case 403:
                    showToast('You do not have permission to perform this action', 'error');
                    break;
                    
                case 429: {
                    const retryAfter = xhr.getResponseHeader('Retry-After');
                    showToast(
                        retryAfter 
                            ? `Rate limited. Try again in ${retryAfter}s`
                            : 'Too many requests. Please wait before trying again.',
                        'warning'
                    );
                    break;
                }
                    
                default:
                    if (xhr.status >= 500) {
                        showToast('Server error. Please try again later.', 'error');
                    } else if (xhr.status >= 400) {
                        showToast('Request failed. Please check your input.', 'error');
                    }
            }
        });
        
        // Handle htmx:afterRequest for form validation errors
        document.body.addEventListener('htmx:afterRequest', function(evt) {
            const xhr = evt.detail.xhr;
            
            // Handle 422 Unprocessable Entity (validation errors)
            if (xhr.status === 422) {
                const target = evt.detail.target;
                if (target) {
                    // Try to parse error from response
                    try {
                        const response = JSON.parse(xhr.responseText);
                        if (response.error && response.error.message) {
                            showToast(response.error.message, 'error');
                        }
                    } catch (e) {
                        // If not JSON, use response text directly
                        if (xhr.responseText) {
                            showToast(xhr.responseText, 'error');
                        }
                    }
                }
            }
        });
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initHtmxErrorHandlers);
    } else {
        initHtmxErrorHandlers();
    }
    
    // Expose globally
    window.htmxErrorHandler = { showToast };
})();