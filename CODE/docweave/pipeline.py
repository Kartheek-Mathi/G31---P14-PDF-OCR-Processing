from __future__ import annotations
from pathlib import Path
from .pdf_io import extract_pages, chunks_from_pages
from .store import Store

class Pipeline:
    def __init__(self, store: Store, upload_dir: Path, extractor):
        self.store, self.upload_dir, self.extractor = store, upload_dir, extractor
        upload_dir.mkdir(parents=True, exist_ok=True)
    def ingest(self, data: bytes, filename: str, allow_ocr: bool = True) -> dict:
        document_id, pages = extract_pages(data, allow_ocr=allow_ocr)
        chunks = chunks_from_pages(document_id, pages)
        triples = [t for c in chunks for t in self.extractor.extract(c)]
        # Original filenames are display-only. A content digest determines storage paths.
        safe_name = Path(filename.replace("\\", "/")).name[:180] or "document.pdf"
        target = self.upload_dir / (document_id + ".pdf")
        temporary = target.with_suffix(".tmp")
        with self.store.lock:
            temporary.write_bytes(data); temporary.replace(target)
            self.store.put(document_id, safe_name, pages, chunks, triples, self.extractor.name)
        return {"id": document_id, "filename": safe_name, "pages": len(pages),
                "chunks": len(chunks), "triples": len(triples), "extractor": self.extractor.name,
                "empty_pages": sum(p["method"] == "empty" for p in pages)}
