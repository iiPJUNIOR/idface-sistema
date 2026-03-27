from idface_client import IDFaceClient
from typing import Dict, Any, List, Optional
import time

class IDFaceManager:
    def __init__(self, db):
        self.db = db
        self._clients_cache: Dict[int, IDFaceClient] = {}
        self._cache_time: Dict[int, float] = {}
        self._cache_ttl = 300
    
    def _get_client(self, device_id: int) -> Optional[IDFaceClient]:
        now = time.time()
        
        if device_id in self._clients_cache:
            if now - self._cache_time.get(device_id, 0) < self._cache_ttl:
                return self._clients_cache[device_id]
        
        device = self.db.get_device(device_id)
        if not device or not device.get('active'):
            return None
        
        client = IDFaceClient(
            ip=device['ip'],
            port=device['port'],
            user=device['user'],
            password=device['password']
        )
        
        self._clients_cache[device_id] = client
        self._cache_time[device_id] = now
        
        return client
    
    def get_client(self, device_id: int) -> Optional[IDFaceClient]:
        return self._get_client(device_id)
    
    def get_all_active_devices(self) -> List[Dict]:
        return self.db.get_active_devices()
    
    def test_connection(self, ip: str, port: int, user: str, password: str) -> Dict[str, Any]:
        client = IDFaceClient(ip=ip, port=port, user=user, password=password)
        result = client.test_connection()
        return result
    
    def sync_user_to_device(self, user: Dict, device_id: int) -> Dict[str, Any]:
        client = self._get_client(device_id)
        if not client:
            return {"success": False, "error": "Dispositivo não encontrado ou inativo"}
        
        return self._sync_user_to_client(user, client)
    
    def sync_user_to_all_devices(self, user: Dict) -> Dict[str, Any]:
        devices = self.get_all_active_devices()
        results = []
        
        for device in devices:
            result = self.sync_user_to_device(user, device['id'])
            results.append({
                "device_id": device['id'],
                "device_name": device['name'],
                "result": result
            })
        
        success_count = sum(1 for r in results if r['result'].get('success'))
        
        return {
            "success": success_count > 0,
            "total_devices": len(devices),
            "success_count": success_count,
            "results": results
        }
    
    def _sync_user_to_client(self, user: Dict, client: IDFaceClient) -> Dict[str, Any]:
        user_id = user.get('id')
        cpf = str(user.get('cpf', '')).strip() if user.get('cpf') else ''
        registration = str(user.get('registration', '')).strip()
        name = user.get('name', '')
        photo_path = user.get('photo_path')
        photo_base64 = user.get('photo_base64')
        
        existing = None
        all_users = client.list_users()
        
        for u in all_users:
            if cpf and str(u.get('id')) == cpf:
                existing = u
                break
            if registration and str(u.get('registration', '')).strip() == registration:
                existing = u
                break
        
        if existing:
            idface_id = existing.get('id')
            
            idface_name = existing.get('name', '').strip()
            if idface_name.lower() != name.lower().strip():
                client.update_user(int(idface_id), name=name, registration=registration)
            
            if photo_path or photo_base64:
                photo_id = int(idface_id) if idface_id else int(cpf) if cpf else None
                if photo_id:
                    if photo_path:
                        result = client.upload_face_photo_from_file(photo_id, photo_path)
                    else:
                        result = client.upload_face_photo(photo_id, photo_base64)
                    if result.get('success'):
                        return {"success": True, "action": "photo_updated", "idface_id": idface_id}
            
            return {"success": True, "action": "updated", "idface_id": idface_id}
        
        create_result = client.create_user(
            name=name,
            registration=registration,
            cpf=cpf
        )
        
        if not create_result.get('success'):
            return {"success": False, "error": create_result.get('error')}
        
        idface_id = create_result.get('user_id')
        
        if photo_path or photo_base64:
            photo_id = int(cpf) if cpf else int(idface_id)
            if photo_path:
                result = client.upload_face_photo_from_file(photo_id, photo_path)
            else:
                result = client.upload_face_photo(photo_id, photo_base64)
        
        return {"success": True, "action": "created", "idface_id": idface_id}
    
    def delete_user_from_device(self, user_id: int, device_id: int) -> Dict[str, Any]:
        client = self._get_client(device_id)
        if not client:
            return {"success": False, "error": "Dispositivo não encontrado"}
        
        result = client.delete_user(user_id)
        return result
    
    def delete_user_from_all_devices(self, idface_id: int) -> Dict[str, Any]:
        devices = self.get_all_active_devices()
        results = []
        
        for device in devices:
            result = self.delete_user_from_device(idface_id, device['id'])
            results.append({
                "device_id": device['id'],
                "device_name": device['name'],
                "result": result
            })
        
        return {
            "success": True,
            "results": results
        }
    
    def clear_cache(self, device_id: int = None):
        if device_id:
            self._clients_cache.pop(device_id, None)
            self._cache_time.pop(device_id, None)
        else:
            self._clients_cache.clear()
            self._cache_time.clear()
