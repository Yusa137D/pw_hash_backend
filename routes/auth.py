from flask import Blueprint, request, jsonify
import hashlib
import mysql.connector

# Import dari file lain
from database import get_db_connection
from utils import get_strength_label

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    method = data.get('method')

    if not username or not email or not password or not method:
        return jsonify({"message": "Semua field harus diisi!"}), 400

    strength = get_strength_label(password)
    role = 'admin' if username.lower() == 'admin' else 'user'

    # --- PERUBAHAN DI SINI (MD5 vs SHA-256) ---
    if method == 'MD5':
        password_hash = hashlib.md5(password.encode()).hexdigest()
    elif method == 'SHA-256':
        password_hash = hashlib.sha256(password.encode()).hexdigest()
    else:
        return jsonify({"message": "Metode hashing tidak valid!"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """INSERT INTO users (username, email, password_hash, hashing_method, role, password_strength) 
                   VALUES (%s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, (username, email, password_hash, method, role, strength))
        conn.commit()
        return jsonify({"message": "Registrasi berhasil!"}), 201
    except mysql.connector.IntegrityError:
        return jsonify({"message": "Username atau Email sudah terdaftar!"}), 400
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return jsonify({"message": "Email tidak ditemukan!"}), 404

    is_valid = False
    
    # --- PERUBAHAN DI SINI (Proses Verifikasi) ---
    if user['hashing_method'] == 'MD5':
        input_hash = hashlib.md5(password.encode()).hexdigest()
        is_valid = (input_hash == user['password_hash'])
    elif user['hashing_method'] == 'SHA-256':
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        is_valid = (input_hash == user['password_hash'])

    if is_valid:
        return jsonify({
            "message": f"Selamat datang, {user['username']}",
            "method": user['hashing_method'],
            "role": user['role'],
            "username": user['username'],
            "strength": user['password_strength']
        }), 200
    else:
        return jsonify({"message": "Password salah!"}), 401