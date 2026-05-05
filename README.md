# NVIDIA NIM Speed Benchmark

Auto-discovers available chat models from your NVIDIA API key and benchmarks them for latency and throughput.

## Requirements

- Python 3.8+
- NVIDIA API key ([get one here](https://org.ngc.nvidia.com/))

## Setup

```bash
# Set your API key
export NVIDIA_API_KEY=your_key_here

# Run the benchmark
python3 main.py
```

## Usage

```bash
# Basic usage
python3 main.py

# Test only top 5 fastest models
python3 main.py --top 5

# Run multiple iterations per model for averaging
python3 main.py --runs 3

# Filter to specific model families (e.g., llama, mistral)
python3 main.py --filter llama
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--top N` | Only test first N models | All |
| `--runs N` | Runs per model for averaging | 1 |
| `--filter STR` | Only test models containing STR | None |

## Output

The benchmark outputs:

- **Latency** — Time to first token (seconds)
- **Tokens** — Completion tokens generated
- **tok/s** — Throughput (tokens/second)
- **Leaderboard** — Ranked fastest to slowest

### Example Output

```
Fetching model list from API...
Found 12 model(s) to test

======================================================================
  NVIDIA NIM Speed Benchmark   (runs/model: 1)
======================================================================

  >> llama-3.1-405b-instruct                     2.31s | 58 tok | 25.1 tok/s
  >> llama-3.1-70b-instruct                      1.89s | 57 tok | 30.2 tok/s
  >> mixtral-8x7b-instruct                       1.12s | 56 tok | 50.0 tok/s

======================================================================
  LEADERBOARD  (fastest to slowest)
======================================================================
  #    Model                                             Latency    tok/s
  --------------------------------------------------------------------
  1st  mixtral-8x7b-instruct                            1.12s      50
  2nd  llama-3.1-70b-instruct                           1.89s      30
  3rd  llama-3.1-405b-instruct                          2.31s      25

  WINNER  : mixtral-8x7b-instruct
  Latency : 1.12s
  tok/s   : 50
  Reply   : "Space exploration has revolutionized our understanding of the universe."
```

## How It Works

1. Fetches all available chat models from `https://integrate.api.nvidia.com/v1/models`
2. Sends a simple prompt to each model ("Reply with exactly one short sentence about space.")
3. Measures latency from request to first response
4. Calculates tokens/second throughput
5. Ranks models by latency

## Notes

- Models that aren't chat-compatible or lack API access are automatically skipped
- The `--runs` flag helps smooth out variance from network latency
- Use `--filter` to focus on specific model families you have access to