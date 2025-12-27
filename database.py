import pymysql
from contextlib import contextmanager

# Database configuration for XAMPP (Local MySQL)
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '',  # Default XAMPP has no password
    'database': 'bookstore_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        return pymysql.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Database connection error: {e}")
        raise


@contextmanager
def get_db_cursor(commit=False):
    """Context manager for database cursor"""
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        yield cursor
        if commit:
            connection.commit()
    except Exception as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()


def execute_query(query, params=None, fetch_one=False, commit=False):
    """
    Execute a SQL query with parameters
    
    Args:
        query: SQL query string
        params: Query parameters (tuple or dict)
        fetch_one: If True, return single row, else return all rows
        commit: If True, commit the transaction
    
    Returns:
        Query results or None
    """
    try:
        with get_db_cursor(commit=commit) as cursor:
            cursor.execute(query, params)
            
            if fetch_one:
                return cursor.fetchone()
            else:
                # For SELECT queries
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                return None
    except Exception as e:
        print(f"Query execution error: {e}")
        raise
