# DocChat — Agentic RAG Document & Web Q&A System

An agentic Retrieval-Augmented Generation assistant that answers questions grounded in your own documents (PDF, Word, Excel, PowerPoint), with confidence-based web search fallback when the answer isn't in your documents.

> **Status: active development.** The current version is a Streamlit prototype used to validate the core pipeline. It is being migrated to a standalone offline desktop application — see [Roadmap](#roadmap) below.

---

## What it does today

- **Multi-format ingestion** — upload PDF, DOCX, XLSX, PPTX, or TXT files; each is normalized into a common internal format so the rest of the pipeline treats them identically.
- **Grounded Q&A** — questions are answered using only retrieved chunks from your uploaded documents, with the source filename and page/section cited.
- **Real confidence scoring** — retrieval confidence is computed from actual vector similarity, not a placeholder value.
- **Web search fallback (opt-in)** — when document confidence is low, you're offered (never forced) a web search via Tavily, and the result is synthesized into a single answer that clearly separates what came from your documents versus the web.
- **Per-document filtering** — restrict answers to a single uploaded document instead of searching everything.
- **Persistent document storage** — uploaded documents remain indexed across restarts (stored locally via ChromaDB).

## What it doesn't do yet

- Conversation history does not currently persist across restarts (in progress — see roadmap).
- No desktop UI yet — currently runs as a local Streamlit web app.
- No workspace/subject organization, flashcards, question-paper generation, YouTube ingestion, or document deletion yet — all planned, not built.

---

## Tech stack

Python · Streamlit · ChromaDB · Sentence-Transformers (`all-MiniLM-L6-v2`) · Groq (LLM inference) · Tavily (web search) · pdfplumber, python-docx, openpyxl, python-pptx (document parsing)

---

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Add your API keys**

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here
```
Get a free Groq key at [console.groq.com](https://console.groq.com) and a free Tavily key at [tavily.com](https://tavily.com).

**3. Run the app**
```bash
streamlit run app.py
```
The app opens in your browser at `http://localhost:8501`. Uploaded documents are stored locally in `./chroma_db` and persist across restarts.

---

## Project structure

| File | Responsibility |
|---|---|
| `app.py` | Streamlit UI — upload, chat, document filtering, web-search confirmation |
| `document_processor.py` | Routes each file type to its extractor, normalizes output |
| `chunker.py` | PDF-specific extraction; overlapping-window text chunking (shared by all formats) |
| `store.py` | ChromaDB indexing and retrieval, source/document management |
| `agent.py` | Retrieval confidence scoring, document/web answer generation, hybrid synthesis |
| `generator.py` | Standalone grounded-answer generation (used outside the agent flow) |
| `embedder.py` | Standalone embedding helper |

---

## Roadmap

Full project scope, architecture decisions, and build order live in [`AGENTIC_RAG_BUILD_GUIDE_V2.md`](./AGENTIC_RAG_BUILD_GUIDE_V2.md). In short, the project is moving from this Streamlit prototype to an offline, account-free desktop application with:

- A three-panel UI (document tree, chat, generative tools)
- Workspace-based organization (subjects/students)
- YouTube video ingestion, flashcard generation, and difficulty-tiered question-paper generation
- Conversation history export/import and document deletion
- Two distribution builds: a pre-configured private release and a bring-your-own-key public release

See the build guide for full details before making architectural changes.

---

## License

Personal/educational project — no license set yet.