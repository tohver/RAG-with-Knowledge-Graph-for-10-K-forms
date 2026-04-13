"""
graph.py
--------
All Neo4j interactions: connecting to the graph, writing chunk nodes,
creating constraints, building relationships, and generating embeddings.
"""

from langchain_community.graphs import Neo4jGraph

from config import FORM_10K_ITEMS, OPENAI_API_KEY
import queries


def connect_to_kg(uri: str, username: str, password: str, database: str) -> Neo4jGraph:
    """Connect to Neo4j and verify the connection by refreshing the schema.

    Returns:
        A ready-to-use Neo4jGraph instance.
    """
    kg = Neo4jGraph(
        url=uri,
        username=username,
        password=password,
        database=database,
    )
    kg.refresh_schema()
    print("[Neo4j] Connected and schema refreshed.")
    return kg


def merge_chunks(kg: Neo4jGraph, chunks: list[dict]) -> None:
    """Upsert all chunk dicts into Neo4j as :Chunk nodes.

    Uses MERGE so re-running is safe (idempotent).
    """
    print(f"[Neo4j] Merging {len(chunks)} chunk node(s)...")
    for chunk in chunks:
        kg.query(queries.MERGE_CHUNK_NODE, params={"chunkParam": chunk})
    print(f"[Neo4j] {len(chunks)} chunk(s) merged.")


def create_chunk_constraint(kg: Neo4jGraph) -> None:
    """Ensure a uniqueness constraint exists on Chunk.chunkId."""
    kg.query(queries.CREATE_UNIQUE_CHUNK_CONSTRAINT)
    print("[Neo4j] Uniqueness constraint on Chunk.chunkId ensured.")


def count_nodes(kg: Neo4jGraph) -> int:
    """Return the total number of nodes currently in the graph."""
    result = kg.query(queries.COUNT_ALL_NODES)
    return result[0]["nodeCount"]


def create_vector_index(kg: Neo4jGraph) -> None:
    """Create the vector index on Chunk.textEmbedding if it doesn't exist."""
    kg.query(queries.CREATE_VECTOR_INDEX)
    print("[Neo4j] Vector index ensured.")


def generate_embeddings(kg: Neo4jGraph) -> None:
    """Populate textEmbedding for all Chunk nodes that are missing one."""
    print("[Neo4j] Generating embeddings for un-embedded chunks...")
    kg.query(queries.GENERATE_EMBEDDINGS, params={"openAiApiKey": OPENAI_API_KEY})
    print("[Neo4j] Embeddings generated.")


def create_form_node(kg: Neo4jGraph) -> dict:
    """Create (or merge) a :Form node derived from existing Chunk metadata.

    Returns:
        The form info dict used to create the node.
    """
    result = kg.query(queries.GET_FORM_INFO_FROM_CHUNK)
    form_info = result[0]["formInfo"]

    kg.query(queries.MERGE_FORM_NODE, params={"formInfoParam": form_info})

    count = kg.query(queries.COUNT_FORMS)[0]["formCount"]
    print(f"[Neo4j] Form node merged. Total :Form nodes: {count}")
    return form_info


def link_chunks_sequentially(kg: Neo4jGraph, form_id: str) -> None:
    """Add NEXT relationships between consecutive chunks in each section."""
    print("[Neo4j] Linking chunks with NEXT relationships...")
    for item in FORM_10K_ITEMS:
        kg.query(
            queries.LINK_CHUNKS_WITH_NEXT,
            params={"formIdParam": form_id, "f10kItemParam": item},
        )
    print("[Neo4j] NEXT relationships created.")


def link_chunks_to_form(kg: Neo4jGraph) -> None:
    """Connect every :Chunk to its parent :Form via PART_OF."""
    kg.query(queries.LINK_CHUNKS_TO_FORM)
    print("[Neo4j] PART_OF relationships created.")


def create_section_relationships(kg: Neo4jGraph) -> None:
    """Create SECTION relationships from each :Form to the first chunk of each section."""
    kg.query(queries.CREATE_SECTION_RELATIONSHIP)
    print("[Neo4j] SECTION relationships created.")


def build_graph_structure(kg: Neo4jGraph, chunks: list[dict]) -> None:
    """Orchestrate the full graph-building pipeline for a single form.

    Steps:
        1. Merge all chunk nodes.
        2. Ensure uniqueness constraint.
        3. Create vector index.
        4. Generate embeddings.
        5. Create the Form node.
        6. Wire up NEXT, PART_OF, and SECTION relationships.
    """
    merge_chunks(kg, chunks)
    create_chunk_constraint(kg)

    node_count = count_nodes(kg)
    print(f"[Neo4j] Total nodes in graph: {node_count}")

    create_vector_index(kg)
    generate_embeddings(kg)
    kg.refresh_schema()

    form_info = create_form_node(kg)

    link_chunks_sequentially(kg, form_info["formId"])
    link_chunks_to_form(kg)
    create_section_relationships(kg)

    print("[Neo4j] Graph structure complete.")
