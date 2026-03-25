# Documentação - Controle de Acesso iDFace

## Visão Geral

Sistema de integração entre frontend e equipamento iDFace (Control iD) para controle de acesso com reconhecimento facial.

## Arquitetura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│  Backend    │────▶│   iDFace    │
│  (SPA)      │     │  (API)     │     │  (Equip.)   │
└─────────────┘     └─────────────┘     └─────────────┘
```

**IMPORTANTE**: O frontend NÃO deve falar direto com o iDFace.理由:
- Segurança (credenciais não expostas no browser)
- CORS / rede local / NAT / VPN
- Governança (auditoria, rate limit, logs)

## Sessão / Autenticação

### Fluxo de Autenticação

1. **Login**: Frontend → Backend → iDFace
2. **Receber session token**: Armazenar no backend
3. **Requisições autenticadas**: Backend → iDFace com `?session={{token}}`
4. **Validação**: Verificar validade da sessão periodicamente
5. **Logout**: Encerrar sessão quando necessário

### Endpoints de Sessão

| Método | Endpoint | Descrição |
|--------|----------|------------|
| POST | `/hidlogin.fcgi` | Criar sessão |
| POST | `/session_is_valid.fcgi?session={{session}}` | Verificar validade |
| POST | `/logout.fcgi?session={{session}}` | Encerrar sessão |

### Formato de Autenticação

- **Tipo**: Sessão via query string
- **Token**: String retornada pelo login
- **Uso**: `?session={{session_token}}` em todas as requisições

## Controle de Acesso (Ações)

| Método | Endpoint | Descrição |
|--------|----------|------------|
| POST | `/open_door_1.fcgi?session={{session}}` | Abrir porta 1 |
| POST | `/open_door_1_3s.fcgi?session={{session}}` | Abrir porta 1 (3 segundos) |
| POST | `/close_door_1.fcgi?session={{session}}` | Fechar porta 1 |
| POST | `/turnstile_open_clockwise.fcgi?session={{session}}` | Liberar catraca sentido horário |
| POST | `/turnstile_open_anticlockwise.fcgi?session={{session}}` | Liberar catraca anti-horário |

## Usuários / Credenciais

| Método | Endpoint | Descrição |
|--------|----------|------------|
| POST | `/create_user.fcgi?session={{session}}` | Criar usuário |
| POST | `/load_users.fcgi?session={{session}}` | Carregar usuários |
| POST | `/delete_user.fcgi?session={{session}}` | Deletar usuário |

## Face / Imagem

| Método | Endpoint | Descrição |
|--------|----------|------------|
| POST | `/set_face_image.fcgi?session={{session}}` | Cadastrar imagem |
| POST | `/get_face_image.fcgi?session={{session}}` | Obter imagem |
| POST | `/delete_face_image.fcgi?session={{session}}` | Excluir foto |

## Eventos / Logs

| Método | Endpoint | Descrição |
|--------|----------|------------|
| POST | `/load_logs.fcgi?session={{session}}` | Carregar logs de acesso |

## Exemplo de Fluxo Completo

### 1. Login
```http
POST {{host}}/hidlogin.fcgi
Content-Type: application/json

{
  "login": "admin",
  "password": "senha"
}
```

**Resposta esperada:**
```json
{
  "session": "abc123token"
}
```

### 2. Verificar Sessão
```http
POST {{host}}/session_is_valid.fcgi?session=abc123token
```

### 3. Abrir Porta
```http
POST {{host}}/open_door_1.fcgi?session=abc123token
```

### 4. Logout
```http
POST {{host}}/logout.fcgi?session=abc123token
```

## Modelo de Dados de Usuário

Os campos retornados pelo endpoint de usuários variam conforme o firmware. Para documentar exatamente, execute o login e colete a resposta real do equipamento.

## Variáveis Postman

| Variável | Descrição | Exemplo |
|----------|------------|---------|
| `host` | IP do equipamento iDFace | `http://192.168.1.100` |
| `session` | Token de sessão | `abc123token` |

## Recomendações de Implementação

1. **Backend como proxy**: Todas as chamadas ao iDFace passam pelo seu backend
2. **Gerenciamento de sessão**: O backend mantém e renova a sessão
3. **Tratamento de erros**: Implementar retry para falhas de rede
4. **Logs**: Registrar todas as operações para auditoria
5. **Timeout**: Definir timeout para requisições (recomendado: 30s)

## Segurança

- Nunca exponha credenciais do iDFace no frontend
- Usar HTTPS em produção
- Implementar rate limiting no backend
- Validar sessão antes de cada operação crítica
- Armazenar logs de acesso para auditoria
