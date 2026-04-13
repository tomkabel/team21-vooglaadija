(function () {
    "use strict";

    const passwordForm = document.getElementById("password-change-form");
    if (passwordForm) {
        passwordForm.addEventListener("submit", function (event) {
            const newPassword = document.getElementById("new_password");
            const confirmPassword = document.getElementById("new_password_confirm");

            if (!newPassword || !confirmPassword) return;

            if (newPassword.value !== confirmPassword.value) {
                event.preventDefault();
                window.showToast("New password and confirmation do not match.", "error");
            }
        });
    }

    const deleteForm = document.getElementById("delete-account-form");
    if (deleteForm) {
        deleteForm.addEventListener("submit", function (event) {
            const confirmInput = document.getElementById("confirm_text");
            const confirmValue = confirmInput ? confirmInput.value.trim().toUpperCase() : "";
            if (confirmValue !== "DELETE") {
                event.preventDefault();
                window.showToast('Type "DELETE" to confirm account deletion.', "warning");
                return;
            }

            const approved = window.confirm(
                "Are you sure? This permanently deletes your account and downloads."
            );
            if (!approved) {
                event.preventDefault();
            }
        });
    }
})();
