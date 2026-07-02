import streamlit as st
from store import index_pdf, collection
from generator import answer_question
import os

st.title("📄 DocChat — Ask Questions About Your Documents")

uploaded_files = st.file_uploader("Upload PDF(s)", type="pdf", accept_multiple_files=True)

if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = set()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if uploaded_files:
    for uploaded_file in uploaded_files:
        if uploaded_file.name not in st.session_state.indexed_files:
            pdf_path = f"temp_{uploaded_file.name}"
            with open(pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner(f"Indexing {uploaded_file.name}..."):
                success = index_pdf(pdf_path)  # CHANGED: capture return value

            if not success:
                st.error(f"⚠️ Could not extract text from '{uploaded_file.name}'. PDF may be image-rendered (OCR not yet supported).")
            else:
                st.session_state.indexed_files.add(uploaded_file.name)
                
    if st.session_state.indexed_files:
        st.success(f"✅ Indexed: {', '.join(st.session_state.indexed_files)}")

    question = st.text_input("Ask a question:")
    if question:
        with st.spinner("Thinking..."):
            answer = answer_question(question)
        st.session_state.chat_history.append({"question": question, "answer": answer})

    if st.session_state.chat_history:
        st.write("### Conversation History")
        for entry in reversed(st.session_state.chat_history):
            st.markdown(f"**You:** {entry['question']}")
            st.markdown(f"**DocChat:** {entry['answer']}")
            st.divider()