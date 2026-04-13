"""
vector_store.py
---------------
Creates Neo4jVector retriever instances backed by the existing Neo4j
vector index.  Two flavours are provided:

  • windowless  – each retrieved chunk stands alone.
  • window      – each chunk is expanded by its immediate NEXT neighbours,
                  giving the LLM a wider reading context.
"""

from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings

from config import (
    VECTOR_EMBEDDING_PROPERTY,
    VECTOR_INDEX_NAME,
    VECTOR_NODE_LABEL,
    VECTOR_SOURCE_PROPERTY,
)
from queries import RETRIEVAL_QUERY_WINDOW


def _embeddings() -> OpenAIEmbeddings:
    """Return a shared OpenAIEmbeddings instance."""
    return OpenAIEmbeddings()


def build_windowless_vector_store(
    uri: str,
    username: str,
    password: str,
    database: str = "neo4j",
) -> Neo4jVector:
    """Connect to the existing graph index without any context window expansion."""
    return Neo4jVector.from_existing_graph(
        embedding=_embeddings(),
        url=uri,
        username=username,
        password=password,
        index_name=VECTOR_INDEX_NAME,
        node_label=VECTOR_NODE_LABEL,
        text_node_properties=[VECTOR_SOURCE_PROPERTY],
        embedding_node_property=VECTOR_EMBEDDING_PROPERTY,
    )


def build_window_vector_store(
    uri: str,
    username: str,
    password: str,
    database: str = "neo4j",
) -> Neo4jVector:
    """Connect to the existing index with a sliding ±1 chunk context window.

    The custom retrieval query expands each matched chunk to include its
    immediate neighbours (via NEXT relationships), giving the model more
    surrounding context per retrieval hit.
    """
    return Neo4jVector.from_existing_index(
        embedding=_embeddings(),
        url=uri,
        username=username,
        password=password,
        database=database,
        index_name=VECTOR_INDEX_NAME,
        text_node_property=VECTOR_SOURCE_PROPERTY,
        retrieval_query=RETRIEVAL_QUERY_WINDOW,
    )
