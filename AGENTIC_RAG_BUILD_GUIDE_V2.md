# DocChat — Agentic RAG Study Assistant
## Build Guide v2 (supersedes the original AGENTIC_RAG_BUILD_GUIDE.md)

This guide describes *what* to build and *why*, and the order to build it in. It intentionally contains no code — it's meant to be handed to a developer or an AI coding agent as a spec, with implementation details worked out at build time.

---

## 1. What this project actually is

Not "a RAG chatbot." It's a personal/family **study and teaching assistant**: a desktop application that lets a person upload their own documents (PDFs, Word, Excel, PowerPoint, YouTube videos), organize them, ask grounded questions with citations, and generate study aids (flashcards, question papers) from them — entirely on their own machine, with no account system and no ongoing hosting cost.

It is being built as a portfolio piece, and will be given to two real users (a student and a teacher) with genuinely different needs, which is why the data model below has more structure than a single-user hobby project would need.

---

## 2. Non-negotiable constraints (decided, do not revisit without reason)

- **No hosting, no server, no login system.** Everything runs locally on the user's machine. This was deliberately chosen over a hosted web app because free-tier hosting cannot guarantee persistent storage, and paid hosting was ruled out.
- **Two separate builds from one codebase:**
  - **Personal build** (for the developer's brother and aunt): ships with the developer's own Groq and Tavily API keys baked in at build time. Accepted risk: a compiled key is not truly secret, but this is acceptable because the key is dedicated to this app and not reused elsewhere.
  - **Public build** (published on GitHub): ships with no key. On first launch it prompts the user to paste their own Groq/Tavily key, which is then saved to a local config file on their machine.
  - Both builds come from the same source; a single build-time flag determines whether a key is embedded or the user is prompted.
- **Mobile is explicitly out of scope for now.** True native mobile (especially iOS) cannot practically run the local embedding model and vector search the way desktop can. If phone access is wanted later, the cheapest path is running the desktop app as a local server and reaching it from a phone browser on the same network — this is not a mobile app and should not be scoped as one. Revisit only after the desktop version is complete and proven useful.

---

## 3. Current build status (as of this guide)

Already built and working:
- Multi-format document ingestion (PDF, DOCX, XLSX, PPTX, TXT), each format normalized into the same "page-like" unit so the rest of the pipeline doesn't care what format a document originally was.
- Chunking with overlap, tuned to avoid losing context at chunk boundaries.
- Local vector storage (embeddings + metadata including source filename and page/section identifier).
- An agent layer that: retrieves relevant chunks for a question, computes a real confidence score from retrieval distance (not a hardcoded number), answers from documents when confidence is high, and — only after explicit user confirmation — searches the web and produces a combined answer that clearly separates what came from the user's documents versus the web.
- Basic Streamlit interface with upload, chat, document indexing status, and per-document answer filtering.

Explicitly not yet built: everything from Section 4 onward. The Streamlit interface was a prototyping tool to validate the pipeline logic — the production interface is the three-column desktop app described below, not an extension of the Streamlit UI.

---

## 4. Data model — the organizational hierarchy

Two people will use this app for genuinely different purposes, so the structure needs to serve both without forcing complexity on the person who doesn't need it.

- **Group** (optional layer): represents a person or category — e.g., a teacher's individual student. A student using the app themselves has no need for this layer and can skip straight to workspaces.
- **Workspace**: represents a subject or notebook — e.g., "Biology," "Physics Revision." This is the unit that actually contains documents and conversation history. All retrieval, chat, and generated study material is scoped to one workspace at a time — nothing crosses between workspaces.
- **Document tree** (new, inside a workspace): documents within a workspace can be organized into a folder-like tree — chapters, units, topics — of arbitrary depth. This is purely organizational (for the human browsing the sidebar); it does not change how retrieval works, since retrieval searches within the whole workspace (or a single selected document) regardless of which folder it sits in.

Because there is no login, "who is using the app" is not tracked by the software at all — each installation belongs to whoever runs it. The Group/Workspace/Document-tree structure lives entirely in that one person's local data.

---

## 5. Three-column desktop layout

The desktop app (built with a native Python UI toolkit, not a web framework) is divided into three resizable, independently collapsible panels:

- **Left panel — Documents.** The Group → Workspace → Document-tree structure from Section 4, shown as an expandable tree. This is where documents are uploaded, organized into chapter/topic folders, and where a document (or folder) can be selected to scope a question to just that material. Collapsible so the middle panel can expand for focused reading.
- **Middle panel — Conversation.** The chat interface: question in, grounded answer out, with citations, confidence-based web-search prompts (as already built), and the running history for the current workspace.
- **Right panel — Tools.** Three tools, described in Section 6, each operating on the currently selected workspace and, where relevant, the currently selected document(s) in the left panel.

---

## 6. Right-panel tools and conversation/document management (new capabilities)

The generative tools (6a–6c) are extensions of the same agent/retrieval logic already built — they reuse the existing "search this workspace's documents" step, then apply a different generation step on top. They are not separate systems. The remaining two (6d–6e) are management capabilities rather than generative ones, but are grouped here since they operate on the same workspace/document structures.

### 6a. YouTube link summarizer
- User pastes a YouTube link. The system fetches the video's transcript, summarizes it, and — per the decision made for this build — treats the video exactly like an uploaded document: it is chunked, embedded, and stored the same way a PDF is, tagged with its own title as the source. This means video content becomes fully searchable in ordinary chat questions, not just available as a static note.
- The user can choose which workspace/folder the video gets filed under, same as a document upload.
- Because it's stored the same way as a document, no separate retrieval logic is needed — it simply becomes more material the existing search already covers.

### 6b. Flashcard generator
- Operates on whatever is currently selected in the left panel (a single document, a folder/chapter, or the whole workspace).
- Produces question/answer style cards drawn only from the selected material, generated the same grounded way as chat answers (retrieval first, generation second) so cards don't drift from what the source actually says.
- Output is a structured set of cards, not free-form prose, so the UI can display and page through them individually.

### 6c. Question paper generator
- Also scoped to whatever is selected in the left panel.
- User picks a difficulty level before generating:
  - **Easy** — questions that test recall of stated facts directly from the material.
  - **Medium** — questions that require explaining a concept in the user's own words, not just quoting it.
  - **Hard** — questions that require applying, comparing, or analyzing across multiple parts of the material, not answerable by finding one sentence.
- **Storage is deliberately separate from the document/vector store.** Generated question papers are kept in their own record store, tagged with workspace, source material used, difficulty, and timestamp. This separation matters for two reasons: (1) a generated quiz question must never be retrievable as if it were source material when the user asks an ordinary question later, and (2) keeping a clean historical record of what's been generated allows a future "was this question already asked before" check when generating new papers, without that check having anything to do with document retrieval.
- Generated papers are downloadable/exportable and remain browsable later as a reference, independent of the chat history.

### 6d. Conversation history export / import
- A user can export the current workspace's conversation history to a file they keep themselves (e.g., on a USB drive, cloud storage, email to themselves).
- On a new machine, or after an accidental wipe, the user can import that file back in to restore the conversation exactly where they left off, inside the same (or a newly created) workspace.
- This is a deliberate safety net independent of whatever the underlying storage system is: even once real local persistence (Section 4) is built, hardware failure or accidental deletion is still possible, so export/import remains useful as a portable backup a user controls themselves, not just a stopgap for the current prototype's lack of persistence.
- Import should be additive, not destructive by default — bringing in an exported history should not silently overwrite or delete whatever's already in the target workspace unless the user explicitly chooses to replace it.

### 6e. Document removal
- A document (or an entire folder in the document tree) that is no longer needed can be deleted from a workspace.
- Deletion must remove the document's chunks and embeddings from the vector store, not just hide it from the visible tree — otherwise "deleted" documents would keep quietly influencing answers and citations.
- Deletion is scoped only to the selected document/folder within its workspace; it must not be able to affect other workspaces or documents outside the selection.
- Deleting a document should not delete conversation history that referenced it — past chat answers stay as a historical record, they just won't be re-derivable from that source anymore going forward.

---

## 7. Core pipeline flow (already built, described for reference)

1. **Ingestion**: a file (or YouTube link) comes in, gets routed to the correct extractor based on its type, and comes out as a normalized list of "page-like" text units, regardless of original format.
2. **Chunking**: each page-like unit is split into overlapping word windows, so no single fact gets orphaned right at a chunk boundary.
3. **Embedding**: each chunk is converted into a vector representation.
4. **Storage**: chunks, their vectors, and metadata (source name, page/section, workspace, timestamp) are stored locally.
5. **Retrieval**: a user's question is embedded the same way, and the closest-matching chunks are retrieved, scoped to the current workspace (and optionally a single selected document/folder).
6. **Confidence scoring**: the retrieval step produces a real confidence score based on how close the best match actually is — not a placeholder number — which determines whether the system trusts the documents alone or offers a web search.
7. **Generation**: retrieved chunks are handed to the language model with instructions to answer only from that context and to cite sources; if confidence is low, the user is asked (not forced) whether to also check the web, and if they agree, the two answers are combined with sources clearly attributed to "from your documents" vs. "from the web."

---

## 8. Packaging and distribution

- The app is packaged into a standalone executable so end users (brother, aunt) don't need Python installed themselves.
- Windows is the priority platform, since that's the primary development and target environment; Mac/Linux packaging is not in scope unless specifically needed later.
- The personal build and public build are produced from the same source tree via a build-time flag, not maintained as separate codebases.

---

## 9. Known issues in the current prototype (fix during/before migration)

- **Word document ingestion silently fails** in the current build due to a wrong dependency being installed (`python-docs` instead of `python-docx`). This is a one-line dependency fix, not a logic bug, but it should be verified working before the docx extraction logic is trusted or built upon further.
- **Conversation history does not survive a restart.** This is expected given the current prototype's design (chat lives only in memory for that session) rather than a defect — it is resolved by the real local persistence work already planned in Section 4, with export/import (Section 6d) as an additional safety net on top, not a replacement for it.

---

## 10. Explicitly deferred (do not build yet)

- Hosted/web version with Google login, per-user accounts, Supabase/Postgres backend — this was the previous direction and has been abandoned in favor of the offline desktop approach. Do not resurrect this without a new, deliberate scoping conversation.
- Native mobile app — deferred per Section 2, revisit only after the desktop app is complete.
- A formal automated test suite — reasonable to add once the desktop rebuild stabilizes, not before.

---

## 11. Suggested build order from here

1. Migrate the existing Streamlit prototype's working logic (ingestion, retrieval, agent, web-search confirmation) into the desktop UI toolkit, starting with a working three-column shell before adding the tools.
2. Implement the Group → Workspace → Document-tree data model as local structured storage, replacing the Streamlit prototype's flat, session-only state.
3. Wire the left-panel document tree to real upload/organize/select behavior.
4. Add the YouTube summarizer tool (simplest of the three, since it reuses the existing document-ingestion path).
5. Add the flashcard generator.
6. Add the question paper generator, including its separate storage and the "previously generated" reference capability.
7. Add document/folder deletion (including removing the corresponding vectors from storage) and conversation history export/import.
8. Set up the two-build packaging process (bundled key vs. prompted key) and produce the first distributable executable.
9. Only after the above is solid and in real use: revisit whether phone/mobile access is still wanted, and scope it as its own deliberate decision.
