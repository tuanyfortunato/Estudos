# Guia do Projeto — AI Studies API

> Documentação didática para quem **já programa em outras linguagens** (Java, C#, JS, etc.)
> mas está chegando agora no **Python**. O objetivo é explicar *como* o projeto funciona,
> *por que* ele foi estruturado assim, e o *fluxo* de cada requisição.

---

## 1. Visão geral

Este é um projeto de **estudos de agentes de IA** usando o **Google Gemini**, exposto como
uma **API REST** com **FastAPI**. Ele tem dois recursos principais:

1. **Geração de conteúdo** (`POST /content`): manda um prompt, recebe um texto. Sem memória.
2. **Agente de inventário** (`POST /inventory/ask`): conversa com um agente que consulta
   preços de produtos via **Function Calling** e **lembra do histórico** por sessão.

A estrutura segue **Clean Architecture** (Arquitetura Limpa). Se você vem de Java/C#, vai
reconhecer muita coisa: interfaces, injeção de dependência, separação em camadas. A
diferença é que o Python faz tudo isso de um jeito mais leve, e este guia mostra como.

---

## 2. Conceitos de Python que você precisa conhecer primeiro

Antes de entender o projeto, vale alinhar alguns conceitos da linguagem que aparecem o
tempo todo no código. Se você já conhece, pode pular para a seção 3.

### 2.1 "Atributos em cima de funções/classes" = **Decorators**

Em C# ou Java você está acostumado com **atributos/anotações** assim:

```csharp
[HttpPost]
public IActionResult Criar(...) { }
```

```java
@Override
public void metodo() { }
```

No Python, o equivalente se chama **decorator** (decorador). É aquele `@alguma_coisa`
escrito **na linha de cima** da função ou classe:

```python
@router.post("/content")          # decorator
def generate_content(...):        # função decorada
    ...
```

A diferença importante em relação a Java/C#: no Python, **um decorator é só uma função
que recebe outra função (ou classe) e devolve uma versão modificada dela**. Não é
"metadado mágico" — é código de verdade que roda. Por exemplo:

```python
@minha_decoracao
def f(): ...

# é exatamente o mesmo que:
def f(): ...
f = minha_decoracao(f)
```

Os decorators que aparecem neste projeto:

| Decorator                  | O que faz                                                                 |
|----------------------------|---------------------------------------------------------------------------|
| `@dataclass`               | Gera automaticamente `__init__`, `__eq__`, etc. para uma classe de dados. |
| `@property`                | Transforma um método em algo que se lê como atributo (getter).            |
| `@staticmethod`            | Método que não recebe `self` (não depende da instância).                  |
| `@lru_cache`               | Memoiza/cacheia o retorno da função (vira um "singleton" prático).        |
| `@router.post` / `.get`    | Registra a função como um endpoint HTTP (FastAPI).                        |
| `@app.exception_handler`   | Registra uma função que trata um tipo de exceção e devolve resposta HTTP. |

### 2.2 `@property` — método que parece atributo

Veja em <ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\config.py" />:

```python
@property
def has_api_key(self) -> bool:
    return bool(self.genai_api_key)
```

Com `@property`, você **chama sem parênteses**: `settings.has_api_key` (e não
`settings.has_api_key()`). É o mesmo conceito de *property* do C# (`get`). Serve para expor
um valor calculado como se fosse um campo, mantendo a lógica encapsulada.

### 2.3 `@dataclass` — classe de dados sem boilerplate

Em <ref_file file="C:\Projetos\Python\Estudos\app\domain\entities.py" />:

```python
@dataclass(frozen=True)
class InventoryItem:
    nome: str
    preco_unitario: float
```

O `@dataclass` gera o construtor, comparação por valor, `repr`, etc. automaticamente —
parecido com `record` no Java/C#. O `frozen=True` torna o objeto **imutável** (não dá para
alterar os campos depois de criado), assim como um `record` imutável.

`field(default_factory=...)` é usado quando o valor padrão precisa ser **criado a cada
instância** (ex.: uma lista nova, um UUID novo). Você **não pode** escrever
`messages: list = []` como padrão, porque essa lista seria compartilhada entre todas as
instâncias (uma pegadinha clássica do Python). Por isso usamos `field(default_factory=list)`.

### 2.4 `Protocol` — interfaces "estruturais"

Em <ref_file file="C:\Projetos\Python\Estudos\app\domain\ports.py" /> você verá:

```python
from typing import Protocol

class InventoryRepository(Protocol):
    def get(self, nome: str) -> InventoryItem | None: ...
    def list_all(self) -> list[InventoryItem]: ...
```

`Protocol` é o jeito do Python de declarar **interfaces**. A grande diferença para Java/C#:
é **duck typing estático**. Uma classe **não precisa** declarar `implements InventoryRepository`.
Se ela *tiver* os métodos `get` e `list_all` com as assinaturas certas, ela já "é" um
`InventoryRepository` para o verificador de tipos. Isso é chamado de **tipagem estrutural**
("se anda como pato e grasna como pato, é um pato").

O `...` (três pontos, literalmente o objeto `Ellipsis`) é só um corpo vazio — significa
"esse método não tem implementação aqui, é só o contrato".

### 2.5 `from __future__ import annotations`

Quase todo arquivo começa com isso. Ele faz as anotações de tipo serem tratadas como
**texto** (avaliadas só quando alguém pede), o que evita erros de import circular e permite
escrever tipos modernos como `str | None` em versões mais antigas. **Exceção importante:**
o arquivo do agente Gemini *não* usa esse import — explicado na seção 6.2.

### 2.6 Type hints não são obrigatórios, mas usamos sempre

`def get(self, nome: str) -> InventoryItem | None:` — os `: str` e `-> ...` são **dicas de
tipo**. O Python **não** as obriga em tempo de execução (o código roda mesmo se estiverem
erradas), mas ferramentas como editores e o `mypy`/`ruff` usam isso para te avisar de erros.
`InventoryItem | None` é o equivalente a `InventoryItem?` (nullable) em C#/Kotlin.

---

## 3. Por que Clean Architecture?

A ideia central da Clean Architecture é a **regra de dependência**: o código de fora
depende do código de dentro, **nunca o contrário**. As camadas, de dentro para fora:

```
        ┌─────────────────────────────────────────┐
        │            presentation (API)           │  ← FastAPI, HTTP, JSON
        │   ┌─────────────────────────────────┐   │
        │   │        application (use cases)   │   │  ← orquestração
        │   │   ┌─────────────────────────┐   │   │
        │   │   │        domain           │   │   │  ← regras de negócio puras
        │   │   │  (entities, ports,      │   │   │
        │   │   │   exceptions)           │   │   │
        │   │   └─────────────────────────┘   │   │
        │   └─────────────────────────────────┘   │
        └─────────────────────────────────────────┘
              infrastructure aponta para o domain ↑
```

- **`domain`** não importa **nada** de fora (nem FastAPI, nem Gemini, nem Pydantic). É Python
  puro. Isso o torna fácil de testar e independente de tecnologia.
- **`application`** depende só do `domain`.
- **`infrastructure`** e **`presentation`** dependem do `domain`/`application`, mas o miolo
  nunca depende delas.

**Por que isso importa?** Porque você pode trocar o Gemini por outro modelo, ou o repositório
em memória por um banco de dados real, **sem tocar nas regras de negócio**. As camadas
internas só conhecem **interfaces** (os `Protocol`s), não implementações concretas. Isso é o
**Princípio da Inversão de Dependência** (o "D" de SOLID) na prática.

---

## 4. O que tem em cada pasta

```
app/
├── domain/                     # O CORAÇÃO. Regras de negócio puras, sem frameworks.
│   ├── entities.py             # InventoryItem, Conversation, Message, Role
│   ├── exceptions.py           # Exceções de negócio (DomainError e filhas)
│   └── ports.py                # Interfaces (Protocol): repositórios e serviços de IA
│
├── application/                # CASOS DE USO. Orquestram o domínio.
│   ├── dtos.py                 # Objetos simples de entrada/saída dos use cases
│   └── use_cases/
│       ├── generate_content.py
│       └── ask_inventory_agent.py
│
├── infrastructure/             # DETALHES TÉCNICOS. Implementações concretas (adapters).
│   ├── config.py               # Configuração via variáveis de ambiente (pydantic-settings)
│   ├── ai/                     # Adapters do Google Gemini
│   │   ├── client_factory.py
│   │   ├── gemini_content_generator.py
│   │   └── gemini_inventory_agent.py
│   └── persistence/            # Repositórios (aqui, em memória)
│       ├── in_memory_conversation_repository.py
│       └── static_inventory_repository.py
│
└── presentation/               # ENTRADA. A API HTTP.
    └── api/
        ├── app.py              # Cria o FastAPI + handlers de exceção
        ├── dependencies.py     # Composition root (injeção de dependência)
        ├── schemas.py          # Modelos Pydantic do contrato HTTP (request/response)
        └── routers/            # Os endpoints
            ├── content.py
            ├── health.py
            └── inventory.py
```

E na raiz:

| Arquivo                | Para que serve                                                       |
|------------------------|----------------------------------------------------------------------|
| `main.py`              | Ponto de entrada; sobe o servidor uvicorn.                           |
| `pyproject.toml`       | Metadados do projeto + config do `pytest` e do `ruff` (linter).      |
| `requirements*.txt`    | Lista de dependências (prod e dev).                                  |
| `Dockerfile` / compose | Empacotamento e execução em container.                              |
| `.env`                 | Variáveis de ambiente (ex.: `GENAI_API_KEY`). **Não vai pro git.**  |
| `tests/`               | Testes unitários e de integração.                                    |

### Por que tantos `__init__.py` vazios?

Cada pasta tem um arquivo `__init__.py` (muitas vezes vazio). No Python, ele marca a pasta
como um **pacote** (package), permitindo o `import app.domain.entities`. É um detalhe da
linguagem — pense nele como um "marcador de namespace".

---

## 5. As camadas em detalhe

### 5.1 Domain (domínio)

**Entidades** — <ref_file file="C:\Projetos\Python\Estudos\app\domain\entities.py" />.
São os conceitos centrais do negócio:

- `InventoryItem` (imutável): um produto com `nome` e `preco_unitario`, e o método de
  negócio `valor_total(quantidade)`.
- `Role`: um `Enum` (`USER` / `ASSISTANT`). Repare que herda de `str` **e** de `Enum`
  (`class Role(str, Enum)`) — isso o torna serializável diretamente como string.
- `Message` (imutável): uma fala dentro da conversa.
- `Conversation` (mutável): tem `session_id` e uma lista de mensagens. Métodos como
  `add_message` e `history` encapsulam o estado.

Repare que **toda a lógica de negócio vive aqui**, não na camada de IA nem na API. Ex.: o
cálculo `preco_unitario * quantidade` está dentro de `InventoryItem.valor_total`.

**Ports** — <ref_file file="C:\Projetos\Python\Estudos\app\domain\ports.py" />. São as
interfaces (`Protocol`) que o domínio "pede" que alguém implemente:
`InventoryRepository`, `ConversationRepository`, `ContentGenerator`, `InventoryAgent`.

**Exceptions** — <ref_file file="C:\Projetos\Python\Estudos\app\domain\exceptions.py" />.
Erros de negócio têm tipos próprios (`EmptyPromptError`, `ProductNotFoundError`, etc.) que
herdam de `DomainError`. O domínio lança essas exceções **sem saber nada de HTTP**. Quem
traduz para código 404/422 é a camada de apresentação (seção 5.4).

### 5.2 Application (casos de uso)

Um **use case** é uma classe que orquestra um fluxo de negócio. Ela recebe suas dependências
**pelo construtor** (injeção de dependência) e expõe um método `execute`.

`GenerateContentUseCase` — <ref_file file="C:\Projetos\Python\Estudos\app\application\use_cases\generate_content.py" />:

```python
class GenerateContentUseCase:
    def __init__(self, content_generator: ContentGenerator) -> None:
        self._content_generator = content_generator  # depende da INTERFACE

    def execute(self, data: GenerateContentInput) -> GenerateContentOutput:
        prompt = data.prompt.strip()
        if not prompt:
            raise EmptyPromptError("O prompt não pode estar vazio.")
        content = self._content_generator.generate(prompt)
        return GenerateContentOutput(content=content)
```

Note dois pontos importantes:
- O atributo `self._content_generator` tem `_` na frente. No Python **não existe `private`
  de verdade**; o `_` é uma **convenção** que diz "isto é interno, não mexa de fora".
- O tipo do parâmetro é `ContentGenerator` (o `Protocol`), **não** `GeminiContentGenerator`.
  Por isso o use case não sabe que está falando com o Gemini — poderia ser qualquer coisa.

`AskInventoryAgentUseCase` — <ref_file file="C:\Projetos\Python\Estudos\app\application\use_cases\ask_inventory_agent.py" />.
O fluxo dele (documentado no próprio docstring):
1. Recupera (ou cria) a conversa pelo `session_id`.
2. Chama o agente passando histórico + nova pergunta.
3. Salva as mensagens do usuário e do assistente.
4. Devolve a resposta e o `session_id`.

**DTOs** — <ref_file file="C:\Projetos\Python\Estudos\app\application\dtos.py" />. São
`@dataclass`es simples de entrada/saída. **Por que existem se já temos os schemas Pydantic
da API?** Para **desacoplar**: o contrato HTTP (schemas) pode mudar sem afetar os use cases,
e vice-versa. Os routers convertem schema ⇄ DTO na fronteira.

### 5.3 Infrastructure (implementações concretas)

São os **adapters**: classes que implementam os ports do domínio usando tecnologia real.

- `StaticInventoryRepository` <ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\persistence\static_inventory_repository.py" />:
  preços fixos num dicionário. Implementa `InventoryRepository`. Num projeto real, viraria um
  adapter de banco de dados — **e o domínio nem ficaria sabendo**.
- `InMemoryConversationRepository` <ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\persistence\in_memory_conversation_repository.py" />:
  guarda conversas num `dict` protegido por `threading.Lock` (thread-safe). Em produção,
  seria Redis ou banco.
- `GeminiContentGenerator` e `GeminiInventoryAgent` (pasta `ai/`): falam com o SDK do Gemini.
- `config.py`: configuração tipada via `pydantic-settings` (seção 6.1).

### 5.4 Presentation (a API)

`app.py` <ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\app.py" /> tem a
**fábrica** `create_app()` que monta o FastAPI, registra os routers e os **handlers de
exceção**. É aqui que as exceções de domínio viram respostas HTTP:

```python
@app.exception_handler(EmptyPromptError)
async def _empty_prompt(_: Request, exc: EmptyPromptError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})
```

Mapeamento atual: `EmptyPromptError → 422`, `ProductNotFoundError`/`ConversationNotFoundError
→ 404`, `MissingApiKeyError → 503`, e qualquer outro `DomainError → 400`. **Essa é a "cola"
entre o mundo do negócio e o mundo HTTP** — graças a ela, os use cases nunca precisam saber
o que é um "status 404".

`schemas.py` <ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\schemas.py" />:
modelos **Pydantic** (`BaseModel`). O Pydantic **valida e converte** os dados que chegam no
JSON automaticamente. Ex.: `prompt: str = Field(..., min_length=1)` — o `...` significa
"obrigatório", e `min_length=1` rejeita string vazia já na entrada (devolvendo 422 antes
mesmo de chegar ao use case).

`routers/` são os endpoints, agrupados por assunto com `APIRouter(prefix=..., tags=...)`.

---

## 6. Decisões importantes (o "porquê")

### 6.1 Configuração tipada com `pydantic-settings` e `@lru_cache`

<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\config.py" />. Em vez de
espalhar `os.getenv("...")` pelo código, centralizamos tudo numa classe `Settings` que lê do
`.env` e **valida tipos**. A função `get_settings()` é decorada com `@lru_cache`:

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

`@lru_cache` faz a função **lembrar do resultado**: a primeira chamada cria o objeto, as
seguintes devolvem o mesmo. Na prática, isso transforma `get_settings()` num **singleton**
sem precisar de classe singleton. O mesmo truque é usado em `dependencies.py` para o client
do Gemini e o repositório de conversas (que precisam ser compartilhados entre requisições
para manter estado).

### 6.2 Por que o agente Gemini NÃO usa `from __future__ import annotations`

Este é o detalhe mais sutil do projeto. Veja o topo de
<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\ai\gemini_inventory_agent.py" />.

O SDK do Gemini, ao fazer **Function Calling**, inspeciona as anotações de tipo da sua
função-ferramenta **em tempo de execução** (faz `isinstance(valor, anotação)`). Se as
anotações virassem **strings** (que é o efeito do `from __future__ import annotations`), o
`isinstance` quebraria com `isinstance() arg 2 must be a type`. Por isso, **só nesse arquivo**
as anotações precisam ser tipos reais.

### 6.3 Por que a ferramenta é uma função (closure) e não um método

Ainda em `gemini_inventory_agent.py`, a ferramenta `obter_valor_estoque` é criada dentro de
`_build_tool` como uma **closure** que captura o `inventory`:

```python
@staticmethod
def _build_tool(inventory: InventoryRepository) -> Callable[[str, int], str]:
    def obter_valor_estoque(produto: str, quantidade: int) -> str:
        item = inventory.get(produto)
        ...
    return obter_valor_estoque
```

Motivo: o SDK faz `deepcopy` da configuração a cada mensagem. Se a ferramenta fosse um
**método bound** (`self.obter_valor_estoque`), o `deepcopy` arrastaria o `self` inteiro —
incluindo o `client` do Gemini, que contém **locks de thread não copiáveis**, causando o erro
`cannot pickle '_thread.lock'`. A closure captura apenas o `inventory` (objeto simples e
seguro de copiar). Repare também que **a regra de negócio fica no domínio**: a ferramenta só
delega para `inventory.get(...)` e `item.valor_total(...)`.

### 6.4 Sessões com estado controladas pela aplicação

Em vez de confiar no objeto de chat do SDK para guardar o histórico, **nós** persistimos a
conversa no `ConversationRepository` e **reenviamos** o histórico ao modelo a cada chamada
(método `_to_genai_history`). Isso nos dá controle total sobre o estado e funciona mesmo se o
processo do SDK for descartado entre requisições.

---

## 7. Fluxo de uma requisição (passo a passo)

Aqui está o coração do que você pediu: o que acontece, em ordem, quando cada endpoint é
chamado.

### 7.0 Como a injeção de dependência do FastAPI funciona

Repare que os endpoints têm parâmetros assim:

```python
def generate_content(
    payload: GenerateContentRequest,
    use_case: GenerateContentUseCase = Depends(get_generate_content_use_case),
):
```

- `payload` (sem `Depends`) → o FastAPI entende que vem do **corpo JSON** da requisição,
  e valida usando o schema Pydantic.
- `use_case = Depends(get_generate_content_use_case)` → o FastAPI **chama a função
  `get_generate_content_use_case()`** (do `dependencies.py`) e injeta o resultado. É a
  injeção de dependência nativa do framework. O **composition root** (`dependencies.py`) é
  quem monta o objeto com todas as suas dependências concretas.

---

### 7.1 `GET /health`

O mais simples, bom para aquecer.

```
Cliente ──GET /health──▶ FastAPI
                           │
                           ▼
             health(settings = Depends(get_settings))
                           │   (get_settings() devolve o Settings cacheado)
                           ▼
             retorna {status, app, version, gemini_configured}
                           │
Cliente ◀──── 200 + JSON ──┘
```

Definido em <ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\routers\health.py" />.
Não toca em use case nem em IA; só reporta o estado da config.

---

### 7.2 `POST /content` — geração de conteúdo

Router: <ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\routers\content.py" />.

```
Cliente
  │  POST /content  { "prompt": "Escreva um haicai..." }
  ▼
FastAPI valida o JSON com GenerateContentRequest (Pydantic)
  │     ├─ se prompt vazio/ausente → 422 automático (min_length=1)
  ▼
Depends(get_generate_content_use_case)
  │     monta GenerateContentUseCase(GeminiContentGenerator(client, model))
  ▼
generate_content(payload, use_case)
  │     converte schema → DTO:  GenerateContentInput(prompt=payload.prompt)
  ▼
use_case.execute(input)
  │     ├─ prompt.strip(); se vazio → raise EmptyPromptError  ──┐
  │     └─ content_generator.generate(prompt)                    │
  ▼                                                              │
GeminiContentGenerator.generate(prompt)                          │
  │     client.models.generate_content(model, contents=prompt)   │
  │     ◀── texto do Gemini                                      │
  ▼                                                              │
retorna GenerateContentOutput(content=...)                       │
  ▼                                                              │
router converte DTO → schema: GenerateContentResponse(content)   │
  ▼                                                              │
Cliente ◀── 200 + { "content": "..." }                          │
                                                                 │
   (se EmptyPromptError foi lançada) ───────────────────────────┘
        exception_handler em app.py → 422 + {"detail": "..."}
```

**Resumo do fluxo de dados:** JSON → schema Pydantic → DTO → use case → port
(`ContentGenerator`) → adapter Gemini → texto → DTO → schema → JSON. Cada seta cruza uma
fronteira de camada, e cada camada só conhece a interface da próxima.

---

### 7.3 `POST /inventory/ask` — agente com estado e Function Calling

O mais rico. Router: <ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\routers\inventory.py" />.

```
Cliente
  │  POST /inventory/ask  { "question": "Cote 3 notebooks", "session_id": null }
  ▼
FastAPI valida com AskInventoryRequest (Pydantic)
  ▼
Depends(get_ask_inventory_use_case)
  │   monta AskInventoryAgentUseCase(
  │       agent = GeminiInventoryAgent(client, inventory, model, temp, sys_instruction),
  │       conversations = InMemoryConversationRepository()  ← cacheado (@lru_cache)
  │   )
  ▼
ask_inventory(payload, use_case)
  │   schema → DTO:  AskInventoryInput(question, session_id)
  ▼
use_case.execute(input)
  │   1) question.strip(); se vazio → EmptyPromptError → 422
  │   2) _load_or_create(session_id):
  │        ├─ session_id existe no repo? devolve a Conversation salva
  │        ├─ session_id veio mas não existe? cria Conversation(session_id=...)
  │        └─ session_id é None? cria Conversation() com UUID novo
  │   3) agent.answer(conversation.history(), question)  ────────────┐
  │   4) conversation.add_message(USER, question)                    │
  │      conversation.add_message(ASSISTANT, answer)                 │
  │   5) conversations.save(conversation)   (com lock, thread-safe)  │
  ▼                                                                  │
retorna AskInventoryOutput(answer, session_id)                       │
  ▼                                                                  │
DTO → schema: AskInventoryResponse(answer, session_id)               │
  ▼                                                                  │
Cliente ◀── 200 + { "answer": "...", "session_id": "uuid..." }      │
                                                                     │
        ┌────────────────────────────────────────────────────────────┘
        ▼  (dentro de agent.answer — onde o Function Calling acontece)
GeminiInventoryAgent.answer(history, question)
  │   monta GenerateContentConfig(tools=[obter_valor_estoque], temperature, system_instruction)
  │   converte o histórico do domínio → formato do Gemini (_to_genai_history)
  │   abre um chat com esse histórico e envia a question
  ▼
   O modelo decide: "preciso do preço" → chama a ferramenta obter_valor_estoque("notebook", 3)
  │   a closure chama inventory.get("notebook") → InventoryItem
  │   item.valor_total(3) = 4500 * 3 = 13500.00   ← regra de negócio no domínio
  │   devolve a string ao modelo
  ▼
   O modelo gera a resposta final em linguagem natural usando esse resultado
  └── response.text ──▶ volta para o use case (passo 3 acima)
```

**Pontos-chave do estado/sessão:**
- Na **1ª chamada** sem `session_id`, nasce uma conversa nova com UUID. Esse UUID volta no
  campo `session_id` da resposta.
- Na **2ª chamada**, o cliente manda o mesmo `session_id`. O use case recupera a conversa
  salva, e o histórico anterior é reenviado ao modelo — por isso o agente "lembra" do que foi
  dito antes.
- Como `get_conversation_repository()` é `@lru_cache`, **o mesmo repositório** (com as
  conversas em memória) é reusado entre requisições. Reiniciar o processo **apaga** tudo
  (é em memória) — em produção, trocaríamos por Redis/banco.

---

### 7.4 `GET /inventory/items`

```
Cliente ──GET /inventory/items──▶ FastAPI
                                    │  Depends(get_inventory_repository)  (cacheado)
                                    ▼
                          list_items(inventory)
                                    │  inventory.list_all() → [InventoryItem, ...]
                                    │  converte cada um → InventoryItemResponse
                                    ▼
Cliente ◀── 200 + [ {nome, preco_unitario}, ... ]
```

Não usa use case porque é só uma leitura direta do repositório — uma decisão pragmática para
um endpoint puramente informativo.

---

## 8. Como rodar e testar

**Rodar a API** (a partir da raiz do projeto):

```bash
# 1. ambiente virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 2. dependências
pip install -r requirements-dev.txt

# 3. configurar a chave no .env
#    GENAI_API_KEY=sua_chave

# 4. subir
python main.py
# ou: uvicorn app.presentation.api.app:app --reload
```

Acesse a documentação interativa (gerada automaticamente pelo FastAPI):
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**Testes:**

```bash
pytest
```

Os testes usam **fakes** dos ports de IA (veja `tests/fakes.py`), então **não fazem chamadas
reais** ao Gemini. Isso é possível justamente porque os use cases dependem de **interfaces**
(`Protocol`): nos testes, injetamos uma implementação falsa no lugar do Gemini. É a maior
vantagem prática da arquitetura — testes rápidos e determinísticos.

A estrutura dos testes espelha a do código:
- `tests/unit/` — testa domínio, repositórios e use cases isoladamente.
- `tests/integration/` — sobe a API e testa os endpoints de ponta a ponta.

---

## 9. Resumo mental

1. **Domínio no centro**, sem dependências externas. Toda regra de negócio mora aqui.
2. **Use cases orquestram** o domínio e dependem só de **interfaces** (`Protocol`).
3. **Infraestrutura implementa** essas interfaces com tecnologia real (Gemini, memória).
4. **Apresentação** traduz HTTP ⇄ aplicação e mapeia exceções de negócio para status HTTP.
5. **Composition root** (`dependencies.py`) é o único lugar que conhece as peças concretas e
   as monta — usando `@lru_cache` para singletons e `Depends` para injetar nos endpoints.
6. **Decorators** (`@property`, `@dataclass`, `@lru_cache`, `@router.post`...) são o
   equivalente Python dos atributos/anotações que você já conhece — só que são funções de
   verdade que transformam o que está logo abaixo delas.
```