import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from ingestion import fetch_competitor
from retrieval import store_documents, query_rag
from classifier import predict_intent, load_classifier, train_classifier
from database import init_db, add_competitor, get_all_competitors

# Initialize
app = FastAPI(title="RivalRadar", description="Competitor Intelligence RAG Agent")
init_db()

# Load classifier once at startup
try:
    classifier_model = load_classifier()
except FileNotFoundError:
    print("Training classifier for first time...")
    classifier_model = train_classifier()


# --- Request Models ---
class CompetitorRequest(BaseModel):
    name: str

class QuestionRequest(BaseModel):
    question: str
    competitor: str
    category: Optional[str] = None  # If None, classifier picks it


# --- Endpoints ---

@app.get("/")
def root():
    return {"app": "RivalRadar", "status": "running"}


@app.post("/add-competitor")
def add_competitor_endpoint(req: CompetitorRequest):
    """Fetch competitor data via Tavily and store in ChromaDB."""
    try:
        # Fetch data
        data = fetch_competitor(req.name)
        if not data:
            raise HTTPException(status_code=404, detail=f"No data found for {req.name}")

        # Store in ChromaDB
        total_chunks = store_documents(data)

        # Save metadata to SQLite
        add_competitor(req.name, total_chunks)

        return {
            "message": f"Successfully ingested {req.name}",
            "documents_fetched": len(data),
            "chunks_stored": total_chunks,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask")
def ask_question(req: QuestionRequest):
    """Ask a question about a competitor. Auto-classifies intent if category not provided."""

    # Step 1: Classify intent if no category given
    if req.category:
        category = req.category
        confidence = 1.0
    else:
        intent = predict_intent(req.question, classifier_model)
        category = intent["category"]
        confidence = intent["confidence"]

    # Step 2: RAG retrieval + answer
    result = query_rag(req.question, req.competitor, category)

    return {
        "question": req.question,
        "competitor": req.competitor,
        "classified_intent": category,
        "confidence": f"{confidence:.2%}",
        "answer": result["answer"],
        "sources": result["sources"],
    }


@app.get("/competitors")
def list_competitors():
    """List all tracked competitors."""
    competitors = get_all_competitors()
    return {"competitors": competitors, "total": len(competitors)}


@app.post("/refresh")
def refresh_competitor(req: CompetitorRequest):
    """Re-fetch latest data for a competitor."""
    try:
        data = fetch_competitor(req.name)
        total_chunks = store_documents(data)
        add_competitor(req.name, total_chunks)
        return {
            "message": f"Refreshed data for {req.name}",
            "chunks_stored": total_chunks,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))