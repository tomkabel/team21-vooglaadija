(function() {
    'use strict';
    
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
                    window.showToast('You do not have permission to perform this action', 'error');
                    break;
                    
                case 429: {
                    const retryAfter = xhr.getResponseHeader('Retry-After');
                    window.showToast(
                        retryAfter 
                            ? `Rate limited. Try again in ${retryAfter}s`
                            : 'Too many requests. Please wait before trying again.',
                        'warning'
                    );
                    break;
                }
                    
                default:
                    if (xhr.status >= 500) {
                        window.showToast('Server error. Please try again later.', 'error');
                    } else if (xhr.status >= 400) {
                        window.showToast('Request failed. Please check your input.', 'error');
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
                            window.showToast(response.error.message, 'error');
                        }
                    } catch (e) {
                        // If not JSON, extract plain text from HTML response
                        if (xhr.responseText) {
                            const tempDiv = document.createElement('div');
                            tempDiv.innerHTML = xhr.responseText;
                            const plainText = tempDiv.textContent || tempDiv.innerText || '';
                            const trimmedText = plainText.trim();
                            if (trimmedText) {
                                window.showToast(trimmedText, 'error');
                            } else {
                                window.showToast('Request failed. Please try again.', 'error');
                            }
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
    window.htmxErrorHandler = {};
})();