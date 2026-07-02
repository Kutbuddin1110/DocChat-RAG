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

    question = st.text_input("Ask a question or request a diagram:")
    if question:
        from generator import is_diagram_request, generate_diagram

        if is_diagram_request(question):
            with st.spinner("Generating diagram..."):
                mermaid_output = generate_diagram(question)

            if mermaid_output == "INSUFFICIENT_CONTEXT":
                st.warning("Not enough information in the document to generate a diagram for this request.")
                st.session_state.chat_history.append({
                    "question": question,
                    "answer": "Could not generate diagram — insufficient context in uploaded documents.",
                    "type": "text"
                })
            else:
                # clean up common LLM output noise around mermaid blocks
                clean = mermaid_output.replace("```mermaid", "").replace("```", "").strip()

                # render mermaid in streamlit using HTML component
                mermaid_html = f"""
                <div class="mermaid">
                {clean}
                </div>
                <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                <script>mermaid.initialize({{startOnLoad: true}});</script>
                """
                st.components.v1.html(mermaid_html, height=500, scrolling=True)
                st.session_state.chat_history.append({
                    "question": question,
                    "answer": f"📊 Diagram generated from document context.",
                    "type": "diagram",
                    "mermaid": clean
                })
        else:
            with st.spinner("Thinking..."):
                answer = answer_question(question)
            st.session_state.chat_history.append({
                "question": question,
                "answer": answer,
                "type": "text"
            })

    if st.session_state.chat_history:
        st.write("### Conversation History")
        for entry in reversed(st.session_state.chat_history):
            st.markdown(f"**You:** {entry['question']}")
            if entry.get("type") == "diagram":
                clean = entry["mermaid"]
                mermaid_html = f"""
                <div class="mermaid">
                {clean}
                </div>
                <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                <script>mermaid.initialize({{startOnLoad: true}});</script>
                """
                st.components.v1.html(mermaid_html, height=500, scrolling=True)
            else:
                st.markdown(f"**DocChat:** {entry['answer']}")
            st.divider()