# ASKLY — AI Learning Platform

ASKLY is a personalized learning assistant that turns your own study materials (PDF notes, textbooks, lecture slides) into an interactive study workspace: ask questions grounded in your documents, generate adaptive quizzes, review spaced-repetition flashcards, track topic mastery, and get a personalized study plan.

Built with a hybrid RAG (Retrieval-Augmented Generation) pipeline, so answers are grounded in the material you actually uploaded — not just the model's general knowledge.

---

## ✨ Features

- **AI Tutor Chat** — Ask questions and get answers grounded in your uploaded documents, with page-level citations. Falls back to the model's general knowledge when no document evidence is found, and can pull in live web results for current-events questions.
- **Document Intelligence** — Upload PDFs and ASKLY automatically splits them into page-aware chunks, detects chapters/sections, and builds embeddings for semantic search.
- **Hybrid Retrieval** — Combines semantic search (embeddings + cosine similarity) with lexical search (BM25 keyword matching), then reranks and deduplicates results for the most relevant context.
- **Adaptive Quizzes** — Generates multiple-choice quizzes at a difficulty level that adapts to your current mastery of the topic.
- **Spaced-Repetition Flashcards** — Auto-generated flashcards from your documents, reviewed on an SM-2-style spaced repetition schedule.
- **Mastery Tracking** — Topic mastery is tracked with an exponential moving average (EMA), weighting recent quiz performance more heavily than old attempts.
- **Study Planner** — Generates a day-by-day study plan prioritizing your weakest topics.
- **Notifications** — Review reminders and quiz result summaries.
- **Admin Dashboard** — Platform-wide usage stats for admin accounts.
- **Auth & Security** — JWT authentication, bcrypt password hashing, per-user rate limiting, upload validation, and security headers.

---

## 🏗️ Tech Stack

**Backend**
- FastAPI (Python) — REST API
- MongoDB (via Motor, async driver) — data storage
- Groq (Llama 3.3 70B) — LLM inference
- Tavily API — optional live web search
- Sentence-Transformers (`all-MiniLM-L6-v2`) — embeddings
- rank-bm25 — lexical/keyword search
- JWT (python-jose) + bcrypt — authentication

**Frontend**
- Next.js 14 (App Router) + React 18
- TypeScript
- Recharts — progress visualizations
- lucide-react — icons

**Infrastructure**
- Docker & docker-compose
- pytest + pytest-asyncio + mongomock-motor — backend test suite

---

## 🧠 How the RAG Pipeline Works

```
User question
     │
     ▼
1. Hybrid retrieval over the user's own document chunks
   ├─ Semantic search  → embeddings + cosine similarity
   └─ Lexical search   → BM25 keyword matching
     │
     ▼
2. Rerank & deduplicate candidates → top-k most relevant chunks
     │
     ▼
3. Build a grounded context block (with source, page, chapter, section)
     │
     ▼
4. Groq (Llama 3.3) answers using that evidence, with citations
   (falls back to general knowledge or live web search if no
   document evidence is found)
```

All retrieval is scoped per-user — one account can never retrieve another account's documents.

---

## 📂 Project Structure

```
askly-main/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI route handlers (auth, chat, documents, quiz, ...)
│   │   ├── services/       # RAG pipeline, retrieval, reranking, mastery, orchestration
│   │   ├── core/           # config, security, rate limiting
│   │   ├── db/              # MongoDB connection & collections
│   │   └── schemas/         # Pydantic request/response models
│   ├── tests/               # unit + integration tests (pytest)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # shared UI components
│   ├── lib/                 # API client
│   └── .env.example
└── docker-compose.yml
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [MongoDB Atlas](https://www.mongodb.com/atlas) cluster (free tier works)
- A [Groq API key](https://console.groq.com) (free tier available)
- *(Optional)* A [Tavily API key](https://tavily.com) for live web search

### 1. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and set:

```env
MONGODB_URI=your_mongodb_connection_string
JWT_SECRET=a_random_string_at_least_32_characters_long
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key   # optional
```

Run the API:

```bash
uvicorn app.main:app --reload
```

The backend runs at `http://localhost:8000`. Interactive API docs: `http://localhost:8000/docs`.

### 2. Frontend setup

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

The app runs at `http://localhost:3000`.

### 3. Run with Docker (alternative)

```bash
docker-compose up --build
```

---

## 🧪 Running Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Tests use `mongomock-motor` to mock MongoDB, so no live database connection is required to run the suite.

---

## 🔐 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `MONGODB_URI` | ✅ | MongoDB connection string |
| `JWT_SECRET` | ✅ | Secret for signing JWTs (min. 32 characters) |
| `GROQ_API_KEY` | ✅ | Groq API key for LLM inference |
| `TAVILY_API_KEY` | ❌ | Enables live web search for current-events questions |
| `NEXT_PUBLIC_API_URL` | ✅ (frontend) | Backend base URL |

---

## ⚠️ Known Limitations

- JWT is stored in `localStorage` on the frontend; migrating to httpOnly cookies would be more XSS-resistant for a production deployment.
- The rate limiter is in-memory and per-process — it won't coordinate correctly across multiple backend instances behind a load balancer. A Redis-backed limiter would be needed to scale horizontally.
- Vector search is done in-application over MongoDB documents rather than a dedicated vector database. This is fine at small-to-moderate scale but would benefit from MongoDB Atlas Vector Search for very large document libraries.

---

## 📄 License

Add your license here.
