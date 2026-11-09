"""Generate original fictional workflow PDFs and deterministic independent gold records."""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import random
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageFilter
import io
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from docweave.pdf_io import render_page

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = {
 "MANAGED_BY": ["{s} is managed by {o}.", "{o} manages {s}.", "{s} is operated by {o}.", "Responsibility for {s} lies with {o}.", "{o} oversees {s}."],
 "USES": ["{s} uses {o}.", "{s} communicates through {o}.", "Traffic from {s} is protected by {o}.", "{s} relies on {o} for transport security.", "{o} secures communications for {s}."],
 "STORES_IN": ["{s} stores records in {o}.", "{s} stores data in {o}.", "Records from {s} are deposited in {o}.", "{o} holds the records produced by {s}.", "The record destination for {s} is {o}."],
 "REQUIRES": ["{s} requires {o}.", "{s} must follow {o}.", "Operation of {s} is governed by {o}.", "{o} is mandatory for {s}.", "{s} is subject to {o}."],
 "LOCATED_IN": ["{s} is hosted in {o}.", "{s} is located in {o}.", "{o} houses {s}.", "The deployment site for {s} is {o}.", "{s} runs at {o}."],
 "REPORTS_TO": ["{s} reports to {o}.", "{s} is accountable to {o}.", "Oversight of {s} belongs to {o}.", "{o} supervises {s}.", "{s} works under the authority of {o}."],
 "RETENTION": ["{s} retains records for {o}.", "{s} keeps records for {o}.", "Records in {s} expire after {o}.", "The retention period of {s} is {o}.", "{s} preserves stored records for {o}."],
 "ALERTS": ["{s} sends alerts to {o}.", "{s} notifies {o}.", "Incident notifications from {s} reach {o}.", "{o} receives warnings from {s}.", "{s} directs incident messages to {o}."],
}

def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(); root = args.root
    for sub in ["raw", "scans", "annotations"]: (root / "DATA" / sub).mkdir(parents=True, exist_ok=True)
    docs, examples, queries = [], [], []
    rng = random.Random(573)
    for number in range(1, 49):
        split = "train" if number <= 30 else "dev" if number <= 39 else "test"
        s = f"Atlas{number:02d} Service"; team = f"Cedar{number:02d} Team"
        archive = f"Granite{number:02d} Archive"; council = f"Assurance{number:02d} Council"
        targets = {"MANAGED_BY": (s, team), "USES": (s, f"Shield{number:02d} Protocol"),
                   "STORES_IN": (s, archive), "REQUIRES": (s, f"Dual{number:02d} Policy"),
                   "LOCATED_IN": (s, f"Desert{number:02d} Facility"), "REPORTS_TO": (team, council),
                   "RETENTION": (archive, f"{30 + number} days"), "ALERTS": (s, f"Signal{number:02d} Team")}
        records = []
        for j, (label, (subject, obj)) in enumerate(targets.items()):
            # Variant 4 is reserved for a separately reported paraphrase stress slice.
            variant = (number + j) % 4
            text = TEMPLATES[label][variant].format(s=subject, o=obj)
            records.append({"text": text, "label": label, "subject": subject, "object": obj,
                            "template_id": f"{label}-{variant}"})
        records += [
            {"text": f"Legacy{number:02d} Service does not use Weak{number:02d} Protocol.", "label": "NO_RELATION", "subject": "", "object": "", "template_id": "NEGATION"},
            {"text": f"Future{number:02d} Service may store records in Planned{number:02d} Archive.", "label": "NO_RELATION", "subject": "", "object": "", "template_id": "MODAL"},
        ]
        order = list(records); rng.shuffle(order)
        name = f"workflow-{number:02d}.pdf"; path = root / "DATA/raw" / name
        title = f"Workflow record {number:02d}"
        c = canvas.Canvas(str(path), pagesize=(612, 792), invariant=1, pageCompression=1)
        c.setTitle(title); c.setAuthor("DocWeave synthetic benchmark generator")
        c.setFillColor(HexColor("#132B3E")); c.rect(0, 690, 612, 102, fill=1, stroke=0)
        c.setFillColor(HexColor("#FFFFFF")); c.setFont("Helvetica-Bold", 24); c.drawString(44, 742, title)
        c.setFont("Helvetica", 10); c.drawString(44, 718, "Fictional workflow specification | WorkflowBench-S v1")
        c.setFillColor(HexColor("#111827")); y = 648
        for item in order:
            c.setFont("Helvetica", 10.5); c.drawString(44, y, item["text"]); y -= 42
        c.setFont("Helvetica", 9); c.setFillColor(HexColor("#526372"))
        c.drawString(44, 128, "Synthetic examples only. Not a real organization, contract, or operating policy.")
        c.drawString(44, 109, "Negated and tentative statements are not affirmative knowledge-graph facts.")
        c.save()
        gold = {"file": name, "split": split, "number": number, "title": title,
                "records": order, "bytes": path.stat().st_size, "pages": 1}
        docs.append(gold)
        for record in records:
            examples.append({**record, "file": name, "split": split})
        if split == "test":
            mapping = {r["label"]: r["text"] for r in records if r["label"] != "NO_RELATION"}
            questions = [
                ("literal", f"Who manages {s}?", ["MANAGED_BY"]),
                ("literal", f"Where are records from {s} stored?", ["STORES_IN"]),
                ("paraphrase", f"What safeguard must {s} follow?", ["REQUIRES"]),
                ("paraphrase", f"Which communication protection is used by {s}?", ["USES"]),
                ("two_hop", f"Which council supervises the team managing {s}?", ["MANAGED_BY", "REPORTS_TO"]),
                ("two_hop", f"How long are records kept in the archive used by {s}?", ["STORES_IN", "RETENTION"]),
                ("unanswerable", f"What is the annual budget of {s}?", []),
            ]
            for index, (kind, question, path_rel) in enumerate(questions):
                queries.append({"id": f"q{number:02d}-{index}", "file": name, "group": number, "kind": kind,
                                "question": question, "gold_quotes": [mapping[r] for r in path_rel],
                                "gold_answer": targets[path_rel[-1]][1] if path_rel else None})
    stress = []
    for doc in docs[-9:]:
        for row in doc["records"]:
            if row["label"] != "NO_RELATION":
                stress.append({**row, "file": doc["file"], "split": "paraphrase_stress",
                               "text": TEMPLATES[row["label"]][4].format(s=row["subject"], o=row["object"]),
                               "template_id": f"{row['label']}-4"})
    write_jsonl(root / "DATA/annotations/documents.jsonl", docs)
    write_jsonl(root / "DATA/annotations/relations.jsonl", examples)
    write_jsonl(root / "DATA/annotations/queries.jsonl", queries)
    write_jsonl(root / "DATA/annotations/paraphrase_stress.jsonl", stress)
    # Four image-only PDFs for OCR smoke testing, derived only from held-out documents.
    scan_manifest = []
    for index, doc in enumerate(docs[-4:]):
        source = root / "DATA/raw" / doc["file"]
        image = Image.open(io.BytesIO(render_page(source.read_bytes(), 1, 2.0))).convert("RGB")
        condition = "clean"
        if index % 2:
            image = image.filter(ImageFilter.GaussianBlur(0.55))
            image = image.rotate(0.5, expand=False, fillcolor="white")
            condition = "blur_0.55_rotation_0.5deg"
        scan = root / "DATA/scans" / (source.stem + "-scan.pdf")
        c = canvas.Canvas(str(scan), pagesize=(612, 792), invariant=1)
        c.drawImage(ImageReader(image), 0, 0, width=612, height=792); c.save()
        scan_manifest.append({"file": scan.name, "source": source.name, "condition": condition,
                              "independent_document": False})
    (root / "DATA/annotations/scans.json").write_text(json.dumps(scan_manifest, indent=2))
    print(json.dumps({"documents": len(docs), "relation_examples": len(examples), "queries": len(queries),
                      "stress_examples": len(stress), "scan_pages": len(scan_manifest)}, indent=2))

if __name__ == "__main__": main()
