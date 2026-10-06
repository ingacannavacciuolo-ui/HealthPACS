/* Logica isolata per il componente Login Card */
document.addEventListener('DOMContentLoaded', () => {
    const togglePasswordBtn = document.getElementById('togglePasswordBtn');
    const passwordInput = document.getElementById('password');
    const eyeIcon = document.getElementById('eyeIcon');

    if (togglePasswordBtn && passwordInput && eyeIcon) {
        togglePasswordBtn.addEventListener('click', () => {
            const isPassword = passwordInput.getAttribute('type') === 'password';
            passwordInput.setAttribute('type', isPassword ? 'text' : 'password');
            
            // Riduce l'opacità quando la password è visibile
            eyeIcon.style.opacity = isPassword ? '0.35' : '1';
        });
    }
});