from __future__ import annotations
from pathlib import Path
import io
import re
import shutil
import subprocess
import tempfile
from hashlib import sha256
from pypdf import PdfReader
from .schema import Chunk, digest, normalize

MAX_BYTES = 20 * 1024 * 1024
MAX_PAGES = 50

def validate_pdf(data: bytes) -> PdfReader:
    if not data or len(data) > MAX_BYTES:
        raise ValueError("PDF must be nonempty and no larger than 20 MiB.")
    if not data.lstrip()[:8].startswith(b"%PDF-"):
        raise ValueError("The file does not have a PDF header.")
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs are not supported. Decrypt locally first.")
        if not 1 <= len(reader.pages) <= MAX_PAGES:
            raise ValueError(f"PDF must contain 1-{MAX_PAGES} pages.")
        return reader
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Cannot parse this PDF.") from exc

def render_page(data: bytes, page: int, scale: float = 1.5) -> bytes:
    import pypdfium2 as pdfium
    document = pdfium.PdfDocument(data)
    try:
        if not 1 <= page <= len(document):
            raise ValueError("Page number is outside the document.")
        p = document[page - 1]
        try:
            width, height = p.get_size()
            # Bound image allocation even for oversized source media boxes.
            actual_scale = min(scale, (4_000_000 / max(width * height, 1)) ** 0.5)
            bitmap = p.render(scale=actual_scale)
            try:
                image = bitmap.to_pil()
                output = io.BytesIO()
                image.save(output, format="PNG")
                return output.getvalue()
            finally:
                bitmap.close()
        finally:
            p.close()
    finally:
        document.close()

def ocr_images(images: list[bytes], timeout: int = 120) -> list[str]:
    """One Tesseract batch call; used only for pages with no usable native text."""
    if not images:
        return []
    executable = shutil.which("tesseract")
    if executable is None:
        raise RuntimeError("OCR requires Tesseract and its English language data.")
    with tempfile.TemporaryDirectory(prefix="docweave-ocr-") as directory:
        root = Path(directory)
        names = []
        for index, image in enumerate(images):
            path = root / f"page-{index:04d}.png"
            path.write_bytes(image)
            names.append(str(path))
        listing = root / "images.txt"
        listing.write_text("\n".join(names) + "\n")
        result = subprocess.run([executable, str(listing), "stdout", "-l", "eng", "--psm", "6"],
                                capture_output=True, timeout=timeout, check=False)
        if result.returncode:
            raise RuntimeError("Tesseract failed: " + result.stderr.decode(errors="replace")[-300:])
        pages = result.stdout.decode("utf-8", errors="replace").split("\f")
        if pages and not pages[-1].strip():
            pages.pop()
        if len(pages) != len(images):
            raise RuntimeError("OCR output page count does not match the input.")
        return pages

def extract_pages(data: bytes, allow_ocr: bool = True) -> tuple[str, list[dict]]:
    reader = validate_pdf(data)
    document_id = sha256(data).hexdigest()
    pages, empty = [], []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if len(text) > 1_000_000:
            raise ValueError("Extracted page text exceeds the local prototype limit.")
        is_empty = len(re.sub(r"\W", "", text)) < 20
        pages.append({"page": index, "text": text, "method": "empty" if is_empty else "native"})
        if is_empty:
            empty.append(index)
    if empty and allow_ocr:
        images = [render_page(data, p, scale=2.2) for p in empty]
        for page, text in zip(empty, ocr_images(images)):
            pages[page - 1] = {"page": page, "text": text, "method": "tesseract"}
    return document_id, pages

def chunks_from_pages(document_id: str, pages: list[dict]) -> list[Chunk]:
    chunks = []
    for page in pages:
        # Conservative English sentence/line boundaries; not a layout parser.
        for index, part in enumerate(re.split(r"(?<=[.!?])\s+|[\r\n]+", page["text"])):
            text = normalize(part)
            if len(text) < 8:
                continue
            # Bound chunks so a long paragraph cannot silently overflow a model.
            words = text.split()
            for offset in range(0, len(words), 100):
                segment = " ".join(words[offset:offset + 100])
                chunks.append(Chunk(digest(document_id, page["page"], index, offset, segment),
                                    document_id, page["page"], segment, page["method"]))
    return chunks
