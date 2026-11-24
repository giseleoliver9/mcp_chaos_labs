# Tool Failure Lab

![Python 3.11+](docs/badges/python.svg) ![FastAPI](docs/badges/fastapi.svg) ![Pydantic](docs/badges/pydantic.svg) ![pytest](docs/badges/pytest.svg) ![Docker · opcional/optional](docs/badges/docker.svg)

[![Português (BR)](docs/badges/lang-pt-br.svg)](README.md) [![English](docs/badges/lang-en.svg)](README.en.md) [![Español](docs/badges/lang-es.svg)](README.es.md) [![Français](docs/badges/lang-fr.svg)](README.fr.md) [![简体中文](docs/badges/lang-zh-cn.svg)](README.zh-CN.md)

**¿Qué pasa cuando una herramienta de la que depende un agente de IA deja de funcionar o devuelve datos inválidos?**

Tool Failure Lab es un simulador en Python que permite responder a esa pregunta. Envía la misma solicitud a dos estrategias, inyecta un fallo y muestra cuál devuelve una respuesta estructuralmente válida, recurre a una alternativa o se detiene. Puedes probarlo sin Docker, sin clave de API y sin un modelo en ejecución.

## MCP y este laboratorio

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/docs/learn/architecture) es un estándar que permite a una aplicación de IA compatible descubrir e invocar herramientas que ofrece un servidor. Por ejemplo, un servidor MCP meteorológico podría ofrecer una herramienta de solo lectura llamada `get_rainfall(neighborhood, date)` que consulta una API meteorológica existente y devuelve la cantidad de lluvia, la estación, la fuente y la fecha y hora del registro. La API REST puede seguir tal como está; el servidor MCP actúa como adaptador para los clientes de IA.

**Este laboratorio no implementa un servidor ni un cliente MCP.** Simula llamadas a herramientas al estilo de MCP dentro de Python para comprobar cómo responde un agente ante fallos. Sus endpoints opcionales de FastAPI son endpoints HTTP convencionales, no un transporte MCP. Las reglas de reintento, recuperación mediante una alternativa y detención las implementa el laboratorio; no forman parte de MCP.

## ¿Puedo corregir el problema?

**Hoy, el laboratorio simula fallos dentro del propio laboratorio.** Te ayuda a reproducir y entender un fallo, pero no prueba tu aplicación directamente ni corrige el código por ti. El proceso es: **reproducir el fallo → corregir tu aplicación → repetir la prueba** para verificar su comportamiento.

**Idea para un futuro modo HTTP (aún no disponible):** imagina que una tienda ficticia consulta el coste del envío por código postal. Un endpoint de prueba devolvería primero `502` y, en el siguiente intento, `200` con un coste de envío ficticio de **R$ 20**. Podrías observar cuántas solicitudes hizo la aplicación. Si se detuviera al recibir el primer error, podrías añadir un único reintento para ese `502` en la consulta, que es de solo lectura. Luego repetirías el escenario para comprobar que la aplicación hizo dos solicitudes y mostró el coste del envío. **Todavía no puedes conectar tu aplicación al laboratorio para ejecutar este escenario.**

## Demostración: herramienta no disponible (30 segundos)

![Demostración en la terminal: la estrategia base se detiene ante una interrupción simulada; la estrategia resiliente devuelve una respuesta alternativa simulada y se detiene ante datos malformados.](docs/tool-failure-lab-demo.gif)

Las dos estrategias reciben la misma solicitud de búsqueda simulada y el mismo fallo forzado. La estrategia base devuelve un error; la resiliente devuelve una respuesta alternativa simulada y registra que la usó. La alternativa es un dato de prueba, no una caché real. La comprobación del esquema valida la estructura de la respuesta, no su exactitud ni su vigencia. Ante la respuesta malformada que se muestra en la demostración, la estrategia resiliente se detiene en lugar de propagar datos inválidos.

Reproduce las tres llamadas tras instalar la CLI (no necesitas una clave de API, Docker ni un modelo en ejecución):

```bash
tool-failure-lab execute --agent baseline --tool search --payload query=demo --failure unavailable
tool-failure-lab execute --agent advanced --tool search --payload query=demo --failure unavailable
tool-failure-lab execute --agent advanced --tool search --payload query=demo --failure malformed
```

## Ejecución local

**Requisitos:** Python 3.11 o posterior y Git para clonar el repositorio. Si no tienes Git, selecciona **Code → Download ZIP** en GitHub, descomprime el archivo, abre la carpeta extraída y empieza por `python -m venv .venv`.

### Windows (PowerShell)

```powershell
git clone https://github.com/giseleoliver9/tool-failure-lab.git
cd tool-failure-lab
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m app.cli execute --agent advanced --tool search --payload query=demo --failure unavailable
```

### macOS / Linux

```bash
git clone https://github.com/giseleoliver9/tool-failure-lab.git
cd tool-failure-lab
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m app.cli execute --agent advanced --tool search --payload query=demo --failure unavailable
```

El comando imprime `Cached fallback result for: demo` y `"recovered": true`. La respuesta es simulada. Cambia `advanced` por `baseline` para reproducir la misma interrupción sin recuperación (`ToolUnavailableError`), o usa `advanced` con `--failure malformed` para ver la detención deliberada (`SafeAbortError`). Ambos errores son esperados y el proceso termina con el código 1.

Ejecuta `python -m app.cli benchmark` o `python -m pytest` con el mismo intérprete de Python del entorno virtual para reproducir el benchmark o ejecutar las pruebas.

## Qué se pone a prueba

El entorno de ejecución en Python compara dos estrategias:

- `BaselineAgent`: ejecuta la herramienta directamente. Si la herramienta falla, la tarea falla.
- `ResilientAgent`: valida la salida, clasifica los fallos, reintenta cuando el tiempo de espera se supera por un fallo transitorio, recurre a alternativas, se adapta a cambios conocidos del esquema y se detiene de forma segura ante datos malformados.

Modos de planificación:

- `DeterministicPlanner`: planificación reproducible que vincula una tarea con una herramienta, pensada para benchmarks.
- `LLMPlanner`: adaptador independiente del proveedor para usar un LLM en la planificación. El código que lo invoca proporciona la función de generación, así que el proyecto no impone un proveedor.

El benchmark de fiabilidad llama directamente a herramientas simuladas, sin planificador ni modelo en ejecución, para aislar el comportamiento en la interfaz con la herramienta. El comando `task`, por separado, permite probar la capa de planificación.

Tipos de fallo:

- `timeout` (se supera el tiempo de espera)
- `tool unavailable` (herramienta no disponible)
- `malformed response` (respuesta malformada)
- `schema mismatch` (esquema incompatible)

Herramientas simuladas al estilo de MCP:

- `calculator`
- `search`
- `weather`

## Resultados del benchmark

Generados con:

```bash
python run_benchmark.py
```

100 casos simulados idénticos para cada estrategia, semilla `7`. El éxito consiste en devolver una respuesta que supera la validación estructural:

| Agente | Éxito de la tarea | Tasa de recuperación | Fallo seguro | Respuesta insegura | Eficiencia de recuperación | Promedio de llamadas |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | 25.0% | 0.0% | 50.7% | 37.0% | 0.0 | 1.0 |
| Avanzado | 75.0% | 66.7% | 100.0% | 0.0% | 1.0 | 1.5 |

Mejora: `+50.0 puntos porcentuales`.

El agente avanzado sigue fallando deliberadamente ante respuestas malformadas. En vez de inventar una respuesta a partir de datos inválidos, se detiene de forma segura cuando no es posible recuperarse sin riesgo.

Benchmark de fallos aleatorios con semilla, más parecido a la variabilidad de un entorno de producción:

```bash
tool-failure-lab benchmark --mode seeded --executions 500 --failure-probability 0.35
```

Última ejecución con semilla:

| Agente | Éxito de la tarea | Tasa de recuperación | Fallo seguro | Respuesta insegura | Eficiencia de recuperación | Promedio de llamadas |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | 63.4% | 0.0% | 44.8% | 20.2% | 0.0 | 1.0 |
| Avanzado | 89.2% | 70.5% | 100.0% | 0.0% | 1.0 | 1.26 |

## Instalación de la CLI

Para desarrollo local:

```bash
pip install -e .[dev]
```

Luego, usa estos comandos en la terminal:

```bash
tool-failure-lab --version
tool-failure-lab tools
tool-failure-lab benchmark
tool-failure-lab benchmark --mode seeded --executions 500 --failure-probability 0.35
```

Prueba un caso de fallo concreto:

```bash
tool-failure-lab execute --agent advanced --tool search --payload query=order-12345 --failure unavailable
```

El comando simula la caída de una herramienta y muestra cómo el agente resiliente redirige la solicitud a una alternativa en lugar de fallar.

Ejecuta una tarea en lenguaje natural mediante el planificador:

```bash
tool-failure-lab task "weather in Recife" --agent advanced --failure schema_mismatch
```

Inicia la API:

```bash
uvicorn app.main:app --reload
```

Endpoints:

- `GET /health`
- `GET /tools`
- `POST /execute`
- `POST /task`
- `POST /benchmark`

Ejemplo de ejecución de una herramienta:

```bash
curl -X POST http://127.0.0.1:8000/execute ^
  -H "Content-Type: application/json" ^
  -d "{\"agent\":\"advanced\",\"tool_name\":\"calculator\",\"payload\":{\"a\":1,\"b\":2},\"failure\":\"schema_mismatch\"}"
```

Ejemplo de tarea con planificación:

```bash
curl -X POST http://127.0.0.1:8000/task ^
  -H "Content-Type: application/json" ^
  -d "{\"agent\":\"advanced\",\"task\":\"weather in Recife\",\"failure\":\"schema_mismatch\"}"
```

## Arquitectura

```text
Tarea
  -> Planificador del agente
  -> Selección de herramienta
  -> Capa de herramientas tipo MCP
  -> Inyector de fallos
       -> tiempo de espera superado
       -> respuesta malformada
       -> herramienta no disponible
       -> esquema incompatible
  -> Motor de recuperación
       -> reintento
       -> alternativa
       -> actualización del esquema
       -> detención segura
  -> Resultado de la herramienta
  -> Respuesta final del agente
  -> Registro y evaluación de trayectorias
```

## Por qué importa

Ante las mismas llamadas a herramientas simuladas, la estrategia con políticas explícitas de recuperación devolvió más respuestas estructuralmente válidas. Este benchmark no mide la autonomía del agente ni su fiabilidad en producción.

La estrategia más fiable no consistió en insistir, sino en saber cuándo reintentar, cuándo cambiar de herramienta, cuándo adaptar la respuesta y cuándo detenerse.
