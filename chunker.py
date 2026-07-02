import pdfplumber

def load_pdf_text(path):
    pages = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            
            # Extract tables separately and convert to readable text
            tables = page.extract_tables()
            table_text = ""
            for table in tables:
                for row in table:
                    clean_row = [cell.strip() if cell else "" for cell in row]
                    if any(clean_row):  # skip completely empty rows
                        table_text += " | ".join(clean_row) + "\n"
                table_text += "\n"  
            
            combined = (text + "\n" + table_text).strip()
            pages.append({"page_num": i + 1, "text": combined})
    return pages

def chunk_text(pages, chunk_size=500, overlap=50):
    chunks = []
    for page in pages:
        text = page["text"]
        if not text or not text.strip():  # skip blank/None pages
            continue
        words = text.split()
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