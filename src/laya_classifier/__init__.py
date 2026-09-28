from .classifier import AccountClassification, IFRS18Classifier
from .rules import IFRS18Category


def main() -> None:
    from .cli import main as cli_main

    cli_main()


__all__ = ["AccountClassification", "IFRS18Category", "IFRS18Classifier", "main"]
