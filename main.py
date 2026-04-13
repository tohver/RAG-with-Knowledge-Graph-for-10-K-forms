"""
main.py
-------
Top-level pipeline.  Imports from all other modules and wires them together.
Keep this file thin — business logic belongs in the specialist modules.
"""

import warnings
warnings.filterwarnings("ignore")

from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE
from graph import connect_to_kg, build_graph_structure
from text_processing import split_form10k_data_from_file
from vector_store import build_window_vector_store
from qa_chain import build_qa_chain, ask


FORM_FILE = "./forms/0001564708-23-000368.json"
QUESTION = "In a single sentence, tell me about the company's primary business."


def main() -> int:
    try:
        # 1. Connect to the knowledge graph
        kg = connect_to_kg(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE)

        # 2. Parse the 10-K file into chunks
        print(f"\nProcessing: {FORM_FILE}")
        chunks = split_form10k_data_from_file(FORM_FILE)

        # 3. Build the full graph (nodes → index → embeddings → relationships)
        print("\nBuilding graph structure...")
        build_graph_structure(kg, chunks)

        # 4. Set up a sliding-window vector store + QA chain
        print("\nSetting up QA chain...")
        vector_store = build_window_vector_store(
            uri=NEO4J_URI,
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD,
            database=NEO4J_DATABASE,
        )
        chain = build_qa_chain(vector_store)

        # 5. Ask a question
        print(f"\nQuestion: {QUESTION}\n")
        ask(chain, QUESTION)

        return 0

    except Exception as exc:
        print(f"\nExecution failed:\n{exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
