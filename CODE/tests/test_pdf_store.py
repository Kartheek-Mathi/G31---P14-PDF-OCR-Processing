import sqlite3
import pytest
from docweave.pdf_io import validate_pdf, extract_pages, chunks_from_pages, MAX_BYTES, render_page
from docweave.schema import Chunk, Triple
from docweave.store import Store
from docweave.pipeline import Pipeline
from docweave.extractors import RuleExtractor

@pytest.mark.parametrize("data",[b"",b"not a PDF",b"%PDF-invalid"])
def test_invalid_pdf(data):
    with pytest.raises(ValueError): validate_pdf(data)
def test_oversized_pdf():
    with pytest.raises(ValueError): validate_pdf(b"%PDF-" + b"0"*MAX_BYTES)
def test_native_extraction(pdf_bytes):
    did,pages=extract_pages(pdf_bytes,False)
    assert len(did)==64 and pages[0]["method"]=="native" and "Atlas40" in pages[0]["text"]
def test_native_avoids_ocr(pdf_bytes,monkeypatch):
    import docweave.pdf_io as module
    monkeypatch.setattr(module,"ocr_images",lambda _:pytest.fail("OCR called for a native-text PDF"))
    extract_pages(pdf_bytes,True)
def test_deterministic_chunks(pdf_bytes):
    did,pages=extract_pages(pdf_bytes,False)
    assert chunks_from_pages(did,pages)==chunks_from_pages(did,pages)
def test_render_invalid_page(pdf_bytes):
    with pytest.raises(ValueError): render_page(pdf_bytes,2)
def test_render_png(pdf_bytes): assert render_page(pdf_bytes,1).startswith(b"\x89PNG")
def test_empty_text_chunks(): assert chunks_from_pages("d",[{"page":1,"text":"","method":"empty"}])==[]
def test_bounded_chunks():
    cs=chunks_from_pages("d",[{"page":1,"text":" ".join(["word"]*250),"method":"native"}])
    assert len(cs)==3 and all(len(c.text.split())<=100 for c in cs)
def test_duplicate_ingestion_idempotent(tmp_path,pdf_bytes):
    store=Store(tmp_path/"db.sqlite3"); p=Pipeline(store,tmp_path/"uploads",RuleExtractor())
    a=p.ingest(pdf_bytes,"sample.pdf",False); b=p.ingest(pdf_bytes,"sample.pdf",False)
    assert a==b and len(store.documents())==1 and len(store.all_triples())==2
def test_filename_not_storage_path(tmp_path,pdf_bytes):
    store=Store(tmp_path/"db.sqlite3"); p=Pipeline(store,tmp_path/"uploads",RuleExtractor())
    d=p.ingest(pdf_bytes,"../../escape.pdf",False)
    assert d["filename"]=="escape.pdf" and not (tmp_path/"escape.pdf").exists()
    assert (tmp_path/"uploads"/(d["id"]+".pdf")).exists()
def test_transaction_restores_document(tmp_path,pdf_bytes):
    store=Store(tmp_path/"db.sqlite3"); p=Pipeline(store,tmp_path/"uploads",RuleExtractor()); result=p.ingest(pdf_bytes,"a.pdf",False)
    bad=Triple("bad","X","USES","Y","missing","bad",1.,"rules")
    with pytest.raises(sqlite3.IntegrityError): store.put(result["id"],"changed.pdf",[],[],[bad],"rules")
    assert store.documents()[0]["filename"]=="a.pdf" and len(store.all_triples())==2
def test_graph_focus_and_limit(tmp_path,pdf_bytes):
    s=Store(tmp_path/"db.sqlite3");Pipeline(s,tmp_path/"uploads",RuleExtractor()).ingest(pdf_bytes,"a.pdf",False)
    assert len(s.graph("Atlas40")["edges"])==2
    assert len(s.graph("",limit=2)["nodes"])<=2
