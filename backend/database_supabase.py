import os
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any
import base64

class DatabaseSupabase:
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL', 'https://qtqofigtjlykzksexvmf.supabase.co')
        self.key = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF0cW9maWd0amx5a3prc2V4dm1mIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ0ODA0NzMsImV4cCI6MjA5MDA1NjQ3M30.LrllHp3wImVxIci4EhWKx8E49GrYKMronHOqrsJ3poI')
        self.headers = {
            'apikey': self.key,
            'Authorization': f'Bearer {self.key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
    
    def _request(self, method: str, path: str, data: dict = None, params: dict = None):
        url = f"{self.url}/rest/v1/{path}"
        response = requests.request(method, url, json=data, headers=self.headers, params=params)
        if response.status_code >= 400:
            print(f"Supabase error: {response.status_code} - {response.text}")
            return None
        return response.json() if response.text else None
    
    def init_db(self):
        pass
    
    # USERS
    def list_users(self, active_only: bool = True):
        query = "users?order=created_at.desc"
        if active_only:
            query += "&active=eq.1"
        result = self._request('GET', query)
        return result or []
    
    def get_user(self, user_id: int):
        result = self._request('GET', f"users?id=eq.{user_id}&limit=1")
        return result[0] if result else None
    
    def get_user_by_cpf(self, cpf: str):
        result = self._request('GET', f"users?cpf=eq.{cpf}&limit=1")
        return result[0] if result else None
    
    def get_user_by_registration(self, registration: str):
        result = self._request('GET', f"users?registration=eq.{registration}&limit=1")
        return result[0] if result else None
    
    def get_user_by_idface_id(self, idface_id: str):
        result = self._request('GET', f"users?idface_id=eq.{idface_id}&limit=1")
        return result[0] if result else None
    
    def add_user(self, name: str, registration: str, cpf: str = None, 
                  idface_id: str = None, photo_path: str = None, photo_base64: str = None,
                  sync_pending: int = 0) -> Dict[str, Any]:
        data = {
            'name': name,
            'registration': registration,
        }
        
        if cpf:
            data['cpf'] = cpf
        if idface_id:
            data['idface_id'] = int(idface_id)
        if photo_base64:
            data['photo_base64'] = photo_base64
        if photo_path:
            data['photo_path'] = photo_path
            
        data['active'] = 1
        data['sync_pending'] = sync_pending
        data['created_at'] = datetime.now().isoformat()
        data['updated_at'] = datetime.now().isoformat()
        
        result = self._request('POST', 'users', data)
        if result:
            return {'success': True, 'user_id': result[0].get('id')}
        return {'success': False, 'error': 'Failed to create user'}
    
    def update_user(self, user_id: int, **kwargs):
        kwargs['updated_at'] = datetime.now().isoformat()
        for key in ['cpf', 'idface_id', 'photo_path', 'photo_base64', 'name', 'registration', 'active', 'sync_pending']:
            if key in kwargs and kwargs[key] is None:
                kwargs[key] = ''
        result = self._request('PATCH', f"users?id=eq.{user_id}", kwargs)
        return {'success': result is not None}
    
    def delete_user(self, user_id: int):
        self._request('DELETE', f"users?id=eq.{user_id}")
        return {'success': True}
    
    def permanently_delete_user(self, user_id: int):
        return self.delete_user(user_id)
    
    # PRESENCE LOGS
    def add_presence_log(self, user_id: int, name: str = None, registration: str = None,
                         idface_id: int = None, device_id: int = None, 
                         identifier_type: str = None, result: str = None):
        data = {
            'user_id': user_id,
            'name': str(name) if name else '',
            'registration': str(registration) if registration else '',
            'timestamp': datetime.now().isoformat(),
            'entries_count': 1
        }
        self._request('POST', 'presence_logs', data)
    
    def get_presence_today(self):
        today = datetime.now().strftime('%Y-%m-%d')
        result = self._request('GET', f"presence_logs?timestamp=gt.{today}&order=timestamp.desc")
        return {'presence': result or []}
    
    def get_presence_stats(self):
        today = datetime.now().strftime('%Y-%m-%d')
        logs = self._request('GET', f"presence_logs?timestamp=gt.{today}")
        users = self._request('GET', 'users?active=eq.1')
        
        present_ids = set(log['user_id'] for log in (logs or []))
        total = len(users) if users else 0
        present = len(present_ids)
        
        return {
            'total_users': total,
            'present_today': present,
            'absent_today': total - present,
            'total_entries_today': len(logs) if logs else 0
        }
    
    def clear_all_users(self):
        self._request('DELETE', 'users?id=gt.0')
    
    def get_recent_presence(self, limit: int = 50):
        result = self._request('GET', f"presence_logs?order=timestamp.desc&limit={limit}")
        return result or []
    
    def get_presence_by_date(self, date: str):
        result = self._request('GET', f"presence_logs?timestamp=like.{date}*&order=timestamp.desc")
        return result or []
    
    def get_all_users(self):
        result = self._request('GET', 'users?order=created_at.desc')
        return result or []


# Instância global
db = DatabaseSupabase()