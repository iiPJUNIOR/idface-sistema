# IDFace Integration Skill (Control iD)

## Context
Use this skill when integrating with IDFace facial recognition devices from Control iD. Based on official examples from https://github.com/controlid/integracao

## Device Configuration

```javascript
const IDFACE_CONFIG = {
  ip: "192.168.0.129",
  user: "admin",
  password: "admin",
  baseUrl: "http://192.168.0.129"
};
```

## Modos de Integração

### Modo Push (Servidor recebe eventos do dispositivo)
O dispositivo envia eventos para o servidor configurado.

### Modo Online (Servidor processa reconhecimentos)
O dispositivo envia foto/template para o servidor decidir acesso.

### Modo Monitor (Dispositivo → Servidor)
Monitoramento de eventos em tempo real.

---

## Node.js IDFace Client

```javascript
const axios = require('axios');

class IDFaceClient {
  constructor(ip, user = 'admin', password = 'admin') {
    this.ip = ip;
    this.baseUrl = `http://${ip}`;
    this.session = null;
    this.user = user;
    this.password = password;
  }

  // Login
  async login() {
    const res = await axios.post(`${this.baseUrl}/login.fcgi`, {
      login: this.user,
      password: this.password
    });
    this.session = res.data.session;
    return { success: !!this.session, session: this.session };
  }

  // Listar usuários
  async listUsers() {
    const res = await axios.post(
      `${this.baseUrl}/load_objects.fcgi?session=${this.session}`,
      { object: 'users' }
    );
    return res.data.users || [];
  }

  // Carregar usuário específico
  async loadUser(id) {
    const res = await axios.post(
      `${this.baseUrl}/load_objects.fcgi?session=${this.session}`,
      { object: 'users', where: { users: { id } } }
    );
    return res.data.users?.[0];
  }

  // Criar usuário
  async createUser(id, name, registration = '') {
    const res = await axios.post(
      `${this.baseUrl}/create_objects.fcgi?session=${this.session}`,
      { object: 'users', values: [{ id, name, registration }] }
    );
    return { success: !!res.data.ids, ids: res.data.ids };
  }

  // Deletar usuário
  async destroyUser(id) {
    const res = await axios.post(
      `${this.baseUrl}/destroy_objects.fcgi?session=${this.session}`,
      { object: 'users', where: { users: { id } } }
    );
    return { success: res.status === 200 };
  }

  // Deletar todos os usuários
  async destroyAllUsers() {
    const res = await axios.post(
      `${this.baseUrl}/destroy_objects.fcgi?session=${this.session}`,
      { object: 'users' }
    );
    return { success: res.status === 200 };
  }

  // Enviar foto (face)
  async setUserImage(userId, imageBase64, timestamp = 0) {
    const res = await axios.post(
      `${this.baseUrl}/user_set_image.fcgi?session=${this.session}&user_id=${userId}&match=0&timestamp=${timestamp}`,
      { image: imageBase64 }
    );
    return { success: res.status === 200 };
  }

  // Enviar lista de fotos (otimizado)
  async setUserImageList(userImages) {
    // userImages: [{ user_id, image, timestamp }]
    const res = await axios.post(
      `${this.baseUrl}/user_set_image_list.fcgi?session=${this.session}`,
      { user_images: userImages }
    );
    return res.data;
  }

  // Baixar foto
  async getUserImage(userId) {
    const res = await axios.get(
      `${this.baseUrl}/user_get_image.fcgi?session=${this.session}&user_id=${userId}`,
      { responseType: 'arraybuffer' }
    );
    if (res.status === 200 && res.data.length > 100) {
      return Buffer.from(res.data);
    }
    return null;
  }

  // Deletar foto do usuário
  async destroyUserImage(userId) {
    const res = await axios.post(
      `${this.baseUrl}/user_destroy_image.fcgi?session=${this.session}`,
      { user_id: userId }
    );
    return { success: res.status === 200 };
  }

  // Abrir porta
  async openDoor(door = 0) {
    const res = await axios.post(
      `${this.baseUrl}/execute_actions.fcgi?session=${this.session}`,
      { actions: [{ action: 'door', parameters: `door=${door}` }] }
    );
    return { success: res.status === 200 };
  }

  // Configurar Push
  async setPush(serverIp, port = 8080) {
    const res = await axios.post(
      `${this.baseUrl}/set_configuration.fcgi?session=${this.session}`,
      {
        push_server: {
          push_request_timeout: "4000",
          push_request_period: "5",
          push_remote_address: `http://${serverIp}:${port}`
        }
      }
    );
    return { success: res.status === 200 };
  }

  // Configurar Modo Online
  async enableOnline(serverId) {
    const res = await axios.post(
      `${this.baseUrl}/set_configuration.fcgi?session=${this.session}`,
      {
        online_client: { server_id: serverId.toString() }
      }
    );
    return { success: res.status === 200 };
  }

  // Desativar modo online
  async disableOnline() {
    const res = await axios.post(
      `${this.baseUrl}/set_configuration.fcgi?session=${this.session}`,
      { general: { online: "0" } }
    );
    return { success: res.status === 200 };
  }

  // Criar dispositivo online
  async createOnlineDevice(id, serverIp, port) {
    const res = await axios.post(
      `${this.baseUrl}/create_objects.fcgi?session=${this.session}`,
      {
        object: 'devices',
        values: [{ id, name: 'server', ip: `${serverIp}:${port}`, public_key: '' }]
      }
    );
    return { success: !!res.data.ids, ids: res.data.ids };
  }

  // Cadastro remoto de biometria/face
  async remoteEnroll(type, save, userId, sync) {
    // type: 'face', 'biometry', 'card'
    const res = await axios.post(
      `${this.baseUrl}/remote_enroll.fcgi?session=${this.session}`,
      { type, save, user_id: userId, sync }
    );
    return res.data;
  }

  // Criar QR Code
  async createQRCode(id, value, userId) {
    const res = await axios.post(
      `${this.baseUrl}/create_objects.fcgi?session=${this.session}`,
      { object: 'qrcodes', values: [{ id, value, user_id: userId }] }
    );
    return { success: !!res.data.ids };
  }

  // Criar cartão
  async createCard(id, value, userId) {
    const res = await axios.post(
      `${this.baseUrl}/create_objects.fcgi?session=${this.session}`,
      { object: 'cards', values: [{ id, value, user_id: userId }] }
    );
    return { success: !!res.data.ids };
  }

  // Criar PIN
  async createPin(id, value, userId) {
    const res = await axios.post(
      `${this.baseUrl}/create_objects.fcgi?session=${this.session}`,
      { object: 'pins', values: [{ id, value, user_id: userId }] }
    );
    return { success: !!res.data.ids };
  }

  // Criar regra de acesso
  async createAccessRule(id, name, type) {
    // type: 0 = blocking, 1 = allow
    const res = await axios.post(
      `${this.baseUrl}/create_objects.fcgi?session=${this.session}`,
      { object: 'access_rules', values: [{ id, name, type, priority: 0 }] }
    );
    return { success: !!res.data.ids };
  }

  // Associar usuário à regra de acesso
  async setUserAccessRule(userId, accessRuleId) {
    const res = await axios.post(
      `${this.baseUrl}/create_objects.fcgi?session=${this.session}`,
      { object: 'user_access_rules', values: [{ user_id: userId, access_rule_id: accessRuleId }] }
    );
    return { success: !!res.data.ids };
  }

  // Testar conexão
  async testConnection() {
    try {
      const result = await this.login();
      return { connected: !!result.session, session: result.session };
    } catch (e) {
      return { connected: false, error: e.message };
    }
  }
}
```

---

## Webhook Endpoints (Modo Push)

```javascript
const express = require('express');
const app = express();
app.use(express.json());

// Endpoint de push (polling do dispositivo)
app.get('/push', (req, res) => {
  const deviceId = req.query.deviceId;
  console.log('Push request from device:', deviceId);
  
  // Responda com comandos para executar
  res.json({
    verb: 'POST',
    endpoint: 'set_configuration',
    body: { general: { language: 'pt_BR' } },
    contentType: 'application/json'
  });
});

// Endpoint de resultado (após reconhecimento)
app.post('/result', (req, res) => {
  const { user_id, event_type, date_time } = req.body;
  console.log('Access event:', req.body);
  
  // Processar evento de acesso
  res.json({ code: 0 });
});

// Endpoints de health
app.post('/dao', (req, res) => res.json({ code: 0 }));
app.post('/device_is_alive', (req, res) => res.json({ code: 0 }));
app.post('/new_user_identified.fcgi/dao', (req, res) => res.json({ code: 0 }));
app.post('/new_user_identified.fcgi/device_is_alive', (req, res) => res.json({ code: 0 }));
```

---

## Modo Online - Webhook de Reconhecimento

```javascript
// Endpoint principal para reconhecimentos online
app.post('/api/notifications', async (req, res) => {
  const { user_id, event_type, matched, image } = req.body;
  
  if (matched) {
    // Usuário reconhecido - decidir se permite ou bloqueia
    const user = await findUserById(user_id);
    if (user && user.active) {
      res.json({
        result: 1,  // 1 = autorizado
        user_id: user_id,
        display_message: "Acesso Permitido",
        user_image: true
      });
    } else {
      res.json({
        result: 6,  // 6 = negado
        user_id: user_id,
        display_message: "Acesso Negado",
        user_image: true
      });
    }
  } else {
    // Usuário não reconhecido
    res.json({
      result: 6,
      display_message: "Não Reconhecido"
    });
  }
});
```

---

## Principais Endpoints da API

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/login.fcgi` | POST | Criar sessão |
| `/load_objects.fcgi` | POST | Listar objetos |
| `/create_objects.fcgi` | POST | Criar objetos |
| `/destroy_objects.fcgi` | POST | Deletar objetos |
| `/remove_objects.fcgi` | POST | Remover objetos |
| `/user_set_image.fcgi` | POST | Enviar foto |
| `/user_get_image.fcgi` | GET | Baixar foto |
| `/user_destroy_image.fcgi` | POST | Deletar foto |
| `/user_set_image_list.fcgi` | POST | Enviar lista de fotos |
| `/execute_actions.fcgi` | POST | Executar ações (abrir porta) |
| `/set_configuration.fcgi` | POST | Configurar dispositivo |
| `/remote_enroll.fcgi` | POST | Cadastro remoto |
| `/cancel_remote_enroll.fcgi` | POST | Cancelar cadastro |

---

## Códigos de Resposta

- `result: 1` - Authorized/Success
- `result: 6` - Not authorized/Denied
- `code: 0` - Success (health checks)

---

## Fluxos Comuns

### 1. Sincronizar usuários do IDFace para sistema
```javascript
async function syncFromIdFace(idface) {
  await idface.login();
  const users = await idface.listUsers();
  
  for (const user of users) {
    // Criar ou atualizar no sistema
    await db.upsertUser({
      idface_id: user.id,
      name: user.name,
      registration: user.registration,
      photo: await idface.getUserImage(user.id)
    });
  }
}
```

### 2. Sincronizar usuários do sistema para IDFace
```javascript
async function syncToIdFace(idface, systemUser) {
  await idface.login();
  
  if (systemUser.idface_id) {
    // Atualizar existente
    await idface.setUserImage(systemUser.idface_id, systemUser.photo_base64);
  } else {
    // Criar novo
    const result = await idface.createUser(
      systemUser.id, 
      systemUser.name, 
      systemUser.registration
    );
    if (result.success && systemUser.photo_base64) {
      await idface.setUserImage(systemUser.id, systemUser.photo_base64);
    }
  }
}
```

### 3. Configurar Push Mode
```javascript
async function configurePush(idface, serverIp, port = 8080) {
  await idface.login();
  await idface.setPush(serverIp, port);
  console.log('Push mode configured!');
}
```
