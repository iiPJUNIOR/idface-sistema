import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import requests


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'presenca.db')
        self.db_path = db_path
        self.supabase_url = os.getenv('SUPABASE_URL', 'https://qtqofigtjlykzksexvmf.supabase.co')
        self.supabase_key = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF0cW9maWd0amx5a3prc2V4dm1mIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ0ODA0NzMsImV4cCI6MjA5MDA1NjQ3M30.LrllHp3wImVxIci4EhWKx8E49GrYKMronHOqrsJ3poI')
        self._supabase_headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        self.use_supabase = os.getenv('USE_SUPABASE', 'false').lower() == 'true'
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idface_id INTEGER UNIQUE,
                name TEXT NOT NULL,
                registration TEXT UNIQUE NOT NULL,
                cpf TEXT,
                photo_path TEXT,
                photo_base64 TEXT,
                active INTEGER DEFAULT 1,
                sync_pending INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN sync_pending INTEGER DEFAULT 0')
        except:
            pass
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS presence_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                idface_id INTEGER,
                device_id INTEGER,
                identifier_type TEXT,
                result INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        try:
            cursor.execute('ALTER TABLE presence_logs ADD COLUMN synced INTEGER DEFAULT 0')
        except:
            pass
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_presence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                first_entry TIMESTAMP,
                last_entry TIMESTAMP,
                entries_count INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, date)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_presence_date ON presence_logs(created_at)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_presence(date)
        ''')
        
        conn.commit()
        conn.close()
    
    # ========== USERS ==========
    def list_users(self, active_only: bool = True):
        conn = self.get_connection()
        cursor = conn.cursor()
        if active_only:
            cursor.execute('SELECT * FROM users WHERE active = 1 ORDER BY created_at DESC')
        else:
            cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users
    
    def get_user(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_user_by_cpf(self, cpf: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE cpf = ?', (cpf,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_user_by_registration(self, registration: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE registration = ?', (registration,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_user_by_idface_id(self, idface_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE idface_id = ?', (idface_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def add_user(self, name: str, registration: str, cpf: str = None, 
                  idface_id: str = None, photo_path: str = None, photo_base64: str = None,
                  sync_pending: int = 0) -> Dict[str, Any]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (name, registration, cpf, idface_id, photo_path, photo_base64, active, sync_pending, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, datetime('now'), datetime('now'))
            ''', (name, registration, cpf, idface_id, photo_path, photo_base64, sync_pending))
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            if self.use_supabase:
                self._sync_user_to_supabase(user_id)
            
            return {'success': True, 'user_id': user_id}
        except sqlite3.IntegrityError as e:
            conn.close()
            return {'success': False, 'error': str(e)}
    
    def update_user(self, user_id: int, **kwargs):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        fields = []
        values = []
        for key, value in kwargs.items():
            if value is not None:
                fields.append(f"{key} = ?")
                values.append(value)
        
        fields.append('updated_at = datetime("now")')
        values.append(user_id)
        
        cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
        conn.close()
        
        if self.use_supabase:
            self._sync_user_to_supabase(user_id)
        
        return {'success': True}
    
    def delete_user(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        if self.use_supabase:
            self._delete_user_from_supabase(user_id)
        
        return {'success': True}
    
    def permanently_delete_user(self, user_id: int):
        return self.delete_user(user_id)
    
    # ========== PRESENCE LOGS ==========
    def add_presence_log(self, user_id: int, name: str = None, registration: str = None,
                         idface_id: int = None, device_id: int = None, 
                         identifier_type: str = None, result: str = None, timestamp: str = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        ts = timestamp if timestamp else datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO presence_logs (user_id, idface_id, device_id, identifier_type, result, timestamp, created_at, synced)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), 0)
        ''', (user_id, idface_id, device_id, identifier_type, result, ts))
        
        log_id = cursor.lastrowid
        conn.commit()
        
        cursor.execute('''
            INSERT OR REPLACE INTO daily_presence (user_id, date, first_entry, last_entry, entries_count)
            VALUES (?, date('now'), 
                COALESCE((SELECT first_entry FROM daily_presence WHERE user_id = ? AND date = date('now')), datetime('now')),
                datetime('now'),
                COALESCE((SELECT entries_count FROM daily_presence WHERE user_id = ? AND date = date('now')), 0) + 1
            )
        ''', (user_id, user_id, user_id))
        
        conn.commit()
        conn.close()
        
        if self.use_supabase:
            self._sync_presence_to_supabase(log_id)
    
    def get_presence_today(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT pl.*, u.name, u.registration 
            FROM presence_logs pl
            JOIN users u ON pl.user_id = u.id
            WHERE date(pl.timestamp) = ?
            ORDER BY pl.timestamp DESC
        ''', (today,))
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {'presence': logs}
    
    def get_presence_stats(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('SELECT COUNT(*) as total FROM users WHERE active = 1')
        total = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(DISTINCT user_id) as present FROM presence_logs WHERE date(timestamp) = ?', (today,))
        present = cursor.fetchone()['present']
        
        cursor.execute('SELECT COUNT(*) as entries FROM presence_logs WHERE date(timestamp) = ?', (today,))
        entries = cursor.fetchone()['entries']
        
        conn.close()
        
        return {
            'total_users': total,
            'present_today': present,
            'absent_today': total - present,
            'total_entries_today': entries
        }
    
    def get_recent_presence(self, limit: int = 50):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pl.*, u.name, u.registration 
            FROM presence_logs pl
            JOIN users u ON pl.user_id = u.id
            ORDER BY pl.timestamp DESC
            LIMIT ?
        ''', (limit,))
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs
    
    def get_presence_by_date(self, date: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pl.*, u.name, u.registration 
            FROM presence_logs pl
            JOIN users u ON pl.user_id = u.id
            WHERE date(pl.timestamp) = ?
            ORDER BY pl.timestamp DESC
        ''', (date,))
        logs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return logs
    
    def get_all_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users
    
    def clear_all_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users')
        conn.commit()
        conn.close()
    
    # ========== SUPABASE SYNC ==========
    def _supabase_request(self, method: str, path: str, data: dict = None, params: dict = None):
        url = f"{self.supabase_url}/rest/v1/{path}"
        response = requests.request(method, url, json=data, headers=self._supabase_headers, params=params)
        if response.status_code >= 400:
            print(f"Supabase error: {response.status_code} - {response.text}")
            return None
        return response.json() if response.text else None
    
    def _sync_user_to_supabase(self, user_id: int):
        user = self.get_user(user_id)
        if not user:
            return
        
        data = {
            'name': user['name'],
            'registration': user['registration'],
            'cpf': user.get('cpf', ''),
            'idface_id': user.get('idface_id'),
            'photo_path': user.get('photo_path', ''),
            'photo_base64': user.get('photo_base64', ''),
            'active': user['active'],
            'sync_pending': user.get('sync_pending', 0),
            'updated_at': datetime.now().isoformat()
        }
        
        existing = self._supabase_request('GET', f"users?registration=eq.{user['registration']}&limit=1")
        
        if existing and len(existing) > 0:
            self._supabase_request('PATCH', f"users?registration=eq.{user['registration']}", data)
        else:
            data['created_at'] = user.get('created_at', datetime.now().isoformat())
            self._supabase_request('POST', 'users', data)
    
    def _delete_user_from_supabase(self, user_id: int):
        user = self.get_user(user_id)
        if user:
            self._supabase_request('DELETE', f"users?registration=eq.{user['registration']}")
    
    def _sync_presence_to_supabase(self, log_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM presence_logs WHERE id = ?', (log_id,))
        log = dict(cursor.fetchone())
        
        cursor.execute('SELECT name, registration FROM users WHERE id = ?', (log['user_id'],))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            data = {
                'user_id': log['user_id'],
                'name': user['name'],
                'registration': user['registration'],
                'timestamp': log['timestamp'],
                'entries_count': 1
            }
            self._supabase_request('POST', 'presence_logs', data)
            
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE presence_logs SET synced = 1 WHERE id = ?', (log_id,))
            conn.commit()
            conn.close()
    
    def sync_all_to_supabase(self):
        users = self.get_all_users()
        for user in users:
            self._sync_user_to_supabase(user['id'])
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM presence_logs WHERE synced = 0')
        unsynced = [row['id'] for row in cursor.fetchall()]
        conn.close()
        
        for log_id in unsynced:
            self._sync_presence_to_supabase(log_id)
        
        return {'synced_users': len(users), 'synced_logs': len(unsynced)}


db = Database()