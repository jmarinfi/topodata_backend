import sys
from getpass import getpass

from data.database.engine import SessionLocal
from data.repositories.user_repository import UserRepository
from services.password_service import PasswordService


def main():
    print("=== Creación de Usuario ===")
    username = input("Nombre de usuario: ").strip()
    if not username:
        print("Error: El nombre de usuario no puede estar vacío.")
        sys.exit(1)

    email = input("Email: ").strip()
    if not email:
        print("Error: El email no puede estar vacío.")
        sys.exit(1)

    password = getpass("Contraseña: ")
    if not password:
        print("Error: La contraseña no puede estar vacía.")
        sys.exit(1)

    confirm_password = getpass("Confirmar contraseña: ")
    if password != confirm_password:
        print("Error: Las contraseñas no coinciden.")
        sys.exit(1)

    is_superuser_input = input("¿Es superusuario? (s/n): ").strip().lower()
    is_superuser = is_superuser_input in ("s", "si", "sí", "y", "yes", "true")

    password_service = PasswordService()

    with SessionLocal() as session:
        user_repo = UserRepository(session=session)

        if user_repo.exists_by_username(username):
            print(f"Error: El nombre de usuario '{username}' ya está en uso.")
            sys.exit(1)

        if user_repo.exists_by_email(email):
            print(f"Error: El email '{email}' ya está registrado.")
            sys.exit(1)

        hashed_password = password_service.hash(password)

        attributes = {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "is_superuser": is_superuser,
            "is_active": True,
        }

        try:
            user_repo.create(attributes)
            session.commit()
            print(f"¡Usuario '{username}' creado con éxito!")
        except Exception as e:
            session.rollback()
            print(f"Error al crear el usuario: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
