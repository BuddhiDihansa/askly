import json, re
import asyncio
from groq import AsyncGroq
from app.core.config import settings

client = AsyncGroq(api_key=settings.groq_api_key) if settings.groq_api_key else None

async def chat(messages, temperature=0.2):
    if not client:
        return "Groq API key is not configured. Add GROQ_API_KEY to backend/.env."
    r = await asyncio.wait_for(
        client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            temperature=temperature,
        ),
        timeout=settings.ai_timeout_seconds,
    )
    return r.choices[0].message.content or ""

def parse_json(text: str):
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    m = re.search(r"\{.*\}|\[.*\]", text, flags=re.S)
    if not m: raise ValueError("No JSON found")
    return json.loads(m.group(0))
