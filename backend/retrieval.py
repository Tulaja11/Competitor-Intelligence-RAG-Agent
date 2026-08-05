import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from config import GEMINI_API_KEY, CHROMA_PATH

# Initialize embeddings
embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=GEMINI_API_KEY,
    request_timeout=120,
)

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection(name="competitors")

# Text splitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
)

# LLM for answer generation
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    google_api_key=GEMINI_API_KEY,
    temperature=0.3,
)


def store_documents(results):
    """Chunk and store fetched results into ChromaDB with metadata."""
    total_stored = 0

    for i, doc in enumerate(results):
        chunks = splitter.split_text(doc["content"])

        for j, chunk in enumerate(chunks):
            doc_id = f"{doc['competitor']}_{doc['category']}_{i}_{j}"

            # Embed the chunk
            vector = embeddings.embed_query(chunk)

            # Store in ChromaDB with metadata
            collection.upsert(
                ids=[doc_id],
                embeddings=[vector],
                documents=[chunk],
                metadatas=[{
                    "competitor": doc["competitor"],
                    "category": doc["category"],
                    "title": doc["title"],
                    "url": doc["url"],
                }],
            )
            total_stored += 1

    print(f"  Stored {total_stored} chunks in ChromaDB")
    return total_stored


def query_rag(question, competitor, category=None):
    """Retrieve relevant chunks and generate answer using Gemini."""

    # Build metadata filter
    where_filter = {"competitor": competitor}
    if category:
        where_filter = {
            "$and": [
                {"competitor": competitor},
                {"category": category},
            ]
        }

    # Embed the question
    question_vector = embeddings.embed_query(question)

    # Retrieve top-5 relevant chunks
    results = collection.query(
        query_embeddings=[question_vector],
        n_results=5,
        where=where_filter,
    )

    # Extract chunks and sources
    chunks = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []

    if not chunks:
        return {
            "answer": "No relevant information found for this competitor.",
            "sources": [],
        }

    # Build context
    context = "\n\n".join(chunks)

    # Build prompt
    prompt = f"""You are a competitor intelligence analyst. Answer the question
based ONLY on the context below. If the context doesn't contain enough
information, say so honestly. Keep the answer concise and factual.

Context:
{context}

Question: {question}

Answer:"""

    # Generate answer
    response = llm.invoke(prompt)

    # Collect unique source URLs
    sources = list(set(m["url"] for m in metadatas if m.get("url")))

    # Handle both string and list-block response formats
    if isinstance(response.content, list):
        answer_text = " ".join(
            block.get("text", "") for block in response.content
        if isinstance(block, dict)
    ).strip()
    else:
        answer_text = response.content
    return {
    "answer": answer_text,
    "sources": sources,
    }


if __name__ == "__main__":
    # First fetch data
    from ingestion import fetch_competitor
    from database import init_db, add_competitor

    init_db()

    # Fetch and store
    data = fetch_competitor("Notion")
    total = store_documents(data)
    add_competitor("Notion", total)

    # Test query
    print("\n--- Testing RAG Query ---")
    result = query_rag("What new features has Notion launched?", "Notion", "product")
    print(f"\nAnswer: {result['answer']}")
    print(f"\nSources: {result['sources']}")