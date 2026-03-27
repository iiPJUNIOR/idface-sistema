"""
iDFace Sistema - Modo Local (Offline)
"""

import os
import sys
import base64
import time
from datetime import datetime
from io import BytesIO

backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_dir)

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room

from config import Config
from database import Database
from idface_client import IDFaceClient

Config.init_folders()

app = Flask(__name__, static_folder='frontend/dist', static_url_path='')
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

CORS(app, resources={r"/api/*": {"origins": "*"}})

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

db = Database()
idface = IDFaceClient()

print("=" * 60)
print("iDFace Sistema - MODO LOCAL (OFFLINE)")
print("=" * 60)
print(f"Banco: {db.db_path}")
print(f"Servidor: http://192.168.0.100:5000")
print("=" * 60)

def format_user(u):
    if not u:
        return None
    return {
        'id': u.get('id'), 'name': u.get('name'), 'registration': u.get('registration'),
        'cpf': u.get('cpf'), 'idface_id': u.get('idface_id'),
        'active': bool(u.get('active', 0)) == 1,
        'has_photo': bool(u.get('photo_path') or u.get('photo_base64')),
        'photo_url': f"/api/users/{u.get('id')}/photo",
        'created_at': u.get('created_at'), 'sync_pending': u.get('sync_pending', 0)
    }

def format_presence(p):
    return {
        'id': p.get('id'), 'user_id': p.get('user_id'),
        'name': p.get('name', ''), 'registration': p.get('registration', ''),
        'timestamp': p.get('timestamp') or p.get('created_at'), 'entries_count': p.get('entries_count', 1)
    }

@app.route('/')
def index():
    return send_from_directory('frontend/dist', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('frontend/dist', path)

@app.route('/api/users')
def get_users():
    return jsonify({'success': True, 'users': [format_user(u) for u in db.list_users(active_only=False)]})

@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    u = db.get_user(user_id)
    return jsonify({'success': True, 'user': format_user(u)}) if u else jsonify({'error': 'Nao encontrado'}), 404

@app.route('/api/users', methods=['POST'])
def create_user():
    d = request.get_json()
    if not d.get('name') or not d.get('registration'):
        return jsonify({'error': 'Nome e matricula obrigatorios'}), 400
    
    photo_base64 = None
    photo_data = None
    if d.get('photo', '').startswith('data:image'):
        photo_base64 = d['photo']
        try:
            # Extract base64 data from data URL
            photo_str = d['photo']
            if ',' in photo_str:
                photo_str = photo_str.split(',')[1]
            photo_data = base64.b64decode(photo_str)
        except Exception as e:
            print(f"[Photo] Erro ao processar foto: {e}")
            photo_data = None
    
    # Create in local database first
    result = db.add_user(d['name'], d['registration'], d.get('cpf'), photo_base64=photo_base64)
    
    if result.get('success'):
        user = db.get_user(result['user_id'])
        
        # Sync to IDFace
        try:
            idface_result = idface.create_user(name=user['name'], registration=user['registration'])
            if idface_result.get('success'):
                new_idface_id = idface_result.get('user_id')
                
                # Upload photo if available
                if photo_data:
                    try:
                        img_base64 = base64.b64encode(photo_data).decode('utf-8')
                        idface.upload_face_photo(new_idface_id, img_base64)
                        print(f"[Photo] Foto enviada para IDFace user {new_idface_id}")
                    except Exception as e:
                        print(f"[Photo] Erro ao enviar foto: {e}")
                
                db.update_user(user['id'], idface_id=str(new_idface_id), sync_pending=0)
                print(f"[Sync] Usuario {user['name']} criado no IDFace com ID {new_idface_id}")
            else:
                print(f"[Sync] Erro ao criar usuario no IDFace: {idface_result}")
        except Exception as e:
            print(f"[Sync] Erro: {e}")
        
        return jsonify({'success': True, 'user': format_user(db.get_user(result['user_id']))})
    return jsonify({'error': 'Erro'}), 400

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    d = request.get_json()
    u = db.get_user(user_id)
    if not u:
        return jsonify({'error': 'Nao encontrado'}), 404
    
    db.update_user(user_id, name=d.get('name', u['name']), registration=d.get('registration', u['registration']),
        cpf=d.get('cpf', u.get('cpf')), sync_pending=1)
    
    user = db.get_user(user_id)
    
    # Sync to IDFace if user has idface_id
    if user.get('idface_id') and str(user.get('idface_id')).lower() != 'none':
        try:
            idface.delete_user(int(user['idface_id']))
        except:
            pass
    
    try:
        idface_result = idface.create_user(name=user['name'], registration=user['registration'])
        if idface_result.get('success'):
            db.update_user(user_id, idface_id=str(idface_result['user_id']), sync_pending=0)
            print(f"[Sync] Usuario {user['name']} atualizado no IDFace")
    except Exception as e:
        print(f"[Sync] Erro ao atualizar: {e}")
    
    return jsonify({'success': True, 'user': format_user(db.get_user(user_id))})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    db.delete_user(user_id)
    return jsonify({'success': True})

@app.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_status(user_id):
    u = db.get_user(user_id)
    if not u:
        return jsonify({'error': 'Nao encontrado'}), 404
    new_status = 0 if u['active'] else 1
    db.update_user(user_id, active=new_status, sync_pending=1)
    return jsonify({'success': True, 'active': bool(new_status)})

@app.route('/api/users/<int:user_id>/photo')
def get_photo(user_id):
    u = db.get_user(user_id)
    if not u:
        return send_file(BytesIO(), mimetype='image/jpeg')
    if u.get('photo_base64'):
        try:
            return send_file(BytesIO(base64.b64decode(u['photo_base64'])), mimetype='image/jpeg')
        except:
            pass
    if u.get('photo_path') and os.path.exists(u['photo_path']):
        return send_file(u['photo_path'], mimetype='image/jpeg')
    return send_file(BytesIO(), mimetype='image/jpeg')

@app.route('/api/users/<int:user_id>/check-sync')
def check_sync(user_id):
    u = db.get_user(user_id)
    return jsonify({'synced': not u or u.get('sync_pending', 0) == 0})

@app.route('/api/presence/today')
def presence_today():
    result = db.get_presence_today()
    return jsonify({'success': True, 'date': datetime.now().strftime('%Y-%m-%d'),
        'presence': [format_presence(p) for p in result.get('presence', [])], 'stats': db.get_presence_stats()})

@app.route('/api/presence/stats')
def presence_stats():
    return jsonify({'success': True, 'stats': db.get_presence_stats()})

@app.route('/api/presence/recent')
def presence_recent():
    limit = request.args.get('limit', 50, type=int)
    return jsonify({'success': True, 'presence': [format_presence(p) for p in db.get_recent_presence(limit)]})

@app.route('/api/idface/test')
def test_idface():
    return jsonify(idface.test_connection())

@app.route('/api/idface/door/open', methods=['POST'])
def open_door():
    door = request.json.get('door', 0) if request.json else 0
    result = idface.open_door(door)
    return jsonify(result)

@app.route('/api/idface/list-users')
def list_idface_users():
    return jsonify({'success': True, 'users': idface.list_users()})

@app.route('/api/idface/sync-from-device', methods=['POST'])
def sync_from_idface():
    """Importa usuarios do IDFace para o sistema"""
    try:
        users = idface.list_users()
        print(f"[Sync] Usuarios encontrados no IDFace: {len(users)}")
        
        imported = 0
        updated = 0
        errors = []
        
        for user in users:
            name = user.get('name', '')
            registration = str(user.get('registration', ''))
            user_id_idface = user.get('id')
            
            print(f"[Sync] Processando: {name} (ID: {user_id_idface}, reg: {registration})")
            
            if not name or not registration:
                print(f"[Sync] Pulando usuario invalido")
                continue
            
            # Check if user exists by registration
            existing = db.get_user_by_registration(registration)
            if existing:
                print(f"[Sync] Usuario {registration} ja existe, atualizando")
                db.update_user(existing['id'], name=name, idface_id=str(user_id_idface))
                updated += 1
            else:
                # Get photo
                photo_data = None
                photo_base64 = None
                try:
                    photo_data = idface.get_user_photo(user_id_idface)
                    if photo_data:
                        photo_base64 = base64.b64encode(photo_data).decode('utf-8')
                        print(f"[Sync] Foto obtida para {name}")
                except Exception as e:
                    print(f"[Sync] Erro ao obter foto: {e}")
                
                print(f"[Sync] Criando usuario: {name}, reg: {registration}, idface_id: {user_id_idface}")
                result = db.add_user(
                    name=name, 
                    registration=registration, 
                    idface_id=str(user_id_idface), 
                    photo_base64=photo_base64
                )
                
                if result.get('success'):
                    imported += 1
                    print(f"[Sync] Sucesso! ID local: {result['user_id']}")
                else:
                    errors.append(f"{name}: {result.get('error', 'Erro desconhecido')}")
                    print(f"[Sync] Erro: {result}")
        
        return jsonify({
            'success': True, 
            'message': f'Importados: {imported}, Atualizados: {updated}', 
            'imported': imported,
            'updated': updated,
            'errors': errors
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/idface/sync-to-device', methods=['POST'])
def sync_to_idface():
    """Envia todos os usuarios do sistema para o IDFace"""
    try:
        users = db.list_users(active_only=True)
        synced = 0
        errors = []
        
        for user in users:
            idface_id = user.get('idface_id')
            
            # Delete existing if has idface_id
            if idface_id and str(idface_id).lower() != 'none':
                try:
                    idface.delete_user(int(idface_id))
                except:
                    pass
            
            # Create user in IDFace
            result = idface.create_user(
                name=user['name'], 
                registration=user['registration']
            )
            
            if result.get('success'):
                new_idface_id = result.get('user_id')
                db.update_user(user['id'], idface_id=str(new_idface_id), sync_pending=0)
                synced += 1
            else:
                errors.append(f"{user['name']}: {result.get('error', 'Erro')}")
        
        return jsonify({
            'success': True, 
            'synced': synced,
            'errors': errors
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/users/sync-all', methods=['POST'])
def sync_all():
    """Importa usuarios do IDFace para o sistema (como o frontend espera)"""
    try:
        users = idface.list_users()
        print(f"[Sync] Usuarios encontrados no IDFace: {len(users)}")
        
        imported = 0
        updated = 0
        errors = []
        
        for user in users:
            name = user.get('name', '')
            registration = str(user.get('registration', ''))
            user_id_idface = user.get('id')
            
            if not name or not registration:
                continue
            
            existing = db.get_user_by_registration(registration)
            if existing:
                db.update_user(existing['id'], name=name, idface_id=str(user_id_idface))
                updated += 1
            else:
                photo_data = None
                photo_base64 = None
                try:
                    photo_data = idface.get_user_photo(user_id_idface)
                    if photo_data:
                        photo_base64 = base64.b64encode(photo_data).decode('utf-8')
                except:
                    pass
                
                result = db.add_user(
                    name=name, 
                    registration=registration, 
                    idface_id=str(user_id_idface), 
                    photo_base64=photo_base64
                )
                
                if result.get('success'):
                    imported += 1
        
        return jsonify({
            'success': True, 
            'message': f'Importados: {imported}, Atualizados: {updated}', 
            'synced': imported + updated,
            'details': [{'action': 'import', 'name': u.get('name', '')} for u in users]
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/users/sync-pending', methods=['POST'])
def sync_pending():
    """Sincroniza apenas usuarios com sync_pending=1"""
    try:
        users = [u for u in db.list_users(active_only=False) if u.get('sync_pending', 0) == 1]
        synced = 0
        for user in users:
            idface_id = user.get('idface_id')
            
            if idface_id and str(idface_id).lower() != 'none':
                try:
                    idface.delete_user(int(idface_id))
                except:
                    pass
            
            result = idface.create_user(name=user['name'], registration=user['registration'])
            if result.get('success'):
                db.update_user(user['id'], idface_id=str(result['user_id']), sync_pending=0)
                synced += 1
        
        return jsonify({'success': True, 'message': f'{synced} usuarios sincronizados', 'success_count': synced})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# IDFace webhook endpoints
@app.route('/push_server.fcgi/push', methods=['GET', 'POST'])
@app.route('/push_server.fcgi/result', methods=['POST'])
@app.route('/push_server.fcgi', methods=['GET', 'POST'])
def push_server_fcgi():
    print(f"[PushServer] path={request.path}, args={dict(request.args)}, data={request.get_json(force=True, silent=True) or {}}")
    return jsonify({"code": 0, "endpoint": "/push_server.fcgi/result"})

@app.route('/new_user_identified.fcgi/push', methods=['GET', 'POST'])
def idface_push():
    print(f"[Push] args={dict(request.args)}")
    return jsonify({"code": 0})

@app.route('/new_user_identified.fcgi/result', methods=['POST'])
def idface_result():
    data = request.get_json(force=True, silent=True) or {}
    args = dict(request.args)
    print(f"[Result] args={args}, data={data}")
    
    user_id = data.get('user_id') or data.get('userId')
    print(f"[Result] user_id = {user_id}")
    
    if user_id:
        try:
            user_id = int(user_id)
        except:
            pass
        
        user = db.get_user_by_idface_id(user_id)
        if not user:
            user = db.get_user_by_registration(str(user_id))
        
        if user and bool(user.get('active', 0)) == 1:
            db.add_presence_log(user_id=user['id'], idface_id=str(user_id))
            socketio.emit('presence_detected', format_presence({**user, 'timestamp': datetime.now().isoformat()}), room='admin')
            idface.open_door(0)
            return jsonify({"result": 1, "user_id": user_id, "display_message": "Presenca Liberada", "user_image": True})
        elif user:
            return jsonify({"result": 6, "display_message": "Nao Autorizado", "user_image": False})
    
    return jsonify({"result": 6, "display_message": "Usuario nao cadastrado", "user_image": False})

@app.route('/new_user_identified.fcgi', methods=['POST'])
def new_user_identified():
    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get('user_id')
    device_id = data.get('device_id')
    timestamp = data.get('date_time')
    
    print(f"[Webhook] user_id={user_id}, device_id={device_id}")
    
    if not user_id:
        return jsonify({'success': True})
    
    user = db.get_user_by_idface_id(user_id)
    if not user:
        user = db.get_user_by_registration(str(user_id))
    
    if user and bool(user.get('active', 0)) == 1:
        db.add_presence_log(user_id=user['id'], idface_id=str(user_id), device_id=device_id, timestamp=timestamp)
        socketio.emit('presence_detected', format_presence({**user, 'timestamp': timestamp}), room='admin')
        idface.open_door(0)
        return jsonify({"result": 1, "user_id": user_id, "display_message": "Presenca Liberada", "user_image": True})
    elif user:
        return jsonify({"result": 6, "display_message": "Nao Autorizado", "user_image": False})
    
    return jsonify({"result": 6, "display_message": "Usuario nao cadastrado", "user_image": False})

@app.route('/new_user_identified.fcgi/dao', methods=['POST'])
@app.route('/new_user_identified.fcgi/device_is_alive', methods=['POST'])
@app.route('/dao', methods=['POST'])
@app.route('/device_is_alive', methods=['POST'])
def idface_dao():
    return jsonify({"code": 0, "message": "OK"})

@socketio.on('connect')
def connect():
    join_room('admin')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)