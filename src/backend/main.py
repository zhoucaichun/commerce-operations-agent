"""Uvicorn entry point for the FastAPI Commerce Agent API."""

from commerce_agent.config import load_local_config

load_local_config()
from commerce_agent.api import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
