"""
main.py

Runs the complete evaluation pipeline.

Each model gets its own results file (results/<model>.txt). If a model
already finished (its file ends with the DONE marker), it is skipped, so
re-running main.py after a crash resumes instead of starting over and
wiping earlier work. If a single question fails (model not pulled, request
timed out, etc), the error is logged for that question only and the run
continues with the next question/model instead of crashing entirely.
"""

from pathlib import Path
from datetime import datetime

from models import MODELS
from schema import DATABASE_SCHEMA
from questions import QUESTIONS
from run_model import run_model, ModelRunError


RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

DONE_MARKER = "STATUS: COMPLETE"


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


def run_one_model(model):
    result_file = RESULTS_DIR / f"{safe_filename(model)}.txt"

    if model_already_done(result_file):
        print(f"Skipping {model} (already completed, see {result_file})")
        return

    print(f"\n{'='*60}")
    print(model)
    print("=" * 60)

    with open(result_file, "w", encoding="utf-8") as f:
        save_header(f, model)

        for q in QUESTIONS:
            print(f"[{q['id']}] {q['question']}")

            f.write(f"Question ID : {q['id']}\n")
            f.write(f"Category    : {q['category']}\n")
            f.write(f"Difficulty  : {q['difficulty']}\n")
            f.write(f"Question    : {q['question']}\n")

            try:
                sql, response_time = run_model(
                    model,
                    DATABASE_SCHEMA,
                    q["question"],
                )
                f.write(f"Time        : {response_time} sec\n\n")
                f.write("Generated SQL:\n")
                f.write(sql)
                f.write("\n")

            except ModelRunError as exc:
                print(f"  ERROR: {exc}")
                f.write("Time        : N/A\n\n")
                f.write("Generated SQL:\n")
                f.write(f"ERROR: {exc}\n")

            f.write("-" * 80 + "\n")
            f.flush()

        f.write(f"\n{DONE_MARKER}\n")

    print(f"Saved results to: {result_file}")


def main():
    for model in MODELS:
        run_one_model(model)

    print("\nEvaluation Finished.")
    print(f"Per-model results saved under: {RESULTS_DIR}/")


if __name__ == "__main__":
    main()