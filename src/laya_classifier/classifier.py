from dataclasses import dataclass
from math import isfinite
from typing import Any, Protocol

from .rules import CLASSIFICATION_QUESTION, IFRS18Category, QUESTION_ID, REVIEW_OPTION


class Predictor(Protocol):
    def predict(self, state: str | dict, questions: dict[str, Any]) -> dict[str, Any]: ...


@dataclass(frozen=True)
class AccountClassification:
    category: IFRS18Category | None
    confidence: float | None
    needs_review: bool


class IFRS18Classifier:
    def __init__(
        self,
        predictor: Predictor | None = None,
        minimum_confidence: float = 0.7,
    ) -> None:
        if not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError("minimum_confidence must be between 0.0 and 1.0")

        self._predictor = predictor
        self.minimum_confidence = minimum_confidence

    def classify(self, account_description: str) -> AccountClassification:
        if not account_description.strip():
            raise ValueError("account_description cannot be empty")

        response = self._get_predictor().predict(
            {"account_description": account_description}, CLASSIFICATION_QUESTION
        )
        answer = response.get("answers", {}).get(QUESTION_ID, {})
        choice = answer.get("choice")
        confidence = answer.get("answer_confidence", answer.get("confidence"))
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            return AccountClassification(None, None, True)

        confidence = float(confidence)
        if not isfinite(confidence) or not 0.0 <= confidence <= 1.0:
            return AccountClassification(None, None, True)

        if choice == REVIEW_OPTION:
            return AccountClassification(None, confidence, True)

        try:
            category = IFRS18Category(choice)
        except (TypeError, ValueError):
            return AccountClassification(None, confidence, True)

        return AccountClassification(
            category=category,
            confidence=confidence,
            needs_review=confidence < self.minimum_confidence,
        )

    def _get_predictor(self) -> Predictor:
        if self._predictor is None:
            from laya import Router

            self._predictor = Router()
        return self._predictor