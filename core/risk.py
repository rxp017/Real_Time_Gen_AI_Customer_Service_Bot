"""Reported high-risk issues, detected independently of sentiment decisions."""

import re

from core.config import get_config
from core.language import LanguageProcessor


class HighRiskDetector:
    def __init__(self, language: LanguageProcessor | None = None) -> None:
        self.language = language or LanguageProcessor()

    def detect(self, message: str) -> list[str]:
        resources = self.language.resources.load()
        protected = self.language.protect(message, resources)
        clauses = [clause + "\n" + self.language.transform(clause, resources)
                   for clause in re.split(get_config().get("support.risk_clause_pattern"), protected.text)]
        return sorted({kind for resource in resources.values()
                       for kind, rules in resource["support"]["high_risk"].items()
                       if any(self.language.matches(clause, rules) for clause in clauses)})
