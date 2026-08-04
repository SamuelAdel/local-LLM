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


def run_model(model_name, schema, question):
    """
    Send one question to one model.

    Returns
    -------
    sql : str
    response_time : float
    """

    prompt = PROMPT_TEMPLATE.format(
        schema=schema,
        question=question,
    )

    start = time.perf_counter()

    response = ollama.chat(
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

    end = time.perf_counter()

    sql = response["message"]["content"].strip()

    return sql, round(end - start, 2)