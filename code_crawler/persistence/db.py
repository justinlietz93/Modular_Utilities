from __future__ import annotations

import os
import sqlite3
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_dir TEXT,
    ts TEXT,
    created_at REAL
);
CREATE TABLE IF NOT EXISTS manifests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES runs(id) ON DELETE CASCADE,
    filename TEXT,
    content TEXT
);
CREATE TABLE IF NOT EXISTS summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES runs(id) ON DELETE CASCADE,
    filename TEXT,
    content TEXT
);
CREATE TABLE IF NOT EXISTS diagrams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES runs(id) ON DELETE CASCADE,
    name TEXT,
    fmt TEXT,
    image BLOB
);
CREATE TABLE IF NOT EXISTS graphs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER REFERENCES runs(id) ON DELETE CASCADE,
    graphml TEXT,
    jsonld TEXT
);
"""

def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys=ON")
    return con


def ensure_schema(db_path: Path) -> None:
    with _connect(db_path) as con:
        con.executescript(SCHEMA)
        # Lightweight migration: add 'name' column on runs if missing
        cols = {row[1] for row in con.execute("PRAGMA table_info(runs)")}
        if "name" not in cols:
            try:
                con.execute("ALTER TABLE runs ADD COLUMN name TEXT")
            except Exception as exc:
                # Ignore if column already exists or alteration not supported; non-fatal
                sys_msg = str(exc)
                # Swallow but keep variable referenced to satisfy linters
                _ = sys_msg


def _safe_read_text(p: Optional[Path]) -> Optional[str]:
    if not p:
        return None
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def _safe_read_bytes(p: Optional[Path]) -> Optional[bytes]:
    if not p:
        return None
    try:
        return Path(p).read_bytes()
    except Exception:
        return None


def store_run_from_files(
    db_path: Path,
    run_dir: Path,
    manifest: Optional[Path],
    summary: Optional[Path],
    diagrams: Dict[str, Path],
    graph_graphml: Optional[Path],
    graph_jsonld: Optional[Path],
) -> int:
    """Persist a run and its artifacts into sqlite; returns run id."""
    ensure_schema(db_path)
    ts = run_dir.name[:15] if run_dir.name else time.strftime("%Y%m%d-%H%M%S")
    created = time.time()
    with _connect(db_path) as con:
        cur = con.cursor()
        cur.execute("INSERT INTO runs(run_dir, ts, created_at) VALUES (?, ?, ?)", (str(run_dir), ts, created))
        run_id = cur.lastrowid
        mtxt = _safe_read_text(manifest)
        if mtxt is not None:
            cur.execute(
                "INSERT INTO manifests(run_id, filename, content) VALUES (?, ?, ?)",
                (run_id, manifest.name if manifest else "manifest.json", mtxt),
            )
        stxt = _safe_read_text(summary)
        if stxt is not None:
            cur.execute(
                "INSERT INTO summaries(run_id, filename, content) VALUES (?, ?, ?)",
                (run_id, summary.name if summary else "summary.md", stxt),
            )
        for name, p in diagrams.items():
            data = _safe_read_bytes(p)
            if data is None:
                continue
            fmt = p.suffix.lstrip(".").lower() or "png"
            cur.execute(
                "INSERT INTO diagrams(run_id, name, fmt, image) VALUES (?, ?, ?, ?)",
                (run_id, name, fmt, data),
            )
        gml = _safe_read_text(graph_graphml)
        jld = _safe_read_text(graph_jsonld)
        if gml is not None or jld is not None:
            cur.execute(
                "INSERT INTO graphs(run_id, graphml, jsonld) VALUES (?, ?, ?)",
                (run_id, gml, jld),
            )
        con.commit()
        return int(run_id)


def list_runs(db_path: Path):
    """Return list of runs sorted by created_at desc: [{id, ts, name, created_at, run_dir}]"""
    ensure_schema(db_path)
    with _connect(db_path) as con:
        rows = con.execute("SELECT id, ts, name, created_at, run_dir FROM runs ORDER BY created_at DESC").fetchall()
        return [
            {
                "id": int(r[0]),
                "ts": r[1],
                "name": r[2] or "",
                "created_at": float(r[3]) if r[3] is not None else 0.0,
                "run_dir": r[4] or "",
            }
            for r in rows
        ]


def rename_run(db_path: Path, run_id: int, new_name: str) -> None:
    ensure_schema(db_path)
    with _connect(db_path) as con:
        con.execute("UPDATE runs SET name=? WHERE id=?", (new_name, run_id))


def delete_run(db_path: Path, run_id: int) -> None:
    ensure_schema(db_path)
    with _connect(db_path) as con:
        con.execute("DELETE FROM runs WHERE id=?", (run_id,))


def get_latest_run_id(db_path: Path) -> Optional[int]:
    if not db_path.exists():
        return None
    with _connect(db_path) as con:
        row = con.execute("SELECT id FROM runs ORDER BY created_at DESC LIMIT 1").fetchone()
        return int(row[0]) if row else None


def load_run_artifacts(db_path: Path, run_id: Optional[int] = None):
    """Return a dict with manifest, summary, diagrams, graph for a run.
    diagrams: Dict[name, (fmt, bytes)]
    """
    ensure_schema(db_path)
    with _connect(db_path) as con:
        if run_id is None:
            row = con.execute("SELECT id FROM runs ORDER BY created_at DESC LIMIT 1").fetchone()
            if not row:
                return None
            run_id = int(row[0])
        data: Dict[str, object] = {"run_id": run_id}
        m = con.execute("SELECT filename, content FROM manifests WHERE run_id=? LIMIT 1", (run_id,)).fetchone()
        if m:
            data["manifest"] = {"filename": m[0], "content": m[1]}
        s = con.execute("SELECT filename, content FROM summaries WHERE run_id=? LIMIT 1", (run_id,)).fetchone()
        if s:
            data["summary"] = {"filename": s[0], "content": s[1]}
        diags = {}
        for name, fmt, image in con.execute("SELECT name, fmt, image FROM diagrams WHERE run_id=?", (run_id,)):
            diags[name] = (fmt, image)
        data["diagrams"] = diags
        g = con.execute("SELECT graphml, jsonld FROM graphs WHERE run_id=? LIMIT 1", (run_id,)).fetchone()
        if g:
            data["graphml"] = g[0]
            data["jsonld"] = g[1]
        return data


def export_run_to_dir(db_path: Path, run_id: Optional[int], out_base: Path) -> Path:
    """Reconstruct files for a run under out_base/<ts>-from-db/ ... and return the path."""
    ensure_schema(db_path)
    out_base.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as con:
        if run_id is None:
            row = con.execute("SELECT id, ts FROM runs ORDER BY created_at DESC LIMIT 1").fetchone()
        else:
            row = con.execute("SELECT id, ts FROM runs WHERE id=?", (run_id,)).fetchone()
        if not row:
            raise RuntimeError("No run found in database to export")
        run_id, ts = int(row[0]), (row[1] or time.strftime("%Y%m%d-%H%M%S"))
        out_dir = out_base / f"{ts}-from-db"
        (out_dir / "manifests").mkdir(parents=True, exist_ok=True)
        (out_dir / "summaries").mkdir(parents=True, exist_ok=True)
        (out_dir / "diagrams").mkdir(parents=True, exist_ok=True)
        (out_dir / "graph").mkdir(parents=True, exist_ok=True)
        m = con.execute("SELECT filename, content FROM manifests WHERE run_id=? LIMIT 1", (run_id,)).fetchone()
        if m:
            (out_dir / "manifests" / (m[0] or "manifest.json")).write_text(m[1] or "", encoding="utf-8")
        s = con.execute("SELECT filename, content FROM summaries WHERE run_id=? LIMIT 1", (run_id,)).fetchone()
        if s:
            (out_dir / "summaries" / (s[0] or "summary.md")).write_text(s[1] or "", encoding="utf-8")
        for name, fmt, image in con.execute("SELECT name, fmt, image FROM diagrams WHERE run_id=?", (run_id,)):
            suffix = (fmt or "png").lower()
            (out_dir / "diagrams" / f"{name}.{suffix}").write_bytes(image or b"")
        g = con.execute("SELECT graphml, jsonld FROM graphs WHERE run_id=? LIMIT 1", (run_id,)).fetchone()
        if g and g[0]:
            (out_dir / "graph" / "graph.graphml").write_text(g[0], encoding="utf-8")
        if g and g[1]:
            (out_dir / "graph" / "graph.jsonld").write_text(g[1], encoding="utf-8")
        return out_dir
