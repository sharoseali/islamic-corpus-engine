"""Open-source embedding and reranking models (local, offline).

The models are measuring instruments for meaning: they read our stored
passages and a user's query and return numbers (vectors, relevance scores).
They never produce text and nothing from them is shown to users.

The embedder runs the multilingual-e5-large ONNX model directly through
onnxruntime (tokenizer + mean pooling + L2 normalisation), which gives
control over threads, batching by length and the exact model files. It
runs on a CUDA GPU when one is available (EMBEDDING_DEVICE), in full
precision so the vectors match a CPU build, and on the CPU otherwise. Model
directories live under EMBEDDING_CACHE_DIR as plain files; the files in use
are pinned by sha256 (see model_file_checksums) and recorded in
search.embedding_state by the indexer.

Models load lazily on first use and are shared across requests.
"""

import hashlib
import threading
from pathlib import Path

import numpy as np

from app.core.config import get_settings

# e5 models are trained with these prefixes; omitting them hurts retrieval.
QUERY_PREFIX = "query: "
PASSAGE_PREFIX = "passage: "

MAX_TOKENS = 512
PAD_ID = 1  # XLM-R <pad>

_embedder = None
_reranker = None
_lock = threading.Lock()


class SemanticUnavailable(RuntimeError):
    """The embedding stack (model files or runtime) is not available."""


def _cache_dir() -> Path:
    path = Path(get_settings().EMBEDDING_CACHE_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _threads() -> int | None:
    n = get_settings().EMBEDDING_THREADS
    return n if n > 0 else None


def _is_out_of_memory(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "out of memory" in msg or "failed to allocate" in msg or "cudaerrormemoryallocation" in msg


# Shared libraries the CUDA provider needs, in dependency order, relative to
# a directory laid out like pip's "nvidia" namespace package.
_CUDA_LIBS = (
    "nvjitlink/lib/libnvJitLink.so.12",
    "cuda_runtime/lib/libcudart.so.12",
    "cuda_nvrtc/lib/libnvrtc.so.12",
    "cublas/lib/libcublasLt.so.12",
    "cublas/lib/libcublas.so.12",
    "cudnn/lib/libcudnn.so.9",
    "cufft/lib/libcufft.so.11",
    "curand/lib/libcurand.so.10",
)


def _preload_cuda_libraries(lib_dir: str) -> None:
    """Load the CUDA libraries into the process before onnxruntime asks for them.

    The dynamic loader reuses an already loaded library of the same name, so
    this lets the provider run against libraries that are not on the system
    library path: a directory given by EMBEDDING_CUDA_LIB_DIR, or else the
    nvidia-*-cu12 packages pip installed into this environment.
    """
    import ctypes

    import onnxruntime as ort

    if lib_dir:
        root = Path(lib_dir)
        for rel in _CUDA_LIBS:
            path = root / rel
            if path.exists():
                ctypes.CDLL(str(path), mode=ctypes.RTLD_GLOBAL)
        # cuDNN 9 is split into sub-libraries it opens by name.
        for path in sorted((root / "cudnn" / "lib").glob("libcudnn_*.so.9")):
            ctypes.CDLL(str(path), mode=ctypes.RTLD_GLOBAL)
    elif hasattr(ort, "preload_dlls"):
        ort.preload_dlls(directory="")


def _open_session(model_path: Path, opts, device: str, cuda_lib_dir: str = ""):
    """Create the onnxruntime session on the requested device.

    "auto" tries the GPU and quietly falls back to the CPU (no GPU, no
    onnxruntime-gpu, or no free GPU memory, e.g. while an index build holds
    it); "cuda" fails instead; "cpu" never tries. The CUDA session runs with
    TF32 disabled so GPU and CPU vectors agree to float precision.
    """
    import onnxruntime as ort

    if device not in ("auto", "cuda", "cpu"):
        raise SemanticUnavailable(f"unknown EMBEDDING_DEVICE {device!r}")
    if device != "cpu" and "CUDAExecutionProvider" in ort.get_available_providers():
        try:
            _preload_cuda_libraries(cuda_lib_dir)
            providers = [
                ("CUDAExecutionProvider", {"device_id": 0, "use_tf32": 0}),
                "CPUExecutionProvider",
            ]
            session = ort.InferenceSession(str(model_path), opts, providers=providers)
            if session.get_providers()[0] == "CUDAExecutionProvider":
                return session, "cuda"
        except Exception as exc:
            if device == "cuda":
                raise SemanticUnavailable(f"CUDA embedding unavailable: {exc}") from exc
    elif device == "cuda":
        raise SemanticUnavailable("CUDA embedding requested but onnxruntime has no CUDA provider")
    return ort.InferenceSession(str(model_path), opts, providers=["CPUExecutionProvider"]), "cpu"


class OnnxEmbedder:
    """Sentence embeddings from a local ONNX text encoder with mean pooling."""

    def __init__(
        self,
        model_dir: Path,
        threads: int | None = None,
        device: str = "auto",
        cuda_lib_dir: str = "",
    ):
        try:
            import onnxruntime as ort
            from tokenizers import Tokenizer
        except ImportError as exc:
            raise SemanticUnavailable("onnxruntime/tokenizers are not installed") from exc
        if not (model_dir / "model.onnx").exists():
            raise SemanticUnavailable(f"embedding model not found at {model_dir}")
        self.model_dir = model_dir
        self.tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
        self.tokenizer.enable_truncation(MAX_TOKENS)
        # Padding is done per length-sorted batch in embed(); the tokenizer
        # must not pad, or the attention mask would cover padding tokens and
        # a text's vector would depend on the texts batched with it.
        self.tokenizer.no_padding()
        opts = ort.SessionOptions()
        if threads:
            opts.intra_op_num_threads = threads
        opts.inter_op_num_threads = 1
        self.session, self.device = _open_session(
            model_dir / "model.onnx", opts, device, cuda_lib_dir
        )
        self.input_names = {i.name for i in self.session.get_inputs()}
        self.dim = int(self.session.get_outputs()[0].shape[-1])

    def token_count(self, text: str) -> int:
        return len(self.tokenizer.encode(text).ids)

    def embed(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Embed texts (already prefixed). Returns (n, dim) float32, L2-normalised."""
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        # Encode once, then batch by length so padding is minimal.
        encodings = self.tokenizer.encode_batch(texts)
        order = sorted(range(len(texts)), key=lambda i: len(encodings[i].ids))
        out = np.empty((len(texts), self.dim), dtype=np.float32)
        batch = max(1, batch_size)
        start = 0
        while start < len(order):
            idx = order[start : start + batch]
            try:
                out[idx] = self._run(encodings, idx)
            except Exception as exc:
                # A GPU with little memory cannot take the longest batches
                # whole; halve and retry rather than fail the run.
                if self.device == "cuda" and batch > 1 and _is_out_of_memory(exc):
                    batch //= 2
                    continue
                raise
            start += len(idx)
        return out

    def _run(self, encodings, idx: list[int]) -> np.ndarray:
        width = max(len(encodings[i].ids) for i in idx)
        ids = np.full((len(idx), width), PAD_ID, dtype=np.int64)
        mask = np.zeros((len(idx), width), dtype=np.int64)
        for row, i in enumerate(idx):
            n = len(encodings[i].ids)
            ids[row, :n] = encodings[i].ids
            mask[row, :n] = 1
        feed = {"input_ids": ids, "attention_mask": mask}
        if "token_type_ids" in self.input_names:
            feed["token_type_ids"] = np.zeros_like(ids)
        hidden = self.session.run(None, feed)[0]  # (b, width, dim)
        m = mask[:, :, None].astype(np.float32)
        pooled = (hidden * m).sum(axis=1) / np.maximum(m.sum(axis=1), 1e-9)
        pooled /= np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12)
        return pooled


def get_embedder() -> OnnxEmbedder:
    global _embedder
    if _embedder is None:
        with _lock:
            if _embedder is None:
                settings = get_settings()
                _embedder = OnnxEmbedder(
                    _cache_dir() / settings.EMBEDDING_MODEL_DIR,
                    _threads(),
                    settings.EMBEDDING_DEVICE,
                    settings.EMBEDDING_CUDA_LIB_DIR,
                )
    return _embedder


def get_reranker():
    global _reranker
    if _reranker is None:
        with _lock:
            if _reranker is None:
                try:
                    from fastembed.rerank.cross_encoder import TextCrossEncoder
                except ImportError as exc:
                    raise SemanticUnavailable("fastembed is not installed") from exc
                settings = get_settings()
                if settings.RERANKER_DEVICE == "cuda":
                    _preload_cuda_libraries(settings.EMBEDDING_CUDA_LIB_DIR)
                    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
                else:
                    providers = ["CPUExecutionProvider"]
                extra = {}
                if settings.RERANKER_MODEL_DIR:
                    extra["specific_model_path"] = str(_cache_dir() / settings.RERANKER_MODEL_DIR)
                _reranker = TextCrossEncoder(
                    settings.RERANKER_MODEL,
                    cache_dir=str(_cache_dir()),
                    threads=_threads(),
                    providers=providers,
                    local_files_only=True,
                    **extra,
                )
    return _reranker


def embed_passages(texts: list[str], batch_size: int = 32) -> np.ndarray:
    """Embed stored passages. Returns an (n, dim) float32 array."""
    return get_embedder().embed([PASSAGE_PREFIX + t for t in texts], batch_size)


def embed_query(text: str) -> np.ndarray:
    """Embed one user query. Returns a (dim,) float32 array."""
    return get_embedder().embed([QUERY_PREFIX + text])[0]


def rerank(query: str, passages: list[str]) -> list[float]:
    """Relevance score of each passage for the query (higher is better)."""
    if not passages:
        return []
    return [float(s) for s in get_reranker().rerank(query, passages)]


def model_file_checksums(model_dir_name: str) -> dict[str, str]:
    """sha256 of every file of a model directory, keyed by file name."""
    root = _cache_dir() / model_dir_name
    out: dict[str, str] = {}
    for path in sorted(root.iterdir()) if root.exists() else []:
        if path.is_file():
            h = hashlib.sha256()
            with path.open("rb") as fh:
                for block in iter(lambda: fh.read(1 << 20), b""):
                    h.update(block)
            out[path.name] = h.hexdigest()
    return out
