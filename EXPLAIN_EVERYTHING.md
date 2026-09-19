# ASKLY — Explain Everything
### A defense document: every design decision, why it was made, and what to say if asked "why?"

This document exists so you can defend every line of this project in a viva or job interview
without having to say "an AI generated it." Read it once fully, then use it as a reference —
you don't need to memorize it, you need to *understand* it well enough to explain it in your
own words.

---

## 1. The Big Picture

Askly is a **modular monolith**: one FastAPI backend process containing several logically
separate modules (auth, chat, documents/RAG, quiz, progress), rather than several independently
deployed microservices.

**If asked "why not microservices?"**
> "Microservices make sense when different parts of a system need to scale independently, or
> when different teams own different parts. For a solo-built project at this stage, that overhead
> (service discovery, network calls between services, multiple deployments) isn't justified.
> A modular monolith gives me the same clean separation of concerns in code — auth, RAG, chat,
> quiz are all separate modules — but as one deployable unit. If a specific module ever needed to
> scale independently (e.g. embeddings generation became a bottleneck), it's structured cleanly
> enough to extract into its own service later."

---

## 2. Authentication — `core/security.py`, `api/auth.py`, `api/dependencies.py`

**What it does:** Register/login with email+password. Passwords are hashed with **bcrypt**
(never stored in plain text). On successful login, a **JWT** (JSON Web Token) is issued and the
frontend stores it, sending it on every subsequent request via the `Authorization: Bearer <token>`
header.

**Why JWT instead of server-side sessions?**
> "JWT is stateless — the server doesn't need to store session data anywhere, the token itself
> contains the user's identity (their `sub` claim) and is cryptographically signed so it can't be
> tampered with. This makes horizontal scaling simpler (any server instance can verify any token
> without shared session storage). The trade-off is that a JWT can't be easily revoked before it
> expires — if I needed instant logout/revocation, I'd need a token blocklist or move to
> short-lived tokens with refresh tokens."

**Why bcrypt for passwords?**
> "bcrypt is a one-way hashing function designed specifically for passwords — it's deliberately
> slow (to resist brute-force attacks) and includes a random 'salt' automatically, so two users
> with the same password get different hashes. Even if the database were breached, an attacker
> can't reverse the hash back into the original password."

**The security fix I made:** the original code had `jwt_secret: str = "change-me"` as a default.
That means if `.env` was ever misconfigured, the app would silently run with a publicly-known
secret string, letting anyone forge a valid login token for any user. I removed the default,
making `jwt_secret` a required field — the app now refuses to start at all if it's missing,
rather than running insecurely.

**Why the same error message for "wrong password" and "no such user"?**
> "If the login endpoint said 'no account with that email' vs 'wrong password' as different
> messages, an attacker could use that to enumerate which emails are registered on the system.
> Returning the same generic 'Invalid email or password' for both closes that information leak."

---

## 3. Rate Limiting — `core/rate_limit.py`

**What it does:** Tracks how many requests a given key (IP for login/register, user ID for
chat/quiz) has made in the last 60 seconds, using a simple in-memory sliding window.

**Why this matters:**
> "Login and register are rate-limited per IP to slow down brute-force / credential-stuffing
> attacks. Chat and quiz generation are rate-limited per user because those endpoints call paid
> external APIs (Groq, Tavily) — without a limit, one compromised or malicious account could run
> up the API bill or hammer the server."

**Why in-memory instead of Redis?**
> "This runs as a single backend process right now, so a plain in-memory counter is enough to
> stop obvious abuse. The known limitation is that it resets on restart, and wouldn't work
> correctly across multiple server instances behind a load balancer — each instance would have
> its own counters. If this scaled to multiple instances, I'd move this to Redis so all instances
> share the same counters."

---

## 4. RAG (Retrieval-Augmented Generation) — `services/retrieval.py`, `services/embeddings.py`, `api/documents.py`

This is the most algorithmically interesting part of the project. Understand this section well.

### 4a. What problem RAG solves
LLMs only know what was in their training data, and don't know anything about a specific
student's uploaded documents. RAG lets the LLM answer questions grounded in documents the student
actually uploaded, by finding the most relevant *chunks* of text and giving them to the LLM as
context before it answers.

### 4b. Chunking — why not just feed the whole document to the LLM?
> "Two reasons: LLMs have a limited context window (a token budget), so a long document might not
> fit at all. And even if it fit, giving the model a 50-page document to find one relevant
> paragraph in is wasteful and can dilute the answer quality. Instead, documents are split into
> ~900-character overlapping chunks (120-character overlap) at upload time, each tagged with its
> page number. At query time, only the most relevant handful of chunks are retrieved and given to
> the LLM."

**Why overlap between chunks?**
> "Without overlap, a sentence that happens to fall right at a chunk boundary gets split in half,
> and neither half fully captures its meaning. Overlap means that content near a boundary appears
> intact in at least one of the two neighboring chunks."

### 4c. Hybrid retrieval — why two search methods, not one?
Two different retrieval strategies are combined:
- **Semantic search**: converts the query and every chunk into a vector (embedding) using a
  sentence-transformer model, then ranks chunks by cosine similarity to the query vector. This
  catches chunks that mean the same thing as the query even with completely different wording.
- **Lexical search (BM25)**: a classic keyword-ranking algorithm. This catches exact-term matches
  — specific names, codes, numbers — that semantic search can sometimes miss or under-rank.

**If asked "why not just use embeddings alone?"**
> "Embeddings are excellent at matching meaning but can sometimes miss exact keyword matches,
> especially for specific terms, names, or numbers that don't have strong 'semantic' neighbors.
> BM25 is the opposite — great at exact term matching, weak at synonyms or paraphrasing. Combining
> both and fusing their rankings gets the strengths of each."

### 4d. Reciprocal Rank Fusion (RRF) — the actual fusion math
```python
rrf_score = SEMANTIC_WEIGHT / (RRF_K + semantic_rank) + LEXICAL_WEIGHT / (RRF_K + lexical_rank)
```
**Why fuse by *rank position*, not raw score?**
> "BM25 scores and cosine similarity scores are on completely different scales — a BM25 score
> might be 12.4, a cosine similarity is always between -1 and 1. You can't directly average or
> compare numbers on different scales. RRF sidesteps this by using each chunk's *rank position*
> (1st, 2nd, 3rd...) in each list instead of its raw score. A chunk ranked #1 by both methods gets
> the highest fused score; a chunk only found by one method still gets partial credit."

**Why is the constant `RRF_K = 60`?**
> "It's the standard value from the original RRF paper (Cormack et al., 2009). It's a damping
> constant — without it, the difference between rank #1 and rank #2 would be huge (1/1 vs 1/2 is
> a 50% drop), which overweights small differences at the top of the list. Adding 60 to both
> smooths that out, so rank position matters, but not in an extreme, unstable way."

**Why is the weighting 0.6 semantic / 0.4 lexical, not 50/50?**
> "For a study assistant answering conceptual questions, matching the *meaning* of what a student
> is asking usually matters slightly more than matching their exact wording — so semantic search
> gets a bit more weight. This is a tunable parameter, not a law of nature; a different domain
> (e.g. legal document search, where exact terms matter a lot) might reasonably weight lexical
> search higher instead."

### 4e. Why normalize embeddings (`normalize_embeddings=True`)?
> "When every embedding vector is scaled to length 1 (unit length), cosine similarity between two
> vectors becomes mathematically equivalent to a simple dot product — cheaper to compute, same
> result. It's a standard optimization, not a shortcut that changes correctness."

---

## 5. Hallucination Control — `services/orchestrator.py`

**The concern this addresses:** LLMs can "hallucinate" — state something confidently that isn't
actually true or isn't actually in the provided evidence.

**How this project addresses it:**
1. The system prompt explicitly tells the model to prefer the retrieved document evidence over
   its own general knowledge for course material.
2. Critically, it also gives the model **explicit permission to say "I don't know"**:
   *"If the evidence provided does not answer the question, say so explicitly rather than
   guessing."* Without this instruction, a model under pressure to "be helpful" will often guess
   rather than admit uncertainty.
3. Document-sourced context and web-search context are labeled separately in the prompt, so the
   model (and the answer it gives) can distinguish "from your course materials" vs "from the web."

**If asked "how do you know the LLM actually follows this instruction?"**
> "Prompt instructions are a strong influence but not a hard guarantee — this is a genuine
> limitation of current LLMs, not something fully solved by prompt engineering alone. A more
> rigorous approach (not yet implemented here) would be to programmatically verify that claims in
> the answer are actually supported by the retrieved chunks — sometimes called 'citation
> verification' — and flag or suppress unsupported claims."

---

## 6. Adaptive Quiz Generation — `api/quiz.py`

**What it does:** Generates multiple-choice questions on a topic, at a difficulty level chosen
automatically based on the student's current mastery of that topic (beginner / intermediate /
advanced), using retrieved document context so questions are grounded in the student's own
material where possible.

**Why strip `answer` and `explanation` before sending questions to the frontend?**
> "If the answer key were included in the API response, a student could just open their browser's
> network tab and read the correct answers directly, defeating the purpose of the quiz. The
> answer is only used server-side, when the student submits their responses in `/quiz/submit`."

---

## 7. Mastery Tracking — `services/mastery.py`

**What it does:** After each quiz, updates a 0.0–1.0 "mastery" score per topic using an
**Exponential Moving Average (EMA)**:
```python
updated_mastery = previous_mastery * 0.7 + quiz_score * 0.3
```

**Why EMA instead of a simple average of all quiz scores ever taken?**
> "A plain average would weight a quiz from months ago exactly as heavily as today's quiz. EMA
> weights recent performance more heavily (here, each new result contributes 30% of the update),
> so the score reflects how the student is doing *now* — a bad quiz from long ago doesn't
> permanently drag the score down once the student has improved."

**Why does a new topic start at 0.25, not 0.0?**
> "Starting at 0.0 would mean the very first quiz on a topic is assumed to be for a total
> beginner, making it maximally easy regardless of the student's actual first-attempt
> performance. 0.25 is a more neutral starting point."

**This is genuinely "ML"-adjacent, but be honest about scope:**
> "This is a rule-based/statistical update (EMA), not a trained machine learning model — there's
> no model being trained on data here. It's a reasonable, explainable first version of mastery
> tracking. A more advanced version could use something like Bayesian Knowledge Tracing or an
> actual trained model on quiz-response data, but that requires substantially more data than a
> single-user or early-stage system would have."

---

## 8. Error Handling & Hardening — what was fixed and why

| Issue found | Fix | Why it mattered |
|---|---|---|
| `jwt_secret` had an insecure default | Made required, no default | Prevented token forgery if `.env` misconfigured |
| No upload size limit enforced | Added `max_upload_mb` check before parsing | Prevented memory exhaustion / cost abuse from huge files |
| Corrupt PDF crashed with 500 | Catch `PdfReadError`, return 400 | Client gets a clear, actionable error instead of a server crash |
| Invalid `ObjectId` (bad ID format) crashed with 500 | Catch `InvalidId`, return 400 | Same principle — malformed input shouldn't crash the server |
| Web search failure crashed the whole chat request | Catch `httpx` errors, degrade to empty results | Chat still works (using documents + LLM knowledge) even if Tavily is down |
| Internal exceptions/LLM raw output leaked to client on quiz/chat failure | Generic error message returned instead | Avoids leaking internals; still logs full detail server-side (in a real deployment, add proper logging here) |
| No rate limiting anywhere | Added to login, register, chat, quiz | Prevents brute-force and API-cost abuse |
| Missing `email-validator` dependency | Added to requirements.txt | `pydantic.EmailStr` silently depends on this; app would crash on startup without it |

---

## 9. Known Limitations (be upfront about these — it builds credibility, not doubt)

- **Frontend stores the JWT in `localStorage`**, which is readable by any JavaScript on the page
  (an XSS vulnerability vector). An httpOnly cookie is the more production-hardened alternative.
- **Rate limiting is in-memory**, not shared across multiple server instances.
- **Vector search is done in-application (loading all of a user's chunks into memory and scoring
  them one by one)**, not via a dedicated vector database or MongoDB Atlas Vector Search. This is
  fine at small scale (a handful of documents per user) but wouldn't scale well to thousands of
  documents per user.
- **No CI/CD pipeline** configured yet (e.g. GitHub Actions running tests automatically on push).
- **No structured logging/monitoring** for a real production deployment (currently just print
  statements and FastAPI's default error responses).
- **Citation verification is not implemented** — the model is *instructed* not to hallucinate
  citations, but nothing programmatically double-checks that its citations are accurate.

Saying "here's what I'd improve with more time" in an interview is a *strength signal*, not a
weakness — it shows you understand the difference between a working demo and a production system.

---

## 10. Quick Reference — "Why did you choose X over Y?" cheat sheet

| Question | One-line answer |
|---|---|
| MongoDB vs PostgreSQL? | Document model fits variable-shaped data (chat messages, quiz questions) more naturally than rigid relational tables |
| Groq vs OpenAI/Anthropic? | Much faster inference (specialized hardware), lower cost, good enough quality for this use case |
| JWT vs sessions? | Stateless, scales horizontally without shared session storage |
| bcrypt vs plain hashing (e.g. SHA-256)? | bcrypt is deliberately slow + auto-salted, specifically designed to resist password-cracking; SHA-256 is fast and NOT designed for passwords |
| BM25 + embeddings vs embeddings alone? | Covers both exact keyword matches and semantic/meaning matches |
| RRF vs averaging raw scores? | BM25 and cosine scores are on incomparable scales; RRF fuses by rank position instead |
| EMA vs simple average for mastery? | Weights recent performance more heavily, so score reflects current ability |
| Modular monolith vs microservices? | Right-sized for current scale/team-size; extractable later if needed |
