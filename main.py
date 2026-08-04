"""
main.py

Runs the complete evaluation pipeline.

Each model gets its own results file (results/<model>.txt). If a model
already finished (its file ends with the DONE marker), it is skipped, so
re-running main.py after a crash resumes instead of starting over and
wiping earlier work.

Resume is now question-level: if a run stops partway through a model
(e.g. after question 18/24), re-running main.py picks up at question 19
instead of redoing the whole model from scratch. Any partially-written
question at the point of the crash (header written but no result yet) is
discarded and re-run, so the results file never ends up with a broken
entry.

If a single question fails (model not pulled, request timed out, etc), the
error is logged for that question only and the run continues with the next
question/model instead of crashing entirely. Each question gets one retry
before being logged as a failure (see run_model.RETRY_ATTEMPTS).

Raw model output (before SQL-extraction cleanup) is saved per-question
under results/raw/<model>/<question_id>.txt, useful for debugging why a
question came back as a SYNTAX_ERROR in evaluate.py.

A run-level log is kept at logs/run.log with start/end times, retries,
and failures, useful when running many models unattended.
"""

import logging
import re
from pathlib import Path
from datetime import datetime

from models import MODELS
from schema import DATABASE_SCHEMA
from questions import QUESTIONS
from run_model import run_model, ModelRunError


RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

RAW_DIR = RESULTS_DIR / "raw"
RAW_DIR.mkdir(exist_ok=True)

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

DONE_MARKER = "STATUS: COMPLETE"
SEPARATOR = "-" * 80 + "\n"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "run.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("main")


def safe_filename(model_name):
    """qwen2.5-coder:7b -> qwen2.5-coder_7b"""
    return model_name.replace(":", "_").replace("/", "_")


def model_already_done(result_file):
    if not result_file.exists():
        return False
    return DONE_MARKER in result_file.read_text(encoding="utf-8")


def save_header(file, model):
    file.write("=" * 80 + "\n")
    file.write("LOCAL LLM EVALUATION\n")
    file.write(f"MODEL : {model}\n")
    file.write(str(datetime.now()) + "\n")
    file.write("=" * 80 + "\n\n")


def completed_question_ids(text):
    """
    Question IDs that have a fully-written entry (header line through the
    trailing separator) in an existing, not-yet-finished results file.
    A question whose header was written but crashed before the trailing
    separator is NOT counted as complete, so it gets re-run.
    """
    completed = set()
    for block in text.split(SEPARATOR):
        m = re.search(r"Question ID\s*:\s*(\S+)", block)
        if m:
            completed.add(m.group(1))
    return completed


def truncate_to_last_complete_entry(result_file, text):
    """
    Drop any trailing partial question entry (header written, no result
    yet) so appending new entries can't corrupt the file. Returns the
    (possibly) truncated text.
    """
    last_sep = text.rfind(SEPARATOR)
    if last_sep == -1:
        # No complete entry yet at all -- keep just the header.
        header_end = text.find("\n\n")
        clean = text[: header_end + 2] if header_end != -1 else text
    else:
        clean = text[: last_sep + len(SEPARATOR)]

    if clean != text:
        result_file.write_text(clean, encoding="utf-8")
    return clean


def run_one_model(model):
    result_file = RESULTS_DIR / f"{safe_filename(model)}.txt"
    model_raw_dir = RAW_DIR / safe_filename(model)
    model_raw_dir.mkdir(parents=True, exist_ok=True)

    if model_already_done(result_file):
        print(f"Skipping {model} (already completed, see {result_file})")
        log.info(f"{model}: skipped, already complete")
        return

    already_done_ids = set()
    mode = "w"
    if result_file.exists():
        text = truncate_to_last_complete_entry(result_file, result_file.read_text(encoding="utf-8"))
        already_done_ids = completed_question_ids(text)
        if already_done_ids:
            mode = "a"
            print(f"Resuming {model}: {len(already_done_ids)}/{len(QUESTIONS)} questions already done")
            log.info(f"{model}: resuming, {len(already_done_ids)} questions already complete")

    print(f"\n{'='*60}")
    print(model)
    print("=" * 60)
    log.info(f"{model}: run started")

    remaining = [q for q in QUESTIONS if q["id"] not in already_done_ids]
    total = len(QUESTIONS)
    model_start = datetime.now()
    latencies = []

    with open(result_file, mode, encoding="utf-8") as f:
        if mode == "w":
            save_header(f, model)

        for q in remaining:
            index = QUESTIONS.index(q) + 1
            print(f"[{index}/{total}] {q['question']}")

            f.write(f"Question ID : {q['id']}\n")
            f.write(f"Category    : {q['category']}\n")
            f.write(f"Difficulty  : {q['difficulty']}\n")
            f.write(f"Question    : {q['question']}\n")

            try:
                result = run_model(
                    model,
                    DATABASE_SCHEMA,
                    q["question"],
                )
                sql = result["sql"]

                response_time = result["latency"]
                latencies.append(response_time)
                f.write(f"Time : {response_time} sec\n")

                f.write(f"Prompt Tokens : {result['prompt_tokens']}\n")
                f.write(f"Completion Tokens : {result['completion_tokens']}\n")
                f.write("Generated SQL:\n")
                f.write(sql)
                f.write("\n")

                if result.get("retries"):
                    log.warning(f"{model} [{q['id']}]: needed {result['retries']} retry(ies)")

                raw_path = model_raw_dir / f"{q['id']}.txt"
                raw_path.write_text(result.get("raw_response", ""), encoding="utf-8")

            except ModelRunError as exc:
                print(f"  ERROR: {exc}")
                log.error(f"{model} [{q['id']}]: {exc}")
                f.write("Time        : N/A\n\n")
                f.write("Generated SQL:\n")
                f.write(f"ERROR: {exc}\n")

            f.write(SEPARATOR)
            f.flush()

        f.write(f"\n{DONE_MARKER}\n")

    elapsed = (datetime.now() - model_start).total_seconds()
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else None
    print(f"Completed {model}")
    print(f"  Questions run this session : {len(remaining)}")
    print(f"  Total Runtime              : {round(elapsed, 1)} sec")
    if avg_latency is not None:
        print(f"  Average Latency            : {avg_latency} sec")
    print(f"Saved results to: {result_file}")
    log.info(
        f"{model}: run finished, {len(remaining)} questions this session, "
        f"{round(elapsed, 1)}s elapsed, avg_latency={avg_latency}"
    )


def main():
    log.info("=== Evaluation run started ===")
    for model in MODELS:
        run_one_model(model)

    print("\nEvaluation Finished.")
    print(f"Per-model results saved under: {RESULTS_DIR}/")
    log.info("=== Evaluation run finished ===")


if __name__ == "__main__":
    main()