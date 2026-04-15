"""
main.py
-------
Pipeline entry point for the SEC 10-K Neo4j + LangChain project.
"""

from config import (
    FORM13_FILE,
    FORM_FILE,
    NEO4J_DATABASE,
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USERNAME,
)
from form13 import load_form13_rows, enrich_graph_with_form13
from graph import build_graph_structure, connect_to_kg
from qa_chain import ask, build_qa_chain
from text_processing import split_form10k_data_from_file
from vector_store import build_window_vector_store

QUESTION = "In a single sentence, tell me about the company's primary business."


def main() -> int:
    try:
        kg = connect_to_kg(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE)

        print(f"\nProcessing 10-K file: {FORM_FILE}")
        chunks = split_form10k_data_from_file(FORM_FILE)
        build_graph_structure(kg, chunks)

        print("\nLoading Form 13 data...")
        form13_rows = load_form13_rows(FORM13_FILE)
        enrich_graph_with_form13(kg, form13_rows)

        vector_store = build_window_vector_store(
            uri=NEO4J_URI,
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD,
            database=NEO4J_DATABASE,
        )
        chain = build_qa_chain(vector_store)

        print("\nAsking a sample question:")
        ask(chain, QUESTION)

        return 0
    except Exception as exc:
        print("\n" + "=" * 60)
        print("REAL ERROR DETECTED:")
        print(str(exc))
        print("=" * 60)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
