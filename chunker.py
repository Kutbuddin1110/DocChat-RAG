import pdfplumber
import logging

logger = logging.getLogger(__name__)


def load_pdf_text(path):
    """Extract text and tables from a PDF, page by page."""
    pages = []
    try:
        with pdfplumber.open(path) as pdf:
            logger.info(f"Loading PDF: {path} ({len(pdf.pages)} pages)")

            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""

                tables = page.extract_tables()
                table_text = ""
                if tables:
                    for table in tables:
                        for row in table:
                            clean_row = [cell.strip() if cell else "" for cell in row]
                            if any(clean_row):
                                table_text += " | ".join(clean_row) + "\n"
                        table_text += "\n"

                combined = (text + "\n" + table_text).strip()
                if combined:
                    pages.append({"page_num": i + 1, "text": combined})

    except Exception as e:
        logger.error(f"Error loading PDF {path}: {str(e)}")
        return None

    logger.info(f"Extracted {len(pages)} pages from {path}")
    return pages if pages else None


def chunk_text(pages, chunk_size=1000, overlap=150):
    """Chunk page text into overlapping word windows for better context."""
    chunks = []
    if not pages:
        return chunks

    for page in pages:
        text = page["text"]
        if not text or not text.strip():
            continue

        words = text.split()
        if len(words) < 10:
            continue

        i = 0
        chunk_count = 0
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            if len(chunk_words) < 5:
                break

            chunks.append({
                "text": " ".join(chunk_words),
                "page_num": page["page_num"],
                "chunk_index": chunk_count,
            })

            chunk_count += 1
            i += chunk_size - overlap

    logger.info(f"Created {len(chunks)} chunks from {len(pages)} pages")
    return chunks


if __name__ == "__main__":
    pages = load_pdf_text("sample.pdf")
    if pages:
        chunks = chunk_text(pages)
        print(f"Total chunks: {len(chunks)}")
        print(f"First chunk: {chunks[0]['text'][:100]}...")
