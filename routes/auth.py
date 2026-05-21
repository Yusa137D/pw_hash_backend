from flask import Blueprint, request, jsonify
import hashlib
import mysql.connector
import time
import secrets

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

    # 1. GENERATE SALT (8 Karakter acak di belakang password)
    salt = secrets.token_hex(4) 
    salted_password = password + salt

    # 2. HITUNG WAKTU PROSES HASHING
    start_time = time.perf_counter()
    
    if method == 'MD5':
        password_hash = hashlib.md5(salted_password.encode()).hexdigest()
    elif method == 'SHA-256':
        password_hash = hashlib.sha256(salted_password.encode()).hexdigest()
    else:
        return jsonify({"message": "Metode hashing tidak valid!"}), 400
        
    end_time = time.perf_counter()
    
    # Durasi dalam milidetik (ms) dengan 4 angka di belakang koma
    duration = (end_time - start_time) * 1000
    hashing_duration = f"{duration:.4f} ms"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """INSERT INTO users (username, email, password_hash, hashing_method, role, password_strength, hashing_duration, password_salt) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, (username, email, password_hash, method, role, strength, hashing_duration, salt))
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

    # Ambil salt yang dulu disimpan saat register
    salt = user['password_salt'] or ""
    salted_input = password + salt
    is_valid = False
    
    if user['hashing_method'] == 'MD5':
        input_hash = hashlib.md5(salted_input.encode()).hexdigest()
        is_valid = (input_hash == user['password_hash'])
    elif user['hashing_method'] == 'SHA-256':
        input_hash = hashlib.sha256(salted_input.encode()).hexdigest()
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