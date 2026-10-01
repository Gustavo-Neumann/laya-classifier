import pytest

from laya_classifier.classifier import IFRS18Classifier
from laya_classifier.examples import EXAMPLE_ACCOUNTS
from laya_classifier.rules import (
    CATEGORY_RULES,
    CLASSIFICATION_QUESTION,
    IFRS18Category,
    QUESTION_ID,
    REVIEW_OPTION,
)
from laya_classifier.worker import classify_request


class FakePredictor:
    def __init__(self, choice: str, confidence: float = 0.95) -> None:
        self.choice = choice
        self.confidence = confidence
        self.state = None
        self.questions = None

    def predict(self, state: dict, questions: dict) -> dict:
        self.state = state
        self.questions = questions
        return {
            "answers": {
                QUESTION_ID: {
                    "choice": self.choice,
                    "answer_confidence": self.confidence,
                }
            }
        }


@pytest.mark.parametrize("example", EXAMPLE_ACCOUNTS)
def test_maps_laya_choice_to_ifrs18_category(example) -> None:
    predictor = FakePredictor(example.expected_category.value)
    classifier = IFRS18Classifier(predictor)

    result = classifier.classify(example.description)

    assert result.category == example.expected_category
    assert result.needs_review is False
    assert predictor.state == {"account_description": example.description}
    assert predictor.questions == CLASSIFICATION_QUESTION


def test_low_confidence_keeps_suggestion_and_requires_review() -> None:
    classifier = IFRS18Classifier(FakePredictor("operating", confidence=0.69))

    result = classifier.classify("Receita de venda")

    assert result.category == IFRS18Category.OPERATING
    assert result.needs_review is True


def test_review_option_has_no_ifrs_category() -> None:
    classifier = IFRS18Classifier(FakePredictor(REVIEW_OPTION))

    result = classifier.classify("Juros recebidos")

    assert result.category is None
    assert result.needs_review is True


def test_unknown_choice_requires_review() -> None:
    classifier = IFRS18Classifier(FakePredictor("other"))

    result = classifier.classify("Conta desconhecida")

    assert result.category is None
    assert result.needs_review is True


def test_empty_description_is_rejected() -> None:
    classifier = IFRS18Classifier(FakePredictor("operating"))

    with pytest.raises(ValueError, match="cannot be empty"):
        classifier.classify("  ")


def test_rules_cover_only_ifrs18_categories_and_add_review_option() -> None:
    criteria = CLASSIFICATION_QUESTION[QUESTION_ID]["criteria"]

    assert set(CATEGORY_RULES) == set(IFRS18Category)
    assert set(criteria) == {category.value for category in IFRS18Category} | {REVIEW_OPTION}


def test_minimum_confidence_must_be_a_probability() -> None:
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        IFRS18Classifier(FakePredictor("operating"), minimum_confidence=1.1)


def test_worker_serializes_low_confidence_results_for_manual_review() -> None:
    classifier = IFRS18Classifier(FakePredictor("operating", confidence=0.5))
    request = {
        "requestId": "b716701a-4125-48ea-bd52-6b7d464c73ea",
        "accountId": "b716701a-4125-48ea-bd52-6b7d464c73ea",
        "description": "Receita de venda",
    }

    result = classify_request(request, classifier)

    assert result["category"] == "operating"
    assert result["needsReview"] is True
    assert result["classifierName"] == "laya-classifier"


def test_worker_marks_missing_description_for_manual_review() -> None:
    request = {
        "requestId": "b716701a-4125-48ea-bd52-6b7d464c73ea",
        "accountId": "b716701a-4125-48ea-bd52-6b7d464c73ea",
    }

    result = classify_request(request, IFRS18Classifier(FakePredictor("operating")))

    assert result["category"] is None
    assert result["needsReview"] is True