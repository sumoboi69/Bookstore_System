import pymysql

timeout = 10
connection = pymysql.connect(
    charset="utf8mb4",
    connect_timeout=timeout,
    cursorclass=pymysql.cursors.DictCursor,
    db="defaultdb",
    host="mysql-31dd1793-project-database25.h.aivencloud.com",
    password="AVNS_wg7_VyxtLYcwYvv_q4m",
    read_timeout=timeout,
    port=24029,
    user="avnadmin",
    write_timeout=timeout,
)

try:
    cursor = connection.cursor()
finally:
    connection.close()