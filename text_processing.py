"""
text_processing.py
------------------
Responsible for reading raw Form 10-K JSON files and splitting
their text into overlapping chunks with metadata attached.
"""

import json
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import FORM_10K_ITEMS, MAX_CHUNKS_PER_ITEM

# One shared splitter instance — tweak chunk_size / overlap here.
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200,
    length_function=len,
    is_separator_regex=False,
)


def split_form10k_data_from_file(filepath: str) -> list[dict]:
    """Parse a Form 10-K JSON file and return a list of chunk records.

    Each record contains the chunk text plus all relevant metadata
    (form ID, section name, sequence number, company identifiers, etc.).

    Args:
        filepath: Path to the JSON file, e.g. './forms/0001564708-23-000368.json'.

    Returns:
        A flat list of chunk dicts ready to be written to Neo4j.
    """
    path = Path(filepath)
    form_id = path.stem  # filename without extension

    with path.open() as fh:
        form_data = json.load(fh)

    chunks: list[dict] = []

    for item in FORM_10K_ITEMS:
        item_text = form_data.get(item, "")
        if not item_text:
            print(f"  [skip] {item} is empty in {path.name}")
            continue

        item_chunks = text_splitter.split_text(item_text)[:MAX_CHUNKS_PER_ITEM]
        print(f"  {item}: split into {len(item_chunks)} chunk(s)")

        for seq_id, chunk_text in enumerate(item_chunks):
            chunks.append({
                "text": chunk_text,
                "f10kItem": item,
                "chunkSeqId": seq_id,
                "formId": form_id,
                "chunkId": f"{form_id}-{item}-chunk{seq_id:04d}",
                "names": form_data["names"],
                "cik": form_data["cik"],
                "cusip6": form_data["cusip6"],
                "source": form_data["source"],
            })

    print(f"Total chunks produced: {len(chunks)}")
    return chunks
