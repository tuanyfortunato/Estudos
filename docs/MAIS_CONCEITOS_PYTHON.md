# Mais Conceitos de Python (usados no projeto)

> Este documento é um **complemento** aos guias anteriores. Ele cobre conceitos de Python que
> **aparecem no código deste projeto** mas que ainda **não tinham sido explicados** em
> <ref_file file="C:\Projetos\Python\Estudos\docs\PYTHON_PARA_DEV_CSHARP.md" />,
> <ref_file file="C:\Projetos\Python\Estudos\docs\ARQUITETURA.md" /> ou
> <ref_file file="C:\Projetos\Python\Estudos\docs\PASSO_A_PASSO_ENDPOINT.md" />.
>
> Mantemos a mesma pegada didática: comparações com **C#** e exemplos tirados do código real.
> Leia depois dos outros três.

---

## Índice

1. [O `with` e os context managers](#1-with-context-managers)
2. [Concorrência: `threading.Lock` e o GIL](#2-concorrencia)
3. [Funções em nível de módulo (sem classe estática)](#3-funcoes-de-modulo)
4. [Referências de objeto, mutabilidade e cópia defensiva](#4-referencias-e-mutabilidade)
5. [Herança e herança múltipla](#5-heranca)
6. [A biblioteca padrão usada no projeto](#6-biblioteca-padrao)
7. [Pydantic em profundidade](#7-pydantic)
8. [`tuple` como tipo e desempacotamento](#8-tuple-desempacotamento)
9. [Fixtures do pytest](#9-fixtures-pytest)
10. [Tabela-resumo](#10-tabela-resumo)

---

<a name="1-with-context-managers"></a>
## 1. O `with` e os context managers

O bloco `with` garante que um recurso seja **aberto e fechado/liberado corretamente**, mesmo
se ocorrer uma exceção no meio. É o equivalente direto do **`using`** do C#.

No projeto, ele aparece no repositório de conversas,
<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\persistence\in_memory_conversation_repository.py" />:

```python
def get(self, session_id: str) -> Conversation | None:
    with self._lock:
        return self._store.get(session_id)

def save(self, conversation: Conversation) -> None:
    with self._lock:
        self._store[conversation.session_id] = conversation
```

```csharp
// C# equivalente (lock é açúcar para Monitor.Enter/Exit em try/finally)
lock (_lock)
{
    return _store.GetValueOrDefault(sessionId);
}
```

Como funciona:

- `with self._lock:` **adquire** o lock ao entrar no bloco e **libera** ao sair — *garantido*,
  mesmo que uma exceção seja lançada lá dentro. Sem `with`, você teria que escrever
  `acquire()` / `try` / `finally release()` na mão.
- Qualquer objeto que implemente os "dunder methods" `__enter__` e `__exit__` é um **context
  manager** e pode ser usado com `with`. O `__enter__` roda na entrada; o `__exit__` roda na
  saída (e recebe a informação de exceção, se houver).

O uso mais comum que você verá por aí é abrir arquivos:

```python
with open("arquivo.txt") as f:   # f é fechado automaticamente ao sair do bloco
    conteudo = f.read()
# aqui o arquivo JÁ está fechado
```

> **Regra mental:** se há um recurso que precisa ser "fechado/devolvido" (lock, arquivo,
> conexão, transação), procure um `with`. É o `using` do Python.

---

<a name="2-concorrencia"></a>
## 2. Concorrência: `threading.Lock` e o GIL

Por que o repositório precisa de um lock? Porque um servidor web atende **várias requisições
ao mesmo tempo**. Se duas requisições mexerem no mesmo dicionário simultaneamente, pode haver
corrupção de dados (condição de corrida). O lock serializa o acesso.

<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\persistence\in_memory_conversation_repository.py" />:

```python
import threading

class InMemoryConversationRepository:
    def __init__(self) -> None:
        self._store: dict[str, Conversation] = {}
        self._lock = threading.Lock()     # cria o cadeado
```

- `threading.Lock()` cria um **cadeado**. Só uma thread por vez consegue entrar num bloco
  `with self._lock:` (seção 1). É o mesmo conceito do `lock`/`Monitor` do C#.

### E o tal do GIL?

Aqui há uma diferença cultural importante em relação ao C#/.NET. O CPython (o interpretador
padrão) tem o **GIL** (*Global Interpreter Lock*): **apenas uma thread executa bytecode Python
por vez**. Consequências práticas:

- Para trabalho **CPU-bound** (cálculo pesado), threads **não** dão paralelismo real — usa-se
  `multiprocessing` (vários processos) nesses casos.
- Para trabalho **I/O-bound** (rede, disco — o caso de uma API), threads e `async` funcionam
  muito bem, porque enquanto uma thread espera I/O, outra roda.

> **Atenção:** o GIL **não** torna seu código automaticamente thread-safe para estruturas de
> dados compostas. Operações como "ler do dict, decidir, escrever no dict" ainda precisam de
> lock — e é exatamente por isso que este repositório usa um. Não confie no GIL para
> sincronização.

Para a sua API neste projeto: os endpoints síncronos rodam em um *pool de threads* do FastAPI,
então o lock protege o dicionário compartilhado de conversas. Correto e necessário.

---

<a name="3-funcoes-de-modulo"></a>
## 3. Funções em nível de módulo (sem classe estática)

Em C#, **todo método precisa morar dentro de uma classe** — por isso você cria classes
`static` só para agrupar funções utilitárias (`public static class Helpers`). No Python,
**funções podem viver soltas no módulo**, sem classe nenhuma.

Veja o topo de <ref_file file="C:\Projetos\Python\Estudos\app\domain\entities.py" />:

```python
def _now() -> datetime:
    return datetime.now(timezone.utc)

def _new_id() -> str:
    return str(uuid.uuid4())
```

Essas são duas funções "soltas" no módulo `entities`. Elas são usadas como *factories* dos
campos das dataclasses:

```python
@dataclass(frozen=True)
class Message:
    role: Role
    content: str
    created_at: datetime = field(default_factory=_now)   # passa a função (sem parênteses!)
```

Pontos para quem vem de C#:

- O `_` no nome (`_now`, `_new_id`) é a convenção de "privado do módulo" — não é para ser
  importado de fora.
- `field(default_factory=_now)` passa **a função em si** (sem `()`), não o resultado. O Python
  chama `_now()` a cada nova instância. (Funções são objetos de primeira classe — veja seção
  18 do guia de fundamentos.)
- **O módulo já é o seu "namespace de funções utilitárias".** Não precisa de classe estática.

A constante `_PRECOS_PADRAO` em
<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\persistence\static_inventory_repository.py" />
segue a mesma ideia: é uma variável de **nível de módulo** (não um campo de classe), em
`UPPER_SNAKE_CASE` por ser constante.

---

<a name="4-referencias-e-mutabilidade"></a>
## 4. Referências de objeto, mutabilidade e cópia defensiva

Como em C# com tipos de referência, **variáveis em Python guardam referências para objetos**,
não cópias. Se você passar uma `list` para uma função e ela alterar a lista, a alteração é
vista por todo mundo que tem a referência. Isso causa bugs sutis se você não tomar cuidado.

O projeto trata isso explicitamente em
<ref_file file="C:\Projetos\Python\Estudos\app\domain\entities.py" />:

```python
@dataclass
class Conversation:
    messages: list[Message] = field(default_factory=list)

    def history(self) -> list[Message]:
        """Retorna uma cópia imutável do histórico atual."""
        return list(self.messages)     # ← cria uma NOVA lista (cópia rasa)
```

Por que `return list(self.messages)` em vez de `return self.messages`?

- `return self.messages` devolveria a **mesma** lista interna. Quem recebesse poderia fazer
  `.append(...)` e **alterar o estado interno** da `Conversation` por fora — quebrando o
  encapsulamento.
- `list(self.messages)` cria uma **nova lista** com os mesmos elementos (uma *cópia rasa*).
  Quem recebe pode mexer à vontade sem afetar a conversa original. É uma **cópia defensiva**.

Isso conversa com outra decisão de design: `Message` e `InventoryItem` são
`@dataclass(frozen=True)` — **imutáveis**. Como os elementos não podem ser alterados, a cópia
rasa da lista é suficiente (ninguém consegue mutar um `Message` por dentro).

> **Pegadinha relacionada (já citada nos outros docs):** nunca use `[]`, `{}` como valor padrão
> de parâmetro/campo — eles seriam compartilhados entre todas as instâncias. Por isso usa-se
> `field(default_factory=list)`. É a mesma armadilha de referência, vista de outro ângulo.

| C#                          | Python                              |
|-----------------------------|-------------------------------------|
| `new List<T>(original)`     | `list(original)`                    |
| `IReadOnlyList<T>` / cópia  | retornar `list(...)` (cópia defensiva) |
| `record` imutável           | `@dataclass(frozen=True)`           |

---

<a name="5-heranca"></a>
## 5. Herança e herança múltipla

Herança simples já apareceu nas exceções (seção 16 do guia de fundamentos):
`class EmptyPromptError(DomainError)`. Mas o projeto também usa **herança múltipla** — algo que
o **C# não permite para classes** (só para interfaces).

Veja <ref_file file="C:\Projetos\Python\Estudos\app\domain\entities.py" />:

```python
class Role(str, Enum):       # herda de DUAS classes: str e Enum
    USER = "user"
    ASSISTANT = "assistant"
```

`Role` é, ao mesmo tempo, uma **string** e um **enum**. Por isso `Role.USER` se comporta como
`"user"` em comparações e serialização, além de ser um membro de enum. Em C# você não consegue
fazer um `enum` herdar de `string`.

### `super()` e a hierarquia

Já vimos `super().__init__(...)` nas exceções,
<ref_file file="C:\Projetos\Python\Estudos\app\domain\exceptions.py" />:

```python
class ProductNotFoundError(DomainError):
    def __init__(self, produto: str) -> None:
        self.produto = produto
        super().__init__(f"Produto '{produto}' não encontrado no inventário.")
```

- `super()` se refere à **classe-mãe** (aqui, `DomainError` → `Exception`). É o `base` do C#.
- `super().__init__(mensagem)` chama o construtor de `Exception`, que guarda a mensagem (é o
  que `str(exc)` devolve depois, usado nos handlers HTTP).

### MRO (Method Resolution Order)

Quando há herança múltipla, o Python precisa decidir **em que ordem** procurar um método nas
classes-mãe. Essa ordem se chama **MRO**. Você raramente precisa pensar nisso no dia a dia,
mas é bom saber que existe: `Role.__mro__` mostra a cadeia `Role → str → Enum → object`.
Tudo no Python, no fim, herda de `object` (como `System.Object` no .NET).

---

<a name="6-biblioteca-padrao"></a>
## 6. A biblioteca padrão usada no projeto

Assim como o .NET tem a BCL (`System.*`), o Python vem com uma **biblioteca padrão** rica. O
projeto usa vários módulos dela. Vale conhecê-los:

### `datetime` — datas e horas

<ref_file file="C:\Projetos\Python\Estudos\app\domain\entities.py" />:

```python
from datetime import datetime, timezone

def _now() -> datetime:
    return datetime.now(timezone.utc)    # agora, em UTC
```

- `datetime` ≈ `DateTime` do C#. `datetime.now(timezone.utc)` pega o instante atual **com
  fuso UTC** (boa prática: armazenar sempre em UTC, como `DateTimeOffset.UtcNow`).
- `timezone.utc` é o fuso UTC pronto.

### `uuid` — identificadores únicos

```python
import uuid

def _new_id() -> str:
    return str(uuid.uuid4())   # gera um UUID v4 aleatório e converte para string
```

`uuid.uuid4()` ≈ `Guid.NewGuid()` do C#. É usado para gerar o `session_id` de cada conversa.

### `enum` — enumerações

`from enum import Enum` (visto na seção 5 e na seção 12 do guia de fundamentos).

### `dataclasses` — classes de dados

`from dataclasses import dataclass, field` (seção 10 do guia de fundamentos).

### `functools` — utilitários de funções

`from functools import lru_cache` (o cache/singleton, seção 14 do guia de fundamentos).

### `threading` — concorrência

`import threading` → `threading.Lock()` (seção 2 deste documento).

### `collections.abc` — tipos abstratos

<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\ai\gemini_inventory_agent.py" />:

```python
from collections.abc import Callable
```

`Callable` é usado nas anotações de tipo para representar "uma função" (seção 15 do guia de
fundamentos).

| Módulo stdlib   | Equivalente .NET (aproximado)          |
|-----------------|----------------------------------------|
| `datetime`      | `System.DateTime` / `DateTimeOffset`   |
| `uuid`          | `System.Guid`                          |
| `enum`          | `enum` (C#)                            |
| `dataclasses`   | `record`                               |
| `functools`     | utilitários (memoização etc.)          |
| `threading`     | `System.Threading`                     |
| `collections.abc` | interfaces de `System.Collections`   |

---

<a name="7-pydantic"></a>
## 7. Pydantic em profundidade

O **Pydantic** não faz parte da linguagem nem da stdlib — é uma biblioteca externa — mas é tão
central no projeto (validação de dados e configuração) que merece uma explicação própria. Pense
nele como uma mistura de **DTOs com validação automática** + **`IOptions<T>`/binding de
configuração** do .NET.

### 7.1 `BaseModel` — modelos com validação

<ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\schemas.py" />:

```python
from pydantic import BaseModel, Field

class GenerateContentRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt para geração de conteúdo.")
```

- Herdar de `BaseModel` dá **validação e conversão automática** a partir das anotações de tipo.
  Quando o JSON chega, o Pydantic confere se `prompt` é uma string não vazia; se não for,
  devolve erro **422** sem você escrever nada.
- `Field(...)`: o primeiro argumento `...` (Ellipsis) significa **obrigatório**. `min_length=1`
  é uma regra de validação. `description=...` alimenta a documentação `/docs`.

Aqui o Pydantic faz o que, no C#, você faria com *data annotations* (`[Required]`,
`[MinLength(1)]`) num DTO de request.

### 7.2 `BaseSettings` — configuração tipada por ambiente

<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\config.py" />:

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    genai_api_key: str = Field(default="", validation_alias="GENAI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", validation_alias="GEMINI_MODEL")
    gemini_temperature: float = Field(default=0.2, validation_alias="GEMINI_TEMPERATURE")
```

- `BaseSettings` **lê valores de variáveis de ambiente e/ou de um arquivo `.env`**
  automaticamente, já convertendo para o tipo certo (`gemini_temperature` vira `float`). É o
  análogo do binding de `appsettings.json`/variáveis de ambiente para uma classe de opções no
  .NET.
- `validation_alias="GENAI_API_KEY"` diz **de qual variável de ambiente** aquele campo vem (o
  atributo no código é `genai_api_key`, mas no ambiente é `GENAI_API_KEY`).
- `model_config = SettingsConfigDict(...)` é a **configuração do próprio modelo**:
  - `env_file=".env"` — também lê de um arquivo `.env`;
  - `extra="ignore"` — ignora variáveis de ambiente não declaradas (em vez de dar erro).

> Note que `model_config` é um **atributo especial** que o Pydantic procura na classe para se
> configurar. Nos `schemas.py` ele aparece como um `dict` literal; aqui, como o helper tipado
> `SettingsConfigDict`. Os dois funcionam.

### 7.3 Por que separar schemas (Pydantic) de DTOs (`@dataclass`)?

Já mencionado nos outros docs, mas reforçando o "porquê" agora que você conhece os dois:

- **Schemas Pydantic** = contrato **externo** (HTTP/JSON), com validação. Ficam na camada de
  apresentação.
- **DTOs `@dataclass`** = contrato **interno** dos use cases, sem dependência de framework web.
  Ficam na camada de aplicação.

Manter os dois separados evita que uma mudança no JSON da API vaze para dentro do domínio.

---

<a name="8-tuple-desempacotamento"></a>
## 8. `tuple` como tipo e desempacotamento

A `tuple` (seção 6 do guia de fundamentos) aparece como **tipo anotado** nos fakes de teste,
<ref_file file="C:\Projetos\Python\Estudos\tests\fakes.py" />:

```python
self.calls: list[tuple[list[Message], str]] = []
# ...
self.calls.append((history, question))   # guarda um par (histórico, pergunta)
```

- `tuple[list[Message], str]` é uma tupla de **dois itens**: uma lista de mensagens e uma
  string. É como `(List<Message>, string)` (ValueTuple) no C#.
- `(history, question)` cria a tupla. Tuplas são **imutáveis** — ótimas para "agrupar valores
  relacionados" sem criar uma classe.

**Desempacotamento (unpacking)** é o idioma associado, muito usado em laços. Já apareceu na
iteração de dicionário em
<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\persistence\static_inventory_repository.py" />:

```python
for nome, preco in precos.items():   # desempacota cada par (chave, valor) em duas variáveis
    ...
```

Em C# você acessaria `.Key` e `.Value`; no Python você "desmonta" a tupla direto em dois nomes.
Também funciona em atribuições: `a, b = 1, 2` (e até a troca clássica `a, b = b, a`).

---

<a name="9-fixtures-pytest"></a>
## 9. Fixtures do pytest

A seção 21 do guia de fundamentos apresentou o `pytest`. Falta explicar as **fixtures**, que
são o mecanismo de **setup/injeção de dependências dos testes**.

<ref_file file="C:\Projetos\Python\Estudos\tests\conftest.py" />:

```python
import pytest

@pytest.fixture
def inventory_repo() -> StaticInventoryRepository:
    return StaticInventoryRepository({"notebook": 4500.0, "monitor": 1200.0})

@pytest.fixture
def conversation_repo() -> InMemoryConversationRepository:
    return InMemoryConversationRepository()
```

Como funciona:

- O decorator `@pytest.fixture` marca uma função como **fábrica de um recurso de teste**.
- Um teste "pede" a fixture **declarando um parâmetro com o mesmo nome**, e o pytest a injeta
  automaticamente:

```python
def test_busca_item_existente(inventory_repo):   # ← pytest injeta o resultado da fixture
    item = inventory_repo.get("notebook")
    assert item is not None
    assert item.preco_unitario == 4500.0
```

É **injeção de dependência por nome** — bem parecido com o `Depends` do FastAPI (seção do
`PASSO_A_PASSO`). Compare com o C#: lá você normalmente faria o setup no construtor da classe
de teste ou num método `[SetUp]`; aqui é uma função reutilizável injetada onde precisar.

### `conftest.py`

O arquivo `conftest.py` é **especial**: o pytest o carrega automaticamente e disponibiliza
suas fixtures para **todos os testes da pasta** (e subpastas), sem precisar importar. É o lugar
de colocar setup compartilhado.

### Os fakes e o poder dos `Protocol`

<ref_file file="C:\Projetos\Python\Estudos\tests\fakes.py" /> mostra a recompensa de programar
contra interfaces. `FakeContentGenerator` implementa o port `ContentGenerator` com uma resposta
fixa e ainda **grava o que recebeu** (`self.received_prompts`), permitindo verificar como o use
case chamou a dependência — sem tocar na rede nem no Gemini. É o equivalente a um *stub/mock*
feito à mão, possível justamente porque o use case depende de um `Protocol`, não da classe
concreta.

---

<a name="10-tabela-resumo"></a>
## 10. Tabela-resumo

| Conceito (deste doc)            | C# / .NET                              | Python (neste projeto)                  |
|---------------------------------|----------------------------------------|-----------------------------------------|
| Liberação garantida de recurso  | `using` / `lock`                       | `with` (context manager)                |
| Cadeado de concorrência         | `lock` / `Monitor`                     | `threading.Lock()` + `with`             |
| Limite de paralelismo de threads| (sem GIL; threads paralelas)           | **GIL**: 1 thread de bytecode por vez   |
| Função utilitária sem classe    | `static class Helpers`                 | função solta no módulo (`def _now()`)   |
| Cópia defensiva de coleção      | `new List<T>(x)` / `IReadOnlyList`     | `list(x)`                               |
| Herança múltipla de classes     | não permitido                          | permitido (`class Role(str, Enum)`)     |
| Chamar construtor base          | `base(...)`                            | `super().__init__(...)`                 |
| Data/hora em UTC                | `DateTimeOffset.UtcNow`                | `datetime.now(timezone.utc)`            |
| Identificador único             | `Guid.NewGuid()`                       | `uuid.uuid4()`                          |
| DTO com validação               | data annotations (`[Required]`)        | `BaseModel` + `Field`                   |
| Binding de configuração         | `IOptions<T>` / `appsettings`          | `BaseSettings` + `.env`                 |
| Par de valores anônimo          | `ValueTuple` `(a, b)`                  | `tuple` `(a, b)`                        |
| Desempacotar par                | `.Key` / `.Value`                      | `for k, v in d.items()`                 |
| Setup injetável de teste        | construtor / `[SetUp]`                 | `@pytest.fixture` + `conftest.py`       |

---

## Onde isto se encaixa

Com este documento, os quatro guias da pasta `docs/` cobrem:

1. **Fundamentos** da linguagem — `PYTHON_PARA_DEV_CSHARP.md`
2. **Arquitetura** e decisões — `ARQUITETURA.md`
3. **Fluxo** de execução — `PASSO_A_PASSO_ENDPOINT.md`
4. **Conceitos adicionais** usados no código — este arquivo

Se ainda encontrar no código algo que pareça "mágico" e não esteja explicado em nenhum dos
quatro, é um ótimo candidato para você investigar e, quem sabe, documentar no mesmo estilo.
