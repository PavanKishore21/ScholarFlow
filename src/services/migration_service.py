import threading
import time
import uuid
from datetime import datetime, timezone

from src.config import settings
from src.db.vector_store import VectorStore
from src.logger import get_logger

log = get_logger("MigrationService")


class MigrationService:
    def __init__(self):
        self.vs = VectorStore()
        self.running = False
        self.finished = False
        self.migrated = 0
        self.errors = 0
        self.logs = []
        self.started_at = None
        self.finished_at = None
        self._lock = threading.Lock()

    @property
    def uptime(self):
        if not self.started_at:
            return "N/A"
        end = self.finished_at or time.time()
        elapsed = max(0, int(end - self.started_at))
        hours, rem = divmod(elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _log(self, level: str, message: str):
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = {"timestamp": timestamp, "level": level, "message": message}
        self.logs.append(entry)
        if len(self.logs) > 200:
            self.logs = self.logs[-200:]

        if level == "error":
            log.error(message)
        elif level == "warning":
            log.warning(message)
        else:
            log.info(message)

    def start_background_migration(self):
        with self._lock:
            if self.running:
                self._log("warning", "Migration already running; ignoring restart request.")
                return

            self.running = True
            self.finished = False
            self.migrated = 0
            self.errors = 0
            self.started_at = time.time()
            self.finished_at = None

        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def _run(self):
        self._log("info", "Starting background Qdrant migration service...")
        if not self.vs.available:
            self._log("error", "Vector store unavailable; migration not started.")
            self.running = False
            self.finished = True
            self.finished_at = time.time()
            return

        offset = None
        loops = 0

        try:
            while True:
                loops += 1
                if loops > 5000:
                    self._log("error", "Infinite scroll detected; stopping migration.")
                    break

                points, offset_new = self.vs.client.scroll(
                    collection_name=settings.COLLECTION_NAME,
                    limit=128,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                )

                # No new points
                if not points:
                    break

                # If offset does not change → bad scroll → break loop safely
                if offset_new == offset:
                    self._log("error", "Offset did not advance; stopping migration.")
                    break

                offset = offset_new

                for p in points:
                    try:
                        payload = p.payload or {}
                        version = payload.get("schema_version", 0)

                        if version >= settings.PAYLOAD_SCHEMA_VERSION:
                            continue

                        # ---- migrate ----
                        paper_id = payload.get("paper_id") or payload.get("id") or str(uuid.uuid4())
                        text = payload.get("text") or payload.get("abstract") or ""
                        title = payload.get("title") or "Untitled"
                        chunk_index = payload.get("chunk_index", 0)
                        source = payload.get("source") or "Unknown"

                        new_payload = {
                            "schema_version": settings.PAYLOAD_SCHEMA_VERSION,
                            "paper_id": paper_id,
                            "title": title,
                            "text": text,
                            "chunk_index": chunk_index,
                            "source": source,
                        }

                        self.vs.client.set_payload(
                            collection_name=settings.COLLECTION_NAME,
                            payload=new_payload,
                            points=[p.id],
                        )

                        self.migrated += 1

                    except Exception as e:
                        self._log("error", f"Migration error on point {p.id}: {e}")
                        self.errors += 1

                    time.sleep(0.001)
        except Exception as e:
            self._log("error", f"Migration fatal error: {e}")

        self.running = False
        self.finished = True
        self.finished_at = time.time()

        self._log(
            "info",
            f"Migration completed: migrated={self.migrated}, errors={self.errors}",
        )
