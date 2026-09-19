import httpx

from app.core.config import settings


async def search_web(query: str) -> list[dict]:
    if not settings.tavily_api_key:
        return []

    try:
        async with httpx.AsyncClient(timeout=15) as http_client:
            response = await http_client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": 5,
                },
            )
            response.raise_for_status()
            return response.json().get("results", [])
    except (httpx.HTTPError, httpx.TimeoutException):
        # if Tavily is down or slow, degrade gracefully to "no web results"
        # rather than failing the whole chat request - the student still
        # gets an answer from their documents + the LLM's own knowledge
        return []
