"""
llama.cpp server process manager.

Manages the lifecycle of a ``llama-server`` subprocess and exposes a
simple ``query()`` interface used by RAGLoader for LLM synthesis.
"""

import os
import subprocess
import time

import requests


class LLMRunner:
    """
    Manages a local ``llama-server`` (llama.cpp) subprocess.

    Starts the server on demand, polls its ``/health`` endpoint until
    ready, and shuts it down cleanly during application teardown.
    Exposes a ``query()`` method that sends prompts to ``/completion``.

    Attributes:
        model_path (str): Absolute path to the GGUF model file.
        context_size (int): Token context window size passed to llama-server.
        host (str): Host address llama-server binds to.
        port (int): Port llama-server listens on.
        n_gpu_layers (int): Number of model layers offloaded to GPU.
        threads (int): CPU threads used for inference.
        parallel (int): Parallel inference slots.
        use_mlock (bool): Whether to lock model weights in RAM.
        server_bin_path (str): Path to the ``llama-server`` binary.
        timeout (int): Seconds to wait for the server to become healthy.
        server_url (str): Base HTTP URL of the running server.
        process (subprocess.Popen | None): The managed server subprocess,
            or ``None`` if the server is not running.
    """

    def __init__(
        self,
        model_path: str,
        context_size: int,
        host: str,
        port: int,
        n_gpu_layers: int,
        threads: int,
        parallel: int,
        use_mlock: bool,
        server_bin_path: str,
        timeout: int = 60,
    ):
        """
        Initialise the runner with llama-server configuration.

        The server is *not* started at construction time. Call
        :meth:`start_server` explicitly (or via the FastAPI lifespan).

        Args:
            model_path (str): Absolute path to the GGUF model file.
            context_size (int): Token context window size.
            host (str): Host address for llama-server to bind to.
            port (int): Port for llama-server to listen on.
            n_gpu_layers (int): Model layers to offload to GPU (0 = CPU-only).
            threads (int): CPU threads for inference.
            parallel (int): Parallel inference slots.
            use_mlock (bool): Lock model weights in RAM.
            server_bin_path (str): Path or name of the llama-server binary.
            timeout (int): Maximum seconds to wait for the server to become
                healthy. Default: 60.
        """
        self.model_path = model_path
        self.context_size = context_size
        self.host = host
        self.port = port
        self.n_gpu_layers = n_gpu_layers
        self.threads = threads
        self.parallel = parallel
        self.use_mlock = use_mlock
        self.server_bin_path = server_bin_path
        self.timeout = timeout
        self.server_url = f"http://{host}:{port}"
        self.process: subprocess.Popen | None = None

    def start_server(self) -> bool:
        """
        Start the llama-server subprocess and wait for it to become healthy.

        If a server is already reachable at the configured host/port this
        method returns ``True`` immediately without spawning a new process.

        Returns:
            bool: ``True`` if the server is healthy and ready to accept
                requests; ``False`` if the model path is invalid or the
                server did not become healthy within ``self.timeout`` seconds.
        """
        if self._is_running():
            return True

        if not self.model_path or not os.path.exists(self.model_path):
            print(f"LLMRunner: model path not found: {self.model_path}")
            return False

        cmd = [
            self.server_bin_path,
            "-m", self.model_path,
            "-c", str(self.context_size),
            "--host", self.host,
            "--port", str(self.port),
            "-ngl", str(self.n_gpu_layers),
            "-t", str(self.threads),
            "--parallel", str(self.parallel),
        ]
        if self.use_mlock:
            cmd.append("--mlock")

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        deadline = time.time() + self.timeout
        while time.time() < deadline:
            if self._is_running():
                return True
            time.sleep(1)

        return False

    def stop_server(self) -> bool:
        """
        Terminate the managed llama-server subprocess.

        Sends ``SIGTERM`` and waits up to 10 seconds for a clean exit.
        If the process does not exit in time, ``SIGKILL`` is sent.
        The internal process reference is cleared in all cases.

        Returns:
            bool: ``True`` on success; ``False`` if an unexpected error
                occurred during termination.
        """
        if self.process is None:
            return True

        try:
            self.process.terminate()
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        except Exception as exc:
            print(f"LLMRunner: error stopping server: {exc}")
            return False
        finally:
            self.process = None

        return True

    def query(self, prompt: str, n_predict: int = 500) -> str:
        """
        Send a completion request to the running llama-server.

        Args:
            prompt (str): The full prompt string to send to the model.
            n_predict (int): Maximum number of tokens to generate.
                Default: 500.

        Returns:
            str: The generated text from the ``content`` field of the
                llama-server JSON response.

        Raises:
            requests.HTTPError: If the server returns a non-2xx status code.
            requests.Timeout: If the server does not respond within 120 seconds.
        """
        response = requests.post(
            f"{self.server_url}/completion",
            json={"prompt": prompt, "n_predict": n_predict},
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("content", "")

    def _is_running(self) -> bool:
        """
        Check whether the llama-server health endpoint is reachable.

        Returns:
            bool: ``True`` if ``GET /health`` returns HTTP 200; ``False``
                otherwise (connection refused, timeout, etc.).
        """
        try:
            r = requests.get(f"{self.server_url}/health", timeout=2)
            return r.status_code == 200
        except Exception:
            return False
