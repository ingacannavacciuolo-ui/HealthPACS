// ==========================================================================
// GESTIONE PAGINA QUERY STUDIES
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    // Inizializzazione dati all'apertura della pagina
    caricaStudi();
});

/**
 * Funzione per recuperare la lista degli studi dal backend FastAPI
 */
async function caricaStudi() {
    try {
        // apiFetch gestisce automaticamente l'intercettazione del 401 e la visualizzazione del Toast
        const response = await apiFetch('/api/v1/studies');

        // Se response è null, la sessione è scaduta o c'è stato un errore catturato da apiFetch
        if (!response) return;

        const data = await response.json();
        console.log("Dati studi ricevuti:", data);

        // Notifica di successo tradotta dinamica
        mostraToast(window.t(LANG_KEY.STUDIES_LOADED_SUCCESS), "success");

        // Qui inseriremo la logica per renderizzare i dati nella tabella HTML
    } catch (error) {
        console.error("Errore durante il caricamento degli studi:", error);
    }
}

// Azione 2: Quando l'utente clicca un pulsante di ricerca sulla pagina
async function quandoLUtenteCliccaCerca() {
    // Qualsiasi azione utente passa da apiFetch
    const res = await apiFetch('/api/v1/studies/search', {
        method: 'POST',
        body: JSON.stringify({ filtro: "demo" })
    });

    if (!res) return; // Se res è null significa che la sessione era scaduta ed è già partito il Toast
    
    // Prosegui con i dati se la sessione era valida...
}

/**
 * Esempio di funzione per inviare la ricerca/filtro studi
 */
async function eseguiRicercaStudi(filtri) {
    try {
        const response = await apiFetch('/api/v1/studies/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(filtri)
        });

        if (!response) return;

        const risultati = await response.json();
        mostraToast(window.t(LANG_KEY.SEARCH_COMPLETED), "success");
        return risultati;

    } catch (error) {
        console.error("Errore durante la ricerca:", error);
    }
}