from config.database import get_db_connection

class UserModel:
    """Modelo de acceso a datos para la tabla oficial 'usuarios'."""

    @staticmethod
    def get_by_email(email: str):
        """Busca un usuario por su correo electrónico utilizando consulta parametrizada."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id_usuario, nombre, correo, contrasena, rol, fecha_registro 
            FROM usuarios 
            WHERE correo = %s;
            """,
            (email.strip().lower(),)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            return {
                "id_usuario": row[0],
                "nombre": row[1],
                "correo": row[2],
                "contrasena": row[3],
                "rol": row[4],
                "fecha_registro": row[5]
            }
        return None

    @staticmethod
    def get_by_id(user_id: int):
        """Busca un usuario por su clave primaria id_usuario."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id_usuario, nombre, correo, rol, fecha_registro 
            FROM usuarios 
            WHERE id_usuario = %s;
            """,
            (user_id,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row:
            return {
                "id_usuario": row[0],
                "nombre": row[1],
                "correo": row[2],
                "rol": row[3],
                "fecha_registro": row[4]
            }
        return None

    @staticmethod
    def create_user(nombre: str, correo: str, password_hash: str, rol: str = "estudiante") -> int:
        """
        Inserta un nuevo usuario en la base de datos con contraseña hasheada y rol.
        En registro público el rol siempre es forzado a 'estudiante'.
        """
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO usuarios (nombre, correo, contrasena, rol)
            VALUES (%s, %s, %s, %s)
            RETURNING id_usuario;
            """,
            (nombre.strip(), correo.strip().lower(), password_hash, rol)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return new_id

    @staticmethod
    def delete_user_by_email(correo: str) -> bool:
        """Elimina un usuario por correo para depuración y limpieza de datos de prueba."""
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM usuarios WHERE correo = %s;", (correo.strip().lower(),))
        deleted_count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        return deleted_count > 0
