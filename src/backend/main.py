"""Uvicorn entry point for the FastAPI Commerce Agent API."""

from commerce_agent.api import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
