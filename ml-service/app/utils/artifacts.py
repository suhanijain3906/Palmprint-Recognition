"""Short lived artifact store.

Algorithms return images.  Instead of embedding large base64 payloads in
JSON responses, the service writes the result to a controlled directory and
hands back an opaque artifact identifier plus a download path.

Artifacts are *not* public: the identifier is random and the download route
lives on the internal network (the backend proxies them to end users).
"""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from .errors import ArtifactNotFoundError


@dataclass
class Artifact:
    artifact_id: str
    path: Path
    media_type: str
    size_bytes: int
    created_at: float
    kind: str


class ArtifactStore:
    """Filesystem backed artifact store with TTL based cleanup."""

    def __init__(self, root: Path, retention_hours: int = 24, max_bytes: int = 8 * 1024 * 1024):
        self._root = Path(root)
        self._retention_seconds = retention_hours * 3600
        self._max_bytes = max_bytes
        self._lock = threading.Lock()
        self._artifacts: dict[str, Artifact] = {}
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def put(self, data: bytes, *, media_type: str, kind: str) -> Artifact:
        if len(data) > self._max_bytes:
            raise ValueError(
                f"Artifact of {len(data)} bytes exceeds the configured limit "
                f"of {self._max_bytes} bytes."
            )
        artifact_id = secrets.token_urlsafe(16)
        target = self._root / f"{artifact_id}.bin"
        target.write_bytes(data)
        artifact = Artifact(
            artifact_id=artifact_id,
            path=target,
            media_type=media_type,
            size_bytes=len(data),
            created_at=time.time(),
            kind=kind,
        )
        with self._lock:
            self._artifacts[artifact_id] = artifact
        return artifact

    def get(self, artifact_id: str) -> Artifact:
        with self._lock:
            artifact = self._artifacts.get(artifact_id)
        if artifact is not None:
            return artifact
        # The service may have restarted; fall back to the on-disk copy.
        candidate = self._root / f"{artifact_id}.bin"
        if artifact_id and candidate.is_file() and self._is_valid_id(artifact_id):
            return Artifact(
                artifact_id=artifact_id,
                path=candidate,
                media_type="application/octet-stream",
                size_bytes=candidate.stat().st_size,
                created_at=candidate.stat().st_mtime,
                kind="unknown",
            )
        raise ArtifactNotFoundError(f"Artifact '{artifact_id}' was not found or has expired.")

    def delete(self, artifact_id: str) -> bool:
        with self._lock:
            artifact = self._artifacts.pop(artifact_id, None)
        if artifact is None:
            return False
        try:
            artifact.path.unlink(missing_ok=True)
        except OSError:
            pass
        return True

    def cleanup_expired(self) -> int:
        """Delete artifacts older than the retention window."""
        cutoff = time.time() - self._retention_seconds
        removed = 0
        with self._lock:
            expired = [aid for aid, art in self._artifacts.items() if art.created_at < cutoff]
            for aid in expired:
                artifact = self._artifacts.pop(aid)
                try:
                    artifact.path.unlink(missing_ok=True)
                except OSError:
                    pass
                removed += 1
        for path in self._root.glob("*.bin"):
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink()
                    removed += 1
            except OSError:
                continue
        return removed

    @staticmethod
    def _is_valid_id(artifact_id: str) -> bool:
        return bool(artifact_id) and all(ch.isalnum() or ch in "-_" for ch in artifact_id)
