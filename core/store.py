"""SQLite repositories module.

Provides lightweight, robust SQLite repositories for document metadata,
audit logging, and metric tracking. Supports both in-memory and persistent storage.
"""

import json
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import RLock
from typing import Any

from core.clock import get_clock


@dataclass
class Document:
    """Document with complete metadata for Policy & Knowledge retrieval."""

    doc_id: str
    version: int
    product: str
    region: str
    access_level: str
    effective_date: str
    expiry_date: str | None
    doc_family: str
    section: str
    content: str
    is_injected: bool = False
    created_at: str | None = None


class SQLiteRepository:
    """Base SQLite repository with connection management and schema migration."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self.lock = RLock()
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self) -> None:
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    version INTEGER NOT NULL,
                    product TEXT NOT NULL,
                    region TEXT NOT NULL,
                    access_level TEXT NOT NULL,
                    effective_date TEXT NOT NULL,
                    expiry_date TEXT,
                    doc_family TEXT NOT NULL,
                    section TEXT NOT NULL,
                    content TEXT NOT NULL,
                    is_injected INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    user_role TEXT NOT NULL,
                    message TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS metric_counters (
                    name TEXT PRIMARY KEY,
                    value INTEGER NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS metric_values (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL, value REAL NOT NULL, recorded_at TEXT NOT NULL
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS metric_latencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    recorded_at TEXT NOT NULL
                )
            """)

    def close(self) -> None:
        self.conn.close()


class TicketRepository(SQLiteRepository):
    """Atomic ticket/draft mutations, including routing workloads and durable events."""

    def __init__(self, db_path: str = ":memory:") -> None:
        super().__init__(db_path)
        with self.conn:
            self.conn.execute("CREATE TABLE IF NOT EXISTS support_tickets (id TEXT PRIMARY KEY, payload_json TEXT NOT NULL)")

    @contextmanager
    def transaction(self) -> Generator[list[dict[str, Any]], None, None]:
        with self.lock:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                records = [json.loads(row[0]) for row in self.conn.execute("SELECT payload_json FROM support_tickets")]
                yield records
                for record in records:
                    self.conn.execute("INSERT INTO support_tickets VALUES (?,?) ON CONFLICT(id) DO UPDATE SET payload_json=excluded.payload_json",
                                      (record["id"], json.dumps(record, ensure_ascii=False)))
                self.conn.commit()
            except BaseException:
                self.conn.rollback()
                raise

    def records(self) -> list[dict[str, Any]]:
        with self.lock:
            return [json.loads(row[0]) for row in self.conn.execute("SELECT payload_json FROM support_tickets")]


class DocumentRepository(SQLiteRepository):
    """Repository for document metadata and contents."""

    def upsert_document(self, doc: Document) -> None:
        clock = get_clock()
        created_at = doc.created_at or clock.now().isoformat()
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO documents (
                    doc_id, version, product, region, access_level,
                    effective_date, expiry_date, doc_family, section,
                    content, is_injected, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(doc_id) DO UPDATE SET
                    version = excluded.version,
                    product = excluded.product,
                    region = excluded.region,
                    access_level = excluded.access_level,
                    effective_date = excluded.effective_date,
                    expiry_date = excluded.expiry_date,
                    doc_family = excluded.doc_family,
                    section = excluded.section,
                    content = excluded.content,
                    is_injected = excluded.is_injected,
                    created_at = excluded.created_at
                """,
                (
                    doc.doc_id,
                    doc.version,
                    doc.product,
                    doc.region,
                    doc.access_level,
                    doc.effective_date,
                    doc.expiry_date,
                    doc.doc_family,
                    doc.section,
                    doc.content,
                    1 if doc.is_injected else 0,
                    created_at,
                ),
            )

    def get_document(self, doc_id: str) -> Document | None:
        cursor = self.conn.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return Document(
            doc_id=row["doc_id"],
            version=row["version"],
            product=row["product"],
            region=row["region"],
            access_level=row["access_level"],
            effective_date=row["effective_date"],
            expiry_date=row["expiry_date"],
            doc_family=row["doc_family"],
            section=row["section"],
            content=row["content"],
            is_injected=bool(row["is_injected"]),
            created_at=row["created_at"],
        )

    def list_all(self) -> list[Document]:
        cursor = self.conn.execute("SELECT * FROM documents")
        docs: list[Document] = []
        for row in cursor.fetchall():
            docs.append(
                Document(
                    doc_id=row["doc_id"],
                    version=row["version"],
                    product=row["product"],
                    region=row["region"],
                    access_level=row["access_level"],
                    effective_date=row["effective_date"],
                    expiry_date=row["expiry_date"],
                    doc_family=row["doc_family"],
                    section=row["section"],
                    content=row["content"],
                    is_injected=bool(row["is_injected"]),
                    created_at=row["created_at"],
                )
            )
        return docs

    def count(self) -> int:
        cursor = self.conn.execute("SELECT COUNT(*) AS c FROM documents")
        return int(cursor.fetchone()["c"])


class AuditLogRepository(SQLiteRepository):
    """Repository for structured masked audit records."""

    def log(
        self,
        level: str,
        event_type: str,
        user_role: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        clock = get_clock()
        timestamp = clock.now().isoformat()
        metadata_str = json.dumps(metadata or {})
        with self.lock, self.conn:
            self.conn.execute(
                """
                INSERT INTO audit_logs (timestamp, level, event_type, user_role, message, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (timestamp, level, event_type, user_role, message, metadata_str),
            )

    def get_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        cursor = self.conn.execute(
            "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)
        )
        logs = []
        for row in cursor.fetchall():
            logs.append({
                "id": row["id"],
                "timestamp": row["timestamp"],
                "level": row["level"],
                "event_type": row["event_type"],
                "user_role": row["user_role"],
                "message": row["message"],
                "metadata": json.loads(row["metadata_json"]),
            })
        return logs


class MetricsRepository(SQLiteRepository):
    """Repository for operational telemetry."""

    def increment(self, name: str, amount: int = 1) -> None:
        with self.lock, self.conn:
            self.conn.execute(
                """
                INSERT INTO metric_counters (name, value)
                VALUES (?, ?)
                ON CONFLICT(name) DO UPDATE SET value = value + excluded.value
                """,
                (name, amount),
            )

    def record_latency(self, name: str, latency_ms: float) -> None:
        clock = get_clock()
        timestamp = clock.now().isoformat()
        with self.lock, self.conn:
            self.conn.execute(
                """
                INSERT INTO metric_latencies (name, latency_ms, recorded_at)
                VALUES (?, ?, ?)
                """,
                (name, latency_ms, timestamp),
            )

    def record_value(self, name: str, value: float) -> None:
        with self.lock, self.conn:
            self.conn.execute("INSERT INTO metric_values(name,value,recorded_at) VALUES(?,?,?)",
                              (name, value, get_clock().now().isoformat()))

    def get_summary(self) -> dict[str, Any]:
        counters: dict[str, int] = {}
        for row in self.conn.execute("SELECT name, value FROM metric_counters"):
            counters[row["name"]] = row["value"]

        latencies: dict[str, dict[str, float]] = {}
        for row in self.conn.execute("SELECT DISTINCT name FROM metric_latencies"):
            name = row["name"]
            stats_row = self.conn.execute(
                "SELECT COUNT(*) as count, AVG(latency_ms) as avg_lat, MAX(latency_ms) as max_lat, MIN(latency_ms) as min_lat FROM metric_latencies WHERE name = ?",
                (name,),
            ).fetchone()
            latencies[name] = {
                "count": stats_row["count"],
                "avg_ms": round(stats_row["avg_lat"] or 0.0, 2),
                "max_ms": round(stats_row["max_lat"] or 0.0, 2),
                "min_ms": round(stats_row["min_lat"] or 0.0, 2),
            }

        return {"counters": counters, "latencies": latencies}


class SnapshotRepository(DocumentRepository):
    """Immutable RAG snapshots and a transactional singleton ACTIVE pointer."""

    def __init__(self, db_path: str = ":memory:") -> None:
        super().__init__(db_path)
        self.lock = RLock()
        with self.conn:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    version INTEGER PRIMARY KEY AUTOINCREMENT,
                    documents_json TEXT NOT NULL,
                    manifest_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS snapshot_states (
                    version INTEGER PRIMARY KEY REFERENCES snapshots(version),
                    status TEXT NOT NULL, report_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS active_snapshot (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    version INTEGER NOT NULL REFERENCES snapshots(version),
                    previous_version INTEGER, activated_at TEXT, monitored INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS update_jobs (
                    id INTEGER PRIMARY KEY CHECK(id=1), payload_json TEXT NOT NULL
                );
                CREATE TRIGGER IF NOT EXISTS snapshots_no_update BEFORE UPDATE ON snapshots
                    BEGIN SELECT RAISE(ABORT, 'immutable snapshot'); END;
                CREATE TRIGGER IF NOT EXISTS snapshots_no_delete BEFORE DELETE ON snapshots
                    BEGIN SELECT RAISE(ABORT, 'immutable snapshot'); END;
            """)

    def create_snapshot(self, docs: list[Document], manifest: dict[str, Any]) -> int:
        with self.lock, self.conn:
            cursor = self.conn.execute(
                "INSERT INTO snapshots(documents_json,manifest_json,created_at) VALUES (?,?,?)",
                (json.dumps([asdict(d) for d in docs], sort_keys=True),
                 json.dumps(manifest, sort_keys=True), get_clock().now().isoformat()),
            )
            version = int(cursor.lastrowid)
            self.conn.execute("INSERT INTO snapshot_states(version,status) VALUES (?, 'CANDIDATE')", (version,))
        return version

    def ensure_active(self) -> int:
        with self.lock:
            if self.active_info() is None:
                version = self.create_snapshot(super().list_all(), {})
                self.set_state(version, "READY")
                self.swap_active(version, None, monitored=False)
            return int(self.active_info()["version"])

    def snapshot(self, version: int) -> dict[str, Any]:
        row = self.conn.execute("""
            SELECT s.*, t.status, t.report_json FROM snapshots s
            JOIN snapshot_states t USING(version) WHERE version=?
        """, (version,)).fetchone()
        if row is None:
            raise ValueError("Unknown snapshot version")
        return {"version": version, "documents": json.loads(row["documents_json"]),
                "manifest": json.loads(row["manifest_json"]), "status": row["status"],
                "report": json.loads(row["report_json"])}

    def set_state(self, version: int, status: str, report: dict[str, Any] | None = None) -> None:
        with self.lock, self.conn:
            if report is None:
                cursor = self.conn.execute("UPDATE snapshot_states SET status=? WHERE version=?", (status, version))
            else:
                cursor = self.conn.execute("UPDATE snapshot_states SET status=?,report_json=? WHERE version=?",
                                           (status, json.dumps(report), version))
            if cursor.rowcount != 1:
                raise ValueError("Unknown snapshot version")

    def active_info(self) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM active_snapshot WHERE singleton=1").fetchone()
        return dict(row) if row else None

    def swap_active(self, version: int, expected: int | None, monitored: bool = True) -> None:
        with self.lock, self.conn:
            self.snapshot(version)
            info = self.active_info()
            if (int(info["version"]) if info else None) != expected:
                raise RuntimeError("ACTIVE changed; reevaluate candidate")
            if expected is None:
                cursor = self.conn.execute("""
                    INSERT OR IGNORE INTO active_snapshot(singleton,version,previous_version,activated_at,monitored)
                    VALUES(1,?,NULL,?,?)
                """, (version, get_clock().now().isoformat(), int(monitored)))
            else:
                cursor = self.conn.execute("""
                    UPDATE active_snapshot SET version=?,previous_version=?,activated_at=?,monitored=?
                    WHERE singleton=1 AND version=?
                """, (version, expected, get_clock().now().isoformat(), int(monitored), expected))
            if cursor.rowcount != 1:
                raise RuntimeError("ACTIVE changed; reevaluate candidate")

    def finish_monitoring(self) -> None:
        with self.lock, self.conn:
            self.conn.execute("UPDATE active_snapshot SET monitored=0 WHERE singleton=1")

    def list_all(self) -> list[Document]:
        with self.lock:
            info = self.active_info()
            if info is None:
                return super().list_all()
            return self.documents_at(int(info["version"]))

    def documents_at(self, version: int) -> list[Document]:
        return [Document(**d) for d in self.snapshot(version)["documents"]]

    def upsert_document(self, doc: Document) -> None:
        if self.active_info() is not None:
            raise RuntimeError("Use candidate ingestion; ACTIVE is immutable")
        super().upsert_document(doc)

    def save_job(self, job: dict[str, Any]) -> None:
        with self.lock, self.conn:
            self.conn.execute("""INSERT INTO update_jobs(id,payload_json) VALUES(1,?)
                ON CONFLICT(id) DO UPDATE SET payload_json=excluded.payload_json""", (json.dumps(job),))

    def load_job(self) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT payload_json FROM update_jobs WHERE id=1").fetchone()
        return json.loads(row[0]) if row else None


class SnapshotView:
    """Pin retrieval and generation to one immutable revision during evaluation."""

    def __init__(self, repo: SnapshotRepository, version: int) -> None:
        self.repo, self.version = repo, version

    def list_all(self) -> list[Document]:
        return self.repo.documents_at(self.version)


class SessionRepository(SQLiteRepository):
    """Owner-bound session JSON, copied on read and atomically revision-checked."""

    def __init__(self, db_path: str = ":memory:") -> None:
        super().__init__(db_path)
        self.lock = RLock()
        with self.conn:
            self.conn.execute("""CREATE TABLE IF NOT EXISTS conversation_sessions (
                session_id TEXT PRIMARY KEY, owner TEXT NOT NULL,
                revision INTEGER NOT NULL, payload_json TEXT NOT NULL
            )""")

    def load_session(self, session_id: str, owner: str) -> tuple[dict[str, Any], int] | None:
        with self.lock:
            row = self.conn.execute("SELECT * FROM conversation_sessions WHERE session_id=?", (session_id,)).fetchone()
        if row is None:
            return None
        if row["owner"] != owner:
            raise PermissionError("Session belongs to a different caller")
        return json.loads(row["payload_json"]), int(row["revision"])

    def save_session(self, session_id: str, owner: str, payload: dict[str, Any], revision: int | None) -> None:
        serialized = json.dumps(payload, ensure_ascii=False)
        with self.lock, self.conn:
            if revision is None:
                cursor = self.conn.execute("""INSERT OR IGNORE INTO conversation_sessions
                    (session_id,owner,revision,payload_json) VALUES (?,?,1,?)""", (session_id, owner, serialized))
            else:
                cursor = self.conn.execute("""UPDATE conversation_sessions SET revision=revision+1,payload_json=?
                    WHERE session_id=? AND owner=? AND revision=?""", (serialized, session_id, owner, revision))
            if cursor.rowcount != 1:
                raise RuntimeError("Session changed concurrently; retry this message")

    def session_owners(self) -> list[tuple[str, str]]:
        with self.lock:
            return [(row[0], row[1]) for row in self.conn.execute("SELECT session_id,owner FROM conversation_sessions")]


class EscalationRepository(SQLiteRepository):
    """Atomic issue state and durable escalation records, independent of LLM success."""

    def __init__(self, db_path: str = ":memory:") -> None:
        super().__init__(db_path)
        with self.conn:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS support_issues (
                    session_id TEXT NOT NULL, generation INTEGER NOT NULL, owner TEXT NOT NULL,
                    payload_json TEXT NOT NULL, PRIMARY KEY(session_id,generation)
                );
                CREATE TABLE IF NOT EXISTS escalations (
                    id TEXT PRIMARY KEY, session_id TEXT NOT NULL, generation INTEGER NOT NULL,
                    owner TEXT NOT NULL, episode INTEGER NOT NULL, condition TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    UNIQUE(session_id,generation,episode,condition)
                );
            """)

    @contextmanager
    def issue(self, session_id: str, generation: int, owner: str) -> Generator[tuple[dict[str, Any], list[dict[str, Any]]], None, None]:
        with self.lock, self.conn:
            self.conn.execute("BEGIN IMMEDIATE")
            row = self.conn.execute("SELECT * FROM support_issues WHERE session_id=? AND generation=?",
                                    (session_id, generation)).fetchone()
            if row and row["owner"] != owner:
                raise PermissionError("Issue belongs to a different caller")
            state = json.loads(row["payload_json"]) if row else {
                "episode": 1, "negative_events": [], "unresolved_since": None,
                "activated": [], "history": [], "urgent": False, "resolved": False,
            }
            records: list[dict[str, Any]] = []
            yield state, records
            self.conn.execute("""INSERT INTO support_issues VALUES(?,?,?,?)
                ON CONFLICT(session_id,generation) DO UPDATE SET payload_json=excluded.payload_json""",
                              (session_id, generation, owner, json.dumps(state, ensure_ascii=False)))
            for record in records:
                self.conn.execute("INSERT INTO escalations VALUES(?,?,?,?,?,?,?)",
                                  (record["id"], session_id, generation, owner, record["episode"],
                                   record["activated_condition"]["kind"], json.dumps(record, ensure_ascii=False)))

    def issues(self) -> list[tuple[str, int, str]]:
        with self.lock:
            return [tuple(row) for row in self.conn.execute("SELECT session_id,generation,owner FROM support_issues")]

    def records(self, session_id: str | None = None, owner: str | None = None) -> list[dict[str, Any]]:
        with self.lock:
            rows = self.conn.execute("SELECT * FROM escalations ORDER BY rowid").fetchall()
        return [json.loads(row["payload_json"]) for row in rows
                if (session_id is None or row["session_id"] == session_id) and (owner is None or row["owner"] == owner)]

    def update_record(self, record: dict[str, Any]) -> None:
        with self.lock:
            if not self.conn.in_transaction:
                raise RuntimeError("Record updates require an atomic issue transaction")
            self.conn.execute("UPDATE escalations SET payload_json=? WHERE id=?",
                              (json.dumps(record, ensure_ascii=False), record["id"]))


class UploadRepository(SQLiteRepository):
    """Owner-bound durable upload jobs and customer notifications."""

    def __init__(self, db_path: str = ":memory:") -> None:
        super().__init__(db_path)
        with self.conn:
            self.conn.execute("""CREATE TABLE IF NOT EXISTS upload_jobs (
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, status TEXT NOT NULL,
                created_at TEXT NOT NULL, expires_at TEXT NOT NULL, storage_path TEXT NOT NULL,
                payload_json TEXT NOT NULL, result_json TEXT, notifications_json TEXT NOT NULL,
                expired INTEGER NOT NULL DEFAULT 0
            )""")

    @staticmethod
    def _job(row: sqlite3.Row) -> dict[str, Any]:
        job = dict(row)
        for key in ("payload", "result", "notifications"):
            raw = job.pop(key + "_json")
            job[key] = json.loads(raw) if raw else None
        return job

    def create_upload(self, job: dict[str, Any], max_pending: int) -> None:
        with self.lock, self.conn:
            self.conn.execute("BEGIN IMMEDIATE")
            count = self.conn.execute("SELECT COUNT(*) FROM upload_jobs WHERE status IN ('queued','running') AND expired=0").fetchone()[0]
            if count >= max_pending:
                raise RuntimeError("Upload queue capacity reached")
            self.conn.execute("INSERT INTO upload_jobs VALUES(?,?,?,?,?,?,?,?,?,0)",
                              (job["id"], job["owner"], "queued", job["created_at"], job["expires_at"],
                               job["storage_path"], json.dumps(job["payload"]), None,
                               json.dumps([{"event": "queued", "message": "File queued for processing.", "at": job["created_at"]}])))

    def get_upload(self, job_id: str, owner: str | None = None) -> dict[str, Any]:
        with self.lock:
            row = self.conn.execute("SELECT * FROM upload_jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown upload")
        if owner is not None and row["owner"] != owner:
            raise PermissionError("Upload belongs to another caller")
        return self._job(row)

    def uploads(self) -> list[dict[str, Any]]:
        with self.lock:
            return [self._job(row) for row in self.conn.execute("SELECT * FROM upload_jobs")]

    def claim_upload(self, job_id: str) -> bool:
        with self.lock, self.conn:
            return self.conn.execute("UPDATE upload_jobs SET status='running' WHERE id=? AND status='queued' AND expired=0",
                                     (job_id,)).rowcount == 1

    def finish_upload(self, job_id: str, status: str, result: dict[str, Any], at: str) -> bool:
        if status not in {"done", "failed"}:
            raise ValueError("Invalid terminal upload status")
        with self.lock, self.conn:
            job = self.get_upload(job_id)
            if job["expired"]:
                return False
            notifications = job["notifications"] + [{"event": status, "at": at,
                                                       "message": "File result is ready." if status == "done" else "File processing failed; see the result."}]
            return self.conn.execute("UPDATE upload_jobs SET status=?,result_json=?,notifications_json=? WHERE id=? AND expired=0",
                                     (status, json.dumps(result), json.dumps(notifications), job_id)).rowcount == 1

    def notify_background(self, job_id: str, at: str) -> None:
        with self.lock, self.conn:
            job = self.get_upload(job_id)
            if job["status"] not in {"queued", "running"} or job["expired"]:
                return
            notices = job["notifications"] + [{"event": "background", "at": at,
                                                "message": "Processing is taking longer; poll this job for its completion notification and result."}]
            self.conn.execute("UPDATE upload_jobs SET notifications_json=? WHERE id=?", (json.dumps(notices), job_id))

    def expire_upload(self, job_id: str, at: str) -> None:
        with self.lock, self.conn:
            self.conn.execute("""UPDATE upload_jobs SET status='failed',expired=1,payload_json='{}',result_json=NULL,
                notifications_json=? WHERE id=?""", (json.dumps([{"event": "expired", "at": at,
                                                                  "message": "Upload expired and stored content was deleted."}]), job_id))

    def requeue_upload(self, job_id: str) -> None:
        with self.lock, self.conn:
            self.conn.execute("UPDATE upload_jobs SET status='queued' WHERE id=? AND status='running' AND expired=0", (job_id,))
