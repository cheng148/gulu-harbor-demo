from fastapi import FastAPI

app = FastAPI(title="咕噜港 AI 选宠顾问")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "gulu-port-agent"}
