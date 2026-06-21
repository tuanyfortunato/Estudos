# Python para quem vem de C#

> Guia **didático de fundamentos de Python** escrito para uma pessoa programadora júnior que
> **já conhece C#**. A ideia é aproveitar o que você já sabe: a cada conceito, mostramos o
> **lado a lado C# ↔ Python** e usamos o **código real deste projeto** como exemplo.
>
> Leia este documento de cima para baixo na primeira vez. Depois ele vira referência de
> consulta. Para a visão de arquitetura e do fluxo das requisições, veja os companheiros
> <ref_file file="C:\Projetos\Python\Estudos\docs\ARQUITETURA.md" /> e
> <ref_file file="C:\Projetos\Python\Estudos\docs\PASSO_A_PASSO_ENDPOINT.md" />.

---

## Índice

1. [Filosofia: o que muda de mentalidade](#1-filosofia)
2. [Como o código é organizado: módulos, pacotes e imports](#2-modulos-pacotes-imports)
3. [Variáveis e tipos: dinâmico, mas tipado por dica](#3-variaveis-e-tipos)
4. [Indentação no lugar de chaves](#4-indentacao)
5. [Tipos básicos e strings (f-strings)](#5-tipos-basicos-strings)
6. [Coleções: list, dict, tuple, set](#6-colecoes)
7. [Controle de fluxo e "truthiness"](#7-controle-de-fluxo)
8. [Funções: argumentos, padrões, nomeados](#8-funcoes)
9. [Classes e o `self`](#9-classes-e-self)
10. [`@dataclass`: o "record" do Python](#10-dataclass)
11. [Propriedades com `@property`](#11-property)
12. [Enums](#12-enums)
13. [Interfaces com `Protocol` (duck typing)](#13-protocol)
14. [Decorators: o que é aquele `@`](#14-decorators)
15. [Type hints com mais profundidade](#15-type-hints)
16. [Exceções](#16-excecoes)
17. [Comprehensions e expressões](#17-comprehensions)
18. [Closures e funções de primeira classe](#18-closures)
19. [`async`/`await`](#19-async-await)
20. [Ambiente, pacotes e ferramentas](#20-ambiente-e-ferramentas)
21. [Testes](#21-testes)
22. [Tabela-resumo C# ↔ Python](#22-tabela-resumo)

---

<a name="1-filosofia"></a>
## 1. Filosofia: o que muda de mentalidade

Vindo de C#, três mudanças culturais são as mais importantes:

1. **Menos cerimônia.** Não existe `public class Foo { ... }` em arquivo separado obrigatório,
   não há `namespace { }` aninhando tudo, não há ponto-e-vírgula no fim das linhas. O Python
   valoriza código curto e legível ("*readability counts*").
2. **Convenção no lugar de palavra-chave.** C# tem `private`, `public`, `internal`,
   `readonly`, `sealed`... O Python tem **muito menos** disso e confia em **convenções** (ex.:
   um `_` na frente do nome significa "privado, não mexa"). O compilador não te obriga; a
   comunidade combina.
3. **Tipagem dinâmica, mas anotada.** O Python não exige tipos. Mas projetos sérios (como
   este) usam **type hints** (`nome: str`) em todo lugar. Eles **não** são checados em tempo
   de execução — servem para o editor e para ferramentas como `mypy`/`ruff`. Pense neles como
   documentação verificável, não como o sistema de tipos do C#.

Existe até um "manifesto" oficial: rode `import this` no interpretador para ver o *Zen of
Python*.

---

<a name="2-modulos-pacotes-imports"></a>
## 2. Como o código é organizado: módulos, pacotes e imports

Em C# você pensa em **namespaces** e **assemblies**. Em Python:

- **Módulo** = um arquivo `.py`. O nome do módulo é o nome do arquivo. Ex.: `entities.py` é o
  módulo `entities`.
- **Pacote** = uma pasta que contém módulos. Para a pasta ser reconhecida como pacote, ela
  costuma ter um arquivo `__init__.py` (muitas vezes **vazio**). Por isso este projeto tem
  vários `__init__.py` espalhados — eles marcam `app`, `app/domain`, etc., como pacotes.

O **caminho do import** segue a estrutura de pastas. Veja em
<ref_file file="C:\Projetos\Python\Estudos\app\application\use_cases\generate_content.py" />:

```python
from app.application.dtos import GenerateContentInput, GenerateContentOutput
from app.domain.exceptions import EmptyPromptError
from app.domain.ports import ContentGenerator
```

Comparando:

| C#                                   | Python                                            |
|--------------------------------------|---------------------------------------------------|
| `using App.Domain;`                  | `from app.domain import ports`                     |
| `using static App.Domain.Ports.X;`   | `from app.domain.ports import ContentGenerator`    |
| namespace = pasta (por convenção)    | módulo = arquivo; pacote = pasta com `__init__.py` |

Formas de importar:

```python
import app.domain.ports                       # importa o módulo inteiro; usa: app.domain.ports.ContentGenerator
from app.domain import ports                  # importa "ports"; usa: ports.ContentGenerator
from app.domain.ports import ContentGenerator # importa o nome direto; usa: ContentGenerator
```

> **Dica:** no topo de quase todo arquivo deste projeto há
> `from __future__ import annotations`. Isso é um ajuste técnico (faz as anotações de tipo
> serem tratadas como texto, evitando imports circulares). Detalhado na seção 15.

---

<a name="3-variaveis-e-tipos"></a>
## 3. Variáveis e tipos: dinâmico, mas tipado por dica

Em C# você **declara** o tipo (ou usa `var`, mas o tipo é fixado em compilação). Em Python,
você só **atribui**:

```python
nome = "notebook"     # str (inferido em runtime)
preco = 4500.00       # float
quantidade = 3        # int
nome = 123            # PERFEITAMENTE válido: a variável pode mudar de tipo
```

```csharp
// C#
string nome = "notebook";
nome = 123;  // ERRO de compilação
```

No Python o tipo está **no valor**, não na variável. Mas neste projeto usamos **type hints**
para documentar a intenção. Veja em
<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\persistence\static_inventory_repository.py" />:

```python
_PRECOS_PADRAO: dict[str, float] = {
    "notebook": 4500.00,
    "monitor": 1200.00,
    "teclado": 350.00,
}
```

O `: dict[str, float]` é a dica de tipo (equivale a `Dictionary<string, double>`). **Importante:
o Python não vai impedir você de colocar outro tipo ali** — a dica é para humanos e
ferramentas. Se você quer checagem de verdade, roda um type checker (`mypy`).

**Convenção de nomes** (PEP 8, o guia de estilo oficial):

| Coisa                | C#              | Python                  |
|----------------------|-----------------|-------------------------|
| Variável / função    | `camelCase` / `PascalCase` | `snake_case` (`valor_total`) |
| Classe               | `PascalCase`    | `PascalCase` (`InventoryItem`) |
| Constante            | `PascalCase`    | `UPPER_SNAKE` (`_PRECOS_PADRAO`) |
| "Privado"            | `private`       | prefixo `_` (`self._client`)   |

---

<a name="4-indentacao"></a>
## 4. Indentação no lugar de chaves

Esta é a diferença visual que mais assusta no começo: **Python não usa `{ }`**. Os blocos são
definidos pela **indentação** (recuo). Os dois-pontos `:` abrem o bloco.

```python
def execute(self, data: GenerateContentInput) -> GenerateContentOutput:
    prompt = data.prompt.strip()
    if not prompt:
        raise EmptyPromptError("O prompt não pode estar vazio.")
    content = self._content_generator.generate(prompt)
    return GenerateContentOutput(content=content)
```

```csharp
// C# equivalente
public GenerateContentOutput Execute(GenerateContentInput data)
{
    var prompt = data.Prompt.Trim();
    if (string.IsNullOrEmpty(prompt))
        throw new EmptyPromptException("O prompt não pode estar vazio.");
    var content = _contentGenerator.Generate(prompt);
    return new GenerateContentOutput(content);
}
```

Regras práticas:
- Use **4 espaços** por nível (padrão). **Não misture tabs e espaços** — é erro.
- A indentação não é estética, é **sintaxe**. Recuo errado = `IndentationError`.
- O exemplo acima é o use case real:
  <ref_file file="C:\Projetos\Python\Estudos\app\application\use_cases\generate_content.py" />.

---

<a name="5-tipos-basicos-strings"></a>
## 5. Tipos básicos e strings (f-strings)

Tipos primitivos: `int`, `float`, `bool` (`True`/`False`, com maiúscula!), `str`, e `None`
(o equivalente ao `null`).

| C#          | Python   |
|-------------|----------|
| `null`      | `None`   |
| `true/false`| `True/False` |
| `string`    | `str`    |
| `int/long`  | `int` (precisão ilimitada!) |
| `double`    | `float`  |

**Strings** podem usar aspas simples ou duplas (sem diferença). O recurso mais útil é a
**f-string** — interpolação igual ao `$"..."` do C#. Veja na ferramenta do agente,
<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\ai\gemini_inventory_agent.py" />:

```python
return (
    f"O valor total para {quantidade} unidades de {produto} "
    f"é R$ {total:.2f}."
)
```

```csharp
// C#
return $"O valor total para {quantidade} unidades de {produto} é R$ {total:F2}.";
```

- `f"..."` ativa a interpolação. Tudo dentro de `{ }` é avaliado como expressão.
- `{total:.2f}` formata com 2 casas decimais (equivale a `:F2` no C#).
- Strings adjacentes são **concatenadas automaticamente** (as duas linhas viram uma só).

Outro idioma útil aparece no adapter:

```python
return response.text or ""
```

O operador `or` retorna o **primeiro valor "verdadeiro"**. Se `response.text` for `None` ou
`""`, devolve `""`. É o equivalente prático do `??` (null-coalescing) do C#, mas vale para
qualquer valor "falsy" (veja seção 7).

---

<a name="6-colecoes"></a>
## 6. Coleções: list, dict, tuple, set

| C#                      | Python  | Literal           | Mutável? |
|-------------------------|---------|-------------------|----------|
| `List<T>`               | `list`  | `[1, 2, 3]`       | sim      |
| `Dictionary<K,V>`       | `dict`  | `{"a": 1}`        | sim      |
| `(T1, T2)` / `ValueTuple` | `tuple` | `(1, "a")`      | **não**  |
| `HashSet<T>`            | `set`   | `{1, 2, 3}`       | sim      |

**`list`** — exemplo na entidade `Conversation`,
<ref_file file="C:\Projetos\Python\Estudos\app\domain\entities.py" />:

```python
messages: list[Message] = field(default_factory=list)
# ...
self.messages.append(message)   # adiciona ao fim (como List.Add)
return list(self.messages)      # cria uma CÓPIA da lista
```

**`dict`** — o repositório de inventário usa um dicionário como "banco":

```python
self._itens: dict[str, InventoryItem] = {
    nome.lower(): InventoryItem(nome=nome.lower(), preco_unitario=preco)
    for nome, preco in precos.items()   # ← dict comprehension (seção 17)
}
# ...
return self._itens.get(nome.lower().strip())   # .get devolve None se a chave não existe
```

`dict.get(chave)` é como `TryGetValue` — devolve `None` em vez de lançar exceção quando a
chave não existe. Muito usado neste projeto (ex.: `InventoryRepository.get` retorna
`InventoryItem | None`).

**`tuple`** é imutável e leve, ótimo para retornos múltiplos. **`set`** é coleção sem
duplicatas.

Acesso e fatiamento (*slicing*) — algo que o C# não tem nativamente:

```python
itens = [10, 20, 30, 40]
itens[0]      # 10  (índice)
itens[-1]     # 40  (último! índices negativos contam do fim)
itens[1:3]    # [20, 30]  (do índice 1 até antes do 3)
itens[:2]     # [10, 20]  (do começo até antes do 2)
```

---

<a name="7-controle-de-fluxo"></a>
## 7. Controle de fluxo e "truthiness"

**`if / elif / else`** (note o `elif`, não `else if`):

```python
def _load_or_create(self, session_id: str | None) -> Conversation:
    if session_id:
        existing = self._conversations.get(session_id)
        if existing is not None:
            return existing
        return Conversation(session_id=session_id)
    return Conversation()
```

(Código real de
<ref_file file="C:\Projetos\Python\Estudos\app\application\use_cases\ask_inventory_agent.py" />.)

Repare em `if session_id:` — **sem comparação explícita**. Isso é **truthiness**: no Python,
muitos valores são "falsy" automaticamente:

| "Falsy" (avaliam como `False`) | "Truthy" |
|--------------------------------|----------|
| `None`, `False`, `0`, `0.0`    | qualquer número diferente de 0 |
| `""` (string vazia)            | qualquer string não vazia |
| `[]`, `{}`, `()` (vazios)      | coleções com itens |

Então `if not prompt:` (visto na seção 4) significa "se o prompt for vazio **ou** None". Em
C# você escreveria `if (string.IsNullOrEmpty(prompt))`.

**`is` vs `==`:** use `is None` (identidade) para comparar com `None`, e `==` para igualdade
de valor. No código: `if existing is not None:`. É como `ReferenceEquals` vs `==` no C#.

**Laços `for`** — são sempre "for-each" (não existe `for(i=0; i<n; i++)` clássico):

```python
for message in history:           # foreach (var message in history)
    ...

for i in range(5):                # for (int i = 0; i < 5; i++)
    print(i)                      # 0,1,2,3,4

for nome, preco in precos.items():  # itera pares chave/valor de um dict
    ...
```

---

<a name="8-funcoes"></a>
## 8. Funções: argumentos, padrões, nomeados

Funções se declaram com `def`. Tipos são opcionais, mas aqui sempre presentes:

```python
def create_gemini_client(api_key: str) -> genai.Client:
    if not api_key:
        raise MissingApiKeyError()
    return genai.Client(api_key=api_key)
```

(De <ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\ai\client_factory.py" />.)

- `api_key: str` = parâmetro tipado.
- `-> genai.Client` = tipo de retorno.

**Valores padrão** (como parâmetros opcionais do C#):

```python
@dataclass(frozen=True)
class AskInventoryInput:
    question: str
    session_id: str | None = None   # ← opcional, padrão None
```

**Argumentos nomeados (keyword arguments)** — usadíssimos no projeto para clareza. Veja o
composition root, <ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\dependencies.py" />:

```python
agent = GeminiInventoryAgent(
    client=get_gemini_client(),
    inventory=get_inventory_repository(),
    model=settings.gemini_model,
    temperature=settings.gemini_temperature,
    system_instruction=settings.agent_system_instruction,
)
```

Isso é como o C# `new GeminiInventoryAgent(client: x, model: y)`, mas no Python é a forma
**preferida** quando há vários argumentos — fica autoexplicativo.

> **Pegadinha clássica:** nunca use um objeto mutável como valor padrão
> (`def f(itens=[])`). Esse `[]` seria criado **uma vez** e compartilhado entre todas as
> chamadas. É por isso que as `@dataclass`es usam `field(default_factory=list)` em vez de
> `= []` (seção 10).

---

<a name="9-classes-e-self"></a>
## 9. Classes e o `self`

Estrutura de uma classe — exemplo real do use case,
<ref_file file="C:\Projetos\Python\Estudos\app\application\use_cases\generate_content.py" />:

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

Comparando com C#:

```csharp
public class GenerateContentUseCase
{
    private readonly IContentGenerator _contentGenerator;

    public GenerateContentUseCase(IContentGenerator contentGenerator)
    {
        _contentGenerator = contentGenerator;
    }

    public GenerateContentOutput Execute(GenerateContentInput data) { ... }
}
```

Diferenças cruciais:

1. **`__init__` é o construtor.** O nome é sempre esse (são os "dunder methods", de *double
   underscore*). Há vários: `__init__`, `__eq__`, `__repr__`, `__str__`...
2. **`self` é o `this` — mas explícito.** Todo método de instância recebe `self` como
   **primeiro parâmetro**. Você não escreve `self` ao chamar (`use_case.execute(x)`), mas
   escreve ao declarar. Isso incomoda no começo e vira natural rápido.
3. **Atributos não são declarados no topo.** Eles "nascem" quando você atribui
   `self._content_generator = ...` dentro do `__init__`. Não existe lista de campos no topo da
   classe (a não ser com `@dataclass`, seção 10).
4. **Não existe `private` real.** O `_` em `_content_generator` é **convenção**: "interno, não
   acesse de fora". Tecnicamente você *consegue* acessar, mas não deve. (Há também `__nome`
   com dois underscores, que ativa *name mangling*, mas o projeto não usa.)
5. **Sem `readonly` / `new` / modificadores de acesso** nas assinaturas. Mais enxuto.

**Métodos estáticos** usam o decorator `@staticmethod` (não recebem `self`). Exemplo no
agente:

```python
@staticmethod
def _to_genai_history(history: list[Message]) -> list[types.Content]:
    ...
```

É o equivalente a um `static` method do C#.

---

<a name="10-dataclass"></a>
## 10. `@dataclass`: o "record" do Python

Escrever construtor + igualdade + `ToString` na mão é chato. O C# resolveu com `record`. O
Python tem `@dataclass`. Veja as entidades,
<ref_file file="C:\Projetos\Python\Estudos\app\domain\entities.py" />:

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class InventoryItem:
    nome: str
    preco_unitario: float

    def valor_total(self, quantidade: int) -> float:
        if quantidade < 0:
            raise ValueError("A quantidade não pode ser negativa.")
        return self.preco_unitario * quantidade
```

O que o `@dataclass` **gera automaticamente** a partir dos campos declarados (`nome`,
`preco_unitario`):
- o construtor `__init__(self, nome, preco_unitario)`;
- igualdade por valor `__eq__` (dois itens com mesmos dados são iguais);
- representação de debug `__repr__` (`InventoryItem(nome='notebook', preco_unitario=4500.0)`).

```csharp
// C# equivalente
public record InventoryItem(string Nome, double PrecoUnitario)
{
    public double ValorTotal(int quantidade) => ...;
}
```

- **`frozen=True`** = imutável (como um `record` com `init`-only). Tentar fazer
  `item.nome = "x"` depois de criado dá erro. Isso protege as entidades do domínio.
- **`field(default_factory=...)`** resolve a pegadinha dos padrões mutáveis. Veja
  `Conversation`:

```python
@dataclass
class Conversation:
    session_id: str = field(default_factory=_new_id)       # gera um UUID novo por instância
    messages: list[Message] = field(default_factory=list)  # cria uma lista NOVA por instância
    created_at: datetime = field(default_factory=_now)
```

Cada nova `Conversation()` ganha seu próprio `session_id` e sua própria lista. Se fosse
`messages: list = []`, todas as conversas compartilhariam a **mesma** lista — bug clássico.

A `Conversation` (sem `frozen`) é mutável e tem métodos de negócio:

```python
def add_message(self, role: Role, content: str) -> Message:
    message = Message(role=role, content=content)
    self.messages.append(message)
    self.updated_at = _now()
    return message
```

---

<a name="11-property"></a>
## 11. Propriedades com `@property`

No C# você tem `public bool HasApiKey => !string.IsNullOrEmpty(ApiKey);`. No Python, o
decorator `@property` transforma um **método** em algo que se **lê como atributo**. Veja
<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\config.py" />:

```python
class Settings(BaseSettings):
    genai_api_key: str = Field(default="", validation_alias="GENAI_API_KEY")

    @property
    def has_api_key(self) -> bool:
        return bool(self.genai_api_key)
```

Uso:

```python
settings.has_api_key      # ✅ SEM parênteses — parece um campo
settings.has_api_key()    # ❌ erro: bool não é "chamável"
```

```csharp
// C#
public bool HasApiKey => !string.IsNullOrEmpty(GenaiApiKey);
```

`@property` é um **getter**. Dá para ter setter também (`@has_api_key.setter`), mas raramente
é necessário. Use `@property` para expor valores **calculados** sem que o chamador precise
saber que há lógica por trás.

---

<a name="12-enums"></a>
## 12. Enums

O Python tem `enum.Enum`. Este projeto usa um truque comum: herdar de `str` **e** `Enum` para
o valor já ser uma string utilizável. Veja
<ref_file file="C:\Projetos\Python\Estudos\app\domain\entities.py" />:

```python
from enum import Enum

class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
```

```csharp
// C# (mais simples, mas sem o valor string embutido)
public enum Role { User, Assistant }
```

Por herdar de `str`, `Role.USER` **é** a string `"user"` para muitos efeitos (serialização,
comparação), além de ser um membro de enum. Uso típico no agente:

```python
role_map = {Role.USER: "user", Role.ASSISTANT: "model"}
```

Acesso: `Role.USER`, `Role.USER.value` (`"user"`), e dá para iterar com `for r in Role:`.

---

<a name="13-protocol"></a>
## 13. Interfaces com `Protocol` (duck typing)

Aqui mora uma das maiores diferenças filosóficas. Em C#, uma classe precisa **declarar** que
implementa uma interface: `class Foo : IBar`. Em Python, com `typing.Protocol`, a relação é
**estrutural**: se a classe **tem os métodos certos**, ela já "satisfaz" o protocolo —
declarar é opcional.

Os contratos do domínio estão em
<ref_file file="C:\Projetos\Python\Estudos\app\domain\ports.py" />:

```python
from typing import Protocol

class ContentGenerator(Protocol):
    def generate(self, prompt: str) -> str:
        ...

class InventoryRepository(Protocol):
    def get(self, nome: str) -> InventoryItem | None: ...
    def list_all(self) -> list[InventoryItem]: ...
```

```csharp
// C#
public interface IContentGenerator
{
    string Generate(string prompt);
}
```

- O `...` (objeto `Ellipsis`) é o corpo vazio — é só a assinatura, sem implementação. É o
  equivalente a uma assinatura de método numa interface C#.
- **Duck typing:** *"se anda como pato e grasna como pato, é um pato"*. O
  `StaticInventoryRepository` tem `get` e `list_all`, então ele **é** um `InventoryRepository`
  para o verificador de tipos — mesmo que não escrevesse a herança.

Neste projeto, alguns adapters **até herdam explicitamente** o Protocol para deixar a
intenção clara, ex.: `class GeminiContentGenerator(ContentGenerator)`. Mas isso é opcional —
o que importa é ter os métodos.

**Por que isso é tão importante na arquitetura?** Porque o use case depende do `Protocol`
(interface), não da classe concreta. Isso permite trocar Gemini por outro provedor, e
**nos testes** injetar um *fake* (seção 21) — sem mudar o domínio.

---

<a name="14-decorators"></a>
## 14. Decorators: o que é aquele `@`

Você já viu vários `@`. Vindo de C#, é tentador pensar que são **atributos** (`[Obsolete]`,
`[HttpPost]`). A semelhança visual existe, mas o mecanismo é diferente e mais poderoso:

> **Um decorator é uma função que recebe outra função (ou classe) e devolve uma versão
> modificada dela.** Não é metadado — é código que executa.

Mentalmente, isto:

```python
@minha_decoracao
def f():
    ...
```

é **exatamente** isto:

```python
def f():
    ...
f = minha_decoracao(f)   # f passa a ser o que minha_decoracao retornou
```

Decorators usados neste projeto e o que cada um faz:

| Decorator                  | Onde aparece                         | O que faz |
|----------------------------|--------------------------------------|-----------|
| `@dataclass`               | `domain/entities.py`, `dtos.py`      | Gera `__init__`, `__eq__`, `__repr__`. |
| `@property`                | `infrastructure/config.py`           | Método lido como atributo (getter).    |
| `@staticmethod`            | `gemini_inventory_agent.py`          | Método sem `self`.                     |
| `@lru_cache`               | `config.py`, `dependencies.py`       | Memoiza o retorno (vira singleton).    |
| `@router.post` / `.get`    | `routers/*.py`                       | Registra a função como endpoint HTTP.  |
| `@app.exception_handler`   | `presentation/api/app.py`            | Registra tratador de exceção → HTTP.   |

**`@lru_cache` como singleton** — exemplo de
<ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\dependencies.py" />:

```python
from functools import lru_cache

@lru_cache
def get_gemini_client() -> genai.Client:
    settings = get_settings()
    return create_gemini_client(settings.genai_api_key)
```

`lru_cache` faz a função **lembrar do resultado**: a 1ª chamada cria o client; as próximas
devolvem o mesmo objeto. Sem escrever uma classe singleton. (LRU = *Least Recently Used*; sem
limite de tamanho aqui, então é cache permanente.)

**`@router.post` como rota** — de
<ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\routers\content.py" />:

```python
@router.post("", response_model=GenerateContentResponse)
def generate_content(payload: GenerateContentRequest, ...):
    ...
```

É o equivalente ao `[HttpPost]` + `[ProducesResponseType]` do C#, mas é uma função de verdade
que pendura `generate_content` na tabela de rotas do FastAPI.

**Decorators empilhados** (vários `@` na mesma função) — de `app.py`:

```python
@app.exception_handler(ProductNotFoundError)
@app.exception_handler(ConversationNotFoundError)
async def _not_found(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})
```

Os dois tipos de erro caem no mesmo handler.

---

<a name="15-type-hints"></a>
## 15. Type hints com mais profundidade

Já vimos `: str` e `-> str`. Mais formas que aparecem no projeto:

```python
str | None                      # "string ou nulo" — como string? (nullable) no C#
list[Message]                   # List<Message>
dict[str, float]                # Dictionary<string, double>
Callable[[str, int], str]       # Func<string, int, string> (função que recebe str,int e devolve str)
InventoryItem | None            # union type
```

O `Callable[[str, int], str]` aparece na assinatura da ferramenta do agente,
<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\ai\gemini_inventory_agent.py" />:

```python
@staticmethod
def _build_tool(inventory: InventoryRepository) -> Callable[[str, int], str]:
    ...
```

**`from __future__ import annotations`** — presente no topo de quase todos os arquivos. Ele
faz as anotações serem guardadas como **texto** e avaliadas só sob demanda. Benefícios:
evita problemas de import circular e permite sintaxe moderna em Pythons mais antigos.

**A exceção reveladora:** o arquivo `gemini_inventory_agent.py` **propositalmente NÃO usa**
esse import. Por quê? Porque o SDK do Gemini, no Function Calling, lê as anotações da função
**em tempo de execução** (faz `isinstance(valor, anotacao)`). Se as anotações fossem strings,
`isinstance` quebraria. É um ótimo exemplo de que type hints, embora normalmente "só
documentação", **podem** ser inspecionados em runtime por bibliotecas (Pydantic e FastAPI
fazem isso o tempo todo). Detalhes no
<ref_file file="C:\Projetos\Python\Estudos\docs\ARQUITETURA.md" /> (seção 6.2).

> **Reforço:** type hints **não** são verificados pelo interpretador. `nome: int = "texto"`
> roda sem erro. Quem verifica é o `mypy`/`ruff`/seu editor. Diferente do C#, onde o tipo é
> lei do compilador.

---

<a name="16-excecoes"></a>
## 16. Exceções

Sintaxe `try / except / else / finally` (note `except`, não `catch`):

```python
try:
    item = inventory.get(produto)
except ProductNotFoundError as exc:
    print(exc)
finally:
    ...
```

**Lançar:** `raise` (não `throw`). **Criar exceções próprias:** herde de `Exception`. Este
projeto tem uma hierarquia de erros de domínio em
<ref_file file="C:\Projetos\Python\Estudos\app\domain\exceptions.py" />:

```python
class DomainError(Exception):
    """Erro base do domínio."""

class EmptyPromptError(DomainError):
    """Lançada quando um prompt/pergunta obrigatório está vazio."""

class ProductNotFoundError(DomainError):
    def __init__(self, produto: str) -> None:
        self.produto = produto
        super().__init__(f"Produto '{produto}' não encontrado no inventário.")
```

```csharp
// C#
public class DomainException : Exception { }
public class ProductNotFoundException : DomainException
{
    public ProductNotFoundException(string produto)
        : base($"Produto '{produto}' não encontrado.") { }
}
```

- `super().__init__(...)` chama o construtor da classe-mãe (como `base(...)` no C#).
- A string `"""..."""` logo abaixo da classe é um **docstring** — documentação embutida. É um
  recurso de linguagem (acessível via `Classe.__doc__`), não um comentário. Os `# ...` é que
  são comentários comuns.

**Como o projeto usa isso de forma elegante:** o domínio **lança** `EmptyPromptError` sem
saber nada de HTTP. A camada de API **traduz** a exceção em status HTTP com
`@app.exception_handler` (veja seção 14 e o
<ref_file file="C:\Projetos\Python\Estudos\docs\PASSO_A_PASSO_ENDPOINT.md" /> parada [9]).
Separação de responsabilidades na prática.

---

<a name="17-comprehensions"></a>
## 17. Comprehensions e expressões

**Comprehensions** são o jeito idiomático do Python de transformar coleções — pense em LINQ,
mas com sintaxe embutida na linguagem.

**List comprehension** — de
<ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\routers\inventory.py" />:

```python
return [
    InventoryItemResponse(nome=item.nome, preco_unitario=item.preco_unitario)
    for item in inventory.list_all()
]
```

```csharp
// C# com LINQ
return inventory.ListAll()
    .Select(item => new InventoryItemResponse(item.Nome, item.PrecoUnitario))
    .ToList();
```

**Com filtro** (o `if` no fim faz o papel do `.Where`):

```python
caros = [item for item in itens if item.preco_unitario > 1000]
```

**Dict comprehension** — de
<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\persistence\static_inventory_repository.py" />:

```python
self._itens: dict[str, InventoryItem] = {
    nome.lower(): InventoryItem(nome=nome.lower(), preco_unitario=preco)
    for nome, preco in precos.items()
}
```

Lê-se: "para cada par `(nome, preco)` no dicionário `precos`, crie uma entrada
`nome.lower() -> InventoryItem(...)`".

**Conversão direta** — `_to_genai_history` no agente usa list comprehension para mapear
mensagens do domínio para o formato do Gemini:

```python
return [
    types.Content(role=role_map[message.role], parts=[types.Part(text=message.content)])
    for message in history
]
```

---

<a name="18-closures"></a>
## 18. Closures e funções de primeira classe

No Python, **funções são objetos**: você pode guardá-las em variáveis, passá-las como
argumento e retorná-las de outra função (como `Func<>`/`Action<>`/delegates no C#, mas sem
cerimônia).

Uma **closure** é uma função criada dentro de outra que "lembra" das variáveis do ambiente
onde nasceu. O exemplo está no agente,
<ref_file file="C:\Projetos\Python\Estudos\app\infrastructure\ai\gemini_inventory_agent.py" />:

```python
@staticmethod
def _build_tool(inventory: InventoryRepository) -> Callable[[str, int], str]:
    def obter_valor_estoque(produto: str, quantidade: int) -> str:
        item = inventory.get(produto)      # ← "inventory" foi capturado do escopo de fora
        if item is None:
            return f"Produto '{produto}' não encontrado no sistema de inventário."
        total = item.valor_total(quantidade)
        return f"O valor total para {quantidade} unidades de {produto} é R$ {total:.2f}."
    return obter_valor_estoque              # ← retorna a função (não o resultado dela!)
```

- `obter_valor_estoque` é definida **dentro** de `_build_tool` e usa `inventory`, que é
  parâmetro da função externa. Mesmo depois de `_build_tool` terminar, a função retornada
  continua "lembrando" daquele `inventory`. Isso é a closure.
- `return obter_valor_estoque` (sem `()`) retorna a **função em si**, não o resultado de
  chamá-la.

**Por que closure aqui e não um método normal?** Porque o SDK do Gemini faz `deepcopy` da
configuração; um método arrastaria o `self` inteiro (com objetos não copiáveis) e quebraria.
A closure captura só o `inventory`, que é leve e seguro. (Motivo completo no
<ref_file file="C:\Projetos\Python\Estudos\docs\ARQUITETURA.md" /> seção 6.3.)

---

<a name="19-async-await"></a>
## 19. `async` / `await`

O Python tem `async`/`await` muito parecido com o do C# (`Task`). Uma função `async def`
retorna uma *coroutine* (análoga a uma `Task`), e você usa `await` para esperar.

Neste projeto, os **endpoints são síncronos** (`def` normal) — o FastAPI roda funções
síncronas num pool de threads automaticamente, então tudo bem. Mas os **handlers de exceção**
são assíncronos, em
<ref_file file="C:\Projetos\Python\Estudos\app\presentation\api\app.py" />:

```python
@app.exception_handler(EmptyPromptError)
async def _empty_prompt(_: Request, exc: EmptyPromptError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})
```

```csharp
// mentalidade C#
public async Task<IActionResult> Handle(...) { ... }
```

Para o seu fluxo de aprendizado, a regra prática: **use `def` normal** a menos que precise
fazer I/O assíncrono de verdade (chamadas de rede com bibliotecas `async`). O FastAPI aceita
os dois.

---

<a name="20-ambiente-e-ferramentas"></a>
## 20. Ambiente, pacotes e ferramentas

Em C#/.NET você tem `dotnet`, NuGet e o `.csproj`. Os equivalentes Python:

| Conceito                    | .NET                     | Python                                  |
|-----------------------------|--------------------------|-----------------------------------------|
| Gerenciador de pacotes      | NuGet                    | `pip`                                   |
| Repositório de pacotes      | nuget.org                | PyPI (pypi.org)                         |
| Lista de dependências       | `.csproj`                | `requirements.txt` / `pyproject.toml`   |
| Isolamento por projeto      | (cada projeto é isolado) | **virtual environment** (`venv`)        |
| Metadados/config do projeto | `.csproj`                | `pyproject.toml`                        |

**Virtual environment (`venv`)** é o conceito que não existe igual no .NET. Por padrão, o
`pip` instala pacotes **globalmente** na máquina, o que causa conflito entre projetos. O
`venv` cria uma "caixa" isolada de pacotes só para este projeto:

```bash
python -m venv .venv          # cria o ambiente na pasta .venv
.venv\Scripts\activate        # ATIVA (Windows). Linux/Mac: source .venv/bin/activate
pip install -r requirements-dev.txt
```

Enquanto o `.venv` está ativo, todo `pip install` e `python` usa aquela caixa isolada.

**`pyproject.toml`** deste projeto, <ref_file file="C:\Projetos\Python\Estudos\pyproject.toml" />,
também configura ferramentas:

```toml
[tool.pytest.ini_options]      # config do pytest (test runner)
pythonpath = ["."]
testpaths = ["tests"]

[tool.ruff]                    # config do ruff (linter + formatador, super rápido)
line-length = 100
target-version = "py311"
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]  # famílias de regras ativadas
```

- **`ruff`** é o linter/formatador (equivale, juntando, ao analyzer + dotnet-format). Roda com
  `ruff check` e `ruff format`.
- **`pytest`** é o framework de testes (equivale ao xUnit/NUnit).

---

<a name="21-testes"></a>
## 21. Testes

O Python tem `unittest` (estilo xUnit, com classes), mas a comunidade prefere **`pytest`**,
que é mais enxuto: **funções** que começam com `test_` e o comando `assert` puro — sem
`Assert.AreEqual`.

```python
def test_valor_total_calcula_corretamente():
    item = InventoryItem(nome="notebook", preco_unitario=4500.0)
    assert item.valor_total(3) == 13500.0

def test_valor_total_rejeita_quantidade_negativa():
    item = InventoryItem(nome="notebook", preco_unitario=4500.0)
    with pytest.raises(ValueError):     # equivale a Assert.Throws<...>
        item.valor_total(-1)
```

A estrutura de testes deste projeto espelha o código (`tests/unit/`, `tests/integration/`).
A grande sacada arquitetural: como os use cases dependem de **`Protocol`** (interfaces), os
testes injetam **fakes** no lugar do Gemini (veja `tests/fakes.py`), então **não há chamadas
reais à API** — testes rápidos e determinísticos.

Rodar tudo:

```bash
pytest
```

Conceitos do pytest que você encontrará:
- **`conftest.py`**: arquivo de configuração/fixtures compartilhadas entre testes.
- **fixtures**: funções que preparam dados/dependências e são injetadas nos testes por nome
  (parecido com a injeção de dependência, mas para o setup de testes).

---

<a name="22-tabela-resumo"></a>
## 22. Tabela-resumo C# ↔ Python

| Conceito                    | C#                                  | Python                                       |
|-----------------------------|-------------------------------------|----------------------------------------------|
| Nulo                        | `null`                              | `None`                                       |
| Booleanos                   | `true` / `false`                    | `True` / `False`                             |
| Blocos                      | `{ }`                               | indentação + `:`                             |
| Comentário                  | `// ...`                            | `# ...`                                       |
| Doc                         | `/// <summary>`                     | docstring `"""..."""`                        |
| Interpolação                | `$"{x}"`                            | `f"{x}"`                                      |
| Construtor                  | `public Classe(...)`                | `def __init__(self, ...)`                     |
| `this`                      | implícito                           | `self` (explícito)                           |
| Privado                     | `private`                           | convenção `_nome`                            |
| `record`                    | `record Foo(...)`                   | `@dataclass`                                  |
| Propriedade                 | `=> ...` getter                     | `@property`                                   |
| Método estático             | `static`                            | `@staticmethod`                              |
| Interface                   | `interface IFoo` + `: IFoo`         | `class Foo(Protocol)` (duck typing)          |
| Enum                        | `enum`                              | `class X(str, Enum)`                          |
| Atributo/anotação           | `[HttpPost]`                        | decorator `@router.post` (é uma função!)     |
| Nullable                    | `string?`                           | `str | None`                                 |
| Lançar exceção              | `throw`                             | `raise`                                       |
| Capturar exceção            | `catch`                             | `except`                                      |
| Herdar construtor base      | `base(...)`                         | `super().__init__(...)`                       |
| LINQ `.Select`              | `.Select(x => ...)`                 | list comprehension `[... for x in ...]`      |
| LINQ `.Where`               | `.Where(x => ...)`                  | `[... for x in ... if cond]`                 |
| `Func<int,string>`          | delegate                            | `Callable[[int], str]`                       |
| Pacotes                     | NuGet / `.csproj`                   | pip / `requirements.txt` + `pyproject.toml`  |
| Isolamento                  | (por projeto)                       | `venv`                                        |
| Testes                      | xUnit `Assert.Equal`                | pytest + `assert`                            |

---

## Próximos passos sugeridos

1. Abra <ref_file file="C:\Projetos\Python\Estudos\app\domain\entities.py" /> e identifique:
   um `@dataclass(frozen=True)`, um `Enum`, um `field(default_factory=...)` e um método com
   `self`.
2. Siga uma requisição inteira pelo
   <ref_file file="C:\Projetos\Python\Estudos\docs\PASSO_A_PASSO_ENDPOINT.md" /> com este guia
   ao lado, e tente reconhecer cada fundamento "no campo".
3. Rode `pytest` e leia um teste em `tests/unit/` — veja como os fakes substituem o Gemini.
4. Como exercício: crie um novo endpoint simples (ex.: `GET /inventory/items/{nome}` que
   retorna um item) seguindo o mesmo caminho de camadas. Você vai usar quase todos os
   fundamentos deste guia.
```