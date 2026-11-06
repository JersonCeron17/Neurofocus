import sys
import os

# Asegurar que la raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models.user import UserModel
from models.task import TaskModel
from utils.security import generate_password_hash
import tests.test_auth as test_auth
import tests.test_roles as test_roles

def run_tests():
    print("==================================================")
    print("EJECUTANDO BATERÍA DE PRUEBAS — ETAPA 6: MÓDULO DE TAREAS")
    print("==================================================")

    app = create_app()
    app.config["TESTING"] = True

    email_user_a = "test_user_a_etapa6@neurofocus.local"
    email_user_b = "test_user_b_etapa6@neurofocus.local"
    test_password = "PasswordSegura123!"

    # Limpieza preventiva previa
    UserModel.delete_user_by_email(email_user_a)
    UserModel.delete_user_by_email(email_user_b)

    id_user_a = None
    id_user_b = None

    try:
        # ----------------------------------------------------
        # 1. Usuario no autenticado no puede acceder a tareas
        # ----------------------------------------------------
        client_anon = app.test_client()

        res_anon_get = client_anon.get("/tareas", follow_redirects=False)
        assert res_anon_get.status_code == 302, f"Esperado 302, obtenido {res_anon_get.status_code}"
        assert res_anon_get.headers["Location"].endswith("/login"), "No redirigió a /login"

        res_anon_post = client_anon.post("/tareas/crear", data={
            "nombre": "Tarea Anónima",
            "prioridad": "media"
        }, follow_redirects=False)
        assert res_anon_post.status_code == 302, f"Esperado 302, obtenido {res_anon_post.status_code}"
        assert res_anon_post.headers["Location"].endswith("/login"), "No redirigió a /login"

        res_anon_edit = client_anon.get("/tareas/1/editar", follow_redirects=False)
        assert res_anon_edit.status_code == 302, f"Esperado 302, obtenido {res_anon_edit.status_code}"
        assert res_anon_edit.headers["Location"].endswith("/login"), "No redirigió a /login"

        print("PRUEBA 1: Usuario no autenticado no puede acceder a tareas (302 a /login) -> OK")

        # Crear usuarios temporales para las pruebas
        with app.app_context():
            hashed_pw = generate_password_hash(test_password)
            id_user_a = UserModel.create_user(
                nombre="Usuario A Tareas",
                correo=email_user_a,
                password_hash=hashed_pw,
                rol="estudiante"
            )
            id_user_b = UserModel.create_user(
                nombre="Usuario B Tareas",
                correo=email_user_b,
                password_hash=hashed_pw,
                rol="estudiante"
            )

        # Cliente autenticado para Usuario A
        client_a = app.test_client()
        login_res_a = client_a.post("/login", data={
            "correo": email_user_a,
            "contrasena": test_password
        }, follow_redirects=False)
        assert login_res_a.status_code == 302, "Error al iniciar sesión de Usuario A"

        # ----------------------------------------------------
        # 2. Usuario autenticado puede crear una tarea
        # ----------------------------------------------------
        res_crear = client_a.post("/tareas/crear", data={
            "nombre": "Estudiar Álgebra Lineal",
            "descripcion": "Repasar matrices y determinantes",
            "fecha_entrega": "2026-10-15",
            "prioridad": "alta",
            "estado": "pendiente"
        }, follow_redirects=False)
        assert res_crear.status_code == 302, f"Fallo al crear tarea: {res_crear.status_code}"
        assert res_crear.headers["Location"].rstrip("/").endswith("/tareas"), f"No redirigió a /tareas: {res_crear.headers['Location']}"
        print("PRUEBA 2: Usuario autenticado puede crear una tarea (302 a /tareas) -> OK")

        # ----------------------------------------------------
        # 3. La tarea queda asociada al usuario correcto
        # ----------------------------------------------------
        tareas_a = TaskModel.get_all_by_user(id_user_a)
        assert len(tareas_a) >= 1, "No se encontró la tarea en la base de datos"
        tarea_creada = tareas_a[0]
        assert tarea_creada["id_usuario"] == id_user_a, f"id_usuario no coincide: {tarea_creada['id_usuario']}"
        assert tarea_creada["nombre"] == "Estudiar Álgebra Lineal", f"Nombre inesperado: {tarea_creada['nombre']}"
        assert tarea_creada["prioridad"] == "alta", f"Prioridad inesperada: {tarea_creada['prioridad']}"
        assert tarea_creada["estado"] == "pendiente", f"Estado inesperado: {tarea_creada['estado']}"
        id_tarea_a = tarea_creada["id_tarea"]
        print(f"PRUEBA 3: La tarea (ID {id_tarea_a}) quedó correctamente asociada al usuario {id_user_a} -> OK")

        # ----------------------------------------------------
        # 4. Usuario puede consultar sus propias tareas
        # ----------------------------------------------------
        res_list = client_a.get("/tareas")
        assert res_list.status_code == 200, f"Error al consultar listado de tareas: {res_list.status_code}"
        content_list = res_list.get_data(as_text=True)
        assert "Estudiar Álgebra Lineal" in content_list, "La tarea no aparece en el HTML del listado"
        assert "Repasar matrices" in content_list, "La descripción no aparece en el listado"

        # Consulta individual de detalle
        res_det = client_a.get(f"/tareas/{id_tarea_a}")
        assert res_det.status_code == 200, f"Error al consultar detalle de tarea: {res_det.status_code}"
        print("PRUEBA 4: Usuario puede consultar sus propias tareas (200 OK) -> OK")

        # ----------------------------------------------------
        # 5. Usuario puede editar su propia tarea
        # ----------------------------------------------------
        res_edit = client_a.post(f"/tareas/{id_tarea_a}/editar", data={
            "nombre": "Estudiar Álgebra Lineal y Cálculo",
            "descripcion": "Actualizado con ejercicios de derivadas",
            "fecha_entrega": "2026-10-20",
            "prioridad": "media",
            "estado": "en_progreso"
        }, follow_redirects=False)
        assert res_edit.status_code == 302, f"Fallo al editar tarea: {res_edit.status_code}"
        assert res_edit.headers["Location"].rstrip("/").endswith("/tareas"), "No redirigió a /tareas tras editar"

        tarea_editada = TaskModel.get_by_id(id_tarea_a)
        assert tarea_editada["nombre"] == "Estudiar Álgebra Lineal y Cálculo", "Nombre no se actualizó"
        assert tarea_editada["prioridad"] == "media", "Prioridad no se actualizó"
        assert tarea_editada["estado"] == "en_progreso", "Estado no se actualizó"
        print("PRUEBA 5: Usuario puede editar su propia tarea exitosamente -> OK")

        # ----------------------------------------------------
        # 6. Usuario puede completar su propia tarea
        # ----------------------------------------------------
        res_comp = client_a.post(f"/tareas/{id_tarea_a}/completar", follow_redirects=False)
        assert res_comp.status_code == 302, f"Fallo al completar tarea: {res_comp.status_code}"
        assert res_comp.headers["Location"].rstrip("/").endswith("/tareas"), "No redirigió a /tareas tras completar"

        tarea_completada = TaskModel.get_by_id(id_tarea_a)
        assert tarea_completada["estado"] == "completada", f"Estado no es 'completada': {tarea_completada['estado']}"
        assert tarea_completada["fecha_completada"] is not None, "fecha_completada no fue registrada"
        print("PRUEBA 6: Usuario puede completar su propia tarea y se registra fecha_completada -> OK")

        # ----------------------------------------------------
        # 7. Usuario puede eliminar su propia tarea
        # ----------------------------------------------------
        # Creamos una tarea secundaria para eliminar
        id_tarea_para_borrar = TaskModel.create(
            id_usuario=id_user_a,
            nombre="Tarea Secundaria a Eliminar",
            descripcion="Temporal",
            fecha_entrega="2026-10-30",
            prioridad="baja",
            estado="pendiente"
        )
        assert TaskModel.get_by_id(id_tarea_para_borrar) is not None, "No se pudo crear tarea secundaria"

        res_del = client_a.post(f"/tareas/{id_tarea_para_borrar}/eliminar", follow_redirects=False)
        assert res_del.status_code == 302, f"Fallo al eliminar tarea: {res_del.status_code}"
        assert res_del.headers["Location"].rstrip("/").endswith("/tareas"), "No redirigió a /tareas tras eliminar"
        assert TaskModel.get_by_id(id_tarea_para_borrar) is None, "La tarea no fue eliminada de la base de datos"
        print("PRUEBA 7: Usuario puede eliminar su propia tarea exitosamente -> OK")

        # ----------------------------------------------------
        # 8. Usuario A no puede consultar/modificar/eliminar tareas de usuario B
        # ----------------------------------------------------
        # Crear tarea perteneciente a Usuario B
        id_tarea_b = TaskModel.create(
            id_usuario=id_user_b,
            nombre="Tarea Privada de Usuario B",
            descripcion="Secretos de B",
            fecha_entrega="2026-11-01",
            prioridad="alta",
            estado="pendiente"
        )

        # Usuario A intenta consultar detalle de la tarea de B -> 403
        res_a_view_b = client_a.get(f"/tareas/{id_tarea_b}")
        assert res_a_view_b.status_code == 403, f"Esperado 403 al ver tarea ajena, obtenido {res_a_view_b.status_code}"

        # Usuario A intenta editar la tarea de B (GET) -> 403
        res_a_get_edit_b = client_a.get(f"/tareas/{id_tarea_b}/editar")
        assert res_a_get_edit_b.status_code == 403, f"Esperado 403 al solicitar editar tarea ajena, obtenido {res_a_get_edit_b.status_code}"

        # Usuario A intenta modificar la tarea de B (POST) -> 403
        res_a_post_edit_b = client_a.post(f"/tareas/{id_tarea_b}/editar", data={
            "nombre": "Ataque de Usuario A",
            "prioridad": "baja",
            "estado": "completada"
        })
        assert res_a_post_edit_b.status_code == 403, f"Esperado 403 al intentar modificar tarea ajena, obtenido {res_a_post_edit_b.status_code}"

        # Usuario A intenta completar la tarea de B -> 403
        res_a_comp_b = client_a.post(f"/tareas/{id_tarea_b}/completar")
        assert res_a_comp_b.status_code == 403, f"Esperado 403 al intentar completar tarea ajena, obtenido {res_a_comp_b.status_code}"

        # Usuario A intenta eliminar la tarea de B -> 403
        res_a_del_b = client_a.post(f"/tareas/{id_tarea_b}/eliminar")
        assert res_a_del_b.status_code == 403, f"Esperado 403 al intentar eliminar tarea ajena, obtenido {res_a_del_b.status_code}"

        # Verificar que la tarea de B sigue intacta
        tarea_b_check = TaskModel.get_by_id(id_tarea_b)
        assert tarea_b_check is not None, "La tarea de B fue alterada o borrada"
        assert tarea_b_check["nombre"] == "Tarea Privada de Usuario B", "El nombre de B fue modificado por A"
        assert tarea_b_check["estado"] == "pendiente", "El estado de B fue modificado por A"

        # Verificar que en el listado de Usuario A no aparece la tarea de Usuario B
        res_list_a = client_a.get("/tareas")
        assert "Tarea Privada de Usuario B" not in res_list_a.get_data(as_text=True), "La tarea de B apareció en el listado de A"

        print("PRUEBA 8: Control de acceso horizontal (IDOR): Usuario A no puede consultar/modificar/eliminar tareas de Usuario B (403) -> OK")

        # ----------------------------------------------------
        # 9. Validación de nombre obligatorio
        # ----------------------------------------------------
        res_val_nombre_empty = client_a.post("/tareas/crear", data={
            "nombre": "",
            "prioridad": "media"
        })
        assert res_val_nombre_empty.status_code == 400, f"Debería rechazar nombre vacío: {res_val_nombre_empty.status_code}"

        res_val_nombre_spaces = client_a.post("/tareas/crear", data={
            "nombre": "     ",
            "prioridad": "media"
        })
        assert res_val_nombre_spaces.status_code == 400, f"Debería rechazar nombre con solo espacios: {res_val_nombre_spaces.status_code}"
        print("PRUEBA 9: Validación de nombre obligatorio rechazada correctamente con 400 -> OK")

        # ----------------------------------------------------
        # 10. Validación de prioridad
        # ----------------------------------------------------
        res_val_prio = client_a.post("/tareas/crear", data={
            "nombre": "Tarea Prioridad Inválida",
            "prioridad": "urgente_critica_no_permitida"
        })
        assert res_val_prio.status_code == 400, f"Debería rechazar prioridad no válida: {res_val_prio.status_code}"
        print("PRUEBA 10: Validación de prioridad restringida a ('alta', 'media', 'baja') con 400 -> OK")

        # ----------------------------------------------------
        # 11. Validación de estado
        # ----------------------------------------------------
        res_val_estado = client_a.post(f"/tareas/{id_tarea_a}/editar", data={
            "nombre": "Tarea Estado Inválido",
            "prioridad": "media",
            "estado": "destruida_invalido"
        })
        assert res_val_estado.status_code == 400, f"Debería rechazar estado no válido: {res_val_estado.status_code}"
        print("PRUEBA 11: Validación de estado restringida a ('pendiente', 'en_progreso', 'completada') con 400 -> OK")

        # ----------------------------------------------------
        # 12. Logout continúa funcionando
        # ----------------------------------------------------
        res_logout = client_a.get("/logout", follow_redirects=False)
        assert res_logout.status_code == 302, f"Logout falló: {res_logout.status_code}"
        assert res_logout.headers["Location"].endswith("/login"), "Logout no redirigió a /login"

        # Tras logout, el acceso a /tareas debe ser denegado y redirigido a login
        res_tareas_post_logout = client_a.get("/tareas", follow_redirects=False)
        assert res_tareas_post_logout.status_code == 302, "Acceso a /tareas permitido tras logout"
        assert res_tareas_post_logout.headers["Location"].endswith("/login"), "No redirigió tras logout"
        print("PRUEBA 12: Logout finaliza la sesión y revoca el acceso a /tareas -> OK")

    finally:
        # ----------------------------------------------------
        # LIMPIEZA OBLIGATORIA DE DATOS TEMPORALES
        # ----------------------------------------------------
        if id_user_a:
            TaskModel.delete_all_by_user(id_user_a)
        if id_user_b:
            TaskModel.delete_all_by_user(id_user_b)

        del_a = UserModel.delete_user_by_email(email_user_a)
        del_b = UserModel.delete_user_by_email(email_user_b)

        # Confirmación de que no existen en DB
        assert UserModel.get_by_email(email_user_a) is None, "Fallo al eliminar Usuario A"
        assert UserModel.get_by_email(email_user_b) is None, "Fallo al eliminar Usuario B"

        print("--------------------------------------------------")
        print("LIMPIEZA DE DATOS TEMPORALES:")
        print(f"- Tareas y Usuario A ({email_user_a}) eliminados: {del_a}")
        print(f"- Tareas y Usuario B ({email_user_b}) eliminados: {del_b}")
        print("--------------------------------------------------")

    # ----------------------------------------------------
    # 13. Las pruebas anteriores de autenticación continúan funcionando
    # ----------------------------------------------------
    print("\n>>> Verificando regresión con Batería de Autenticación (Etapa 4)...")
    test_auth.run_tests()
    print("PRUEBA 13: Batería de pruebas de autenticación pasó sin regresiones -> OK")

    # ----------------------------------------------------
    # 14. Las pruebas anteriores de roles continúan funcionando
    # ----------------------------------------------------
    print("\n>>> Verificando regresión con Batería de Roles y Permisos (Etapa 5)...")
    test_roles.run_tests()
    print("PRUEBA 14: Batería de pruebas de roles pasó sin regresiones -> OK")

    print("==================================================")
    print("TODAS LAS 14 PRUEBAS DE LA ETAPA 6 PASARON EXITOSAMENTE")
    print("==================================================")

def test_suite_tasks():
    run_tests()

if __name__ == "__main__":
    run_tests()
