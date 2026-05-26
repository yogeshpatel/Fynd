"""
Ollama API client.

Provides a lightweight wrapper around the Ollama REST API for LLM
inference. Unlike LLMRunner, this class does not manage any subprocess —
Ollama is assumed to be running as a standalone service (``ollama serve``
or via the Ollama desktop app).
"""

import requests


class OllamaRunner:
    """
    Queries a running Ollama service for LLM completions.

    Implements the same interface as ``LLMRunner`` (``start_server``,
    ``stop_server``, ``query``) so both backends are interchangeable
    from the perspective of :class:`~app.rag_loader.RAGLoader`.

    ``start_server`` does *not* launch a process — it only verifies that
    the Ollama service is reachable and prints instructions if it is not.
    ``stop_server`` is a no-op since Ollama is managed externally.

    Attributes:
        host (str): Host address of the Ollama service.
        port (int): Port of the Ollama service. Default: ``11434``.
        model (str): Ollama model identifier to use (e.g. ``"llama3"``).
        base_url (str): Base HTTP URL derived from host and port.
    """

    def __init__(self, host: str, port: int, model: str):
        """
        Initialise the Ollama runner.

        Args:
            host (str): Host address where Ollama is listening.
            port (int): Port where Ollama is listening.
            model (str): Model name as registered in Ollama
                (e.g. ``"llama3"``, ``"mistral"``). Run ``ollama list``
                to see installed models.
        """
        self.host = host
        self.port = port
        self.model = model
        self.base_url = f"http://{host}:{port}"

    def is_available(self) -> bool:
        """
        Check whether the Ollama service is reachable.

        Sends a ``GET /api/tags`` request which returns the list of
        installed models when Ollama is healthy.

        Returns:
            bool: ``True`` if Ollama responds with HTTP 200; ``False``
                if the service is not running or unreachable.
        """
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def start_server(self) -> bool:
        """
        Verify that the Ollama service is reachable.

        This method does **not** start a process. If Ollama is not running
        it prints actionable instructions and returns ``False``.

        Returns:
            bool: ``True`` if Ollama is reachable; ``False`` otherwise.
        """
        if self.is_available():
            return True

        print(
            f"OllamaRunner: Ollama is not reachable at {self.base_url}.\n"
            "  Start the service:   ollama serve\n"
            f"  Pull the model:      ollama pull {self.model}"
        )
        return False

    def stop_server(self) -> bool:
        """
        No-op — Ollama is managed externally and is not stopped here.

        Returns:
            bool: Always ``True``.
        """
        return True

    def query(self, prompt: str, n_predict: int = 500) -> str:
        """
        Send a generate request to the Ollama ``/api/generate`` endpoint.

        Args:
            prompt (str): The full prompt string to send to the model.
            n_predict (int): Maximum number of tokens to generate
                (passed as ``options.num_predict``). Default: 500.

        Returns:
            str: The generated text from the ``response`` field of the
                Ollama JSON response.

        Raises:
            requests.HTTPError: If Ollama returns a non-2xx status code.
            requests.Timeout: If Ollama does not respond within 120 seconds.
        """
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": n_predict},
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("response", "")
