from fastapi import FastAPI

app = FastAPI(title="Askly API")


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Askly backend is running"}