import bcrypt


class PasswordService:
    """Servicio para hashear y verificar contraseñas con bcrypt."""

    ENCODING = "utf-8"

    def hash(self, plain_password: str) -> str:
        """Genera el hash bcrypt de una contraseña en texto plano."""

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode(self.ENCODING), salt)

        return hashed.decode(self.ENCODING)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Comprueba si una contraseña en texto plano coincide con su hash."""

        return bcrypt.checkpw(
            plain_password.encode(self.ENCODING), hashed_password.encode(self.ENCODING)
        )
