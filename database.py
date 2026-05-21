import os
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        # os.environ.get akan membaca variabel dari Railway, 
        # jika tidak ada (di laptop), dia akan memakai nilai default sebelah kanan
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "db_keamanan_password")
    )