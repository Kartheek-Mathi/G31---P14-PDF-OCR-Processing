import pytest
from docweave.retrieval import plan, Retriever

@pytest.mark.parametrize("q,p",[
    ("Which council supervises the team managing Atlas40 Service?",["MANAGED_BY","REPORTS_TO"]),
    ("How long are records kept in the archive used by Atlas40 Service?",["STORES_IN","RETENTION"]),
    ("What is the annual budget of Atlas40 Service?",[]),
    ("Who manages Atlas40 Service?",["MANAGED_BY"]),
])
def test_question_plan(q,p): assert plan(q)==p
def test_empty_index(): assert Retriever([],[]).search("anything")["results"]==[]
def test_empty_query_rejected():
    with pytest.raises(ValueError): Retriever([],[]).search(" ")
def test_invalid_method():
    with pytest.raises(ValueError): Retriever([],[]).search("something","invented")
def test_health_empty(client): assert client.get("/api/status").json()["documents"]==0
def test_home_and_headers(client):
    response=client.get("/"); assert response.status_code==200 and "DocWeave" in response.text
    assert response.headers["x-content-type-options"]=="nosniff"
def test_missing_document(client): assert client.get("/api/documents/unknown").status_code==404
def test_upload_search_export(client,pdf_bytes):
    upload=client.post("/api/ingest",files={"file":("source.pdf",pdf_bytes,"application/pdf")})
    assert upload.status_code==200 and upload.json()["triples"]==2
    result=client.post("/api/search",json={"question":"Which council supervises the team managing Atlas40 Service?","method":"graph"}).json()
    assert result["trace"]["answers"]==["Assurance40 Council"]
    assert len(result["trace"]["edges"])==2 and all(r["graph_support"] for r in result["results"][:2])
    assert len(client.get("/api/export").json())==2
    assert "MANAGED_BY" in client.get("/api/export?format=csv").text
    docid=upload.json()["id"]
    assert client.get(f"/api/documents/{docid}/file").content==pdf_bytes
    assert client.get(f"/api/documents/{docid}/pages/1").headers["content-type"]=="image/png"
def test_unsupported_abstains(client,pdf_bytes):
    client.post("/api/ingest",files={"file":("source.pdf",pdf_bytes)})
    result=client.post("/api/search",json={"question":"What is the annual budget of Atlas40 Service?"}).json()
    assert result["trace"]["answers"]==[] and result["trace"]["status"]=="unsupported_question"
def test_upload_invalid(client): assert client.post("/api/ingest",files={"file":("bad.pdf",b"bad")}).status_code==400
def test_cross_origin_write_blocked(client,pdf_bytes):
    response=client.post("/api/ingest",files={"file":("a.pdf",pdf_bytes)},headers={"Origin":"https://untrusted.example"})
    assert response.status_code==403
def test_untrusted_host_blocked(client): assert client.get("/api/status",headers={"Host":"evil.example"}).status_code==400
def test_query_limit(client): assert client.post("/api/search",json={"question":"x"*1001}).status_code==422
def test_bad_top_k(client): assert client.post("/api/search",json={"question":"example","k":0}).status_code==422
def test_metrics_not_run(client): assert client.get("/api/evaluations").status_code==404
def test_bad_export_format(client): assert client.get("/api/export?format=sql").status_code==400
def test_second_page_preview(client):
    import io
    from reportlab.pdfgen import canvas
    output=io.BytesIO(); c=canvas.Canvas(output,invariant=1)
    c.drawString(40,740,"Atlas40 Service uses Shield40 Protocol."); c.showPage()
    c.drawString(40,740,"Cedar40 Team reports to Assurance40 Council.");c.save()
    doc=client.post("/api/ingest",files={"file":("two-pages.pdf",output.getvalue())}).json()
    content=client.get(f"/api/documents/{doc['id']}").json()
    assert doc["pages"]==2 and content["page_data"][1]["page"]==2
    assert client.get(f"/api/documents/{doc['id']}/pages/2").status_code==200
