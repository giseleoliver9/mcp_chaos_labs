# MCP Chaos Lab

![Python 3.11+](docs/badges/python.svg) ![FastAPI](docs/badges/fastapi.svg) ![Pydantic](docs/badges/pydantic.svg) ![pytest](docs/badges/pytest.svg) ![Docker · opcional/optional](docs/badges/docker.svg)

[![Português (BR)](docs/badges/lang-pt-br.svg)](README.md) [![English](docs/badges/lang-en.svg)](README.en.md) [![Español](docs/badges/lang-es.svg)](README.es.md) [![Français](docs/badges/lang-fr.svg)](README.fr.md) [![简体中文](docs/badges/lang-zh-cn.svg)](README.zh-CN.md)

**O que acontece quando a ferramenta de um agente de IA sai do ar ou devolve dados inválidos?**

O MCP Chaos Lab é um simulador em Python. Ele faz a mesma chamada com duas estratégias, provoca uma falha de propósito e mostra o que cada uma faz: retorna dados no formato esperado, recorre a uma alternativa ou interrompe a execução. Dá para testar sem Docker, chave de API ou modelo de IA.

## O que é MCP e o que este laboratório faz

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/docs/learn/architecture) é um padrão para um app de IA descobrir e chamar as ferramentas que um servidor oferece. Por exemplo, um servidor MCP de clima pode oferecer a função de consulta `get_rainfall(neighborhood, date)`. Ela chama a API de clima que já existe e devolve o volume de chuva, a estação, a fonte e a hora da medição. A API REST continua como está. O servidor MCP faz a ponte com o app de IA.

**O laboratório não implementa um servidor nem um cliente MCP.** As chamadas são simuladas dentro do Python para testar como o agente reage a falhas. As rotas opcionais do FastAPI são HTTP comum, não um transporte MCP. Repetir a chamada, usar uma alternativa (fallback) ou interromper são decisões do laboratório, não do protocolo.

## Demo de 30 segundos

![Demo no terminal: a versão básica para quando a ferramenta fica indisponível. A versão resiliente usa uma alternativa simulada e para se os dados estiverem malformados.](docs/mcp-chaos-lab-demo.gif)

As duas estratégias recebem a mesma busca e a mesma falha simulada. A básica devolve um erro. A resiliente devolve uma resposta alternativa e registra esse caminho. A resposta alternativa é de teste, não vem de um cache real. A validação verifica o formato, não se o conteúdo está correto ou atualizado. Se a resposta vem malformada, a estratégia resiliente para em vez de repassar dados inválidos.

Depois de [instalar a CLI](#instalação-da-cli), reproduza os três cenários:

```bash
mcp-chaos execute --agent baseline --tool search --payload query=demo --failure unavailable
mcp-chaos execute --agent advanced --tool search --payload query=demo --failure unavailable
mcp-chaos execute --agent advanced --tool search --payload query=demo --failure malformed
```

## Como rodar

**Requisitos:** Python 3.11 ou mais recente e Git para clonar. Sem Git, escolha **Code → Download ZIP** no GitHub, extraia o ZIP, abra o terminal na pasta extraída e comece pelo comando que cria o ambiente virtual.

### Windows (PowerShell)

```powershell
git clone https://github.com/giseleoliver9/mcp_chaos_labs.git
cd mcp_chaos_labs
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.cli execute --agent advanced --tool search --payload query=demo --failure unavailable
```

### macOS / Linux

```bash
git clone https://github.com/giseleoliver9/mcp_chaos_labs.git
cd mcp_chaos_labs
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m app.cli execute --agent advanced --tool search --payload query=demo --failure unavailable
```

O comando mostra `Cached fallback result for: demo` e `"recovered": true`. Troque `advanced` por `baseline` para ver a mesma falha sem recuperação (`ToolUnavailableError`). Use `advanced` com `--failure malformed` para ver a interrupção intencional (`SafeAbortError`). Nos dois cenários de erro, o código de saída esperado é 1.

Para reproduzir o benchmark ou rodar os testes, use o Python do mesmo ambiente virtual com `-m app.cli benchmark` ou `-m pytest`.

## O que o laboratório testa

O laboratório compara duas estratégias:

- `BaselineAgent`: chama a ferramenta direto. Se ela falha, a tarefa falha.
- `ResilientAgent`: valida a resposta, identifica a falha, repete chamadas que expiraram, usa uma alternativa quando a ferramenta está indisponível, adapta mudanças conhecidas de formato e para quando recebe dados malformados.

Opções de planejamento:

- `DeterministicPlanner`: escolhe a ferramenta para cada tarefa de forma reproduzível.
- `LLMPlanner`: adaptador opcional para planejar com um modelo de linguagem. Quem chama fornece a função que consulta o modelo, sem depender de um provedor específico.

O benchmark chama ferramentas simuladas diretamente, sem planejador nem modelo real. Assim, mede só o comportamento na chamada da ferramenta. Para testar a etapa de planejamento, use o comando `task` à parte.

Falhas simuladas:

- Tempo limite excedido (`timeout`)
- Ferramenta indisponível (`unavailable`)
- Resposta malformada (`malformed`)
- Mudança no formato da resposta (`schema_mismatch`)

Ferramentas simuladas:

- `calculator`
- `search`
- `weather`

## Resultados do benchmark

Para reproduzir o cenário controlado:

```bash
python run_benchmark.py
```

As duas estratégias passaram pelos mesmos 100 casos simulados, com a semente `7`. Sucesso aqui significa que a resposta passou na validação de formato.

| Estratégia | Sucesso | Recuperação | Falha segura | Resposta insegura | Eficiência da recuperação | Média de chamadas |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 25.0% | 0.0% | 50.7% | 37.0% | 0.0 | 1.0 |
| Advanced | 75.0% | 66.7% | 100.0% | 0.0% | 1.0 | 1.5 |

A diferença foi de **50 pontos percentuais**: de 25% para 75%.

O agente resiliente rejeita respostas malformadas de propósito. Parar nesse cenário evita que dados inválidos sigam para a próxima etapa.

Também dá para variar as falhas em uma simulação pseudoaleatória, sem envolver produção:

```bash
mcp-chaos benchmark --mode seeded --executions 500 --failure-probability 0.35
```

Resultado da execução registrada com falhas pseudoaleatórias:

| Estratégia | Sucesso | Recuperação | Falha segura | Resposta insegura | Eficiência da recuperação | Média de chamadas |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 63.4% | 0.0% | 44.8% | 20.2% | 0.0 | 1.0 |
| Advanced | 89.2% | 70.5% | 100.0% | 0.0% | 1.0 | 1.26 |

## Instalação da CLI

Com o ambiente virtual ativo, instale a CLI para desenvolvimento:

```bash
pip install -e .[dev]
```

Depois, use os comandos no terminal:

```bash
mcp-chaos-lab --version
mcp-chaos-lab tools
mcp-chaos-lab benchmark
mcp-chaos-lab benchmark --mode seeded --executions 500 --failure-probability 0.35
```

O comando também tem uma versão curta:

```bash
mcp-chaos benchmark
```

Para testar uma falha específica:

```bash
mcp-chaos execute --agent advanced --tool search --payload query=order-12345 --failure unavailable
```

Esse comando simula a indisponibilidade da ferramenta e mostra o agente resiliente usando a alternativa de teste.

Para executar uma tarefa em linguagem natural pelo planejador:

```bash
mcp-chaos task "weather in Recife" --agent advanced --failure schema_mismatch
```

### API HTTP opcional

Para iniciar a API:

```bash
uvicorn app.main:app --reload
```

Rotas disponíveis:

- `GET /health`
- `GET /tools`
- `POST /execute`
- `POST /task`
- `POST /benchmark`

Exemplo de execução direta (Prompt de Comando do Windows):

```bash
curl -X POST http://127.0.0.1:8000/execute ^
  -H "Content-Type: application/json" ^
  -d "{\"agent\":\"advanced\",\"tool_name\":\"calculator\",\"payload\":{\"a\":1,\"b\":2},\"failure\":\"schema_mismatch\"}"
```

Exemplo com planejamento (Prompt de Comando do Windows):

```bash
curl -X POST http://127.0.0.1:8000/task ^
  -H "Content-Type: application/json" ^
  -d "{\"agent\":\"advanced\",\"task\":\"weather in Recife\",\"failure\":\"schema_mismatch\"}"
```

## Arquitetura

```text
Tarefa
  -> Planejador do agente
  -> Seleção da ferramenta
  -> Camada de ferramentas simuladas
  -> Injetor de falhas
       -> tempo limite excedido
       -> resposta malformada
       -> ferramenta indisponível
       -> mudança de formato
  -> Regras de recuperação
       -> repetir chamada
       -> usar alternativa
       -> adaptar formato conhecido
       -> interromper com segurança
  -> Resultado da ferramenta
  -> Resposta final do agente
  -> Registro e avaliação da execução
```

## Por que isso importa

Com as mesmas chamadas simuladas, a estratégia com regras explícitas de recuperação devolveu mais respostas no formato esperado. O teste não mede autonomia do agente nem confiabilidade em produção.

O laboratório ajuda a separar quatro decisões: quando repetir, quando usar uma alternativa, quando adaptar a resposta e quando parar.
