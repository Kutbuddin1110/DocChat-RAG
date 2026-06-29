from pypdf import PdfReader

def load_pdf_text(path):
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        pages.append({"page_num": i + 1, "text": page.extract_text()})
    return pages

def chunk_text(pages, chunk_size=500, overlap=50):
    """Splits text into overlapping word chunks, keeping track of source page."""
    chunks = []
    for page in pages:
        words = page["text"].split()
        i = 0
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunks.append({
                "text": " ".join(chunk_words),
                "page_num": page["page_num"]
            })
            i += chunk_size - overlap
    return chunks

if __name__ == "__main__":
    pages = load_pdf_text("sample.pdf")
    chunks = chunk_text(pages)
    print(f"Total chunks: {len(chunks)}")
    print(chunks[0])