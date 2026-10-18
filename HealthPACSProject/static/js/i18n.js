/**
 * Helper globale per la localizzazione (i18n) lato client
 */
window.t = function(key, defaultValue = "it") {
    if (window.TRANSLATIONS && window.TRANSLATIONS[key]) {
        return window.TRANSLATIONS[key];
    }
    return defaultValue || key;
};