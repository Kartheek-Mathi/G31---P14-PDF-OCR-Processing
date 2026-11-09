"""Build plots from saved metrics and crop genuine app screenshots for the paper."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import pypdfium2 as pdfium
ROOT=Path(__file__).resolve().parents[2]
FIG=ROOT/"EVALUATIONS/figures"

def save(fig,name):
    fig.tight_layout();fig.savefig(FIG/f"{name}.png",dpi=200,bbox_inches="tight")
    fig.savefig(FIG/f"{name}.pdf",bbox_inches="tight");plt.close(fig)

def main():
    FIG.mkdir(exist_ok=True,parents=True)
    m=json.loads((ROOT/"EVALUATIONS/results/metrics.json").read_text())
    fig,ax=plt.subplots(figsize=(6.4,3.7))
    labels=["Rule baseline","TF-IDF + logistic","BiLSTM"]
    x=np.arange(3);width=.35
    a=[m["relation_classification"][k]["test"]["macro_f1"] for k in ["rules","logistic","neural"]]
    b=[m["relation_classification"][k]["paraphrase_stress"]["macro_f1"] for k in ["rules","logistic","neural"]]
    ax.bar(x-width/2,a,width,label="Standard test (90 statements)")
    ax.bar(x+width/2,b,width,label="Unseen phrasing (72 statements)")
    ax.set_xticks(x,labels);ax.set_ylim(0,1.18);ax.set_ylabel("Macro F1")
    ax.legend(loc="upper center",fontsize=8,frameon=False,ncol=1)
    for i,(v,w) in enumerate(zip(a,b)):
        ax.text(i-width/2,v+.02,f"{v:.3f}",ha="center",fontsize=9)
        ax.text(i+width/2,w+.02,f"{w:.3f}",ha="center",fontsize=9)
    ax.spines[['top','right']].set_visible(False)
    save(fig,"relation-comparison")
    fig,ax=plt.subplots(figsize=(6.4,3.7))
    labels=["Literal","Paraphrase","Two-hop"]
    x=np.arange(3)
    a=[m["retrieval"]["lexical"]["by_kind"][k]["recall_at_5"] for k in ["literal","paraphrase","two_hop"]]
    b=[m["retrieval"]["graph"]["by_kind"][k]["recall_at_5"] for k in ["literal","paraphrase","two_hop"]]
    ax.bar(x-width/2,a,width,label="TF-IDF baseline");ax.bar(x+width/2,b,width,label="Graph-assisted")
    ax.set_xticks(x,labels);ax.set_ylabel("Evidence Recall@5");ax.set_ylim(0,1.18)
    ax.legend(loc="upper center",fontsize=9,frameon=False,ncol=2)
    for i,(v,w) in enumerate(zip(a,b)):
        ax.text(i-width/2,v+.02,f"{v:.3f}",ha="center",fontsize=9);ax.text(i+width/2,w+.02,f"{w:.3f}",ha="center",fontsize=9)
    ax.spines[['top','right']].set_visible(False);save(fig,"retrieval-by-type")
    # Vector architecture drawing (not a data chart).
    path=FIG/"architecture.pdf";c=canvas.Canvas(str(path),pagesize=(800,265))
    ink=HexColor("#173247");fill=HexColor("#eef4f5");accent=HexColor("#087f8c")
    boxes=[(12,"PDF / SCAN",["Validate size and pages","Native text; OCR if empty"]),
           (210,"EXTRACT",["Typed entity candidates","Rules / logistic / BiLSTM"]),
           (408,"LINK + STORE",["Subject-predicate-object","SQLite + page provenance"]),
           (606,"RETRIEVE + VIEW",["TF-IDF + typed graph path","Source-linked interface"])]
    for x,title,lines in boxes:
        c.setFillColor(fill);c.setStrokeColor(HexColor("#b8ccd3"));c.roundRect(x,110,182,95,8,fill=1,stroke=1)
        c.setFillColor(accent);c.setFont("Helvetica-Bold",11);c.drawString(x+13,179,title)
        c.setFillColor(ink);c.setFont("Helvetica",9)
        for j,line in enumerate(lines):c.drawString(x+13,157-j*16,line)
        if x<600:
            c.setStrokeColor(ink);c.line(x+184,157,x+195,157);c.line(x+195,157,x+191,160);c.line(x+195,157,x+191,154)
    c.setFillColor(ink);c.setFont("Helvetica-Bold",12);c.drawString(12,237,"DOCWEAVE / EXECUTED CORE PIPELINE")
    c.setFont("Helvetica",10);c.drawString(12,79,"Evidence contract: original PDF hash + page + chunk ID + exact source quote on each relation")
    c.setDash(4,3);c.setStrokeColor(HexColor("#9badb4"));c.roundRect(12,14,776,41,5,stroke=1,fill=0);c.setDash()
    c.setFont("Helvetica",9);c.drawString(25,36,"Optional, not live-evaluated: Ollama LLM extraction  |  Neo4j export  |  Docling Markdown conversion")
    c.save();doc=pdfium.PdfDocument(path);page=doc[0];bitmap=page.render(scale=3);bitmap.to_pil().save(FIG/"architecture.png");bitmap.close();page.close();doc.close()
    # Crops remove surrounding navigation, preserving actual UI content.
    for name,box in {
        "02-documents.png":(280,120,1495,1100),
        "03-graph.png":(280,220,1495,920),
        "04-search.png":(280,220,1495,850),
        "05-evaluation.png":(280,110,1495,940),
    }.items():
        p=ROOT/"EVALUATIONS/screenshots"/name
        if p.exists():
            image=Image.open(p);x0,y0,x1,y1=box
            image.crop((x0,y0,min(x1,image.width),min(y1,image.height))).save(FIG/(name.replace('.png','-crop.png')))
    print("Built measured plots, vector architecture and real UI crops.")
if __name__=="__main__":main()
