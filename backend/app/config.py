"""
Application configuration module.

Loads settings from a .env file (via python-dotenv) and environment variables,
then returns a typed Settings object used throughout the application.
All path fields resolve relative to the backend root when not explicitly set.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    """
    Application settings loaded from environment variables.

    Instantiated by get_settings() and passed to the FastAPI lifespan
    context. All fields are read-only after construction.

    Attributes:
        app_host (str): Host address FastAPI binds to. Default: ``127.0.0.1``.
        app_port (int): Port FastAPI listens on. Default: ``8000``.
        data_dir (str): Directory scanned for ``.md`` and ``.txt`` documents.
            Defaults to ``<backend>/data`` when not set in the environment.
        vector_db_dir (str): Directory used for TF-IDF cache files.
            Defaults to ``<backend>/vector_db_cache`` when not set.
        enable_llm (bool): Whether to start an LLM backend at startup.
            Default: ``False``.
        llm_backend (str): Active LLM backend selector.
            Accepted values: ``"llama_cpp"`` (default) or ``"ollama"``.
        model_path (str): Absolute path to a GGUF model file.
            Required when ``llm_backend="llama_cpp"``.
        llama_server_bin (str): Path or name of the ``llama-server`` binary.
            Default: ``"llama-server"`` (assumes it is on PATH).
        llama_host (str): Host address llama-server binds to. Default: ``127.0.0.1``.
        llama_port (int): Port llama-server listens on. Default: ``8080``.
        llama_context_size (int): Token context window for llama-server. Default: ``2048``.
        llama_gpu_layers (int): Model layers offloaded to GPU. ``0`` = CPU-only.
        llama_threads (int): CPU threads used for inference. Default: ``4``.
        llama_parallel (int): Parallel inference slots. Default: ``1``.
        llama_use_mlock (bool): Lock model weights in RAM. Default: ``False``.
        ollama_host (str): Host address of the Ollama service. Default: ``127.0.0.1``.
        ollama_port (int): Port of the Ollama service. Default: ``11434``.
        ollama_model (str): Ollama model identifier to use (e.g. ``"llama3"``).
    """

    def __init__(self, **kwargs):
        """
        Initialise Settings from keyword arguments.

        Args:
            **kwargs: Arbitrary keyword arguments that become instance attributes.
                Typically supplied by get_settings().
        """
        for key, value in kwargs.items():
            setattr(self, key, value)


def get_settings() -> Settings:
    """
    Load and return application settings from the environment.

    Reads ``<backend>/.env`` with python-dotenv (non-overriding), then
    reads environment variables with safe defaults. ``DATA_DIR`` and
    ``VECTOR_DB_DIR`` resolve to subdirectories of the backend root when
    left blank.

    Returns:
        Settings: Fully populated settings object ready for application use.
    """
    # Load .env — does not override variables already set in the environment
    load_dotenv(BASE_DIR / ".env")

    # Resolve optional path overrides; fall back to backend-relative defaults
    data_dir = os.getenv("DATA_DIR") or str(BASE_DIR / "data")
    vector_db_dir = os.getenv("VECTOR_DB_DIR") or str(BASE_DIR / "vector_db_cache")

    return Settings(
        # Server
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        # Storage paths
        data_dir=data_dir,
        vector_db_dir=vector_db_dir,
        # LLM feature flag and backend selector
        enable_llm=os.getenv("ENABLE_LLM", "false").lower() == "true",
        llm_backend=os.getenv("LLM_BACKEND", "llama_cpp").lower(),
        # llama.cpp / llama-server settings
        model_path=os.getenv("MODEL_PATH", ""),
        llama_server_bin=os.getenv("LLAMA_SERVER_BIN", "llama-server"),
        llama_host=os.getenv("LLAMA_HOST", "127.0.0.1"),
        llama_port=int(os.getenv("LLAMA_PORT", "8080")),
        llama_context_size=int(os.getenv("LLAMA_CONTEXT_SIZE", "2048")),
        llama_gpu_layers=int(os.getenv("LLAMA_GPU_LAYERS", "0")),
        llama_threads=int(os.getenv("LLAMA_THREADS", "4")),
        llama_parallel=int(os.getenv("LLAMA_PARALLEL", "1")),
        llama_use_mlock=os.getenv("LLAMA_USE_MLOCK", "false").lower() == "true",
        # Ollama settings
        ollama_host=os.getenv("OLLAMA_HOST", "127.0.0.1"),
        ollama_port=int(os.getenv("OLLAMA_PORT", "11434")),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3"),
    )
