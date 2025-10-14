import myssql.connector
from myssql.connector import Error
from contextlib import contextmanager
from typing import Generator
from app.core.config import settings

class Database:
    """Classe para gerenciar a conexão com o banco de dados MySQL."""

    @staticmethod
    def get_connection():
        """Cria uma nova conexão com o banco de dados"""
        try:
            connection = mysql.connector.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            
            if connection.is_connected():
                return connection
            
        except Error as e:
            print(f"Erro ao conectar ao MySQL: {e}")
            raise
    @staticmethod
    @contextmanager
    def get_cursor(dictionary=True):
        """
        Context manager para obter cursor
        Usage:
            with Database.get_cursor() as cursor:
                cursor.execute("SELECT * FROM users")
                results = cursor.fetchall()
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            cursor = connection.cursor(dictionary=dictionary)
            yield cursor
            connection.commit()
        except Error as e:
            if connection:
                connection.rollback()
            print(f"Erro no banco de dados: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

# Dependency para FastAPI
def get_db() -> Generator:
    """
    Dependency do FastAPI para injeção de cursor
    Usage nos endpoints:
        @router.get("/users")
        def get_users(cursor = Depends(get_db)):
            cursor.execute("SELECT * FROM users")
            return cursor.fetchall()
    """
    with Database.get_cursor() as cursor:
        yield cursor