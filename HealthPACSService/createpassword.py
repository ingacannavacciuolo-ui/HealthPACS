# createpassword.py

import sys
import getpass
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

# Inizializzazione hasher Argon2id secondo i parametri OWASP
ph = PasswordHasher()


def main():
    print("=" * 60)
    print(" ARGON2id PASSWORD HASH GENERATOR")
    print("=" * 60)

    # Legge la password da argomento CLI oppure da prompt nascosto
    if len(sys.argv) > 1:
        raw_password = sys.argv[1]
    else:
        raw_password = getpass.getpass("Inserisci la password da criptare: ")
        confirm_password = getpass.getpass("Conferma la password: ")
        
        if raw_password != confirm_password:
            print("\n❌ Errore: Le password non coincidono!")
            sys.exit(1)

    if not raw_password.strip():
        print("\n❌ Errore: La password non può essere vuota!")
        sys.exit(1)

    # Generazione dell'hash
    print("\nGenerazione hash in corso...")
    hashed_password = ph.hash(raw_password)

    print("\n✅ HASH GENERATO CON SUCCESSO:")
    print("-" * 60)
    print(hashed_password)
    print("-" * 60)

    # Test rapido di verifica
    try:
        ph.verify(hashed_password, raw_password)
        print("\n✔️ Test di verifica dell'hash: SUPERATO")
    except (VerifyMismatchError, VerificationError):
        print("\n❌ Test di verifica dell'hash: FALLITO")

    print("\nPuoi copiare questo valore e inserirlo nel database o negli script SQL di seed.")


if __name__ == "__main__":
    main()