import chromadb
from sentence_transformers import SentenceTransformer
from chunker import load_pdf_text, chunk_text

model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection("docchat")

def index_pdf(pdf_path):
    pages = load_pdf_text(pdf_path)
    chunks = chunk_text(pages)
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts).tolist()
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"page_num": c["page_num"]} for c in chunks]

    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    print(f"Indexed {len(chunks)} chunks from {pdf_path}")

def search(query, top_k=3):
    query_embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=top_k)
    return results

if __name__ == "__main__":
    index_pdf("sample.pdf")
    results = search("What is this document about?")
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"\n--- Page {meta['page_num']} ---")
        print(doc[:200], "...")