import operator
from dataclasses import dataclass

import pytest
from pygments.token import Comment
from pygments.token import Punctuation
from pygments.token import Text
from pygments.token import Token
from pygments.token import _TokenType

from liquid2_lexer import Liquid2Lexer


@dataclass
class Case:
    name: str
    source: str
    want: list[tuple[str, _TokenType]]


TEST_CASES = [
    Case(
        name="comment",
        source="{# This is a comment #}",
        want=[
            ("{#", Punctuation),
            (" This is a comment ", Comment),
            ("#}", Punctuation),
            ("\n", Text),
        ],
    ),
    Case(
        name="comment, multiple lines",
        source="\n".join(
            [
                "{#",
                "This is a comment",
                "#}",
            ]
        ),
        want=[
            ("{#", Punctuation),
            ("\nThis is a comment\n", Comment),
            ("#}", Punctuation),
            ("\n", Text),
        ],
    ),
    Case(
        name="comment, more hashes",
        source="\n".join(
            [
                "{##",
                "This is a comment",
                "##}",
            ]
        ),
        want=[
            ("{##", Punctuation),
            ("\nThis is a comment\n", Comment),
            ("##}", Punctuation),
            ("\n", Text),
        ],
    ),
    Case(
        name="comment, nested",
        source="\n".join(
            [
                "{##",
                "  This is a ",
                "  {#",
                "    nested ",
                "  #}",
                "  comment",
                "##}",
            ]
        ),
        want=[
            ("{##", Token.Punctuation),
            ("\n  This is a \n  {", Token.Comment),
            ("#", Token.Comment),
            ("\n    nested \n  ", Token.Comment),
            ("#}", Token.Comment),
            ("\n  comment\n", Token.Comment),
            ("##}", Token.Punctuation),
            ("\n", Token.Text),
        ],
    ),
]


LEXER = Liquid2Lexer()


@pytest.mark.parametrize("case", TEST_CASES, ids=operator.attrgetter("name"))
def test_liquid2_comment(case: Case) -> None:
    assert case.want == [(v, t) for t, v in LEXER.get_tokens(case.source)]
