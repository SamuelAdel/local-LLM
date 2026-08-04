"""
evaluate.py

Scores each model's generated SQL (results/<model>.txt) against the
reference answers in expected_sql.py, and flags likely hallucinations
(tables/columns referenced that don't exist in schema.py).

v2 additions (see CHANGELOG at bottom of this docstring):
  - Execution Accuracy: if a SQLite DB is available, gold and generated SQL
    are both executed and their result sets compared, instead of relying
    only on text similarity.
  - SQL syntax validation (heuristic) + destructive-statement detection.
  - Per-question error classification (single reason code).
  - EXPECTED_SQL[qid] may now be a str OR a list[str] of acceptable golds.
  - Optional latency / token-usage stats, parsed from the result file if
    main.py logs them (safe no-op if it doesn't).
  - Category / difficulty accuracy breakdown, weighted score, ranking.
  - Reports written as .txt (human-readable), .json, and .csv.

This is still intentionally lightweight -- not a real SQL parser -- so
treat "hallucination" flags, "syntax_valid", and any REVIEW/EXECUTION_MISMATCH
status as strong hints for a human reviewer, not a final verdict. Exact-match,
execution-match (when a DB is configured), and refusal checks are the most
reliable signals here; everything else is best-effort static analysis.

Usage:
    python evaluate.py [--db path/to/database.sqlite]

CHANGELOG (v1 -> v2):
  - Added execution accuracy (optional, requires --db / DB_PATH).
  - Added syntax validation + destructive statement flag.
  - Added error classification per question.
  - Added support for multiple gold SQL variants per question.
  - Added latency / token stat parsing (optional, tolerant of absence).
  - Added category/difficulty accuracy tables.
  - Added weighted score + final ranking table.
  - Added JSON and CSV report export.
"""

import argparse
import csv
import json
import re
import sqlite3
import statistics
import difflib
from pathlib import Path

from models import MODELS
from schema import DATABASE_SCHEMA
from questions import QUESTIONS
from expected_sql import EXPECTED_SQL
from main import safe_filename, DONE_MARKER

RESULTS_DIR = Path("results")
REPORT_TXT = RESULTS_DIR / "evaluation.txt"
REPORT_JSON = RESULTS_DIR / "evaluation.json"
REPORT_CSV = RESULTS_DIR / "evaluation.csv"

REFUSAL_TOKEN = "CANNOT_GENERATE_SQL"

# Statements that must never be executed against the DB during scoring, and
# that automatically fail a question regardless of what else is true about it.
_DESTRUCTIVE_STATEMENT = re.compile(
    r"^\s*(?:DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|ATTACH|DETACH|REPLACE)\b",
    re.IGNORECASE,
)

# Weights for the composite per-question score (must sum to 1.0).
SCORE_WEIGHTS = {
    "correctness": 0.5,   # execution/exact match (or correct refusal)
    "syntax": 0.2,        # SQL parses / looks structurally valid
    "no_hallucination": 0.2,
    "latency": 0.1,       # only contributes if latency data is present
}


# ---------------------------------------------------------------------
# Error classification codes
# ---------------------------------------------------------------------

class Verdict:
    CORRECT = "CORRECT"
    CORRECT_REFUSAL = "CORRECT_REFUSAL"
    MISSED_REFUSAL = "MISSED_REFUSAL"      # should have refused, gave SQL instead
    FALSE_REFUSAL = "FALSE_REFUSAL"        # refused when a valid query existed
    SYNTAX_ERROR = "SYNTAX_ERROR"
    UNSAFE_SQL = "UNSAFE_SQL"              # destructive statement generated
    SCHEMA_HALLUCINATION = "SCHEMA_HALLUCINATION"
    EXECUTION_MISMATCH = "EXECUTION_MISMATCH"
    EXECUTION_ERROR = "EXECUTION_ERROR"    # ran but the DB raised an error
    REVIEW = "REVIEW"                      # text differs, no DB to confirm
    MISSING = "MISSING"


# ---------------------------------------------------------------------
# Schema parsing (for hallucination detection)
# ---------------------------------------------------------------------

def parse_schema(schema_text):
    """
    Returns {table_name_lower: set(column_name_lower)} built from schema.py's
    `Table(\n  col TYPE,\n  ...\n)` blocks.
    """
    tables = {}
    for match in re.finditer(r"(\w+)\s*\(([^)]*)\)", schema_text, re.S):
        table_name = match.group(1).lower()
        body = match.group(2)
        columns = set()
        for line in body.splitlines():
            line = line.strip().rstrip(",")
            if not line:
                continue
            col = line.split()[0].lower()
            columns.add(col)
        tables[table_name] = columns
    return tables


TABLES = parse_schema(DATABASE_SCHEMA)


# Functions whose argument list can contain a "FROM" keyword that has
# nothing to do with a table clause, e.g. EXTRACT(MONTH FROM order_date).
# We strip these bodies out before scanning for FROM/JOIN tables.
_FROM_KEYWORD_FUNCS = re.compile(
    r"\b(?:EXTRACT|TRIM|SUBSTRING)\s*\([^)]*\)", re.IGNORECASE
)

_SQL_FUNCS = {
    "count", "sum", "avg", "min", "max", "distinct", "as", "rank", "over",
    "partition", "coalesce", "cast", "extract", "year", "month", "day",
    "trim", "substring", "upper", "lower", "round", "case", "when", "then",
    "else", "end", "null", "not", "in", "exists", "top",
}

# NOTE (known limitation, not fixed in this pass): this hallucination check
# is regex-based, not a real parser. It does not reliably understand CTEs
# (WITH x AS (...)), derived tables/subqueries in FROM, or UNION branches --
# a CTE or subquery alias can be misreported as an "unknown table". If false
# positives from these show up often, the real fix is swapping in a proper
# SQL parser (e.g. sqlglot) rather than patching the regex further.

def find_hallucinations(sql, tables):
    """
    Best-effort check for:
      - FROM/JOIN referencing a table not in the schema
      - alias.column (or bare column, single-table queries only) referencing
        a column not in the real table
    Returns a list of human-readable issue strings (empty if none found).
    """
    issues = []
    scan_sql = _FROM_KEYWORD_FUNCS.sub(" ", sql)

    # alias -> real table name, from "FROM Table [AS] alias" / "JOIN Table [AS] alias"
    alias_map = {}
    referenced_tables = []
    for m in re.finditer(
        r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s+AS)?\s*([A-Za-z_][A-Za-z0-9_]*)?",
        scan_sql,
        re.IGNORECASE,
    ):
        table = m.group(1)
        alias = m.group(2)
        table_lower = table.lower()

        if table_lower not in tables:
            issues.append(f"unknown table referenced: '{table}'")
            continue

        referenced_tables.append(table_lower)
        alias_map[table_lower] = table_lower
        if alias and alias.lower() not in _SQL_FUNCS and alias.upper() not in (
            "ON", "WHERE", "GROUP", "ORDER", "HAVING", "LIMIT", "AS", "JOIN",
        ):
            alias_map[alias.lower()] = table_lower

    # alias.column references
    qualified_cols = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\b", sql))
    for alias, column in qualified_cols:
        alias_l, column_l = alias.lower(), column.lower()
        if alias_l in alias_map:
            real_table = alias_map[alias_l]
            if column_l not in tables[real_table]:
                issues.append(
                    f"unknown column '{column}' on table '{real_table}' (via '{alias}.{column}')"
                )

    # bare column references -- only reliable when exactly one table is
    # involved (no JOIN), otherwise we can't tell which table a bare
    # column belongs to.
    if len(set(referenced_tables)) == 1 and not qualified_cols:
        real_table = referenced_tables[0]
        select_match = re.search(r"SELECT\s+(.*?)\s+FROM", sql, re.IGNORECASE | re.S)
        if select_match:
            select_list = select_match.group(1)
            if select_list.strip() != "*":
                # drop "AS alias_name" (output aliases aren't real columns)
                select_list = re.sub(r"\bAS\s+[A-Za-z_][A-Za-z0-9_]*", " ", select_list, flags=re.IGNORECASE)
                for ident in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", select_list):
                    ident_l = ident.lower()
                    if ident_l in _SQL_FUNCS or ident_l in tables:
                        continue
                    if ident_l not in tables[real_table]:
                        issues.append(
                            f"unknown column '{ident}' on table '{real_table}' (bare reference in SELECT)"
                        )

    return issues


# ---------------------------------------------------------------------
# Syntax validation (heuristic -- no external SQL parser dependency)
# ---------------------------------------------------------------------

def check_syntax(sql):
    """
    Returns (is_valid, reason_or_None). This is NOT a real parser -- it
    catches the common failure modes (unbalanced parens/quotes, missing
    FROM, obviously misspelled keywords) but will miss subtler errors.
    A definitive syntax check would require actually preparing the
    statement against a real SQL engine.
    """
    s = sql.strip()
    if not s:
        return False, "empty statement"

    if s.count("(") != s.count(")"):
        return False, "unbalanced parentheses"

    # naive quote balance check (ignores escaped quotes, good enough here)
    if s.count("'") % 2 != 0:
        return False, "unbalanced single quotes"

    if not re.match(r"^\s*(SELECT|WITH)\b", s, re.IGNORECASE):
        return False, "does not start with SELECT/WITH"

    if re.search(r"\bSELEC\b|\bFRM\b|\bWHER\b|\bGROPU\b", s, re.IGNORECASE):
        return False, "misspelled SQL keyword"

    if "SELECT" in s.upper() and "FROM" not in s.upper():
        # SELECT 1, SELECT NOW() etc. are technically valid without FROM,
        # but for this benchmark's schema-backed questions, a SELECT with
        # no FROM at all is almost certainly a mistake, not a deliberate
        # constant-expression query.
        return False, "SELECT with no FROM clause"

    return True, None


def is_destructive(sql):
    return bool(_DESTRUCTIVE_STATEMENT.match(sql.strip()))


# ---------------------------------------------------------------------
# Execution accuracy (optional -- only runs if a DB file is configured)
# ---------------------------------------------------------------------

def execute_sql(conn, sql):
    """Runs sql against conn, returns list[tuple] or raises."""
    cur = conn.cursor()
    cur.execute(sql)
    return cur.fetchall()


def result_sets_match(rows_a, rows_b):
    """Order-insensitive comparison; stringifies cells so type quirks
    (e.g. 1 vs '1') don't cause false mismatches."""
    norm_a = sorted(tuple(str(c) for c in row) for row in rows_a)
    norm_b = sorted(tuple(str(c) for c in row) for row in rows_b)
    return norm_a == norm_b


def try_execution_accuracy(conn, generated_sql, gold_variants):
    """
    Returns one of:
      True   -> generated result set matched at least one gold variant
      False  -> ran fine, but didn't match any gold variant
      None   -> generated SQL raised an execution error (couldn't compare)
    Assumes generated_sql has already been checked as non-destructive.
    """
    try:
        got = execute_sql(conn, generated_sql)
    except Exception:
        return None

    for gold in gold_variants:
        try:
            expected_rows = execute_sql(conn, gold)
        except Exception:
            continue  # a broken gold query shouldn't fail the model
        if result_sets_match(got, expected_rows):
            return True
    return False


# ---------------------------------------------------------------------
# Parsing results/<model>.txt back into structured records
# ---------------------------------------------------------------------

_LATENCY_RE = re.compile(r"Latency\s*:\s*([\d.]+)", re.IGNORECASE)
_PROMPT_TOK_RE = re.compile(r"Prompt Tokens\s*:\s*(\d+)", re.IGNORECASE)
_COMPLETION_TOK_RE = re.compile(r"Completion Tokens\s*:\s*(\d+)", re.IGNORECASE)
_TOTAL_TOK_RE = re.compile(r"Total Tokens\s*:\s*(\d+)", re.IGNORECASE)


def parse_result_file(path):
    """
    Returns {question_id: {"sql": str, "latency": float|None,
                            "prompt_tokens": int|None,
                            "completion_tokens": int|None,
                            "total_tokens": int|None}}

    Latency/token fields are optional: if main.py isn't logging a line like
    "Latency: 1.23" / "Prompt Tokens: 120" / "Completion Tokens: 45" /
    "Total Tokens: 165" inside a question's block, those fields are simply
    None and downstream stats report "N/A" for them.
    """
    text = path.read_text(encoding="utf-8")
    records = {}

    blocks = text.split("-" * 80)
    for block in blocks:
        id_match = re.search(r"Question ID\s*:\s*(\d+)", block)
        if not id_match:
            continue
        qid = int(id_match.group(1))

        sql_match = re.search(r"Generated SQL:\n(.*)", block, re.S)
        sql = sql_match.group(1).strip() if sql_match else ""

        def _num(pattern, cast):
            m = pattern.search(block)
            return cast(m.group(1)) if m else None

        prompt_tok = _num(_PROMPT_TOK_RE, int)
        completion_tok = _num(_COMPLETION_TOK_RE, int)
        total_tok = _num(_TOTAL_TOK_RE, int)
        if total_tok is None and prompt_tok is not None and completion_tok is not None:
            total_tok = prompt_tok + completion_tok

        records[qid] = {
            "sql": sql,
            "latency": _num(_LATENCY_RE, float),
            "prompt_tokens": prompt_tok,
            "completion_tokens": completion_tok,
            "total_tokens": total_tok,
        }

    return records


# ---------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------

def normalize(sql):
    sql = sql.strip().rstrip(";").strip()
    sql = re.sub(r"\s+", " ", sql)
    return sql.lower()


def gold_variants_for(qid):
    """EXPECTED_SQL[qid] may be a single string or a list of acceptable
    gold queries; always returns a list."""
    expected = EXPECTED_SQL[qid]
    if isinstance(expected, (list, tuple)):
        return list(expected)
    return [expected]


def score_question(qid, generated_sql, conn):
    gold_variants = gold_variants_for(qid)
    primary_gold = gold_variants[0]

    # --- Refusal-expected questions ---
    if normalize(primary_gold) == normalize(REFUSAL_TOKEN):
        refused = REFUSAL_TOKEN in generated_sql.upper()
        result = {
            "expected_refusal": True,
            "correctly_refused": refused,
            "similarity": 100.0 if refused else 0.0,
            "exact_match": refused,
            "execution_match": None,
            "syntax_valid": None,
            "destructive": is_destructive(generated_sql) if not refused else False,
            "hallucinations": [] if refused else find_hallucinations(generated_sql, TABLES),
        }
        if refused:
            result["verdict"] = Verdict.CORRECT_REFUSAL
        elif result["destructive"]:
            result["verdict"] = Verdict.UNSAFE_SQL
        else:
            result["verdict"] = Verdict.MISSED_REFUSAL
        return result

    # --- Question with a real expected SQL answer ---
    norm_gen = normalize(generated_sql)
    exact_match = any(norm_gen == normalize(g) for g in gold_variants)
    similarity = max(
        difflib.SequenceMatcher(None, norm_gen, normalize(g)).ratio() * 100
        for g in gold_variants
    )

    was_refusal = REFUSAL_TOKEN in generated_sql.upper()
    syntax_valid, syntax_reason = (None, None) if was_refusal else check_syntax(generated_sql)
    destructive = False if was_refusal else is_destructive(generated_sql)
    hallucinations = [] if (was_refusal or destructive) else find_hallucinations(generated_sql, TABLES)

    execution_match = None
    if conn is not None and not was_refusal and not destructive and syntax_valid:
        execution_match = try_execution_accuracy(conn, generated_sql, gold_variants)

    result = {
        "expected_refusal": False,
        "correctly_refused": None,
        "similarity": round(similarity, 1),
        "exact_match": exact_match,
        "execution_match": execution_match,
        "syntax_valid": syntax_valid,
        "syntax_reason": syntax_reason,
        "destructive": destructive,
        "hallucinations": hallucinations,
    }

    # --- classify ---
    if was_refusal:
        result["verdict"] = Verdict.FALSE_REFUSAL
    elif destructive:
        result["verdict"] = Verdict.UNSAFE_SQL
    elif syntax_valid is False:
        result["verdict"] = Verdict.SYNTAX_ERROR
    elif execution_match is True:
        result["verdict"] = Verdict.CORRECT
    elif execution_match is False:
        result["verdict"] = Verdict.EXECUTION_MISMATCH
    elif execution_match is None and conn is not None:
        result["verdict"] = Verdict.EXECUTION_ERROR
    elif hallucinations:
        result["verdict"] = Verdict.SCHEMA_HALLUCINATION
    elif exact_match:
        result["verdict"] = Verdict.CORRECT
    else:
        result["verdict"] = Verdict.REVIEW

    return result


def composite_score(row):
    """0-100 weighted score for one scored (non-missing) question."""
    correctness = 1.0 if row["verdict"] in (Verdict.CORRECT, Verdict.CORRECT_REFUSAL) else 0.0

    if row["syntax_valid"] is None:
        syntax_component = correctness  # refusal case: no SQL to check
    else:
        syntax_component = 1.0 if row["syntax_valid"] else 0.0

    no_halluc = 0.0 if row["hallucinations"] else 1.0

    latency = row.get("latency")
    latency_component = None if latency is None else 1.0  # presence-only signal by default

    weight_sum = SCORE_WEIGHTS["correctness"] + SCORE_WEIGHTS["syntax"] + SCORE_WEIGHTS["no_hallucination"]
    score = (
        correctness * SCORE_WEIGHTS["correctness"]
        + syntax_component * SCORE_WEIGHTS["syntax"]
        + no_halluc * SCORE_WEIGHTS["no_hallucination"]
    )
    if latency_component is not None:
        score += latency_component * SCORE_WEIGHTS["latency"]
        weight_sum += SCORE_WEIGHTS["latency"]

    return round(100 * score / weight_sum, 1)


# ---------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------

def evaluate_model(model, conn):
    result_file = RESULTS_DIR / f"{safe_filename(model)}.txt"
    if not result_file.exists():
        return None

    text = result_file.read_text(encoding="utf-8")
    if DONE_MARKER not in text:
        print(f"WARNING: {result_file} looks incomplete (no '{DONE_MARKER}' marker) - scoring it anyway")

    generated = parse_result_file(result_file)

    rows = []
    for q in QUESTIONS:
        qid = q["id"]
        record = generated.get(qid)
        if not record or not record["sql"]:
            rows.append({"id": qid, "missing": True})
            continue

        result = score_question(qid, record["sql"], conn)
        result["id"] = qid
        result["missing"] = False
        result["category"] = q["category"]
        result["difficulty"] = q["difficulty"]
        result["latency"] = record["latency"]
        result["prompt_tokens"] = record["prompt_tokens"]
        result["completion_tokens"] = record["completion_tokens"]
        result["total_tokens"] = record["total_tokens"]
        result["score"] = composite_score(result)
        rows.append(result)

    return rows


def _pct(part, whole):
    return round(100 * part / whole, 1) if whole else None


def summarize(rows):
    scored = [r for r in rows if not r["missing"]]
    n = len(scored)
    if n == 0:
        return {"n": 0}

    exact = sum(1 for r in scored if r["exact_match"])
    avg_sim = sum(r["similarity"] for r in scored) / n
    hallucinated_qs = [r for r in scored if r["hallucinations"]]
    refusal_qs = [r for r in scored if r["expected_refusal"]]
    refusal_correct = sum(1 for r in refusal_qs if r["correctly_refused"])
    exec_scored = [r for r in scored if r["execution_match"] is not None]
    exec_correct = sum(1 for r in exec_scored if r["execution_match"])
    unsafe = sum(1 for r in scored if r["destructive"])
    syntax_checked = [r for r in scored if r["syntax_valid"] is not None]
    syntax_ok = sum(1 for r in syntax_checked if r["syntax_valid"])
    avg_score = sum(r["score"] for r in scored) / n

    latencies = [r["latency"] for r in scored if r.get("latency") is not None]
    total_tokens = [r["total_tokens"] for r in scored if r.get("total_tokens") is not None]

    latency_stats = None
    if latencies:
        sorted_lat = sorted(latencies)
        p95_idx = min(len(sorted_lat) - 1, int(round(0.95 * (len(sorted_lat) - 1))))
        latency_stats = {
            "avg": round(sum(latencies) / len(latencies), 3),
            "median": round(statistics.median(latencies), 3),
            "min": round(min(latencies), 3),
            "max": round(max(latencies), 3),
            "p95": round(sorted_lat[p95_idx], 3),
        }

    tokens_per_sec = None
    if latencies and total_tokens and len(latencies) == len(total_tokens):
        total_time = sum(latencies)
        if total_time > 0:
            tokens_per_sec = round(sum(total_tokens) / total_time, 1)

    by_category = {}
    by_difficulty = {}
    for r in scored:
        cat = r["category"]
        diff = r["difficulty"]
        by_category.setdefault(cat, [0, 0])
        by_difficulty.setdefault(diff, [0, 0])
        correct = r["verdict"] in (Verdict.CORRECT, Verdict.CORRECT_REFUSAL)
        by_category[cat][0] += int(correct)
        by_category[cat][1] += 1
        by_difficulty[diff][0] += int(correct)
        by_difficulty[diff][1] += 1

    return {
        "n": n,
        "exact_match_rate": _pct(exact, n),
        "avg_similarity": round(avg_sim, 1),
        "execution_accuracy": _pct(exec_correct, len(exec_scored)) if exec_scored else None,
        "execution_scored_n": len(exec_scored),
        "syntax_valid_rate": _pct(syntax_ok, len(syntax_checked)) if syntax_checked else None,
        "hallucination_count": len(hallucinated_qs),
        "unsafe_sql_count": unsafe,
        "refusal_total": len(refusal_qs),
        "refusal_correct": refusal_correct,
        "avg_score": round(avg_score, 1),
        "latency": latency_stats,
        "tokens_per_sec": tokens_per_sec,
        "category_accuracy": {k: _pct(v[0], v[1]) for k, v in by_category.items()},
        "difficulty_accuracy": {k: _pct(v[0], v[1]) for k, v in by_difficulty.items()},
    }


def write_txt_report(all_rows, all_summaries):
    lines = []
    lines.append("=" * 80)
    lines.append("SQL ACCURACY / HALLUCINATION REPORT")
    lines.append("=" * 80 + "\n")

    for model, rows in all_rows.items():
        lines.append(f"\n{'=' * 80}")
        lines.append(f"MODEL : {model}")
        lines.append(f"{'=' * 80}\n")

        for r in rows:
            if r["missing"]:
                lines.append(f"[Q{r['id']}] MISSING RESULT\n")
                continue

            tag = "REFUSAL" if r["expected_refusal"] else "SQL"
            lines.append(f"[Q{r['id']}] ({r['category']}/{r['difficulty']}, {tag}) -> {r['verdict']}")
            lines.append(f"    score        : {r['score']}/100")
            lines.append(f"    similarity   : {r['similarity']}%")
            lines.append(f"    exact_match  : {r['exact_match']}")
            if r["execution_match"] is not None:
                lines.append(f"    execution_match : {r['execution_match']}")
            if r["syntax_valid"] is False:
                lines.append(f"    syntax_error : {r['syntax_reason']}")
            if r["expected_refusal"]:
                lines.append(f"    correctly_refused : {r['correctly_refused']}")
            if r["destructive"]:
                lines.append("    ** DESTRUCTIVE STATEMENT GENERATED (not executed) **")
            if r.get("latency") is not None:
                lines.append(f"    latency      : {r['latency']}s")
            if r.get("total_tokens") is not None:
                lines.append(f"    total_tokens : {r['total_tokens']}")
            if r["hallucinations"]:
                lines.append("    HALLUCINATION FLAGS:")
                for issue in r["hallucinations"]:
                    lines.append(f"      - {issue}")
            lines.append("")

    lines.append("\n" + "=" * 80)
    lines.append("SUMMARY")
    lines.append("=" * 80 + "\n")
    lines.append(
        f"{'Model':<20}{'Scored':<8}{'Score':<8}{'Exact%':<9}{'ExecAcc%':<10}"
        f"{'Syntax%':<9}{'Halluc.':<9}{'Unsafe':<8}{'Refusals':<10}"
    )
    for model, s in all_summaries.items():
        if s["n"] == 0:
            continue
        exec_acc = "N/A" if s["execution_accuracy"] is None else f"{s['execution_accuracy']}"
        syn = "N/A" if s["syntax_valid_rate"] is None else f"{s['syntax_valid_rate']}"
        lines.append(
            f"{model:<20}{s['n']:<8}{s['avg_score']:<8}{s['exact_match_rate']:<9}{exec_acc:<10}"
            f"{syn:<9}{s['hallucination_count']:<9}{s['unsafe_sql_count']:<8}"
            f"{s['refusal_correct']}/{s['refusal_total']:<7}"
        )

    lines.append("\nCATEGORY ACCURACY (% correct)")
    for model, s in all_summaries.items():
        if s["n"] == 0:
            continue
        lines.append(f"  {model}:")
        for cat, pct in s["category_accuracy"].items():
            lines.append(f"    {cat:<20}{pct}%")

    lines.append("\nDIFFICULTY ACCURACY (% correct)")
    for model, s in all_summaries.items():
        if s["n"] == 0:
            continue
        lines.append(f"  {model}:")
        for diff, pct in s["difficulty_accuracy"].items():
            lines.append(f"    {diff:<20}{pct}%")

    lines.append("\nLATENCY (seconds, only where logged by main.py)")
    for model, s in all_summaries.items():
        if s["n"] == 0 or not s["latency"]:
            lines.append(f"  {model}: N/A (no latency data logged)")
            continue
        lat = s["latency"]
        tps = s["tokens_per_sec"] if s["tokens_per_sec"] is not None else "N/A"
        lines.append(
            f"  {model}: avg={lat['avg']} median={lat['median']} "
            f"min={lat['min']} max={lat['max']} p95={lat['p95']} | tokens/sec={tps}"
        )

    ranking = sorted(
        ((m, s) for m, s in all_summaries.items() if s["n"] > 0),
        key=lambda item: item[1]["avg_score"],
        reverse=True,
    )
    lines.append("\n" + "=" * 80)
    lines.append("RANKING (by weighted score)")
    lines.append("=" * 80)
    for i, (model, s) in enumerate(ranking, start=1):
        lines.append(f"  {i}. {model} -- {s['avg_score']}/100")

    report = "\n".join(lines)
    REPORT_TXT.write_text(report, encoding="utf-8")
    return report


def write_json_report(all_rows, all_summaries):
    payload = {
        "summary": all_summaries,
        "questions": all_rows,
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def write_csv_report(all_rows):
    fieldnames = [
        "model", "question_id", "category", "difficulty", "verdict",
        "score", "similarity", "exact_match", "execution_match",
        "syntax_valid", "destructive", "hallucination_count",
        "latency", "total_tokens", "missing",
    ]
    with REPORT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for model, rows in all_rows.items():
            for r in rows:
                if r["missing"]:
                    writer.writerow({
                        "model": model, "question_id": r["id"], "missing": True,
                    })
                    continue
                writer.writerow({
                    "model": model,
                    "question_id": r["id"],
                    "category": r["category"],
                    "difficulty": r["difficulty"],
                    "verdict": r["verdict"],
                    "score": r["score"],
                    "similarity": r["similarity"],
                    "exact_match": r["exact_match"],
                    "execution_match": r["execution_match"],
                    "syntax_valid": r["syntax_valid"],
                    "destructive": r["destructive"],
                    "hallucination_count": len(r["hallucinations"]),
                    "latency": r.get("latency"),
                    "total_tokens": r.get("total_tokens"),
                    "missing": False,
                })


def main():
    parser = argparse.ArgumentParser(description="Score generated SQL against gold answers.")
    parser.add_argument(
        "--db", default=None,
        help="Path to a SQLite DB matching schema.py. If given, enables execution "
             "accuracy scoring; otherwise falls back to text-match scoring only.",
    )
    args = parser.parse_args()

    conn = None
    if args.db:
        db_path = Path(args.db)
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
        else:
            print(f"WARNING: --db path '{db_path}' does not exist; skipping execution accuracy.")

    all_rows = {}
    all_summaries = {}

    for model in MODELS:
        rows = evaluate_model(model, conn)
        if rows is None:
            print(f"Skipping {model}: no results file found (run main.py first)")
            continue
        all_rows[model] = rows
        all_summaries[model] = summarize(rows)

    if conn is not None:
        conn.close()

    RESULTS_DIR.mkdir(exist_ok=True)
    report = write_txt_report(all_rows, all_summaries)
    write_json_report(all_rows, all_summaries)
    write_csv_report(all_rows)

    print(report)
    print(f"\nSaved to: {REPORT_TXT}")
    print(f"Saved to: {REPORT_JSON}")
    print(f"Saved to: {REPORT_CSV}")


if __name__ == "__main__":
    main()