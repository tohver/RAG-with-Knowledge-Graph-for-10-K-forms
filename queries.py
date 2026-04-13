"""
queries.py
----------
All Cypher query strings in one place.
Keeping queries out of business logic makes them easy to find,
review, and test independently.
"""

# ── Chunk nodes ────────────────────────────────────────────────────────────

MERGE_CHUNK_NODE = """
MERGE (mergedChunk:Chunk {chunkId: $chunkParam.chunkId})
ON CREATE SET
    mergedChunk.names        = $chunkParam.names,
    mergedChunk.formId       = $chunkParam.formId,
    mergedChunk.cik          = $chunkParam.cik,
    mergedChunk.cusip6       = $chunkParam.cusip6,
    mergedChunk.source       = $chunkParam.source,
    mergedChunk.f10kItem     = $chunkParam.f10kItem,
    mergedChunk.chunkSeqId   = $chunkParam.chunkSeqId,
    mergedChunk.text         = $chunkParam.text
RETURN mergedChunk
"""

CREATE_UNIQUE_CHUNK_CONSTRAINT = """
CREATE CONSTRAINT unique_chunk IF NOT EXISTS
    FOR (c:Chunk) REQUIRE c.chunkId IS UNIQUE
"""

COUNT_ALL_NODES = """
MATCH (n)
RETURN count(n) AS nodeCount
"""

# ── Vector index ───────────────────────────────────────────────────────────

CREATE_VECTOR_INDEX = """
CREATE VECTOR INDEX `form_10k_chunks` IF NOT EXISTS
  FOR (c:Chunk) ON (c.textEmbedding)
  OPTIONS { indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
  }}
"""

GENERATE_EMBEDDINGS = """
MATCH (chunk:Chunk) WHERE chunk.textEmbedding IS NULL
WITH chunk, genai.vector.encode(
    chunk.text,
    "OpenAI",
    { token: $openAiApiKey }
) AS vector
CALL db.create.setNodeVectorProperty(chunk, "textEmbedding", vector)
"""

# ── Form node ──────────────────────────────────────────────────────────────

GET_FORM_INFO_FROM_CHUNK = """
MATCH (anyChunk:Chunk)
WITH anyChunk LIMIT 1
RETURN anyChunk { .names, .source, .formId, .cik, .cusip6 } AS formInfo
"""

MERGE_FORM_NODE = """
MERGE (f:Form {formId: $formInfoParam.formId})
ON CREATE SET
    f.names  = $formInfoParam.names,
    f.source = $formInfoParam.source,
    f.cik    = $formInfoParam.cik,
    f.cusip6 = $formInfoParam.cusip6
"""

COUNT_FORMS = """
MATCH (f:Form) RETURN count(f) AS formCount
"""

# ── Graph relationships ────────────────────────────────────────────────────

LINK_CHUNKS_WITH_NEXT = """
MATCH (from_same_section:Chunk)
WHERE from_same_section.formId   = $formIdParam
  AND from_same_section.f10kItem = $f10kItemParam
WITH from_same_section
    ORDER BY from_same_section.chunkSeqId ASC
WITH collect(from_same_section) AS section_chunk_list
    CALL apoc.nodes.link(
        section_chunk_list,
        "NEXT",
        {avoidDuplicates: true}
    )
RETURN size(section_chunk_list)
"""

LINK_CHUNKS_TO_FORM = """
MATCH (c:Chunk), (f:Form)
WHERE c.formId = f.formId
MERGE (c)-[newRelationship:PART_OF]->(f)
RETURN count(newRelationship)
"""

CREATE_SECTION_RELATIONSHIP = """
MATCH (first:Chunk), (f:Form)
WHERE first.formId = f.formId
  AND first.chunkSeqId = 0
WITH first, f
MERGE (f)-[r:SECTION {f10kItem: first.f10kItem}]->(first)
RETURN count(r)
"""

# ── Vector search ──────────────────────────────────────────────────────────

VECTOR_SEARCH = """
WITH genai.vector.encode(
    $question,
    "OpenAI",
    { token: $openAiApiKey }
) AS question_embedding
CALL db.index.vector.queryNodes($index_name, $top_k, question_embedding)
    YIELD node, score
RETURN score, node.text AS text
"""

# ── Retrieval query (sliding window) ──────────────────────────────────────

RETRIEVAL_QUERY_WINDOW = """
MATCH window=(:Chunk)-[:NEXT*0..1]->(node)-[:NEXT*0..1]->(:Chunk)
WITH node, score, window AS longestWindow
    ORDER BY length(window) DESC LIMIT 1
WITH nodes(longestWindow) AS chunkList, node, score
UNWIND chunkList AS chunkRows
WITH collect(chunkRows.text) AS textList, node, score
RETURN apoc.text.join(textList, " \\n ") AS text,
       score,
       node { .source } AS metadata
"""
