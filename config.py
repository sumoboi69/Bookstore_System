"""
Configuration for Flask application
"""
import secrets

sql_uri = "mysql://avnadmin:AVNS_wg7_VyxtLYcwYvv_q4m@mysql-31dd1793-project-database25.h.aivencloud.com:24029/defaultdb?ssl-mode=REQUIRED"

class Config:
    SECRET_KEY = secrets.token_hex(16)  # Generate a random secret key for sessions
    SQLALCHEMY_DATABASE_URI = sql_uri  # Kept for compatibility but not using SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
