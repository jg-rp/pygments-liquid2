import operator
from dataclasses import dataclass

import pytest
from pygments.token import Token
from pygments.token import _TokenType

from liquid2_lexer import StandardLiquidLexer


@dataclass
class Case:
    name: str
    source: str
    want: list[tuple[str, _TokenType]]


TEST_CASES = [
    Case(
        name="raw tag",
        source="{% raw %}This is {{ plain }} text.{% endraw %}",
        want=[
            ("{%", Token.Punctuation),
            (" ", Token.Text.Whitespace),
            ("raw", Token.Name.Tag),
            (" ", Token.Text.Whitespace),
            ("%}", Token.Punctuation),
            ("This is ", Token.Text),
            ("{", Token.Text),
            ("{", Token.Text),
            (" plain }} text.", Token.Text),
            ("{%", Token.Punctuation),
            (" ", Token.Text.Whitespace),
            ("endraw", Token.Name.Tag),
            (" ", Token.Text.Whitespace),
            ("%}", Token.Punctuation),
            ("\n", Token.Text),
        ],
    ),
    Case(
        name="raw tag, whitespace control",
        source="\n".join(
            [
                "{%- raw %}",
                "This is {{ plain }} text.",
                "{% endraw -%}",
            ]
        ),
        want=[
            ("{%-", Token.Punctuation),
            (" ", Token.Text.Whitespace),
            ("raw", Token.Name.Tag),
            (" ", Token.Text.Whitespace),
            ("%}", Token.Punctuation),
            ("\nThis is ", Token.Text),
            ("{", Token.Text),
            ("{", Token.Text),
            (" plain }} text.\n", Token.Text),
            ("{%", Token.Punctuation),
            (" ", Token.Text.Whitespace),
            ("endraw", Token.Name.Tag),
            (" ", Token.Text.Whitespace),
            ("-%}", Token.Punctuation),
            ("\n", Token.Text),
        ],
    ),
]


LEXER = StandardLiquidLexer()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("name"))
def test_raw_tag(case: Case) -> None:
    assert case.want == [(v, t) for t, v in LEXER.get_tokens(case.source)]
