from flask_bcrypt import Bcrypt

# Instancia central de Bcrypt
bcrypt = Bcrypt()

def generate_password_hash(password: str) -> str:
    """Genera un hash seguro con salt utilizando Flask-Bcrypt."""
    return bcrypt.generate_password_hash(password).decode("utf-8")

def check_password_hash(pw_hash: str, password: str) -> bool:
    """Verifica si la contraseña coincide con el hash almacenado."""
    return bcrypt.check_password_hash(pw_hash, password)
