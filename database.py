"""
Database connection and utility functions
"""
import pymysql
from contextlib import contextmanager

# Database configuration
DB_CONFIG = {
    "charset": "utf8mb4",
    "connect_timeout": 10,
    "cursorclass": pymysql.cursors.DictCursor,
    "db": "defaultdb",
    "host": "mysql-31dd1793-project-database25.h.aivencloud.com",
    "password": "AVNS_wg7_VyxtLYcwYvv_q4m",
    "read_timeout": 10,
    "port": 24029,
    "user": "avnadmin",
    "write_timeout": 10,
}


def get_db_connection():
    """Create and return a database connection"""
    return pymysql.connect(**DB_CONFIG)


@contextmanager
def get_db_cursor(commit=False):
    """
    Context manager for database operations
    Usage:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("INSERT ...")
    """
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


def execute_query(query, params=None, fetch_one=False, fetch_all=True, commit=False):
    """
    Execute a query and return results

    Args:
        query: SQL query string
        params: Query parameters (tuple or dict)
        fetch_one: If True, return single row
        fetch_all: If True, return all rows
        commit: If True, commit the transaction

    Returns:
        Query results or None
    """
    with get_db_cursor(commit=commit) as cursor:
        cursor.execute(query, params or ())

        if fetch_one:
            return cursor.fetchone()
        elif fetch_all:
            return cursor.fetchall()
        else:
            return None

