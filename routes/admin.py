from flask import Blueprint, jsonify
from database import get_db_connection

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/users', methods=['GET'])
def get_all_users():
    # Inisialisasi variabel koneksi di awal agar bisa dibaca di blok 'finally'
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # PERBAIKAN: Menambahkan kolom plaintext_password ke dalam SELECT query
        query = """
            SELECT 
                id, 
                username, 
                email, 
                password_hash, 
                password_hash_unsalted, 
                hashing_method, 
                role, 
                password_strength, 
                hashing_duration, 
                hash_size,
                password_salt,
                plaintext_password
            FROM users
        """
        
        cursor.execute(query)
        users = cursor.fetchall()
        
        return jsonify(users), 200

    except Exception as e:
        # Jika ada error pada query/database, Flask tidak akan crash/freeze
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        # PENGAMAN UTAMA: Apapun yang terjadi (sukses maupun error), 
        # koneksi database WAJIB ditutup agar Gunicorn tidak TIMEOUT/SIGKILL
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()