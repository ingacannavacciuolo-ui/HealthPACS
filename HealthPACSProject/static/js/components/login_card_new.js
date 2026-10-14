/* login_card.js */
document.addEventListener('DOMContentLoaded', () => {
    const togglePasswordBtn = document.getElementById('togglePasswordBtn');
    const passwordInput = document.getElementById('password');
    const eyeIcon = document.getElementById('eyeIcon');
    const loginForm = document.getElementById('loginForm');
    const errorAlert = document.getElementById('loginErrorAlert');

    // Toggle mostra/nascondi password
    if (togglePasswordBtn && passwordInput && eyeIcon) {
        togglePasswordBtn.addEventListener('click', () => {
            const isPassword = passwordInput.getAttribute('type') === 'password';
            passwordInput.setAttribute('type', isPassword ? 'text' : 'password');
            eyeIcon.style.opacity = isPassword ? '0.35' : '1';
        });
    }

    // Gestione invio Form di Login
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('username').value;
            const password = passwordInput.value;

            // Pulisce errori locali precedenti
            if (errorAlert) {
                errorAlert.style.display = 'none';
                errorAlert.textContent = '';
            }

            try {
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                if (response.ok) {
                    // Login concesso -> Entra nell'app
                    window.location.href = '/querystudies';
                    return;
                }

                const data = await response.json();
                const detail = data.detail || {};

                // 1. CREDENZIALI ERRATE -> Mostra div rosso nel form (.login-error-alert)
                if (detail.code === "BAD_CREDENTIALS" || response.status === 400) {
                    if (errorAlert) {
                        errorAlert.textContent = detail.message || "Username o password errati.";
                        errorAlert.style.display = 'block';
                    }
                } 
                // 2. UTENTE NON AUTORIZZATO -> Mostra Card Arancione tramite alertServerCard
                else if (detail.notify_key === "LOGIN_UNAUTHORIZED" || response.status === 401) {
                    if (window.alertServerCard) {
                        window.alertServerCard.renderAlert({
                            notify_key: "LOGIN_UNAUTHORIZED",
                            severity: "WARNING",
                            message: detail.message || "Utente non autorizzato ad accedere al sistema.",
                            permanent: false
                        });
                    }
                }

            } catch (err) {
                console.error("Errore durante il login:", err);
            }
        });
    }
});