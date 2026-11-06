import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.user import UserModel
from utils.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"

@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    """Ruta pública de registro de usuarios. Asigna obligatoriamente el rol 'estudiante'."""
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip().lower()
        contrasena = request.form.get("contrasena", "")
        confirmar_contrasena = request.form.get("confirmar_contrasena", "")

        # Validaciones de entrada
        if not nombre or not correo or not contrasena or not confirmar_contrasena:
            flash("Todos los campos son obligatorios.", "danger")
            return render_template("auth/registro.html", nombre=nombre, correo=correo), 400

        if not re.match(EMAIL_REGEX, correo):
            flash("Por favor, ingresa un correo electrónico con formato válido.", "danger")
            return render_template("auth/registro.html", nombre=nombre, correo=correo), 400

        if len(contrasena) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "danger")
            return render_template("auth/registro.html", nombre=nombre, correo=correo), 400

        if contrasena != confirmar_contrasena:
            flash("Las contraseñas ingresadas no coinciden.", "danger")
            return render_template("auth/registro.html", nombre=nombre, correo=correo), 400

        # Verificación de correo duplicado
        usuario_existente = UserModel.get_by_email(correo)
        if usuario_existente:
            flash("El correo electrónico ya se encuentra registrado en el sistema.", "danger")
            return render_template("auth/registro.html", nombre=nombre), 400

        # Generación de hash seguro con Flask-Bcrypt
        pw_hash = generate_password_hash(contrasena)

        # Creación obligatoria con rol 'estudiante'
        try:
            UserModel.create_user(
                nombre=nombre,
                correo=correo,
                password_hash=pw_hash,
                rol="estudiante"
            )
            flash("¡Registro exitoso! Ya puedes iniciar sesión.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            flash("Ocurrió un error al procesar el registro. Inténtalo nuevamente.", "danger")
            return render_template("auth/registro.html", nombre=nombre, correo=correo), 500

    return render_template("auth/registro.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Ruta pública de inicio de sesión."""
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        contrasena = request.form.get("contrasena", "")

        if not correo or not contrasena:
            flash("Por favor ingresa tu correo y contraseña.", "danger")
            return render_template("auth/login.html", correo=correo), 400

        usuario = UserModel.get_by_email(correo)

        # Validación segura: mensaje genérico para evitar enumeración de usuarios
        if not usuario or not check_password_hash(usuario["contrasena"], contrasena):
            flash("Credenciales incorrectas. Verifica tu correo y contraseña.", "danger")
            return render_template("auth/login.html", correo=correo), 401

        # Inicialización de sesión segura en Flask (sin almacenar contraseñas ni hashes)
        session.clear()
        session["user_id"] = usuario["id_usuario"]
        session["user_nombre"] = usuario["nombre"]
        session["user_correo"] = usuario["correo"]
        session["user_rol"] = usuario["rol"]

        flash(f"¡Bienvenido/a, {usuario['nombre']}!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/login.html")

@auth_bp.route("/logout")
def logout():
    """Ruta para cerrar sesión de forma segura y redirigir al login."""
    session.clear()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("auth.login"))
