# IDFace Sistema de Presença

Sistema completo para controle de presença usando o terminal IDFace da Control iD.

## Funcionalidades

- Cadastro de usuários com foto (captura via webcam)
- Sincronização automática com IDFace
- Presença em tempo real via WebSocket
- Dashboard com estatísticas
- Abrir porta remotamente
- Status de conexão com IDFace

## Estrutura do Projeto

```
IDFaceSistema/
├── backend/
│   ├── app.py              # Servidor Flask principal
│   ├── config.py           # Configurações
│   ├── database.py         # Banco de dados SQLite
│   ├── idface_client.py   # Cliente IDFace API
│   ├── requirements.txt    # Dependências Python
│   └── uploads/            # Fotos salvas
├── frontend/
│   ├── src/
│   │   ├── components/     # Componentes React
│   │   ├── hooks/         # Hooks personalizados
│   │   ├── pages/         # Páginas
│   │   └── services/      # Serviços API
│   └── ...
└── README.md
```

## Instalação

### Backend

```bash
cd IDFaceSistema/backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### Frontend

```bash
cd IDFaceSistema/frontend
npm install
```

## Configuração

### Backend

Edite o arquivo `backend/.env` (copie de `.env.example`):

```env
IDFACE_IP=192.168.0.129
IDFACE_USER=admin
IDFACE_PASSWORD=admin
IDFACE_PORT=8080
SECRET_KEY=sua-chave-secreta
```

### Frontend

O arquivo `.env` já está configurado para desenvolvimento local:

```env
VITE_API_URL=http://localhost:5000
VITE_WS_URL=http://localhost:5000
```

## Execução

### Terminal 1 - Backend

```bash
cd IDFaceSistema/backend
python app.py
```

O servidor estará disponível em `http://localhost:5000`

### Terminal 2 - Frontend

```bash
cd IDFaceSistema/frontend
npm run dev
```

O frontend estará disponível em `http://localhost:5173`

## Configuração do IDFace

Para que o IDFace envie eventos para o sistema, configure no equipamento:

1. Acesse a interface web do IDFace
2. Vá em **Configurações > Modo de Operação**
3. Selecione **Modo Pro** ou **Modo Enterprise**
4. Configure o servidor:
   - **URL do Servidor:** `http://SEU_IP:5000/api/idface/webhook`
   - **Endpoint deheartbeat:** `/api/idface/webhook/device_alive`
   - **Endpoint de evento:** `/api/idface/webhook/new_user_info`

## API Endpoints

### Usuários

- `GET /api/users` - Listar usuários
- `POST /api/users` - Criar usuário
- `GET /api/users/:id` - Obter usuário
- `PUT /api/users/:id` - Atualizar usuário
- `DELETE /api/users/:id` - Excluir usuário
- `POST /api/users/:id/sync` - Sincronizar com IDFace
- `POST /api/users/sync-all` - Sincronizar todos

### Presença

- `GET /api/presence/today` - Presença de hoje
- `GET /api/presence/recent` - Registros recentes
- `GET /api/presence/stats` - Estatísticas

### IDFace

- `GET /api/idface/test` - Testar conexão
- `POST /api/idface/door/open` - Abrir porta

## Tecnologias

### Backend
- Python 3.8+
- Flask
- Flask-CORS
- Flask-SocketIO
- SQLite

### Frontend
- React 18
- TypeScript
- Tailwind CSS
- Socket.io Client
- Lucide Icons
- Vite

## Licença

MIT
