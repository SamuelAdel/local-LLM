"""
leaderboard.py

Turns results/evaluation.json (produced by `python evaluate.py`) into a
single ranked leaderboard table, instead of reading evaluation.csv/.txt
row by row.

Usage:
    python evaluate.py --db enterprise.db   # produces results/evaluation.json
    python leaderboard.py                   # reads it, prints + saves the table

Output:
    - Printed to the console as an aligned text table.
    - results/leaderboard.md   (Markdown table, e.g. for a GitHub README)
    - results/leaderboard.txt  (same aligned text table, for sharing/logs)

This script is intentionally read-only with respect to evaluate.py: it
does not re-score anything, it only re-presents the "summary" section
evaluate.py already computed, sorted by weighted score. Run evaluate.py
again first if you want the leaderboard to reflect a new run.
"""

import json
import sys
from pathlib import Path

RESULTS_DIR = Path("results")
REPORT_JSON = RESULTS_DIR / "evaluation.json"
LEADERBOARD_MD = RESULTS_DIR / "leaderboard.md"
LEADERBOARD_TXT = RESULTS_DIR / "leaderboard.txt"

# Columns shown on the leaderboard: (json key(s), header, formatter)
# "score" is nested under summary[model][key], except latency which is
# nested one level deeper under summary[model]["latency"]["avg"].


def fmt_pct(v):
    return "N/A" if v is None else f"{v}%"


def fmt_num(v):
    return "N/A" if v is None else str(v)


def fmt_latency(summary):
    latency = summary.get("latency")
    if not latency or latency.get("avg") is None:
        return "N/A"
    return f"{latency['avg']}s"


def fmt_refusal(summary):
    total = summary.get("refusal_total") or 0
    correct = summary.get("refusal_correct") or 0
    if total == 0:
        return "N/A"
    pct = round(100 * correct / total, 1)
    return f"{pct}%"


COLUMNS = [
    ("rank", "#", None),
    ("model", "Model", None),
    ("avg_score", "Weighted Score", lambda s: f"{s['avg_score']}/100" if s.get("avg_score") is not None else "N/A"),
    ("execution_accuracy", "Execution Acc.", lambda s: fmt_pct(s.get("execution_accuracy"))),
    ("syntax_valid_rate", "Syntax Valid", lambda s: fmt_pct(s.get("syntax_valid_rate"))),
    ("hallucination_count", "Hallucinations", lambda s: fmt_num(s.get("hallucination_count"))),
    ("unsafe_sql_count", "Unsafe SQL", lambda s: fmt_num(s.get("unsafe_sql_count"))),
    ("refusal", "Refusal Acc.", fmt_refusal),
    ("latency", "Avg Latency", fmt_latency),
    ("n", "Questions", lambda s: fmt_num(s.get("n"))),
]


def load_summaries():
    if not REPORT_JSON.exists():
        print(f"ERROR: {REPORT_JSON} not found.")
        print("Run `python evaluate.py --db <your.db>` first to generate it.")
        sys.exit(1)

    payload = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    summary = payload.get("summary", {})
    # Drop models with no scored questions (n == 0 / missing results file).
    return {m: s for m, s in summary.items() if s.get("n", 0) > 0}


def rank_models(summaries):
    """Highest weighted score first; ties broken by execution accuracy."""
    def sort_key(item):
        _, s = item
        return (
            -(s.get("avg_score") or 0),
            -(s.get("execution_accuracy") or 0),
        )
    return sorted(summaries.items(), key=sort_key)


def build_rows(ranked):
    rows = []
    for i, (model, summary) in enumerate(ranked, start=1):
        row = {"rank": str(i), "model": model}
        for key, _header, formatter in COLUMNS:
            if key in ("rank", "model"):
                continue
            row[key] = formatter(summary)
        rows.append(row)
    return rows


def render_text_table(rows):
    headers = [h for _key, h, _fmt in COLUMNS]
    keys = [k for k, _h, _fmt in COLUMNS]

    widths = [len(h) for h in headers]
    for row in rows:
        for i, k in enumerate(keys):
            widths[i] = max(widths[i], len(row[k]))

    def render_row(values):
        return "  ".join(v.ljust(widths[i]) for i, v in enumerate(values))

    lines = [
        render_row(headers),
        "  ".join("-" * w for w in widths),
    ]
    for row in rows:
        lines.append(render_row([row[k] for k in keys]))
    return "\n".join(lines)


def render_markdown_table(rows):
    headers = [h for _key, h, _fmt in COLUMNS]
    keys = [k for k, _h, _fmt in COLUMNS]

    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---:" if k not in ("model",) else ":---" for k in keys]) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row[k] for k in keys) + " |")
    return "\n".join(lines)


def main():
    summaries = load_summaries()
    if not summaries:
        print("No scored models found in results/evaluation.json.")
        sys.exit(1)

    ranked = rank_models(summaries)
    rows = build_rows(ranked)

    text_table = render_text_table(rows)
    md_table = render_markdown_table(rows)

    print("\nLEADERBOARD (by weighted score)\n")
    print(text_table)

    RESULTS_DIR.mkdir(exist_ok=True)
    LEADERBOARD_TXT.write_text(text_table + "\n", encoding="utf-8")
    LEADERBOARD_MD.write_text(
        "# Model Leaderboard\n\n"
        "Generated from `results/evaluation.json`. Run `python evaluate.py --db <db>` "
        "then `python leaderboard.py` to refresh.\n\n" + md_table + "\n",
        encoding="utf-8",
    )

    print(f"\nSaved to: {LEADERBOARD_TXT}")
    print(f"Saved to: {LEADERBOARD_MD}")


if __name__ == "__main__":
    main()
