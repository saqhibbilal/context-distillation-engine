"""ChromaDB vector store for chat embeddings."""

from pathlib import Path
from typing import Any, Optional

from app.models.message import Message

# Default persistence path
DEFAULT_PERSIST_PATH = Path("chroma_data")


def _get_client(persist_path: Path = DEFAULT_PERSIST_PATH):
    import chromadb
    from chromadb.config import Settings

    persist_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(persist_path),
        settings=Settings(anonymized_telemetry=False),
    )


def get_collection(session_id: str, persist_path: Path = DEFAULT_PERSIST_PATH, create: bool = True):
    """Get or create a ChromaDB collection for a session."""
    client = _get_client(persist_path)
    name = f"session_{session_id.replace('-', '_')}"
    if create:
        return client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
    try:
        return client.get_collection(name=name)
    except Exception:
        return None


def query_similar_safe(session_id: str, query_embedding: list[float], n_results: int = 8) -> list[dict]:
    """Query ChromaDB for similar chunks. Returns empty list if collection missing."""
    coll = get_collection(session_id, create=False)
    if coll is None or coll.count() == 0:
        return []
    results = coll.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, coll.count()),
    )
    if not results or not results.get("ids") or not results["ids"][0]:
        return []
    out = []
    metas = results.get("metadatas") or [[]]
    for i, id_ in enumerate(results["ids"][0]):
        meta = metas[0][i] if i < len(metas[0]) else {}
        out.append({"id": id_, "metadata": meta})
    return out


def store_embeddings(
    session_id: str,
    messages: list[Message],
    embeddings: list[list[float]],
    metadata: Optional[list[dict[str, Any]]] = None,
) -> None:
    """Store message embeddings in ChromaDB. Replaces existing data for this session."""
    if not messages or not embeddings:
        return
    if len(messages) != len(embeddings):
        raise ValueError("messages and embeddings length mismatch")

    client = _get_client()
    name = f"session_{session_id.replace('-', '_')}"
    try:
        client.delete_collection(name)
    except Exception:
        pass
    coll = client.get_or_create_collection(name=name, metadata={"hnsw:space": "cosine"})
    ids = [f"msg_{i}" for i in range(len(messages))]
    metadatas = metadata or []
    if not metadatas:
        metadatas = [
            {
                "author": m.author,
                "content": m.content[:500],
                "timestamp": m.timestamp.isoformat() if m.timestamp else "",
            }
            for m in messages
        ]
    coll.add(ids=ids, embeddings=embeddings, metadatas=metadatas)


