import streamlit as st

from config import NEO4J_DATABASE, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USERNAME
from graph import connect_to_kg
from qa_chain import build_qa_chain
from vector_store import build_window_vector_store


@st.cache_resource
def get_qa_chain():
    kg = connect_to_kg(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE)
    vector_store = build_window_vector_store(
        uri=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
    )
    return build_qa_chain(vector_store)


st.set_page_config(page_title="SEC 10-K Q&A", layout="wide")
st.title("SEC 10-K Question Answering")
st.write(
    "Enter a natural-language question and the app will answer from the ingested "
    "10-K document stored in Neo4j."
)

question = st.text_input("Ask a question", value="What is this company’s primary business?")

if st.button("Ask") and question:
    with st.spinner("Retrieving answer..."):
        chain = get_qa_chain()
        response = chain({"question": question}, return_only_outputs=False)

    answer = response.get("answer", "No answer returned.")
    sources = response.get("sources")

    st.subheader("Answer")
    st.write(answer)

    if sources:
        st.subheader("Sources")
        st.write(sources)

    st.write("---")
    st.write("If the answer is missing detail, please rephrase your question or ask for a specific section.")
