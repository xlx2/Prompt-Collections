import os
import sqlite3
from datetime import datetime
from typing import Iterable, List, Optional, Tuple

DB_PATH = os.getenv("PROMPT_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "prompts.db"))


def _connect() -> sqlite3.Connection:
    db_dir = os.path.dirname(DB_PATH) or "."
    os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    conn = _connect()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                purpose TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS prompt_tags (
                prompt_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (prompt_id, tag_id),
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def list_prompts() -> List[sqlite3.Row]:
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM prompts ORDER BY updated_at DESC").fetchall()
        return rows
    finally:
        conn.close()


def get_prompt(prompt_id: int) -> Optional[sqlite3.Row]:
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,)).fetchone()
        return row
    finally:
        conn.close()


def create_prompt(title: str, summary: str, purpose: str, content: str) -> int:
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    conn = _connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO prompts (title, summary, purpose, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, summary, purpose, content, now, now),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def update_prompt(prompt_id: int, title: str, summary: str, purpose: str, content: str) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    conn = _connect()
    try:
        conn.execute(
            """
            UPDATE prompts
            SET title = ?, summary = ?, purpose = ?, content = ?, updated_at = ?
            WHERE id = ?
            """,
            (title, summary, purpose, content, now, prompt_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_prompt(prompt_id: int) -> None:
    conn = _connect()
    try:
        conn.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        conn.commit()
    finally:
        conn.close()


def update_prompt_updated_at(prompt_id: int) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    conn = _connect()
    try:
        conn.execute("UPDATE prompts SET updated_at = ? WHERE id = ?", (now, prompt_id))
        conn.commit()
    finally:
        conn.close()


def list_tags() -> List[sqlite3.Row]:
    conn = _connect()
    try:
        return conn.execute("SELECT * FROM tags ORDER BY name ASC").fetchall()
    finally:
        conn.close()


def get_tags_for_prompt(prompt_id: int) -> List[sqlite3.Row]:
    conn = _connect()
    try:
        return conn.execute(
            """
            SELECT t.* FROM tags t
            JOIN prompt_tags pt ON pt.tag_id = t.id
            WHERE pt.prompt_id = ?
            ORDER BY t.name ASC
            """,
            (prompt_id,),
        ).fetchall()
    finally:
        conn.close()


def upsert_tag(name: str, color: str) -> int:
    conn = _connect()
    try:
        existing = conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
        if existing:
            return int(existing["id"])
        cur = conn.execute("INSERT INTO tags (name, color) VALUES (?, ?)", (name, color))
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def update_tag_color(tag_id: int, color: str) -> None:
    conn = _connect()
    try:
        conn.execute("UPDATE tags SET color = ? WHERE id = ?", (color, tag_id))
        conn.commit()
    finally:
        conn.close()


def delete_tag(tag_id: int) -> None:
    conn = _connect()
    try:
        conn.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        conn.commit()
    finally:
        conn.close()


def set_prompt_tags(prompt_id: int, tag_ids: Iterable[int]) -> None:
    conn = _connect()
    try:
        conn.execute("DELETE FROM prompt_tags WHERE prompt_id = ?", (prompt_id,))
        conn.executemany(
            "INSERT INTO prompt_tags (prompt_id, tag_id) VALUES (?, ?)",
            [(prompt_id, tag_id) for tag_id in tag_ids],
        )
        conn.commit()
    finally:
        conn.close()


def list_prompts_with_tags() -> List[Tuple[sqlite3.Row, List[sqlite3.Row]]]:
    prompts = list_prompts()
    results = []
    for prompt in prompts:
        tags = get_tags_for_prompt(int(prompt["id"]))
        results.append((prompt, tags))
    return results
