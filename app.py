from flask import Flask
from flask_cors import CORS
from config import Config

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
CORS(app)

# Mendaftarkan Blueprint ke aplikasi utama
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

@app.route('/export-pdf')
def export_pdf():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT username,
               email,
               hashing_method,
               password_strength,
               password_hash
        FROM users
    """)

    users = cursor.fetchall()

    cursor.close()
    conn.close()

    # =========================
    # HITUNG STATISTIK
    # =========================

    total_users = len(users)

    md5_count = len([
        u for u in users
        if u['hashing_method'] == 'MD5'
    ])

    sha_count = len([
        u for u in users
        if u['hashing_method'] == 'SHA-256'
    ])

    strength_stats = {
        'Very Strong': 0,
        'Strong': 0,
        'Fair': 0,
        'Weak': 0,
        'Very Weak': 0
    }

    for u in users:
        strength = u['password_strength']

        if strength in strength_stats:
            strength_stats[strength] += 1

    # =========================
    # PDF
    # =========================

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=25,
        leftMargin=25,
        topMargin=20,
        bottomMargin=20
    )

    styles = getSampleStyleSheet()

    NAVY = HexColor('#0F172A')
    WHITE = HexColor('#FFFFFF')
    BORDER = HexColor('#CBD5E1')

    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=NAVY,
        alignment=TA_CENTER
    )

    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=NAVY,
        alignment=TA_LEFT,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=NAVY
    )

    normal_style = ParagraphStyle(
        'TableNormal',
        parent=body_style,
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=NAVY,
        alignment=TA_CENTER
    )

    header_style = ParagraphStyle(
        'TableHeader',
        parent=normal_style,
        fontName='Helvetica-Bold',
        textColor=WHITE,
        alignment=TA_CENTER
    )

    hash_style = ParagraphStyle(
        'HashWrap',
        parent=normal_style,
        alignment=TA_LEFT,
        wordWrap='CJK'
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

    # =========================
    # TITLE
    # =========================

    title = Paragraph(
        "<b>Laporan Keamanan Password (Sistem Analisis)</b>",
        title_style
    )

    elements.append(title)

    elements.append(Spacer(1, 10))

    # =========================
    # INFO
    # =========================

    info = Paragraph(
        f"""
        <b>Tanggal Cetak :</b> {datetime.now().strftime('%d %B %Y %H:%M:%S')}<br/>
        <b>Jumlah Total Entri :</b> {total_users}
        """,
        body_style
    )

    elements.append(info)

    elements.append(Spacer(1, 18))

    # =========================
    # RINGKASAN
    # =========================

    summary_title = Paragraph(
        "<b>Ringkasan Statistik Kontrol Kriptografi</b>",
        section_title_style
    )

    elements.append(summary_title)

    summary_data = [
        ['Kategori', 'Jumlah'],
        ['Total Entri Akun', str(total_users)],
        ['Penggunaan Algoritma MD5', str(md5_count)],
        ['Penggunaan Algoritma SHA-256', str(sha_count)],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[260, 100]
    )
    apply_navy_table_style(summary_table)

    elements.append(summary_table)

    elements.append(Spacer(1, 20))

    # =========================
    # DISTRIBUSI ALGORITMA
    # =========================

    algo_title = Paragraph(
        "<b>Distribusi Algoritma Hashing</b>",
        section_title_style
    )

    elements.append(algo_title)

    algo_data = [
        ['Algoritma', 'Jumlah Pengguna'],
        ['MD5', str(md5_count)],
        ['SHA-256', str(sha_count)],
    ]

    algo_table = Table(
        algo_data,
        colWidths=[180, 180]
    )
    apply_navy_table_style(algo_table)

    elements.append(algo_table)

    elements.append(Spacer(1, 18))

    # =========================
    # DISTRIBUSI STRENGTH
    # =========================

    strength_title = Paragraph(
        "<b>Distribusi Kekuatan Password (zxcvbn)</b>",
        section_title_style
    )

    elements.append(strength_title)

    strength_data = [
        ['Kekuatan', 'Jumlah Pengguna'],
        ['Very Strong', str(strength_stats['Very Strong'])],
        ['Strong', str(strength_stats['Strong'])],
        ['Fair', str(strength_stats['Fair'])],
        ['Weak', str(strength_stats['Weak'])],
        ['Very Weak', str(strength_stats['Very Weak'])],
    ]

    strength_table = Table(
        strength_data,
        colWidths=[180, 180]
    )
    apply_navy_table_style(strength_table)

    elements.append(strength_table)

    elements.append(PageBreak())

    # =========================
    # DATA USER
    # =========================

    user_title = Paragraph(
        "<b>Data Pengguna dan Informasi Keamanan Password</b>",
        section_title_style
    )

    elements.append(user_title)

    elements.append(Spacer(1, 10))

    user_data = [[
        Paragraph("<b>No</b>", header_style),
        Paragraph("<b>Username</b>", header_style),
        Paragraph("<b>Email</b>", header_style),
        Paragraph("<b>Algoritma</b>", header_style),
        Paragraph("<b>Kekuatan</b>", header_style),
        Paragraph("<b>Hash Password</b>", header_style),
    ]]

    for index, u in enumerate(users, start=1):

        # HASH AUTO WRAP KE BAWAH
        hash_paragraph = Paragraph(
            u['password_hash'],
            hash_style
        )

        user_data.append([
            Paragraph(str(index), normal_style),
            Paragraph(u['username'], normal_style),
            Paragraph(u['email'], normal_style),
            Paragraph(u['hashing_method'], normal_style),
            Paragraph(u['password_strength'], normal_style),
            hash_paragraph
        ])

    user_table = Table(
        user_data,
        colWidths=[28, 70, 120, 65, 75, 170],
        repeatRows=1
    )
    apply_navy_table_style(user_table)

    elements.append(user_table)

    elements.append(Spacer(1, 22))

    # =========================
    # DISCLAIMER
    # =========================

    disclaimer = Paragraph(
        """
        <b>Disclaimer Analisis Keamanan:</b><br/>
        Laporan ini dihasilkan dari sistem analisis keamanan password lokal.
        Algoritma enkripsi MD5 tanpa garam (salt) secara teoritis rentan
        terhadap manipulasi berbasis tabel pelangi (Rainbow Table) dan
        serangan brute-force. Implementasi SHA-256 memberikan tingkat
        keamanan yang lebih tinggi terhadap serangan tersebut.
        """,
        body_style
    )

    elements.append(disclaimer)

    # =========================
    # BUILD PDF
    # =========================

    doc.build(elements)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='security_report.pdf',
        mimetype='application/pdf'
    )

if __name__ == '__main__':
    # Mengambil pengaturan Port dan Debug dari .env via config.py
    app.run(debug=Config.DEBUG, port=Config.PORT)
