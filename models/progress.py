from config.database import get_db_connection

class ProgressModel:
    """Modelo de acceso a datos para la tabla oficial 'progreso_diario'."""

    @classmethod
    def upsert(cls, id_usuario: int, fecha, tareas_completadas: int = 0, minutos_estudio: int = 0, ejercicios_completados: int = 0) -> int:
        """
        Inserta o actualiza el progreso diario del usuario para la fecha indicada.
        Asegura que no se generen duplicados respetando la restricción UNIQUE (id_usuario, fecha).
        """
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO progreso_diario (id_usuario, fecha, tareas_completadas, minutos_estudio, ejercicios_completados)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id_usuario, fecha) 
            DO UPDATE SET 
                tareas_completadas = EXCLUDED.tareas_completadas,
                minutos_estudio = EXCLUDED.minutos_estudio,
                ejercicios_completados = EXCLUDED.ejercicios_completados
            RETURNING id_progreso;
            """,
            (id_usuario, fecha, max(0, tareas_completadas), max(0, minutos_estudio), max(0, ejercicios_completados))
        )
        id_progreso = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return id_progreso

    @classmethod
    def get_by_id(cls, id_progreso: int):
        """Obtiene un registro de progreso por su id_progreso."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id_progreso, id_usuario, fecha, tareas_completadas, minutos_estudio, ejercicios_completados
            FROM progreso_diario
            WHERE id_progreso = %s;
            """,
            (id_progreso,)
        )
        r = cur.fetchone()
        cur.close()
        conn.close()
        if r:
            return {
                "id_progreso": r[0],
                "id_usuario": r[1],
                "fecha": r[2],
                "tareas_completadas": r[3],
                "minutos_estudio": r[4],
                "ejercicios_completados": r[5]
            }
        return None

    @classmethod
    def get_by_user_and_date(cls, id_usuario: int, fecha):
        """Obtiene el progreso de un usuario para una fecha determinada."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id_progreso, id_usuario, fecha, tareas_completadas, minutos_estudio, ejercicios_completados
            FROM progreso_diario
            WHERE id_usuario = %s AND fecha = %s;
            """,
            (id_usuario, fecha)
        )
        r = cur.fetchone()
        cur.close()
        conn.close()
        if r:
            return {
                "id_progreso": r[0],
                "id_usuario": r[1],
                "fecha": r[2],
                "tareas_completadas": r[3],
                "minutos_estudio": r[4],
                "ejercicios_completados": r[5]
            }
        return None

    @classmethod
    def get_all_by_user(cls, id_usuario: int):
        """Obtiene el historial de progreso diario del usuario ordenado cronológicamente de forma descendente."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id_progreso, id_usuario, fecha, tareas_completadas, minutos_estudio, ejercicios_completados
            FROM progreso_diario
            WHERE id_usuario = %s
            ORDER BY fecha DESC, id_progreso DESC;
            """,
            (id_usuario,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [
            {
                "id_progreso": r[0],
                "id_usuario": r[1],
                "fecha": r[2],
                "tareas_completadas": r[3],
                "minutos_estudio": r[4],
                "ejercicios_completados": r[5]
            }
            for r in rows
        ]

    @classmethod
    def delete_all_by_user(cls, id_usuario: int) -> int:
        """Elimina todos los registros de progreso de un usuario (para limpieza en pruebas)."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM progreso_diario WHERE id_usuario = %s;", (id_usuario,))
        count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        return count
