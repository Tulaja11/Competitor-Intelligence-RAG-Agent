# RivalRadar

Track what your competitors are doing — without spending hours googling.

RivalRadar fetches real-time competitor data (product launches, hiring activity, pricing changes) and lets you ask questions in plain English. A trained ML classifier routes your question to the right data, and a RAG pipeline pulls the answer from indexed competitor content with source links.

## How it works

1. Add a competitor name → Tavily API searches for their product updates, job postings, and pricing info
2. Results get chunked, embedded (Gemini), and stored in ChromaDB with metadata tags
3. You ask a question → Scikit-learn classifier detects intent (Product / Hiring / Pricing)
4. ChromaDB retrieval is filtered by competitor + predicted category
5. Gemini Flash generates an answer from the retrieved chunks

## Features

- **Ask tab** — chat with any tracked competitor, quick insight buttons for common queries
- **Compare tab** — ask the same question to two competitors side by side
- **Dashboard tab** — see all tracked competitors, chunk counts, last updated timestamps
- **Refresh** — one-click re-fetch to get latest data for any competitor
- **Intent classification** — 84% cross-validation accuracy across 3 categories, trained on 90 labeled examples

Started with 4 intent categories but cross-validation showed "News" overlapping with the other three. Dropped it, accuracy went from 69% to 84%. The classifier uses TF-IDF + LinearSVC.

## Tech stack

- **RAG:** LangChain + ChromaDB + Gemini embeddings
- **Search:** Tavily API (product, hiring, pricing searches per competitor)
- **ML:** Scikit-learn (TF-IDF + LinearSVC with CalibratedClassifierCV)
- **LLM:** Google Gemini Flash
- **API:** FastAPI (4 endpoints — add, ask, list, refresh)
- **Frontend:** Streamlit
- **Storage:** SQLite for competitor metadata
