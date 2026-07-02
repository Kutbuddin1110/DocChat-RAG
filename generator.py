import os
from groq import Groq
from dotenv import load_dotenv
from store import search

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def answer_question(query, top_k=3):
    results = search(query, top_k=top_k)
    chunks = results["documents"][0]
    pages = [m["page_num"] for m in results["metadatas"][0]]
    sources = [m["source"] for m in results["metadatas"][0]]  

    context = "\n\n".join([f"[{s}, Page {p}]: {c}" for c, p, s in zip(chunks, pages, sources)])

    prompt = f"""Answer the question using ONLY the context below. 
If the answer isn't in the context, say "I couldn't find that in the document."
Cite the filename and page number(s) you used.

Context:
{context}

Question: {query}

Answer:"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    answer = answer_question("What is this document about?")
    print(answer)