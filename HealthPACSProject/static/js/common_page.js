/* common_page.js - Logica e intercettori condivisi per TUTTE le pagine (Login e App) */

document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Controlla se nell'URL è presente il parametro ?reason=session_expired (es. dopo reindirizzamento)
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('reason') === 'session_expired') {
        if (window.alertServerCard) {
            window.alertServerCard.renderAlert({
                notify_key: "LOGIN_SESSION_TIMEOUT",
                severity: SEVERITY.WARNING,
                message: "Sessione scaduta per inattività. Effettuare nuovamente il login.",
                permanent: false
            });
        }
        // Pulisce l'URL per evitare di riattivare l'avviso con un refresh manuale (F5)
        window.history.replaceState({}, document.title, window.location.pathname);
    }
});

/* 2. Intercettore globale fetch per risposte 401 (Sessione Scaduta) */
(function() {
    const originalFetch = window.fetch;

    window.fetch = async function(...args) {
        const response = await originalFetch(...args);

        if (response.status === 401) {
            try {
                const clone = response.clone();
                const errorBody = await clone.json();

                // Se la dipendenza FastAPI ha restituito LOGIN_SESSION_TIMEOUT
                if (errorBody.detail && errorBody.detail.notify_key === "LOGIN_SESSION_TIMEOUT") {
                    
                    if (window.alertServerCard) {
                        window.alertServerCard.renderAlert({
                            notify_key: errorBody.detail.notify_key,
                            severity: "WARNING",
                            message: errorBody.detail.message || "Sessione scaduta per inattività.",
                            permanent: false
                        });
                    }

                    // Reindirizza al login dopo 2.5 secondi
                    setTimeout(() => {
                        window.location.href = "/?reason=session_expired";
                    }, 2500);
                }
            } catch (e) {
                console.error("Errore nell'intercettore 401:", e);
            }
        }

        return response;
    };
})();