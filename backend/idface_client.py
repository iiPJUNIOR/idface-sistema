import requests
import base64
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import Config


class IDFaceClient:
    def __init__(self, ip: str = None, username: str = None, password: str = None):
        self.base_url = f"http://{ip or Config.IDFACE_IP}:{Config.IDFACE_PORT}"
        self.username = username or Config.IDFACE_USER
        self.password = password or Config.IDFACE_PASSWORD
        self.session = None
        self.session_created_at = None
        self.cookies = None
        
    def _make_url(self, endpoint: str) -> str:
        return f"{self.base_url}{endpoint}"
    
    def _get_session_param(self) -> str:
        if not self.session:
            self.create_session()
        return f"session={self.session}"
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest"
        }
    
    def create_session(self) -> Dict[str, Any]:
        try:
            login_url = self._make_url("/login.fcgi")
            
            response = requests.post(
                login_url, 
                data={
                    "login": self.username,
                    "password": self.password
                },
                headers={
                    "X-Requested-With": "XMLHttpRequest"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("session"):
                    self.session = data.get("session")
                    self.cookies = response.cookies
                    self.session_created_at = time.time()
                    print(f"[IDFace] Sessão criada. Session: {self.session[:20]}...")
                    return {"success": True, "session": self.session}
                else:
                    print(f"[IDFace] Falha ao criar sessão: {data}")
                    return {"success": False, "error": data.get("error", "No session")}
            else:
                print(f"[IDFace] Falha ao criar sessão: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            print(f"[IDFace] Erro ao conectar: {e}")
            return {"success": False, "error": str(e)}
    
    def refresh_session(self):
        self.session = None
        return self.create_session()
    
    def get_user_by_registration(self, registration: str) -> Optional[Dict]:
        url = f"{self._make_url('/load_objects.fcgi')}?{self._get_session_param()}"
        
        payload = {
            "object": "users",
            "filter": {"registration": registration}
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            users = response.json().get("users", [])
            
            if users:
                return users[0]
            return None
            
        except Exception as e:
            print(f"[IDFace] Erro ao buscar usuário: {e}")
            return None
    
    def get_user_by_cpf(self, cpf: str) -> Optional[Dict]:
        url = f"{self._make_url('/load_objects.fcgi')}?{self._get_session_param()}"
        
        payload = {
            "object": "users",
            "filter": {"id": cpf}
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            users = response.json().get("users", [])
            
            if users:
                return users[0]
            return None
            
        except Exception as e:
            print(f"[IDFace] Erro ao buscar usuário por CPF: {e}")
            return None
    
    def create_user(self, name: str, registration: str, cpf: str = None) -> Dict[str, Any]:
        url = f"{self._make_url('/create_objects.fcgi')}?{self._get_session_param()}"
        
        values = {
            "name": name,
            "registration": registration
        }
        
        if cpf:
            values["id"] = int(cpf)
        
        payload = {
            "object": "users",
            "values": [values]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            
            if data.get("ids"):
                user_id = data["ids"][0]
                print(f"[IDFace] Usuário criado com ID: {user_id}")
                return {"success": True, "user_id": user_id}
            else:
                print(f"[IDFace] Falha ao criar usuário: {data}")
                return {"success": False, "error": data}
                
        except Exception as e:
            print(f"[IDFace] Erro ao criar usuário: {e}")
            return {"success": False, "error": str(e)}
    
    def upload_face_photo(self, user_id: int, image_base64: str) -> Dict[str, Any]:
        url = f"{self._make_url('/user_set_image.fcgi')}?{self._get_session_param()}&user_id={user_id}&match=0&timestamp={int(time.time())}"
        
        try:
            response = requests.post(url, data=image_base64.encode(), headers={"Content-Type": "image/jpeg"}, timeout=30)
            data = response.json()
            
            if data.get("success"):
                print(f"[IDFace] Foto enviada com sucesso para usuário {user_id}")
                return {"success": True}
            else:
                print(f"[IDFace] Falha ao enviar foto: {data}")
                return {"success": False, "error": data}
                
        except Exception as e:
            print(f"[IDFace] Erro ao enviar foto: {e}")
            return {"success": False, "error": str(e)}
    
    def upload_face_photo_from_file(self, user_id: int, image_path: str) -> Dict[str, Any]:
        url = f"{self._make_url('/user_set_image.fcgi')}?session={self.session}&user_id={user_id}&match=1&timestamp={int(time.time())}"
        
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            response = requests.post(url, data=image_data, headers={"Content-Type": "application/octet-stream"}, timeout=30)
            print(f"[IDFace] Upload response: {response.status_code} - {response.text}")
            data = response.json()
            
            if data.get("success"):
                print(f"[IDFace] Foto enviada com sucesso para usuário {user_id}")
                return {"success": True}
            else:
                print(f"[IDFace] Falha ao enviar foto: {data}")
                return {"success": False, "error": data}
                
        except Exception as e:
            print(f"[IDFace] Erro ao enviar foto: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        url = f"{self._make_url('/destroy_objects.fcgi')}?{self._get_session_param()}"
        
        payload = {
            "object": "users",
            "ids": [user_id]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            
            if data.get("success") or data.get("ids"):
                print(f"[IDFace] Usuário {user_id} removido com sucesso")
                return {"success": True}
            else:
                return {"success": False, "error": data}
                
        except Exception as e:
            print(f"[IDFace] Erro ao remover usuário: {e}")
            return {"success": False, "error": str(e)}
    
    def set_user_status(self, user_id: int, active: bool) -> Dict[str, Any]:
        url = f"{self._make_url('/set_objects.fcgi')}?{self._get_session_param()}"
        
        status_value = 1 if active else 0
        
        payload = {
            "object": "users",
            "where": [{"object": "users", "field": "id", "value": user_id}],
            "values": {
                "active": status_value
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            
            if data.get("success"):
                print(f"[IDFace] Usuário {user_id} {'ativado' if active else 'bloqueado'} com sucesso")
                return {"success": True}
            else:
                print(f"[IDFace] Falha ao alterar status: {data}")
                return {"success": False, "error": data}
                
        except Exception as e:
            print(f"[IDFace] Erro ao alterar status: {e}")
            return {"success": False, "error": str(e)}
    
    def get_user_status(self, user_id: int) -> Optional[bool]:
        url = f"{self._make_url('/load_objects.fcgi')}?{self._get_session_param()}"
        
        payload = {
            "object": "users",
            "filter": {"id": user_id}
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            users = data.get("users", [])
            
            if users:
                active = users[0].get("active", 1)
                return bool(active)
            return None
            
        except Exception as e:
            print(f"[IDFace] Erro ao buscar status: {e}")
            return None
    
    def get_access_rules(self) -> List[Dict]:
        url = f"{self._make_url('/load_objects.fcgi')}?{self._get_session_param()}"
        
        payload = {"object": "access_rules"}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            return data.get("access_rules", [])
        except Exception as e:
            print(f"[IDFace] Erro ao buscar access_rules: {e}")
            return []
    
    def get_user_access_rules(self, user_id: int) -> List[Dict]:
        url = f"{self._make_url('/load_objects.fcgi')}?{self._get_session_param()}"
        
        payload = {
            "object": "user_access_rules",
            "filter": {"user_id": user_id}
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            return data.get("user_access_rules", [])
        except Exception as e:
            print(f"[IDFace] Erro ao buscar user_access_rules: {e}")
            return []
    
    def set_user_access_rule(self, user_id: int, access_rule_id: int) -> Dict[str, Any]:
        url = f"{self._make_url('/create_objects.fcgi')}?{self._get_session_param()}"
        
        payload = {
            "object": "user_access_rules",
            "values": [{
                "user_id": user_id,
                "access_rule_id": access_rule_id
            }]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            
            if data.get("ids"):
                return {"success": True, "id": data["ids"][0]}
            else:
                return {"success": False, "error": data}
        except Exception as e:
            print(f"[IDFace] Erro ao vincular access_rule: {e}")
            return {"success": False, "error": str(e)}
    
    def remove_user_access_rules(self, user_id: int) -> Dict[str, Any]:
        url = f"{self._make_url('/load_objects.fcgi')}?{self._get_session_param()}"
        
        payload = {
            "object": "user_access_rules",
            "filter": {"user_id": user_id}
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            rules = data.get("user_access_rules", [])
            
            if not rules:
                return {"success": True}
            
            ids = [r.get("id") for r in rules if r.get("id")]
            
            if ids:
                delete_url = f"{self._make_url('/destroy_objects.fcgi')}?{self._get_session_param()}"
                delete_payload = {"object": "user_access_rules", "ids": ids}
                delete_response = requests.post(delete_url, json=delete_payload, timeout=10)
                delete_data = delete_response.json()
                
                if delete_data.get("success"):
                    return {"success": True}
            
            return {"success": False, "error": "Failed to delete"}
        except Exception as e:
            print(f"[IDFace] Erro ao remover user_access_rules: {e}")
            return {"success": False, "error": str(e)}
    
    def list_users(self) -> List[Dict]:
        url = f"{self._make_url('/load_objects.fcgi')}?{self._get_session_param()}"
        
        payload = {"object": "users"}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            return data.get("users", [])
        except Exception as e:
            print(f"[IDFace] Erro ao listar usuários: {e}")
            return []
    
    def open_door(self, door: int = 0) -> Dict[str, Any]:
        if not self.session:
            session_result = self.create_session()
            if not session_result.get("success"):
                return {"success": False, "error": "Falha ao criar sessão"}
        
        url = self._make_url(f"/execute_actions.fcgi?session={self.session}")
        
        payload = {
            "actions": [
                {
                    "action": "sec_box",
                    "parameters": f"id={door}, reason=3"
                }
            ]
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=10
            )
            
            print(f"[IDFace] Resposta abrir porta: {response.text}")
            return {"success": True, "response": response.json()}
        except Exception as e:
            print(f"[IDFace] Erro ao abrir porta: {e}")
            return {"success": False, "error": str(e)}
    
    def ping(self) -> bool:
        try:
            response = requests.post(
                self._make_url("/login.fcgi"),
                data={"login": self.username, "password": self.password},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        result = {
            "connected": False,
            "session": False,
            "message": ""
        }
        
        if not self.ping():
            result["message"] = "Não foi possível conectar ao IDFace"
            return result
        
        result["connected"] = True
        
        session_result = self.create_session()
        if session_result.get("success"):
            result["session"] = True
            result["message"] = "Conexão estabelecida com sucesso!"
        else:
            result["message"] = f"Falha ao criar sessão: {session_result.get('error')}"
        
        return result
    
    def get_access_logs(self, limit: int = 10) -> List[Dict]:
        if not self.session:
            session_result = self.create_session()
            if not session_result.get("success"):
                print("[IDFace] Sem sessão, não foi possível buscar logs")
                return []
        
        url = f"{self._make_url('/load_objects.fcgi')}?session={self.session}"
        
        payload = {
            "object": "access_logs"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            print(f"[IDFace] Access logs status: {response.status_code}")
            data = response.json()
            print(f"[IDFace] Access logs raw response: {data}")
            
            if "ac_records" in data:
                return data["ac_records"]
            elif "users" in data:
                return data["users"]
            elif isinstance(data, list):
                return data
            return []
        except Exception as e:
            print(f"[IDFace] Erro ao buscar logs: {e}")
            return []
    
    def get_alarm_logs(self, limit: int = 10) -> List[Dict]:
        url = f"{self._make_url('/load_objects.fcgi')}?{self._get_session_param()}"
        
        payload = {
            "object": "alarm_logs",
            "limit": limit
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            
            if "alarm_logs" in data:
                return data["alarm_logs"]
            elif isinstance(data, list):
                return data
            return []
        except Exception as e:
            print(f"[IDFace] Erro ao buscar alarm logs: {e}")
            return []
    
    def get_access_logs_v2(self, since_timestamp: int = None) -> List[Dict]:
        if not self.session:
            session_result = self.create_session()
            if not session_result.get("success"):
                return []
        
        url = f"{self._make_url('/load_objects.fcgi')}?session={self.session}"
        
        if since_timestamp is None:
            since_timestamp = int(time.time()) - 60
        
        payload = {
            "join": "LEFT",
            "object": "access_logs",
            "fields": ["id", "time", "user_id", "portal_id", "log_type_id", "event"],
            "where": [{"field": "time", "value": since_timestamp, "operator": ">"}],
            "order": ["time", "descending"],
            "limit": 20,
            "finish": True,
            "offset": 0
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            
            if isinstance(data, dict):
                if "access_logs" in data:
                    return data["access_logs"]
                elif "ac_records" in data:
                    return data["ac_records"]
                elif "records" in data:
                    return data["records"]
            elif isinstance(data, list):
                return data
            
            print(f"[IDFace] access_logs response keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
            return []
        except Exception as e:
            print(f"[IDFace] Erro ao buscar access_logs: {e}")
            return []
    
    def get_ac_log(self) -> List[Dict]:
        logs = self.get_access_logs_v2()
        if not logs:
            logs = self.get_ac_log_fcgi()
        return logs
    
    def get_ac_log_fcgi(self) -> List[Dict]:
        if not self.session:
            session_result = self.create_session()
            if not session_result.get("success"):
                return []
        
        url = self._make_url(f"/get_ac_log.fcgi?session={self.session}")
        
        try:
            response = requests.post(url, timeout=10)
            print(f"[IDFace] get_ac_log.fcgi response status: {response.status_code}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, dict) and "ac_log" in data:
                        return data["ac_log"]
                    elif isinstance(data, list):
                        return data
                except:
                    pass
            return []
        except Exception as e:
            print(f"[IDFace] Erro ao buscar ac_log.fcgi: {e}")
            return []
    
    def get_online_log(self) -> List[Dict]:
        if not self.session:
            session_result = self.create_session()
            if not session_result.get("success"):
                return []
        
        url = f"{self._make_url('/load_objects.fcgi')}?session={self.session}"
        
        payload = {
            "object": "records"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            print(f"[IDFace] records response: {data}")
            return data if isinstance(data, list) else []
        except Exception as e:
            print(f"[IDFace] Erro ao buscar records: {e}")
            return []
    
    def get_user_records(self, user_id: int = None) -> List[Dict]:
        if not self.session:
            session_result = self.create_session()
            if not session_result.get("success"):
                return []
        
        url = f"{self._make_url('/load_objects.fcgi')}?session={self.session}"
        
        if user_id:
            payload = {
                "object": "users",
                "filter": {"id": user_id}
            }
        else:
            payload = {"object": "users"}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            data = response.json()
            users = data.get("users", [])
            
            records = []
            for user in users:
                last_access = user.get("last_access") or user.get("last_login")
                if last_access:
                    records.append({
                        "id": user.get("id"),
                        "user_id": user.get("id"),
                        "name": user.get("name"),
                        "last_access": last_access
                    })
            
            print(f"[IDFace] user records: {records}")
            return records
        except Exception as e:
            print(f"[IDFace] Erro ao buscar user records: {e}")
            return []
