"""Convert the preserved training FAQ CSV to the shared document schema."""

import csv
import io
from pathlib import Path

from core.store import Document


def faq_documents(path: str | Path = "dataset/dataset.csv") -> list[Document]:
    documents = []
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")
    with io.StringIO(text, newline="") as source:
        for index, row in enumerate(csv.DictReader(source), 1):
            if not row["prompt"].strip() or not row["response"].strip():
                raise ValueError(f"FAQ row {index} is missing a question or answer")
            documents.append(Document(f"TRAINING-FAQ-{index:04}", 1, "bootcamp", "all", "public",
                                      "2020-01-01", None, f"training-faq-{index}", row["prompt"].strip(),
                                      row["response"].strip()))
    return documents
