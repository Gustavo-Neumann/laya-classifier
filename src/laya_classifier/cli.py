import argparse

from .classifier import IFRS18Classifier
from .examples import EXAMPLE_ACCOUNTS


def main() -> None:
    parser = argparse.ArgumentParser(description="Classificador inicial de contas IFRS 18")
    parser.add_argument("account", nargs="?", help="Nome ou descricao da conta")
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Classifica exemplos incluidos no projeto",
    )
    args = parser.parse_args()

    if args.examples == (args.account is not None):
        parser.error("informe uma conta ou use --examples")

    classifier = IFRS18Classifier()
    descriptions = (
        [example.description for example in EXAMPLE_ACCOUNTS]
        if args.examples
        else [args.account]
    )

    for description in descriptions:
        result = classifier.classify(description)
        category = result.category.value if result.category else "sem classificacao"
        if result.needs_review:
            category = f"revisao necessaria (sugestao: {category})"
        confidence = (
            f"{result.confidence:.2f}" if result.confidence is not None else "indisponivel"
        )
        print(f"{description} -> {category} [confianca: {confidence}]")