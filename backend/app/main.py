from fastapi import FastAPI

app = FastAPI(title="AI JLPT App API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
