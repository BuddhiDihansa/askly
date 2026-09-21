# ASKLY V2: AI-Powered Personalized Learning Assistant

ASKLY is a full-stack personalized learning platform. It uses document-grounded retrieval, optional web search, learner mastery data, conversation memory, and Groq-powered generation to help students understand and practise course material.

## Architecture

Next.js -> FastAPI -> AI Orchestrator -> {Hybrid RAG, Web Search, Mastery, Memory} -> Groq -> grounded response + citations

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

## Project structure

```text
ASKLY-Hardened-v2/
├── backend/        FastAPI API, MongoDB access, RAG, AI services and tests
├── frontend/       Next.js web application
├── docker-compose.yml
└── README.md
```

## Requirements

- Python 3.11 or newer
- Node.js 20 or newer
- MongoDB Atlas or a local MongoDB server
- A Groq API key
- Internet access on the first run to download the embedding model

## Configuration

Create the backend environment file:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env` and set:

```dotenv
MONGODB_URI=your MongoDB connection string
JWT_SECRET=a random secret with at least 32 characters
GROQ_API_KEY=your Groq API key
GROQ_MODEL=qwen/qwen3.8-27b
```

`TAVILY_API_KEY` is optional. Leave it empty if web search is not required. The configured model must be available to your Groq account because model availability can change over time.

Never commit `.env` or expose API keys in frontend code.

## Run the backend

Run:

```powershell
uvicorn app.main:app --reload
```

API: http://localhost:8000
Swagger: http://localhost:8000/docs

Keep the backend terminal running.

## Run the frontend

Install Node.js 20+.

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

If the frontend needs a custom backend URL, create `frontend/.env.local`:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Important first run

The first PDF upload downloads the `all-MiniLM-L6-v2` embedding model through Sentence Transformers. This can take some time and needs internet access once.

## MongoDB

The backend uses MongoDB Atlas. No vector-search index is required for this student-friendly implementation: embeddings are stored with chunks and cosine similarity is calculated in the service layer. This keeps setup simple while demonstrating the full retrieval pipeline. For a production scale-up, move retrieval to MongoDB Atlas Vector Search or a dedicated vector database.

## Troubleshooting

### Chat returns `502 Bad Gateway`

The chat route uses 502 when an upstream AI or retrieval operation fails. Check the backend terminal for the original exception. Common causes include:

- The Groq model is unavailable for the configured API key.
- `GROQ_API_KEY` is missing, expired, or invalid.
- MongoDB is unreachable or the connection string is incorrect.
- The embedding model is still downloading on its first use.

After changing `.env`, restart Uvicorn so the new settings are loaded.

### Frontend cannot reach the backend

Confirm that both servers are running and that `NEXT_PUBLIC_API_URL` points to `http://localhost:8000`. Also check that the backend `FRONTEND_URL` includes `http://localhost:3000`.

### Run tests

Run backend tests from the `backend` directory:

```powershell
pytest
```

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
