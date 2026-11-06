import sys
import os

# Asegurar que la raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models.user import UserModel
from utils.security import generate_password_hash

def run_tests():
    print("==================================================")
    print("EJECUTANDO BATERÍA DE PRUEBAS — ETAPA 5: ROLES Y PERMISOS")
    print("==================================================")

    app = create_app()
    app.config["TESTING"] = True

    # Correos de prueba exclusivos y controlados
    email_estudiante = "test_estudiante_etapa5@neurofocus.local"
    email_docente = "test_docente_etapa5@neurofocus.local"
    email_admin = "test_admin_etapa5@neurofocus.local"
    test_password = "PasswordSegura123!"

    # Limpieza preventiva
    UserModel.delete_user_by_email(email_estudiante)
    UserModel.delete_user_by_email(email_docente)
    UserModel.delete_user_by_email(email_admin)

    try:
        with app.app_context():
            hashed_pw = generate_password_hash(test_password)

            # Crear usuario docente de prueba en DB
            UserModel.create_user(
                nombre="Docente Prueba",
                correo=email_docente,
                password_hash=hashed_pw,
                rol="docente"
            )

            # Crear usuario administrador de prueba en DB
            UserModel.create_user(
                nombre="Admin Prueba",
                correo=email_admin,
                password_hash=hashed_pw,
                rol="administrador"
            )

        # ----------------------------------------------------
        # PRUEBAS 1, 2, 3: No autenticado -> 302 Redirige a Login
        # ----------------------------------------------------
        client_anon = app.test_client()

        # 1. No autenticado -> /estudiante/panel
        res1 = client_anon.get("/estudiante/panel", follow_redirects=False)
        assert res1.status_code == 302, f"Esperado 302, obtenido {res1.status_code}"
        assert res1.headers["Location"].endswith("/login"), "No redirigió a /login"
        print("PRUEBA 1: No autenticado -> /estudiante/panel redirige a login (302) -> OK")

        # 2. No autenticado -> /docente/panel
        res2 = client_anon.get("/docente/panel", follow_redirects=False)
        assert res2.status_code == 302, f"Esperado 302, obtenido {res2.status_code}"
        assert res2.headers["Location"].endswith("/login"), "No redirigió a /login"
        print("PRUEBA 2: No autenticado -> /docente/panel redirige a login (302) -> OK")

        # 3. No autenticado -> /admin/panel
        res3 = client_anon.get("/admin/panel", follow_redirects=False)
        assert res3.status_code == 302, f"Esperado 302, obtenido {res3.status_code}"
        assert res3.headers["Location"].endswith("/login"), "No redirigió a /login"
        print("PRUEBA 3: No autenticado -> /admin/panel redirige a login (302) -> OK")

        # ----------------------------------------------------
        # PRUEBA 13: Registro público crea únicamente rol 'estudiante'
        # (Se realiza antes para usar el usuario estudiante en pruebas 4, 5, 6)
        # ----------------------------------------------------
        client_estudiante = app.test_client()
        res_reg = client_estudiante.post("/registro", data={
            "nombre": "Estudiante Prueba",
            "correo": email_estudiante,
            "contrasena": test_password,
            "confirmar_contrasena": test_password,
            "rol": "administrador"  # Intento malicioso de inyectar rol
        }, follow_redirects=False)
        assert res_reg.status_code == 302, f"Error en registro: {res_reg.status_code}"

        user_db = UserModel.get_by_email(email_estudiante)
        assert user_db is not None, "El usuario estudiante no fue creado"
        assert user_db["rol"] == "estudiante", f"El rol debió ser 'estudiante', obtenido: {user_db['rol']}"
        print("PRUEBA 13: Registro público continúa creando únicamente rol estudiante -> OK")

        # Iniciar sesión como Estudiante
        res_login_est = client_estudiante.post("/login", data={
            "correo": email_estudiante,
            "contrasena": test_password
        }, follow_redirects=False)
        assert res_login_est.status_code == 302, "Error al iniciar sesión como estudiante"

        # 4. Estudiante -> /estudiante/panel = 200
        res4 = client_estudiante.get("/estudiante/panel")
        assert res4.status_code == 200, f"Esperado 200, obtenido {res4.status_code}"
        print("PRUEBA 4: Estudiante -> /estudiante/panel = 200 -> OK")

        # 5. Estudiante -> /docente/panel = 403
        res5 = client_estudiante.get("/docente/panel")
        assert res5.status_code == 403, f"Esperado 403, obtenido {res5.status_code}"
        print("PRUEBA 5: Estudiante -> /docente/panel = 403 -> OK")

        # 6. Estudiante -> /admin/panel = 403
        res6 = client_estudiante.get("/admin/panel")
        assert res6.status_code == 403, f"Esperado 403, obtenido {res6.status_code}"
        print("PRUEBA 6: Estudiante -> /admin/panel = 403 -> OK")

        # ----------------------------------------------------
        # PRUEBAS 7, 8, 9: Docente
        # ----------------------------------------------------
        client_docente = app.test_client()
        res_login_doc = client_docente.post("/login", data={
            "correo": email_docente,
            "contrasena": test_password
        }, follow_redirects=False)
        assert res_login_doc.status_code == 302, "Error al iniciar sesión como docente"

        # 7. Docente -> /docente/panel = 200
        res7 = client_docente.get("/docente/panel")
        assert res7.status_code == 200, f"Esperado 200, obtenido {res7.status_code}"
        print("PRUEBA 7: Docente -> /docente/panel = 200 -> OK")

        # 8. Docente -> /estudiante/panel = 403
        res8 = client_docente.get("/estudiante/panel")
        assert res8.status_code == 403, f"Esperado 403, obtenido {res8.status_code}"
        print("PRUEBA 8: Docente -> /estudiante/panel = 403 -> OK")

        # 9. Docente -> /admin/panel = 403
        res9 = client_docente.get("/admin/panel")
        assert res9.status_code == 403, f"Esperado 403, obtenido {res9.status_code}"
        print("PRUEBA 9: Docente -> /admin/panel = 403 -> OK")

        # ----------------------------------------------------
        # PRUEBAS 10, 11, 12: Administrador
        # ----------------------------------------------------
        client_admin = app.test_client()
        res_login_adm = client_admin.post("/login", data={
            "correo": email_admin,
            "contrasena": test_password
        }, follow_redirects=False)
        assert res_login_adm.status_code == 302, "Error al iniciar sesión como administrador"

        # 10. Administrador -> /admin/panel = 200
        res10 = client_admin.get("/admin/panel")
        assert res10.status_code == 200, f"Esperado 200, obtenido {res10.status_code}"
        print("PRUEBA 10: Administrador -> /admin/panel = 200 -> OK")

        # 11. Administrador -> /estudiante/panel = 403
        res11 = client_admin.get("/estudiante/panel")
        assert res11.status_code == 403, f"Esperado 403, obtenido {res11.status_code}"
        print("PRUEBA 11: Administrador -> /estudiante/panel = 403 -> OK")

        # 12. Administrador -> /docente/panel = 403
        res12 = client_admin.get("/docente/panel")
        assert res12.status_code == 403, f"Esperado 403, obtenido {res12.status_code}"
        print("PRUEBA 12: Administrador -> /docente/panel = 403 -> OK")

        # ----------------------------------------------------
        # PRUEBA 14: Logout continúa funcionando
        # ----------------------------------------------------
        res_logout = client_admin.get("/logout", follow_redirects=False)
        assert res_logout.status_code == 302, f"Esperado 302 en logout, obtenido {res_logout.status_code}"
        assert res_logout.headers["Location"].endswith("/login"), "No redirigió a /login"

        # Tras logout, acceso al panel debe ser denegado y redirigido a login
        res_post_logout = client_admin.get("/admin/panel", follow_redirects=False)
        assert res_post_logout.status_code == 302, "Acceso no protegido tras logout"
        assert res_post_logout.headers["Location"].endswith("/login"), "No redirigió a /login tras logout"
        print("PRUEBA 14: Logout continúa funcionando y revoca el acceso a rutas protegidas -> OK")

    finally:
        # Limpieza obligatoria de usuarios temporales
        del1 = UserModel.delete_user_by_email(email_estudiante)
        del2 = UserModel.delete_user_by_email(email_docente)
        del3 = UserModel.delete_user_by_email(email_admin)
        print("--------------------------------------------------")
        print("LIMPIEZA DE DATOS TEMPORALES:")
        print(f"- Usuario {email_estudiante} eliminado: {del1}")
        print(f"- Usuario {email_docente} eliminado: {del2}")
        print(f"- Usuario {email_admin} eliminado: {del3}")
        print("--------------------------------------------------")

    print("==================================================")
    print("TODAS LAS 14 PRUEBAS DE ROLES PASARON EXITOSAMENTE")
    print("==================================================")

def test_suite_roles():
    run_tests()

if __name__ == "__main__":
    run_tests()
