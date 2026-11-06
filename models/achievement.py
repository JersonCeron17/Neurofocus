from config.database import get_db_connection

class AchievementModel:
    """Modelo de acceso a datos para las tablas oficiales 'logros' y 'logros_usuario'."""

    @classmethod
    def ensure_default_achievements(cls):
        """Puebla logros estándar del catálogo si no existen."""
        conn = get_db_connection()
        cur = conn.cursor()
        logros_semilla = [
            ("Primer Paso", "Completa tu primera tarea de estudio en NeuroFocus.", "check-circle", "primera_tarea"),
            ("Mente Enfocada", "Completa tu primera sesión de estudio de concentración.", "clock", "primera_sesion"),
            ("Gimnasia Cerebral", "Completa tu primer ejercicio cognitivo.", "brain", "primer_ejercicio"),
            ("Constancia Diaria", "Registra actividad o progreso en tu jornada de estudio.", "award", "progreso_diario")
        ]
        for nombre, desc, icono, clave in logros_semilla:
            cur.execute(
                """
                INSERT INTO logros (nombre, descripcion, icono, condicion_clave)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (nombre) DO NOTHING;
                """,
                (nombre, desc, icono, clave)
            )
        conn.commit()
        cur.close()
        conn.close()

    @classmethod
    def get_all(cls):
        """Retorna todos los logros disponibles en el catálogo general."""
        cls.ensure_default_achievements()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id_logro, nombre, descripcion, icono, condicion_clave
            FROM logros
            ORDER BY id_logro ASC;
            """
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [
            {
                "id_logro": r[0],
                "nombre": r[1],
                "descripcion": r[2],
                "icono": r[3],
                "condicion_clave": r[4]
            }
            for r in rows
        ]

    @classmethod
    def get_user_achievements(cls, id_usuario: int):
        """
        Retorna la lista de todos los logros disponibles indicando si el usuario
        los tiene desbloqueados y la fecha en que los obtuvo.
        """
        cls.ensure_default_achievements()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT l.id_logro, l.nombre, l.descripcion, l.icono, l.condicion_clave,
                   lu.fecha_obtenido,
                   CASE WHEN lu.id_usuario IS NOT NULL THEN TRUE ELSE FALSE END as desbloqueado
            FROM logros l
            LEFT JOIN logros_usuario lu ON l.id_logro = lu.id_logro AND lu.id_usuario = %s
            ORDER BY l.id_logro ASC;
            """,
            (id_usuario,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [
            {
                "id_logro": r[0],
                "nombre": r[1],
                "descripcion": r[2],
                "icono": r[3],
                "condicion_clave": r[4],
                "fecha_obtenido": r[5],
                "desbloqueado": r[6]
            }
            for r in rows
        ]

    @classmethod
    def unlock(cls, id_usuario: int, condicion_clave: str) -> bool:
        """Desbloquea un logro para el usuario a partir de su condición clave."""
        cls.ensure_default_achievements()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id_logro FROM logros WHERE condicion_clave = %s;", (condicion_clave,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return False

        id_logro = row[0]
        cur.execute(
            """
            INSERT INTO logros_usuario (id_usuario, id_logro)
            VALUES (%s, %s)
            ON CONFLICT (id_usuario, id_logro) DO NOTHING;
            """,
            (id_usuario, id_logro)
        )
        unlocked = cur.rowcount > 0
        conn.commit()
        cur.close()
        conn.close()
        return unlocked

    @classmethod
    def delete_all_by_user(cls, id_usuario: int) -> int:
        """Elimina las asignaciones de logros de un usuario (para limpieza en pruebas)."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM logros_usuario WHERE id_usuario = %s;", (id_usuario,))
        count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        return count
