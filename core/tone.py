"""Presentation prefaces that never modify the supplied policy answer."""

from core.config import get_config
from core.language import LanguageProcessor
from core.sentiment import Sentiment


class TonePresenter:
    def present(self, policy_answer: str, sentiment: Sentiment, enabled: bool | None = None) -> dict[str, str]:
        cfg = get_config()
        enabled = bool(cfg.get("support.tone_enabled")) if enabled is None else enabled
        prefix = ""
        if enabled and sentiment.confidence >= float(cfg.get("support.sentiment_threshold")):
            prefix = LanguageProcessor().resources.load()[sentiment.language]["support"]["tone"][sentiment.label]
        return {"policy_answer": policy_answer, "tone_prefix": prefix,
                "display_answer": prefix + "\n" + policy_answer if prefix else policy_answer}
