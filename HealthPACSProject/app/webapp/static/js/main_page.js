
// ==========================================================================
// 1. MONKEY PATCH GLOBALE SU FETCH (Intercetta il 401 ovunque)
// ==========================================================================
const originalFetch = window.fetch;

window.fetch = async function (...args) {
    const response = await originalFetch(...args);

    // 1. Controllo se il fetch è stato reindirizzato alla login con un motivo
    if (response.redirected && response.url.includes('reason=')) {
        const url = new URL(response.url);
        const reason = url.searchParams.get('reason');

        let messaggio = window.t(LANG_KEY.ALERT_SESSION_EXPIRED);
        if (reason === NOTIFY_ERROR.MISSING_TOKEN) {
            messaggio = window.t(LANG_KEY.ALERT_MISSING_TOKEN);
        } else if (reason === NOTIFY_ERROR.SESSION_EXPIRED) {
            messaggio = window.t(LANG_KEY.ALERT_SESSION_EXPIRED);
        }

        // Fai scattare subito il Toast e avvia il timer per il redirect
        forzaLogoutSessioneScaduta(messaggio);
        
        // Interrompiamo la catena restituendo una risposta vuota per bloccare eventuali elaborazioni JS successive
        return new Response(JSON.stringify({ error: NOTIFY_ERROR.SESSION_EXPIRED }), { status: 401 });
    }

    // 2. Controllo standard in caso di risposta 401 JSON diretta
    if (response.status === 401 && !window.location.pathname.endsWith('/')) {
        const data = await response.clone().json().catch(() => ({}));

        let messaggio = window.t(LANG_KEY.ALERT_SESSION_EXPIRED);
        if (data.detail === NOTIFY_ERROR.MISSING_TOKEN) {
            messaggio = window.t(LANG_KEY.ALERT_MISSING_TOKEN);
        } else if (data.detail === NOTIFY_ERROR.SESSION_EXPIRED) {
            messaggio = window.t(LANG_KEY.ALERT_SESSION_EXPIRED);
        }

        forzaLogoutSessioneScaduta(messaggio);
    }

    return response;
};

// Intercetta qualsiasi click su pulsanti o link interattivi nella pagina
document.addEventListener('click', async (event) => {
    // Se l'elemento cliccato è un pulsante o ha una classe interattiva
    const elemento = event.target.closest('button, .btn, a[data-api]');
    
    if (elemento) {
        // Esegue una verifica veloce della sessione verso il backend
        await fetch('/querystudies');
    }
});

// ==========================================================================
// 2. WRAPPER apiFetch (Semplificato)
// ==========================================================================
async function apiFetch(url, options = {}) {
    try {
        // Chiama il fetch che ora è protetto dall'intercettore globale
        return await fetch(url, options);
    } catch (error) {
        mostraToast(window.t(LANG_KEY.SERVER_CONNECTION_ERROR), "error");
        throw error;
    }
}

// ==========================================================================
// 3. FUNZIONE GLOBALE PER MOSTRARE NOTIFICHE TOAST
// ==========================================================================
function mostraToast(messaggio, tipo = 'success') {
    let container = document.getElementById('toast-container');
    
    // Se per qualsiasi motivo il contenitore non esiste ancora, lo crea al volo nel body
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    // Crea l'elemento toast
    const toast = document.createElement('div');
    toast.className = `toast ${tipo}`;

    // Span dedicato al messaggio
    const msgSpan = document.createElement('span');
    msgSpan.className = 'toast-message';
    msgSpan.innerText = messaggio;
    toast.appendChild(msgSpan);

    container.appendChild(toast);

    // Rimuove automaticamente il toast dopo 5 secondi
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            toast.remove();
        }, 500);
    }, 4000);
}



// ==========================================================================
// 4. FUNZIONE PER REDIRECT SU SESSIONE SCADUTA
// ==========================================================================
function forzaLogoutSessioneScaduta(messaggio = window.t(LANG_KEY.ALERT_SESSION_EXPIRED)) {
    //console.warn("[SESSION] Intercettata sessione scaduta:", messaggio);

    // 1. Pulisce la sessione locale del browser
    sessionStorage.clear();

    // 2. Mostra il Toast d'errore
    mostraToast(messaggio, "error");

    // 3. Attende 2 secondi per mostrare l'animazione del Toast prima del redirect
    setTimeout(() => {
        window.location.href = "/logout";
    }, 2000);
}