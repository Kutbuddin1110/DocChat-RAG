import chromadb
import os
import logging
import datetime
from sentence_transformers import SentenceTransformer
from document_processor import DocumentProcessor
from chunker import load_pdf_text, chunk_text

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("docchat")


def index_document(file_path):
    """Index any supported document type (pdf, docx, xlsx, pptx, txt)."""
    try:
        logger.info(f"Starting indexing for: {file_path}")

        pages = DocumentProcessor.process(file_path)
        
        if not pages:
            logger.error(f"No text extracted from {file_path}")
            return {"success": False, "chunks": 0, "error": f"Could not extract text from {os.path.basename(file_path)}"}

        chunks = chunk_text(pages)
        if not chunks:
            logger.error(f"No chunks generated from {file_path}")
            return {"success": False, "chunks": 0, "error": f"Could not chunk document {os.path.basename(file_path)}"}

        texts = [c["text"] for c in chunks]
        embeddings = model.encode(texts, show_progress_bar=True).tolist()
        ids = [f"{os.path.basename(file_path)}_{i}" for i in range(len(chunks))]

        source_name = os.path.basename(file_path)
        metadatas = [
            {
                "page_num": c["page_num"],
                "chunk_index": c.get("chunk_index", 0),
                "source": source_name,
                "timestamp": str(datetime.datetime.now()),
            }
            for c in chunks
        ]

        collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

        logger.info(f"Successfully indexed {len(chunks)} chunks from {file_path}")
        return {"success": True, "chunks": len(chunks), "error": None}

    except Exception as e:
        logger.error(f"Error indexing {file_path}: {str(e)}")
        return {"success": False, "chunks": 0, "error": str(e)}


def search(query, top_k=5, filter_by_source=None):
    """
    Search the vector store, optionally restricted to one document.

    Args:
        query: search text
        top_k: number of results
        filter_by_source: exact filename to filter to (None = all documents)
    """
    try:
        query_embedding = model.encode([query]).tolist()

        where_filter = None
        if filter_by_source:
            where_filter = {"source": {"$eq": filter_by_source}}
            logger.info(f"Filtering by source: {filter_by_source}")

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where=where_filter,
        )

        logger.info(f"Retrieved {len(results['documents'][0])} results")
        return results

    except Exception as e:
        logger.error(f"Error searching: {str(e)}")
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}


def get_indexed_documents():
    """Return a list of unique source filenames currently indexed."""
    try:
        all_items = collection.get()
        sources = set(meta["source"] for meta in all_items.get("metadatas", []))
        return sorted(sources)
    except Exception as e:
        logger.error(f"Error getting documents: {str(e)}")
        return []


if __name__ == "__main__":
    result = index_document("sample.pdf")
    print(result)

    docs = get_indexed_documents()
    print(f"Indexed documents: {docs}")

    results = search("What is this document about?")
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"\n--- {meta['source']} (Page {meta['page_num']}) ---")
        print(doc[:200], "...")
