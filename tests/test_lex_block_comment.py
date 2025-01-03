import operator
from dataclasses import dataclass

import pytest
from pygments.token import Comment
from pygments.token import Name
from pygments.token import Punctuation
from pygments.token import Text
from pygments.token import Token
from pygments.token import Whitespace
from pygments.token import _TokenType

from liquid2_lexer import StandardLiquidLexer


@dataclass
class Case:
    name: str
    source: str
    want: list[tuple[str, _TokenType]]


TEST_CASES = [
    Case(
        name="block comment",
        source="{% comment %}This is a comment{% endcomment %}",
        want=[
            ("{%", Punctuation),
            (" ", Whitespace),
            ("comment", Name.Tag),
            (" ", Whitespace),
            ("%}", Punctuation),
            ("This is a comment", Comment),
            ("{%", Punctuation),
            (" ", Whitespace),
            ("endcomment", Name.Tag),
            (" ", Whitespace),
            ("%}", Punctuation),
            ("\n", Text),
        ],
    ),
    Case(
        name="block comment, multiple lines",
        source="\n".join(
            [
                "{% comment %}",
                "This is a comment",
                "{% endcomment %}",
            ]
        ),
        want=[
            ("{%", Punctuation),
            (" ", Whitespace),
            ("comment", Name.Tag),
            (" ", Whitespace),
            ("%}", Punctuation),
            ("\nThis is a comment\n", Comment),
            ("{%", Punctuation),
            (" ", Whitespace),
            ("endcomment", Name.Tag),
            (" ", Whitespace),
            ("%}", Punctuation),
            ("\n", Text),
        ],
    ),
    Case(
        name="block comment, nested block comment",
        source="\n".join(
            [
                "{% comment %}",
                "This is a ",
                "{% comment %}",
                "nested",
                "{% endcomment %}",
                " comment",
                "{% endcomment %}",
            ]
        ),
        want=[
            ("{%", Token.Punctuation),
            (" ", Token.Text.Whitespace),
            ("comment", Token.Name.Tag),
            (" ", Token.Text.Whitespace),
            ("%}", Token.Punctuation),
            ("\nThis is a \n", Token.Comment),
            ("{% comment %}", Token.Comment),
            ("\nnested\n", Token.Comment),
            ("{% endcomment %}", Token.Comment),
            ("\n comment\n", Token.Comment),
            ("{%", Token.Punctuation),
            (" ", Token.Text.Whitespace),
            ("endcomment", Token.Name.Tag),
            (" ", Token.Text.Whitespace),
            ("%}", Token.Punctuation),
            ("\n", Token.Text),
        ],
    ),
    Case(
        name="block comment, other tag",
        source="\n".join(
            [
                "{% comment %}",
                "This is a comment ",
                "with an {% assign %} tag",
                "{% endcomment %}",
            ]
        ),
        want=[
            ("{%", Token.Punctuation),
            (" ", Token.Text.Whitespace),
            ("comment", Token.Name.Tag),
            (" ", Token.Text.Whitespace),
            ("%}", Token.Punctuation),
            ("\nThis is a comment \nwith an ", Token.Comment),
            ("{", Token.Comment),
            ("% assign %} tag\n", Token.Comment),
            ("{%", Token.Punctuation),
            (" ", Token.Text.Whitespace),
            ("endcomment", Token.Name.Tag),
            (" ", Token.Text.Whitespace),
            ("%}", Token.Punctuation),
            ("\n", Token.Text),
        ],
    ),
    Case(
        name="block comment, whitespace control",
        source="{%- comment %}This is a comment{% endcomment -%}",
        want=[
            ("{%-", Punctuation),
            (" ", Whitespace),
            ("comment", Name.Tag),
            (" ", Whitespace),
            ("%}", Punctuation),
            ("This is a comment", Comment),
            ("{%", Punctuation),
            (" ", Whitespace),
            ("endcomment", Name.Tag),
            (" ", Whitespace),
            ("-%}", Punctuation),
            ("\n", Text),
        ],
    ),
]


LEXER = StandardLiquidLexer()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("name"))
def test_block_comment(case: Case) -> None:
    assert case.want == [(v, t) for t, v in LEXER.get_tokens(case.source)]
