from dataclasses import dataclass

from .rules import IFRS18Category


@dataclass(frozen=True)
class ExampleAccount:
    description: str
    expected_category: IFRS18Category


EXAMPLE_ACCOUNTS = (
    ExampleAccount(
        "Receita de venda de mercadorias da atividade principal",
        IFRS18Category.OPERATING,
    ),
    ExampleAccount(
        "Resultado de investimento em coligada; investir nao e atividade principal",
        IFRS18Category.INVESTING,
    ),
    ExampleAccount(
        "Despesa de juros de emprestimo bancario obtido para captar recursos",
        IFRS18Category.FINANCING,
    ),
    ExampleAccount(
        "Despesa de imposto de renda sobre o lucro do periodo",
        IFRS18Category.INCOME_TAXES,
    ),
    ExampleAccount(
        "Resultado de operacao descontinuada conforme IFRS 5",
        IFRS18Category.DISCONTINUED_OPERATIONS,
    ),
)