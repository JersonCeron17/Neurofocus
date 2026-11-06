import sys
import os

# Asegurar que la raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models.user import UserModel
from utils.security import check_password_hash

def run_tests():
    print("==================================================")
    print("EJECUTANDO BATERÍA DE PRUEBAS — ETAPA 4: AUTENTICACIÓN")
    print("==================================================")

    # 1. Flask inicia
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    print("PRUEBA 1: Flask inicia correctamente -> OK")

    # 2. /registro responde
    res_reg_get = client.get("/registro")
    assert res_reg_get.status_code == 200, f"Error en GET /registro: {res_reg_get.status_code}"
    print("PRUEBA 2: GET /registro responde 200 -> OK")

    # 3. /login responde
    res_log_get = client.get("/login")
    assert res_log_get.status_code == 200, f"Error en GET /login: {res_log_get.status_code}"
    print("PRUEBA 3: GET /login responde 200 -> OK")

    # Datos del usuario de prueba
    test_nombre = "Usuario Prueba NeuroFocus"
    test_correo = "usuario_test_etapa4@neurofocus.local"
    test_pass = "ClavePrueba123!"

    # Limpieza preventiva previa
    UserModel.delete_user_by_email(test_correo)

    # 4. Registro exitoso de usuario de prueba
    res_reg_post = client.post("/registro", data={
        "nombre": test_nombre,
        "correo": test_correo,
        "contrasena": test_pass,
        "confirmar_contrasena": test_pass
    }, follow_redirects=False)
    assert res_reg_post.status_code == 302, f"Fallo al registrar usuario: {res_reg_post.status_code}"
    print("PRUEBA 4: Registro exitoso de usuario de prueba (302 Redirect) -> OK")

    # 5. Confirmar que el rol creado es 'estudiante'
    user_db = UserModel.get_by_email(test_correo)
    assert user_db is not None, "El usuario no fue encontrado en la base de datos"
    assert user_db["rol"] == "estudiante", f"Rol inesperado: {user_db['rol']}"
    print(f"PRUEBA 5: Rol en base de datos confirmado como '{user_db['rol']}' -> OK")

    # 6. Confirmar que la contraseña almacenada no está en texto plano
    stored_hash = user_db["contrasena"]
    assert stored_hash != test_pass, "La contraseña se guardó en texto plano"
    assert stored_hash.startswith("$2b$") or stored_hash.startswith("$2a$"), "El formato no corresponde a bcrypt"
    assert check_password_hash(stored_hash, test_pass), "El hash no valida con la contraseña original"
    print("PRUEBA 6: Contraseña verificada como hash seguro Bcrypt (no texto plano) -> OK")

    # 7. Intento de correo duplicado rechazado
    res_dup = client.post("/registro", data={
        "nombre": "Otro Nombre",
        "correo": test_correo,
        "contrasena": "OtraClave456!",
        "confirmar_contrasena": "OtraClave456!"
    })
    assert res_dup.status_code == 400, f"Debería rechazar correo duplicado: {res_dup.status_code}"
    print("PRUEBA 7: Intento de registro con correo duplicado rechazado con 400 -> OK")

    # 8. Login con contraseña incorrecta rechazado
    res_bad_login = client.post("/login", data={
        "correo": test_correo,
        "contrasena": "ClaveErronea999!"
    })
    assert res_bad_login.status_code == 401, f"Debería rechazar contraseña incorrecta: {res_bad_login.status_code}"
    print("PRUEBA 8: Login con contraseña incorrecta rechazado con 401 -> OK")

    # 9. Login con contraseña correcta exitoso
    res_good_login = client.post("/login", data={
        "correo": test_correo,
        "contrasena": test_pass
    }, follow_redirects=False)
    assert res_good_login.status_code == 302, f"Fallo al iniciar sesión: {res_good_login.status_code}"
    assert res_good_login.headers["Location"].endswith("/dashboard"), "No redirigió a /dashboard"
    print("PRUEBA 9: Login con contraseña correcta exitoso (302 a /dashboard) -> OK")

    # 10. La sesión identifica al usuario
    res_dash = client.get("/dashboard")
    assert res_dash.status_code == 200, f"No se pudo acceder a la ruta protegida con sesión: {res_dash.status_code}"
    assert test_nombre in res_dash.get_data(as_text=True), "El nombre del usuario no aparece en el dashboard"
    print("PRUEBA 10: La sesión activa identifica correctamente al usuario en /dashboard -> OK")

    # 11. Ruta protegida rechaza usuario no autenticado (cliente limpio)
    unauth_client = app.test_client()
    res_unauth = unauth_client.get("/dashboard", follow_redirects=False)
    assert res_unauth.status_code == 302, f"Debería rechazar acceso no autenticado: {res_unauth.status_code}"
    assert res_unauth.headers["Location"].endswith("/login"), "No redirigió a /login"
    print("PRUEBA 11: Ruta protegida rechaza usuario no autenticado (302 a /login) -> OK")

    # 12. Logout funciona
    res_logout = client.get("/logout", follow_redirects=False)
    assert res_logout.status_code == 302, f"Logout no redirigió: {res_logout.status_code}"
    assert res_logout.headers["Location"].endswith("/login"), "Logout no redirigió a /login"
    print("PRUEBA 12: Logout finaliza la sesión y redirige al login -> OK")

    # 13. Después del logout, la ruta protegida vuelve a rechazar acceso
    res_dash_post_logout = client.get("/dashboard", follow_redirects=False)
    assert res_dash_post_logout.status_code == 302, "La ruta protegida sigue accesible tras logout"
    assert res_dash_post_logout.headers["Location"].endswith("/login"), "No redirigió a /login tras logout"
    print("PRUEBA 13: Tras logout, /dashboard rechaza el acceso nuevamente -> OK")

    # Limpieza final del usuario de prueba
    UserModel.delete_user_by_email(test_correo)
    assert UserModel.get_by_email(test_correo) is None, "Fallo al eliminar el usuario de prueba"
    print("LIMPIEZA: Usuario de prueba eliminado de la base de datos -> OK")

    print("==================================================")
    print("TODAS LAS 13 PRUEBAS DE AUTENTICACIÓN PASARON EXITOSAMENTE")
    print("==================================================")

def test_suite_auth():
    run_tests()

if __name__ == "__main__":
    run_tests()
