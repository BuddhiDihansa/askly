# ASKLY V2 — AI-Powered Personalized Learning Assistant

A full-stack student project demonstrating RAG, hybrid retrieval, personalization, adaptive assessment, memory, web routing and cloud-ready architecture.

## Architecture

Next.js → FastAPI → AI Orchestrator → {Hybrid RAG, Web Search, Mastery, Memory} → Groq → grounded response + citations

## Included advanced features

- JWT authentication and user isolation
- MongoDB persistence
- PDF ingestion with page-aware extraction
- Overlapping document chunking
- Sentence-Transformer embeddings (`all-MiniLM-L6-v2`)
- Vector similarity retrieval
- BM25 lexical retrieval
- Reciprocal-rank-fusion hybrid retrieval
- RAG citations with document/page metadata
- Query routing for current/web questions
- Optional Tavily web search
- Conversation history (short-term memory)
- Persistent learning/mastery records (long-term learning memory)
- Adaptive quiz generation through Groq
- Difficulty selection from mastery
- Quiz scoring + mastery update loop
- Responsive dark learning dashboard
- Dockerfiles for deployment
- Clean separation of API, AI, services, schemas and database layers

## 1. Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`:
- `MONGODB_URI` = your MongoDB Atlas connection string
- `GROQ_API_KEY` = Groq API key
- `TAVILY_API_KEY` = optional Tavily key (leave blank if not using web search)

Run:

```powershell
uvicorn app.main:app --reload
```

API: http://localhost:8000
Swagger: http://localhost:8000/docs

## 2. Frontend

Install Node.js 20+.

```powershell
cd frontend
copy .env.example .env.local
npm install
npm run dev
```

Open http://localhost:3000

## Important first run

The first PDF upload downloads the `all-MiniLM-L6-v2` embedding model through Sentence Transformers. This can take some time and needs internet access once.

## MongoDB

The backend uses MongoDB Atlas. No vector-search index is required for this student-friendly implementation: embeddings are stored with chunks and cosine similarity is calculated in the service layer. This keeps setup simple while demonstrating the full retrieval pipeline. For a production scale-up, move retrieval to MongoDB Atlas Vector Search or a dedicated vector database.

## Viva-ready explanation

**Why hybrid RAG?** BM25 is strong for exact terms and course vocabulary; embeddings are stronger for semantic similarity. Combining both improves recall.

**Why reranking/fusion?** Different retrieval methods produce different rankings. Reciprocal Rank Fusion combines their evidence without depending on incompatible score scales.

**Why personalization?** ASKLY keeps a mastery estimate per topic. Quiz performance updates mastery, and future quizzes use that estimate to choose difficulty.

**Why web routing?** A student asking for a current event should not rely only on old uploaded notes. Current-looking queries can be routed to web search, while course questions use the student's material first.

**Why citations?** The response can expose which uploaded document and page supplied the retrieved evidence, improving trust and auditability.

## Production extensions (not required for the demo)

- Redis cache and background job queue
- Atlas Vector Search / dedicated vector DB
- Cross-encoder reranker
- LLM-based memory extraction and knowledge graph
- automated RAG evaluation dataset with Recall@K, MRR, faithfulness and answer relevance
- streaming responses
- object storage (S3/Cloudinary) instead of in-process upload
- observability/tracing
