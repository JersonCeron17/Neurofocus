import sys
import os

# Asegurar que la raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import get_db_connection

def inspect_table(table_name):
    """Inspecciona la estructura de una tabla en modo de solo lectura."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Columnas
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position;
    """, (table_name,))
    columns = cur.fetchall()
    
    # Restricciones detalladas (incluyendo CHECK si existen)
    cur.execute("""
        SELECT conname, contype, pg_get_constraintdef(oid)
        FROM pg_constraint
        WHERE conrelid = %s::regclass;
    """, (table_name,))
    constraints = cur.fetchall()
    
    cur.close()
    conn.close()
    
    print(f"=== ESTRUCTURA DE LA TABLA '{table_name}' ===")
    print("Columnas:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]} (max_len: {col[2]}, nullable: {col[3]}, default: {col[4]})")
    print("\nRestricciones:")
    for con in constraints:
        print(f"  - {con[0]} (Tipo: {con[1]}, Definición: {con[2]})")

if __name__ == "__main__":
    inspect_table("usuarios")
