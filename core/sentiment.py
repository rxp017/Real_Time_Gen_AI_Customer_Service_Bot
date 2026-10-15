"""History-aware sentiment evidence via the shared language resources."""

from dataclasses import dataclass
from typing import Any

from core.config import get_config
from core.language import LanguageProcessor


@dataclass(frozen=True)
class Sentiment:
    label: str
    confidence: float
    language: str
    negative: bool
    evidence: tuple[str, ...]


class SentimentClassifier:
    def __init__(self, language: LanguageProcessor | None = None) -> None:
        self.language = language or LanguageProcessor()

    def text(self, message: str, resources: dict[str, dict[str, Any]]) -> str:
        protected = self.language.protect(message, resources)
        return protected.text + "\n" + self.language.transform(protected.text, resources)

    def _labels(self, text: str, resources: dict[str, dict[str, Any]]) -> set[str]:
        return {label for resource in resources.values()
                for label, rules in resource["support"]["sentiment"].items() if self.language.matches(text, rules)}

    def classify(self, message: str, history: list[dict[str, Any]]) -> Sentiment:
        cfg = get_config()
        resources = self.language.resources.load()
        text = self.text(message, resources)
        labels = self._labels(text, resources)
        negatives = set(cfg.get("support.negative_labels"))
        recent = history[-int(cfg.get("support.history_messages")):]
        prior_negative = sum(bool(self._labels(self.text(str(item["content"]), resources), resources) & negatives)
                             for item in recent if item["role"] in {"user", "assistant"})
        context = prior_negative >= int(cfg.get("support.minimum_history_negatives"))
        if context:
            for label, key in (("sarcastic", "sarcasm_with_history"), ("frustrated", "frustration_with_history")):
                if any(self.language.matches(text, resource["support"][key]) for resource in resources.values()):
                    labels.add(label)
        label = next((name for name in cfg.get("support.label_priority") if name in labels), "neutral")
        confidence = float(cfg.get("support.context_confidence") if context and label in {"sarcastic", "frustrated"}
                           else cfg.get("support.evidence_confidence") if labels else cfg.get("support.neutral_confidence"))
        language = self.language.detect(text.split("\n", 1)[0], resources).language
        return Sentiment(label, confidence, language, bool(labels & negatives), tuple(sorted(labels)))


