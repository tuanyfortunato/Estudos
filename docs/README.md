# Documentação — AI Studies API

Bem-vindo(a)! Esta pasta reúne a documentação didática do projeto, pensada especialmente para
quem **já programa em outras linguagens** (em particular **C#**) e está aprendendo **Python** e
**Clean Architecture** na prática, usando este código como material de estudo.

São três guias complementares. A ordem de leitura abaixo é a recomendada.

---

## Ordem de leitura recomendada

### 1️⃣ Fundamentos da linguagem — comece aqui se Python é novo para você
📄 <ref_file file="C:\Projetos\Python\Estudos\docs\PYTHON_PARA_DEV_CSHARP.md" />

Guia de **fundamentos de Python para quem vem de C#**, com comparações lado a lado em cada
conceito (sintaxe, classes, `@dataclass`, `Protocol`, decorators, exceções, comprehensions,
`venv`, testes...). Usa o código real do projeto como exemplo.

> **Leia primeiro** se você ainda não está confortável com a sintaxe e os idiomas do Python.
> Se já manja de Python, pode pular direto para o item 2.

### 2️⃣ Visão de arquitetura — o "como" e o "porquê" do projeto
📄 <ref_file file="C:\Projetos\Python\Estudos\docs\ARQUITETURA.md" />

Explica a **Clean Architecture** aplicada aqui: o que tem em cada pasta, a regra de
dependência, os ports (`Protocol`), os use cases, os adapters, e as **decisões de design** mais
sutis (por que `@lru_cache` vira singleton, por que o agente usa closure, etc.). Inclui também
uma seção de conceitos de Python e diagramas do fluxo de cada endpoint.

> Leia para entender **como as peças se encaixam** e por que o projeto foi estruturado assim.

### 3️⃣ Passo a passo de uma requisição — seguindo o código camada por camada
📄 <ref_file file="C:\Projetos\Python\Estudos\docs\PASSO_A_PASSO_ENDPOINT.md" />

Tutorial **"siga o código"**: percorre o projeto **na ordem em que ele executa**, do endpoint
até o adapter e de volta, parada por parada (`[0]` a `[9]`), explicando cada linha e cada
decorator no caminho. Usa o `POST /content` como exemplo principal e repete o exercício com o
`POST /inventory/ask`.

> Leia por último, com o código aberto ao lado, para **ver a teoria acontecendo na prática**.

### 4️⃣ Mais conceitos de Python — complemento de aprofundamento
📄 <ref_file file="C:\Projetos\Python\Estudos\docs\MAIS_CONCEITOS_PYTHON.md" />

Cobre conceitos de Python que **aparecem no código mas não foram detalhados** nos guias
anteriores: o `with`/context managers, `threading.Lock` e o GIL, funções em nível de módulo,
referências e cópia defensiva, herança múltipla, a biblioteca padrão usada, Pydantic em
profundidade, `tuple`/desempacotamento e fixtures do pytest.

> Leia depois dos outros três, para fechar as lacunas e entender o que ainda parecia "mágico".

---

## Resumo de cada documento

| # | Documento | Foco | Quando ler |
|---|-----------|------|------------|
| 1 | `PYTHON_PARA_DEV_CSHARP.md` | Fundamentos da linguagem Python (vs. C#) | Se Python é novo para você |
| 2 | `ARQUITETURA.md` | Estrutura, camadas e decisões de design | Para entender o todo |
| 3 | `PASSO_A_PASSO_ENDPOINT.md` | Fluxo de execução camada a camada | Com o código aberto, para fixar |
| 4 | `MAIS_CONCEITOS_PYTHON.md` | Conceitos adicionais usados no código | Para fechar as lacunas |

---

## Sobre o projeto

**AI Studies API** é um projeto de estudos de **agentes de IA** com o **Google Gemini**,
estruturado em **Clean Architecture** e exposto como **API REST** com **FastAPI**. Tem dois
recursos principais:

1. **Geração de conteúdo** (`POST /content`) — manda um prompt, recebe um texto. Sem estado.
2. **Agente de inventário** (`POST /inventory/ask`) — conversa com um agente que consulta
   preços via **Function Calling** e **lembra do histórico** por sessão.

Para instruções de instalação, execução e exemplos de chamada, veja o
<ref_file file="C:\Projetos\Python\Estudos\README.md" /> na raiz do projeto.

---

## Mapa rápido do código

```
app/
├── domain/          # Regras de negócio puras (entities, ports, exceptions)
├── application/     # Casos de uso e DTOs
├── infrastructure/  # Implementações concretas (Gemini, persistência, config)
└── presentation/    # API HTTP (FastAPI): routers, schemas, dependências
```

Cada camada é detalhada no documento **2 (Arquitetura)**, e o caminho que uma requisição
percorre por elas está no documento **3 (Passo a passo)**.
