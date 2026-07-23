import streamlit as st
from store import index_document, collection
from generator import answer_question
import os
import tempfile
from store import get_indexed_documents
from agent import AgentRouter

# --- Page Config ---
st.set_page_config(
    page_title="DocChat",
    page_icon="📄",
    layout="wide"
)

# --- Custom CSS for chat bubbles ---
st.markdown("""
<style>
    /* Main chat area */
    .main-header {
        text-align: center;
        padding: 1rem 0 0.5rem 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    
    /* User bubble - right aligned */
    .user-bubble {
        display: flex;
        justify-content: flex-end;
        margin: 8px 0;
    }
    .user-bubble-inner {
        background-color: #0084ff;
        color: white;
        padding: 10px 16px;
        border-radius: 18px 18px 4px 18px;
        max-width: 70%;
        font-size: 0.95rem;
        line-height: 1.4;
    }

    /* Bot bubble - left aligned */
    .bot-bubble {
        display: flex;
        justify-content: flex-start;
        margin: 8px 0;
    }
    .bot-bubble-inner {
        background-color: #f0f2f6;
        color: #1a1a1a;
        padding: 10px 16px;
        border-radius: 18px 18px 18px 4px;
        max-width: 70%;
        font-size: 0.95rem;
        line-height: 1.4;
    }

    /* Avatar labels */
    .avatar-you {
        font-size: 0.75rem;
        color: #888;
        text-align: right;
        margin-right: 4px;
        margin-bottom: 2px;
    }
    .avatar-bot {
        font-size: 0.75rem;
        color: #888;
        margin-left: 4px;
        margin-bottom: 2px;
    }

    /* Chat container */
    .chat-container {
        padding: 1rem 0;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #5a5b5c;
    }

    /* Input area */
    .input-area {
        position: sticky;
        bottom: 0;
        background: white;
        padding-top: 1rem;
        border-top: 1px solid #e0e0e0;
    }

    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Session State ---
if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = set(get_indexed_documents())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "agent" not in st.session_state:
    st.session_state.agent = AgentRouter()
if "pending_websearch" not in st.session_state:
    st.session_state.pending_websearch = None

# --- Sidebar ---
with st.sidebar:
    st.markdown("## 📄 DocChat")
    st.markdown("Ask questions about your PDF documents using AI.")
    st.divider()

    st.markdown("### Upload Documents")
    uploaded_files = st.file_uploader(
    "Upload one or more documents",
    type=["pdf", "docx", "xlsx", "xls", "pptx", "txt"],
    accept_multiple_files=True,
    label_visibility="collapsed"
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file.name not in st.session_state.indexed_files:
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    pdf_path = tmp.name

                with st.spinner(f"Indexing {uploaded_file.name}..."):
                    result = index_document(pdf_path)

                os.remove(pdf_path)

                if not result["success"]:
                    st.error(f"⚠️ Could not index '{uploaded_file.name}': {result['error']}")
                else:
                    st.session_state.indexed_files.add(uploaded_file.name)

    if st.session_state.indexed_files:
        st.markdown("### 📚 Indexed Documents")
        for fname in st.session_state.indexed_files:
            st.markdown(f"✅ {fname}")

        st.markdown("### 🔍 Answer From")
        doc_options = ["All documents"] + sorted(st.session_state.indexed_files)
        selected_doc = st.selectbox(
            "Restrict answers to a single document",
            doc_options,
            label_visibility="collapsed",
        )
        st.session_state.doc_filter = None if selected_doc == "All documents" else selected_doc

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.75rem; color:#888;'>Built with Sentence-Transformers, ChromaDB, Groq & Streamlit</div>",
        unsafe_allow_html=True
    )

# --- Main Chat Area ---
st.markdown(
    "<div class='main-header'><h2>📄 DocChat</h2>"
    "<p style='color:#888; font-size:0.9rem;'>Upload PDFs in the sidebar, then ask questions below</p></div>",
    unsafe_allow_html=True
)

# Display chat history as bubbles
if st.session_state.chat_history:
    for entry in st.session_state.chat_history:
        # User bubble
        st.markdown(
            f"<div class='avatar-you'>You</div>"
            f"<div class='user-bubble'>"
            f"<div class='user-bubble-inner'>{entry['question']}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        # Bot bubble
        st.markdown(
            f"<div class='avatar-bot'>DocChat</div>"
            f"<div class='bot-bubble'>"
            f"<div class='bot-bubble-inner'>{entry['answer']}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
else:
    if not st.session_state.indexed_files:
        st.markdown(
            "<div style='text-align:center; color:#aaa; margin-top:4rem;'>"
            "<h3>👈 Upload a PDF to get started</h3>"
            "</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='text-align:center; color:#aaa; margin-top:4rem;'>"
            "<h3>💬 Ask a question about your documents</h3>"
            "</div>",
            unsafe_allow_html=True
        )

if st.session_state.pending_websearch:
    pending = st.session_state.pending_websearch
    st.info("Your documents don't fully cover this. Want me to check the web?")
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔍 Search the web"):
            agent = st.session_state.agent
            with st.spinner("Searching the web..."):
                web_result = agent.search_web(pending["query"])

            if web_result["found"]:
                web_answer = agent.generate_web_answer(pending["query"], web_result)
                combined = agent.synthesize_hybrid(pending["query"], pending["doc_answer"], web_answer)
                st.session_state.chat_history[pending["entry_index"]]["answer"] = combined
            else:
                st.warning("Web search didn't return anything useful.")

            st.session_state.pending_websearch = None
            st.rerun()
    with col2:
        if st.button("No, that's fine"):
            st.session_state.pending_websearch = None
            st.rerun()
            
# --- Input ---
st.markdown("<div class='input-area'>", unsafe_allow_html=True)

if st.session_state.indexed_files:
    question = st.chat_input("Ask a question about your documents...")
    if question:
        agent = st.session_state.agent
        with st.spinner("Searching documents..."):
            doc_result = agent.search_documents(question, doc_source=st.session_state.get("doc_filter"))

        if doc_result["found"]:
            doc_answer = agent.generate_doc_answer(question, doc_result)
        else:
            doc_answer = "This information is not available in the provided documents."

        entry = {"question": question, "answer": doc_answer, "confidence": doc_result["confidence"]}
        st.session_state.chat_history.append(entry)

        # Low confidence -> offer (don't force) a web search
        if doc_result["confidence"] < 0.55:
            st.session_state.pending_websearch = {
                "query": question,
                "doc_answer": doc_answer,
                "entry_index": len(st.session_state.chat_history) - 1,
            }
        st.rerun()
else:
    st.chat_input("Upload a PDF first to start asking questions...", disabled=True)

st.markdown("</div>", unsafe_allow_html=True)