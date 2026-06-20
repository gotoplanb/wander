"""SQLite-backed result store for bench runs.

Tables:

    runs           one row per (spec, fleet) execution
    gen_jobs       one row per (run, model) — the code_generation job
    eval_jobs      one row per gen_job — the code_eval follow-up
    dimensions     one row per (eval_job, dimension_name) — compile, golden,
                   property, ... — the per-dimension score the bench reads
                   to rank models in #6.

The dimensions table is the read path for the bench report. It mirrors
what Conduct's `/eval/compare` rollup also returns, but keeping a local
copy lets the harness diff runs across time without depending on the
server's retention policy.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "runs" / "runs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    spec_id         TEXT    NOT NULL,
    started_at      TEXT    NOT NULL,
    finished_at     TEXT
);

CREATE TABLE IF NOT EXISTS gen_jobs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id              INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    model               TEXT    NOT NULL,
    conduct_job_id      TEXT,
    status              TEXT    NOT NULL,
    artifact_url        TEXT,
    error               TEXT,
    UNIQUE(run_id, model)
);

CREATE TABLE IF NOT EXISTS eval_jobs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id              INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    gen_job_id          INTEGER NOT NULL REFERENCES gen_jobs(id) ON DELETE CASCADE,
    conduct_job_id      TEXT,
    status              TEXT    NOT NULL,
    error               TEXT,
    UNIQUE(gen_job_id)
);

CREATE TABLE IF NOT EXISTS dimensions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    eval_job_id         INTEGER NOT NULL REFERENCES eval_jobs(id) ON DELETE CASCADE,
    name                TEXT    NOT NULL,
    score               REAL    NOT NULL,
    detail_json         TEXT,
    UNIQUE(eval_job_id, name)
);

CREATE INDEX IF NOT EXISTS idx_gen_jobs_run ON gen_jobs(run_id);
CREATE INDEX IF NOT EXISTS idx_eval_jobs_run ON eval_jobs(run_id);
CREATE INDEX IF NOT EXISTS idx_dimensions_eval ON dimensions(eval_job_id);
"""


@dataclass(frozen=True)
class GenJobRow:
    id: int
    model: str
    conduct_job_id: str | None
    status: str
    artifact_url: str | None
    error: str | None


@dataclass(frozen=True)
class EvalJobRow:
    id: int
    gen_job_id: int
    conduct_job_id: str | None
    status: str
    error: str | None
    dimensions: dict[str, float]


class Store:
    """Thin wrapper over a sqlite3 connection — opens lazily, schema-on-init."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @contextmanager
    def _txn(self) -> Iterator[sqlite3.Cursor]:
        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cur.close()

    # ----- writes -------------------------------------------------------

    def start_run(self, spec_id: str, *, started_at: str) -> int:
        with self._txn() as cur:
            cur.execute(
                "INSERT INTO runs (spec_id, started_at) VALUES (?, ?)",
                (spec_id, started_at),
            )
            return int(cur.lastrowid)

    def finish_run(self, run_id: int, *, finished_at: str) -> None:
        with self._txn() as cur:
            cur.execute(
                "UPDATE runs SET finished_at = ? WHERE id = ?",
                (finished_at, run_id),
            )

    def upsert_gen_job(
        self,
        *,
        run_id: int,
        model: str,
        conduct_job_id: str | None,
        status: str,
        artifact_url: str | None,
        error: str | None,
    ) -> int:
        with self._txn() as cur:
            cur.execute(
                """
                INSERT INTO gen_jobs
                    (run_id, model, conduct_job_id, status, artifact_url, error)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id, model) DO UPDATE SET
                    conduct_job_id = excluded.conduct_job_id,
                    status         = excluded.status,
                    artifact_url   = excluded.artifact_url,
                    error          = excluded.error
                """,
                (run_id, model, conduct_job_id, status, artifact_url, error),
            )
            row = cur.execute(
                "SELECT id FROM gen_jobs WHERE run_id = ? AND model = ?",
                (run_id, model),
            ).fetchone()
            return int(row[0])

    def upsert_eval_job(
        self,
        *,
        run_id: int,
        gen_job_id: int,
        conduct_job_id: str | None,
        status: str,
        error: str | None,
    ) -> int:
        with self._txn() as cur:
            cur.execute(
                """
                INSERT INTO eval_jobs
                    (run_id, gen_job_id, conduct_job_id, status, error)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(gen_job_id) DO UPDATE SET
                    conduct_job_id = excluded.conduct_job_id,
                    status         = excluded.status,
                    error          = excluded.error
                """,
                (run_id, gen_job_id, conduct_job_id, status, error),
            )
            row = cur.execute(
                "SELECT id FROM eval_jobs WHERE gen_job_id = ?",
                (gen_job_id,),
            ).fetchone()
            return int(row[0])

    def record_dimension(
        self,
        *,
        eval_job_id: int,
        name: str,
        score: float,
        detail: dict[str, Any] | None = None,
    ) -> None:
        detail_json = json.dumps(detail, sort_keys=True) if detail else None
        with self._txn() as cur:
            cur.execute(
                """
                INSERT INTO dimensions (eval_job_id, name, score, detail_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(eval_job_id, name) DO UPDATE SET
                    score       = excluded.score,
                    detail_json = excluded.detail_json
                """,
                (eval_job_id, name, score, detail_json),
            )

    # ----- reads --------------------------------------------------------

    def gen_jobs_for_run(self, run_id: int) -> list[GenJobRow]:
        cur = self._conn.execute(
            "SELECT id, model, conduct_job_id, status, artifact_url, error "
            "FROM gen_jobs WHERE run_id = ? ORDER BY model",
            (run_id,),
        )
        return [GenJobRow(*row) for row in cur.fetchall()]

    def eval_jobs_for_run(self, run_id: int) -> list[EvalJobRow]:
        cur = self._conn.execute(
            "SELECT id, gen_job_id, conduct_job_id, status, error "
            "FROM eval_jobs WHERE run_id = ?",
            (run_id,),
        )
        rows = cur.fetchall()
        out: list[EvalJobRow] = []
        for ev_id, gen_id, cjid, st, err in rows:
            dim_cur = self._conn.execute(
                "SELECT name, score FROM dimensions WHERE eval_job_id = ?",
                (ev_id,),
            )
            dims = {name: float(score) for name, score in dim_cur.fetchall()}
            out.append(EvalJobRow(ev_id, gen_id, cjid, st, err, dims))
        return out
