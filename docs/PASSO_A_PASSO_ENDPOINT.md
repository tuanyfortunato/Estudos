# Passo a Passo — Seguindo um Endpoint Camada por Camada

> Esta documentação é um **tutorial "siga o código"**. Em vez de descrever a arquitetura de
> cima para baixo, nós vamos **percorrer o código na ordem em que ele executa**, começando
> pelo endpoint e descendo camada por camada. A cada parada, explico **o que aquela linha
> faz** e **o que cada decorator (`@...`) está fazendo ali**.
>
> Vamos usar como exemplo principal o endpoint **`POST /content`**, por ser o mais simples e
> completo. No final, repetimos o exercício com o `POST /inventory/ask`, que é mais rico.
>
> Se você quer a visão geral da arquitetura e dos conceitos de Python, leia antes o
> <ref_file file="C:\Projetos\Python\Estudos\docs\ARQUITETURA.md" />. Aqui o foco é **seguir o
> fio da execução**.

---

## Mapa do percurso

Quando alguém chama `POST /content`, o código passa por estas paradas, nesta ordem:

```
[0] Servidor sobe a aplicação            → main.py / app.py
       │
[1] Requisição chega no ENDPOINT         → presentation/api/routers/content.py
       │
[2] Validação do corpo (schema)          → presentation/api/schemas.py
       │
[3] Injeção de dependência               → presentation/api/dependencies.py
       │
[4] CASO DE USO (regra de orquestração)  → application/use_cases/generate_content.py
       │
[5] DTOs (entrada/saída do use case)     → application/dtos.py
       │
[6] PORT (a interface que o use case usa)→ domain/ports.py
       │
[7] ADAPTER (implementação concreta)     → infrastructure/ai/gemini_content_generator.py
       │
[8] Resposta volta subindo as camadas
       │
[9] Se deu erro de negócio: handler      → presentation/api/app.py
```

Vamos parada por parada.

---

## [0] Antes de tudo: como o servidor sobe

### `main.py`

<ref_file file="C:\Projetos\Python\Estudos\main.py" />

```python
import uvicorn

def main() -> None:
    uvicorn.run(
        "app.presentation.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

if __name__ == "__main__":
    main()
```

- `uvicorn` é o **servidor** que executa a aplicação (ele "fala HTTP" e chama o seu código).
- A string `"app.presentation.api.app:app"` significa: *"no módulo
  `app/presentation/api/app.py`, pegue a variável chamada `app`"*. O que vem antes dos dois
  pontos é o **caminho do módulo**; o que vem depois é o **nome do objeto**.
- `reload=True` reinicia o servidor sozinho quando você salva um arquivo (modo dev).
- `if __name__ == "__main__":` é um idioma clássico do Python. Ele significa *"só execute
  isto se este arquivo foi rodado diretamente (`python main.py`), e não se ele foi
  importado por outro arquivo"*. Pense nisso como o `public static void main` de Java/C#,
  mas opcional e baseado em convenção.

### `app/presentation/api/app.py`

<ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\app.py" />

Este arquivo tem a **fábrica** da aplicação:

```python
def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version, ...)

    app.include_router(health.router)
    app.include_router(content.router)
    app.include_router(inventory.router)

    _register_exception_handlers(app)
    return app

# ...
app = create_app()   # ← esta é a variável "app" que o uvicorn procura
```

Três coisas acontecem aqui na subida:
1. Cria-se o objeto `FastAPI`.
2. **Registram-se os routers** (`include_router`). Cada router é um grupo de endpoints. É por
   isso que, lá no `main.py`, o uvicorn consegue achar todas as rotas.
3. **Registram-se os handlers de exceção** (voltaremos a eles na parada [9]).

> Por que uma "fábrica" `create_app()` em vez de criar o `app` direto no topo do arquivo?
> Porque assim conseguimos criar instâncias controladas (ex.: nos testes), e mantemos a
> montagem da aplicação organizada em um só lugar.

---

## [1] A requisição chega no ENDPOINT

### `app/presentation/api/routers/content.py`

<ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\routers\content.py" />

```python
router = APIRouter(prefix="/content", tags=["content"])

@router.post(
    "",
    response_model=GenerateContentResponse,
    summary="Gera conteúdo de texto a partir de um prompt",
)
def generate_content(
    payload: GenerateContentRequest,
    use_case: GenerateContentUseCase = Depends(get_generate_content_use_case),
) -> GenerateContentResponse:
    result = use_case.execute(GenerateContentInput(prompt=payload.prompt))
    return GenerateContentResponse(content=result.content)
```

Vamos dissecar **linha por linha**, porque aqui mora muita coisa.

**`router = APIRouter(prefix="/content", tags=["content"])`**
- `APIRouter` é um "mini-app" que agrupa endpoints relacionados.
- `prefix="/content"` faz com que toda rota deste arquivo comece com `/content`.
- `tags=["content"]` só organiza a documentação automática (o `/docs`) em seções.

**O decorator `@router.post("", ...)` — o que ele está fazendo:**
- Este é o decorator mais importante do arquivo. Ele **registra a função `generate_content`
  como o handler do método HTTP POST** na rota `/content` (prefixo `+ ""` = `/content`).
- Sem esse decorator, `generate_content` seria só uma função comum que ninguém chama. O `@`
  é o que a "pendura" na rota.
- `response_model=GenerateContentResponse`: diz ao FastAPI qual o **formato da resposta**.
  Ele usa isso para (a) validar/filtrar o que sai e (b) documentar o endpoint.
- Lembre-se do conceito da seção 2 do outro doc: `@router.post(...)` é o equivalente Python
  do `[HttpPost]` (C#) ou `@PostMapping` (Spring), **mas é literalmente uma função** que
  recebe `generate_content` e a registra na tabela de rotas.

**Os parâmetros da função — de onde vem cada um:**

```python
def generate_content(
    payload: GenerateContentRequest,                                  # (A)
    use_case: GenerateContentUseCase = Depends(get_generate_content_use_case),  # (B)
):
```

- **(A) `payload`** não tem `Depends`, e seu tipo é um schema Pydantic. Por isso o FastAPI
  entende: *"isto vem do **corpo JSON** da requisição"*. Ele lê o JSON, valida contra
  `GenerateContentRequest` (parada [2]) e entrega o objeto já pronto.
- **(B) `use_case`** usa `Depends(...)`. Isto é a **injeção de dependência** do FastAPI:
  antes de chamar `generate_content`, o framework executa `get_generate_content_use_case()`
  (parada [3]) e injeta o resultado aqui. Você nunca constrói o use case "na mão" dentro do
  endpoint — ele chega pronto.

**O corpo da função — a tradução de fronteira:**

```python
result = use_case.execute(GenerateContentInput(prompt=payload.prompt))
return GenerateContentResponse(content=result.content)
```

Repare no padrão: o endpoint **converte** o schema HTTP (`payload`) em um **DTO** da
aplicação (`GenerateContentInput`), chama o use case, e depois **converte** o DTO de saída
(`result`) de volta em um schema HTTP (`GenerateContentResponse`). O endpoint é só um
**tradutor** entre o mundo HTTP e o mundo da aplicação. Ele não tem regra de negócio.

---

## [2] Validação do corpo: o SCHEMA

### `app/presentation/api/schemas.py`

<ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\schemas.py" />

```python
from pydantic import BaseModel, Field

class GenerateContentRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt para geração de conteúdo.")
    model_config = {"json_schema_extra": {"examples": [{"prompt": "Escreva um haicai sobre tecnologia."}]}}

class GenerateContentResponse(BaseModel):
    content: str
```

- `BaseModel` (do **Pydantic**) é a classe-mãe dos schemas. Quem herda dela ganha
  **validação e conversão automática** de dados. Quando o JSON chega, o Pydantic verifica
  se os campos batem com os tipos declarados; se não baterem, devolve **422** automaticamente.
- `prompt: str = Field(..., min_length=1)`:
  - `...` (o `Ellipsis`) como primeiro argumento de `Field` significa **"campo
    obrigatório"**. Se o cliente não mandar `prompt`, dá erro antes de chegar no seu código.
  - `min_length=1` rejeita string vazia. Ou seja, parte da "regra" (prompt não pode ser
    vazio) já é barrada **aqui na entrada**, sem nem chegar ao use case.
- `model_config` com `examples` só alimenta a documentação interativa (`/docs`) com um
  exemplo pronto.

> **Por que o schema é separado do DTO?** O schema é o **contrato HTTP** (o que entra e sai
> pela rede). O DTO (parada [5]) é o **contrato interno** do use case. Mantê-los separados
> permite mudar um sem quebrar o outro. É repetição proposital, em nome do desacoplamento.

---

## [3] Injeção de dependência: o COMPOSITION ROOT

### `app/presentation/api/dependencies.py`

<ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\dependencies.py" />

Este arquivo é o **único lugar** que sabe quais implementações concretas existem e como
montá-las. É chamado de **composition root** ("raiz de composição").

```python
@lru_cache
def get_gemini_client() -> genai.Client:
    settings = get_settings()
    return create_gemini_client(settings.genai_api_key)

def get_generate_content_use_case() -> GenerateContentUseCase:
    settings: Settings = get_settings()
    generator = GeminiContentGenerator(
        client=get_gemini_client(),
        model=settings.gemini_model,
    )
    return GenerateContentUseCase(content_generator=generator)
```

Quando o FastAPI resolve o `Depends(get_generate_content_use_case)` da parada [1], é **esta
função** que roda. Ela:
1. Lê as configurações (`get_settings()`).
2. Cria o **adapter** concreto `GeminiContentGenerator`, passando o client do Gemini e o
   nome do modelo.
3. Cria o **use case**, injetando o adapter nele.
4. Devolve o use case montado.

**O decorator `@lru_cache` — o que ele está fazendo:**
- `lru_cache` (Least Recently Used cache) faz a função **memorizar o resultado**. Na primeira
  chamada, `get_gemini_client()` cria o client do Gemini; nas chamadas seguintes, devolve
  **o mesmo objeto**, sem recriar.
- Efeito prático: vira um **singleton** sem precisar de classe singleton. Isso é importante
  para o client do Gemini (criar conexão é caro) e, no caso do `inventory/ask`, para o
  repositório de conversas (que precisa manter o estado das sessões entre requisições).
- Repare que `get_generate_content_use_case` **não** é cacheado: queremos um use case novo a
  cada requisição (ele é barato), mas com o client cacheado dentro.

---

## [4] O CASO DE USO (a orquestração)

### `app/application/use_cases/generate_content.py`

<ref_file file="C:\Projetos\Python\Estudos\app\application\use_cases\generate_content.py" />

```python
class GenerateContentUseCase:
    def __init__(self, content_generator: ContentGenerator) -> None:
        self._content_generator = content_generator

    def execute(self, data: GenerateContentInput) -> GenerateContentOutput:
        prompt = data.prompt.strip()
        if not prompt:
            raise EmptyPromptError("O prompt não pode estar vazio.")
        content = self._content_generator.generate(prompt)
        return GenerateContentOutput(content=content)
```

Esta é a **regra de orquestração** do negócio. Pontos para um olhar de júnior:

- **`__init__`** é o **construtor** (como o `constructor`/`__construct`). O `self` é o
  equivalente ao `this` — mas no Python ele é **explícito**: todo método de instância recebe
  `self` como primeiro parâmetro.
- **`self._content_generator`**: o `_` na frente é uma **convenção** que diz "atributo
  interno, não mexa de fora". No Python **não existe `private` de verdade** — é um acordo
  entre programadores, não uma regra do compilador.
- **O tipo é `ContentGenerator` (a interface), não `GeminiContentGenerator`.** O use case
  **não sabe** que está falando com o Gemini. Ele só conhece o **contrato** (parada [6]).
  É isso que permite, nos testes, trocar o Gemini por um fake.
- **A regra de negócio mora aqui:** `prompt.strip()` (remove espaços) e, se ficar vazio,
  `raise EmptyPromptError(...)`. Note que ela lança uma **exceção de domínio** — e **não**
  sabe nada sobre "status HTTP 422". Quem traduz isso é a parada [9].

---

## [5] Os DTOs (a "moeda de troca" do use case)

### `app/application/dtos.py`

<ref_file file="C:\Projetos\Python\Estudos\app\application\dtos.py" />

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class GenerateContentInput:
    prompt: str

@dataclass(frozen=True)
class GenerateContentOutput:
    content: str
```

**O decorator `@dataclass(frozen=True)` — o que ele está fazendo:**
- `@dataclass` **gera automaticamente** o construtor (`__init__`), a comparação por valor
  (`__eq__`) e o `__repr__` (texto de debug). É como um `record` de Java/C#. Sem ele, você
  teria que escrever o `__init__` na mão.
- `frozen=True` torna o objeto **imutável**: depois de criado, você não consegue alterar
  `input.prompt`. Isso evita bugs de objetos sendo modificados sem querer no meio do fluxo.

Esses DTOs são objetos bem simples, de propósito. Eles são a interface de **entrada e saída**
do use case, isolada do JSON/HTTP. O endpoint (parada [1]) é quem traduz schema ⇄ DTO.

---

## [6] O PORT (a interface que o use case enxerga)

### `app/domain/ports.py`

<ref_file file="C:\Projetos\Python\Estudos\app\domain\ports.py" />

```python
from typing import Protocol

class ContentGenerator(Protocol):
    def generate(self, prompt: str) -> str:
        ...
```

Esta é a peça-chave da arquitetura. Quando o use case chama
`self._content_generator.generate(prompt)`, **na cabeça dele** ele está chamando este
contrato — não a implementação concreta.

- `Protocol` é o jeito do Python de declarar **interface**. A diferença para Java/C#: é
  **tipagem estrutural** ("duck typing"). A classe `GeminiContentGenerator` **não precisa**
  escrever `class GeminiContentGenerator(ContentGenerator)` para "valer" como um. Basta ela
  **ter** um método `generate(self, prompt: str) -> str`. Se tem o método certo, ela "é" um
  `ContentGenerator` para o verificador de tipos. (Neste projeto o adapter até herda
  explicitamente, mas isso é opcional com `Protocol`.)
- O corpo `...` (três pontos) é literalmente "nada aqui" — é só a **assinatura** do contrato,
  sem implementação.

> Por que o port vive em `domain` e não junto do adapter? Porque é o **domínio quem dita as
> regras**: ele declara "preciso de algo que saiba gerar conteúdo". Quem obedece (a
> infraestrutura) é que se adapta. Isso é a **Inversão de Dependência** — a seta de
> dependência aponta para dentro, para o domínio.

---

## [7] O ADAPTER (a implementação concreta)

### `app/infrastructure/ai/gemini_content_generator.py`

<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\ai\gemini_content_generator.py" />

```python
from google import genai
from app.domain.ports import ContentGenerator

class GeminiContentGenerator(ContentGenerator):
    def __init__(self, client: genai.Client, model: str) -> None:
        self._client = client
        self._model = model

    def generate(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        return response.text or ""
```

Aqui o "contrato" vira realidade. Esta é a única parte do fluxo que **realmente conhece o
Google Gemini**.

- `class GeminiContentGenerator(ContentGenerator)`: implementa o port da parada [6].
- `generate(...)` chama o SDK do Gemini e devolve o texto.
- `response.text or ""`: se `response.text` for `None` (ou vazio), o `or ""` devolve string
  vazia. Esse idioma `a or b` é muito comum em Python: significa "use `a`, mas se ele for
  'falsy' (None, "", 0...), use `b`". É um jeito enxuto de dar um valor padrão.

**Por que isolar o Gemini aqui?** Porque amanhã, se você quiser usar OpenAI, Claude, ou um
modelo local, você só cria **outro adapter** que implemente `ContentGenerator` e troca uma
linha no composition root (parada [3]). Nada no use case, nos DTOs ou no domínio muda.

> Curiosidade: o **outro** adapter de IA — o `GeminiInventoryAgent` — tem um detalhe sutil de
> Python (ele propositalmente **não** usa `from __future__ import annotations`, e a ferramenta
> é uma *closure*). Isso é explicado na seção 6 do
> <ref_file file="C:\Projetos\Python\Estudos\docs\ARQUITETURA.md" />. Veremos esse endpoint na
> parada extra mais abaixo.

---

## [8] A resposta volta subindo

Agora o caminho de volta, na ordem inversa:

```
GeminiContentGenerator.generate(prompt)  →  retorna  "haicai..." (str)
        ▲
GenerateContentUseCase.execute(...)      →  embrulha em GenerateContentOutput(content="haicai...")
        ▲
generate_content(...) (endpoint)         →  converte em GenerateContentResponse(content="haicai...")
        ▲
FastAPI                                   →  serializa o schema em JSON, aplica response_model
        ▲
Cliente                                   →  recebe 200 + { "content": "haicai..." }
```

Repare que **cada camada só fala com a camada vizinha** e usa **seu próprio tipo de dado**
(str → DTO → schema → JSON). Ninguém "pula" camadas. É essa disciplina que mantém o projeto
fácil de mudar e testar.

---

## [9] E se der erro de negócio? Os HANDLERS de exceção

Lembra que o use case (parada [4]) faz `raise EmptyPromptError(...)`? Essa exceção **sobe** a
pilha. Mas o cliente HTTP não entende "EmptyPromptError" — ele entende **códigos de status**.
A tradução acontece em:

### `app/presentation/api/app.py`

<ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\app.py" />

```python
def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(EmptyPromptError)
    async def _empty_prompt(_: Request, exc: EmptyPromptError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(ProductNotFoundError)
    @app.exception_handler(ConversationNotFoundError)
    async def _not_found(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(MissingApiKeyError)
    async def _missing_api_key(_: Request, exc: MissingApiKeyError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(DomainError)
    async def _domain_error(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
```

**O decorator `@app.exception_handler(...)` — o que ele está fazendo:**
- Ele **registra** uma função como o tratador de um **tipo de exceção** específico. Quando
  uma `EmptyPromptError` borbulha até o FastAPI, ele procura o handler registrado para esse
  tipo e o executa, devolvendo a resposta HTTP que o handler montar.
- É assim que o **domínio fica limpo de HTTP**: o use case só diz "isto está errado"
  (lançando a exceção), e a borda da API decide "isto vira um 422".

Detalhes que valem explicar para um júnior:
- **Decorators empilhados:** repare que `_not_found` tem **dois** decorators em cima
  (`@app.exception_handler(ProductNotFoundError)` e `@...(ConversationNotFoundError)`). Você
  pode empilhar decorators — ambos os tipos de erro caem no mesmo handler (→ 404).
- **`async def`:** estes handlers são funções **assíncronas** (`async`). No FastAPI, handlers
  podem ser `async` (não bloqueiam o servidor enquanto esperam I/O). Os endpoints deste
  projeto são `def` normal (síncronos), o que também é suportado — o FastAPI roda os
  síncronos num pool de threads. Para o seu fluxo, a diferença é só performance, não lógica.
- **`_: Request`:** o nome `_` é uma convenção para "recebo este parâmetro mas não vou usar".
- **Ordem importa (do específico para o genérico):** `EmptyPromptError`, `ProductNotFound...`
  etc. são todos filhos de `DomainError`. Como existem handlers específicos para eles, esses
  são usados primeiro; qualquer **outro** `DomainError` cai no handler genérico (→ 400). É um
  "catch-all" para erros de negócio não mapeados individualmente.

Fluxo do erro, visualmente:

```
use_case.execute()  →  raise EmptyPromptError("...")
        │  (a exceção sobe sem ser tratada pelo endpoint)
        ▼
FastAPI procura @app.exception_handler(EmptyPromptError)
        ▼
_empty_prompt(...) → JSONResponse(status_code=422, {"detail": "O prompt não pode estar vazio."})
        ▼
Cliente recebe 422 + { "detail": "..." }
```

---

## Parada extra: o mesmo exercício com `POST /inventory/ask`

Esse endpoint segue **exatamente o mesmo formato de camadas**, mas tem dois ingredientes a
mais: **estado de sessão** e **Function Calling**. Vamos seguir os mesmos passos, focando só
no que muda.

### [1’] Endpoint

<ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\routers\inventory.py" />

```python
router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.post("/ask", response_model=AskInventoryResponse, summary="...")
def ask_inventory(
    payload: AskInventoryRequest,
    use_case: AskInventoryAgentUseCase = Depends(get_ask_inventory_use_case),
) -> AskInventoryResponse:
    result = use_case.execute(
        AskInventoryInput(question=payload.question, session_id=payload.session_id)
    )
    return AskInventoryResponse(answer=result.answer, session_id=result.session_id)
```

Mesmíssimo padrão da parada [1]: `@router.post` registra o handler, `payload` vem do JSON,
`use_case` é injetado via `Depends`, e o corpo só traduz schema ⇄ DTO. A diferença é o
campo extra `session_id`.

Há também um segundo endpoint no mesmo arquivo, `GET /inventory/items`, que **não usa use
case** — ele lê o repositório direto, porque é só uma listagem informativa:

```python
@router.get("/items", response_model=list[InventoryItemResponse], summary="...")
def list_items(inventory: InventoryRepository = Depends(get_inventory_repository)):
    return [InventoryItemResponse(nome=i.nome, preco_unitario=i.preco_unitario)
            for i in inventory.list_all()]
```

(Aquele `[... for i in ...]` é uma **list comprehension** — o jeito idiomático do Python de
transformar uma lista em outra, equivalente a um `map`/`select`.)

### [3’] Composition root com estado

<ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\dependencies.py" />

```python
@lru_cache
def get_conversation_repository() -> ConversationRepository:
    return InMemoryConversationRepository()

def get_ask_inventory_use_case() -> AskInventoryAgentUseCase:
    settings = get_settings()
    agent = GeminiInventoryAgent(
        client=get_gemini_client(),
        inventory=get_inventory_repository(),
        model=settings.gemini_model,
        temperature=settings.gemini_temperature,
        system_instruction=settings.agent_system_instruction,
    )
    return AskInventoryAgentUseCase(agent=agent, conversations=get_conversation_repository())
```

Aqui o `@lru_cache` é **essencial**: como `get_conversation_repository()` é cacheado, **todas
as requisições compartilham o mesmo repositório em memória**. É isso que faz o histórico das
sessões "sobreviver" entre uma chamada e outra. (Se não fosse cacheado, cada requisição teria
um repositório vazio e o agente nunca lembraria de nada.)

### [4’] Use case com estado

<ref_file file="C:\Projetos\Python\Estudos\app\application\use_cases\ask_inventory_agent.py" />

```python
def execute(self, data: AskInventoryInput) -> AskInventoryOutput:
    question = data.question.strip()
    if not question:
        raise EmptyPromptError("A pergunta não pode estar vazia.")

    conversation = self._load_or_create(data.session_id)   # 1) recupera ou cria a sessão
    answer = self._agent.answer(conversation.history(), question)  # 2) chama o agente com o histórico

    conversation.add_message(Role.USER, question)           # 3) registra a fala do usuário
    conversation.add_message(Role.ASSISTANT, answer)        #    e a resposta do agente
    self._conversations.save(conversation)                  # 4) persiste

    return AskInventoryOutput(answer=answer, session_id=conversation.session_id)
```

A novidade é o ciclo **carrega → usa histórico → atualiza → salva**. O `_load_or_create`
decide: se veio `session_id` e ele existe, recupera; se veio mas não existe, cria com aquele
id; se não veio, cria uma sessão nova com UUID. Esse UUID volta na resposta para o cliente
reusar na próxima chamada.

### [7’] Adapter do agente: Function Calling

<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\ai\gemini_inventory_agent.py" />

Aqui está a maior diferença de mecânica. Em vez de só mandar um prompt, montamos um **chat
com ferramentas**:

```python
def answer(self, history: list[Message], question: str) -> str:
    config = types.GenerateContentConfig(
        tools=[self._tool],            # ← a ferramenta que o modelo pode "chamar"
        temperature=self._temperature,
        system_instruction=self._system_instruction,
    )
    chat = self._client.chats.create(model=self._model, config=config,
                                     history=self._to_genai_history(history))
    response = chat.send_message(question)
    return response.text or ""
```

E a ferramenta é construída como uma **closure** (uma função criada dentro de outra, que
"lembra" das variáveis do entorno):

```python
@staticmethod
def _build_tool(inventory: InventoryRepository) -> Callable[[str, int], str]:
    def obter_valor_estoque(produto: str, quantidade: int) -> str:
        """Calcula o valor total de um produto em estoque. ..."""
        item = inventory.get(produto)               # ← capturou "inventory" do entorno
        if item is None:
            return f"Produto '{produto}' não encontrado no sistema de inventário."
        total = item.valor_total(quantidade)        # ← regra de negócio no DOMÍNIO
        return f"O valor total para {quantidade} unidades de {produto} é R$ {total:.2f}."
    return obter_valor_estoque
```

Três detalhes que vale um júnior entender (todos com o "porquê" detalhado no outro doc):

- **`@staticmethod`:** marca um método que **não recebe `self`** — não depende da instância.
  É só uma função "morando" dentro da classe por organização.
- **Por que uma closure e não um método (`self.obter_valor_estoque`)?** Porque o SDK do
  Gemini faz `deepcopy` da config a cada mensagem; um método arrastaria o `self` inteiro
  (incluindo o client com locks de thread não copiáveis) e quebraria. A closure captura só o
  `inventory`, que é seguro de copiar.
- **A regra de negócio continua no domínio:** a ferramenta só **delega** para
  `inventory.get(...)` e `item.valor_total(...)`. A camada de IA não calcula preço sozinha.

O ciclo do Function Calling, em palavras: o modelo recebe a pergunta + a lista de
ferramentas, **decide sozinho** que precisa do preço, "chama" `obter_valor_estoque("notebook",
3)`, recebe o resultado em texto, e então redige a resposta final em linguagem natural. Tudo
isso acontece dentro de `chat.send_message(...)`.

---

## Resumo do percurso (cole na parede)

| Parada | Arquivo | Papel | Decorator(s) em destaque |
|--------|---------|-------|--------------------------|
| [0] | `main.py`, `app.py` | Sobe o servidor e monta o app | — |
| [1] | `routers/content.py` | Endpoint: recebe HTTP, traduz p/ DTO | `@router.post` |
| [2] | `schemas.py` | Valida o corpo JSON (Pydantic) | (herança de `BaseModel`) |
| [3] | `dependencies.py` | Monta e injeta as dependências | `@lru_cache` |
| [4] | `use_cases/generate_content.py` | Regra de orquestração | — |
| [5] | `dtos.py` | Entrada/saída do use case | `@dataclass(frozen=True)` |
| [6] | `domain/ports.py` | Interface (contrato) | (classe `Protocol`) |
| [7] | `infrastructure/ai/...` | Implementação concreta (Gemini) | `@staticmethod` (no agente) |
| [8] | (volta) | Resposta sobe camada a camada | — |
| [9] | `app.py` | Traduz exceção de negócio → status HTTP | `@app.exception_handler` |

**A grande lição:** cada camada só conhece a **interface** da próxima, nunca a implementação.
Os decorators são as "ferramentas de plugagem" que ligam tudo: `@router.post` pluga a função
na rota, `@Depends`/`@lru_cache` plugam as dependências, `@dataclass` gera os objetos de
dados, e `@app.exception_handler` pluga a tradução de erros. Entendendo esse esqueleto, você
consegue adicionar um novo endpoint seguindo exatamente o mesmo caminho.
```