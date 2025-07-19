import os
import tempfile
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_groq import ChatGroq
from chromadb.config import Settings
from langchain_core.documents import Document

# --- Helper: Extract text from PDFs ---
def extract_text_from_pdfs(uploaded_files):
    raw_text = ""
    for file in uploaded_files:
        try:
            pdf_reader = PdfReader(file)
            for page in pdf_reader.pages:
                raw_text += page.extract_text() or ""
        except Exception as e:
            st.error(f"❌ Error reading {file.name}: {e}")
    return raw_text


# --- Cached Vectorstore Initialization ---
@st.cache_resource(show_spinner="🔍 Embedding & indexing PDFs...")
def initialize_vectorstore(docs, persist_path):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    settings = Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=persist_path
    )

    return Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=persist_path,
        client_settings=settings,
        collection_name="pdf_collection"
    )


# --- Main QA Chain Setup ---
def initialize_pdf_qa_chain(pdf_files):
    text = extract_text_from_pdfs(pdf_files)
    if not text.strip():
        st.warning("No readable text found in the uploaded PDFs.")
        return None

    # Split text
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=150)
    chunks = splitter.split_text(text)
    docs = [Document(page_content=c) for c in chunks]

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            vectorstore = initialize_vectorstore(docs, temp_dir)

            retriever = vectorstore.as_retriever(search_type="similarity", k=4)

            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )

            # Load GROQ API Key
            groq_api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
            if not groq_api_key:
                st.error("GROQ API Key not found. Set it in .env or secrets.toml.")
                return None

            llm = ChatGroq(
                api_key=groq_api_key,
                model_name="llama3-8b-8192",
                temperature=0.2
            )

            chain = ConversationalRetrievalChain.from_llm(
                llm=llm,
                retriever=retriever,
                memory=memory,
                return_source_documents=True
            )
            return chain

    except Exception as e:
        st.error(f"❌ Failed to initialize PDF QA chain: {e}")
        return None
def render_pdf_chat():
    st.markdown("## 📚 Ask Questions from Your PDFs")
    uploaded_files = st.file_uploader(
        "📄 Upload PDF file(s)", 
        type=["pdf"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("🔄 Process PDFs"):
            with st.spinner("Processing PDFs... Please wait."):
                chain = initialize_pdf_qa_chain(uploaded_files)
                if chain:
                    st.session_state["pdf_chain"] = chain
                    st.success("✅ PDFs processed. You can now ask questions.")

    if "pdf_chain" in st.session_state:
        query = st.text_input("❓ Ask a question from the PDF(s)", placeholder="e.g., What is the main topic in chapter 2?")

        if query:
            try:
                result = st.session_state["pdf_chain"].invoke({"question": query})
                st.markdown("### 💡 Answer")
                st.success(result["answer"])

                with st.expander("📖 Source Snippets"):
                    for doc in result.get("source_documents", []):
                        content = getattr(doc, "page_content", "")
                        st.markdown(content[:500] + "..." if content else "⚠️ No text in source.")
            except Exception as e:
                st.error(f"❌ Error answering question: {e}")
