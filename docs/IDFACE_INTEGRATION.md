# IDFace Integration Skill

## Overview
This skill provides integration patterns for connecting to IDFace (Control iD) facial recognition devices via their HTTP API.

## Base Configuration

### Device Connection
```python
IDFACE_IP = "192.168.1.100"  # Device IP address
IDFACE_USER = "admin"
IDFACE_PASSWORD = "admin"
```

### Required Endpoints (Flask Server)

#### 1. Webhook Endpoints (receive events from IDFace)
```python
from flask import Flask, request, jsonify

app = Flask(__name__)

# Main webhook for user identification
@app.route('/new_user_identified.fcgi', methods=['POST'])
def new_user_identified():
    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get('user_id')
    device_id = data.get('device_id')
    timestamp = data.get('date_time')
    
    # Process the access event
    if user_id:
        # TODO: Save to database, emit to frontend, etc.
        pass
    
    # Always return this format
    return jsonify({
        "result": 1,  # 1 = authorized, 6 = not authorized
        "user_id": user_id,
        "display_message": "Access Granted",
        "user_image": True
    })

# Push endpoint (polling)
@app.route('/new_user_identified.fcgi/push', methods=['GET', 'POST'])
def idface_push():
    return jsonify({"code": 0})

# Result endpoint (after identification)
@app.route('/new_user_identified.fcgi/result', methods=['POST'])
def idface_result():
    data = request.get_json(force=True, silent=True) or {}
    user_id = data.get('user_id')
    # Process the result
    return jsonify({"code": 0})

# DAO/Device alive endpoints
@app.route('/new_user_identified.fcgi/dao', methods=['POST'])
@app.route('/new_user_identified.fcgi/device_is_alive', methods=['POST'])
@app.route('/dao', methods=['POST'])
@app.route('/device_is_alive', methods=['POST'])
def idface_dao():
    return jsonify({"code": 0, "message": "OK"})
```

#### 2. IDFace API Client (connect to device)
```python
import requests
import time
from typing import Dict, List, Optional

class IDFaceClient:
    def __init__(self, ip: str, username: str = "admin", password: str = "admin"):
        self.ip = ip
        self.username = username
        self.password = password
        self.session = None
    
    def _make_url(self, path: str) -> str:
        return f"http://{self.ip}{path}"
    
    def _get_session_param(self) -> str:
        if not self.session:
            self.create_session()
        return f"session={self.session}"
    
    def create_session(self) -> Dict:
        url = self._make_url("/login.fcgi")
        payload = {"login": self.username, "password": self.password}
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        self.session = data.get("session")
        return {"success": bool(self.session), "session": self.session}
    
    # LIST USERS
    def list_users(self) -> List[Dict]:
        url = f"{self._make_url('/load_objects.fcgi')}?{self._get_session_param()}"
        payload = {"object": "users"}
        response = requests.post(url, json=payload, timeout=10)
        return response.json().get("users", [])
    
    # CREATE USER
    def create_user(self, name: str, registration: str) -> Dict:
        url = f"{self._make_url('/create_objects.fcgi')}?{self._get_session_param()}"
        values = {"name": name, "registration": registration}
        payload = {"object": "users", "values": [values]}
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()
        if data.get("ids"):
            return {"success": True, "user_id": data["ids"][0]}
        return {"success": False, "error": data}
    
    # DELETE USER
    def delete_user(self, user_id: int) -> Dict:
        url = f"{self._make_url('/remove_objects.fcgi')}?{self._get_session_param()}"
        payload = {"object": "users", "ids": [user_id]}
        response = requests.post(url, json=payload, timeout=10)
        return {"success": response.status_code == 200}
    
    # UPLOAD PHOTO
    def upload_face_photo(self, user_id: int, image_base64: str) -> Dict:
        url = f"{self._make_url('/user_set_image.fcgi')}?{self._get_session_param()}&user_id={user_id}&match=0&timestamp={int(time.time())}"
        payload = {"image": image_base64}
        response = requests.post(url, json=payload, timeout=30)
        return {"success": response.status_code == 200}
    
    # GET PHOTO
    def get_user_photo(self, user_id: int) -> Optional[bytes]:
        url = f"{self._make_url('/user_get_image.fcgi')}?{self._get_session_param()}&user_id={user_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and len(response.content) > 100:
            return response.content
        return None
    
    # OPEN DOOR
    def open_door(self, door: int = 0) -> Dict:
        url = f"{self._make_url('/execute_actions.fcgi')}?{self._get_session_param()}"
        payload = {
            "actions": [{"action": "door", "parameters": f"door={door}"}]
        }
        response = requests.post(url, json=payload, timeout=10)
        return {"success": response.status_code == 200}
    
    # TEST CONNECTION
    def test_connection(self) -> Dict:
        try:
            result = self.create_session()
            return {"connected": bool(result.get("session")), "session": result.get("session")}
        except Exception as e:
            return {"connected": False, "error": str(e)}
```

## iDCloud Configuration

For cloud integration, set the webhook URL in iDCloud to:
```
https://YOUR_SERVER/new_user_identified.fcgi
```

For local integration:
```
http://YOUR_LOCAL_IP:5000/new_user_identified.fcgi
```

## IDFace iDCloud API Documentation Summary

### User Object Fields
- `id` - User ID in device
- `name` - User name
- `registration` - Registration number (matrícula)
- `image_timestamp` - When photo was updated

### Access Result Codes
- `1` - Authorized/Success
- `6` - Not authorized/Denied
- `7` - Identified (success)

### Key Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/login.fcgi` | POST | Create session |
| `/load_objects.fcgi` | POST | List users |
| `/create_objects.fcgi` | POST | Create user |
| `/remove_objects.fcgi` | POST | Delete user |
| `/user_set_image.fcgi` | POST | Upload photo |
| `/user_get_image.fcgi` | GET | Get photo |
| `/execute_actions.fcgi` | POST | Open door |

## Common Integration Patterns

### 1. Two-Way Sync
```
System → IDFace: Create/update users
IDFace → System: Webhook on access
```

### 2. One-Way (IDFace as source)
```
IDFace → System: Import users via API
IDFace → System: Webhook on access
```

### 3. One-Way (System as source)
```
System → IDFace: Create/update users on access events only
```
