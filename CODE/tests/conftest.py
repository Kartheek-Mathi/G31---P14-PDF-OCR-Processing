from pathlib import Path
import sys, io
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reportlab.pdfgen import canvas
from fastapi.testclient import TestClient
from docweave.server import create_app

@pytest.fixture
def pdf_bytes():
    output=io.BytesIO(); c=canvas.Canvas(output,invariant=1)
    c.drawString(40,740,"Atlas40 Service is managed by Cedar40 Team.")
    c.drawString(40,710,"Cedar40 Team reports to Assurance40 Council.")
    c.save(); return output.getvalue()

@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path,extractor_name="rules"))
