#!/usr/bin/env python3
"""
NVIDIA NIM Free Model Speed Benchmark
Auto-discovers available chat models from your API key, then benchmarks them.

Usage:
    export NVIDIA_API_KEY=your_key_here
    python3 nim_benchmark.py

Optional flags:
    --top N       Only test the first N models (default: all)
    --runs N      Runs per model for averaging (default: 1)
    --filter STR  Only test models whose name contains STR (e.g. llama, mistral)
"""

import os
import time
import json
import urllib.request
import urllib.error
import argparse

API_KEY = os.environ.get("NVIDIA_API_KEY", "")
if not API_KEY:
    raise SystemExit("NVIDIA_API_KEY not set. Run: export NVIDIA_API_KEY=<your_key>")

BASE = "https://integrate.api.nvidia.com/v1"
PROMPT = "Reply with exactly one short sentence about space."


def api_get(path):
    req = urllib.request.Request(
        BASE + path,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def api_post(path, payload):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def fetch_models():
    data = api_get("/models")
    return sorted(m["id"] for m in data.get("data", []))


def benchmark(model, runs=1):
    latencies, tokens = [], []
    last_reply = ""
    for _ in range(runs):
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": PROMPT}],
            "max_tokens": 60,
            "stream": False,
        }
        t0 = time.perf_counter()
        try:
            data = api_post("/chat/completions", payload)
            elapsed = time.perf_counter() - t0
            reply = data["choices"][0]["message"]["content"].strip()
            tok = data.get("usage", {}).get("completion_tokens", 0)
            latencies.append(elapsed)
            tokens.append(tok)
            last_reply = reply
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            return None, None, None, f"HTTP {e.code}: {body[:100]}"
        except TimeoutError:
            return None, None, None, "TIMEOUT >5s"
        except Exception as ex:
            return None, None, None, str(ex)[:100]

    avg_lat = sum(latencies) / len(latencies)
    avg_tok = sum(tokens) / len(tokens)
    tps = round(avg_tok / avg_lat, 1) if avg_lat else 0
    return avg_lat, int(avg_tok), tps, last_reply


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--top", type=int, default=0, help="limit to first N models")
    p.add_argument("--runs", type=int, default=1, help="runs per model")
    p.add_argument(
        "--filter", type=str, default="", help="substring filter on model name"
    )
    args = p.parse_args()

    print("\nFetching model list from API...", flush=True)
    try:
        models = fetch_models()
    except Exception as e:
        raise SystemExit(f"Could not fetch models: {e}")

    if args.filter:
        models = [m for m in models if args.filter.lower() in m.lower()]
    if args.top:
        models = models[: args.top]

    print(f"Found {len(models)} model(s) to test\n")
    print(f"{'=' * 70}")
    print(f"  NVIDIA NIM Speed Benchmark   (runs/model: {args.runs})")
    print(f'  Prompt: "{PROMPT}"')
    print(f"{'=' * 70}\n")

    results = []
    skipped = []

    for model in models:
        short = model[:50]
        print(f"  >> {short:<52}", end="", flush=True)
        lat, tok, tps, reply = benchmark(model, runs=args.runs)
        if lat is None:
            print(f" SKIP  ({reply[:50]})")
            skipped.append((model, reply))
            continue
        print(f" {lat:.2f}s | {tok} tok | {tps} tok/s")
        results.append((model, lat, tok, tps, reply))

    if not results:
        print("\n  No models responded successfully.")
        if skipped:
            print("\n  Skipped:")
            for m, r in skipped:
                print(f"    - {m}: {r}")
        return

    results.sort(key=lambda x: x[1])

    print(f"\n{'=' * 70}")
    print("  LEADERBOARD  (fastest to slowest)")
    print(f"{'=' * 70}")
    print(f"  {'#':<5} {'Model':<48} {'Latency':>8}  {'tok/s':>7}")
    print(f"  {'-' * 68}")

    medals = {1: "1st", 2: "2nd", 3: "3rd"}
    for i, (model, lat, tok, tps, _) in enumerate(results, 1):
        badge = medals.get(i, f"  {i}.")
        short = model[:46]
        print(f"  {badge:<5} {short:<48} {lat:.2f}s   {str(tps):>6}")

    w = results[0]
    print(f"\n  WINNER  : {w[0]}")
    print(f"  Latency : {w[1]:.2f}s")
    print(f"  tok/s   : {w[3]}")
    print(f'  Reply   : "{w[4][:80]}"')

    if skipped:
        print(
            f"\n  Note: {len(skipped)} model(s) skipped (not chat-compatible or no access)"
        )
    print()


if __name__ == "__main__":
    main()
