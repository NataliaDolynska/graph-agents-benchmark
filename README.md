# Graph Agents Benchmark 
_Work in progress...._

A benchmarking framework for evaluating AI agents' performance on graph database tasks.

## Features

- Standardized evaluation of graph query generation
- Support for multiple AI frameworks (LangChain, LlamaIndex, custom)
- Detailed performance metrics (accuracy, latency, error rate)
- Easy integration with Neo4j

## Requirements

1. [UV](https://docs.astral.sh/uv/) - project dependency management command line tool.
2. [Docker/Docker compose](https://docs.docker.com/compose/) - containers management tool
3. UNIX based system for executing bash scripts 
4. Access to one of defined LLM models (OLLAMA ... TBD)

## Quick Start

1. Install dependencies:

```bash
uv sync
```

2. Configure database connection in `.env`:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEOPSW=your_password
```

3. Run benchmark:

```bash
python -m graph_agents_benchmark.main --agent-type langchain --model gpt-4
```

## Project Structure

```
graph-agents-benchmark/
├── src/
│   ├── graph_agents_benchmark/    # Core benchmarking logic
│   ├── model_provider.py          # Model management
│   ├── utils/                     # Utilities
│   └── solution/                  # Agent implementations
├── results/                       # Benchmark results
└── configs/                       # Configuration files
```

## Supported Agents

| Framework | Version | Features |
|-----------|---------|----------|
| TBD       | TBD     | TBD      |

------

## 📄 [License](LICENSE.txt)

_This project is licensed under the **Apache 2.0 License**. See the LICENSE file for details.
Please note: Public deployments of this project must visibly credit the original creator, **Natalia Dolynska**, on the
main UI._

