"""
main.py

Runs the complete evaluation pipeline.
"""

from pathlib import Path
from datetime import datetime

from models import MODELS
from schema import DATABASE_SCHEMA
from questions import QUESTIONS
from run_model import run_model


RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

RESULT_FILE = RESULTS_DIR / "results.txt"


def save_header(file):

    file.write("=" * 80 + "\n")
    file.write("LOCAL LLM EVALUATION\n")
    file.write(str(datetime.now()) + "\n")
    file.write("=" * 80 + "\n\n")


def main():

    with open(RESULT_FILE, "w", encoding="utf-8") as f:

        save_header(f)

        for model in MODELS:

            print(f"\n{'='*60}")
            print(model)
            print("=" * 60)

            f.write(f"\n{'='*80}\n")
            f.write(f"MODEL : {model}\n")
            f.write(f"{'='*80}\n\n")

            for q in QUESTIONS:

                print(f"[{q['id']}] {q['question']}")

                sql, response_time = run_model(
                    model,
                    DATABASE_SCHEMA,
                    q["question"],
                )

                f.write(f"Question ID : {q['id']}\n")
                f.write(f"Category    : {q['category']}\n")
                f.write(f"Difficulty  : {q['difficulty']}\n")
                f.write(f"Question    : {q['question']}\n")
                f.write(f"Time        : {response_time} sec\n\n")

                f.write("Generated SQL:\n")
                f.write(sql)
                f.write("\n")

                f.write("-" * 80 + "\n")

    print("\nEvaluation Finished.")
    print(f"Results saved to: {RESULT_FILE}")


if __name__ == "__main__":
    main()