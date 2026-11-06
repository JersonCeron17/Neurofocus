from config.database import get_db_connection

class ActivityModel:
    """Modelo de acceso a datos para la tabla oficial 'actividades_calendario'."""

    TIPOS = ("estudio", "entrega", "recordatorio", "otro")

    @staticmethod
    def _row_to_dict(row):
        """Convierte una tupla de base de datos a un diccionario estructurado."""
        if not row:
            return None
        d = {
            "id_actividad": row[0],
            "id_usuario": row[1],
            "id_tarea": row[2],
            "titulo": row[3],
            "descripcion": row[4],
            "fecha_inicio": row[5],
            "fecha_fin": row[6],
            "tipo": row[7],
            "fecha_creacion": row[8]
        }
        if len(row) > 9:
            d["tarea_nombre"] = row[9]
        return d

    @classmethod
    def get_by_id(cls, id_actividad: int):
        """Obtiene una actividad por su id_actividad con el nombre de tarea vinculada si existe."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT a.id_actividad, a.id_usuario, a.id_tarea, a.titulo, a.descripcion,
                   a.fecha_inicio, a.fecha_fin, a.tipo, a.fecha_creacion, t.nombre as tarea_nombre
            FROM actividades_calendario a
            LEFT JOIN tareas t ON a.id_tarea = t.id_tarea
            WHERE a.id_actividad = %s;
            """,
            (id_actividad,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return cls._row_to_dict(row)

    @classmethod
    def get_all_by_user(cls, id_usuario: int):
        """Obtiene todas las actividades de un usuario ordenadas por fecha de inicio."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT a.id_actividad, a.id_usuario, a.id_tarea, a.titulo, a.descripcion,
                   a.fecha_inicio, a.fecha_fin, a.tipo, a.fecha_creacion, t.nombre as tarea_nombre
            FROM actividades_calendario a
            LEFT JOIN tareas t ON a.id_tarea = t.id_tarea
            WHERE a.id_usuario = %s
            ORDER BY a.fecha_inicio ASC, a.id_actividad DESC;
            """,
            (id_usuario,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [cls._row_to_dict(r) for r in rows]

    @classmethod
    def create(cls, id_usuario: int, titulo: str, fecha_inicio, fecha_fin=None, tipo: str = "estudio", descripcion: str = None, id_tarea: int = None) -> int:
        """Crea una nueva actividad asociada obligatoriamente al id_usuario autenticado."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO actividades_calendario (id_usuario, id_tarea, titulo, descripcion, fecha_inicio, fecha_fin, tipo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id_actividad;
            """,
            (
                id_usuario,
                id_tarea if id_tarea else None,
                titulo.strip(),
                descripcion.strip() if descripcion else None,
                fecha_inicio,
                fecha_fin if fecha_fin else None,
                tipo.strip().lower()
            )
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return new_id

    @classmethod
    def update(cls, id_actividad: int, id_usuario: int, titulo: str, fecha_inicio, fecha_fin=None, tipo: str = "estudio", descripcion: str = None, id_tarea: int = None) -> bool:
        """Actualiza una actividad garantizando la propiedad del usuario autenticado."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE actividades_calendario
            SET id_tarea = %s,
                titulo = %s,
                descripcion = %s,
                fecha_inicio = %s,
                fecha_fin = %s,
                tipo = %s
            WHERE id_actividad = %s AND id_usuario = %s;
            """,
            (
                id_tarea if id_tarea else None,
                titulo.strip(),
                descripcion.strip() if descripcion else None,
                fecha_inicio,
                fecha_fin if fecha_fin else None,
                tipo.strip().lower(),
                id_actividad,
                id_usuario
            )
        )
        updated = cur.rowcount > 0
        conn.commit()
        cur.close()
        conn.close()
        return updated

    @classmethod
    def delete(cls, id_actividad: int, id_usuario: int) -> bool:
        """Elimina una actividad garantizando la propiedad del usuario autenticado."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM actividades_calendario
            WHERE id_actividad = %s AND id_usuario = %s;
            """,
            (id_actividad, id_usuario)
        )
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        conn.close()
        return deleted

    @classmethod
    def delete_all_by_user(cls, id_usuario: int) -> int:
        """Elimina todas las actividades de un usuario (para limpieza en pruebas)."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM actividades_calendario WHERE id_usuario = %s;", (id_usuario,))
        count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        return count
