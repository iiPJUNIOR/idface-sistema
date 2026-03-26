# IDFace Sistema de Presença - Documentação da API

## Visão Geral

Sistema de controle de acesso e presença usando reconhecimento facial com dispositivos IDFace (Control iD).

## URLs Base

- **Local**: `http://localhost:5000`
- **Produção**: `https://seu-dominio.com` (ou URL do servidor em nuvem)

---

## Autenticação

Não requer autenticação (CORS aberto para todas as origens).

---

## Endpoints da API REST

### Saúde e Status

#### `GET /`
Retorna status da API.

**Resposta:**
```json
{
  "name": "IDFace Presença API",
  "version": "1.0.0",
  "status": "running"
}
```

#### `GET /api/health`
Verifica saúde do sistema.

**Resposta:**
```json
{
  "status": "healthy",
  "database": "connected",
  "idface": {
    "connected": true,
    "session": true,
    "message": "Conexão estabelecida!"
  }
}
```

#### `GET /api/idface/test`
Testa conexão com o IDFace.

**Resposta:**
```json
{
  "connected": true,
  "session": true,
  "message": "Conexão estabelecida!"
}
```

---

### Usuários

#### `GET /api/users`
Lista todos os usuários.

**Resposta:**
```json
{
  "success": true,
  "users": [
    {
      "id": 1,
      "name": "João Silva",
      "registration": "12345",
      "cpf": "12345678900",
      "idface_id": "12345678900",
      "active": true,
      "created_at": "2024-01-15T10:30:00",
      "has_photo": true,
      "photo_url": "/api/users/1/photo"
    }
  ]
}
```

#### `POST /api/users`
Cria um novo usuário.

**Body:**
```json
{
  "name": "João Silva",
  "registration": "12345",
  "cpf": "12345678900",
  "photo": "base64_da_foto_jpeg..."
}
```

**Resposta:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "name": "João Silva",
    "registration": "12345",
    "cpf": "12345678900",
    "active": true,
    "has_photo": true
  },
  "synced_to_idface": true
}
```

#### `GET /api/users/{id}`
Retorna dados de um usuário específico.

**Resposta:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "name": "João Silva",
    "registration": "12345",
    "active": true,
    "has_photo": true,
    "photo_url": "/api/users/1/photo"
  }
}
```

#### `PUT /api/users/{id}`
Atualiza dados do usuário.

**Body:**
```json
{
  "name": "João Silva Atualizado",
  "photo": "base64_da_nova_foto..."
}
```

#### `DELETE /api/users/{id}`
Exclui um usuário.

**Resposta:**
```json
{
  "success": true
}
```

#### `GET /api/users/{id}/photo`
Retorna a foto do usuário (JPEG).

#### `POST /api/users/{id}/toggle-status`
Ativa/desativa usuário (controla acesso).

**Resposta:**
```json
{
  "success": true,
  "active": false
}
```

#### `POST /api/users/{id}/sync`
Sincroniza usuário com o IDFace.

**Resposta:**
```json
{
  "success": true,
  "idface_id": "12345678900",
  "action": "created"
}
```

#### `GET /api/users/{id}/check-sync`
Verifica se usuário está sincronizado com IDFace.

**Resposta:**
```json
{
  "success": true,
  "synced": true,
  "idface_id": "12345678900"
}
```

---

### Sincronização em Lote

#### `POST /api/users/sync-pending`
Sincroniza usuários pendentes.

**Body (opcional):**
```json
{
  "force": true
}
```

**Resposta:**
```json
{
  "success": true,
  "success_count": 10,
  "error_count": 2
}
```

#### `POST /api/users/sync-all`
Sincroniza todos os usuários (importa do IDFace para o sistema).

**Resposta:**
```json
{
  "success": true,
  "synced": 15,
  "deleted": 0,
  "details": [...]
}
```

#### `POST /api/users/reset-and-sync`
Limpa banco e sincroniza todos do IDFace.

#### `POST /api/users/import-csv`
Importa usuários de arquivo CSV.

**Form Data:**
- `file`: arquivo CSV

**CSV formato:**
```csv
name,registration,cpf
João Silva,12345,12345678900
Maria Santos,12346,98765432100
```

#### `POST /api/users/batch-create`
Cria múltiplos usuários de uma vez.

**Body:**
```json
{
  "users": [
    {"name": "João", "registration": "001", "cpf": "111"},
    {"name": "Maria", "registration": "002", "cpf": "222"}
  ]
}
```

---

### Presença

#### `GET /api/presence/today`
Lista presença do dia.

**Resposta:**
```json
{
  "success": true,
  "date": "2024-01-15",
  "presence": [
    {
      "id": 1,
      "user_id": 1,
      "name": "João Silva",
      "registration": "12345",
      "timestamp": "2024-01-15T08:30:00",
      "entries_count": 1
    }
  ],
  "stats": {
    "total_users": 50,
    "present_today": 30,
    "absent_today": 20,
    "total_entries_today": 45
  }
}
```

#### `GET /api/presence/recent?limit=50`
Lista presença recente.

#### `GET /api/presence/date/{YYYY-MM-DD}`
Lista presença de uma data específica.

#### `GET /api/presence/stats`
Retorna estatísticas de presença.

**Resposta:**
```json
{
  "success": true,
  "stats": {
    "total_users": 50,
    "present_today": 30,
    "absent_today": 20,
    "total_entries_today": 45
  }
}
```

---

### Controle do IDFace

#### `POST /api/idface/door/open`
Abre a porta.

**Body:**
```json
{
  "door": 0
}
```

**Resposta:**
```json
{
  "success": true,
  "response": {...}
}
```

#### `GET /api/idface/list-users`
Lista usuários do IDFace.

**Resposta:**
```json
{
  "success": true,
  "count": 50,
  "users": [
    {"id": "12345", "name": "João", "registration": "12345"}
  ]
}
```

#### `GET /api/idface/test-photo/{user_id}`
Testa busca de foto do IDFace.

---

### Polling

#### `GET /api/polling/reset`
Reseta o polling de logs do IDFace.

**Resposta:**
```json
{
  "success": true,
  "message": "Polling resetado"
}
```

---

## WebSocket Events

### Conexão

```
ws://servidor:socketio
```

### Canais

O cliente deve entrar na sala `admin`:

```javascript
socket.emit('subscribe', { room: 'admin' });
```

### Eventos Recebidos (Server → Client)

#### `recognition_detected`
Enviado quando ocorre um reconhecimento no IDFace.

```json
{
  "user_id": 1,
  "name": "João Silva",
  "registration": "12345",
  "active": true,
  "timestamp": "2024-01-15T10:30:00",
  "created_at": "2024-01-15T10:30:05",
  "event_type": 7,
  "event_description": "Face reconhecida"
}
```

**Campos adicionais possíveis:**
- `not_recognized`: true (quando face não reconhecida)
- `blocked`: true (quando usuário bloqueado)
- `not_found`: true (quando usuário não cadastrado)

#### `presence_detected`
Enviado quando um usuário ativo passa no IDFace.

```json
{
  "id": 1,
  "user_id": 1,
  "name": "João Silva",
  "registration": "12345",
  "timestamp": "2024-01-15T10:30:00",
  "entries_count": 1
}
```

#### `user_created`
Enviado quando um usuário é criado.

#### `user_updated`
Enviado quando um usuário é atualizado.

```json
{
  "id": 1,
  "name": "João Silva",
  "active": true,
  ...
}
```

#### `user_deleted`
Enviado quando um usuário é excluído.

```json
{
  "user_id": 1
}
```

#### `device_heartbeat`
Enviado periodicamente pelo IDFace.

```json
{
  "device_id": "device_1",
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `users_synced`
Enviado após sincronização completa.

```json
{
  "count": 10,
  "deleted": 0
}
```

---

## Tipos de Eventos IDFace

| Código | Descrição |
|--------|-----------|
| 1 | Acesso por cartão |
| 2 | Acesso por biometria |
| 3 | Face não reconhecida |
| 4 | Cartão inválido |
| 5 | Acesso negado |
| 6 | Usuário bloqueado |
| 7 | Face reconhecida |
| 8 | Acesso por senha |
| 9 | Evento de porta |
| 10 | Anti-passback |
| 11 | Intertravamento |
| 12 | Acesso neg. por horário |
| 13 | Acesso neg. por feriado |
| 14 | Acesso neg. por blacklist |
| 15 | Acesso neg. por leitor inválido |

---

## Webhooks IDFace (Receber Push Notifications)

O sistema recebe notificações push do IDFace nos seguintes endpoints:

### Endpoint Principal de Push
```
POST /push_server.fcgi
```

### Catch-all para Push
```
POST /<caminho>
```
(Processa qualquer URL que contenha `push_server`, `new_user` ou `device_is_alive`)

### Formato do Payload IDFace (Push)

```json
{
  "object_changes": [
    {
      "type": "inserted",
      "values": {
        "id": 12345,
        "event": 7,
        "user_id": 12345678900,
        "time": 1705312200
      }
    }
  ]
}
```

### Respostas para IDFace

**Porta liberada:**
```json
{
  "result": 1,
  "user_id": "12345678900",
  "display_message": "Presença Liberada",
  "user_image": true
}
```

**Acesso negado:**
```json
{
  "result": 6,
  "display_message": "Não Autorizado",
  "user_image": false
}
```

---

## Estrutura do Banco de Dados

### Tabela `users`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER | ID único (auto incremento) |
| name | TEXT | Nome do usuário |
| registration | TEXT | Matrícula |
| cpf | TEXT | CPF (usado como idface_id) |
| idface_id | TEXT | ID no IDFace |
| active | INTEGER | 1=ativo, 0=inativo |
| photo_path | TEXT | Caminho da foto |
| photo_base64 | TEXT | Foto em base64 |
| sync_pending | INTEGER | 1=pendente de sync |
| created_at | TEXT | Data de criação |

### Tabela `presence_logs`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER | ID único |
| user_id | INTEGER | FK para users |
| idface_id | TEXT | ID no IDFace |
| device_id | INTEGER | ID do dispositivo |
| identifier_type | TEXT | Tipo (face, card, etc) |
| result | INTEGER | Código do resultado |
| timestamp | INTEGER | Unix timestamp |
| created_at | TEXT | Data de criação |

---

## Exemplo de Integração com Outro Sistema

### JavaScript (Frontend)

```javascript
// API REST
const API_BASE = 'https://seu-servidor.com';

// Listar usuários
async function getUsers() {
  const res = await fetch(`${API_BASE}/api/users`);
  return res.json();
}

// Criar usuário
async function createUser(data) {
  const res = await fetch(`${API_BASE}/api/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

// Toggle status
async function toggleStatus(userId) {
  const res = await fetch(`${API_BASE}/api/users/${userId}/toggle-status`, {
    method: 'POST'
  });
  return res.json();
}

// WebSocket em tempo real
import { io } from 'socket.io-client';

const socket = io('https://seu-servidor.com', {
  transports: ['websocket', 'polling']
});

socket.on('connect', () => {
  console.log('Conectado!');
  socket.emit('subscribe', { room: 'admin' });
});

socket.on('recognition_detected', (data) => {
  console.log('Reconhecimento:', data);
  // data.not_recognized = true  → Face não reconhecida
  // data.blocked = true         → Usuário bloqueado
  // data.active = true          → Acesso liberado
});

socket.on('presence_detected', (data) => {
  console.log('Presença detectada:', data.name);
});
```

### Python

```python
import requests
import socketio

API_BASE = 'https://seu-servidor.com'

# API REST
response = requests.get(f'{API_BASE}/api/users')
users = response.json()

# Toggle status
requests.post(f'{API_BASE}/api/users/1/toggle-status')

# WebSocket
sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('Conectado!')
    sio.emit('subscribe', {'room': 'admin'})

@sio.on('recognition_detected')
def on_recognition(data):
    print(f'Reconhecimento: {data}')

@sio.on('presence_detected')
def on_presence(data):
    print(f'Presença: {data["name"]}')

sio.connect(API_BASE)
sio.wait()
```

### PHP

```php
<?php
$API_BASE = 'https://seu-servidor.com';

// Listar usuários
$response = file_get_contents("$API_BASE/api/users");
$users = json_decode($response, true);

// Criar usuário
$data = [
    'name' => 'João Silva',
    'registration' => '12345',
    'cpf' => '12345678900'
];

$options = [
    'http' => [
        'method' => 'POST',
        'header' => 'Content-Type: application/json',
        'content' => json_encode($data)
    ]
];

$context = stream_context_create($options);
$result = file_get_contents("$API_BASE/api/users", false, $context);
?>
```

---

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| IDFACE_IP | IP do dispositivo IDFace | 192.168.0.129 |
| IDFACE_PORT | Porta do IDFace | 80 |
| IDFACE_USER | Usuário do IDFace | admin |
| IDFACE_PASSWORD | Senha do IDFace | 123456 |
| SECRET_KEY | Chave secreta Flask | idface-presenca-secret |
| PORT | Porta do servidor | 5000 |

---

## Códigos de Sucesso/Erro

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso |
| 201 | Criado |
| 400 | Erro de requisição |
| 404 | Não encontrado |
| 500 | Erro interno |

---

## Problemas Comuns

### IDFace não conecta
- Verificar IP e porta
- Verificar credenciais
- Verificar rede (firewall)

### Push não chega
- Configurar URL de push no IDFace: `http://seu-servidor:5000/push_server.fcgi`
- Verificar se o servidor está acessível

### Usuário não sincroniza
- Verificar CPF (usado como ID)
- Verificar se access_rule está configurada no IDFace
