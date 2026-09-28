# Laya Classifier

Primeira versao de um classificador experimental de itens de receita e despesa
nas categorias da demonstracao do resultado do IFRS 18. Nao cria API web nem
conexao com RabbitMQ.

## Categorias e limites

As categorias e descricoes iniciais ficam em `src/laya_classifier/rules.py`:
operacional, investimento, financiamento, imposto de renda e operacoes
descontinuadas. As descricoes sao orientacoes resumidas, nao regras completas do
IFRS 18. A classificacao pode depender das atividades principais da entidade,
da natureza da transacao e de outros fatos; quando o contexto estiver ausente,
o modelo pode sugerir `needs_review`. A confianca abaixo de 0.70 tambem exige
revisao. Esse limite e provisorio e deve ser validado com dados rotulados.

As contas de exemplo sao casos ilustrativos para exercitar a integracao, nao
interpretacoes contabeis definitivas. O resultado do modelo deve ser validado
por profissional contábil antes de uso financeiro.

## Executar

Requer Python 3.12 e `uv`. O projeto usa `uv` para instalar e executar:

```sh
uv sync
uv run pytest
uv run laya-classifier "Despesa de juros de emprestimo bancario"
uv run laya-classifier --examples
```

O primeiro uso do classificador carrega o `Router` do Laya e pode baixar os
pesos do modelo. Os testes usam um preditor simulado e nao baixam pesos.

## Uso em Python

```python
from laya_classifier import IFRS18Classifier

result = IFRS18Classifier().classify(
	"Despesa de juros de emprestimo bancario obtido para captar recursos"
)
print(result.category, result.confidence, result.needs_review)
```

O classificador recebe um preditor compativel com `Router.predict`, permitindo
testes sem modelo e futura troca da camada de entrada/saida sem alterar as
regras ou a classificacao.

## Referencias

- [Documentacao e API do Laya](https://nandhakishorm.github.io/laya/)
- [IFRS 18 na IFRS Foundation](https://www.ifrs.org/issued-standards/list-of-standards/ifrs-18-presentation-and-disclosure-in-financial-statements/)
