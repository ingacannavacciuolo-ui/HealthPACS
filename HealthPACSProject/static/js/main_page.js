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

        let messaggio = "Sessione scaduta. Effettuare nuovamente il login.";
        if (reason === "missing_token") {
            messaggio = "Autenticazione mancante. Ritorno al login.";
        } else if (reason === "session_expired") {
            messaggio = "Sessione scaduta per inattività. Effettuare nuovamente il login.";
        }

        // Fai scattare subito il Toast e avvia il timer per il redirect
        forzaLogoutSessioneScaduta(messaggio);
        
        // Interrompiamo la catena restituendo una risposta vuota per bloccare eventuali elaborazioni JS successive
        return new Response(JSON.stringify({ error: "session_expired" }), { status: 401 });
    }

    // 2. Controllo standard in caso di risposta 401 JSON diretta
    if (response.status === 401 && !window.location.pathname.endsWith('/')) {
        const data = await response.clone().json().catch(() => ({}));

        let messaggio = "Sessione scaduta. Effettuare nuovamente il login.";
        if (data.detail === "missing_token") {
            messaggio = "Autenticazione mancante. Ritorno al login.";
        } else if (data.detail === "session_expired") {
            messaggio = "Sessione scaduta per inattività. Effettuare nuovamente il login.";
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
        mostraToast("Errore di connessione al server.", "error");
        throw error;
    }
}

// ==========================================================================
// 1. FUNZIONE GLOBALE PER MOSTRARE NOTIFICHE TOAST
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
    toast.innerText = messaggio;

    // Aggiunge il toast al contenitore
    container.appendChild(toast);

    // Rimuove automaticamente il toast dopo 4 secondi
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            toast.remove();
        }, 500);
    }, 5000);
}

// ==========================================================================
// 2. FUNZIONE PER REDIRECT SU SESSIONE SCADUTA
// ==========================================================================
function forzaLogoutSessioneScaduta(messaggio = "Sessione scaduta. Ritorno al login.") {
    console.warn("[SESSION] Intercettata sessione scaduta:", messaggio);

    // 1. Pulisce la sessione locale del browser
    sessionStorage.clear();

    // 2. Mostra il Toast d'errore
    mostraToast(messaggio, "error");

    // 3. Attende 2.5 secondi per mostrare l'animazione del Toast prima del redirect
    setTimeout(() => {
        window.location.href = "/logout";
    }, 2000);
}

