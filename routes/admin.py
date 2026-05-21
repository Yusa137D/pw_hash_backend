from flask import Blueprint, jsonify
from database import get_db_connection

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/users', methods=['GET'])
def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Menarik seluruh data termasuk salt dan waktu proses untuk dashboard
    cursor.execute("SELECT id, username, email, password_hash, hashing_method, role, password_strength, hashing_duration, password_salt FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users), 200