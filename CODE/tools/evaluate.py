"""Produce measured metrics, predictions, OCR evidence and bootstrap intervals."""
from __future__ import annotations
import json, sys, csv, io, platform, time, subprocess, shutil
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
import importlib.metadata
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from docweave.schema import LABELS, Chunk, normalize, entities
from docweave.extractors import get_extractor
from docweave.pdf_io import extract_pages, chunks_from_pages, render_page, ocr_images
from docweave.store import Store
from docweave.pipeline import Pipeline
from docweave.retrieval import Retriever
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "EVALUATIONS/results"

def read_jsonl(path): return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
def save_jsonl(path, rows): path.write_text("".join(json.dumps(r) + "\n" for r in rows))
def save_csv(path, rows):
    if not rows: return
    with path.open("w",newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)

def prf(pred: set, gold: set) -> dict:
    tp, fp, fn = len(pred & gold), len(pred - gold), len(gold - pred)
    p = tp / (tp+fp) if tp+fp else 0.0; r = tp / (tp+fn) if tp+fn else 0.0
    return {"precision":p, "recall":r, "f1": 2*p*r/(p+r) if p+r else 0.0,
            "tp":tp,"fp":fp,"fn":fn}

def edit_distance(a, b):
    if len(a)<len(b): a,b=b,a
    last = list(range(len(b)+1))
    for i, x in enumerate(a,1):
        current=[i]
        for j,y in enumerate(b,1): current.append(min(current[-1]+1,last[j]+1,last[j-1]+(x!=y)))
        last=current
    return last[-1]

def bootstrap_by_document(rows: list[dict], key: str, seed=573):
    groups=sorted({r["group"] for r in rows}); lookup={g:np.array([r[key] for r in rows if r["group"]==g]) for g in groups}
    rng=np.random.default_rng(seed); values=[]
    for _ in range(2000):
        sample=rng.choice(groups,size=len(groups),replace=True)
        values.append(float(np.concatenate([lookup[int(g)] for g in sample]).mean()))
    return [float(x) for x in np.quantile(values,[0.025,0.975])]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    docs=read_jsonl(ROOT/"DATA/annotations/documents.jsonl")
    examples=read_jsonl(ROOT/"DATA/annotations/relations.jsonl")
    stress=read_jsonl(ROOT/"DATA/annotations/paraphrase_stress.jsonl")
    queries=read_jsonl(ROOT/"DATA/annotations/queries.jsonl")
    model_dir=ROOT/"DATA/models"
    extractors={n:get_extractor(n,model_dir) for n in ["rules","logistic","neural"]}
    metrics={"run_utc":datetime.now(timezone.utc).isoformat(),"seed":573,
        "data":{"source":"original, AI-assisted synthetic workflow benchmark; not public or team-supplied data",
                "documents":len(docs),"pages":sum(d["pages"] for d in docs),"raw_bytes":sum(d["bytes"] for d in docs),
                "splits":{s:sum(d["split"]==s for d in docs) for s in ["train","dev","test"]},
                "relation_examples":len(examples),"test_examples":sum(r["split"]=="test" for r in examples),
                "stress_examples":len(stress),"queries":len(queries),"answerable_queries":sum(q["kind"]!="unanswerable" for q in queries),
                "test_document_groups":9,"scan_pages":4},"relation_classification":{},"triples":{},"retrieval":{},"ocr":{},
        "optional_integrations":{"ollama":"adapter included; live service NOT evaluated", "neo4j":"parameterized exporter included; live service NOT evaluated", "docling":"converter included; NOT evaluated", "sentence_transformers":"not used; package/model download unavailable"},
        "limitations":["Synthetic closed-schema pilot, not a real-world accuracy benchmark.","Train/dev/test entities are disjoint but normal-test phrasing templates overlap training.","Stress paraphrases are template-disjoint; only 72 positive statements and no new entity schema.","Question planning uses handcrafted schema rules; this is not unrestricted natural-language reasoning.","Confidence scores are not calibrated probabilities of correctness.","Four derived scan pages are a smoke test, not four independent documents.","No human usability study or production security review was performed."]}
    predictions=[]; confusion={}
    for name,extractor in extractors.items():
        metrics["relation_classification"][name]={}; confusion[name]={}
        for slice_name,rows in [("test",[r for r in examples if r["split"]=="test"]),("paraphrase_stress",stress)]:
            actual=[]; predicted=[]
            for row in rows:
                label,confidence=extractor.label(row["text"])
                actual.append(row["label"]); predicted.append(label)
                predictions.append({"method":name,"slice":slice_name,"file":row["file"],"text":row["text"],
                    "gold":row["label"],"predicted":label,"score":confidence,"correct":label==row["label"]})
            labels=LABELS if slice_name=="test" else LABELS[:-1]
            metrics["relation_classification"][name][slice_name]={
                "accuracy":float(accuracy_score(actual,predicted)),
                "macro_f1":float(f1_score(actual,predicted,labels=labels,average="macro",zero_division=0)),"n":len(rows)}
            confusion[name][slice_name]=confusion_matrix(actual,predicted,labels=LABELS).tolist()
    # Actual native PDF extraction on all 48 PDFs; annotation text is never an inference input.
    parsed={}; all_chunks=[]; parse_start=time.perf_counter()
    for doc in docs:
        data=(ROOT/"DATA/raw"/doc["file"]).read_bytes()
        did,pages=extract_pages(data,allow_ocr=False)
        chunks=chunks_from_pages(did,pages)
        parsed[doc["file"]]=(did,pages,chunks)
        all_chunks.extend([{**c.__dict__,"filename":doc["file"]} for c in chunks])
    metrics["native_extraction"]={"seconds":time.perf_counter()-parse_start,"chunks":len(all_chunks),
        "all_gold_sentences_recovered":all(any(normalize(r["text"])==c.text for c in parsed[d["file"]][2]) for d in docs for r in d["records"])}
    triple_predictions=[]; neural_triples=[]
    for name,extractor in extractors.items():
        predset=set(); goldset=set(); count=0; started=time.perf_counter()
        for doc in docs:
            did,pages,chunks=parsed[doc["file"]]
            triples=[t for c in chunks for t in extractor.extract(c)]
            if name=="neural":
                chunk_map={c.id:c for c in chunks}
                neural_triples.extend([{**t.to_dict(),"filename":doc["file"],"document_id":did,"page":chunk_map[t.chunk_id].page} for t in triples])
            if doc["split"]!="test": continue
            for t in triples:
                key=(doc["file"],t.subject,t.predicate,t.object)
                predset.add(key); triple_predictions.append({"method":name,"file":doc["file"],**t.to_dict()})
            goldset|={(doc["file"],r["subject"],r["label"],r["object"]) for r in doc["records"] if r["label"]!="NO_RELATION"}
        metrics["triples"][name]={**prf(predset,goldset),"seconds_all_documents":time.perf_counter()-started,
                                 "gold_test_triples":len(goldset)}
    save_jsonl(ROOT/"DATA/processed/chunks.jsonl",all_chunks)
    save_jsonl(ROOT/"DATA/processed/triples.jsonl",neural_triples)
    metrics["graph"]={"nodes":len({x for t in neural_triples for x in [t["subject"],t["object"]]}),
        "edges":len(neural_triples),"predicates":len({t["predicate"] for t in neural_triples})}
    index=Retriever(all_chunks,neural_triples)
    retrieval_rows=[]; answer_rows=[]
    for method in ["lexical","graph"]:
        for query in queries:
            response=index.search(query["question"],method=method,k=5)
            if query["kind"]=="unanswerable":
                if method=="graph": answer_rows.append({"id":query["id"],"expected":None,"answers":response["trace"]["answers"],"status":response["trace"]["status"],"correct":not response["trace"]["answers"]})
                continue
            gold=set(query["gold_quotes"]); hits=[r["text"] in gold and r["filename"]==query["file"] for r in response["results"]]
            # Every gold evidence chunk is unique in this generated corpus.
            ranks=[i+1 for i,hit in enumerate(hits) if hit]
            dcg=sum(1/np.log2(i+2) for i,hit in enumerate(hits) if hit)
            ideal=sum(1/np.log2(i+2) for i in range(min(len(gold),5)))
            row={"method":method,"id":query["id"],"group":query["group"],"kind":query["kind"],"question":query["question"],
                "recall_at_1":sum(hits[:1])/len(gold),"recall_at_5":sum(hits)/len(gold),
                "mrr_at_5":1/min(ranks) if ranks else 0.,"ndcg_at_5":float(dcg/ideal),
                "complete_evidence_at_5":float(sum(hits)==len(gold)),"milliseconds":response["milliseconds"],
                "ranked_chunk_ids":";".join(r["id"] for r in response["results"])}
            retrieval_rows.append(row)
            if method=="graph": answer_rows.append({"id":query["id"],"expected":query["gold_answer"],"answers":response["trace"]["answers"],
                "status":response["trace"]["status"],"correct":response["trace"]["answers"]==[query["gold_answer"]]})
        method_rows=[r for r in retrieval_rows if r["method"]==method]
        result={k:float(np.mean([r[k] for r in method_rows])) for k in ["recall_at_1","recall_at_5","mrr_at_5","ndcg_at_5","complete_evidence_at_5"]}
        result["recall_at_5_ci95_document_bootstrap"]=bootstrap_by_document(method_rows,"recall_at_5")
        result["latency_median_ms"]=float(np.median([r["milliseconds"] for r in method_rows]))
        result["latency_p95_ms"]=float(np.percentile([r["milliseconds"] for r in method_rows],95))
        result["n"]=len(method_rows)
        result["by_kind"]={kind:{k:float(np.mean([r[k] for r in method_rows if r["kind"]==kind])) for k in ["recall_at_5","mrr_at_5","complete_evidence_at_5"]} for kind in ["literal","paraphrase","two_hop"]}
        metrics["retrieval"][method]=result
    supported=[r for r in answer_rows if r["expected"] is not None]; unsupported=[r for r in answer_rows if r["expected"] is None]
    metrics["answers"]={"exact_match":float(np.mean([r["correct"] for r in supported])),"n_answerable":len(supported),
        "unanswerable_abstention":float(np.mean([r["correct"] for r in unsupported])),"n_unanswerable":len(unsupported),
        "generation":"deterministic evidence-path endpoint; no LLM answer generation"}
    # OCR is actually necessary here: image-only pages have no native text.
    scans=json.loads((ROOT/"DATA/annotations/scans.json").read_text()); images=[]; native_empty=[]
    for scan in scans:
        data=(ROOT/"DATA/scans"/scan["file"]).read_bytes(); _,pages=extract_pages(data,allow_ocr=False)
        native_empty.append(all(p["method"]=="empty" for p in pages)); images.append(render_page(data,1,2.2))
    ocr_start=time.perf_counter(); recognized=ocr_images(images)
    ocr_rows=[]; total_char_error=total_chars=total_word_error=total_words=0
    for scan,text in zip(scans,recognized):
        reference=normalize(parsed[scan["source"]][1][0]["text"]); predicted=normalize(text)
        char_error=edit_distance(reference,predicted); word_error=edit_distance(reference.split(),predicted.split())
        total_char_error+=char_error; total_chars+=len(reference); total_word_error+=word_error; total_words+=len(reference.split())
        ocr_rows.append({**scan,"cer":char_error/max(len(reference),1),"wer":word_error/max(len(reference.split()),1),
            "reference":reference,"recognized":predicted})
    metrics["ocr"]={"pages":len(scans),"all_native_empty":all(native_empty),
        "character_error_rate":total_char_error/total_chars,"word_error_rate":total_word_error/total_words,
        "seconds_batch":time.perf_counter()-ocr_start,"scope":"4 image-only derived pages; one Tesseract batch; whitespace normalized; case and punctuation retained"}
    # Evaluation does not mutate the application database. Use run.py seed separately.
    packages={}
    for name in ["torch","pypdf","pypdfium2","numpy","scikit-learn","fastapi","uvicorn","reportlab","python-pptx","Pillow","pytest","httpx"]:
        packages[name]=importlib.metadata.version(name)
    environment={"python":platform.python_version(),"platform":platform.platform(),"processor":platform.processor(),"packages":packages,
        "tesseract":subprocess.check_output([shutil.which("tesseract"),"--version"],text=True).splitlines()[0],
        "training_device":"CPU","num_threads":1,"seed":573}
    (OUT/"metrics.json").write_text(json.dumps(metrics,indent=2)); (OUT/"environment.json").write_text(json.dumps(environment,indent=2))
    (OUT/"confusion_matrices.json").write_text(json.dumps({"labels":LABELS,"matrices":confusion},indent=2))
    save_jsonl(OUT/"classification_predictions.jsonl",predictions)
    save_jsonl(OUT/"triple_predictions.jsonl",triple_predictions)
    save_jsonl(OUT/"answer_predictions.jsonl",answer_rows)
    save_jsonl(OUT/"ocr_predictions.jsonl",ocr_rows)
    save_csv(OUT/"retrieval_per_query.csv",retrieval_rows)
    print(json.dumps(metrics,indent=2))

if __name__=="__main__": main()
