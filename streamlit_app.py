import hashlib
import os
import streamlit as st
from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIError,
    AuthenticationError,
    NotFoundError,
    OpenAI,
    RateLimitError,
)
import chromadb

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("groq_api_key")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

base_dir = os.path.dirname(__file__)
Data_Folder = os.path.join(base_dir, "Data")
Chroma_Folder = os.path.join(base_dir, ".chroma_db")
if not os.path.exists(Data_Folder):
    Data_Folder = os.path.join(base_dir, "data")


st.set_page_config(
    page_title="NovaTech Assistant",
    page_icon="🤖",
    layout="centered"
)

st.title("NovaTech Internal Assistant")
st.caption("Ask questions about NovaTech's internal documentation and get answers in real-time.")
st.divider()



##
#   RAG SETUP
##

@st.cache_resource
def load_rag():
    """
    Read all .txt files from _data/, chunk by paragraph, and index in ChromaDB.

    @st.cahche_resource decorator:
        - Runs this function ONCE when the app first loads
        - Caches the return value in memory
        - Returns the cached value on all subsequent Streamlit re-runs
        - Without this, load_rag() would re-run on EVERY user message,
        re-indexing 120 chunks each time - extremely slow

    ChromaDB semantic search:
        When you call collection.query(query_texts=["WFH policy"]):
        1. ChromaDB converts "WFH policy" to a 384-dimensional vector
           using the all-MiniLM-L6-v2 sentence transformer model
        2. It computes cosine similarity between that vector and all
           stored chunk vectors
        3. Returns the top N chunks with the smallest angular distance
        This finds semantically similar chunks even if they use different
        words - e.g. "remote work" would match a "work from home" query.

    Returns:
        collection  : ChromaDB collection (ready to query)
        client      : Groq API client
        chunk_id    : total number of chunks indexed (for display)

    """

    if not os.path.exists(Data_Folder):
        st.error(f"Data folder not found: {Data_Folder}")
        st.stop()

    if not GROQ_API_KEY:
        st.error("Missing GROQ_API_KEY. Add it to your .env file or environment variables.")
        st.stop()

    client = OpenAI(
        api_key=GROQ_API_KEY,
        base_url="https://api.groq.com/openai/v1",
    )

    all_chunks = []
    all_ids = []
    all_metadatas = []
    chunk_id = 0

    for filename in sorted(os.listdir(Data_Folder)):
        if not filename.endswith(".txt"):
            continue

        with open(os.path.join(Data_Folder, filename), "r", encoding="utf-8") as f:
            text = f.read()

        for para in text.strip().split("\n\n"):
            para = para.strip()

            if len(para) < 50:
                continue

            if para.startswith("==="):
                continue

            all_chunks.append(para)
            all_ids.append(f"chunk_{chunk_id}")
            all_metadatas.append({"source": filename, "text": para})
            chunk_id += 1

    # Use a content-addressed collection name. A Streamlit code reload can keep
    # an older cached Collection alive briefly, so deleting and recreating a
    # fixed-name collection can leave that object pointing at removed tables.
    index_content = "\0".join(
        f"{metadata['source']}\0{document}"
        for document, metadata in zip(all_chunks, all_metadatas)
    )
    index_hash = hashlib.sha256(index_content.encode("utf-8")).hexdigest()[:16]

    # A persistent client keeps Chroma's SQLite schema alive across Streamlit
    # reruns and hot reloads. EphemeralClient can leave cached Collection
    # objects pointing at an in-memory database that has already been reset.
    chroma = chromadb.PersistentClient(path=Chroma_Folder)
    collection = chroma.get_or_create_collection(f"novatech_docs_{index_hash}")

    if all_chunks and collection.count() == 0:
        collection.add(
            documents=all_chunks,
            metadatas=all_metadatas,
            ids=all_ids,
        )

    return collection, client, chunk_id


with st.spinner("Loading internal documentation..."):
    collection, client, total_chunks = load_rag()

st.success(f"Ready - {total_chunks} document chunks indexed.", icon="✅")
st.divider()

#
# CHAT History
#


if "messages" not in st.session_state:
    st.session_state.messages = []

#
# RAG FUNCTION
#

def ask_rag(question: str) -> dict:
    """
    Execute the full RAG pipeline: retrieve - augment - generate.

    Args:
        question (str) : the user's natural language question

    Returns:
        dict with keys:
            "answer" : str - the LLM-generated answer
            "sources" : list [str] - deduplicated source filenames
            "chunks" : list[tuple] - [(chunk_text, source_file), ... ]

    Retrieve:
        ChromaDB.query() finds the 3 most semantically similar chunks.
        It uses the same embedding model that was used to index the documents,
        so the question and chunk vectors are in the same vector space.
    
    Augment:
        The 3 chunks are concatenated (separated by " --- ") and injected
        into the prompt as "Context". The system message instructs the LLM
        to answer ONLY from this context - not from its training data.
        This is what makes it a RAG system rather than a plain chatbot.

    Generate:
        Groq runs LLaMA 3.3 70B with temperature=0.2.
        Low temperature = more deterministic, factual answers.
        High temperature (0.8+) = more creative but less accurate.
        
    """

    results = collection.query(
        query_texts=[question],
        n_results=3)

    chunks = results["documents"][0]
    sources = [m["source"] for m in results["metadatas"][0]]

    context = "\n\n---\n\n".join(chunks)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that answers questions about NovaTech's internal documentation. "
                "Answer ONLY from the provided context. "
                "If the answer is not in the context, say "
                "\"I don't have enough information to answer that question.\" "
                "Be concise and factual, and do not make up answers."
            )
        },
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion:   {question}"
        }
    ]    


        # Call Groq LLM

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.2,
        )
        answer = response.choices[0].message.content
    except APIConnectionError:
        answer = (
            "I couldn't connect to the language model service. "
            "Please check the network connection and try again."
        )
    except AuthenticationError:
        answer = "The Groq API key was rejected. Please check GROQ_API_KEY."
    except RateLimitError:
        answer = "The language model service is rate-limited. Please try again shortly."
    except NotFoundError:
        answer = (
            f"The configured language model ({GROQ_MODEL}) is unavailable. "
            "Set GROQ_MODEL to a model enabled for this Groq account."
        )
    except APIError:
        answer = "The language model service returned an error. Please try again shortly."

    return {
        "answer": answer,
        "sources": list(set(sources)),
        "chunks": list(zip(chunks, sources))
    }


#
# Render Chat History
#

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if msg["role"] == "assistant" and msg.get("sources"):

            st.caption(f"Sources: {', '.join(msg['sources'])}")


            with st.expander("Show retrieved document chunks"):
                for i, (chunk_text, source_file) in enumerate(msg["chunks"], 1):
                    st.markdown(f"**Chunk {i} - `{source_file}`**")
                    st.info(chunk_text)
                    st.divider()


#
# CHAT INPUT
#

question = st.chat_input("Ask a question about NovaTech's internal documentation...")

if question:

    with st.chat_message("user"):
        st.markdown(question)

    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("assistant"):
        with st.spinner("Generating answer..."):
            result = ask_rag(question)

        st.markdown(result["answer"])

        st.caption(f"Sources: {', '.join(result['sources'])}")

        with st.expander("Show retrieved document chunks"):
            for i, (chunk_text, source_file) in enumerate(result["chunks"], 1):
                st.markdown(f"**Chunk {i} - `{source_file}`**")
                st.info(chunk_text)
                st.divider()


    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
        "chunks": result["chunks"]
    })
