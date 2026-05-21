from flask import Blueprint, jsonify
from database import get_db_connection

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/users', methods=['GET'])
def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Mengambil seluruh kolom analisis termasuk kolum hash tanpa salt (unsalted)
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
            password_salt 
        FROM users
    """
    
    cursor.execute(query)
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(users), 200