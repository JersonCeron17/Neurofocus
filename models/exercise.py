from config.database import get_db_connection

class ExerciseModel:
    """Modelo de acceso a datos para la tabla oficial 'ejercicios'."""

    CATEGORIAS = ("atencion", "memoria", "concentracion")
    DIFICULTADES = ("facil", "medio", "dificil")

    @classmethod
    def ensure_default_exercises(cls):
        """Puebla ejercicios estándar si la tabla está vacía, respetando las restricciones de PostgreSQL."""
        conn = get_db_connection()
        cur = conn.cursor()
        ejercicios_semilla = [
            ("Prueba de Stroop - Enfoque", "Identifica rápidamente el color del texto ignorando el significado de la palabra para entrenar la inhibición cognitiva.", "atencion", "medio"),
            ("Secuencia Numérica Inversa", "Memoriza y reproduce una secuencia de números en orden inverso para mejorar la memoria de trabajo.", "memoria", "facil"),
            ("Seguimiento de Patrones", "Sigue una serie de patrones geométricos sin perder el foco en el objetivo.", "concentracion", "dificil")
        ]
        for titulo, desc, cat, dif in ejercicios_semilla:
            cur.execute(
                """
                INSERT INTO ejercicios (titulo, descripcion, categoria, dificultad)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (titulo) DO NOTHING;
                """,
                (titulo, desc, cat, dif)
            )
        conn.commit()
        cur.close()
        conn.close()

    @classmethod
    def get_all(cls):
        """Retorna todos los ejercicios disponibles."""
        cls.ensure_default_exercises()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id_ejercicio, titulo, descripcion, categoria, dificultad
            FROM ejercicios
            ORDER BY id_ejercicio ASC;
            """
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [
            {
                "id_ejercicio": r[0],
                "titulo": r[1],
                "descripcion": r[2],
                "categoria": r[3],
                "dificultad": r[4]
            }
            for r in rows
        ]

    @classmethod
    def get_by_id(cls, id_ejercicio: int):
        """Retorna un ejercicio específico por su id_ejercicio."""
        cls.ensure_default_exercises()
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id_ejercicio, titulo, descripcion, categoria, dificultad
            FROM ejercicios
            WHERE id_ejercicio = %s;
            """,
            (id_ejercicio,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return {
                "id_ejercicio": row[0],
                "titulo": row[1],
                "descripcion": row[2],
                "categoria": row[3],
                "dificultad": row[4]
            }
        return None

class ExerciseResultModel:
    """Modelo de acceso a datos para la tabla oficial 'resultados_ejercicios'."""

    @classmethod
    def create(cls, id_usuario: int, id_ejercicio: int, puntuacion: int, tiempo_segundos: int = None) -> int:
        """Registra un resultado asociado al usuario autenticado."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO resultados_ejercicios (id_usuario, id_ejercicio, puntuacion, tiempo_segundos)
            VALUES (%s, %s, %s, %s)
            RETURNING id_resultado;
            """,
            (id_usuario, id_ejercicio, puntuacion, tiempo_segundos)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return new_id

    @classmethod
    def get_all_by_user(cls, id_usuario: int):
        """Obtiene todos los resultados del usuario autenticado con información del ejercicio."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT r.id_resultado, r.id_usuario, r.id_ejercicio, r.puntuacion,
                   r.tiempo_segundos, r.fecha_realizacion, e.titulo as ejercicio_titulo,
                   e.categoria, e.dificultad
            FROM resultados_ejercicios r
            JOIN ejercicios e ON r.id_ejercicio = e.id_ejercicio
            WHERE r.id_usuario = %s
            ORDER BY r.fecha_realizacion DESC, r.id_resultado DESC;
            """,
            (id_usuario,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [
            {
                "id_resultado": r[0],
                "id_usuario": r[1],
                "id_ejercicio": r[2],
                "puntuacion": r[3],
                "tiempo_segundos": r[4],
                "fecha_realizacion": r[5],
                "ejercicio_titulo": r[6],
                "categoria": r[7],
                "dificultad": r[8]
            }
            for r in rows
        ]

    @classmethod
    def get_by_id(cls, id_resultado: int):
        """Obtiene un resultado por su id_resultado."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT r.id_resultado, r.id_usuario, r.id_ejercicio, r.puntuacion,
                   r.tiempo_segundos, r.fecha_realizacion, e.titulo as ejercicio_titulo,
                   e.categoria, e.dificultad
            FROM resultados_ejercicios r
            JOIN ejercicios e ON r.id_ejercicio = e.id_ejercicio
            WHERE r.id_resultado = %s;
            """,
            (id_resultado,)
        )
        r = cur.fetchone()
        cur.close()
        conn.close()
        if r:
            return {
                "id_resultado": r[0],
                "id_usuario": r[1],
                "id_ejercicio": r[2],
                "puntuacion": r[3],
                "tiempo_segundos": r[4],
                "fecha_realizacion": r[5],
                "ejercicio_titulo": r[6],
                "categoria": r[7],
                "dificultad": r[8]
            }
        return None

    @classmethod
    def delete_all_by_user(cls, id_usuario: int) -> int:
        """Elimina todos los resultados de un usuario (para limpieza en pruebas)."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM resultados_ejercicios WHERE id_usuario = %s;", (id_usuario,))
        count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        return count
