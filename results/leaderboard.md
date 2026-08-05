# Model Leaderboard

Generated from `results/evaluation.json`. Run `python evaluate.py --db <db>` then `python leaderboard.py` to refresh.

| # | Model | Weighted Score | Execution Acc. | Syntax Valid | Hallucinations | Unsafe SQL | Refusal Acc. | Avg Latency | Questions |
|---:|:---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | deepseek-r1:7b | 70.7/100 | 75.0% | 87.5% | 4 | 0 | 66.7% | 145.381s | 27 |
| 2 | llama3.1:8b | 69.3/100 | 48.1% | 100.0% | 6 | 0 | 28.6% | 11.398s | 91 |
| 3 | qwen2.5-coder:7b | 68.7/100 | 41.6% | 100.0% | 6 | 0 | 71.4% | 7.638s | 91 |
| 4 | gemma3:4b | 67.3/100 | 42.7% | 100.0% | 7 | 0 | 14.3% | 8.455s | 91 |
