from config.database import get_db_connection

class StudySessionModel:
    """Modelo de acceso a datos para la tabla oficial 'sesiones_estudio'."""

    ESTADOS = ("planificada", "en_curso", "completada", "cancelada")

    @staticmethod
    def _row_to_dict(row):
        """Convierte una tupla de base de datos a un diccionario estructurado."""
        if not row:
            return None
        d = {
            "id_sesion": row[0],
            "id_usuario": row[1],
            "id_tarea": row[2],
            "duracion_minutos": row[3],
            "tiempo_pausa_minutos": row[4],
            "estado": row[5],
            "fecha_inicio": row[6],
            "fecha_fin": row[7],
            "notas": row[8]
        }
        if len(row) > 9:
            d["tarea_nombre"] = row[9]
        return d

    @classmethod
    def get_by_id(cls, id_sesion: int):
        """Obtiene una sesión de estudio por su id_sesion con nombre de tarea vinculada si existe."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT s.id_sesion, s.id_usuario, s.id_tarea, s.duracion_minutos,
                   s.tiempo_pausa_minutos, s.estado, s.fecha_inicio, s.fecha_fin,
                   s.notas, t.nombre as tarea_nombre
            FROM sesiones_estudio s
            LEFT JOIN tareas t ON s.id_tarea = t.id_tarea
            WHERE s.id_sesion = %s;
            """,
            (id_sesion,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return cls._row_to_dict(row)

    @classmethod
    def get_all_by_user(cls, id_usuario: int):
        """Obtiene todas las sesiones de estudio de un usuario ordenadas por fecha de inicio descendente."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT s.id_sesion, s.id_usuario, s.id_tarea, s.duracion_minutos,
                   s.tiempo_pausa_minutos, s.estado, s.fecha_inicio, s.fecha_fin,
                   s.notas, t.nombre as tarea_nombre
            FROM sesiones_estudio s
            LEFT JOIN tareas t ON s.id_tarea = t.id_tarea
            WHERE s.id_usuario = %s
            ORDER BY s.fecha_inicio DESC, s.id_sesion DESC;
            """,
            (id_usuario,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [cls._row_to_dict(r) for r in rows]

    @classmethod
    def create(cls, id_usuario: int, duracion_minutos: int, tiempo_pausa_minutos: int = 5, estado: str = "completada", id_tarea: int = None, fecha_inicio=None, fecha_fin=None, notas: str = None) -> int:
        """Crea una sesión de estudio vinculada obligatoriamente al id_usuario de la sesión."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO sesiones_estudio (
                id_usuario, id_tarea, duracion_minutos, tiempo_pausa_minutos, 
                estado, fecha_inicio, fecha_fin, notas
            )
            VALUES (
                %s, %s, %s, %s, 
                %s, COALESCE(%s, CURRENT_TIMESTAMP), %s, %s
            )
            RETURNING id_sesion;
            """,
            (
                id_usuario,
                id_tarea if id_tarea else None,
                duracion_minutos,
                tiempo_pausa_minutos,
                estado.strip().lower(),
                fecha_inicio if fecha_inicio else None,
                fecha_fin if fecha_fin else None,
                notas.strip() if notas else None
            )
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return new_id

    @classmethod
    def finish_session(cls, id_sesion: int, id_usuario: int, notas: str = None) -> bool:
        """Finaliza una sesión en curso o planificada, marcándola como 'completada' y registrando fecha_fin."""
        conn = get_db_connection()
        cur = conn.cursor()
        if notas:
            cur.execute(
                """
                UPDATE sesiones_estudio
                SET estado = 'completada',
                    fecha_fin = CURRENT_TIMESTAMP,
                    notas = COALESCE(notas || E'\n' || %s, %s)
                WHERE id_sesion = %s AND id_usuario = %s;
                """,
                (notas.strip(), notas.strip(), id_sesion, id_usuario)
            )
        else:
            cur.execute(
                """
                UPDATE sesiones_estudio
                SET estado = 'completada',
                    fecha_fin = CURRENT_TIMESTAMP
                WHERE id_sesion = %s AND id_usuario = %s;
                """,
                (id_sesion, id_usuario)
            )
        updated = cur.rowcount > 0
        conn.commit()
        cur.close()
        conn.close()
        return updated

    @classmethod
    def update(cls, id_sesion: int, id_usuario: int, duracion_minutos: int, tiempo_pausa_minutos: int, estado: str, notas: str = None, id_tarea: int = None) -> bool:
        """Actualiza los datos de una sesión garantizando que pertenezca al usuario autenticado."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE sesiones_estudio
            SET duracion_minutos = %s,
                tiempo_pausa_minutos = %s,
                estado = %s,
                notas = %s,
                id_tarea = %s
            WHERE id_sesion = %s AND id_usuario = %s;
            """,
            (
                duracion_minutos,
                tiempo_pausa_minutos,
                estado.strip().lower(),
                notas.strip() if notas else None,
                id_tarea if id_tarea else None,
                id_sesion,
                id_usuario
            )
        )
        updated = cur.rowcount > 0
        conn.commit()
        cur.close()
        conn.close()
        return updated

    @classmethod
    def delete(cls, id_sesion: int, id_usuario: int) -> bool:
        """Elimina una sesión garantizando que pertenezca al usuario autenticado."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM sesiones_estudio
            WHERE id_sesion = %s AND id_usuario = %s;
            """,
            (id_sesion, id_usuario)
        )
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        conn.close()
        return deleted

    @classmethod
    def delete_all_by_user(cls, id_usuario: int) -> int:
        """Elimina todas las sesiones de un usuario (para limpieza en pruebas)."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM sesiones_estudio WHERE id_usuario = %s;", (id_usuario,))
        count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        return count
