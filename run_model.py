"""
run_model.py

Handles communication with the local Ollama server.
Sends prompts to a selected model and returns the response.
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
