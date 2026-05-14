from flask import Flask
from flask_cors import CORS
from config import Config

# Import Blueprint dari folder routes
from routes.auth import auth_bp
from routes.admin import admin_bp

app = Flask(__name__)
CORS(app)

# Mendaftarkan Blueprint ke aplikasi utama
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    # Mengambil pengaturan Port dan Debug dari .env via config.py
    app.run(debug=Config.DEBUG, port=Config.PORT)