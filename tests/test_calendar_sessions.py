import sys
import os

# Asegurar que la raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models.user import UserModel
from models.task import TaskModel
from models.activity import ActivityModel
from models.study_session import StudySessionModel
from utils.security import generate_password_hash
import tests.test_auth as test_auth
import tests.test_roles as test_roles
import tests.test_tasks as test_tasks

def run_tests():
    print("==================================================")
    print("EJECUTANDO BATERÍA DE PRUEBAS — ETAPA 7: CALENDARIO Y SESIONES")
    print("==================================================")

    app = create_app()
    app.config["TESTING"] = True

    email_user_a = "test_user_a_etapa7@neurofocus.local"
    email_user_b = "test_user_b_etapa7@neurofocus.local"
    test_password = "PasswordSegura123!"

    # Limpieza preventiva previa
    UserModel.delete_user_by_email(email_user_a)
    UserModel.delete_user_by_email(email_user_b)

    id_user_a = None
    id_user_b = None

    try:
        # ----------------------------------------------------
        # PRUEBAS CALENDARIO
        # ----------------------------------------------------
        client_anon = app.test_client()

        # 1. Usuario no autenticado no puede acceder a calendario
        res_cal_anon = client_anon.get("/calendario", follow_redirects=False)
        assert res_cal_anon.status_code == 302, f"Esperado 302, obtenido {res_cal_anon.status_code}"
        assert res_cal_anon.headers["Location"].endswith("/login"), "No redirigió a /login"

        res_cal_anon_post = client_anon.post("/calendario/crear", data={"titulo": "Test"}, follow_redirects=False)
        assert res_cal_anon_post.status_code == 302, f"Esperado 302, obtenido {res_cal_anon_post.status_code}"
        assert res_cal_anon_post.headers["Location"].endswith("/login"), "No redirigió a /login"
        print("PRUEBA 1: Usuario no autenticado no puede acceder a calendario (302 a /login) -> OK")

        # 8. Usuario no autenticado no puede acceder a sesiones
        res_ses_anon = client_anon.get("/sesiones", follow_redirects=False)
        assert res_ses_anon.status_code == 302, f"Esperado 302, obtenido {res_ses_anon.status_code}"
        assert res_ses_anon.headers["Location"].endswith("/login"), "No redirigió a /login"

        res_ses_anon_post = client_anon.post("/sesiones/crear", data={"duracion_minutos": "25"}, follow_redirects=False)
        assert res_ses_anon_post.status_code == 302, f"Esperado 302, obtenido {res_ses_anon_post.status_code}"
        assert res_ses_anon_post.headers["Location"].endswith("/login"), "No redirigió a /login"
        print("PRUEBA 8: Usuario no autenticado no puede acceder a sesiones (302 a /login) -> OK")

        # Crear usuarios de prueba temporales
        with app.app_context():
            hashed_pw = generate_password_hash(test_password)
            id_user_a = UserModel.create_user(
                nombre="Usuario A Calendario",
                correo=email_user_a,
                password_hash=hashed_pw,
                rol="estudiante"
            )
            id_user_b = UserModel.create_user(
                nombre="Usuario B Calendario",
                correo=email_user_b,
                password_hash=hashed_pw,
                rol="estudiante"
            )

        # Iniciar sesión para Usuario A
        client_a = app.test_client()
        login_a = client_a.post("/login", data={"correo": email_user_a, "contrasena": test_password}, follow_redirects=False)
        assert login_a.status_code == 302, "Error al iniciar sesión de Usuario A"

        # Crear una tarea para usuario A para probar vinculación
        id_tarea_a = TaskModel.create(
            id_usuario=id_user_a,
            nombre="Tarea para Calendario",
            descripcion="Tarea de prueba",
            fecha_entrega="2026-10-30",
            prioridad="alta",
            estado="pendiente"
        )

        # 2. Usuario autenticado puede crear actividad
        res_crear_act = client_a.post("/calendario/crear", data={
            "titulo": "Sesión de Repaso de Química",
            "descripcion": "Estudio de estequiometría",
            "fecha_inicio": "2026-10-15 14:00",
            "fecha_fin": "2026-10-15 16:00",
            "tipo": "estudio",
            "id_tarea": str(id_tarea_a)
        }, follow_redirects=False)
        assert res_crear_act.status_code == 302, f"Fallo al crear actividad: {res_crear_act.status_code}"
        assert res_crear_act.headers["Location"].rstrip("/").endswith("/calendario"), "No redirigió a /calendario"
        print("PRUEBA 2: Usuario autenticado puede crear actividad en calendario (302 a /calendario) -> OK")

        # 3. La actividad queda asociada al usuario correcto
        actividades_a = ActivityModel.get_all_by_user(id_user_a)
        assert len(actividades_a) >= 1, "No se encontró la actividad en la base de datos"
        act_creada = actividades_a[0]
        assert act_creada["id_usuario"] == id_user_a, f"id_usuario no coincide: {act_creada['id_usuario']}"
        assert act_creada["titulo"] == "Sesión de Repaso de Química", f"Título no coincide: {act_creada['titulo']}"
        assert act_creada["tipo"] == "estudio", f"Tipo no coincide: {act_creada['tipo']}"
        assert act_creada["id_tarea"] == id_tarea_a, "La tarea vinculada no coincide"
        id_actividad_a = act_creada["id_actividad"]
        print(f"PRUEBA 3: La actividad (ID {id_actividad_a}) quedó correctamente asociada al usuario {id_user_a} -> OK")

        # 4. Usuario puede consultar sus actividades
        res_list_act = client_a.get("/calendario")
        assert res_list_act.status_code == 200, f"Error al consultar calendario: {res_list_act.status_code}"
        content_cal = res_list_act.get_data(as_text=True)
        assert "Sesión de Repaso de Química" in content_cal, "La actividad no aparece en el HTML"

        res_det_act = client_a.get(f"/calendario/{id_actividad_a}")
        assert res_det_act.status_code == 200, f"Error al ver detalle de actividad: {res_det_act.status_code}"
        print("PRUEBA 4: Usuario puede consultar sus actividades (200 OK en listado y detalle) -> OK")

        # 5. Usuario puede editar su actividad
        res_edit_act = client_a.post(f"/calendario/{id_actividad_a}/editar", data={
            "titulo": "Sesión de Química Orgánica",
            "descripcion": "Actualizado a compuestos aromáticos",
            "fecha_inicio": "2026-10-15 15:00",
            "fecha_fin": "2026-10-15 17:30",
            "tipo": "otro"
        }, follow_redirects=False)
        assert res_edit_act.status_code == 302, f"Fallo al editar actividad: {res_edit_act.status_code}"

        act_editada = ActivityModel.get_by_id(id_actividad_a)
        assert act_editada["titulo"] == "Sesión de Química Orgánica", "Título no actualizado"
        assert act_editada["tipo"] == "otro", "Tipo no actualizado"
        print("PRUEBA 5: Usuario puede editar su propia actividad exitosamente -> OK")

        # 6. Usuario puede eliminar su actividad
        id_act_borrar = ActivityModel.create(
            id_usuario=id_user_a,
            titulo="Actividad Temporal Para Borrar",
            fecha_inicio="2026-10-20 09:00",
            tipo="recordatorio"
        )
        assert ActivityModel.get_by_id(id_act_borrar) is not None, "Fallo al crear actividad temporal"

        res_del_act = client_a.post(f"/calendario/{id_act_borrar}/eliminar", follow_redirects=False)
        assert res_del_act.status_code == 302, f"Fallo al eliminar actividad: {res_del_act.status_code}"
        assert ActivityModel.get_by_id(id_act_borrar) is None, "La actividad no fue borrada de la DB"
        print("PRUEBA 6: Usuario puede eliminar su propia actividad exitosamente -> OK")

        # 7. Usuario A no puede acceder ni modificar actividades de usuario B
        id_act_b = ActivityModel.create(
            id_usuario=id_user_b,
            titulo="Actividad Secreta de Usuario B",
            fecha_inicio="2026-10-22 10:00",
            tipo="entrega"
        )

        res_a_view_b = client_a.get(f"/calendario/{id_act_b}")
        assert res_a_view_b.status_code == 403, f"Esperado 403 al ver actividad ajena, obtenido {res_a_view_b.status_code}"

        res_a_edit_b = client_a.post(f"/calendario/{id_act_b}/editar", data={
            "titulo": "Hackeo por A",
            "fecha_inicio": "2026-10-22 10:00",
            "tipo": "otro"
        })
        assert res_a_edit_b.status_code == 403, f"Esperado 403 al editar actividad ajena, obtenido {res_a_edit_b.status_code}"

        res_a_del_b = client_a.post(f"/calendario/{id_act_b}/eliminar")
        assert res_a_del_b.status_code == 403, f"Esperado 403 al eliminar actividad ajena, obtenido {res_a_del_b.status_code}"

        # Verificar que la actividad de B sigue intacta
        act_b_check = ActivityModel.get_by_id(id_act_b)
        assert act_b_check is not None and act_b_check["titulo"] == "Actividad Secreta de Usuario B"
        print("PRUEBA 7: Anti-IDOR Calendario: Usuario A no puede consultar/modificar/eliminar actividades de B (403) -> OK")

        # ----------------------------------------------------
        # PRUEBAS SESIONES DE ESTUDIO
        # ----------------------------------------------------
        # 9. Usuario puede crear una sesión
        res_crear_ses = client_a.post("/sesiones/crear", data={
            "duracion_minutos": "50",
            "tiempo_pausa_minutos": "10",
            "estado": "en_curso",
            "notas": "Bloque de física cuántica",
            "id_tarea": str(id_tarea_a)
        }, follow_redirects=False)
        assert res_crear_ses.status_code == 302, f"Fallo al crear sesión: {res_crear_ses.status_code}"
        assert res_crear_ses.headers["Location"].rstrip("/").endswith("/sesiones"), "No redirigió a /sesiones"
        print("PRUEBA 9: Usuario autenticado puede crear una sesión de estudio (302 a /sesiones) -> OK")

        # 10. La sesión queda asociada al usuario correcto
        sesiones_a = StudySessionModel.get_all_by_user(id_user_a)
        assert len(sesiones_a) >= 1, "No se encontró la sesión en la base de datos"
        ses_creada = sesiones_a[0]
        assert ses_creada["id_usuario"] == id_user_a, f"id_usuario no coincide: {ses_creada['id_usuario']}"
        assert ses_creada["duracion_minutos"] == 50, f"Duración no coincide: {ses_creada['duracion_minutos']}"
        assert ses_creada["tiempo_pausa_minutos"] == 10, f"Pausa no coincide: {ses_creada['tiempo_pausa_minutos']}"
        assert ses_creada["estado"] == "en_curso", f"Estado no coincide: {ses_creada['estado']}"
        assert ses_creada["id_tarea"] == id_tarea_a, "La tarea vinculada no coincide"
        id_sesion_a = ses_creada["id_sesion"]
        print(f"PRUEBA 10: La sesión (ID {id_sesion_a}) quedó correctamente asociada al usuario {id_user_a} -> OK")

        # 11. Usuario puede consultar sus propias sesiones
        res_list_ses = client_a.get("/sesiones")
        assert res_list_ses.status_code == 200, f"Error al consultar listado de sesiones: {res_list_ses.status_code}"
        content_ses = res_list_ses.get_data(as_text=True)
        assert "50 min" in content_ses, "La duración de la sesión no aparece en el HTML"

        res_det_ses = client_a.get(f"/sesiones/{id_sesion_a}")
        assert res_det_ses.status_code == 200, f"Error al consultar detalle de sesión: {res_det_ses.status_code}"
        print("PRUEBA 11: Usuario puede consultar sus propias sesiones de estudio (200 OK) -> OK")

        # 12. Usuario puede finalizar una sesión
        res_fin_ses = client_a.post(f"/sesiones/{id_sesion_a}/finalizar", data={
            "notas": "Completada exitosamente todos los ejercicios"
        }, follow_redirects=False)
        assert res_fin_ses.status_code == 302, f"Fallo al finalizar sesión: {res_fin_ses.status_code}"

        ses_finalizada = StudySessionModel.get_by_id(id_sesion_a)
        assert ses_finalizada["estado"] == "completada", f"Estado esperado 'completada', obtenido: {ses_finalizada['estado']}"
        assert ses_finalizada["fecha_fin"] is not None, "fecha_fin no registrada tras finalizar"
        print("PRUEBA 12: Usuario puede finalizar una sesión (cambio a 'completada' y registro de fecha_fin) -> OK")

        # 13. Usuario A no puede acceder a sesiones de usuario B
        id_sesion_b = StudySessionModel.create(
            id_usuario=id_user_b,
            duracion_minutos=30,
            tiempo_pausa_minutos=5,
            estado="en_curso",
            notas="Sesión privada de Usuario B"
        )

        res_a_view_ses_b = client_a.get(f"/sesiones/{id_sesion_b}")
        assert res_a_view_ses_b.status_code == 403, f"Esperado 403 al ver sesión ajena, obtenido {res_a_view_ses_b.status_code}"

        res_a_fin_ses_b = client_a.post(f"/sesiones/{id_sesion_b}/finalizar")
        assert res_a_fin_ses_b.status_code == 403, f"Esperado 403 al finalizar sesión ajena, obtenido {res_a_fin_ses_b.status_code}"

        res_a_del_ses_b = client_a.post(f"/sesiones/{id_sesion_b}/eliminar")
        assert res_a_del_ses_b.status_code == 403, f"Esperado 403 al eliminar sesión ajena, obtenido {res_a_del_ses_b.status_code}"

        ses_b_check = StudySessionModel.get_by_id(id_sesion_b)
        assert ses_b_check is not None and ses_b_check["estado"] == "en_curso"
        print("PRUEBA 13: Anti-IDOR Sesiones: Usuario A no puede consultar/finalizar/eliminar sesiones de B (403) -> OK")

    finally:
        # Limpieza obligatoria de datos de prueba
        if id_user_a:
            ActivityModel.delete_all_by_user(id_user_a)
            StudySessionModel.delete_all_by_user(id_user_a)
            TaskModel.delete_all_by_user(id_user_a)
        if id_user_b:
            ActivityModel.delete_all_by_user(id_user_b)
            StudySessionModel.delete_all_by_user(id_user_b)
            TaskModel.delete_all_by_user(id_user_b)

        del_a = UserModel.delete_user_by_email(email_user_a)
        del_b = UserModel.delete_user_by_email(email_user_b)

        assert UserModel.get_by_email(email_user_a) is None, "Fallo al eliminar Usuario A"
        assert UserModel.get_by_email(email_user_b) is None, "Fallo al eliminar Usuario B"

        print("--------------------------------------------------")
        print("LIMPIEZA DE DATOS TEMPORALES:")
        print(f"- Actividades, Sesiones, Tareas y Usuario A ({email_user_a}) eliminados: {del_a}")
        print(f"- Actividades, Sesiones, Tareas y Usuario B ({email_user_b}) eliminados: {del_b}")
        print("--------------------------------------------------")

    # ----------------------------------------------------
    # REGRESIÓN: Etapas 4, 5 y 6
    # ----------------------------------------------------
    print("\n>>> Verificando regresión con Batería de Autenticación (Etapa 4)...")
    test_auth.run_tests()
    print("PRUEBA 14: Batería de pruebas de autenticación pasó sin regresiones -> OK")

    print("\n>>> Verificando regresión con Batería de Roles y Permisos (Etapa 5)...")
    test_roles.run_tests()
    print("PRUEBA 15: Batería de pruebas de roles pasó sin regresiones -> OK")

    print("\n>>> Verificando regresión con Batería de Tareas (Etapa 6)...")
    test_tasks.run_tests()
    print("PRUEBA 16: Batería de pruebas de tareas pasó sin regresiones -> OK")

    print("==================================================")
    print("TODAS LAS 16 PRUEBAS DE LA ETAPA 7 PASARON EXITOSAMENTE")
    print("==================================================")

def test_suite_calendar_sessions():
    run_tests()

if __name__ == "__main__":
    run_tests()
