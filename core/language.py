"""Resource-driven language/intent evidence and protected lexical normalization."""

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.config import get_config
from core.entities import EntityProtector, ProtectedText


@dataclass
class Detection:
    language: str
    confidence: float
    languages: list[str]
    mixed: bool
    evidence: dict[str, float]


@dataclass
class Intent:
    name: str
    confidence: float
    text: str
    inherited: bool = False


@dataclass
class Analysis:
    protected: ProtectedText
    detection: Detection
    normalized: str
    requests: list[Intent] = field(default_factory=list)


class LanguageResources:
    def load(self) -> dict[str, dict[str, Any]]:
        cfg = get_config()
        root = Path(cfg.get("conversation.resource_directory"))
        resources = {}
        for code in cfg.languages:
            if not re.fullmatch(r"[a-z][a-z0-9_-]*", code):
                raise ValueError("Invalid configured language code")
            data = json.loads((root / f"{code}.json").read_text(encoding="utf-8"))
            for key in ("markers", "script_ranges", "entities", "replacements", "intents", "messages", "split_pattern", "followup_pattern"):
                if key not in data:
                    raise ValueError(f"Language resource missing {key}: {code}")
            if "support" not in data:
                raise ValueError(f"Language resource missing support: {code}")
            resources[code] = data
        if cfg.get("conversation.default_language") not in resources:
            raise ValueError("Default language must be enabled with resources")
        return resources


class LanguageProcessor:
    def __init__(self) -> None:
        self.resources = LanguageResources()
        self.protector = EntityProtector()

    @staticmethod
    def matches(text: str, rules: list[dict[str, str]]) -> bool:
        return any(re.search(rule["pattern"], text, re.IGNORECASE)
                   and not (rule.get("exclude") and re.search(rule["exclude"], text, re.IGNORECASE))
                   for rule in rules)

    def protect(self, text: str, resources: dict[str, dict[str, Any]]) -> ProtectedText:
        cfg = get_config()
        patterns = list(cfg.get("conversation.common_entity_patterns"))
        # Correction groups have priority over ordinary identifiers and names.
        corrections = [r for data in resources.values() for r in data["entities"] if "groups" in r]
        patterns = corrections + patterns + [r for data in resources.values() for r in data["entities"] if "groups" not in r]
        return self.protector.protect(text, patterns, cfg.get("conversation.entity_token_pattern"))

    def transform(self, text: str, resources: dict[str, dict[str, Any]]) -> str:
        token_pattern = get_config().get("conversation.entity_token_pattern")
        pieces = re.split(f"({token_pattern})", text)
        rules = [rule for data in resources.values() for rule in data["replacements"]]
        rules.sort(key=lambda r: len(r["pattern"]), reverse=True)
        for i, piece in enumerate(pieces):
            if re.fullmatch(token_pattern, piece):
                continue
            value = unicodedata.normalize("NFC", piece).casefold()
            for rule in rules:
                value = re.sub(rule["pattern"], rule["value"], value, flags=re.IGNORECASE)
            pieces[i] = value
        return "".join(pieces)

    def detect(self, protected: str, resources: dict[str, dict[str, Any]]) -> Detection:
        cfg = get_config()
        without_entities = re.sub(cfg.get("conversation.entity_token_pattern"), " ", protected)
        words = [w.casefold().strip(".,!?;:()\"'") for w in without_entities.split()]
        words = [w for w in words if any(c.isalpha() for c in w)]
        scores = dict.fromkeys(resources, 0.0)
        recognized = 0
        marker_owners: dict[str, list[str]] = {}
        for code, resource in resources.items():
            for marker in resource["markers"]:
                marker_owners.setdefault(marker, []).append(code)
        for word in words:
            matched = False
            for code, resource in resources.items():
                scripted = any(any(int(start, 16) <= ord(c) <= int(end, 16) for c in word)
                               for start, end in resource["script_ranges"])
                if scripted or marker_owners.get(word) == [code]:
                    scores[code] += (float(cfg.get("conversation.script_weight")) if scripted
                                     else float(cfg.get("conversation.nondefault_marker_weight"))
                                     if code != cfg.get("conversation.default_language")
                                     else float(resource.get("marker_weights", {}).get(word, 1.0)))
                    matched = True
                elif word in resource["markers"]:
                    matched = True
            recognized += int(matched)
        enabled = [code for code, score in scores.items() if score > 0]
        primary = max(scores, key=lambda c: scores[c]) if enabled else cfg.get("conversation.default_language")
        total = sum(scores.values())
        coverage = recognized / len(words) if words else 0.0
        purity = scores[primary] / total if total else 0.0
        confidence = (float(cfg.get("conversation.coverage_weight")) * coverage
                      + float(cfg.get("conversation.primary_language_weight")) * purity)
        if not enabled:
            confidence = 0.0
        return Detection(primary, confidence, enabled, len(enabled) > 1, scores)

    def analyze(self, original: str, previous_intent: str | None = None) -> Analysis:
        resources = self.resources.load()
        protected = self.protect(original, resources)
        detection = self.detect(protected.text, resources)
        normalized = self.transform(protected.text, resources)
        # Restoration is a hard invariant, not a probabilistic confidence score.
        protected.restore(normalized)
        split = "|".join(f"(?:{r['split_pattern']})" for r in resources.values())
        segments = [s.strip() for s in re.split(split, normalized, flags=re.IGNORECASE) if s.strip()]
        requests = []
        followup = "|".join(f"(?:{r['followup_pattern']})" for r in resources.values())
        for segment in segments:
            found: dict[str, float] = {}
            for data in resources.values():
                for name, rules in data["intents"].items():
                    evidence = [float(rule["confidence"]) for rule in rules
                                if re.search(rule["pattern"], segment, re.IGNORECASE)
                                and not (rule.get("exclude") and re.search(rule["exclude"], segment, re.IGNORECASE))
                                and (not rule.get("entity_usage") or any(
                                    e.usage == rule["entity_usage"] and e.token in segment for e in protected.entities))]
                    if len(evidence) >= int(get_config().get("conversation.minimum_intent_evidence")):
                        found[name] = max(found.get(name, 0.0), max(evidence))
            if found:
                requests.extend(Intent(name, score, segment) for name, score in found.items())
            elif previous_intent and re.search(followup, segment, re.IGNORECASE):
                requests.append(Intent(previous_intent, float(get_config().get("conversation.context_intent_confidence")), segment, True))
            else:
                requests.append(Intent("unknown", 0.0, segment))
        return Analysis(protected, detection, normalized, requests or [Intent("unknown", 0.0, normalized)])

    def message(self, language: str, key: str) -> str:
        return str(self.resources.load()[language]["messages"][key])

    def retrieval_text(self, protected: str) -> str:
        """Remove configured request filler while leaving entity placeholders untouched."""
        token_pattern = get_config().get("conversation.entity_token_pattern")
        resources = self.resources.load()
        pieces = re.split(f"({token_pattern})", protected)
        for i, piece in enumerate(pieces):
            if re.fullmatch(token_pattern, piece):
                continue
            for data in resources.values():
                for pattern in data.get("retrieval_noise_patterns", []):
                    piece = re.sub(pattern, " ", piece, flags=re.IGNORECASE)
            pieces[i] = piece
        return " ".join("".join(pieces).split())

    def localize(self, answer: str, language: str) -> tuple[str, bool]:
        resources = self.resources.load()
        protected = self.protect(answer, resources)
        localized = protected.text
        # Full-sentence translations are curated resources, not generated policy facts.
        for rule in resources[language].get("answer_translations", []):
            pattern = re.escape(rule["source"]).replace(r"\ ", r"\s+")
            for punctuation in (r"\.", r"\,", r"\!", r"\?"):
                pattern = pattern.replace(punctuation, r"\s*" + punctuation)
            localized = re.sub(pattern, lambda match, target=rule["target"]: target, localized, flags=re.IGNORECASE)
        return protected.restore(localized), localized != protected.text
