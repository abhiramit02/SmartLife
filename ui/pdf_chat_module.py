# 📁 ui/pdf_chat_module.py

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
from langchain_core.documents import Document

# --- Extract Text from Uploaded PDFs ---
def extract_text_from_pdfs(uploaded_files):
    raw_text = ""
    for file in uploaded_files:
        try:
            pdf_reader = PdfReader(file)
            for page in pdf_reader.pages:
                raw_text += page.extract_text() or ""
        except Exception as e:
            st.error(f"Error reading {file.name}: {e}")
    return raw_text

# --- Set Up Conversational Retrieval Chain ---
def initialize_pdf_qa_chain(pdf_files):
    text = extract_text_from_pdfs(pdf_files)
    if not text.strip():
        st.warning("No readable text found in the uploaded PDFs.")
        return None

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=150)
    docs = splitter.create_documents([text])

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            vectorstore = Chroma.from_documents(docs, embeddings, persist_directory=temp_dir)
            retriever = vectorstore.as_retriever(search_type="similarity", k=4)

            memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"
            )

            # Load GROQ API Key from Streamlit secrets or environment
            groq_api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
            if not groq_api_key:
                st.error("GROQ API Key not found. Please set it in `.env` or `secrets.toml`.")
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
        st.error(f"Failed to initialize PDF QA chain: {e}")
        return None

# --- Streamlit UI Component ---
def render_pdf_chat():
    st.markdown("## 📚 Ask Questions from Your PDFs")
    st.markdown("Upload one or more PDF files and ask anything about their content.")

    uploaded_files = st.file_uploader(
        "📄 Upload PDF file(s)", 
        type=["pdf"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        chain = initialize_pdf_qa_chain(uploaded_files)
        if chain:
            query = st.text_input("❓ Ask a question from the PDF(s)", placeholder="e.g., What is the main topic in chapter 2?")

            if query:
                try:
                    result = chain.invoke({"question": query})
                    st.markdown("### 💡 Answer")
                    st.success(result["answer"])

                    with st.expander("📖 Source Snippets"):
                        for doc in result.get("source_documents", []):
                            content = getattr(doc, "page_content", "")
                            if content:
                                st.markdown(content[:500] + "...")
                            else:
                                st.write("⚠️ No text available in this source.")
                except Exception as e:
                    st.error(f"Error processing the query: {e}")
        else:
            st.warning("PDF chain initialization failed.")
