"""
iDFace Sistema - Modo Local (Offline)
Para usar quando não tiver internet ou o servidor online estiver indisponível.

Como usar:
1. Execute: python run_local.py
2. Acesse: http://localhost:5000
3. Configure o IDFace para enviar para: http://SEU_PC_IP:5000/new_user_identified.fcgi

O sistema usará SQLite local (presenca.db) para armazenamento.
"""

import os
import sys

# Adicionar diretório backend ao path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

# Usar SQLite local
os.environ['USE_LOCAL_DB'] = 'true'

# Importar componentes
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
import base64
import time
import json
import csv
import io
from datetime import datetime
from io import BytesIO

from config import Config
from database import Database
from idface_client import IDFaceClient

Config.init_folders()

# Criar app Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

CORS(app, resources={r"/api/*": {"origins": "*"}})

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Inicializar banco SQLite local
db = Database()
idface = IDFaceClient()

print("=" * 60)
print("iDFace Sistema - MODO LOCAL (OFFLINE)")
print("=" * 60)
print(f"Banco de dados: {db.db_path}")
print(f"Servidor: http://localhost:5000")
print("=" * 60)

# Funções auxiliares
def format_user_for_response(user):
    if not user:
        return None
    return {
        'id': user.get('id'),
        'name': user.get('name'),
        'registration': user.get('registration'),
        'cpf': user.get('cpf'),
        'idface_id': user.get('idface_id'),
        'active': bool(user.get('active', 0)) == 1,
        'has_photo': bool(user.get('photo_path') or user.get('photo_base64')),
        'photo_url': f"/api/users/{user.get('id')}/photo",
        'created_at': user.get('created_at'),
        'sync_pending': user.get('sync_pending', 0)
    }

def format_presence_for_response(log):
    return {
        'id': log.get('id'),
        'user_id': log.get('user_id'),
        'name': log.get('name', ''),
        'registration': log.get('registration', ''),
        'timestamp': log.get('timestamp') or log.get('created_at'),
        'created_at': log.get('created_at'),
        'entries_count': log.get('entries_count', 1)
    }

# ========== ROTAS ==========

@app.route('/')
def index():
    return jsonify({
        'service': 'iDFace Sistema',
        'mode': 'local',
        'version': '1.0.0',
        'endpoints': [
            '/api/users',
            '/api/presence/today',
            '/api/idface/test',
            '/new_user_identified.fcgi'
        ]
    })

# USERS
@app.route('/api/users')
def get_users():
    users = db.list_users(active_only=False)
    return jsonify({
        'success': True,
        'users': [format_user_for_response(u) for u in users]
    })

@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    user = db.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Usuário não encontrado'}), 404
    return jsonify({'success': True, 'user': format_user_for_response(user)})

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data.get('name')
    registration = data.get('registration')
    cpf = data.get('cpf')
    photo = data.get('photo', '')
    
    if not name or not registration:
        return jsonify({'success': False, 'error': 'Nome e matrícula são obrigatórios'}), 400
    
    photo_base64 = photo if photo and photo.startswith('data:image') else None
    photo_path = None
    if photo and not photo_base64:
        filename = f"user_{int(time.time())}.jpg"
        photo_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        try:
            import base64
            img_data = base64.b64decode(photo)
            with open(photo_path, 'wb') as f:
                f.write(img_data)
        except:
            photo_path = None
    
    result = db.add_user(name, registration, cpf, photo_path=photo_path, photo_base64=photo_base64)
    if result.get('success'):
        user = db.get_user(result['user_id'])
        socketio.emit('user_created', format_user_for_response(user), room='admin')
        return jsonify({'success': True, 'user': format_user_for_response(user)})
    return jsonify({'success': False, 'error': result.get('error', 'Erro ao criar usuário'}), 400

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    user = db.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Usuário não encontrado'}), 404
    
    photo = data.get('photo', '')
    photo_path = user.get('photo_path')
    photo_base64 = user.get('photo_base64')
    
    if photo and photo.startswith('data:image'):
        filename = f"user_{user_id}_{int(time.time())}.jpg"
        photo_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        try:
            img_data = base64.b64decode(photo)
            with open(photo_path, 'wb') as f:
                f.write(img_data)
            photo_base64 = None
        except:
            photo_path = None
    
    db.update_user(user_id, 
        name=data.get('name', user['name']),
        registration=data.get('registration', user['registration']),
        cpf=data.get('cpf', user.get('cpf')),
        photo_path=photo_path,
        photo_base64=photo_base64,
        active=data.get('active', user['active']),
        sync_pending=1
    )
    
    user = db.get_user(user_id)
    socketio.emit('user_updated', format_user_for_response(user), room='admin')
    return jsonify({'success': True, 'user': format_user_for_response(user)})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    db.delete_user(user_id)
    socketio.emit('user_deleted', {'user_id': user_id}, room='admin')
    return jsonify({'success': True})

@app.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    user = db.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Usuário não encontrado'}), 404
    
    new_status = 0 if user['active'] else 1
    db.update_user(user_id, active=new_status, sync_pending=1)
    
    user = db.get_user(user_id)
    socketio.emit('user_updated', format_user_for_response(user), room='admin')
    return jsonify({'success': True, 'active': bool(new_status)})

@app.route('/api/users/<int:user_id>/photo')
def get_user_photo(user_id):
    user = db.get_user(user_id)
    if not user:
        return send_file(BytesIO(), mimetype='image/jpeg')
    
    if user.get('photo_base64'):
        try:
            img_data = base64.b64decode(user['photo_base64'])
            return send_file(BytesIO(img_data), mimetype='image/jpeg')
        except:
            pass
    
    if user.get('photo_path') and os.path.exists(user['photo_path']):
        return send_file(user['photo_path'], mimetype='image/jpeg')
    
    return send_file(BytesIO(), mimetype='image/jpeg')

# PRESENCE
@app.route('/api/presence/today')
def presence_today():
    result = db.get_presence_today()
    presence = result.get('presence', []) if isinstance(result, dict) else result
    stats = db.get_presence_stats()
    return jsonify({
        'success': True,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'presence': [format_presence_for_response(p) for p in presence],
        'stats': stats
    })

@app.route('/api/presence/stats')
def presence_stats():
    stats = db.get_presence_stats()
    return jsonify({'success': True, 'stats': stats})

@app.route('/api/presence/recent')
def presence_recent():
    limit = request.args.get('limit', 50, type=int)
    presence = db.get_recent_presence(limit)
    return jsonify({
        'success': True,
        'presence': [format_presence_for_response(p) for p in presence]
    })

# IDFACE
@app.route('/api/idface/test')
def test_idface():
    result = idface.test_connection()
    return jsonify(result)

@app.route('/api/idface/door/open', methods=['POST'])
def open_door():
    door = request.json.get('door', 0) if request.json else 0
    result = idface.open_door(door)
    return jsonify(result)

# WEBHOOK IDFACE
@app.route('/new_user_identified.fcgi', methods=['POST'])
def new_user_identified():
    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get('user_id')
    device_id = data.get('device_id')
    timestamp = data.get('date_time')
    
    if not user_id:
        return jsonify({'success': True})
    
    user = db.get_user_by_idface_id(user_id)
    if not user:
        user = db.get_user_by_registration(str(user_id))
    
    if user:
        is_active = bool(user.get('active', 0)) == 1
        
        if is_active:
            db.add_presence_log(
                user_id=user['id'],
                idface_id=str(user_id),
                device_id=device_id,
                timestamp=timestamp
            )
            
            presence_data = format_presence_for_response({
                **user,
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat()
            })
            
            socketio.emit('presence_detected', presence_data, room='admin')
            idface.open_door(0)
            
            return jsonify({
                "result": 1,
                "user_id": user_id,
                "display_message": "Presença Liberada",
                "user_image": True
            })
        else:
            return jsonify({
                "result": 6,
                "display_message": "Não Autorizado",
                "user_image": False
            })
    
    return jsonify({
        "result": 6,
        "display_message": "Usuário não cadastrado",
        "user_image": False
    })

# SOCKET.IO
@socketio.on('connect')
def handle_connect():
    print('Cliente conectado')
    join_room('admin')

@socketio.on('disconnect')
def handle_disconnect():
    print('Cliente desconectado')

@socketio.on('subscribe')
def handle_subscribe(data):
    if data.get('room'):
        join_room(data['room'])

# INICIAR SERVIDOR
if __name__ == '__main__':
    print("\nPara configurar o IDFace local:")
    print("1. No IDFace/iDCloud, configure o servidor como:")
    print(f"   http://SEU_IP_LOCAL:5000/new_user_identified.fcgi")
    print("2. Use ipconfig (Windows) ou ifconfig (Linux/Mac) para descobrir seu IP local\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)