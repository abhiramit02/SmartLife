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

# --- Helper Function to extract text from PDFs ---
def extract_text_from_pdfs(uploaded_files):
    raw_text = ""
    for file in uploaded_files:
        pdf_reader = PdfReader(file)
        for page in pdf_reader.pages:
            raw_text += page.extract_text() or ""
    return raw_text

# --- Initialize Chain from Uploaded PDFs ---
def initialize_pdf_qa_chain(pdf_files):
    text = extract_text_from_pdfs(pdf_files)

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=150)
    docs = splitter.create_documents([text])

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # ✅ Use Chroma instead of FAISS for compatibility
    with tempfile.TemporaryDirectory() as temp_dir:
        vectorstore = Chroma.from_documents(docs, embeddings, persist_directory=temp_dir)
        retriever = vectorstore.as_retriever(search_type="similarity", k=4)

        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )

        llm = ChatGroq(
    api_key=st.secrets["GROQ_API_KEY"],
    temperature=0.2,
    model_name="llama3-8b-8192"
)


        chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=memory,
            return_source_documents=True
        )
        return chain

# --- UI Logic ---
def render_pdf_chat():
    st.markdown("## 📚 Ask Questions from Your PDFs")
    st.markdown("Upload one or more PDF files and ask anything about their content.")

    uploaded_files = st.file_uploader("📄 Upload PDF file(s)", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        chain = initialize_pdf_qa_chain(uploaded_files)

        query = st.text_input("❓ Ask a question from the PDF(s)", placeholder="e.g., What is the main topic in chapter 2?")

        if query:
            result = chain.invoke({"question": query})
            st.markdown("### 💡 Answer")
            st.success(result["answer"])

            # Optional: Show source documents
            with st.expander("📖 Source Snippets"):
                for doc in result["source_documents"]:
                    st.markdown(doc.page_content[:500] + "...")
