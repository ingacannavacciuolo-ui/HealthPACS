/**
 * Modulo di gestione visiva e socket per la card di stato del Server
 */
const ServerStatusCard = {
    cardEl: null,
    textEl: null,
    connected: false,
    socket: null,

    init() {
        this.cardEl = document.getElementById('server-status-card');
        this.textEl = document.getElementById('server-status-text');
        //this.setDisconnected(); // Stato iniziale obbligatorio

        // Avvia la connessione Socket autonoma
        this.initSocket();
    },

    initSocket() {
        if (typeof io === 'undefined' || typeof SOCKET_NAMESPACES === 'undefined') {
            console.error('[ServerStatusCard] Socket.IO o SOCKET_NAMESPACES non trovati.');
            return;
        }

        // Connessione al namespace LOGIN gestita internamente
        this.socket = io(SOCKET_NAMESPACES.WEB, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 2000
        });

        // Evento di connessione Socket
        this.socket.on('connect', () => {
            console.log(`[ServerStatusCard] Connesso al namespace: ${SOCKET_NAMESPACES.WEB}`);
            //this.setConnected("CONNESSO");
        });

        // Evento Heartbeat / Stato operativo inviato dal backend
       this.socket.on(SOCKET_EVENTS.SERVICE_STATUS_UPDATE, (data) => {
            console.log('[ServerStatusCard] Aggiornamento stato:', data);

            // Recupera il valore 'ONLINE' dalla costante globale SERVICE_STATUS_STATES
            const onlineValue = (typeof SERVICE_STATUS_STATES !== 'undefined' && SERVICE_STATUS_STATES.ONLINE) 
                ? SERVICE_STATUS_STATES.ONLINE 
                : 'ONLINE';

            // Confronta direttamente data.status con la costante del backend
            if (data && data.status === onlineValue) {
                this.setConnected("CONNESSO");    // Attiva classe CSS verde + testo "CONNESSO"
            } else {
                this.setDisconnected("DISCONNESSO"); // Attiva classe CSS rossa + testo "DISCONNESSO"
            }
        });

        // Evento fallback server_alive (se inviato dal backend)
        this.socket.on(SOCKET_EVENTS.SERVER_ALIVE, (data) => {
            this.setConnected(data && data.status ? data.status : "CONNESSO");
        });

        // Evento di disconnessione
        this.socket.on('disconnect', () => {
            console.warn('[ServerStatusCard] Disconnesso dal server.');
            this.setDisconnected("DISCONNESSO");
        });

        // Errore di connessione
        this.socket.on('connect_error', (error) => {
            console.error('[ServerStatusCard] Errore di connessione:', error);
            this.setDisconnected("DISCONNESSO");
        });
    },

    setConnected(customText = "CONNESSO") {
        if (!this.cardEl || !this.textEl) return;
        
        this.connected = true;
        this.cardEl.classList.remove('status-disconnected');
        this.cardEl.classList.add('status-connected');
        this.textEl.textContent = customText;
    },

    setDisconnected(customText = "DISCONNESSO") {
        if (!this.cardEl || !this.textEl) return;

        this.connected = false;
        this.cardEl.classList.remove('status-connected');
        this.cardEl.classList.add('status-disconnected');
        this.textEl.textContent = customText;
    },

    isOnline() {
        return this.connected;
    }
};

// Inizializzazione automatica al caricamento del DOM
document.addEventListener('DOMContentLoaded', () => {
    ServerStatusCard.init();
});