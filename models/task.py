from config.database import get_db_connection

class TaskModel:
    """Modelo de acceso a datos para la tabla oficial 'tareas'."""

    PRIORIDADES = ("alta", "media", "baja")
    ESTADOS = ("pendiente", "en_progreso", "completada")

    @staticmethod
    def _row_to_dict(row):
        """Convierte una tupla de base de datos a un diccionario estructurado."""
        if not row:
            return None
        return {
            "id_tarea": row[0],
            "id_usuario": row[1],
            "nombre": row[2],
            "descripcion": row[3],
            "fecha_entrega": row[4],
            "prioridad": row[5],
            "estado": row[6],
            "fecha_creacion": row[7],
            "fecha_completada": row[8]
        }

    @classmethod
    def get_by_id(cls, id_tarea: int):
        """Obtiene una tarea por su id_tarea."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id_tarea, id_usuario, nombre, descripcion, fecha_entrega, 
                   prioridad, estado, fecha_creacion, fecha_completada
            FROM tareas
            WHERE id_tarea = %s;
            """,
            (id_tarea,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return cls._row_to_dict(row)

    @classmethod
    def get_all_by_user(cls, id_usuario: int):
        """Obtiene todas las tareas pertenecientes a un usuario ordenadas por fecha de entrega."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id_tarea, id_usuario, nombre, descripcion, fecha_entrega, 
                   prioridad, estado, fecha_creacion, fecha_completada
            FROM tareas
            WHERE id_usuario = %s
            ORDER BY fecha_entrega ASC, id_tarea DESC;
            """,
            (id_usuario,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [cls._row_to_dict(r) for r in rows]

    @classmethod
    def create(cls, id_usuario: int, nombre: str, descripcion: str, fecha_entrega, prioridad: str = "media", estado: str = "pendiente") -> int:
        """Crea una nueva tarea vinculada al id_usuario autenticado."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO tareas (id_usuario, nombre, descripcion, fecha_entrega, prioridad, estado)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id_tarea;
            """,
            (
                id_usuario,
                nombre.strip(),
                descripcion.strip() if descripcion else None,
                fecha_entrega,
                prioridad.strip().lower(),
                estado.strip().lower()
            )
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return new_id

    @classmethod
    def update(cls, id_tarea: int, id_usuario: int, nombre: str, descripcion: str, fecha_entrega, prioridad: str, estado: str) -> bool:
        """Actualiza una tarea existente asegurando que pertenezca al id_usuario autenticado."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE tareas
            SET nombre = %s,
                descripcion = %s,
                fecha_entrega = %s,
                prioridad = %s,
                estado = %s,
                fecha_completada = CASE 
                    WHEN %s = 'completada' THEN COALESCE(fecha_completada, CURRENT_TIMESTAMP)
                    ELSE NULL 
                END
            WHERE id_tarea = %s AND id_usuario = %s;
            """,
            (
                nombre.strip(),
                descripcion.strip() if descripcion else None,
                fecha_entrega,
                prioridad.strip().lower(),
                estado.strip().lower(),
                estado.strip().lower(),
                id_tarea,
                id_usuario
            )
        )
        updated = cur.rowcount > 0
        conn.commit()
        cur.close()
        conn.close()
        return updated

    @classmethod
    def mark_completed(cls, id_tarea: int, id_usuario: int) -> bool:
        """Marca una tarea como completada y registra la fecha de completado."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE tareas
            SET estado = 'completada',
                fecha_completada = CURRENT_TIMESTAMP
            WHERE id_tarea = %s AND id_usuario = %s;
            """,
            (id_tarea, id_usuario)
        )
        updated = cur.rowcount > 0
        conn.commit()
        cur.close()
        conn.close()
        return updated

    @classmethod
    def delete(cls, id_tarea: int, id_usuario: int) -> bool:
        """Elimina una tarea garantizando que pertenezca al id_usuario autenticado."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            DELETE FROM tareas
            WHERE id_tarea = %s AND id_usuario = %s;
            """,
            (id_tarea, id_usuario)
        )
        deleted = cur.rowcount > 0
        conn.commit()
        cur.close()
        conn.close()
        return deleted

    @classmethod
    def delete_all_by_user(cls, id_usuario: int) -> int:
        """Elimina todas las tareas de un usuario (utilizado en limpieza de pruebas)."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM tareas WHERE id_usuario = %s;", (id_usuario,))
        count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        return count
