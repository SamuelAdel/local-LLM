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

# One client, reused for every call, with TIMEOUT actually applied
# (previously TIMEOUT was imported but never passed to Ollama).
_client = ollama.Client(timeout=TIMEOUT)


class ModelRunError(Exception):
    """Raised when a model fails to respond (not pulled, crashed, timed out, ...)."""


def run_model(model_name, schema, question):
    """
    Send one question to one model.

    Returns
    -------
    sql : str
    response_time : float

    Raises
    ------
    ModelRunError
        If Ollama can't reach/run the model (not pulled locally, server down,
        request timed out, etc). Callers should catch this per-question so
        one bad model/question doesn't kill the whole evaluation run.
    """

    prompt = PROMPT_TEMPLATE.format(
        schema=schema,
        question=question,
    )

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
        raise ModelRunError(f"{model_name} failed: {exc}") from exc

    end = time.perf_counter()

    sql = response["message"]["content"].strip()

    return sql, round(end - start, 2)