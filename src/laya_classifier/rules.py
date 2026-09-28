from enum import StrEnum


class IFRS18Category(StrEnum):
    OPERATING = "operating"
    INVESTING = "investing"
    FINANCING = "financing"
    INCOME_TAXES = "income_taxes"
    DISCONTINUED_OPERATIONS = "discontinued_operations"


CATEGORY_RULES = {
    IFRS18Category.OPERATING: (
        "Receitas e despesas que nao sejam classificadas nas categorias de "
        "investimento, financiamento, imposto de renda ou operacoes descontinuadas. "
        "E a categoria residual."
    ),
    IFRS18Category.INVESTING: (
        "Receitas e despesas de ativos que geram retornos individualmente e em "
        "grande medida independentemente dos demais recursos da entidade. A "
        "classificacao pode depender de investimento ser uma atividade principal."
    ),
    IFRS18Category.FINANCING: (
        "Receitas e despesas de passivos provenientes de transacoes que envolvem "
        "a obtencao de financiamento. A classificacao pode depender de fornecer "
        "financiamento a clientes ser uma atividade principal."
    ),
    IFRS18Category.INCOME_TAXES: (
        "Despesa ou receita de imposto de renda classificada na categoria de "
        "impostos sobre o lucro."
    ),
    IFRS18Category.DISCONTINUED_OPERATIONS: (
        "Receitas e despesas de operacoes descontinuadas conforme definidas pelo IFRS 5."
    ),
}

REVIEW_OPTION = "needs_review"
QUESTION_ID = "ifrs18_category"

CLASSIFICATION_QUESTION = {
    QUESTION_ID: {
        "type": "choice",
        "instructions": (
            "Classifique este item de receita ou despesa na demonstracao do "
            "resultado conforme IFRS 18. Use needs_review se a descricao nao "
            "trouxer o contexto da entidade ou da transacao necessario para aplicar "
            "os criterios, se nao for um item da demonstracao do resultado ou se "
            "mais de uma categoria for plausivel. Nao adivinhe."
        ),
        "criteria": {
            **{category.value: rule for category, rule in CATEGORY_RULES.items()},
            REVIEW_OPTION: (
                "Contexto insuficiente, classificacao ambigua ou item que nao e "
                "receita ou despesa na demonstracao do resultado."
            ),
        },
    }
}