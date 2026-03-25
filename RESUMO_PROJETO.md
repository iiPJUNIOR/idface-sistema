# iDFace Sistema de Presença - Resumo do Projeto

## Visão Geral
Sistema de controle de acesso com reconhecimento facial usando o dispositivo iDFace da Control iD. Integração bidirecional entre o sistema (backend Flask + frontend React) e o dispositivo iDFace.

## Estrutura do Projeto
```
IDFaceSistema/
├── backend/
│   ├── app.py              # API principal (Flask)
│   ├── database.py         # Banco de dados SQLite
│   ├── idface_client.py    # Cliente para comunicar com iDFace
│   ├── config.py           # Configurações
│   └── uploads/photos/    # Fotos dos usuários
├── frontend/
│   ├── src/
│   │   ├── pages/Dashboard.tsx  # Interface principal
│   │   ├── services/api.ts       # Conexão com backend
│   │   └── hooks/useSocket.ts    # WebSocket em tempo real
│   └── dist/                    # Build de produção
└── Controle de Acesso.postman_collection.json  # Collection de APIs do iDFace
```

## Configurações Importantes

### Dispositivo iDFace
- **IP**: 192.168.3.129
- **Usuário**: admin
- **Senha**: 123456

### Backend
- **URL**: http://localhost:5000
- **WebSocket**: ws://localhost:5000

### Frontend
- **URL desenvolvimento**: http://localhost:5173
- **URL produção**: pasta `frontend/dist`

## Como Iniciar o Projeto

### 1. Backend (Flask)
```bash
cd backend
python app.py
```

### 2. Frontend (desenvolvimento)
```bash
cd frontend
npm run dev
```

### 3. Frontend (produção)
```bash
cd frontend
npm run build
# Os arquivos ficam em dist/
# Servir com qualquer servidor web
```

## Funcionalidades Principais

### 1. Cadastro de Usuários
- Criar usuário com nome, matrícula, CPF e foto
- Foto capturada pela câmera do frontend
- Armazenada localmente em `backend/uploads/photos/`

### 2. Sincronização Automática
- Ao criar usuário no sistema → sincroniza automaticamente para o iDFace
- CPF é usado como ID no iDFace (evita duplicatas)
- Foto é enviada automaticamente

### 3. Reconhecimento em Tempo Real
- Polling a cada 3 segundos verifica novos reconhecimentos
- Usuário ATIVO → porta abre + registra presença + mostra verde
- Usuário INATIVO → porta não abre + mostra vermelho
- Não cadastrado → mostra "Não Autorizado"

### 4. Presença em Tempo Real
- Aba no frontend mostra reconhecimentos em tempo real
- Atualiza via WebSocket

### 5. Espelhamento (iDFace ↔ Sistema)
- Sync bidirecional
- Se apagar no sistema → apaga no iDFace
- Se apagar no iDFace → some do sistema após sync

### 6. Exclusão de Fotos
- Ao excluir usuário → foto é removida do sistema

## Endpoints da API

### Usuários
- `GET /api/users` - Listar usuários
- `POST /api/users` - Criar usuário
- `PUT /api/users/<id>` - Atualizar usuário
- `DELETE /api/users/<id>` - Excluir usuário (apaga foto + iDFace)
- `POST /api/users/<id>/sync` - Sincronizar usuário específico
- `POST /api/users/sync-all` - Sincronizar todos
- `POST /api/users/sync-pending` - Sincronizar pendentes
- `POST /api/users/reset-and-sync` - Limpar e sincronizar do zero

### Presença
- `GET /api/presence/today` - Presença de hoje
- `GET /api/presence/stats` - Estatísticas

### iDFace
- `GET /api/idface/test` - Testar conexão
- `POST /api/idface/open-door/<porta>` - Abrir porta

### Webhooks (recebe do iDFace)
- `POST /new_user_identified.fcgi` - Reconhecimento (modo online)
- `POST /api/idface/webhook/new_user_info` - Alternative webhook

## Lógica de Ativo/Inativo

- **Toggle no frontend** ativa/inativa usuário
- Usuário ATIVO = pode entrar (badge verde)
- Usuário INATIVO = não pode entrar (badge vermelho)

## Importante: Modo Offline

O iDFace deve estar em **modo offline** (standalone). A comunicação funciona via polling:
- Backend verifica logs do iDFace a cada 3 segundos
- Quando detecta reconhecimento, verifica status no banco
- Se ativo → abre porta automaticamente via API

## Solução de Problemas

### Foto não sobe para o iDFace
- Verificar se o user_id está sendo passado como inteiro
- Usar `match=1` e `Content-Type: application/octet-stream`

### Usuários duplicados no iDFace
- Usar CPF como ID no iDFace
- Garantir que idface_id no banco = CPF

### Sync não funciona
- Reiniciar backend: `python app.py`
- Verificar se iDFace está acessível (mesma rede)

### Reconhecimento não aparece
- Verificar se polling está rodando (busca "[Polling] Started" no terminal)
- Verificar se logs do iDFace estão sendo retornados

## Comandos Úteis

### Testar API
```bash
# Listar usuários
curl http://localhost:5000/api/users

# Sincronizar todos
curl -X POST http://localhost:5000/api/users/sync-all

# Testar webhook
curl -X POST http://localhost:5000/new_user_identified.fcgi \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":123456789}"
```

### Testar iDFace
```bash
# Login
curl -X POST "http://192.168.3.129/login.fcgi" \
  -H "Content-Type: application/json" \
  -d "{\"login\":\"admin\",\"password\":\"123456\"}"

# Listar usuários
curl -X POST "http://192.168.3.129/load_objects.fcgi?session=SESSION" \
  -H "Content-Type: application/json" \
  -d "{\"object\":\"users\"}"
```

## Tecnologias
- **Backend**: Flask, Flask-SocketIO, SQLite
- **Frontend**: React, TypeScript, TailwindCSS, Socket.io
- **Dispositivo**: iDFace (Control iD)
- **Comunicação**: REST API + WebSocket

## Observações
- CPF é usado como ID no iDFace para evitar duplicatas
- Fotos ficam em `backend/uploads/photos/`
- O sistema precisa estar na mesma rede que o iDFace
- Modo online do iDFace tem problemas de configuração; modo offline com polling funciona melhor
