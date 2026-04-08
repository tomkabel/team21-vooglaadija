(function () {
  "use strict";

  /**
   * Initialize HTMX error handlers
   */
  function initHtmxErrorHandlers() {
    // Global HTMX error handler
    document.body.addEventListener("htmx:responseError", function (evt) {
      const xhr = evt.detail.xhr;

      switch (xhr.status) {
        case 401:
          // Token expired or invalid - redirect to login
          window.location.href = "/web/login?expired=1";
          break;

        case 403:
          window.showToast(
            "You do not have permission to perform this action",
            "error",
          );
          break;

        case 429: {
          const retryAfter = xhr.getResponseHeader("Retry-After");
          window.showToast(
            retryAfter
              ? `Rate limited. Try again in ${retryAfter}s`
              : "Too many requests. Please wait before trying again.",
            "warning",
          );
          break;
        }

        default:
          if (xhr.status >= 500) {
            window.showToast("Server error. Please try again later.", "error");
          } else if (xhr.status >= 400) {
            window.showToast(
              "Request failed. Please check your input.",
              "error",
            );
          }
      }
    });

    // Handle htmx:afterRequest for form validation errors
    document.body.addEventListener("htmx:afterRequest", function (evt) {
      const xhr = evt.detail.xhr;

      // Handle 422 Unprocessable Entity (validation errors)
      if (xhr.status === 422) {
        // Try to parse error from response
        let errorMessage = null;
        try {
          const response = JSON.parse(xhr.responseText);
          // Check various error response shapes in order of specificity
          if (response.error && response.error.message) {
            errorMessage = response.error.message;
          } else if (response.message) {
            errorMessage = response.message;
          } else if (response.error) {
            // response.error could be a string or object with other fields
            errorMessage =
              typeof response.error === "string"
                ? response.error
                : response.error.error ||
                  response.error.detail ||
                  JSON.stringify(response.error);
          } else if (response.errors && Array.isArray(response.errors)) {
            // Field-level validation errors - join them
            errorMessage = response.errors
              .map((e) => e.message || JSON.stringify(e))
              .join("; ");
          } else if (response.detail) {
            errorMessage = response.detail;
          }
        } catch (e) {
          // If not JSON, continue to HTML extraction below
        }

        if (errorMessage) {
          // Sanitize HTML by extracting text content using DOM
          const tempDiv = document.createElement("div");
          tempDiv.textContent = errorMessage; // This safely escapes HTML
          const sanitized = tempDiv.textContent.trim();
          window.showToast(
            sanitized || "Request failed. Please try again.",
            "error",
          );
        } else if (xhr.responseText) {
          // Fall back to extracting plain text from HTML response
          const tempDiv = document.createElement("div");
          tempDiv.innerHTML = xhr.responseText;
          const plainText = (
            tempDiv.textContent ||
            tempDiv.innerText ||
            ""
          ).trim();
          if (plainText) {
            window.showToast(plainText, "error");
          } else {
            window.showToast("Request failed. Please try again.", "error");
          }
        } else {
          // No response body - still show generic error
          window.showToast("Request failed. Please try again.", "error");
        }
      }
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initHtmxErrorHandlers);
  } else {
    initHtmxErrorHandlers();
  }

  // Expose globally
  window.htmxErrorHandler = {};
})();
