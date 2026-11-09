from __future__ import annotations
import re
import torch
from torch import nn

TOKEN = re.compile(r"<[^>]+>|[a-z]+|\d+|[^\w\s]")

def tokens(text: str) -> list[str]:
    return TOKEN.findall(text.lower())

def encode(text: str, vocabulary: dict[str, int]) -> list[int]:
    return [vocabulary.get(token, 1) for token in tokens(text)[:96]] or [1]

class RelationModel(nn.Module):
    """Small task-trained BiLSTM; not a pretrained LLM or foundation model."""
    def __init__(self, vocabulary_size: int, labels: int):
        super().__init__()
        self.embedding = nn.Embedding(vocabulary_size, 32, padding_idx=0)
        self.encoder = nn.LSTM(32, 32, batch_first=True, bidirectional=True)
        self.classifier = nn.Sequential(nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, labels))
    def forward(self, ids: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        embedded = self.embedding(ids)
        packed = nn.utils.rnn.pack_padded_sequence(embedded, lengths.cpu(), batch_first=True, enforce_sorted=False)
        packed_out, _ = self.encoder(packed)
        encoded, _ = nn.utils.rnn.pad_packed_sequence(packed_out, batch_first=True, total_length=ids.shape[1])
        mask = torch.arange(ids.shape[1], device=ids.device)[None, :] >= lengths[:, None]
        pooled = encoded.masked_fill(mask[:, :, None], -1e9).max(dim=1).values
        return self.classifier(pooled)
