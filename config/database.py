import psycopg2
from config.settings import Config

def get_db_connection():
    """
    Establece y retorna una nueva conexión con la base de datos PostgreSQL
    utilizando los parámetros de configuración centralizados.
    """
    params = Config.get_db_connection_params()
    return psycopg2.connect(**params)
