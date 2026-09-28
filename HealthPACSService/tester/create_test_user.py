# tester/create_test_user.py

import getpass
import sys
from pathlib import Path

# Aggiunge la radice del progetto al PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent))

from argon2 import PasswordHasher
from sqlalchemy import select
from library.dbmanager import DatabaseManager
from library.models.app_users_roles_model import AppUsersRolesModel
from library.repository.app_users_repo import AppUsersRepo


def main():
    print("==================================================")
    print("      PACS/VNA BACKEND - CREAZIONE UTENTE TEST    ")
    print("==================================================")

    db = DatabaseManager()
    if not db.connect():
        print("[-] ERRORE: Impossibile connettersi al Database.")
        sys.exit(1)

    # 1. Recupera i ruoli disponibili dal Database
    with db.get_session() as session:
        roles = session.execute(
            select(AppUsersRolesModel).order_by(AppUsersRolesModel.id)
        ).scalars().all()

    if not roles:
        print("[-] ERRORE: Nessun ruolo trovato nella tabella public.app_users_roles.")
        sys.exit(1)

    # 2. Richiesta dati anagrafici e credenziali da CLI
    print("\nInserisci i dati del nuovo utente:")
    first_name = input("Nome: ").strip()
    last_name = input("Cognome: ").strip()
    email = input("Email: ").strip()
    username = input("Username: ").strip()

    if not username:
        print("[-] Errore: L'username è obbligatorio.")
        sys.exit(1)

    # getpass nasconde la digitazione a schermo
    password = getpass.getpass("Password: ").strip()
    password_confirm = getpass.getpass("Conferma Password: ").strip()

    if not password:
        print("[-] Errore: La password non può essere vuota.")
        sys.exit(1)

    if password != password_confirm:
        print("[-] Errore: Le password inserite non coincidono.")
        sys.exit(1)

    # 3. Selezione del Ruolo
    print("\nSeleziona il Ruolo da assegnare:")
    role_map = {}
    for idx, role in enumerate(roles, 1):
        print(f"  [{idx}] {role.name} - {role.description or 'Nessuna descrizione'}")
        role_map[str(idx)] = role

    role_choice = input("\nInserisci il numero corrispondente al ruolo: ").strip()

    if role_choice not in role_map:
        print("[-] Scelta non valida.")
        sys.exit(1)

    selected_role = role_map[role_choice]

    # 4. Hashing password con Argon2id
    ph = PasswordHasher()
    hashed_pwd = ph.hash(password)

    # 5. Salvataggio utente nel DB via AppUsersRepo
    users_repo = AppUsersRepo(db)

    # Verifica se l'username è già occupato
    if users_repo.get_by_username(username):
        print(f"\n[❌] ERRORE: L'username '{username}' esiste già a database!")
        sys.exit(1)

    user_id = users_repo.create(
        username=username,
        password_hash=hashed_pwd,
        users_roles_id=selected_role.id,
        first_name=first_name if first_name else None,
        last_name=last_name if last_name else None,
        email=email if email else None,
        is_active=True,
    )

    if user_id:
        print("\n[✅] UTENTE CREATO CON SUCCESSO!")
        print(f"    - ID Utente:  {user_id}")
        print(f"    - Username:   {username}")
        print(f"    - Ruolo:      {selected_role.name} (ID: {selected_role.id})")
        print(f"    - Nome/Cogn:  {first_name} {last_name}")
        print(f"    - Email:      {email}")
    else:
        print("\n[❌] ERRORE durante il salvataggio dell'utente nel DB.")

    print("\n==================================================")


if __name__ == "__main__":
    main()