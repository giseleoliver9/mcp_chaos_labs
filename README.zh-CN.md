# MCP Chaos Lab

![Python 3.11+](docs/badges/python.svg) ![FastAPI](docs/badges/fastapi.svg) ![Pydantic](docs/badges/pydantic.svg) ![pytest](docs/badges/pytest.svg) ![Docker · opcional/optional](docs/badges/docker.svg)

[![Português (BR)](docs/badges/lang-pt-br.svg)](README.md) [![English](docs/badges/lang-en.svg)](README.en.md) [![Español](docs/badges/lang-es.svg)](README.es.md) [![Français](docs/badges/lang-fr.svg)](README.fr.md) [![简体中文](docs/badges/lang-zh-cn.svg)](README.zh-CN.md)

**当 AI 智能体依赖的工具下线或返回损坏的数据时，会发生什么？**

MCP Chaos Lab 是一个用 Python 编写的模拟器，用来回答这个问题。它向两种策略发送相同的请求，注入故障，再展示哪种策略能返回结构有效的响应、使用备用结果，或停止执行。无需 Docker、API 密钥或真实模型即可体验。

## MCP 与本实验室

[模型上下文协议（MCP）](https://modelcontextprotocol.io/docs/learn/architecture) 是一项标准，让兼容的 AI 应用能够发现并调用服务器提供的工具。例如，气象 MCP 服务器可以提供名为 `get_rainfall(neighborhood, date)` 的只读工具，调用现有的气象 API，并返回降雨量、观测站、数据来源和时间戳。现有 REST API 无需修改；MCP 服务器充当 AI 客户端的适配器。

**本实验室并未实现 MCP 服务器或客户端。** 它在 Python 内模拟 MCP 风格的工具调用，以测试智能体如何处理故障。可选的 FastAPI 端点只是普通的 HTTP 端点，并非 MCP 传输接口。重试、回退和停止规则由实验室实现，并非 MCP 自带。

## 演示：工具不可用（30 秒）

![终端演示：基线策略遇到模拟故障时停止；弹性策略返回模拟的备用结果，并在数据格式错误时停止。](docs/mcp-chaos-lab-demo.gif)

两种策略收到相同的模拟搜索请求，并遭遇相同的强制故障。基线策略返回错误；弹性策略返回模拟的备用结果，并在日志中记录这次回退。备用结果来自模拟测试数据，不是真实缓存。模式校验只检查响应结构，不验证内容是否正确或最新。对于演示中的格式错误响应，弹性策略会停止，而不会把无效数据继续传下去。

安装 CLI 后，可复现这三次调用（无需 API 密钥、Docker 或真实模型）：

```bash
mcp-chaos execute --agent baseline --tool search --payload query=demo --failure unavailable
mcp-chaos execute --agent advanced --tool search --payload query=demo --failure unavailable
mcp-chaos execute --agent advanced --tool search --payload query=demo --failure malformed
```

## 在本地运行

**要求：** Python 3.11 或更新版本；克隆仓库需要 Git。如果没有 Git，请在 GitHub 上选择 **Code → Download ZIP**，解压后打开解压目录，并从 `python -m venv .venv` 开始。

### Windows（PowerShell）

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

命令会输出 `Cached fallback result for: demo` 和 `"recovered": true`。该响应是模拟的。将 `advanced` 改为 `baseline`，可以看到同一故障下未执行恢复的结果（`ToolUnavailableError`）；也可使用 `advanced` 和 `--failure malformed`，查看主动停止的结果（`SafeAbortError`）。这两种错误均符合预期，退出码为 1。

使用同一虚拟环境中的 Python 执行 `python -m app.cli benchmark` 或 `python -m pytest`，分别复现基准测试或运行测试套件。

## 测试内容

这个小型 Python 运行时比较两种策略：

- `BaselineAgent`：直接执行工具；如果工具失败，任务也失败。
- `ResilientAgent`：校验输出，区分故障类型，重试暂时性超时，切换到备用路径，适配已知的模式变更，并在数据格式错误时安全停止。

规划模式：

- `DeterministicPlanner`：可复现地从任务确定工具，用于基准测试。
- `LLMPlanner`：可连接真实大语言模型的规划适配器，不绑定供应商。调用方自行注入生成函数。

可靠性基准测试直接调用模拟工具，不使用规划器或真实模型，以便单独观察工具调用边界的行为。独立的 `task` 命令用于测试规划层。

故障模式：

- `timeout`：超时
- `tool unavailable`：工具不可用
- `malformed response`：响应格式错误
- `schema mismatch`：响应与模式不匹配

模拟的 MCP 风格工具：

- `calculator`：计算器
- `search`：搜索
- `weather`：天气

## 基准测试结果

使用以下命令生成：

```bash
python run_benchmark.py
```

每种策略使用 100 个一一对应的模拟用例，随机种子为 `7`。成功指返回通过结构校验的响应：

| 智能体 | 任务成功率 | 恢复率 | 安全失败率 | 不安全响应率 | 恢复效率 | 平均工具调用次数 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 25.0% | 0.0% | 50.7% | 37.0% | 0.0 | 1.0 |
| Advanced | 75.0% | 66.7% | 100.0% | 0.0% | 1.0 | 1.5 |

提升：`+50.0` 个百分点。

高级策略仍会有意拒绝格式错误的响应。目标不是在错误数据的基础上编造答案，而是在无法安全恢复时停止。

使用固定种子的混沌基准测试，更接近生产环境中的随机性：

```bash
mcp-chaos benchmark --mode seeded --executions 500 --failure-probability 0.35
```

最近一次固定种子测试结果：

| 智能体 | 任务成功率 | 恢复率 | 安全失败率 | 不安全响应率 | 恢复效率 | 平均工具调用次数 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 63.4% | 0.0% | 44.8% | 20.2% | 0.0 | 1.0 |
| Advanced | 89.2% | 70.5% | 100.0% | 0.0% | 1.0 | 1.26 |

## 安装为 CLI

用于本地开发：

```bash
pip install -e .[dev]
```

然后在终端中运行：

```bash
mcp-chaos-lab --version
mcp-chaos-lab tools
mcp-chaos-lab benchmark
mcp-chaos-lab benchmark --mode seeded --executions 500 --failure-probability 0.35
```

也可以使用更短的别名：

```bash
mcp-chaos benchmark
```

运行一个实际的故障示例：

```bash
mcp-chaos execute --agent advanced --tool search --payload query=order-12345 --failure unavailable
```

该命令模拟工具服务中断，并展示弹性智能体如何把请求转到备用路径，而不是直接崩溃。

通过规划器执行自然语言任务：

```bash
mcp-chaos task "weather in Recife" --agent advanced --failure schema_mismatch
```

启动 API：

```bash
uvicorn app.main:app --reload
```

可访问的端点：

- `GET /health`
- `GET /tools`
- `POST /execute`
- `POST /task`
- `POST /benchmark`

工具执行示例：

```bash
curl -X POST http://127.0.0.1:8000/execute ^
  -H "Content-Type: application/json" ^
  -d "{\"agent\":\"advanced\",\"tool_name\":\"calculator\",\"payload\":{\"a\":1,\"b\":2},\"failure\":\"schema_mismatch\"}"
```

任务规划示例：

```bash
curl -X POST http://127.0.0.1:8000/task ^
  -H "Content-Type: application/json" ^
  -d "{\"agent\":\"advanced\",\"task\":\"weather in Recife\",\"failure\":\"schema_mismatch\"}"
```

## 架构

```text
任务
  -> 智能体规划器
  -> 工具选择
  -> MCP 风格的工具层
  -> 故障注入器
       -> 超时
       -> 响应格式错误
       -> 工具不可用
       -> 响应与模式不匹配
  -> 恢复引擎
       -> 重试
       -> 回退
       -> 刷新模式
       -> 安全停止
  -> 工具结果
  -> 智能体最终响应
  -> 执行轨迹记录器 / 评估器
```

## 为什么重要

在相同的模拟工具调用下，采用明确恢复规则的策略返回了更多结构有效的响应。这个基准测试并不衡量智能体的自主性，也不能说明它在生产环境中的可靠性。

最可靠的行为不是“再努力一点”，而是知道何时重试、何时换工具、何时调整，以及何时停止。
