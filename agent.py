import os
import logging
from groq import Groq
from tavily import TavilyClient
from store import search

logger = logging.getLogger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

# Below this, document evidence is considered too weak to trust alone
CONFIDENCE_THRESHOLD = 0.55


class AgentRouter:

    def search_documents(self, query, doc_source=None, top_k=5):
        """Search documents and compute a REAL confidence score from
        ChromaDB's distance metric, instead of a hardcoded number."""
        results = search(query, top_k=top_k, filter_by_source=doc_source)
        chunks = results["documents"][0]

        if not chunks:
            return {"found": False, "confidence": 0.0, "chunks": [], "metadatas": [], "citations": []}

        # ChromaDB's default distance is cosine distance: 0 = identical, 2 = opposite.
        # Convert the best (smallest) distance into a 0-1 "confidence" score.
        best_distance = min(results["distances"][0])
        confidence = max(0.0, 1 - (best_distance / 2))

        metadatas = results["metadatas"][0]
        citations = [f"{m['source']} ({m['page_num']})" for m in metadatas]

        return {
            "found": True,
            "confidence": confidence,
            "chunks": chunks,
            "metadatas": metadatas,
            "citations": citations,
        }

    def generate_doc_answer(self, query, doc_result):
        context = "\n\n".join(
            f"[{m['source']}, {m['page_num']}]\n{c}"
            for c, m in zip(doc_result["chunks"], doc_result["metadatas"])
        )
        prompt = f"""Answer using ONLY this document context. Be thorough and cite sources.

Context:
{context}

Question: {query}

Answer:"""
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3,
        )
        return response.choices[0].message.content

    def search_web(self, query):
        """Search the web via Tavily. Only called after explicit user confirmation."""
        try:
            response = tavily_client.search(query, max_results=5, include_answer=False)
            results = response.get("results", [])
            if not results:
                return {"found": False, "context": "", "citations": []}

            context = "\n".join(f"- {r['title']}: {r['content'][:400]}" for r in results)
            citations = [r["url"] for r in results]
            return {"found": True, "context": context, "citations": citations}
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return {"found": False, "context": "", "citations": []}

    def generate_web_answer(self, query, web_result):
        prompt = f"""Answer using these web search results. Be thorough.

Web results:
{web_result['context']}

Question: {query}

Answer:"""
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3,
        )
        return response.choices[0].message.content

    def synthesize_hybrid(self, query, doc_answer, web_answer):
        """Combine a document-grounded answer with a web-grounded answer into one response."""
        prompt = f"""You have two partial answers to the same question, from two different sources.
Combine them into a single clear answer. Distinguish clearly which parts came from the
user's documents and which came from the web.

From documents:
{doc_answer}

From the web:
{web_answer}

Question: {query}

Combined answer:"""
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3,
        )
        return response.choices[0].message.content