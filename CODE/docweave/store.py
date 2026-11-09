from __future__ import annotations
import sqlite3, json, threading
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime, timezone
from .schema import Chunk, Triple, entity_key, entity_type

class Store:
    def __init__(self, database: Path):
        database.parent.mkdir(parents=True, exist_ok=True)
        self.database = database; self.lock = threading.RLock()
        with self.connect() as con:
            con.executescript('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY, filename TEXT NOT NULL, pages INTEGER NOT NULL,
                page_data TEXT NOT NULL, extractor TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                page INTEGER NOT NULL, text TEXT NOT NULL, method TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS triples (
                id TEXT PRIMARY KEY, subject TEXT NOT NULL, predicate TEXT NOT NULL, object TEXT NOT NULL,
                chunk_id TEXT NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
                quote TEXT NOT NULL, confidence REAL NOT NULL, method TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS chunks_document ON chunks(document_id);
            CREATE INDEX IF NOT EXISTS triples_chunk ON triples(chunk_id);
            ''')
    @contextmanager
    def connect(self):
        con = sqlite3.connect(str(self.database), timeout=30)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        try:
            with con:
                yield con
        finally:
            con.close()
    def put(self, document_id: str, filename: str, pages: list[dict], chunks: list[Chunk],
            triples: list[Triple], extractor: str) -> None:
        with self.lock, self.connect() as con:
            con.execute("DELETE FROM documents WHERE id=?", (document_id,))
            con.execute("INSERT INTO documents VALUES(?,?,?,?,?,?)", (document_id, filename, len(pages),
                json.dumps(pages), extractor, datetime.now(timezone.utc).isoformat()))
            con.executemany("INSERT INTO chunks VALUES(?,?,?,?,?)", [(c.id,c.document_id,c.page,c.text,c.method) for c in chunks])
            con.executemany("INSERT INTO triples VALUES(?,?,?,?,?,?,?,?)", [
                (t.id,t.subject,t.predicate,t.object,t.chunk_id,t.quote,t.confidence,t.method) for t in triples])
    def documents(self) -> list[dict]:
        with self.connect() as con:
            return [dict(r) for r in con.execute('''SELECT d.id,d.filename,d.pages,d.extractor,d.created_at,
            (SELECT count(*) FROM chunks c WHERE c.document_id=d.id) AS chunks,
            (SELECT count(*) FROM triples t JOIN chunks c ON c.id=t.chunk_id WHERE c.document_id=d.id) AS triples
            FROM documents d ORDER BY d.filename''')]
    def document(self, document_id: str) -> dict | None:
        with self.connect() as con:
            row = con.execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()
            if row is None: return None
            result = dict(row); result["page_data"] = json.loads(result["page_data"])
            result["chunks"] = [dict(r) for r in con.execute("SELECT * FROM chunks WHERE document_id=? ORDER BY page,rowid", (document_id,))]
            result["triples"] = [dict(r) for r in con.execute('''SELECT t.* FROM triples t JOIN chunks c ON c.id=t.chunk_id
                WHERE c.document_id=?''', (document_id,))]
            return result
    def all_chunks(self) -> list[dict]:
        with self.connect() as con:
            return [dict(r) for r in con.execute("SELECT c.*,d.filename FROM chunks c JOIN documents d ON d.id=c.document_id ORDER BY c.rowid")]
    def all_triples(self) -> list[dict]:
        with self.connect() as con:
            return [dict(r) for r in con.execute('''SELECT t.*,c.document_id,c.page,d.filename FROM triples t
                JOIN chunks c ON c.id=t.chunk_id JOIN documents d ON d.id=c.document_id ORDER BY t.rowid''')]
    def graph(self, focus: str = "", limit: int = 70) -> dict:
        triples = self.all_triples(); selected = triples
        if focus:
            seeds = {entity_key(v) for t in triples for v in [t["subject"],t["object"]] if focus.casefold() in v.casefold()}
            frontier = set(seeds)
            selected_ids = set()
            for _ in range(2):
                neighbors = set()
                for t in triples:
                    if entity_key(t["subject"]) in frontier or entity_key(t["object"]) in frontier:
                        selected_ids.add(t["id"])
                        neighbors.update([entity_key(t["subject"]), entity_key(t["object"])])
                frontier = neighbors - seeds
                seeds.update(neighbors)
            selected = [t for t in triples if t["id"] in selected_ids]
        nodes, edges = {}, []
        for t in selected:
            s, o = entity_key(t["subject"]), entity_key(t["object"])
            missing = {s,o} - nodes.keys()
            if len(nodes) + len(missing) > limit: continue
            for key,label in [(s,t["subject"]),(o,t["object"])]:
                nodes[key] = {"id": key, "label": label, "type": entity_type(label)}
            edges.append({**t, "source": s, "target": o})
        return {"nodes": list(nodes.values()), "edges": edges,
                "truncated": len(edges) < len(selected), "total_edges": len(triples)}
