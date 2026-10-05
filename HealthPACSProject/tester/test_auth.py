import getpass
import sys
from pathlib import Path

# Aggiunge la radice del progetto al PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent))

from library.dbmanager import DatabaseManager
from library.services.auth_service import AuthService


def main():
    print("==================================================")
    print("      PACS/VNA BACKEND - TERMINAL AUTH TEST       ")
    print("==================================================")

    db = DatabaseManager()
    if not db.connect():
        print("[-] ERRORE: Impossibile connettersi al Database.")
        sys.exit(1)

    auth_service = AuthService(db)

    print("\nInserisci le tue credenziali di accesso:")
    username_input = input("Username: ").strip()
    password_input = getpass.getpass("Password: ")

    if not username_input or not password_input:
        print("[-] Errore: Username e Password non possono essere vuoti.")
        sys.exit(1)

    print("\n[...] Autenticazione in corso su PostgreSQL...")

    auth_result = auth_service.login(
        username=username_input,
        password_plain=password_input,
        ip_address="127.0.0.1",
        user_agent="CLI-Test-Agent/1.0",
    )

    if not auth_result:
        print("\n[❌] LOGIN FALLITO!")
        print("    Credenziali non valide o utente disabilitato.")
        sys.exit(1)

    session_token = auth_result["session_token"]
    permissions = auth_result["permissions"]

    print("\n[✅] LOGIN RIUSCITO!")
    print(f"    - ID Utente:      {auth_result['user_id']}")
    print(f"    - Username:       {auth_result['username']}")
    print(f"    - ID Ruolo:       {auth_result['role_id']}")
    print(f"    - Token Sessione: {session_token[:16]}... (troncato per sicurezza)")
    print(f"    - Permessi Effettivi Accordati ({len(permissions)}):")
    for perm in sorted(permissions):
        print(f"        * {perm}")

    print("\n--------------------------------------------------")
    print(" VERIFICA FUNZIONALE PERMESSI RISERVATI")
    print("--------------------------------------------------")

    test_actions = ["study:read", "study:export", "study:purge", "user:write"]

    for action in test_actions:
        has_perm = auth_service.has_permission(session_token, action)
        status = "ACCORDATO" if has_perm else "NEGATO"
        symbol = "✔" if has_perm else "✖"
        print(f"  [{symbol}] Permesso '{action}': {status}")

    print("\n--------------------------------------------------")
    input("Premi INVIO per effettuare il LOGOUT e invalidare la sessione...")
    
    if auth_service.logout(session_token):
        print("[+] Sessione disattivata correttamente nel DB.")

    if not auth_service.validate_session(session_token):
        print("[+] Test di sicurezza superato: Il token è disattivato e non più riutilizzabile.")
    else:
        print("[❌] ERRORE SICUREZZA: Il token è ancora attivo dopo il logout!")

    print("\n==================================================")
    print("                 TEST CONCLUSO                    ")
    print("==================================================")


if __name__ == "__main__":
    main()