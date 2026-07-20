import os
import logging
from groq import Groq
from dotenv import load_dotenv
from store import search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def answer_question(query, top_k=5, doc_source=None):
    """
    Generate an answer from retrieved document chunks.

    Args:
        query: user's question
        top_k: number of chunks to retrieve
        doc_source: optional filename to restrict search to a single document
    """
    try:
        results = search(query, top_k=top_k, filter_by_source=doc_source)

        if not results["documents"][0]:
            logger.info(f"No chunks found for query: {query}")
            return "I couldn't find that in the document."

        chunks = results["documents"][0]
        pages = [m["page_num"] for m in results["metadatas"][0]]
        sources = [m["source"] for m in results["metadatas"][0]]

        logger.info(f"Retrieved {len(chunks)} chunks for query: {query}")

        context = "\n\n".join(
            [f"[Source: {s}, Page {p}]\n{c}" for c, p, s in zip(chunks, pages, sources)]
        )

        prompt = f"""Answer the question using ONLY the provided context below.

Rules:
1. If the answer is in the context, provide a comprehensive, complete answer.
2. If the answer is NOT in the context, say "This information is not available in the provided documents."
3. Always cite the source document and page number(s) you used.
4. Be thorough and detailed — do not cut your answer short.

Context from documents:
{context}

Question: {query}

Answer:"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,   # THE FIX: this was unset before, causing truncation
            temperature=0.3,
            timeout=30,
        )

        answer = response.choices[0].message.content
        logger.info(f"Generated response length: {len(answer)} characters")
        return answer

    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        return f"Error generating response: {str(e)}"


if __name__ == "__main__":
    answer = answer_question("What is this document about?")
    print(answer)
