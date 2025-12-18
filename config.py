sql_uri = "mysql://avnadmin:AVNS_wg7_VyxtLYcwYvv_q4m@mysql-31dd1793-project-database25.h.aivencloud.com:24029/defaultdb?ssl-mode=REQUIRED"

class Config:
    SECRET_KEY = "dev-secret-key"
    SQLALCHEMY_DATABASE_URI = (
        sql_uri
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
