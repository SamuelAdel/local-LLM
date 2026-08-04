"""
config.py

Stores the global configuration used during model evaluation.
Modify the values here instead of changing them across multiple files.
"""

# ==========================
# Generation Settings
# ==========================

# Controls response randomness (0 = deterministic)
TEMPERATURE = 0

# Maximum context size
NUM_CTX = 4096

# Use all available GPU layers
NUM_GPU = -1

# Fixed seed for reproducibility
SEED = 42

# Request timeout (seconds)
TIMEOUT = 300

# Maximum generated tokens
MAX_TOKENS = 512