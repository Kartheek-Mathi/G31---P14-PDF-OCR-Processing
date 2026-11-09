from __future__ import annotations
import re, time
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from .schema import entity_key


def plan(question: str, seed_type: str = "Service") -> list[str]:
    q = question.lower()
    if re.search(r"budget|price|salary|carbon|warranty|annual cost", q): return []
    if "council" in q and any(w in q for w in ["manag", "team", "operat"]):
        return ["MANAGED_BY", "REPORTS_TO"]
    if any(w in q for w in ["how long", "retention", "kept", "retain", "expire"]):
        return ["RETENTION"] if seed_type == "Archive" else ["STORES_IN", "RETENTION"]
    if any(w in q for w in ["stored", "archive", "record destination", "deposited"]): return ["STORES_IN"]
    if any(w in q for w in ["safeguard", "policy", "must", "require", "mandatory"]): return ["REQUIRES"]
    if any(w in q for w in ["protection", "protocol", "communicat", "transport", "encrypt"]): return ["USES"]
    if any(w in q for w in ["manage", "managing", "owner", "responsib", "operate"]): return ["MANAGED_BY"]
    if any(w in q for w in ["hosted", "facility", "located", "deployment"]): return ["LOCATED_IN"]
    if any(w in q for w in ["alert", "notif", "warning"]): return ["ALERTS"]
    if any(w in q for w in ["reports to", "accountable", "council"]): return ["REPORTS_TO"]
    return []

class Retriever:
    def __init__(self, chunks: list[dict], triples: list[dict]):
        self.chunks, self.triples = chunks, triples
        self.by_id = {c["id"]: c for c in chunks}
        self.entities = sorted({v for t in triples for v in (t["subject"],t["object"])}, key=len, reverse=True)
        self.vectorizer = TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform([c["text"] for c in chunks]) if chunks else None
    def seeds(self, question: str) -> list[str]:
        q = entity_key(question)
        return [e for e in self.entities if re.search(r"(?<!\w)" + re.escape(entity_key(e)) + r"(?!\w)", q)]
    def trace(self, question: str) -> dict:
        seeds = self.seeds(question)
        if len(seeds) != 1:
            return {"path": [], "edges": [], "answers": [], "status": "entity_not_unique",
                    "message": "Name exactly one indexed entity to trace a workflow relation."}
        seed = seeds[0]; relation_path = plan(question, seed.rsplit(" ", 1)[-1])
        if not relation_path:
            return {"path": [], "edges": [], "answers": [], "status": "unsupported_question",
                    "message": "The indexed graph does not support that question type. No answer was generated."}
        frontier = {entity_key(seed)}; evidence = []
        for predicate in relation_path:
            links = [t for t in self.triples if entity_key(t["subject"]) in frontier and t["predicate"] == predicate]
            if not links:
                return {"path": relation_path, "edges": evidence, "answers": [], "status": "insufficient_evidence",
                        "message": "No complete evidence path was found. No answer was generated."}
            evidence.extend(links); frontier = {entity_key(t["object"]) for t in links}
        answers = sorted({t["object"] for t in links})
        return {"path": relation_path, "edges": evidence, "answers": answers,
                "status": "supported" if len(answers)==1 else "multiple_supported_answers",
                "message": "; ".join(answers)}
    def search(self, question: str, method: str = "graph", k: int = 5) -> dict:
        if not question.strip(): raise ValueError("Enter a nonempty question.")
        if method not in {"lexical", "graph"}: raise ValueError("Method must be lexical or graph.")
        started = time.perf_counter()
        trace = self.trace(question)
        if self.matrix is None: return {"results": [], "trace": trace, "milliseconds": 0.0}
        scores = np.asarray(self.matrix @ self.vectorizer.transform([question]).T.toarray()).ravel()
        graph_chunks = {edge["chunk_id"] for edge in trace["edges"]} if trace["answers"] else set()
        # A documented ontology-guided boost, not a general-purpose neural reranker.
        boost = np.array([1.0 if c["id"] in graph_chunks else 0.0 for c in self.chunks]) if method == "graph" else 0.0
        combined = scores + boost
        order = np.argsort(-combined, kind="stable")[:max(1, min(k, 20))]
        results = [{**self.chunks[int(i)], "score": float(combined[i]), "lexical_score": float(scores[i]),
                    "graph_support": self.chunks[int(i)]["id"] in graph_chunks} for i in order if combined[i] > 0]
        return {"results": results, "trace": trace, "milliseconds": (time.perf_counter()-started)*1000,
                "method": method}
