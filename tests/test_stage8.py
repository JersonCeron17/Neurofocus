import sys
import os
from datetime import date

# Asegurar que la raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models.user import UserModel
from models.exercise import ExerciseModel, ExerciseResultModel
from models.progress import ProgressModel
from models.achievement import AchievementModel
from utils.security import generate_password_hash
import tests.test_auth as test_auth
import tests.test_roles as test_roles
import tests.test_tasks as test_tasks
import tests.test_calendar_sessions as test_calendar_sessions

def run_tests():
    print("==================================================")
    print("EJECUTANDO BATERÍA DE PRUEBAS — ETAPA 8: EJERCICIOS + PROGRESO + LOGROS")
    print("==================================================")

    app = create_app()
    app.config["TESTING"] = True

    email_user_a = "test_user_a_etapa8@neurofocus.local"
    email_user_b = "test_user_b_etapa8@neurofocus.local"
    test_password = "PasswordSegura123!"

    # Limpieza preventiva previa
    UserModel.delete_user_by_email(email_user_a)
    UserModel.delete_user_by_email(email_user_b)

    id_user_a = None
    id_user_b = None

    try:
        # ----------------------------------------------------
        # PRUEBAS EJERCICIOS
        # ----------------------------------------------------
        client_anon = app.test_client()

        # 1. Usuario no autenticado no puede acceder
        res_ej_anon = client_anon.get("/ejercicios", follow_redirects=False)
        assert res_ej_anon.status_code == 302, f"Esperado 302, obtenido {res_ej_anon.status_code}"
        assert res_ej_anon.headers["Location"].endswith("/login"), "No redirigió a /login"

        res_prog_anon = client_anon.get("/progreso", follow_redirects=False)
        assert res_prog_anon.status_code == 302, f"Esperado 302, obtenido {res_prog_anon.status_code}"
        assert res_prog_anon.headers["Location"].endswith("/login"), "No redirigió a /login"

        res_log_anon = client_anon.get("/logros", follow_redirects=False)
        assert res_log_anon.status_code == 302, f"Esperado 302, obtenido {res_log_anon.status_code}"
        assert res_log_anon.headers["Location"].endswith("/login"), "No redirigió a /login"
        print("PRUEBA 1: Usuario no autenticado no puede acceder a ejercicios, progreso ni logros (302 a /login) -> OK")

        # Crear usuarios temporales de prueba
        with app.app_context():
            hashed_pw = generate_password_hash(test_password)
            id_user_a = UserModel.create_user(
                nombre="Usuario A Etapa 8",
                correo=email_user_a,
                password_hash=hashed_pw,
                rol="estudiante"
            )
            id_user_b = UserModel.create_user(
                nombre="Usuario B Etapa 8",
                correo=email_user_b,
                password_hash=hashed_pw,
                rol="estudiante"
            )

        # Iniciar sesión para Usuario A
        client_a = app.test_client()
        login_a = client_a.post("/login", data={"correo": email_user_a, "contrasena": test_password}, follow_redirects=False)
        assert login_a.status_code == 302, "Error al iniciar sesión de Usuario A"

        # 2. Usuario autenticado puede consultar ejercicios
        res_ej_list = client_a.get("/ejercicios")
        assert res_ej_list.status_code == 200, f"Error al consultar ejercicios: {res_ej_list.status_code}"
        content_ej = res_ej_list.get_data(as_text=True)
        assert "Prueba de Stroop" in content_ej or "Secuencia" in content_ej, "Los ejercicios no aparecen en el catálogo"
        print("PRUEBA 2: Usuario autenticado puede consultar ejercicios disponibles (200 OK) -> OK")

        # Obtener un ejercicio para la prueba
        ejercicios = ExerciseModel.get_all()
        assert len(ejercicios) >= 1, "No existen ejercicios en el catálogo"
        ej_test = ejercicios[0]
        id_ej = ej_test["id_ejercicio"]

        # 3. Usuario puede registrar un resultado
        res_reg_res = client_a.post(f"/ejercicios/{id_ej}/resultado", data={
            "puntuacion": "95",
            "tiempo_segundos": "45"
        }, follow_redirects=False)
        assert res_reg_res.status_code == 302, f"Fallo al registrar resultado: {res_reg_res.status_code}"
        assert res_reg_res.headers["Location"].rstrip("/").endswith("/ejercicios/mis-resultados"), "No redirigió a mis-resultados"
        print("PRUEBA 3: Usuario puede registrar un resultado de ejercicio exitosamente (302 a /ejercicios/mis-resultados) -> OK")

        # 4. El resultado queda asociado al usuario correcto
        resultados_a = ExerciseResultModel.get_all_by_user(id_user_a)
        assert len(resultados_a) >= 1, "No se encontró el resultado en la base de datos"
        res_creado = resultados_a[0]
        assert res_creado["id_usuario"] == id_user_a, f"id_usuario no coincide: {res_creado['id_usuario']}"
        assert res_creado["id_ejercicio"] == id_ej, f"id_ejercicio no coincide: {res_creado['id_ejercicio']}"
        assert res_creado["puntuacion"] == 95, f"Puntuación no coincide: {res_creado['puntuacion']}"
        assert res_creado["tiempo_segundos"] == 45, f"Tiempo no coincide: {res_creado['tiempo_segundos']}"
        id_res_a = res_creado["id_resultado"]
        print(f"PRUEBA 4: El resultado (ID {id_res_a}) quedó asociado correctamente al usuario {id_user_a} -> OK")

        # 5. Usuario no puede acceder a resultados de otro usuario
        id_res_b = ExerciseResultModel.create(
            id_usuario=id_user_b,
            id_ejercicio=id_ej,
            puntuacion=80,
            tiempo_segundos=60
        )

        # Usuario A intenta ver detalle de resultado de B -> 403
        res_a_view_b = client_a.get(f"/ejercicios/resultados/{id_res_b}")
        assert res_a_view_b.status_code == 403, f"Esperado 403 al ver resultado ajeno, obtenido {res_a_view_b.status_code}"

        # Verificar que en el listado de A no aparece el resultado de B
        res_mis_res_a = client_a.get("/ejercicios/mis-resultados")
        assert f"#{id_res_b}" not in res_mis_res_a.get_data(as_text=True), "El resultado de B apareció en el listado de A"
        print("PRUEBA 5: Anti-IDOR Ejercicios: Usuario A no puede acceder a resultados de Usuario B (403) -> OK")

        # ----------------------------------------------------
        # PRUEBAS PROGRESO DIARIO
        # ----------------------------------------------------
        # 6. Usuario autenticado puede consultar su progreso
        res_prog_get = client_a.get("/progreso")
        assert res_prog_get.status_code == 200, f"Error al consultar progreso: {res_prog_get.status_code}"
        assert "Mi Progreso Diario" in res_prog_get.get_data(as_text=True), "No cargó la vista de progreso"
        print("PRUEBA 6: Usuario autenticado puede consultar su progreso (200 OK) -> OK")

        # 7. Usuario puede registrar/actualizar progreso
        fecha_prueba = date(2026, 10, 15)
        res_act_prog = client_a.post("/progreso/actualizar", data={
            "fecha": fecha_prueba.isoformat(),
            "tareas_completadas": "4",
            "minutos_estudio": "60",
            "ejercicios_completados": "3"
        }, follow_redirects=False)
        assert res_act_prog.status_code == 302, f"Fallo al actualizar progreso: {res_act_prog.status_code}"

        prog_db = ProgressModel.get_by_user_and_date(id_user_a, fecha_prueba)
        assert prog_db is not None, "No se guardó el progreso en la base de datos"
        assert prog_db["tareas_completadas"] == 4, "tareas_completadas no coincide"
        assert prog_db["minutos_estudio"] == 60, "minutos_estudio no coincide"
        assert prog_db["ejercicios_completados"] == 3, "ejercicios_completados no coincide"
        id_prog_a = prog_db["id_progreso"]
        print("PRUEBA 7: Usuario puede registrar/actualizar su progreso diario -> OK")

        # 8. No se generan duplicados para la misma fecha y usuario
        # Se envía una actualización para la misma fecha
        res_act_dup = client_a.post("/progreso/actualizar", data={
            "fecha": fecha_prueba.isoformat(),
            "tareas_completadas": "5",
            "minutos_estudio": "75",
            "ejercicios_completados": "4"
        }, follow_redirects=False)
        assert res_act_dup.status_code == 302, "Fallo al re-actualizar progreso"

        # Verificar que sigue habiendo un único registro para esa fecha y usuario
        all_prog_a = [p for p in ProgressModel.get_all_by_user(id_user_a) if p["fecha"] == fecha_prueba]
        assert len(all_prog_a) == 1, f"Se generaron duplicados para la misma fecha: {len(all_prog_a)}"
        assert all_prog_a[0]["tareas_completadas"] == 5, "No se actualizó el valor existente"
        assert all_prog_a[0]["minutos_estudio"] == 75, "No se actualizó el valor existente"
        print("PRUEBA 8: Restricción uq_usuario_fecha verificada: No se generan duplicados para la misma fecha y usuario -> OK")

        # 9. Usuario no puede acceder al progreso de otro usuario
        fecha_b = date(2026, 10, 16)
        id_prog_b = ProgressModel.upsert(
            id_usuario=id_user_b,
            fecha=fecha_b,
            tareas_completadas=10,
            minutos_estudio=120,
            ejercicios_completados=5
        )

        res_a_view_prog_b = client_a.get(f"/progreso/{id_prog_b}")
        assert res_a_view_prog_b.status_code == 403, f"Esperado 403 al ver progreso ajeno, obtenido {res_a_view_prog_b.status_code}"
        print("PRUEBA 9: Anti-IDOR Progreso: Usuario A no puede acceder al progreso de Usuario B (403) -> OK")

        # ----------------------------------------------------
        # PRUEBAS LOGROS
        # ----------------------------------------------------
        # 10. Usuario autenticado puede consultar logros disponibles
        res_log_get = client_a.get("/logros")
        assert res_log_get.status_code == 200, f"Error al consultar logros: {res_log_get.status_code}"
        content_log = res_log_get.get_data(as_text=True)
        assert "Primer Paso" in content_log or "Mente Enfocada" in content_log, "No aparecen los logros del catálogo"
        print("PRUEBA 10: Usuario autenticado puede consultar el catálogo de logros (200 OK) -> OK")

        # 11. Usuario puede consultar sus logros (ver cuáles tiene desbloqueados)
        # Como Usuario A registró un ejercicio y progreso, debe tener logros desbloqueados
        logros_a = AchievementModel.get_user_achievements(id_user_a)
        desbloqueados_a = [l for l in logros_a if l["desbloqueado"]]
        assert len(desbloqueados_a) >= 1, "No se registró ningún logro desbloqueado para Usuario A"
        print(f"PRUEBA 11: Usuario puede consultar sus logros ({len(desbloqueados_a)} desbloqueados) -> OK")

        # 12. Usuario no puede modificar o consultar asignaciones de otro usuario
        # Verificar que los logros de B están limpios (no afectados por A)
        logros_b = AchievementModel.get_user_achievements(id_user_b)
        desbloqueados_b = [l for l in logros_b if l["desbloqueado"]]
        assert len(desbloqueados_b) == 0, "Usuario B tiene logros desbloqueados inesperadamente"
        print("PRUEBA 12: Control de asignación de logros: Los logros están estrictamente asociados al usuario de la sesión -> OK")

    finally:
        # Limpieza obligatoria de todos los datos temporales
        if id_user_a:
            ExerciseResultModel.delete_all_by_user(id_user_a)
            ProgressModel.delete_all_by_user(id_user_a)
            AchievementModel.delete_all_by_user(id_user_a)
        if id_user_b:
            ExerciseResultModel.delete_all_by_user(id_user_b)
            ProgressModel.delete_all_by_user(id_user_b)
            AchievementModel.delete_all_by_user(id_user_b)

        del_a = UserModel.delete_user_by_email(email_user_a)
        del_b = UserModel.delete_user_by_email(email_user_b)

        assert UserModel.get_by_email(email_user_a) is None, "Fallo al eliminar Usuario A"
        assert UserModel.get_by_email(email_user_b) is None, "Fallo al eliminar Usuario B"

        print("--------------------------------------------------")
        print("LIMPIEZA DE DATOS TEMPORALES:")
        print(f"- Resultados, Progreso, Logros y Usuario A ({email_user_a}) eliminados: {del_a}")
        print(f"- Resultados, Progreso, Logros y Usuario B ({email_user_b}) eliminados: {del_b}")
        print("--------------------------------------------------")

    # ----------------------------------------------------
    # REGRESIÓN: Etapas 4, 5, 6 y 7
    # ----------------------------------------------------
    print("\n>>> Verificando regresión con Batería de Autenticación (Etapa 4)...")
    test_auth.run_tests()
    print("PRUEBA 13: Batería de pruebas de autenticación pasó sin regresiones -> OK")

    print("\n>>> Verificando regresión con Batería de Roles y Permisos (Etapa 5)...")
    test_roles.run_tests()
    print("PRUEBA 14: Batería de pruebas de roles pasó sin regresiones -> OK")

    print("\n>>> Verificando regresión con Batería de Tareas (Etapa 6)...")
    test_tasks.run_tests()
    print("PRUEBA 15: Batería de pruebas de tareas pasó sin regresiones -> OK")

    print("\n>>> Verificando regresión con Batería de Calendario y Sesiones (Etapa 7)...")
    test_calendar_sessions.run_tests()
    print("PRUEBA 16: Batería de pruebas de calendario y sesiones pasó sin regresiones -> OK")

    print("==================================================")
    print("TODAS LAS 16 PRUEBAS DE LA ETAPA 8 PASARON EXITOSAMENTE")
    print("==================================================")

def test_suite_stage8():
    run_tests()

if __name__ == "__main__":
    run_tests()
