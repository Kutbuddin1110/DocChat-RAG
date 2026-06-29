from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_chunks(chunks):
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings

if __name__ == "__main__":
    from chunker import load_pdf_text, chunk_text
    pages = load_pdf_text("sample.pdf")
    chunks = chunk_text(pages)
    embeddings = embed_chunks(chunks)
    print(f"Embedding shape: {embeddings.shape}")