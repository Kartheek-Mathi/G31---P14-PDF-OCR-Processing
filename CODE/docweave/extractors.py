from __future__ import annotations
from pathlib import Path
import json
import re
from .schema import Chunk, Triple, make_triple, entities, LABELS, masked

# The conservative rule baseline deliberately supports fewer paraphrases.
RULES = [
    ("MANAGED_BY", r"\b(managed by|manages)\b"),
    ("USES", r"\b(uses|communicates through)\b"),
    ("STORES_IN", r"\b(stores records in|stores data in)\b"),
    ("REQUIRES", r"\b(requires|must follow)\b"),
    ("LOCATED_IN", r"\b(hosted in|located in)\b"),
    ("REPORTS_TO", r"\b(reports to|is accountable to)\b"),
    ("RETENTION", r"\b(retains records for|keeps records for)\b"),
    ("ALERTS", r"\b(sends alerts to|notifies)\b"),
]
NEGATION = re.compile(r"\b(not|never|may|might|proposed|hypothetical)\b", re.I)

class RuleExtractor:
    name = "rules"
    def label(self, text: str) -> tuple[str, float]:
        if NEGATION.search(text):
            return "NO_RELATION", 1.0
        for relation, pattern in RULES:
            if re.search(pattern, text, re.I):
                return relation, 1.0
        return "NO_RELATION", 1.0
    def extract(self, chunk: Chunk) -> list[Triple]:
        label, score = self.label(chunk.text)
        triple = make_triple(chunk, label, score, self.name)
        return [triple] if triple else []

class NeuralExtractor:
    name = "bilstm"
    def __init__(self, model_dir: Path):
        from .neural import RelationModel, encode
        import torch
        self.torch, self.encode = torch, encode
        torch.set_num_threads(1)
        metadata = json.loads((model_dir / "bilstm.json").read_text())
        self.vocab = metadata["vocabulary"]
        self.model = RelationModel(len(self.vocab), len(LABELS))
        self.model.load_state_dict(torch.load(model_dir / "bilstm.pt", map_location="cpu", weights_only=True))
        self.model.eval()
    def label(self, text: str) -> tuple[str, float]:
        ids = self.encode(masked(text), self.vocab)
        with self.torch.inference_mode():
            values = self.model(self.torch.tensor([ids]), self.torch.tensor([len(ids)]))
            probabilities = values.softmax(-1)[0]
        index = int(probabilities.argmax())
        return LABELS[index], float(probabilities[index])
    def extract(self, chunk: Chunk) -> list[Triple]:
        if len(entities(chunk.text)) < 2:
            return []
        label, confidence = self.label(chunk.text)
        # A deterministic guard rejects explicit negation/modal assertions.
        if NEGATION.search(chunk.text):
            return []
        triple = make_triple(chunk, label, confidence, self.name)
        return [triple] if triple else []

class LogisticExtractor:
    """Portable JSON/NPZ inference; no pickle loading."""
    name = "logistic"
    def __init__(self, model_dir: Path):
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer
        meta = json.loads((model_dir / "logistic.json").read_text())
        self.np = np
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), vocabulary=meta["vocabulary"])
        self.vectorizer.idf_ = np.asarray(meta["idf"])
        self.classes = meta["classes"]
        weights = np.load(model_dir / "logistic.npz", allow_pickle=False)
        self.coef, self.intercept = weights["coef"], weights["intercept"]
    def label(self, text: str) -> tuple[str, float]:
        score = self.np.asarray(self.vectorizer.transform([masked(text)]) @ self.coef.T).ravel() + self.intercept
        prob = self.np.exp(score - score.max()); prob /= prob.sum()
        index = int(prob.argmax())
        return self.classes[index], float(prob[index])
    def extract(self, chunk: Chunk) -> list[Triple]:
        if len(entities(chunk.text)) < 2 or NEGATION.search(chunk.text):
            return []
        label, confidence = self.label(chunk.text)
        triple = make_triple(chunk, label, confidence, self.name)
        return [triple] if triple else []

def get_extractor(name: str, model_dir: Path):
    if name == "rules": return RuleExtractor()
    if name == "neural": return NeuralExtractor(model_dir)
    if name == "logistic": return LogisticExtractor(model_dir)
    if name == "ollama":
        from .adapters import OllamaExtractor
        return OllamaExtractor()
    raise ValueError("Extractor must be rules, logistic, neural, or ollama.")
