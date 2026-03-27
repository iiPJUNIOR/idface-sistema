# Guia de Integração - IDFace Sistema de Presença

## O que é este sistema?

Sistema de controle de acesso e presença usando reconhecimento facial com dispositivos **IDFace (Control iD)**.

### Funcionalidades:
- Cadastro de usuários com foto biométrica
- Sincronização automática com dispositivo IDFace
- Controle de acesso (ativar/bloquear usuários)
- Registro de presença em tempo real
- Dashboard em tempo real via WebSocket
- API REST completa para integrações

---

## Passo a Passo para Integração

### 1. Configuração do IDFace

Antes de integrar, configure seu dispositivo IDFace:

1. Acesse o painel do IDFace (acesso via navegador)
2. Vá em **Configurações → Rede** e configure um IP fixo
3. Anote as credenciais de acesso (usuário/senha)
4. **Importante**: Configure a URL de Push em **Configurações → Push Server**:
   ```
   http://SEU_SERVIDOR:5000/push_server.fcgi
   ```
   (Substitua pelo IP/domínio do seu servidor)

---

### 2. Variáveis de Ambiente

Configure no seu servidor:

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| IDFACE_IP | IP do IDFace | 192.168.0.129 |
| IDFACE_PORT | Porta | 80 |
| IDFACE_USER | Usuário admin | admin |
| IDFACE_PASSWORD | Senha | 123456 |
| SECRET_KEY | Chave secreta | qualquer-texto |
| PORT | Porta servidor | 5000 |

---

### 3. Endpoints da API

#### 3.1 Usuários

**Listar todos os usuários**
```http
GET /api/users
```

**Criar usuário**
```http
POST /api/users
Content-Type: application/json

{
  "name": "João Silva",
  "registration": "12345",
  "cpf": "12345678900",
  "photo": "base64_da_foto..."
}
```

**Buscar usuário**
```http
GET /api/users/{id}
```

**Atualizar usuário**
```http
PUT /api/users/{id}
Content-Type: application/json

{
  "name": "Nome Atualizado",
  "photo": "nova_foto_base64..."
}
```

**Excluir usuário**
```http
DELETE /api/users/{id}
```

**Ativar/Desativar acesso**
```http
POST /api/users/{id}/toggle-status
```
- Usuário ativo = acesso liberado
- Usuário inativo = acesso bloqueado

**Sincronizar com IDFace**
```http
POST /api/users/{id}/sync
```

---

#### 3.2 Presença

**Presença de hoje**
```http
GET /api/presence/today
```

**Presença recente**
```http
GET /api/presence/recent?limit=50
```

**Presença por data**
```http
GET /api/presence/date/2024-01-15
```

**Estatísticas**
```http
GET /api/presence/stats
```

---

#### 3.3 IDFace

**Testar conexão**
```http
GET /api/idface/test
```

**Abrir porta**
```http
POST /api/idface/door/open
Content-Type: application/json

{
  "door": 0
}
```

**Listar usuários do IDFace**
```http
GET /api/idface/list-users
```

---

#### 3.4 Sincronização em Lote

**Sincronizar pendentes**
```http
POST /api/users/sync-pending
```

**Sincronizar todos**
```http
POST /api/users/sync-all
```

**Importar CSV**
```http
POST /api/users/import-csv
```
Corpo do formulário:
- `file`: arquivo CSV com colunas `name,registration,cpf`

**Criar múltiplos usuários**
```http
POST /api/users/batch-create
Content-Type: application/json

{
  "users": [
    {"name": "João", "registration": "001", "cpf": "111"},
    {"name": "Maria", "registration": "002", "cpf": "222"}
  ]
}
```

---

### 4. WebSocket (Tempo Real)

Conecte ao WebSocket para receber eventos em tempo real:

```javascript
import { io } from 'socket.io-client';

const socket = io('http://SEU_SERVIDOR:5000', {
  transports: ['websocket', 'polling']
});

socket.on('connect', () => {
  console.log('Conectado!');
  // Entrar na sala admin para receber eventos
  socket.emit('subscribe', { room: 'admin' });
});

// Evento: reconhecimento facial
socket.on('recognition_detected', (data) => {
  console.log('Reconhecimento:', data);
  /*
  data = {
    user_id: 1,
    name: "João Silva",
    registration: "12345",
    active: true,           // acesso liberado?
    not_recognized: false,  // face não reconhecida?
    blocked: false,         // usuário bloqueado?
    not_found: false,       // não cadastrado?
    event_type: 7,
    event_description: "Face reconhecida",
    timestamp: "2024-01-15T10:30:00"
  }
  */
});

// Evento: presença detectada
socket.on('presence_detected', (data) => {
  console.log('Presença:', data.name);
  /*
  data = {
    id: 1,
    user_id: 1,
    name: "João Silva",
    registration: "12345",
    timestamp: "2024-01-15T10:30:00",
    entries_count: 1
  }
  */
});

// Evento: usuário criado
socket.on('user_created', (user) => {
  console.log('Novo usuário:', user.name);
});

// Evento: usuário atualizado
socket.on('user_updated', (user) => {
  console.log('Usuário atualizado:', user);
});

// Evento: usuário excluído
socket.on('user_deleted', (data) => {
  console.log('Usuário deletado:', data.user_id);
});
```

---

### 5. Exemplos de Integração

#### 5.1 JavaScript/TypeScript

```javascript
// Configuração
const API = 'https://seu-servidor.com';
const WS_URL = 'https://seu-servidor.com';

// ==================== API REST ====================

// Buscar todos os usuários
async function getUsers() {
  const res = await fetch(`${API}/api/users`);
  const data = await res.json();
  return data.users;
}

// Criar usuário com foto
async function createUser(name, registration, cpf, photoBase64) {
  const res = await fetch(`${API}/api/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name,
      registration,
      cpf,
      photo: photoBase64
    })
  });
  return res.json();
}

// Ativar/desativar acesso
async function toggleUserStatus(userId) {
  const res = await fetch(`${API}/api/users/${userId}/toggle-status`, {
    method: 'POST'
  });
  const data = await res.json();
  return data.active; // true = ativo, false = inativo
}

// Ver presença de hoje
async function getPresenceToday() {
  const res = await fetch(`${API}/api/presence/today`);
  return res.json();
}

// Abrir porta
async function openDoor() {
  await fetch(`${API}/api/idface/door/open`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ door: 0 })
  });
}

// ==================== WEBSOCKET ====================
import { io } from 'socket.io-client';

function connectWebSocket() {
  const socket = io(WS_URL, {
    transports: ['websocket', 'polling'],
    reconnection: true
  });

  socket.on('connect', () => {
    console.log('Conectado ao WebSocket');
    socket.emit('subscribe', { room: 'admin' });
  });

  socket.on('recognition_detected', (data) => {
    if (data.not_recognized) {
      console.log('⚠️ Face não reconhecida');
    } else if (data.blocked) {
      console.log('🚫 Acesso bloquado:', data.name);
    } else if (data.active) {
      console.log('✅ Acesso liberado:', data.name);
    }
  });

  socket.on('presence_detected', (data) => {
    console.log('📍 Presença:', data.name, data.timestamp);
  });

  socket.on('disconnect', () => {
    console.log('Desconectado do WebSocket');
  });

  return socket;
}
```

---

#### 5.2 Python

```python
import requests
import socketio

API = 'https://seu-servidor.com'

# ==================== API REST ====================

def get_users():
    response = requests.get(f'{API}/api/users')
    return response.json()['users']

def create_user(name, registration, cpf, photo_base64=None):
    data = {
        'name': name,
        'registration': registration,
        'cpf': cpf
    }
    if photo_base64:
        data['photo'] = photo_base64
    
    response = requests.post(f'{API}/api/users', json=data)
    return response.json()

def toggle_status(user_id):
    response = requests.post(f'{API}/api/users/{user_id}/toggle-status')
    return response.json()['active']

def get_presence_today():
    response = requests.get(f'{API}/api/presence/today')
    return response.json()

def open_door():
    requests.post(f'{API}/api/idface/door/open', json={'door': 0})

# ==================== WEBSOCKET ====================

sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('Conectado!')
    sio.emit('subscribe', {'room': 'admin'})

@sio.on('recognition_detected')
def on_recognition(data):
    if data.get('not_recognized'):
        print('⚠️ Face não reconhecida')
    elif data.get('blocked'):
        print('🚫 Bloqueado:', data.get('name'))
    elif data.get('active'):
        print('✅ Liberado:', data.get('name'))

@sio.on('presence_detected')
def on_presence(data):
    print('📍 Presença:', data.get('name'))

# Conectar
sio.connect(API)
sio.wait()
```

---

#### 5.3 PHP

```php
<?php
$API = 'https://seu-servidor.com';

// ==================== API REST ====================

function getUsers() {
    global $API;
    $response = file_get_contents("$API/api/users");
    return json_decode($response, true)['users'];
}

function createUser($name, $registration, $cpf, $photo = null) {
    global $API;
    
    $data = [
        'name' => $name,
        'registration' => $registration,
        'cpf' => $cpf
    ];
    
    if ($photo) {
        $data['photo'] = $photo;
    }
    
    $options = [
        'http' => [
            'method' => 'POST',
            'header' => 'Content-Type: application/json',
            'content' => json_encode($data)
        ]
    ];
    
    $context = stream_context_create($options);
    $response = file_get_contents("$API/api/users", false, $context);
    return json_decode($response, true);
}

function toggleStatus($userId) {
    global $API;
    
    $options = [
        'http' => [
            'method' => 'POST'
        ]
    ];
    
    $context = stream_context_create($options);
    $response = file_get_contents("$API/api/users/$userId/toggle-status", false, $context);
    return json_decode($response, true)['active'];
}

function getPresenceToday() {
    global $API;
    $response = file_get_contents("$API/api/presence/today");
    return json_decode($response, true);
}

// ==================== USO ====================

$users = getUsers();
foreach ($users as $user) {
    echo $user['name'] . ' - ' . ($user['active'] ? 'Ativo' : 'Inativo') . "\n";
}

// Ativar usuário
toggleStatus(1);
?>
```

---

#### 5.4 C# / .NET

```csharp
using System.Net.Http;
using System.Text;
using System.Text.Json;
using SocketIOClient;

var API = "https://seu-servidor.com";
var httpClient = new HttpClient();

// ==================== API REST ====================

public async Task<List<User>> GetUsers()
{
    var response = await httpClient.GetAsync($"{API}/api/users");
    var json = await response.Content.ReadAsStringAsync();
    var data = JsonSerializer.Deserialize<JsonElement>(json);
    
    return JsonSerializer.Deserialize<List<User>>(data.GetProperty("users").GetRawText());
}

public async Task<bool> ToggleStatus(int userId)
{
    var response = await httpClient.PostAsync($"{API}/api/users/{userId}/toggle-status", null);
    var json = await response.Content.ReadAsStringAsync();
    var data = JsonSerializer.Deserialize<JsonElement>(json);
    
    return data.GetProperty("active").GetBoolean();
}

public async Task CreateUser(string name, string registration, string cpf, string photoBase64)
{
    var data = new {
        name = name,
        registration = registration,
        cpf = cpf,
        photo = photoBase64
    };
    
    var json = JsonSerializer.Serialize(data);
    var content = new StringContent(json, Encoding.UTF8, "application/json");
    
    await httpClient.PostAsync($"{API}/api/users", content);
}

// ==================== WEBSOCKET ====================

var socket = new SocketIOClient.SocketIO(API, new SocketIOClientOptions
{
    Transports = new List<TransportType> { TransportType.WebSocket }
});

socket.On("connect", () =>
{
    Console.WriteLine("Conectado!");
    socket.EmitAsync("subscribe", new { room = "admin" });
});

socket.On("recognition_detected", (data) =>
{
    Console.WriteLine($"Reconhecimento: {data}");
});

socket.On("presence_detected", (data) =>
{
    Console.WriteLine($"Presença: {data}");
});

await socket.ConnectAsync();
```

---

#### 5.5 Flutter / Dart

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:socket_io_client/socket_io_client.dart' as io;

var API = 'https://seu-servidor.com';

// ==================== API REST ====================

Future<List<Map<String, dynamic>>> getUsers() async {
  final response = await http.get(Uri.parse('$API/api/users'));
  final data = json.decode(response.body);
  return List<Map<String, dynamic>>.from(data['users']);
}

Future<Map<String, dynamic>> createUser(String name, String registration, String cpf, {String? photo}) async {
  final response = await http.post(
    Uri.parse('$API/api/users'),
    headers: {'Content-Type': 'application/json'},
    body: json.encode({
      'name': name,
      'registration': registration,
      'cpf': cpf,
      'photo': photo
    })
  );
  return json.decode(response.body);
}

Future<bool> toggleStatus(int userId) async {
  final response = await http.post(Uri.parse('$API/api/users/$userId/toggle-status'));
  final data = json.decode(response.body);
  return data['active'];
}

// ==================== WEBSOCKET ====================

io.Socket socket = io.io(API, <String, dynamic>{
  'transports': ['websocket'],
});

socket.on('connect', (_) {
  print('Conectado!');
  socket.emit('subscribe', {'room': 'admin'});
});

socket.on('recognition_detected', (data) {
  print('Reconhecimento: $data');
});

socket.on('presence_detected', (data) {
  print('Presença: $data');
});
```

---

#### 5.6 Java (Android)

```java
import okhttp3.*;
import com.github.nickvl.lsxsocketio.LSXSocketIO;
import com.github.nickvl.lsxsocketio.SocketIO;

public class IDFaceService {
    private static final String API = "https://seu-servidor.com";
    private final OkHttpClient client = new OkHttpClient();
    
    // ==================== API REST ====================
    
    public String getUsers() throws Exception {
        Request request = new Request.Builder()
            .url(API + "/api/users")
            .build();
        
        try (Response response = client.newCall(request).execute()) {
            return response.body().string();
        }
    }
    
    public String toggleStatus(int userId) throws Exception {
        Request request = new Request.Builder()
            .url(API + "/api/users/" + userId + "/toggle-status")
            .post(RequestBody.create("", null))
            .build();
        
        try (Response response = client.newCall(request).execute()) {
            return response.body().string();
        }
    }
    
    public String createUser(String name, String registration, String cpf) throws Exception {
        String json = String.format(
            "{\"name\":\"%s\",\"registration\":\"%s\",\"cpf\":\"%s\"}",
            name, registration, cpf
        );
        
        RequestBody body = RequestBody.create(json, MediaType.parse("application/json"));
        Request request = new Request.Builder()
            .url(API + "/api/users")
            .post(body)
            .build();
        
        try (Response response = client.newCall(request).execute()) {
            return response.body().string();
        }
    }
}
```

---

### 6. Códigos de Evento IDFace

| Código | Descrição |
|--------|-----------|
| 1 | Acesso por cartão |
| 2 | Acesso por biometria |
| 3 | Face não reconhecida |
| 4 | Cartão inválido |
| 5 | Acesso negado |
| 6 | Usuário bloqueado |
| 7 | Face reconhecida ✅ |
| 8 | Acesso por senha |
| 9 | Evento de porta |

---

### 7. Respostas de Erro

```json
{
  "success": false,
  "error": "Mensagem de erro"
}
```

Códigos HTTP:
- `200` - Sucesso
- `201` - Criado
- `400` - Erro na requisição
- `404` - Não encontrado
- `500` - Erro interno

---

### 8. Estrutura do Banco

**Tabela users:**
- `id` - ID único
- `name` - Nome
- `registration` - Matrícula
- `cpf` - CPF (usado como IDFace ID)
- `idface_id` - ID no dispositivo IDFace
- `active` - 1=ativo, 0=inativo
- `photo_base64` - Foto em base64

**Tabela presence_logs:**
- `id` - ID único
- `user_id` - FK para users
- `timestamp` - Data/hora Unix
- `result` - Código do evento

---

### 9. Fluxo Completo de Integração

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUXO DE INTEGRAÇÃO                         │
└─────────────────────────────────────────────────────────────────┘

1. CADASTRO
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │  Frontend    │────▶│   API REST   │────▶│    IDFace    │
   │ (seu app)    │     │  (este sist) │     │  (dispositivo)│
   └──────────────┘     └──────────────┘     └──────────────┘
                                │
                                ▼
                         Cria usuário no
                         banco + envia
                         foto para IDFace

2. ACESSO
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │   Usuário    │────▶│    IDFace    │────▶│   API REST   │
   │  passa face  │     │  reconhece   │────▶│  (este sist) │
   └──────────────┘     └──────────────┘     └──────────────┘
                                                     │
                          Registra presença ◀────────┘
                          no banco
                          + abre porta (se ativo)
                                                     │
                                                     ▼
                          ┌──────────────┐     ┌──────────────┐
                          │  WebSocket   │◀────│   Frontend   │
                          │ (evento real)│     │ (dashboard)  │
                          └──────────────┘     └──────────────┘

3. CONTROLE
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │   Frontend   │────▶│   API REST   │────▶│    IDFace    │
   │ (toggle)     │     │ (toggle)     │────▶│ (libera/bloq)│
   └──────────────┘     └──────────────┘     └──────────────┘
```

---

### 10. Checklist de Integração

- [ ] Servidor configurado e rodando
- [ ] IDFace acessível na rede
- [ ] URL de Push configurada no IDFace
- [ ] Credenciais corretas no config
- [ ] Banco de dados criado
- [ ] Testado endpoint /api/health
- [ ] Testado WebSocket conexão
- [ ] Testado criar usuário
- [ ] Testado toggle status
- [ ] Testado presença em tempo real

---

### 11. Solução de Problemas

**IDFace não conecta:**
- Verifique IP e porta
- Verifique credenciais
- Teste acesso pelo navegador

**Push não chega:**
- Verifique URL de push no IDFace
- Teste se servidor está acessível
- Verifique firewall

**Usuário não sincroniza:**
- Verifique CPF (usado como ID)
- Verifique se access_rule existe no IDFace

**WebSocket não conecta:**
- Verifique URL correta
- Teste com transport 'polling' como fallback

---

### 12. Variáveis de Ambiente Completas

```bash
# IDFace
IDFACE_IP=192.168.0.129
IDFACE_PORT=80
IDFACE_USER=admin
IDFACE_PASSWORD=123456

# Servidor
PORT=5000
SECRET_KEY=sua-chave-secreta

# Database (se usando Supabase)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=sua-chave-supabase
```

---

## API Reference Rápida

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/users` | Listar usuários |
| POST | `/api/users` | Criar usuário |
| GET | `/api/users/{id}` | Ver usuário |
| PUT | `/api/users/{id}` | Atualizar usuário |
| DELETE | `/api/users/{id}` | Excluir usuário |
| POST | `/api/users/{id}/toggle-status` | Ativar/Bloquear |
| POST | `/api/users/{id}/sync` | Sincronizar |
| GET | `/api/presence/today` | Presença hoje |
| GET | `/api/presence/stats` | Estatísticas |
| POST | `/api/idface/door/open` | Abrir porta |
| GET | `/api/health` | Status sistema |

---

## Suporte

Em caso de dúvidas, consulte o código fonte em:
https://github.com/iiPJUNIOR/idface-sistema
