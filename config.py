"""Central configuration. Credentials are read from the environment, never hard-coded."""
from pathlib import Path
import os

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
STORAGE_DIR = ROOT_DIR / "storage"
load_dotenv(ROOT_DIR / ".env")

WATSONX_API_KEY = os.getenv("WATSONX_API_KEY", "").strip()
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "").strip()
WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com").strip()
WATSONX_MODEL_ID = os.getenv("WATSONX_MODEL_ID", "ibm/granite-3-3-8b-instruct").strip()
WATSONX_EMBEDDING_MODEL_ID = os.getenv(
    "WATSONX_EMBEDDING_MODEL_ID", "ibm/slate-30m-english-rtrvr"
).strip()
RAG_EMBEDDING_PROVIDER = os.getenv("RAG_EMBEDDING_PROVIDER", "local").strip().lower()
ALLOW_OFFLINE_FALLBACK = os.getenv("ALLOW_OFFLINE_FALLBACK", "true").strip().lower() == "true"


def watsonx_is_configured() -> bool:
    """Return True only when the three required connection settings are present."""
    return bool(WATSONX_API_KEY and WATSONX_PROJECT_ID and WATSONX_URL)


def public_configuration() -> dict:
    """Return non-secret settings for display in the UI; never return the API key."""
    return {
        "configured": watsonx_is_configured(),
        "url": WATSONX_URL,
        "model_id": WATSONX_MODEL_ID,
        "embedding_model_id": WATSONX_EMBEDDING_MODEL_ID,
        "embedding_provider": RAG_EMBEDDING_PROVIDER,
        "fallback_enabled": ALLOW_OFFLINE_FALLBACK,
    }
