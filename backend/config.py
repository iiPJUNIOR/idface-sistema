import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    IDFACE_IP = os.getenv('IDFACE_IP', '192.168.0.129')
    IDFACE_USER = os.getenv('IDFACE_USER', 'admin')
    IDFACE_PASSWORD = os.getenv('IDFACE_PASSWORD', '123456')
    IDFACE_PORT = int(os.getenv('IDFACE_PORT', '80'))
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'idface-presenca-secret-key-2024')
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    PHOTOS_FOLDER = os.path.join(UPLOAD_FOLDER, 'photos')
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    @classmethod
    def init_folders(cls):
        os.makedirs(cls.PHOTOS_FOLDER, exist_ok=True)
