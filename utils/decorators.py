from functools import wraps
from flask import session, redirect, url_for, flash, abort

def login_required(f):
    """
    Decorador para autenticación obligatoria.
    Impide el acceso a vistas protegidas si el usuario no tiene una sesión válida.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Por favor, inicia sesión para acceder a esta sección.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """
    Decorador modular para autorización basada en roles.
    Acepta uno o múltiples roles autorizados.
    
    1. Si el usuario no está autenticado, redirige al login (login_required).
    2. Si el usuario está autenticado pero su rol no está entre allowed_roles,
       aborta la petición con código de estado HTTP 403 (Forbidden).
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 1. Comprobar autenticación
            if "user_id" not in session:
                flash("Por favor, inicia sesión para acceder a esta sección.", "warning")
                return redirect(url_for("auth.login"))

            # 2. Comprobar rol del usuario desde la sesión segura
            user_rol = session.get("user_rol")
            if user_rol not in allowed_roles:
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator
