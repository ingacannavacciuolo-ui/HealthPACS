/**
 * Modulo di gestione visiva e socket per le Card Allerte Server
 */
const AlertServerCard = {
    socket: null,

    // Mappatura contenitori DOM per Severity
    containers: {
        CRITICAL: "container-critical-alerts", // Top Left
        WARNING:  "container-warning-alerts",  // Bottom Right
        INFO:     "container-info-alerts"   // Bottom Right
    },

    init() {
        // Avvia la connessione Socket autonoma
        this.initSocket();
    },

    initSocket() {
        if (typeof io === 'undefined' || typeof SOCKET_NAMESPACES === 'undefined') {
            console.error('[AlertServerCard] Socket.IO o SOCKET_NAMESPACES non trovati.');
            return;
        }

        // Connessione autonoma al namespace WEB (stessa logica di ServerStatusCard)
        this.socket = io(SOCKET_NAMESPACES.WEB, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 2000
        });

        // Evento di connessione Socket
        this.socket.on('connect', () => {
            console.log(`[AlertServerCard] Connesso al namespace: ${SOCKET_NAMESPACES.WEB}`);

            // Il BROWSER chiede esplicitamente le notifiche attive dal DB al refresh / apertura
            this.socket.emit('get_active_alerts');
        });

        // Riceve la lista e renderizza le card
        this.socket.on('active_alerts_list', (alerts) => {
            console.log('[AlertServerCard] Ricevute allerte attive dal DB:', alerts);
            if (Array.isArray(alerts)) {
                alerts.forEach(alertData => this.renderAlert(alertData));
            }
        });

        // Nomi dei canali dagli eventi di Severity
        const criticalEvent = (typeof NOTIFY_SEVERITY !== 'undefined' && NOTIFY_SEVERITY.CRITICAL) ? NOTIFY_SEVERITY.CRITICAL : NOTIFY_SEVERITY.CRITICAL;
        const warningEvent  = (typeof NOTIFY_SEVERITY !== 'undefined' && NOTIFY_SEVERITY.WARNING)  ? NOTIFY_SEVERITY.WARNING  : NOTIFY_SEVERITY.WARNING;
        const infoEvent     = (typeof NOTIFY_SEVERITY !== 'undefined' && NOTIFY_SEVERITY.INFO)     ? NOTIFY_SEVERITY.INFO     : NOTIFY_SEVERITY.INFO;

        // Ascolto diretto sui tre canali di severità
        this.socket.on(criticalEvent, (data) => this.renderAlert(data));
        this.socket.on(warningEvent, (data) => this.renderAlert(data));
        this.socket.on(infoEvent, (data) => this.renderAlert(data));

        // Evento di disconnessione
        this.socket.on('disconnect', () => {
            console.warn('[AlertServerCard] Disconnesso dal server.');
        });

        // Errore di connessione
        this.socket.on('connect_error', (error) => {
            console.error('[AlertServerCard] Errore di connessione:', error);
        });
    },

    renderAlert(data) {
        if (!data || !data.notify_key) return;

        const cardId = `alert-${data.notify_key}`;

        // Quietanza: rimuove la card se is_active è false
        if (data.is_active === false) {
            const existingCard = document.getElementById(cardId);
            if (existingCard) existingCard.remove();
            return;
        }

        const severity = (data.severity || NOTIFY_SEVERITY.INFO).toUpperCase();
        const cssClass = severity.toLowerCase();
        const containerId = this.containers[severity] || this.containers.INFO;
        const targetContainer = document.getElementById(containerId);

        if (!targetContainer) return;

        // Struttura HTML della card (coordinata con il CSS)
        const cardHTML = `
            <div class="alert-icon"></div>
            <div class="alert-content">
                <span class="alert-prefix"></span>
                <span class="alert-message">${data.message || ''}</span>
            </div>
            ${!data.permanent ? `<button class="alert-close-btn" onclick="document.getElementById('${cardId}').remove()">✕</button>` : ''}
        `;

        let card = document.getElementById(cardId);

        if (card) {
            card.className = `alert-card-tech ${cssClass}`;
            card.innerHTML = cardHTML;
            if (card.parentElement.id !== containerId) {
                targetContainer.appendChild(card);
            }
        } else {
            card = document.createElement("div");
            card.id = cardId;
            card.className = `alert-card-tech ${cssClass}`;
            card.innerHTML = cardHTML;
            targetContainer.appendChild(card);
        }
    }
};

// Inizializzazione automatica al caricamento del DOM
document.addEventListener('DOMContentLoaded', () => {
    AlertServerCard.init();
});