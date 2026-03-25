import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import os


class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'presenca.db')
        self.db_path = db_path
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS presence_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                idface_id INTEGER,
                device_id INTEGER,
                identifier_type TEXT,
                result INTEGER,
                timestamp INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
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
    
    def add_user(self, name: str, registration: str, cpf: str = None, 
                 idface_id: str = None, photo_path: str = None, photo_base64: str = None) -> Dict[str, Any]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (name, registration, cpf, idface_id, photo_path, photo_base64)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, registration, cpf or '', idface_id or '', photo_path or '', photo_base64 or ''))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            return {"success": True, "user_id": user_id}
        except sqlite3.IntegrityError as e:
            conn.close()
            if "registration" in str(e):
                return {"success": False, "error": "Matrícula já cadastrada"}
            return {"success": False, "error": str(e)}
        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}
    
    def update_user(self, user_id: int, **kwargs) -> Dict[str, Any]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        allowed_fields = ['name', 'registration', 'cpf', 'idface_id', 'photo_path', 'photo_base64', 'active']
        updates = []
        values = []
        
        for key, value in kwargs.items():
            if key in allowed_fields:
                updates.append(f"{key} = ?")
                values.append(value)
        
        if not updates:
            return {"success": False, "error": "Nenhum campo válido para atualizar"}
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(user_id)
        
        try:
            cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", values)
            conn.commit()
            conn.close()
            return {"success": True}
        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_user_by_registration(self, registration: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE registration = ?', (registration,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_user_by_idface_id(self, idface_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE idface_id = ?', (idface_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_user_by_cpf(self, cpf: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE cpf = ?', (cpf,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def list_users(self, active_only: bool = True) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM users'
        if active_only:
            query += ' WHERE active = 1'
        query += ' ORDER BY name'
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def delete_user(self, user_id: int) -> Dict[str, Any]:
        return self.update_user(user_id, active=0)
    
    def permanently_delete_user(self, user_id: int) -> Dict[str, Any]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            return {"success": True}
        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}
    
    def clear_all_users(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users')
        conn.commit()
        conn.close()
    
    def add_presence_log(self, user_id: int, idface_id: int = None, 
                         device_id: int = None, identifier_type: str = None,
                         result: int = None, timestamp: int = None) -> Dict[str, Any]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            idface_id_int = int(idface_id) if idface_id else None
            timestamp_int = int(timestamp) if timestamp else None
            
            cursor.execute('''
                INSERT INTO presence_logs (user_id, idface_id, device_id, identifier_type, result, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, idface_id_int, device_id, identifier_type, result, timestamp_int))
            
            conn.commit()
            log_id = cursor.lastrowid
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            cursor.execute('''
                INSERT INTO daily_presence (user_id, date, first_entry, last_entry, entries_count)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
                ON CONFLICT(user_id, date) DO UPDATE SET
                    last_entry = CURRENT_TIMESTAMP,
                    entries_count = entries_count + 1
            ''', (user_id, today))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "log_id": log_id}
        except Exception as e:
            conn.close()
            return {"success": False, "error": str(e)}
    
    def get_presence_today(self) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT dp.*, u.name, u.registration
            FROM daily_presence dp
            JOIN users u ON dp.user_id = u.id
            WHERE dp.date = ?
            ORDER BY dp.last_entry DESC
        ''', (today,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_recent_presence(self, limit: int = 50) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pl.*, u.name, u.registration
            FROM presence_logs pl
            JOIN users u ON pl.user_id = u.id
            ORDER BY pl.created_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_presence_by_date(self, date: str) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT dp.*, u.name, u.registration
            FROM daily_presence dp
            JOIN users u ON dp.user_id = u.id
            WHERE dp.date = ?
            ORDER BY dp.last_entry DESC
        ''', (date,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_presence_stats(self) -> Dict[str, Any]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('SELECT COUNT(*) as total FROM users WHERE active = 1')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) 
            FROM daily_presence 
            WHERE date = ?
        ''', (today,))
        present_today = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) 
            FROM presence_logs 
            WHERE date(created_at) = ?
        ''', (today,))
        total_entries = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_users": total_users,
            "present_today": present_today,
            "absent_today": total_users - present_today,
            "total_entries_today": total_entries
        }
