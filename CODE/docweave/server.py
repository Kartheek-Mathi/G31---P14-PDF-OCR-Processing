from __future__ import annotations
from pathlib import Path
import csv, io, json, os, threading
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
from .pdf_io import MAX_BYTES, render_page
from .store import Store
from .pipeline import Pipeline
from .extractors import get_extractor
from .retrieval import Retriever

ROOT = Path(__file__).resolve().parents[2]
WEB = Path(__file__).resolve().parent / "web"

class SearchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    method: str = "graph"
    k: int = Field(default=5, ge=1, le=20)

def create_app(root: Path = ROOT, extractor_name: str | None = None) -> FastAPI:
    app = FastAPI(title="DocWeave", version="1.0.0", docs_url="/api/docs")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver", "[::1]"])
    runtime = root / "DATA/runtime"
    store = Store(runtime / "docweave.sqlite3")
    extractor = get_extractor(extractor_name or os.getenv("DOCWEAVE_EXTRACTOR", "neural"), root / "DATA/models")
    pipeline = Pipeline(store, runtime / "uploads", extractor)
    state = {"index": None}; mutex = threading.RLock()
    def index():
        with mutex:
            if state["index"] is None:
                state["index"] = Retriever(store.all_chunks(), store.all_triples())
            return state["index"]
    @app.middleware("http")
    async def safe_headers(request, call_next):
        # Restrict state-changing browser requests to the same local origin.
        origin = request.headers.get("origin")
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and origin:
            expected = f"{request.url.scheme}://{request.headers.get('host', '')}"
            if origin.rstrip("/") != expected:
                return JSONResponse({"detail":"Cross-origin writes are not allowed."}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-src 'self'; object-src 'none'; base-uri 'none'"
        return response
    @app.get("/")
    def home(): return FileResponse(WEB / "index.html")
    @app.get("/api/status")
    def status():
        docs = store.documents(); triples = store.all_triples()
        nodes = {e for t in triples for e in (t["subject"], t["object"])}
        return {"documents": len(docs), "pages": sum(d["pages"] for d in docs),
                "chunks": sum(d["chunks"] for d in docs), "nodes": len(nodes), "triples": len(triples),
                "extractor": extractor.name, "mode": "local-first research prototype",
                "dataset": "WorkflowBench-S | synthetic", "optional_services_evaluated": False}
    @app.get("/api/documents")
    def documents(): return store.documents()
    @app.get("/api/documents/{document_id}")
    def document(document_id: str):
        found = store.document(document_id)
        if not found: raise HTTPException(404, "Document not found.")
        return found
    @app.get("/api/documents/{document_id}/file")
    def original(document_id: str):
        found = store.document(document_id)
        if not found: raise HTTPException(404,"Document not found.")
        path = runtime / "uploads" / (found["id"] + ".pdf")
        if not path.exists(): raise HTTPException(404,"Original PDF missing; re-seed the demo.")
        return FileResponse(path, media_type="application/pdf", filename=found["filename"])
    @app.get("/api/documents/{document_id}/pages/{page}")
    def page_preview(document_id: str, page: int):
        found = store.document(document_id)
        if not found: raise HTTPException(404,"Document not found.")
        path = runtime / "uploads" / (found["id"] + ".pdf")
        try: return Response(render_page(path.read_bytes(), page), media_type="image/png")
        except ValueError as exc: raise HTTPException(400,str(exc)) from exc
    @app.post("/api/ingest")
    def ingest(file: UploadFile = File(...)):
        data = file.file.read(MAX_BYTES + 1)
        try:
            with mutex:
                result = pipeline.ingest(data, file.filename or "document.pdf", allow_ocr=True)
                state["index"] = None
            return result
        except ValueError as exc: raise HTTPException(400,str(exc)) from exc
        except RuntimeError as exc: raise HTTPException(503,str(exc)) from exc
        except Exception as exc: raise HTTPException(500,"Processing failed; inspect the local server log.") from exc
    @app.post("/api/search")
    def search(request: SearchRequest):
        try: return index().search(request.question,request.method,request.k)
        except ValueError as exc: raise HTTPException(400,str(exc)) from exc
    @app.get("/api/graph")
    def graph(focus: str = "", limit: int = 60):
        if len(focus)>200: raise HTTPException(400,"Focus text too long.")
        return store.graph(focus, max(2,min(limit,100)))
    @app.get("/api/evaluations")
    def evaluations():
        path = root / "EVALUATIONS/results/metrics.json"
        if not path.exists(): raise HTTPException(404,"Run CODE/tools/evaluate.py first.")
        return json.loads(path.read_text())
    @app.get("/api/export")
    def export(format: str = "json"):
        triples = store.all_triples()
        if format == "json":
            return Response(json.dumps(triples,indent=2),media_type="application/json",
                            headers={"Content-Disposition":'attachment; filename="docweave-triples.json"'})
        if format != "csv": raise HTTPException(400,"Format must be json or csv.")
        output = io.StringIO()
        columns = ["subject","predicate","object","filename","page","quote","method","confidence"]
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore"); writer.writeheader()
        # Neutralize spreadsheet formula injection in exported text cells.
        writer.writerows({k:("'"+str(v) if str(v).startswith(("=","+","-","@")) else v) for k,v in row.items()} for row in triples)
        return Response(output.getvalue(), media_type="text/csv",headers={"Content-Disposition":'attachment; filename="docweave-triples.csv"'})
    app.mount("/static", StaticFiles(directory=WEB), name="static")
    return app
