# Configuração do IDFace

## Dados do Sistema

- **IP do Computador (servidor):** `192.168.3.6`
- **Porta do Servidor:** `5000`
- **URL do Servidor:** `http://192.168.3.6:5000`

- **IP do IDFace:** `192.168.3.129`
- **Usuário:** `admin`
- **Senha:** `123456`

---

## Configuração no IDFace

### Passo 1: Acessar o IDFace

1. Abra um navegador e acesse: `http://192.168.3.129`
2. Faça login com usuário `admin` e senha `123456`

### Passo 2: Configurar Modo Online (Modo Pro)

1. No menu lateral, clique em **Configurações**
2. Vá em **Sistema** → **Modo de Operação**
3. Selecione **Modo Pro** (ou "Online" / "Enterprise" dependendo da versão)
4. Salve as configurações

### Passo 3: Configurar Servidor Push

1. Vá em **Configurações** → **Monitor** (ou "Servidor Online")
2. Configure os campos:

```
Servidor: http://192.168.3.6:5000
Porta: 5000
```

3. Marque as opções de eventos que deseja receber:
   - [x] Evento de identificação (new_user_info)
   - [x] Heartbeat (device_is_alive)
   - [x] Solicitação de foto (user_get_image)

4. Salve

### Passo 4: Reiniciar o IDFace

Após configurar, reinicie o equipamento para aplicar as mudanças.

---

## Verificar Conexão

Depois de configurar, você pode verificar se está funcionando:

1. Inicie o backend:
```bash
cd IDFaceSistema/backend
python app.py
```

2. No IDFace, vá em **Configurações** → **Monitor** e clique em "Testar Conexão"

3. No frontend, você verá o status do IDFace mudar para "Conectado"

---

## Solução de Problemas

### IDFace não conecta ao servidor

1. **Verifique o firewall do Windows:**
   - Abra o Firewall do Windows
   - Vá em "Permitir um aplicativo..."
   - Adicione o Python e permita conexões de entrada na porta 5000

2. **Verifique se o backend está rodando:**
   - O terminal deve mostrar "Running on http://0.0.0.0:5000"

3. **Teste a conexão manualmente:**
   - No navegador do computador, acesse: `http://192.168.3.6:5000/api/health`
   - Deve retornar um JSON com status

### Verificar se a porta 5000 está aberta

```powershell
# No PowerShell (como Administrador)
netsh advfirewall firewall add rule name="IDFace Server" dir=in action=allow protocol=tcp localport=5000
```

---

## Estrutura dos Webhooks

O servidor espera as seguintes requisições do IDFace:

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/idface/webhook/new_user_info` | POST | Quando alguém passa no IDFace |
| `/api/idface/webhook/device_alive` | POST | Heartbeat do IDFace |
| `/api/idface/webhook/user_image` | GET | IDFace solicita foto do usuário |
