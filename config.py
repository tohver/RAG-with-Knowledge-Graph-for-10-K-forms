"""
config.py
---------
Central configuration: environment loading, constants, and helpers.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def get_env(name: str, default: str | None = None) -> str:
    """Return the value of an environment variable.

    Raises ValueError if the variable is missing and no default is provided.
    """
    value = os.getenv(name, default)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


# ── Neo4j ──────────────────────────────────────────────────────────────────
NEO4J_URI = get_env("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = get_env("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = get_env("NEO4J_PASSWORD", "password")
NEO4J_DATABASE = get_env("NEO4J_DATABASE", "neo4j")

# ── OpenAI ─────────────────────────────────────────────────────────────────
OPENAI_API_KEY = get_env("OPENAI_API_KEY")

# ── Vector index ───────────────────────────────────────────────────────────
VECTOR_INDEX_NAME = "form_10k_chunks"
VECTOR_NODE_LABEL = "Chunk"
VECTOR_SOURCE_PROPERTY = "text"
VECTOR_EMBEDDING_PROPERTY = "textEmbedding"

# ── Form 10-K processing ───────────────────────────────────────────────────
FORM_10K_ITEMS = ["item1", "item1a", "item7", "item7a"]
MAX_CHUNKS_PER_ITEM = 20
