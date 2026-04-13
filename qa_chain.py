"""
qa_chain.py
-----------
Constructs LangChain RetrievalQA chains and provides a helper for
printing answers in a readable format.
"""

import textwrap

from langchain_community.vectorstores import Neo4jVector
from langchain_classic.chains import RetrievalQAWithSourcesChain
from langchain_openai import ChatOpenAI


def build_qa_chain(vector_store: Neo4jVector, temperature: float = 0) -> RetrievalQAWithSourcesChain:
    """Build a RetrievalQAWithSourcesChain from a Neo4jVector store.

    Args:
        vector_store: Any Neo4jVector instance (windowless or window).
        temperature:  Sampling temperature for the underlying LLM.

    Returns:
        A ready-to-call RetrievalQAWithSourcesChain.
    """
    retriever = vector_store.as_retriever()
    return RetrievalQAWithSourcesChain.from_chain_type(
        ChatOpenAI(temperature=temperature),
        chain_type="stuff",
        retriever=retriever,
    )


def ask(chain: RetrievalQAWithSourcesChain, question: str, line_width: int = 80) -> str:
    """Run a question through a QA chain and pretty-print the answer.

    Args:
        chain:      The QA chain to query.
        question:   The natural-language question.
        line_width: Column width used for wrapping the printed output.

    Returns:
        The raw answer string (also printed to stdout).
    """
    response = chain({"question": question}, return_only_outputs=True)
    answer = response.get("answer", "")
    print(textwrap.fill(answer, line_width))
    return answer
