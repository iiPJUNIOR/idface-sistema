from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
import os
import base64
import time
import json
import csv
import io
import requests
from datetime import datetime
from io import BytesIO

from config import Config
# Usar Supabase (descomente para usar SQLite local)
# from database import Database
from database_supabase import db
from idface_client import IDFaceClient

Config.init_folders()

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

CORS(app, resources={r"/api/*": {"origins": "*"}})

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# db é importado diretamente de database_supabase
idface = IDFaceClient()

polling_active = False
max_log_id_seen = None
last_timestamp_seen = None
first_run = True
PROCESSED_LOGS_FILE = os.path.join(os.path.dirname(__file__), '.processed_logs.json')

def load_max_log_id():
    global max_log_id_seen
    try:
        if os.path.exists(PROCESSED_LOGS_FILE):
            with open(PROCESSED_LOGS_FILE, 'r') as f:
                data = json.load(f)
                return data.get('max_log_id_seen')
    except:
        pass
    return None

def save_max_log_id(log_id):
    try:
        with open(PROCESSED_LOGS_FILE, 'w') as f:
            json.dump({'max_log_id_seen': log_id}, f)
    except:
        pass

def reset_polling():
    global max_log_id_seen, first_run
    max_log_id_seen = None
    first_run = True
    if os.path.exists(PROCESSED_LOGS_FILE):
        try:
            os.remove(PROCESSED_LOGS_FILE)
        except:
            pass

def poll_idface_logs():
    global last_timestamp_seen, first_run
    try:
        if first_run:
            last_timestamp_seen = int(time.time()) - 10
            first_run = False
        
        since = last_timestamp_seen if last_timestamp_seen else int(time.time()) - 10
        logs = idface.get_access_logs_v2(since_timestamp=since)
        
        if not logs:
            return
        
        for log in logs:
            unix_time = log.get('time', 0)
            
            if unix_time <= last_timestamp_seen:
                continue
            
            last_timestamp_seen = unix_time
            
            event_type = log.get('event', 0)
            user_id = log.get('user_id', 0)
            log_id = log.get('id', 0)
            
            if unix_time:
                try:
                    dt = datetime.fromtimestamp(unix_time)
                    timestamp = dt.isoformat()
                except:
                    timestamp = datetime.now().isoformat()
            else:
                timestamp = datetime.now().isoformat()
            
            try:
                event_type_int = int(event_type) if event_type else 0
            except (ValueError, TypeError):
                event_type_int = 0
            
            try:
                user_id_int = int(user_id) if user_id else 0
            except (ValueError, TypeError):
                user_id_int = 0
            
            recognition_data = {
                "user_id": user_id_int if user_id_int else None,
                "name": "",
                "registration": "",
                "active": False,
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "event_type": event_type_int
            }
            
            event_description = get_event_description(event_type_int)
            recognition_data["event_description"] = event_description
            
            if event_type_int == 3 or user_id_int == 0:
                recognition_data["name"] = "Não Reconhecido"
                recognition_data["not_recognized"] = True
                recognition_data["active"] = False
                recognition_data["blocked"] = False
            elif user_id_int and event_type_int == 7:
                try:
                    user = db.get_user_by_cpf(str(user_id_int))
                    if not user:
                        user = db.get_user_by_idface_id(user_id_int)
                    if not user:
                        user = db.get_user_by_registration(str(user_id_int))
                    
                    if user:
                        is_active = bool(user.get('active', 0)) == 1
                        
                        recognition_data["user_id"] = user['id']
                        recognition_data["name"] = user['name']
                        recognition_data["registration"] = user['registration']
                        recognition_data["active"] = is_active
                        recognition_data["blocked"] = False
                        
                        if is_active:
                            unix_timestamp = int(unix_time) if unix_time else int(time.time())
                            db.add_presence_log(
                                user_id=user['id'],
                                idface_id=user_id_int,
                                device_id=0,
                                identifier_type="face",
                                result=7,
                                timestamp=unix_timestamp
                            )
                            
                            presence_data = format_presence_for_response({
                                **user,
                                "timestamp": timestamp,
                                "created_at": datetime.now().isoformat()
                            })
                            
                            socketio.emit('presence_detected', presence_data, room='admin')
                            idface.open_door(0)
                        else:
                            recognition_data["blocked"] = True
                    else:
                        recognition_data["name"] = f"Usuário {user_id_int}"
                        recognition_data["registration"] = str(user_id_int)
                        recognition_data["not_found"] = True
                        recognition_data["blocked"] = False
                except Exception as e:
                    recognition_data["error"] = str(e)
            else:
                recognition_data["name"] = f"Evento {event_type_int}"
            
            socketio.emit('recognition_detected', recognition_data, room='admin')
    
    except Exception as e:
        print(f"[Polling] Erro: {e}")

def start_polling():
    global polling_active
    import threading
    polling_active = True
    
    def run_polling():
        while polling_active:
            try:
                poll_idface_logs()
            except Exception as e:
                print(f"[Polling] Erro: {e}")
            time.sleep(3)
    
    thread = threading.Thread(target=run_polling, daemon=True)
    thread.start()
    print("[Polling] Started")

def stop_polling():
    global polling_active
    polling_active = False
    print("[Polling] Stopped")

def format_user_for_response(user: dict) -> dict:
    if not user:
        return {}
    response = {
        "id": user.get("id"),
        "name": user.get("name"),
        "registration": user.get("registration"),
        "cpf": user.get("cpf"),
        "idface_id": user.get("idface_id"),
        "active": bool(user.get("active", 1)),
        "created_at": user.get("created_at"),
        "has_photo": bool(user.get("photo_path") or user.get("photo_base64"))
    }
    
    if user.get("photo_path") or user.get("photo_base64"):
        response["photo_url"] = f"/api/users/{user['id']}/photo"
    
    return response

def format_presence_for_response(log: dict) -> dict:
    return {
        "id": log.get("id"),
        "user_id": log.get("user_id"),
        "name": log.get("name"),
        "registration": log.get("registration"),
        "timestamp": log.get("timestamp") or log.get("created_at"),
        "created_at": log.get("created_at"),
        "entries_count": log.get("entries_count", 1)
    }

def get_event_description(event_type: int) -> str:
    descriptions = {
        1: "Acesso por cartão",
        2: "Acesso por biometria",
        3: "Face não reconhecida",
        4: "Cartão inválido",
        5: "Acesso negado",
        6: "Usuário bloqueado",
        7: "Face reconhecida",
        8: "Acesso por senha",
        9: "Evento de porta",
        10: "Anti-s防火back",
        11: "Intertravamento",
        12: "Acesso neg. por horário",
        13: "Acesso neg. por feriado",
        14: "Acesso neg. por blacklist",
        15: "Acesso neg. por leitor inválido",
    }
    return descriptions.get(event_type, f"Evento {event_type}")

@app.route('/')
def index():
    return jsonify({
        "name": "IDFace Presença API",
        "version": "1.0.0",
        "status": "running"
    })

@app.route('/api/polling/reset', methods=['GET', 'POST'])
def reset_polling_endpoint():
    reset_polling()
    return jsonify({"success": True, "message": "Polling resetado"})

@app.route('/api/health')
def health():
    idface_status = idface.test_connection()
    
    return jsonify({
        "status": "healthy",
        "database": "connected",
        "idface": idface_status
    })

@app.route('/api/idface/test')
def test_idface():
    result = idface.test_connection()
    return jsonify(result)

@app.route('/api/idface/test-photo/<int:user_id>', methods=['GET'])
def test_idface_photo(user_id):
    print(f"[Test Photo] Tentando baixar foto do usuário IDFace ID: {user_id}")
    
    if not idface.session or (idface.session_created_at and time.time() - idface.session_created_at > 3600):
        session_result = idface.create_session()
        if not session_result.get('success'):
            return jsonify({"success": False, "message": "Falha ao criar sessão IDFace"}), 500
    
    url = f"{idface._make_url('/load_objects.fcgi')}?session={idface.session}"
    
    payload = {
        "object": "users",
        "filter": {"id": user_id},
        "include": ["face_image"]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        print(f"[Test Photo] Response: {data}")
        
        users = data.get("users", [])
        if users:
            user = users[0]
            print(f"[Test Photo] User: {user.get('name')}, has face_image: {bool(user.get('face_image'))}")
            
            if user.get("face_image"):
                face_image = user["face_image"]
                print(f"[Test Photo] face_image length: {len(face_image) if face_image else 0}")
                
                photo_bytes = base64.b64decode(face_image)
                print(f"[Test Photo] Decoded bytes length: {len(photo_bytes)}")
                
                return send_file(
                    BytesIO(photo_bytes),
                    mimetype='image/jpeg'
                )
        
        return jsonify({
            "success": False,
            "message": "Foto não encontrada",
            "user_id": user_id,
            "response": str(data)[:500]
        }), 404
    except Exception as e:
        print(f"[Test Photo] Erro: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/idface/list-users', methods=['GET'])
def list_idface_users():
    try:
        users = idface.list_users()
        return jsonify({
            "success": True,
            "count": len(users),
            "users": [{"id": u.get("id"), "name": u.get("name"), "registration": u.get("registration")} for u in users]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/idface/door/open', methods=['POST'])
def open_door():
    door = request.json.get('door', 0) if request.json else 0
    result = idface.open_door(door)
    return jsonify(result)

@app.route('/api/users', methods=['GET'])
def list_users():
    users = db.list_users(active_only=False)
    return jsonify({
        "success": True,
        "users": [format_user_for_response(u) for u in users]
    })

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    
    if not data.get('name') or not data.get('registration'):
        return jsonify({"success": False, "error": "Nome e matrícula são obrigatórios"}), 400
    
    name = data['name']
    registration = data['registration']
    cpf = data.get('cpf')
    photo_base64 = data.get('photo')
    photo_path = None
    
    if photo_base64:
        filename = f"{registration}_{int(time.time())}.jpg"
        photo_path = os.path.join(Config.PHOTOS_FOLDER, filename)
        
        try:
            image_data = base64.b64decode(photo_base64)
            with open(photo_path, 'wb') as f:
                f.write(image_data)
        except Exception as e:
            print(f"Erro ao salvar foto: {e}")
            photo_path = None
    
    result = db.add_user(
        name=name,
        registration=registration,
        cpf=cpf,
        photo_path=photo_path,
        photo_base64=photo_base64
    )
    
    if not result.get('success'):
        return jsonify(result), 400
    
    user_id = result['user_id']
    
    sync_result = sync_user_to_idface(user_id)
    if sync_result.get('success'):
        db.update_user(user_id, idface_id=sync_result.get('idface_id'), sync_pending=0)
    
    user = db.get_user(user_id)
    
    socketio.emit('user_created', format_user_for_response(user), room='admin')
    
    return jsonify({
        "success": True,
        "user": format_user_for_response(user),
        "synced_to_idface": photo_base64 is not None
    }), 201

def sync_user_to_idface(user_id: int) -> dict:
    print(f"[Sync] Iniciando sincronização do usuário ID {user_id}")
    user = db.get_user(user_id)
    if not user:
        print(f"[Sync] Usuário {user_id} não encontrado no banco")
        return {"success": False, "error": "Usuário não encontrado"}
    
    print(f"[Sync] Criando sessão IDFace para {user.get('name')}")
    if not idface.session or (idface.session_created_at and time.time() - idface.session_created_at > 3600):
        session_result = idface.create_session()
        print(f"[Sync] Resultado da sessão: {session_result}")
        if not session_result.get('success'):
            return {"success": False, "error": f"Falha ao conectar com IDFace: {session_result.get('message', 'Erro desconhecido')}"}
    
    print(f"[Sync] Verificando se usuário já existe no IDFace...")
    existing = None
    
    # Usar list_users e filtrar manualmente (a busca por CPF do IDFace tem bugs)
    all_users = idface.list_users()
    user_cpf = str(user.get('cpf', '')).strip() if user.get('cpf') else ''
    user_reg = str(user.get('registration', '')).strip()
    user_name_lower = user.get('name', '').lower().strip()
    
    print(f"[Sync] Procurando em {len(all_users)} usuários do IDFace...")
    for u in all_users:
        idface_cpf = str(u.get('registration'))  # O IDFace usa registration como CPF
        idface_reg = str(u.get('registration', '')).strip()
        idface_name = u.get('name', '').strip().lower()
        
        # Verificar se é o mesmo usuário pelo ID (cpf)
        if user_cpf and str(u.get('id')) == user_cpf:
            print(f"[Sync] Encontrou pelo ID={u.get('id')}")
            existing = u
            break
        # Verificar pela registration
        if user_reg and idface_reg == user_reg:
            print(f"[Sync] Encontrou pela registration={idface_reg}")
            existing = u
            break
    
    if existing:
        idface_id = existing.get('id')
        if user.get('cpf') and user.get('idface_id') != user['cpf']:
            db.update_user(user_id, idface_id=user['cpf'])
            idface_id = int(user['cpf'])
        
        # Verificar se nome mudou - se mudou, excluir e recriar
        idface_name = existing.get('name', '').strip()
        print(f"[Sync] Nome no IDFace: '{idface_name}', Nome no sistema: '{user.get('name', '')}'")
        if idface_name.lower() != user.get('name', '').lower().strip():
            print(f"[Sync] Nome mudou! Excluindo e recriando usuário...")
            # Excluir usuário antigo
            if existing.get('registration'):
                result_del = idface.delete_user_alternative(existing['registration'])
                print(f"[Sync] Resultado exclusão: {result_del}")
            # Criar novo usuário com novo nome
            create_result = idface.create_user(
                name=user['name'],
                registration=user['registration'],
                cpf=user.get('cpf') or str(idface_id)
            )
            if create_result.get('success'):
                new_idface_id = create_result['user_id']
                db.update_user(user_id, idface_id=str(new_idface_id))
                # Enviar foto se existir
                if user.get('photo_base64') or user.get('photo_path'):
                    if user.get('photo_path'):
                        idface.upload_face_photo_from_file(int(new_idface_id), user['photo_path'])
                    else:
                        idface.upload_face_photo(int(new_idface_id), user['photo_base64'])
                print(f"[Sync] Usuário recriado com novo nome! ID: {new_idface_id}")
                return {"success": True, "idface_id": str(new_idface_id), "action": "updated"}
        
        if user.get('photo_base64') or user.get('photo_path'):
            photo_id = int(idface_id) if idface_id else int(user.get('cpf', 0))
            if user.get('photo_path'):
                result = idface.upload_face_photo_from_file(photo_id, user['photo_path'])
            else:
                result = idface.upload_face_photo(photo_id, user['photo_base64'])
            
            if result.get('success'):
                print(f"[Sync] Foto enviada para usuário {photo_id}")
                return {"success": True, "idface_id": idface_id, "action": "updated"}
            else:
                print(f"[Sync] Erro ao enviar foto: {result}")
        
        return {"success": True, "idface_id": idface_id, "action": "exists"}
    
    # Se não encontrou pelo nome/CPF mas tem idface_id e registration, usar direto
    # (O IDFace pode ter nomes diferentes, mas se registration bate, é o mesmo usuário)
    if user.get('idface_id') and user.get('registration'):
        print(f"[Sync] Usuário não encontrado pelo nome, mas tem idface_id={user.get('idface_id')} no banco")
        # Verificar se existe no IDFace pelo ID
        all_users = idface.list_users()
        for u in all_users:
            if str(u.get('id')) == str(user.get('idface_id')):
                print(f"[Sync] Encontrou usuário pelo idface_id existente!")
                # Verificar se nome mudou
                idface_name = u.get('name', '').strip()
                if idface_name.lower() != user.get('name', '').lower().strip():
                    print(f"[Sync] Nome mudou! Excluindo e recriando...")
                    if u.get('registration'):
                        idface.delete_user_alternative(u['registration'])
                    create_result = idface.create_user(
                        name=user['name'],
                        registration=user['registration'],
                        cpf=user.get('cpf') or str(user['idface_id'])
                    )
                    if create_result.get('success'):
                        new_idface_id = create_result['user_id']
                        db.update_user(user_id, idface_id=str(new_idface_id))
                        if user.get('photo_base64') or user.get('photo_path'):
                            if user.get('photo_path'):
                                idface.upload_face_photo_from_file(int(new_idface_id), user['photo_path'])
                            else:
                                idface.upload_face_photo(int(new_idface_id), user['photo_base64'])
                        return {"success": True, "idface_id": str(new_idface_id), "action": "updated"}
                if user.get('photo_base64') or user.get('photo_path'):
                    photo_id = int(user['idface_id'])
                    if user.get('photo_path'):
                        result = idface.upload_face_photo_from_file(photo_id, user['photo_path'])
                    else:
                        result = idface.upload_face_photo(photo_id, user['photo_base64'])
                    if result.get('success'):
                        print(f"[Sync] Foto enviada para usuário {photo_id}")
                        return {"success": True, "idface_id": user['idface_id'], "action": "updated"}
                return {"success": True, "idface_id": user['idface_id'], "action": "exists"}
    
    print(f"[Sync] Criando usuário no IDFace: {user.get('name')} - {user.get('registration')}")
    create_result = idface.create_user(
        name=user['name'],
        registration=user['registration'],
        cpf=user.get('cpf')
    )
    print(f"[Sync] Resultado criação: {create_result}")
    
    if not create_result.get('success'):
        error_msg = str(create_result.get('error', ''))
        if 'UNIQUE constraint' in error_msg or 'constraint failed' in error_msg:
            print(f"[Sync] Erro de constraint - tentando encontrar usuário existente...")
            # Tenta listar todos os usuários e encontrar pelo nome
            all_users = idface.list_users()
            for u in all_users:
                if u.get('name', '').lower() == user.get('name', '').lower():
                    print(f"[Sync] Encontrou usuário existente: {u.get('id')}")
                    db.update_user(user_id, idface_id=str(u.get('id')), sync_pending=0)
                    return {"success": True, "idface_id": str(u.get('id')), "action": "found_existing"}
            return {"success": False, "error": "IDFace com problema: não consegue criar usuário. Tente sincronizar novamente."}
        print(f"[Sync] ERRO ao criar usuário: {create_result}")
        return create_result
    
    idface_id = create_result.get('user_id')
    
    photo_id = None
    if user.get('cpf'):
        photo_id = int(user['cpf'])
        idface_id = user['cpf']
        db.update_user(user_id, idface_id=user['cpf'])
    else:
        photo_id = int(idface_id)
        db.update_user(user_id, idface_id=str(idface_id))
    
    if user.get('photo_base64') or user.get('photo_path'):
        if user.get('photo_path'):
            photo_result = idface.upload_face_photo_from_file(photo_id, user['photo_path'])
        else:
            photo_result = idface.upload_face_photo(photo_id, user['photo_base64'])
        
        if not photo_result.get('success'):
            print(f"Aviso: Foto não foi enviada para IDFace: {photo_result}")
    
    try:
        access_rules = idface.get_access_rules()
        release_rule = next((r for r in access_rules if r.get('type') == 1), None)
        if release_rule:
            idface.set_user_access_rule(photo_id, release_rule.get('id'))
            print(f"[Sync] Regra de acesso liberada para usuário {photo_id}")
    except Exception as e:
        print(f"[Sync] Erro ao definir regra de acesso: {e}")
    
    db.update_user(user_id, sync_pending=0)
    
    return {"success": True, "idface_id": idface_id, "action": "created"}

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = db.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "Usuário não encontrado"}), 404
    
    return jsonify({
        "success": True,
        "user": format_user_for_response(user)
    })

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    
    user = db.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "Usuário não encontrado"}), 404
    
    photo_base64 = data.get('photo')
    has_new_photo = photo_base64 and len(photo_base64) > 100  # Verifica se é uma foto nova (base64 válido)
    
    if has_new_photo:
        filename = f"{data.get('registration', user['registration'])}_{int(time.time())}.jpg"
        photo_path = os.path.join(Config.PHOTOS_FOLDER, filename)
        
        try:
            image_data = base64.b64decode(photo_base64)
            with open(photo_path, 'wb') as f:
                f.write(image_data)
            data['photo_path'] = photo_path
            data['photo_base64'] = photo_base64
        except Exception as e:
            print(f"Erro ao salvar foto: {e}")
    
    update_data = {k: v for k, v in data.items() if k in ['name', 'cpf', 'photo_path', 'photo_base64', 'idface_id']}
    
    # Verifica se nome ou foto foi alterado - marca como pendente de sync APENAS se realmente mudou
    name_changed = 'name' in update_data and update_data['name'] and update_data['name'] != user.get('name')
    photo_changed = has_new_photo  # Só marca se tem foto nova
    
    if update_data:
        db.update_user(user_id, **update_data)
    
    # Se nome ou foto mudou, marca como pendente
    if name_changed or photo_changed:
        db.update_user(user_id, sync_pending=1)
        print(f"[Update] Usuário {user_id} marcado como pendente de sync (nome alterado: {name_changed}, foto alterada: {photo_changed})")
    
    # Se tem foto nova, envia para IDFace
    if has_new_photo:
        sync_result = sync_user_to_idface(user_id)
        if sync_result.get('success'):
            db.update_user(user_id, idface_id=sync_result.get('idface_id'), sync_pending=0)
    
    # Se nome mudou mas não tem foto nova, ainda tenta sync para manter a foto (mesmo que nome não seja atualizável no IDFace)
    if name_changed and not has_new_photo and user.get('idface_id'):
        # Tenta sync mesmo só com nome (vai manter a foto existente)
        sync_result = sync_user_to_idface(user_id)
        if sync_result.get('success'):
            db.update_user(user_id, sync_pending=0)
    
    user = db.get_user(user_id)
    
    socketio.emit('user_updated', format_user_for_response(user), room='admin')
    
    return jsonify({
        "success": True,
        "user": format_user_for_response(user)
    })

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = db.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "Usuário não encontrado"}), 404
    
    if user.get('photo_path') and os.path.exists(user['photo_path']):
        try:
            os.remove(user['photo_path'])
            print(f"[Delete] Foto removida: {user['photo_path']}")
        except Exception as e:
            print(f"[Delete] Erro ao remover foto: {e}")
    
    if user.get('idface_id'):
        if user.get('registration'):
            result = idface.delete_user_alternative(user['registration'])
        else:
            result = idface.delete_user(user['idface_id'])
        print(f"[Delete] IDFace delete: {result}")
    
    db.permanently_delete_user(user_id)
    
    socketio.emit('user_deleted', {"user_id": user_id}, room='admin')
    
    return jsonify({"success": True})

@app.route('/api/users/<int:user_id>/photo')
def get_user_photo(user_id):
    user = db.get_user(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    
    if user.get('photo_path') and os.path.exists(user['photo_path']):
        return send_file(user['photo_path'], mimetype='image/jpeg')
    
    if user.get('photo_base64'):
        try:
            image_data = base64.b64decode(user['photo_base64'])
            return app.response_class(image_data, mimetype='image/jpeg')
        except:
            pass
    
    return jsonify({"error": "Foto não disponível"}), 404

@app.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    user = db.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "Usuário não encontrado"}), 404
    
    new_status = 0 if user.get('active', 0) == 1 else 1
    db.update_user(user_id, active=new_status)
    
    idface_id = user.get('idface_id')
    print(f"[Toggle Status] User {user_id}, name={user.get('name')}, idface_id={idface_id}, new_status={new_status}")
    
    if idface_id:
        try:
            access_rules = idface.get_access_rules()
            release_rule = next((r for r in access_rules if r.get('type') == 1), None)
            
            if release_rule:
                rule_id = release_rule.get('id')
                if new_status == 1:
                    result = idface.set_user_access_rule(int(idface_id), rule_id)
                    print(f"[Toggle Status] Acesso LIBERADO via access_rule {rule_id}: {result}")
                else:
                    result = idface.remove_user_access_rules(int(idface_id))
                    print(f"[Toggle Status] Acesso BLOQUEADO: {result}")
            else:
                print(f"[Toggle Status] Nenhuma access_rule do tipo release encontrada")
        except Exception as e:
            print(f"[Toggle Status] Erro ao sync com IDFace: {e}")
    
    socketio.emit('user_updated', format_user_for_response(db.get_user(user_id)), room='admin')
    
    return jsonify({"success": True, "active": bool(new_status)})

@app.route('/api/users/<int:user_id>/set-idface-id/<int:idface_id>', methods=['POST'])
def set_idface_id(user_id, idface_id):
    user = db.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "Usuário não encontrado"}), 404
    
    db.update_user(user_id, idface_id=idface_id)
    
    return jsonify({"success": True, "idface_id": idface_id})

@app.route('/api/users/<int:user_id>/check-sync', methods=['GET'])
def check_user_sync(user_id):
    print(f"[Check Sync] ========== Verificando usuário ID {user_id} ==========")
    user = db.get_user(user_id)
    if not user:
        print(f"[Check Sync] Usuário não encontrado no banco")
        return jsonify({"success": False, "error": "Usuário não encontrado"}), 404
    
    print(f"[Check Sync] Dados local: name={user.get('name')}, registration={user.get('registration')}, cpf={user.get('cpf')}, idface_id={user.get('idface_id')}, sync_pending={user.get('sync_pending')}")
    
    # Se sync_pending = 1, mostra como pendente
    if user.get('sync_pending') == 1:
        print(f"[Check Sync] Resultado: sync_pending=1 -> Pendente")
        return jsonify({"success": True, "synced": False, "reason": "Alteração pendente"})
    
    if not user.get('idface_id'):
        print(f"[Check Sync] Resultado: SEM idface_id -> Não sincronizado")
        return jsonify({"success": True, "synced": False, "reason": "Sem ID IDFace"})
    
    try:
        if not idface.session or (idface.session_created_at and time.time() - idface.session_created_at > 3600):
            print(f"[Check Sync] Criando sessão IDFace...")
            session_result = idface.create_session()
            if not session_result.get('success'):
                print(f"[Check Sync] FALHA na conexão: {session_result}")
                return jsonify({"success": True, "synced": False, "reason": "Sem conexão IDFace"})
            print(f"[Check Sync] Sessão criada com sucesso")
        
        print(f"[Check Sync] Listando todos usuários do IDFace...")
        all_users = idface.list_users()
        print(f"[Check Sync] Total usuários IDFace: {len(all_users)}")
        
        idface_user = None
        
        # Busca por todos os métodos e verifica se os dados batem
        user_name_lower = user.get('name', '').lower().strip()
        user_reg = str(user.get('registration', '')).strip()
        user_cpf = str(user.get('cpf', '')).strip() if user.get('cpf') else ''
        
        for u in all_users:
            u_id = str(u.get('id', '')).strip()
            u_name = u.get('name', '').lower().strip()
            u_reg = str(u.get('registration', '')).strip()
            u_cpf = str(u.get('cpf', '')).strip() if u.get('cpf') else ''
            
            # Verifica se batem pelo menos 2 campos (ou ID exato)
            matches = 0
            if user.get('idface_id') and u_id == str(user.get('idface_id')):
                matches = 2
            if user_cpf and u_cpf == user_cpf:
                matches += 1
            if user_reg and u_reg == user_reg:
                matches += 1
            if u_name == user_name_lower:
                matches += 1
            
            if matches >= 2:
                idface_user = u
                print(f"[Check Sync] USUÁRIO ENCONTRADO! name={u.get('name')}, matches={matches}")
                break
        
        if idface_user:
            print(f"[Check Sync] Resultado: SINCRONIZADO (verificação robusta passou)")
            return jsonify({"success": True, "synced": True, "idface_id": idface_user.get('id')})
        else:
            print(f"[Check Sync] Resultado: NÃO sincronizado (não encontrou correspondência)")
            return jsonify({"success": True, "synced": False, "reason": "Não encontrado no IDFace"})
    
    except Exception as e:
        print(f"[Check Sync] ERRO: {str(e)}")
        return jsonify({"success": True, "synced": False, "reason": f"Erro: {str(e)}"})

@app.route('/api/users/<int:user_id>/sync', methods=['POST'])
def sync_user(user_id):
    result = sync_user_to_idface(user_id)
    
    if result.get('success'):
        db.update_user(user_id, idface_id=result.get('idface_id'))
    
    return jsonify(result)

@app.route('/api/users/sync-pending', methods=['POST'])
def sync_pending_users():
    force = request.json.get('force', False) if request.json else False
    print(f"[Sync Pending] ========== INICIANDO SYNC PENDENTES (force={force}) ==========")
    users = db.list_users()
    print(f"[Sync Pending] Total usuários: {len(users)}")
    success_count = 0
    error_count = 0
    
    for user in users:
        # Se force=True, sempre sincroniza
        is_pending = force or user.get('sync_pending') == 1 or not user.get('idface_id')
        
        print(f"[Sync Pending] Processando: {user.get('name')} (ID: {user.get('id')}, sync_pending={user.get('sync_pending')}, idface_id={user.get('idface_id')}, is_pending={is_pending})")
        
        if not is_pending:
            # Verifica se realmente existe no IDFace
            result = check_user_sync_internal(user['id'])
            if result.get('synced'):
                print(f"[Sync Pending] {user.get('name')} confirmado no IDFace")
                success_count += 1
            else:
                print(f"[Sync Pending] {user.get('name')} NÃO existe no IDFace, forçando sync...")
                is_pending = True
        
        if is_pending:
            sync_result = sync_user_to_idface(user['id'])
            print(f"[Sync Pending] Resultado: {sync_result}")
            if sync_result.get('success'):
                db.update_user(user['id'], idface_id=sync_result.get('idface_id'), sync_pending=0)
                success_count += 1
                print(f"[Sync Pending] {user.get('name')} sincronizado com sucesso!")
            else:
                error_count += 1
                print(f"[Sync Pending] ERRO: {sync_result.get('error')}")
    
    print(f"[Sync Pending] ========== FIM: {success_count} sucesso, {error_count} erros ==========")
    return jsonify({
        "success": True,
        "success_count": success_count,
        "error_count": error_count
    })

def check_user_sync_internal(user_id):
    user = db.get_user(user_id)
    if not user:
        return {"synced": False}
    
    if not user.get('idface_id'):
        return {"synced": False}
    
    try:
        if not idface.session or (idface.session_created_at and time.time() - idface.session_created_at > 3600):
            idface.create_session()
        
        all_users = idface.list_users()
        
        user_name_lower = user.get('name', '').lower().strip()
        user_reg = str(user.get('registration', '')).strip()
        user_cpf = str(user.get('cpf', '')).strip() if user.get('cpf') else ''
        
        for u in all_users:
            u_id = str(u.get('id', '')).strip()
            u_name = u.get('name', '').lower().strip()
            u_reg = str(u.get('registration', '')).strip()
            u_cpf = str(u.get('cpf', '')).strip() if u.get('cpf') else ''
            
            matches = 0
            if user.get('idface_id') and u_id == str(user.get('idface_id')):
                matches = 2
            if user_cpf and u_cpf == user_cpf:
                matches += 1
            if user_reg and u_reg == user_reg:
                matches += 1
            if u_name == user_name_lower:
                matches += 1
            
            if matches >= 2:
                return {"synced": True}
        
        return {"synced": False}
    except:
        return {"synced": False}

@app.route('/api/users/reset-and-sync', methods=['POST'])
def reset_and_sync():
    try:
        db.clear_all_users()
        
        idface_users = idface.list_users()
        results = []
        
        for idface_user in idface_users:
            uid = str(idface_user.get('id'))
            name = idface_user.get('name', '')
            registration = idface_user.get('registration', '')
            cpf = ''
            
            result = db.add_user(
                name=name,
                registration=registration or '',
                cpf=cpf,
                idface_id=uid
            )
            if result.get('success'):
                results.append({
                    'action': 'created',
                    'name': name,
                    'idface_id': uid
                })
        
        return jsonify({
            "success": True,
            "synced": len(results),
            "details": results
        })
    except Exception as e:
        print(f"[Reset & Sync] Erro: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/users/sync-pending', methods=['POST'])
def sync_pending():
    users = db.list_users()
    results = []
    
    for user in users:
        if not user.get('idface_id') or user.get('idface_id') == '':
            result = sync_user_to_idface(user['id'])
            results.append({
                'user_id': user['id'],
                'name': user['name'],
                'result': result
            })
    
    return jsonify({
        "success": True,
        "synced": len(results),
        "details": results
    })

@app.route('/api/users/sync-all', methods=['POST'])
def sync_all_users():
    results = []
    deleted_from_system = []
    
    try:
        idface_users = idface.list_users()
        system_users = db.list_users(active_only=False)
        
        # Criar conjunto de IDs do IDFace
        idface_ids = set(str(u.get('id')) for u in idface_users)
        
        # Verificar usuários do sistema que têm idface_id e se foram deletados do IDFace
        for system_user in system_users:
            if system_user.get('idface_id'):
                user_idface_id = str(system_user['idface_id'])
                if user_idface_id not in idface_ids:
                    # Usuário foi deletado do IDFace, deletar do sistema
                    print(f"[Sync] Usuário {system_user['name']} (ID {system_user['id']}) foi deletado do IDFace, removendo do sistema...")
                    try:
                        if system_user.get('photo_path') and os.path.exists(system_user['photo_path']):
                            os.remove(system_user['photo_path'])
                    except:
                        pass
                    db.permanently_delete_user(system_user['id'])
                    deleted_from_system.append(system_user['name'])
        
        for idface_user in idface_users:
            uid = str(idface_user.get('id'))
            name = idface_user.get('name', '')
            registration = idface_user.get('registration', '')
            cpf = idface_user.get('cpf', '')
            
            # Verifica se já existe pelo idface_id
            existing_by_idface = next((u for u in system_users if str(u.get('idface_id')) == uid), None)
            if existing_by_idface:
                # Sempre baixa/atualiza a foto do IDFace
                try:
                    photo_bytes = idface.get_user_photo(int(uid))
                    if photo_bytes:
                        photo_data = base64.b64encode(photo_bytes).decode('utf-8')
                        filename = f"{uid}_{int(time.time())}.jpg"
                        photo_path = os.path.join(Config.PHOTOS_FOLDER, filename)
                        
                        # Remove foto antiga se existir
                        if existing_by_idface.get('photo_path') and os.path.exists(existing_by_idface['photo_path']):
                            try:
                                os.remove(existing_by_idface['photo_path'])
                            except:
                                pass
                        
                        with open(photo_path, 'wb') as f:
                            f.write(photo_bytes)
                        db.update_user(existing_by_idface['id'], photo_path=photo_path, photo_base64=photo_data)
                        print(f"[Sync] Foto atualizada para {name}")
                except Exception as e:
                    print(f"[Sync] Erro ao baixar foto: {e}")
                
                results.append({
                    'action': 'exists',
                    'name': name,
                    'idface_id': uid,
                    'photo': True
                })
                continue
            
            # Verifica se já existe pelo CPF
            if cpf:
                existing_by_cpf = next((u for u in system_users if str(u.get('cpf', '')).strip() == str(cpf).strip()), None)
                if existing_by_cpf:
                    # Baixa foto se não existir
                    photo_path = None
                    photo_data = None
                    if not existing_by_cpf.get('photo_path') and not existing_by_cpf.get('photo_base64'):
                        try:
                            photo_bytes = idface.get_user_photo(int(uid))
                            if photo_bytes:
                                photo_data = base64.b64encode(photo_bytes).decode('utf-8')
                                filename = f"{uid}_{int(time.time())}.jpg"
                                photo_path = os.path.join(Config.PHOTOS_FOLDER, filename)
                                with open(photo_path, 'wb') as f:
                                    f.write(photo_bytes)
                        except Exception as e:
                            print(f"[Sync] Erro ao baixar foto: {e}")
                    
                    if photo_data:
                        db.update_user(existing_by_cpf['id'], idface_id=uid, sync_pending=0, photo_path=photo_path, photo_base64=photo_data)
                    else:
                        db.update_user(existing_by_cpf['id'], idface_id=uid, sync_pending=0)
                    results.append({
                        'action': 'linked',
                        'name': name,
                        'idface_id': uid
                    })
                    continue
            
            # Verifica se já existe pela registration
            if registration:
                existing_by_reg = next((u for u in system_users if str(u.get('registration', '')).strip() == str(registration).strip()), None)
                if existing_by_reg:
                    # Baixa foto se não existir
                    if not existing_by_reg.get('photo_path') and not existing_by_reg.get('photo_base64'):
                        try:
                            photo_bytes = idface.get_user_photo(int(uid))
                            if photo_bytes:
                                photo_data = base64.b64encode(photo_bytes).decode('utf-8')
                                filename = f"{uid}_{int(time.time())}.jpg"
                                photo_path = os.path.join(Config.PHOTOS_FOLDER, filename)
                                with open(photo_path, 'wb') as f:
                                    f.write(photo_bytes)
                                db.update_user(existing_by_reg['id'], idface_id=uid, sync_pending=0, photo_path=photo_path, photo_base64=photo_data)
                            else:
                                db.update_user(existing_by_reg['id'], idface_id=uid, sync_pending=0)
                        except Exception as e:
                            print(f"[Sync] Erro ao baixar foto: {e}")
                            db.update_user(existing_by_reg['id'], idface_id=uid, sync_pending=0)
                    else:
                        db.update_user(existing_by_reg['id'], idface_id=uid, sync_pending=0)
                    results.append({
                        'action': 'linked',
                        'name': name,
                        'idface_id': uid
                    })
                    continue
            
            # Cria novo usuário
            photo_data = None
            photo_path = None
            try:
                photo_bytes = idface.get_user_photo(int(uid))
                if photo_bytes:
                    photo_data = base64.b64encode(photo_bytes).decode('utf-8')
                    filename = f"{uid}_{int(time.time())}.jpg"
                    photo_path = os.path.join(Config.PHOTOS_FOLDER, filename)
                    with open(photo_path, 'wb') as f:
                        f.write(photo_bytes)
                    print(f"[Sync] Foto baixada para {name}")
            except Exception as e:
                print(f"[Sync] Erro ao baixar foto: {e}")
            
            result = db.add_user(
                name=name,
                registration=registration or uid,
                cpf=cpf or '',
                idface_id=uid,
                sync_pending=0,
                photo_path=photo_path if photo_data else None,
                photo_base64=photo_data
            )
            if result.get('success'):
                results.append({
                    'action': 'created',
                    'name': name,
                    'idface_id': uid,
                    'photo': bool(photo_data)
                })
            else:
                results.append({
                    'action': 'error',
                    'name': name,
                    'error': result.get('error')
                })
    
    except Exception as e:
        print(f"[Sync] Erro: {e}")
    
    socketio.emit('users_synced', {"count": len(results), "deleted": len(deleted_from_system)}, room='admin')
    
    return jsonify({
        "success": True,
        "synced": len(results),
        "deleted": len(deleted_from_system),
        "details": results
    })

@app.route('/api/users/import-csv', methods=['POST'])
def import_users_csv():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Nenhum arquivo selecionado"}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({"success": False, "error": "Arquivo deve ser CSV"}), 400
    
    try:
        raw_content = file.read()
        
        if raw_content.startswith(b'\xef\xbb\xbf'):
            raw_content = raw_content[3:]
        
        try:
            content = raw_content.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                content = raw_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content = raw_content.decode('latin-1')
                except:
                    content = raw_content.decode('utf-8', errors='replace')
        
        content = content.strip()
        lines = content.split('\n')
        if not lines:
            return jsonify({"success": False, "error": "Arquivo vazio"}), 400
        
        first_line = lines[0]
        if '\t' in first_line:
            delimiter = '\t'
        elif ';' in first_line:
            delimiter = ';'
        else:
            delimiter = ','
        
        reader = csv.DictReader(lines, delimiter=delimiter)
        
        if reader.fieldnames:
            reader.fieldnames = [f.strip().lower() for f in reader.fieldnames]
        
        name_key = next((f for f in reader.fieldnames if 'name' in f.lower() or 'nome' in f.lower()), 'name')
        reg_key = next((f for f in reader.fieldnames if 'registration' in f.lower() or 'matricula' in f.lower() or 'registro' in f.lower()), 'registration')
        cpf_key = next((f for f in reader.fieldnames if 'cpf' in f.lower()), 'cpf')
        
        users_data = []
        for row in reader:
            name = row.get(name_key, '').strip() if name_key else row.get('name', '').strip()
            registration = row.get(reg_key, '').strip() if reg_key else row.get('registration', '').strip()
            cpf = row.get(cpf_key, '').strip() if cpf_key else row.get('cpf', '').strip()
            
            if not name or not registration:
                continue
            
            users_data.append({
                'name': name,
                'registration': registration,
                'cpf': cpf if cpf else None
            })
        
        return jsonify({
            "success": True,
            "count": len(users_data),
            "users": users_data
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/users/batch-create', methods=['POST'])
def batch_create_users():
    data = request.json
    if not data.get('users'):
        return jsonify({"success": False, "error": "Nenhum usuário enviado"}), 400
    
    users_data = data.get('users', [])
    results = []
    success_count = 0
    error_count = 0
    
    for user_data in users_data:
        name = user_data.get('name', '').strip()
        registration = user_data.get('registration', '').strip()
        cpf = user_data.get('cpf', '').strip() if user_data.get('cpf') else None
        photo_base64 = user_data.get('photo')
        
        if not name or not registration:
            results.append({
                'registration': registration,
                'success': False,
                'error': 'Nome e matrícula são obrigatórios'
            })
            error_count += 1
            continue
        
        photo_path = None
        if photo_base64:
            filename = f"{registration}_{int(time.time())}.jpg"
            photo_path = os.path.join(Config.PHOTOS_FOLDER, filename)
            try:
                image_data = base64.b64decode(photo_base64)
                with open(photo_path, 'wb') as f:
                    f.write(image_data)
            except Exception as e:
                print(f"Erro ao salvar foto: {e}")
                photo_path = None
        
        result = db.add_user(
            name=name,
            registration=registration,
            cpf=cpf,
            photo_path=photo_path,
            photo_base64=photo_base64
        )
        
        if not result.get('success'):
            results.append({
                'registration': registration,
                'name': name,
                'success': False,
                'error': result.get('error', 'Erro ao criar usuário')
            })
            error_count += 1
            continue
        
        user_id = result['user_id']
        
        sync_result = sync_user_to_idface(user_id)
        if sync_result.get('success'):
            db.update_user(user_id, idface_id=sync_result.get('idface_id'), sync_pending=0)
        
        results.append({
            'registration': registration,
            'name': name,
            'success': True,
            'user_id': user_id,
            'synced': True
        })
        success_count += 1
    
    socketio.emit('batch_import_completed', {
        'success': success_count,
        'errors': error_count
    }, room='admin')
    
    return jsonify({
        "success": True,
        "total": len(users_data),
        "success_count": success_count,
        "error_count": error_count,
        "results": results
    })

@app.route('/api/presence/today')
def presence_today():
    result = db.get_presence_today()
    presence = result.get('presence', []) if isinstance(result, dict) else result
    stats = db.get_presence_stats()
    
    return jsonify({
        "success": True,
        "date": datetime.now().strftime('%Y-%m-%d'),
        "presence": [format_presence_for_response(p) for p in presence],
        "stats": stats
    })

@app.route('/api/presence/recent')
def presence_recent():
    limit = request.args.get('limit', 50, type=int)
    presence = db.get_recent_presence(limit)
    
    return jsonify({
        "success": True,
        "presence": [format_presence_for_response(p) for p in presence]
    })

@app.route('/api/presence/date/<date>')
def presence_by_date(date):
    presence = db.get_presence_by_date(date)
    
    return jsonify({
        "success": True,
        "date": date,
        "presence": [format_presence_for_response(p) for p in presence]
    })

@app.route('/api/presence/stats')
def presence_stats():
    stats = db.get_presence_stats()
    return jsonify({
        "success": True,
        "stats": stats
    })

@app.route('/api/idface/webhook/new_user_info', methods=['POST'])
def webhook_new_user():
    data = request.json
    
    user_id = data.get('user_id')
    device_id = data.get('device_id')
    identifier_id = data.get('identifier_id')
    timestamp = data.get('date_time')
    
    user = db.get_user_by_idface_id(user_id)
    
    if not user:
        user = db.get_user_by_registration(str(user_id))
    
    if user:
        is_active = bool(user.get('active', 0)) == 1
        
        if is_active:
            db.add_presence_log(
                user_id=user['id'],
                idface_id=user_id,
                device_id=device_id,
                identifier_type=str(identifier_id) if identifier_id else None,
                result=7,
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
    else:
        return jsonify({
            "result": 6,
            "display_message": "Usuário não cadastrado",
            "user_image": False
        })

@app.route('/device_is_alive.fcgi', methods=['POST'])
def device_is_alive():
    device_id = request.args.get('device_id')
    socketio.emit('device_heartbeat', {
        "device_id": device_id,
        "timestamp": datetime.now().isoformat()
    }, room='admin')
    return jsonify({"success": True, "code": 0})

@app.route('/new_user_identified.fcgi/device_is_alive', methods=['POST'])
def idface_device_is_alive():
    socketio.emit('device_heartbeat', {
        "timestamp": datetime.now().isoformat()
    }, room='admin')
    return jsonify({"success": True, "code": 0})

@app.route('/new_user_identified.fcgi/dao', methods=['POST'])
def idface_dao():
    return jsonify({"success": True, "code": 0})

@app.route('/api/idface/webhook/device_alive', methods=['POST'])
def webhook_device_alive():
    socketio.emit('device_heartbeat', request.json, room='admin')
    return jsonify({"connected": True})

@app.route('/push', methods=['GET', 'POST'])
def push_callback():
    return jsonify({"success": True})

@app.route('/192.168.0.6:5000/push_server.fcgi/<path:subpath>', methods=['GET', 'POST'])
def push_server_wrong(subpath):
    return jsonify({"success": True})

@app.route('/http://192.168.0.100:5000/push_server.fcgi/<path:subpath>', methods=['GET', 'POST'])
@app.route('/<path:subpath>', methods=['GET', 'POST'])
def push_server_catchall(subpath):
    if 'push_server' in subpath or 'new_user' in subpath or 'device_is_alive' in subpath:
        try:
            data = request.get_json(force=True, silent=True) or {}
            print(f"[IDFace Push] {subpath}: {data}")
            
            object_changes = data.get('object_changes', [])
            for change in object_changes:
                if change.get('type') == 'inserted':
                    values = change.get('values', {})
                    log_id = int(values.get('id', 0))
                    event_type = int(values.get('event', 0))
                    user_id = int(values.get('user_id', 0))
                    timestamp = int(values.get('time', 0))
                    
                    dt = datetime.fromtimestamp(timestamp)
                    timestamp_str = dt.isoformat()
                    
                    recognition_data = {
                        "user_id": user_id if user_id else None,
                        "name": "",
                        "registration": "",
                        "active": False,
                        "timestamp": timestamp_str,
                        "created_at": datetime.now().isoformat(),
                        "event_type": event_type
                    }
                    
                    event_description = get_event_description(event_type)
                    recognition_data["event_description"] = event_description
                    
                    if event_type == 3 or user_id == 0:
                        recognition_data["name"] = "Não Reconhecido"
                        recognition_data["not_recognized"] = True
                        recognition_data["blocked"] = False
                    elif event_type == 6:
                        recognition_data["name"] = f"Usuário Bloqueado"
                        recognition_data["blocked"] = True
                        recognition_data["not_recognized"] = False
                    elif user_id and event_type == 7:
                        user = db.get_user_by_cpf(str(user_id))
                        if not user:
                            user = db.get_user_by_idface_id(user_id)
                        if not user:
                            user = db.get_user_by_registration(str(user_id))
                        
                        if user:
                            is_active = bool(user.get('active', 0)) == 1
                            recognition_data["user_id"] = user['id']
                            recognition_data["name"] = user['name']
                            recognition_data["registration"] = user['registration']
                            recognition_data["active"] = is_active
                            recognition_data["blocked"] = False
                            
                            if is_active:
                                db.add_presence_log(
                                    user_id=user['id'],
                                    idface_id=user_id,
                                    device_id=0,
                                    identifier_type="face",
                                    result=7,
                                    timestamp=timestamp
                                )
                                
                                presence_data = format_presence_for_response({
                                    **user,
                                    "timestamp": timestamp_str,
                                    "created_at": datetime.now().isoformat()
                                })
                                
                                socketio.emit('presence_detected', presence_data, room='admin')
                                idface.open_door(0)
                        else:
                            recognition_data["name"] = f"Usuário {user_id}"
                            recognition_data["registration"] = str(user_id)
                            recognition_data["not_found"] = True
                    else:
                        recognition_data["name"] = f"Evento {event_type}"
                    
                    socketio.emit('recognition_detected', recognition_data, room='admin')
            
        except Exception as e:
            print(f"[IDFace Push] Erro: {e}")
    
    return jsonify({"success": True})

@app.route('/push_server.fcgi/push', methods=['GET', 'POST'])
def push_server_push():
    device_id = request.args.get('deviceId')
    uuid = request.args.get('uuid')
    print(f"[IDFace Push] Push received - deviceId: {device_id}, uuid: {uuid}")
    return jsonify({"code": 0, "endpoint": "/push_server.fcgi/result"})

@app.route('/push_server.fcgi/result', methods=['POST'])
def push_server_result():
    device_id = request.args.get('deviceId')
    uuid = request.args.get('uuid')
    
    data = {}
    try:
        data = request.get_json(force=True) or {}
    except:
        pass
    
    print(f"[IDFace Result] Received data: {data}")
    
    user_id = data.get('user_id') or data.get('userId')
    event = data.get('event') or data.get('type')
    
    if user_id:
        recognition_data = {
            "user_id": int(user_id) if user_id else None,
            "event_type": int(event) if event else 7,
            "name": "",
            "registration": "",
            "active": False,
            "timestamp": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        user = db.get_user_by_cpf(str(user_id))
        if not user:
            user = db.get_user_by_idface_id(user_id)
        if not user:
            user = db.get_user_by_registration(str(user_id))
        
        if user:
            recognition_data["user_id"] = user['id']
            recognition_data["name"] = user['name']
            recognition_data["registration"] = user['registration']
            recognition_data["active"] = bool(user.get('active', 0)) == 1
            recognition_data["event_description"] = "Face reconhecida"
            
            if recognition_data["active"]:
                db.add_presence_log(
                    user_id=user['id'],
                    idface_id=str(user_id),
                    device_id=device_id,
                    identifier_type="face",
                    result=7,
                    timestamp=int(time.time())
                )
                socketio.emit('presence_detected', format_presence_for_response({**user, "timestamp": datetime.now().isoformat(), "created_at": datetime.now().isoformat()}), room='admin')
        else:
            recognition_data["name"] = "Não Reconhecido"
            recognition_data["not_recognized"] = True
            recognition_data["event_description"] = "Face não reconhecida"
        
        socketio.emit('recognition_detected', recognition_data, room='admin')
    
    return jsonify({"code": 0, "endpoint": "/push_server.fcgi/result"})

@app.route('/push_server.fcgi', methods=['POST'])
def push_server_callback():
    data = request.json or {}
    print(f"[Push Server] Received: {data}")
    
    user_id = data.get('user_id')
    device_id = data.get('device_id')
    identifier_type = data.get('identifier_type')
    result = data.get('result')
    timestamp = data.get('timestamp') or data.get('date_time')
    
    if user_id:
        user = db.get_user_by_cpf(str(user_id))
        if not user:
            user = db.get_user_by_idface_id(user_id)
        if not user:
            user = db.get_user_by_registration(str(user_id))
        
        if user:
            is_active = bool(user.get('active', 0)) == 1
            
            recognition_data = {
                "user_id": user['id'],
                "name": user['name'],
                "registration": user['registration'],
                "active": is_active,
                "timestamp": timestamp or datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            socketio.emit('recognition_detected', recognition_data, room='admin')
            
            if is_active:
                db.add_presence_log(
                    user_id=user['id'],
                    idface_id=str(user_id),
                    device_id=device_id,
                    identifier_type=str(identifier_type) if identifier_type else None,
                    result=result,
                    timestamp=timestamp
                )
                
                presence_data = format_presence_for_response({
                    **user,
                    "timestamp": timestamp,
                    "created_at": datetime.now().isoformat()
                })
                
                socketio.emit('presence_detected', presence_data, room='admin')
                
                idface.open_door(0)
                
                return jsonify({"success": True, "action": "open_door"})
            else:
                return jsonify({"success": True, "action": "deny"})
        else:
            return jsonify({"success": True, "action": "not_found"})
    
    return jsonify({"success": True})

@app.route('/api/idface/webhook/operation_mode', methods=['POST'])
def webhook_operation_mode():
    return jsonify({"code": 0, "message": "OK"})

@app.route('/api/idface/webhook/dao', methods=['POST'])
def webhook_dao():
    return jsonify({"code": 0, "message": "OK"})

@app.route('/new_user_identified.fcgi', methods=['POST'])
def new_user_identified():
    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get('user_id')
    device_id = data.get('device_id')
    timestamp = data.get('date_time')
    
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
                identifier_type=None,
                result=7,
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

@app.route('/api/idface/webhook/user_image', methods=['GET'])
def webhook_user_image():
    user_id = request.args.get('user_id', type=int)
    
    if not user_id:
        return "", 404
    
    user = db.get_user(user_id)
    
    if not user:
        user = db.get_user_by_idface_id(user_id)
    
    if not user:
        return "", 404
    
    if user.get('photo_path') and os.path.exists(user['photo_path']):
        return send_file(user['photo_path'], mimetype='image/jpeg')
    
    if user.get('photo_base64'):
        try:
            image_data = base64.b64decode(user['photo_base64'])
            return app.response_class(image_data, mimetype='image/jpeg')
        except:
            pass
    
    return "", 404

@socketio.on('connect')
def handle_connect():
    print(f"Cliente conectado: {request.sid}")
    join_room('admin')

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Cliente desconectado: {request.sid}")

@socketio.on('subscribe')
def handle_subscribe(data):
    room = data.get('room', 'admin')
    join_room(room)
    emit('subscribed', {'room': room})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 50)
    print("  IDFace Sistema de Presença")
    print("=" * 50)
    print(f"\n  API Server: http://localhost:{port}")
    print(f"  WebSocket: ws://localhost:{port}")
    print(f"\n  Endpoints principais:")
    print(f"  - GET  /api/users - Listar usuários")
    print(f"  - POST /api/users - Cadastrar usuário")
    print(f"  - GET  /api/presence/today - Presença de hoje")
    print(f"\n  Configuração IDFace:")
    print(f"  - IP: {Config.IDFACE_IP}")
    print(f"  - User: {Config.IDFACE_USER}")
    print("=" * 50)
    
    start_polling()
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
