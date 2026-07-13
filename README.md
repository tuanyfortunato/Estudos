# AI Studies API

Projeto de **estudos de agentes de IA** com Google Gemini, estruturado em
**Clean Architecture** e exposto via **API REST (FastAPI)**.

Inclui dois casos de uso:

1. **Geração de conteúdo** (sem estado) a partir de um prompt.
2. **Agente de inventário** com **Function Calling** automático e **sessões com
   estado** (histórico de conversa por `session_id`).

## Arquitetura

O código segue Clean Architecture, com dependências sempre apontando para
dentro (regra de dependência). Cada camada só conhece a camada mais interna:

```
app/
├── domain/                     # Regras de negócio puras (sem frameworks)
│   ├── entities.py             # InventoryItem, Conversation, Message, Role
│   ├── exceptions.py           # Exceções de domínio
│   └── ports.py                # Interfaces (Protocol): repositórios e serviços de IA
├── application/                # Casos de uso (orquestração)
│   ├── dtos.py                 # DTOs de entrada/saída
│   └── use_cases/
│       ├── generate_content.py
│       └── ask_inventory_agent.py
├── infrastructure/             # Implementações concretas (adapters)
│   ├── config.py               # Pydantic Settings (variáveis de ambiente)
│   ├── ai/                     # Adapters do Google Gemini
│   └── persistence/            # Repositórios em memória
└── presentation/               # Camada de entrada (API)
    └── api/
        ├── app.py              # Fábrica do FastAPI + handlers de exceção
        ├── dependencies.py     # Composition root (injeção de dependências)
        ├── schemas.py          # Modelos Pydantic de transporte (HTTP)
        └── routers/            # Endpoints
```

**Regra de dependência:** `presentation → application → domain` e
`infrastructure → domain`. O domínio não importa nada de fora; as
implementações concretas são injetadas no *composition root*
(`dependencies.py`).

## Configuração

### 1. Ambiente virtual e dependências

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements-dev.txt
```

### 2. Variáveis de ambiente

```bash
cp .env.example .env
```

Edite o `.env` e informe sua chave:

```
GENAI_API_KEY=sua_api_key_aqui
```

> Crie uma chave em https://ai.google.dev/gemini-api/docs/api-key

## Execução

```bash
python main.py
# ou
uvicorn app.presentation.api.app:app --reload
```

A API sobe em `http://localhost:8000`. Documentação interativa:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

| Método | Rota               | Descrição                                          |
|--------|--------------------|----------------------------------------------------|
| GET    | `/health`          | Status da aplicação                                |
| POST   | `/content`         | Gera conteúdo a partir de um prompt                |
| POST   | `/inventory/ask`   | Conversa com o agente de inventário (com sessão)   |
| GET    | `/inventory/items` | Lista os itens disponíveis no inventário           |

### Exemplos

Geração de conteúdo:

```bash
curl -X POST http://localhost:8000/content \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Escreva um haicai sobre tecnologia."}'
```

Agente de inventário (mantendo a sessão entre chamadas):

```bash
# 1ª chamada (sem session_id -> cria nova sessão)
curl -X POST http://localhost:8000/inventory/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Preciso cotar o preço de 3 notebooks."}'

# resposta inclui "session_id"; reutilize-o para continuar a conversa
curl -X POST http://localhost:8000/inventory/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "E quanto custam 2 monitores?", "session_id": "<SESSION_ID>"}'
```

## Testes

```bash
pytest
```

Os testes usam *fakes* dos ports de IA, portanto **não fazem chamadas reais**
ao Gemini — são rápidos e determinísticos.

## Docker

```bash
docker compose up --build
```

A API ficará disponível em `http://localhost:8000` (lê o `.env` automaticamente).

## Boas práticas de agentes de IA aplicadas

- **Ferramentas como funções, não métodos bound:** o SDK faz `deepcopy` da
  config a cada mensagem; um método bound arrastaria o client (com locks de
  thread não copiáveis), causando `cannot pickle '_thread.lock'`.
- **Lógica de negócio fora da camada de IA:** a ferramenta de preços delega ao
  `InventoryRepository` do domínio.
- **Sessões com estado controladas pela aplicação:** o histórico é persistido em
  um repositório do domínio e reenviado ao modelo, em vez de depender do ciclo
  de vida do objeto de chat do SDK.
- **Configuração tipada e validada** via `pydantic-settings`.
- **Inversão de dependência:** use cases dependem de interfaces (`Protocol`),
  não de implementações concretas.
