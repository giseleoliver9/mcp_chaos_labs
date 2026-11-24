# Tool Failure Lab

![Python 3.11+](docs/badges/python.svg) ![FastAPI](docs/badges/fastapi.svg) ![Pydantic](docs/badges/pydantic.svg) ![pytest](docs/badges/pytest.svg) ![Docker · opcional/optional](docs/badges/docker.svg)

[![Português (BR)](docs/badges/lang-pt-br.svg)](README.md) [![English](docs/badges/lang-en.svg)](README.en.md) [![Español](docs/badges/lang-es.svg)](README.es.md) [![Français](docs/badges/lang-fr.svg)](README.fr.md) [![简体中文](docs/badges/lang-zh-cn.svg)](README.zh-CN.md)

**Que se passe-t-il lorsqu’un outil dont dépend un agent d’IA devient indisponible ou renvoie des données invalides ?**

Tool Failure Lab est un simulateur Python conçu pour répondre à cette question. Il soumet la même requête à deux stratégies, injecte une panne et montre laquelle renvoie une réponse structurellement valide, utilise une solution de repli ou s’arrête. Vous pouvez l’essayer sans Docker, sans clé API et sans modèle en service.

## MCP et ce laboratoire

Le [Model Context Protocol (MCP)](https://modelcontextprotocol.io/docs/learn/architecture) est une norme qui permet à une application d’IA compatible de découvrir et d’appeler les outils exposés par un serveur. Par exemple, un serveur MCP météo pourrait exposer un outil en lecture seule appelé `get_rainfall(neighborhood, date)` qui interroge une API météo existante et renvoie le cumul de précipitations, la station, la source et l’horodatage. L’API REST n’a pas besoin de changer : le serveur MCP sert d’adaptateur pour les clients d’IA.

**Ce laboratoire n’implémente ni serveur ni client MCP.** Il simule des appels d’outils de type MCP dans Python afin de tester la gestion des pannes par un agent. Les points d’accès FastAPI facultatifs sont des points d’accès HTTP ordinaires, pas un mécanisme de transport MCP. Les règles de nouvelle tentative, de repli et d’arrêt sont implémentées dans le laboratoire ; MCP ne les fournit pas.

## Démonstration : outil indisponible (30 secondes)

![Démonstration dans le terminal : la stratégie de référence s’arrête lors d’une panne simulée ; la stratégie résiliente utilise un résultat de repli simulé et s’arrête face à des données mal formées.](docs/tool-failure-lab-demo.gif)

Les deux stratégies reçoivent la même requête de recherche simulée et subissent la même panne forcée. La stratégie de référence renvoie une erreur ; la stratégie résiliente renvoie un résultat de repli simulé et consigne son utilisation. Il provient de données de test, pas d’un cache actif. La vérification du schéma valide la structure de la réponse, pas son exactitude ni sa fraîcheur. Pour la réponse mal formée montrée dans la démonstration, la stratégie résiliente s’arrête plutôt que de transmettre des données invalides.

Reproduisez les trois appels après avoir installé l’interface en ligne de commande (aucune clé API, aucun Docker ni modèle en service requis) :

```bash
tool-failure-lab execute --agent baseline --tool search --payload query=demo --failure unavailable
tool-failure-lab execute --agent advanced --tool search --payload query=demo --failure unavailable
tool-failure-lab execute --agent advanced --tool search --payload query=demo --failure malformed
```

## Exécuter en local

**Prérequis :** Python 3.11 ou plus récent, et Git pour cloner le dépôt. Sans Git, choisissez **Code → Download ZIP** sur GitHub, décompressez l’archive, ouvrez le dossier extrait et commencez à `python -m venv .venv`.

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

La commande affiche `Cached fallback result for: demo` et `"recovered": true`. La réponse est simulée. Remplacez `advanced` par `baseline` pour reproduire la même panne sans récupération (`ToolUnavailableError`), ou utilisez `advanced` avec `--failure malformed` pour observer l’arrêt volontaire (`SafeAbortError`). Ces deux erreurs sont attendues et entraînent un code de sortie de 1.

Exécutez `python -m app.cli benchmark` ou `python -m pytest` avec le même interpréteur Python de l’environnement virtuel pour reproduire le benchmark ou lancer les tests.

## Ce que le laboratoire teste

Ce petit moteur Python compare deux stratégies :

- `BaselineAgent` : exécution directe de l’outil. Si l’outil échoue, la tâche échoue.
- `ResilientAgent` : valide la sortie, classe les pannes, relance les appels après un dépassement temporaire du délai, utilise des solutions de repli, s’adapte aux changements de schéma connus et s’arrête de manière sûre face à des données mal formées.

Modes de planification :

- `DeterministicPlanner` : associe les tâches aux outils de manière reproductible pour les benchmarks.
- `LLMPlanner` : adaptateur indépendant du fournisseur pour un planificateur reposant sur un vrai LLM. L’appelant fournit la fonction de génération, de sorte que le projet n’impose aucun fournisseur.

Le benchmark de fiabilité appelle directement des outils simulés, sans planificateur ni modèle en service, pour isoler le comportement à l’interface avec l’outil. La commande distincte `task` teste la couche de planification.

Modes de panne :

- `timeout` : dépassement du délai
- `tool unavailable` : outil indisponible
- `malformed response` : réponse mal formée
- `schema mismatch` : schéma incompatible

Outils simulés de type MCP :

- `calculator`
- `search`
- `weather`

## Résultats du benchmark

Générés avec :

```bash
python run_benchmark.py
```

100 cas simulés identiques par stratégie, graine `7`. Une tâche est considérée comme réussie si la réponse satisfait à la vérification structurelle :

| Agent | Réussite des tâches | Taux de récupération | Échec sûr | Réponse non sûre | Efficacité de la récupération | Nombre moyen d’appels d’outils |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 25.0% | 0.0% | 50.7% | 37.0% | 0.0 | 1.0 |
| Advanced | 75.0% | 66.7% | 100.0% | 0.0% | 1.0 | 1.5 |

Gain : `+50.0` points de pourcentage.

L’agent avancé s’arrête toujours volontairement face aux réponses mal formées. Le but n’est pas d’inventer une réponse en présence de données invalides, mais de s’arrêter de manière sûre lorsque la récupération présente un risque.

Benchmark avec une graine aléatoire fixe, dont la variabilité se rapproche de celle de la production :

```bash
tool-failure-lab benchmark --mode seeded --executions 500 --failure-probability 0.35
```

Résultats de la dernière exécution avec graine fixe :

| Agent | Réussite des tâches | Taux de récupération | Échec sûr | Réponse non sûre | Efficacité de la récupération | Nombre moyen d’appels d’outils |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 63.4% | 0.0% | 44.8% | 20.2% | 0.0 | 1.0 |
| Advanced | 89.2% | 70.5% | 100.0% | 0.0% | 1.0 | 1.26 |

## Installer l’interface en ligne de commande

Pour le développement local :

```bash
pip install -e .[dev]
```

Puis utilisez les commandes suivantes dans le terminal :

```bash
tool-failure-lab --version
tool-failure-lab tools
tool-failure-lab benchmark
tool-failure-lab benchmark --mode seeded --executions 500 --failure-probability 0.35
```

Exécutez un cas concret de panne :

```bash
tool-failure-lab execute --agent advanced --tool search --payload query=order-12345 --failure unavailable
```

Cette commande simule l’indisponibilité d’un outil et montre comment l’agent résilient redirige la requête vers une solution de repli au lieu de planter.

Soumettez une tâche en langage naturel au planificateur :

```bash
tool-failure-lab task "weather in Recife" --agent advanced --failure schema_mismatch
```

Lancez l’API :

```bash
uvicorn app.main:app --reload
```

Points d’accès :

- `GET /health`
- `GET /tools`
- `POST /execute`
- `POST /task`
- `POST /benchmark`

Exemple d’exécution d’un outil :

```bash
curl -X POST http://127.0.0.1:8000/execute ^
  -H "Content-Type: application/json" ^
  -d "{\"agent\":\"advanced\",\"tool_name\":\"calculator\",\"payload\":{\"a\":1,\"b\":2},\"failure\":\"schema_mismatch\"}"
```

Exemple de tâche planifiée :

```bash
curl -X POST http://127.0.0.1:8000/task ^
  -H "Content-Type: application/json" ^
  -d "{\"agent\":\"advanced\",\"task\":\"weather in Recife\",\"failure\":\"schema_mismatch\"}"
```

## Architecture

```text
Tâche
  -> Planificateur de l’agent
  -> Sélection de l’outil
  -> Couche d’outils de type MCP
  -> Injecteur de pannes
       -> dépassement du délai
       -> réponse mal formée
       -> outil indisponible
       -> schéma incompatible
  -> Moteur de récupération
       -> réessayer
       -> utiliser une solution de repli
       -> actualiser le schéma
       -> s’arrêter de manière sûre
  -> Résultat de l’outil
  -> Réponse finale de l’agent
  -> Journalisation et évaluation du parcours d’exécution
```

## Pourquoi c’est important

Pour les mêmes appels d’outils simulés, la stratégie dotée de règles explicites de récupération a renvoyé davantage de réponses structurellement valides. Ce benchmark ne mesure ni l’autonomie des agents ni leur fiabilité en production.

Le comportement le plus fiable ne consistait pas à « insister », mais à savoir quand réessayer, changer d’outil, s’adapter ou s’arrêter.
