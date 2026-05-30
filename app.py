from flask import Flask
from flask_cors import CORS
import os
import random
import string
import hashlib
import zipfile

# Import Blueprint dari folder routes
from routes.auth import auth_bp
from routes.admin import admin_bp

from flask import send_file
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    PageBreak,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.pagesizes import letter

import io
from datetime import datetime
from database import get_db_connection

app = Flask(__name__)

# 1. Daftarkan semua Blueprint terlebih dahulu
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

# 2. AKTIFKAN CORS
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}})

# ==========================================
# ROUTE RAHASIA UNTUK INJEKSI 100 DATA DUMMY
# ==========================================
@app.route('/seed-rahasia-100-akun', methods=['GET'])
def seed_dummy_data():
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        
        weak_pool = ['admin123', 'password', 'qwerty', '123456', 'yusaganteng']
        fair_pool = ['KucingTerbang12', 'MadiunKota2026', 'BukuBiru99', 'KopiPanas123']
        strong_pool = ['Kopi.Pahit.Laptop.Menyala!', 'Xy7!pQ9$mL4%kR2@wN8#', 'Keamanan.Skripsi.Yusa.2026!']

        def generate_random_string(length=4):
            return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

        for i in range(1, 101):
            if i <= 40:
                raw_password = random.choice(weak_pool)
                strength_label = "Weak"
            elif i <= 80:
                raw_password = random.choice(fair_pool)
                strength_label = "Fair"
            else:
                raw_password = random.choice(strong_pool)
                strength_label = "Very Strong" if "!" in raw_password else "Strong"

            username = f"dummy_{i}_{generate_random_string()}"
            email = f"{username}@dummy.com"
            hashing_method = random.choice(['MD5', 'SHA-256'])
            
            salt_hex = os.urandom(8).hex()

            if hashing_method == 'MD5':
                hash_unsalted = hashlib.md5(raw_password.encode()).hexdigest()
                hash_salted = hashlib.md5((raw_password + salt_hex).encode()).hexdigest()
                hash_size = 32
                duration = f"0.0{random.randint(10, 99)} ms"
            else:
                hash_unsalted = hashlib.sha256(raw_password.encode()).hexdigest()
                hash_salted = hashlib.sha256((raw_password + salt_hex).encode()).hexdigest()
                hash_size = 64
                duration = f"{random.uniform(1.1, 2.5):.4f} ms"

            # PERBAIKAN: Menambahkan kolom plaintext_password ke dalam query
            query = """
                INSERT INTO users 
                (username, email, password_hash, password_hash_unsalted, hashing_method, role, password_strength, hashing_duration, password_salt, hash_size, plaintext_password) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (username, email, hash_salted, hash_unsalted, hashing_method, 'user', strength_label, duration, salt_hex, hash_size, raw_password)
            cursor.execute(query, values)

        conn.commit()
        return "SUKSES BIKIN 100 AKUN BESERTA PLAINTEXT! Cek UI Flutter-mu sekarang.", 200

    except Exception as e:
        return f"Terjadi kesalahan: {str(e)}", 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn.is_connected():
            conn.close()

# ==========================================
# ROUTE EXPORT DATASET UNTUK HASHCAT (ZIP)
# ==========================================
@app.route('/export-hashcat')
def export_hashcat():
    conn = get_db_connection()
    users = []
    
    try:
        cursor = conn.cursor(dictionary=True)
        # PERBAIKAN: Jangan lupa panggil juga kolom plaintext_password di SELECT
        cursor.execute("""
            SELECT hashing_method, 
                   password_hash, 
                   password_hash_unsalted, 
                   password_salt,
                   plaintext_password 
            FROM users 
            WHERE plaintext_password IS NOT NULL
        """)
        users = cursor.fetchall()
    finally:
        if 'cursor' in locals(): cursor.close()
        if conn.is_connected(): conn.close()

    md5_nosalt = []
    md5_salt = []
    sha256_nosalt = []
    sha256_salt = []
    
    # Wadah baru untuk wordlist (Menggunakan 'set' agar password tidak duplikat)
    plaintexts = set() 

    for u in users:
        method = u['hashing_method']
        hash_murni = str(u['password_hash_unsalted'])
        hash_dengan_salt = f"{u['password_hash']}:{u['password_salt']}"
        
        # Masukkan password asli ke dalam set wordlist
        if u['plaintext_password']:
            plaintexts.add(str(u['plaintext_password']))

        if method == 'MD5':
            md5_nosalt.append(hash_murni)
            md5_salt.append(hash_dengan_salt)
        elif method == 'SHA-256':
            sha256_nosalt.append(hash_murni)
            sha256_salt.append(hash_dengan_salt)

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('hashes_md5_nosalt.txt', '\n'.join(md5_nosalt))
        zf.writestr('hashes_md5_salt.txt', '\n'.join(md5_salt))
        zf.writestr('hashes_sha256_nosalt.txt', '\n'.join(sha256_nosalt))
        zf.writestr('hashes_sha256_salt.txt', '\n'.join(sha256_salt))
        
        # Tambahkan file ke-5: Kamus Wordlist (Plaintext)
        zf.writestr('kamus_wordlist.txt', '\n'.join(plaintexts))

    memory_file.seek(0)

    return send_file(
        memory_file,
        as_attachment=True,
        download_name='dataset_hashcat_skripsi.zip',
        mimetype='application/zip'
    )

# ==========================================
# ROUTE EXPORT PDF
# ==========================================
@app.route('/export-pdf')
def export_pdf():
    conn = get_db_connection()
    users = []
    
    try:
        cursor = conn.cursor(dictionary=True)
        # PERBAIKAN: Memanggil kolom plaintext_password
        cursor.execute("""
            SELECT username,
                   plaintext_password,
                   hashing_method,
                   password_strength,
                   password_hash,
                   password_hash_unsalted 
            FROM users
        """)
        users = cursor.fetchall()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if conn.is_connected():
            conn.close()

    total_users = len(users)
    md5_count = len([u for u in users if u['hashing_method'] == 'MD5'])
    sha_count = len([u for u in users if u['hashing_method'] == 'SHA-256'])

    strength_stats = {
        'Very Strong': 0, 'Strong': 0, 'Fair': 0, 'Weak': 0, 'Very Weak': 0
    }

    for u in users:
        strength = u['password_strength']
        if strength in strength_stats:
            strength_stats[strength] += 1

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=25, leftMargin=25, topMargin=20, bottomMargin=20
    )

    styles = getSampleStyleSheet()
    NAVY = HexColor('#0F172A')
    WHITE = HexColor('#FFFFFF')
    BORDER = HexColor('#CBD5E1')

    title_style = ParagraphStyle(
        'ReportTitle', parent=styles['Title'], fontName='Helvetica-Bold',
        fontSize=14, leading=18, textColor=NAVY, alignment=TA_CENTER
    )

    section_title_style = ParagraphStyle(
        'SectionTitle', parent=styles['Heading2'], fontName='Helvetica-Bold',
        fontSize=13, leading=16, textColor=NAVY, alignment=TA_LEFT, spaceAfter=8
    )

    body_style = ParagraphStyle(
        'ReportBody', parent=styles['BodyText'], fontName='Helvetica',
        fontSize=9, leading=12, textColor=NAVY
    )

    normal_style = ParagraphStyle(
        'TableNormal', parent=body_style, fontName='Helvetica',
        fontSize=8, leading=10, textColor=NAVY, alignment=TA_CENTER
    )

    header_style = ParagraphStyle(
        'TableHeader', parent=normal_style, fontName='Helvetica-Bold',
        textColor=WHITE, alignment=TA_CENTER
    )

    hash_style = ParagraphStyle(
        'HashWrap', parent=normal_style, alignment=TA_LEFT, wordWrap='CJK'
    )

    def apply_navy_table_style(table):
        table.hAlign = 'CENTER'
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BACKGROUND', (0, 1), (-1, -1), WHITE),
            ('TEXTCOLOR', (0, 1), (-1, -1), NAVY),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, BORDER),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('LINEBELOW', (0, 0), (-1, 0), 2, BORDER),
        ]))

    elements = []

    title = Paragraph("<b>Laporan Keamanan Password (Sistem Analisis)</b>", title_style)
    elements.append(title)
    elements.append(Spacer(1, 10))

    info = Paragraph(f"<b>Tanggal Cetak :</b> {datetime.now().strftime('%d %B %Y %H:%M:%S')}<br/><b>Jumlah Total Entri :</b> {total_users}", body_style)
    elements.append(info)
    elements.append(Spacer(1, 18))

    summary_title = Paragraph("<b>Ringkasan Statistik Kontrol Kriptografi</b>", section_title_style)
    elements.append(summary_title)

    summary_data = [
        ['Kategori', 'Jumlah'],
        ['Total Entri Akun', str(total_users)],
        ['Penggunaan Algoritma MD5', str(md5_count)],
        ['Penggunaan Algoritma SHA-256', str(sha_count)],
    ]
    summary_table = Table(summary_data, colWidths=[260, 100])
    apply_navy_table_style(summary_table)
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    algo_title = Paragraph("<b>Distribusi Algoritma Hashing</b>", section_title_style)
    elements.append(algo_title)

    algo_data = [
        ['Algoritma', 'Jumlah Pengguna'],
        ['MD5', str(md5_count)],
        ['SHA-256', str(sha_count)],
    ]
    algo_table = Table(algo_data, colWidths=[180, 180])
    apply_navy_table_style(algo_table)
    elements.append(algo_table)
    elements.append(Spacer(1, 18))

    strength_title = Paragraph("<b>Distribusi Kekuatan Password (zxcvbn)</b>", section_title_style)
    elements.append(strength_title)

    strength_data = [
        ['Kekuatan', 'Jumlah Pengguna'],
        ['Very Strong', str(strength_stats['Very Strong'])],
        ['Strong', str(strength_stats['Strong'])],
        ['Fair', str(strength_stats['Fair'])],
        ['Weak', str(strength_stats['Weak'])],
        ['Very Weak', str(strength_stats['Very Weak'])],
    ]
    strength_table = Table(strength_data, colWidths=[180, 180])
    apply_navy_table_style(strength_table)
    elements.append(strength_table)
    elements.append(PageBreak())

    user_title = Paragraph("<b>Data Pengguna dan Informasi Keamanan Password</b>", section_title_style)
    elements.append(user_title)
    elements.append(Spacer(1, 10))

    # PERBAIKAN: Kolom Email diganti dengan Password Asli di PDF
    user_data = [[
        Paragraph("<b>No</b>", header_style),
        Paragraph("<b>Username</b>", header_style),
        Paragraph("<b>Pass Asli</b>", header_style),
        Paragraph("<b>Algoritma</b>", header_style),
        Paragraph("<b>Kekuatan</b>", header_style),
        Paragraph("<b>Hash Murni</b>", header_style),
        Paragraph("<b>Hash (+Salt)</b>", header_style),
    ]]

    for index, u in enumerate(users, start=1):
        unsalted_val = u.get('password_hash_unsalted') or 'Belum ada'
        pass_asli = u.get('plaintext_password') or '-'
        
        hash_unsalted_paragraph = Paragraph(str(unsalted_val), hash_style)
        hash_salted_paragraph = Paragraph(u['password_hash'], hash_style)
        
        user_data.append([
            Paragraph(str(index), normal_style),
            Paragraph(u['username'], normal_style),
            Paragraph(str(pass_asli), normal_style),
            Paragraph(u['hashing_method'], normal_style),
            Paragraph(u['password_strength'], normal_style),
            hash_unsalted_paragraph,
            hash_salted_paragraph 
        ])

    # PERBAIKAN: Matematika lebar kolom PDF disesuaikan agar Pass Asli cukup ruang
    user_table = Table(user_data, colWidths=[20, 50, 70, 50, 46, 163, 163], repeatRows=1)
    apply_navy_table_style(user_table)
    elements.append(user_table)
    elements.append(Spacer(1, 22))

    disclaimer = Paragraph("""<b>Disclaimer Analisis Keamanan:</b><br/>Laporan ini dihasilkan dari sistem analisis keamanan password lokal. Algoritma enkripsi MD5 tanpa garam (salt) secara teoritis rentan terhadap manipulasi berbasis tabel pelangi (Rainbow Table) dan serangan brute-force. Implementasi SHA-256 memberikan tingkat keamanan yang lebih tinggi terhadap serangan tersebut.""", body_style)
    elements.append(disclaimer)

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer, as_attachment=True,
        download_name='security_report_lengkap.pdf', mimetype='application/pdf'
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
    import zipfile