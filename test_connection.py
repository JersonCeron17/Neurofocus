from config.database import get_db_connection

def test_db_connection():
    """Ejecuta consultas de solo lectura para verificar la base de datos y sus tablas oficiales."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Consulta de solo lectura para verificar la base de datos conectada
        cursor.execute("SELECT current_database();")
        result = cursor.fetchone()
        current_db = result[0] if result else None

        if current_db != "neurofocus":
            print(f"ADVERTENCIA: Conectado a '{current_db}', pero se esperaba 'neurofocus'")
            cursor.close()
            conn.close()
            return False

        print(f"EXITO: Conexión establecida correctamente con la base de datos: {current_db}")

        # 2. Consulta de solo lectura para verificar las 9 tablas oficiales
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        found_tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        expected_tables = [
            "actividades_calendario",
            "ejercicios",
            "logros",
            "logros_usuario",
            "progreso_diario",
            "resultados_ejercicios",
            "sesiones_estudio",
            "tareas",
            "usuarios"
        ]

        missing = [t for t in expected_tables if t not in found_tables]
        if missing:
            print(f"ERROR: Faltan las siguientes tablas: {missing}")
            return False

        print(f"EXITO: Se confirmaron las 9 tablas oficiales presentes: {found_tables}")
        return True

    except Exception as e:
        print(f"ERROR al conectar a PostgreSQL: {e}")
        return False

if __name__ == "__main__":
    test_db_connection()
