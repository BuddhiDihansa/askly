# ASKLY — Start Here

1. Extract this ZIP.
2. Open the folder in VS Code.
3. Start MongoDB Atlas and copy the connection string.
4. In `backend`, create `.env` from `.env.example` and add MongoDB + Groq keys.
5. Create Python venv, install requirements, run `uvicorn app.main:app --reload`.
6. In `frontend`, create `.env.local` from `.env.example`, run `npm install`, then `npm run dev`.
7. Register a user.
8. Upload a PDF.
9. Ask a question about the PDF.
10. Generate a quiz for the same topic and submit it.
11. Open Progress and observe mastery updating.

This repository intentionally excludes virtual environments, node_modules and API secrets.
