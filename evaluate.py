"""
evaluate.py

Scores each model's generated SQL (results/<model>.txt) against the
reference answers in expected_sql.py, and flags likely hallucinations
(tables/columns referenced that don't exist in schema.py).

This is intentionally a lightweight, regex-based checker -- not a real SQL
parser -- so treat "hallucination" flags and similarity scores as strong
hints for a human reviewer, not a final verdict. Exact-match / refusal
checks are reliable; alias.column hallucination checks are best-effort.

Usage:
    python evaluate.py
"""

import re
import difflib
from pathlib import Path

from models import MODELS
from schema import DATABASE_SCHEMA
from questions import QUESTIONS
from expected_sql import EXPECTED_SQL
from main import safe_filename, DONE_MARKER

RESULTS_DIR = Path("results")
REPORT_FILE = RESULTS_DIR / "evaluation.txt"

REFUSAL_TOKEN = "CANNOT_GENERATE_SQL"


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
# Parsing results/<model>.txt back into structured records
# ---------------------------------------------------------------------

def parse_result_file(path):
    """Returns {question_id: generated_sql_str}."""
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
        records[qid] = sql

    return records


# ---------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------

def normalize(sql):
    sql = sql.strip().rstrip(";").strip()
    sql = re.sub(r"\s+", " ", sql)
    return sql.lower()


def score_question(qid, generated_sql):
    expected = EXPECTED_SQL[qid]

    if normalize(expected) == normalize(REFUSAL_TOKEN):
        refused = REFUSAL_TOKEN in generated_sql.upper()
        return {
            "expected_refusal": True,
            "correctly_refused": refused,
            "similarity": 100.0 if refused else 0.0,
            "exact_match": refused,
            "hallucinations": [] if refused else find_hallucinations(generated_sql, TABLES),
        }

    norm_gen = normalize(generated_sql)
    norm_exp = normalize(expected)
    similarity = difflib.SequenceMatcher(None, norm_gen, norm_exp).ratio() * 100

    return {
        "expected_refusal": False,
        "correctly_refused": None,
        "similarity": round(similarity, 1),
        "exact_match": norm_gen == norm_exp,
        "hallucinations": find_hallucinations(generated_sql, TABLES),
    }


# ---------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------

def evaluate_model(model):
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
        sql = generated.get(qid, "")
        if not sql:
            rows.append({"id": qid, "missing": True})
            continue

        result = score_question(qid, sql)
        result["id"] = qid
        result["missing"] = False
        result["category"] = q["category"]
        result["difficulty"] = q["difficulty"]
        rows.append(result)

    return rows


def summarize(model, rows):
    scored = [r for r in rows if not r["missing"]]
    n = len(scored)
    if n == 0:
        return {"n": 0}

    exact = sum(1 for r in scored if r["exact_match"])
    avg_sim = sum(r["similarity"] for r in scored) / n
    hallucinated_qs = [r for r in scored if r["hallucinations"]]
    refusal_qs = [r for r in scored if r["expected_refusal"]]
    refusal_correct = sum(1 for r in refusal_qs if r["correctly_refused"])

    return {
        "n": n,
        "exact_match_rate": round(100 * exact / n, 1),
        "avg_similarity": round(avg_sim, 1),
        "hallucination_count": len(hallucinated_qs),
        "refusal_total": len(refusal_qs),
        "refusal_correct": refusal_correct,
    }


def main():
    lines = []
    lines.append("=" * 80)
    lines.append("SQL ACCURACY / HALLUCINATION REPORT")
    lines.append("=" * 80 + "\n")

    summary_table = []

    for model in MODELS:
        rows = evaluate_model(model)
        if rows is None:
            print(f"Skipping {model}: no results file found (run main.py first)")
            continue

        summary = summarize(model, rows)
        summary_table.append((model, summary))

        lines.append(f"\n{'=' * 80}")
        lines.append(f"MODEL : {model}")
        lines.append(f"{'=' * 80}\n")

        for r in rows:
            if r["missing"]:
                lines.append(f"[Q{r['id']}] MISSING RESULT\n")
                continue

            tag = "REFUSAL" if r["expected_refusal"] else "SQL"
            status = "OK" if r["exact_match"] or (r["expected_refusal"] and r["correctly_refused"]) else "REVIEW"

            lines.append(f"[Q{r['id']}] ({r['category']}/{r['difficulty']}, {tag}) -> {status}")
            lines.append(f"    similarity   : {r['similarity']}%")
            lines.append(f"    exact_match  : {r['exact_match']}")
            if r["expected_refusal"]:
                lines.append(f"    correctly_refused : {r['correctly_refused']}")
            if r["hallucinations"]:
                lines.append("    HALLUCINATION FLAGS:")
                for issue in r["hallucinations"]:
                    lines.append(f"      - {issue}")
            lines.append("")

    lines.append("\n" + "=" * 80)
    lines.append("SUMMARY")
    lines.append("=" * 80 + "\n")
    lines.append(
        f"{'Model':<22}{'Scored':<8}{'ExactMatch%':<13}{'AvgSim%':<10}{'Halluc.':<9}{'Refusals':<10}"
    )
    for model, s in summary_table:
        if s["n"] == 0:
            continue
        lines.append(
            f"{model:<22}{s['n']:<8}{s['exact_match_rate']:<13}{s['avg_similarity']:<10}"
            f"{s['hallucination_count']:<9}{s['refusal_correct']}/{s['refusal_total']:<7}"
        )

    report = "\n".join(lines)
    RESULTS_DIR.mkdir(exist_ok=True)
    REPORT_FILE.write_text(report, encoding="utf-8")

    print(report)
    print(f"\nSaved to: {REPORT_FILE}")


if __name__ == "__main__":
    main()
