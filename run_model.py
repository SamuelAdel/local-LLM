"""
run_model.py

Runs a local LLM using Ollama.
"""

import time
import ollama
from config import (
    TEMPERATURE,
    NUM_CTX,
    NUM_GPU,
    SEED,
    TIMEOUT,
    MAX_TOKENS,
)

from prompt import PROMPT_TEMPLATE

import re


def extract_sql(text):
    text = text.strip()

    # remove <think> ... </think>
    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # remove ```sql
    text = re.sub(
        r"```sql",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = text.replace("```", "")

    # find first SELECT or WITH
    match = re.search(
        r"(SELECT\b.*|WITH\b.*)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if match:
        return match.group(1).strip()

    return text.strip()

# One client, reused for every call, with TIMEOUT actually applied
# (previously TIMEOUT was imported but never passed to Ollama).
_client = ollama.Client(timeout=TIMEOUT)


class ModelRunError(Exception):
    """Raised when a model fails to respond (not pulled, crashed, timed out, ...)."""


# Number of attempts for a single question (1 initial try + this many retries).
RETRY_ATTEMPTS = 1


def run_model(model_name, schema, question):
    """
    Send one question to one model. Retries once on failure (transient
    Ollama errors/timeouts are common) before giving up.

    Returns
    -------
    dict with keys:
        sql               : str
        latency           : float (seconds, of the successful attempt only)
        prompt_tokens     : int or None
        completion_tokens : int or None
        raw_response      : str (model output before extract_sql cleanup)
        retries           : int (number of retries that were needed, 0 if
                            the first attempt succeeded)

    Raises
    ------
    ModelRunError
        If Ollama can't reach/run the model after all attempts (not pulled
        locally, server down, request timed out, etc). Callers should catch
        this per-question so one bad model/question doesn't kill the whole
        evaluation run.
    """

    prompt = PROMPT_TEMPLATE.format(
        schema=schema,
        question=question,
    )

    last_exc = None

    for attempt in range(RETRY_ATTEMPTS + 1):
        start = time.perf_counter()
        try:
            response = _client.chat(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                options={
                    "temperature": TEMPERATURE,
                    "num_ctx": NUM_CTX,
                    "num_gpu": NUM_GPU,
                    "seed": SEED,
                    "num_predict": MAX_TOKENS,
                },
            )
        except Exception as exc:
            last_exc = exc
            continue  # try again if attempts remain

        end = time.perf_counter()

        raw = response["message"]["content"]
        sql = extract_sql(raw)

        return {
            "sql": sql,
            "latency": round(end - start, 2),
            "prompt_tokens": response.get("prompt_eval_count"),
            "completion_tokens": response.get("eval_count"),
            "raw_response": raw,
            "retries": attempt,
        }

    # All attempts (initial + retries) failed.
    raise ModelRunError(f"{model_name} failed after {RETRY_ATTEMPTS + 1} attempt(s): {last_exc}") from last_exc