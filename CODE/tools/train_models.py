"""Train classical and neural relation classifiers using only the train split."""
from __future__ import annotations
from pathlib import Path
import sys, json, copy, time, platform, random
import numpy as np
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, accuracy_score
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from docweave.schema import LABELS, masked
from docweave.neural import RelationModel, tokens, encode
ROOT = Path(__file__).resolve().parents[2]

def batch(sequences, indices):
    selected = [sequences[int(i)] for i in indices]
    lengths = torch.tensor([len(x) for x in selected])
    ids = torch.zeros((len(selected), int(lengths.max())), dtype=torch.long)
    for i, row in enumerate(selected): ids[i, :len(row)] = torch.tensor(row)
    return ids, lengths

def main():
    started = time.perf_counter()
    torch.set_num_threads(1); torch.manual_seed(573); random.seed(573); np.random.seed(573)
    torch.use_deterministic_algorithms(True)
    rows = [json.loads(s) for s in (ROOT / "DATA/annotations/relations.jsonl").read_text().splitlines()]
    train = [r for r in rows if r["split"] == "train"]
    dev = [r for r in rows if r["split"] == "dev"]
    output = ROOT / "DATA/models"; output.mkdir(parents=True, exist_ok=True)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    x = vectorizer.fit_transform([masked(r["text"]) for r in train])
    logistic = LogisticRegression(C=1.0, max_iter=1000, random_state=573)
    logistic.fit(x, [r["label"] for r in train])
    np.savez_compressed(output / "logistic.npz", coef=logistic.coef_, intercept=logistic.intercept_)
    (output / "logistic.json").write_text(json.dumps({"vocabulary": {k: int(v) for k,v in vectorizer.vocabulary_.items()},
        "idf": vectorizer.idf_.tolist(), "classes": logistic.classes_.tolist(), "train_rows": len(train)}, indent=2))
    vocabulary = {"<pad>": 0, "<unk>": 1}
    for token in sorted({t for r in train for t in tokens(masked(r["text"]))}):
        if token not in vocabulary: vocabulary[token] = len(vocabulary)
    sequences = [encode(masked(r["text"]), vocabulary) for r in train]
    targets = torch.tensor([LABELS.index(r["label"]) for r in train])
    dev_seq = [encode(masked(r["text"]), vocabulary) for r in dev]
    dev_ids, dev_len = batch(dev_seq, np.arange(len(dev_seq)))
    dev_y = [LABELS.index(r["label"]) for r in dev]
    model = RelationModel(len(vocabulary), len(LABELS))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.003)
    criterion = torch.nn.CrossEntropyLoss()
    rng = np.random.default_rng(573); history = []; best_score = -1; best_epoch = 0; best_state = None
    for epoch in range(1, 101):
        model.train(); losses = []
        permutation = rng.permutation(len(train))
        for start in range(0, len(train), 32):
            indices = permutation[start:start + 32]
            ids, lengths = batch(sequences, indices)
            optimizer.zero_grad(); logits = model(ids, lengths)
            loss = criterion(logits, targets[indices]); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); optimizer.step()
            losses.append(float(loss.detach()))
        model.eval()
        with torch.inference_mode(): prediction = model(dev_ids, dev_len).argmax(-1).tolist()
        score = f1_score(dev_y, prediction, labels=list(range(len(LABELS))), average="macro", zero_division=0)
        history.append({"epoch": epoch, "loss": float(np.mean(losses)), "dev_macro_f1": float(score)})
        if score > best_score + 1e-10:
            best_score, best_epoch, best_state = score, epoch, copy.deepcopy(model.state_dict())
    torch.save(best_state, output / "bilstm.pt")
    metadata = {"vocabulary": vocabulary, "labels": LABELS, "seed": 573,
                "architecture": "embedding32-bidirectional_LSTM32-maxpool-linear32-ReLU-linear9",
                "selected_epoch": best_epoch, "dev_macro_f1": best_score, "epochs": 100,
                "train_rows": len(train), "dev_rows": len(dev), "test_used_for_selection": False,
                "training_seconds": time.perf_counter() - started, "torch": torch.__version__,
                "python": platform.python_version(), "parameter_count": sum(p.numel() for p in model.parameters())}
    (output / "bilstm.json").write_text(json.dumps(metadata, indent=2))
    (ROOT / "EVALUATIONS/results/training_history.json").write_text(json.dumps(history, indent=2))
    print(json.dumps({k: v for k,v in metadata.items() if k != "vocabulary"}, indent=2))

if __name__ == "__main__": main()
