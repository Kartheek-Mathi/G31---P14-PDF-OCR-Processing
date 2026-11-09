from pathlib import Path
import json
from docweave.schema import entities
from docweave.extractors import get_extractor
ROOT=Path(__file__).resolve().parents[2]

def rows(name): return [json.loads(r) for r in (ROOT/"DATA/annotations"/name).read_text().splitlines()]
def test_split_document_counts():
    docs=rows("documents.jsonl")
    assert len(docs)==48 and {s:sum(d["split"]==s for d in docs) for s in ["train","dev","test"]}=={"train":30,"dev":9,"test":9}
def test_entity_disjoint_splits():
    sets={s:set() for s in ["train","dev","test"]}
    for r in rows("relations.jsonl"): sets[r["split"]].update(entities(r["text"]))
    assert not sets["train"] & sets["dev"] and not sets["train"] & sets["test"] and not sets["dev"] & sets["test"]
def test_queries_only_test():
    test_files={d["file"] for d in rows("documents.jsonl") if d["split"]=="test"}
    assert all(q["file"] in test_files for q in rows("queries.jsonl"))
def test_stress_templates_disjoint():
    train={r["template_id"] for r in rows("relations.jsonl") if r["split"]=="train"}
    stress={r["template_id"] for r in rows("paraphrase_stress.jsonl")}
    assert not train & stress
def test_neural_checkpoint_prediction():
    e=get_extractor("neural",ROOT/"DATA/models")
    assert e.label("Atlas99 Service uses Shield99 Protocol.")[0]=="USES"
def test_logistic_checkpoint_prediction():
    e=get_extractor("logistic",ROOT/"DATA/models")
    assert e.label("Atlas99 Service is managed by Cedar99 Team.")[0]=="MANAGED_BY"
def test_metrics_not_generated_claims():
    m=json.loads((ROOT/"EVALUATIONS/results/metrics.json").read_text())
    assert m["ocr"]["all_native_empty"] and m["native_extraction"]["all_gold_sentences_recovered"]
    assert m["relation_classification"]["logistic"]["paraphrase_stress"]["macro_f1"] > m["relation_classification"]["neural"]["paraphrase_stress"]["macro_f1"]
