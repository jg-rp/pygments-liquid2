"""A lexer for Liquid2.

There's also `ExtendedLiquidLexer`, which should be more "correct" than the
Liquid lexer bundled with Pygments.
"""

import re
from typing import Iterable
from typing import Match

from pygments.lexer import ExtendedRegexLexer
from pygments.lexer import LexerContext
from pygments.lexer import bygroups
from pygments.lexer import default
from pygments.lexer import include
from pygments.token import Comment
from pygments.token import Keyword
from pygments.token import Name
from pygments.token import Number
from pygments.token import Operator
from pygments.token import Punctuation
from pygments.token import String
from pygments.token import Text
from pygments.token import Whitespace
from pygments.token import _TokenType


class ExtendedLiquidLexer(ExtendedRegexLexer):
    """Lexer for Liquid templates.

    This lexer handles some things that the bundled Liquid lexer does not:

    - Nested block comments (those with balanced `comment`/`endcomment` tags).
    - Whitespace control.
    - Inline comment tags (`{% # some comment %}`).
    - `{% liquid %}` tags.
    - Bracketed variable and index syntax (`foo[bar]["with a space"][1]`).

    We've also removed the `not` operator as Shopify/Liquid does not have a logical
    `not` operator.
    """

    name = "liquid-ext"
    url = "https://www.rubydoc.info/github/Shopify/liquid"
    aliases = ["liquid-ext"]
    filenames = ["*.liquid"]
    version_added = "2.0"

    liquid_reserved_words = {"true", "false", "nil", "null", "with", "required", "as"}
    liquid_operator_words = {"and", "or", "contains", "in"}
    re_param_delimiter = re.compile(r"\s*[:=]", re.MULTILINE)

    def endcomment_callback(  # noqa: D102
        self,
        match: Match[str],
        ctx: LexerContext,
    ) -> Iterable[tuple[int, _TokenType, str]]:
        if len(ctx.stack) > 1 and ctx.stack[-2] == "block-comment":
            # This is the end of a nested block comment, so it's still a comment.
            yield (match.start(), Comment, match.group(0))
        else:
            index = match.start()
            for group, token_type in zip(
                match.groups(),
                (Punctuation, Whitespace, Name.Tag, Whitespace, Punctuation),
            ):
                yield (index, token_type, group)
                index += len(group)

        ctx.stack.pop()
        ctx.pos = match.end()

    # TODO: don't really need word_callback anymore, it can be done without
    def word_callback(  # noqa: D102
        self,
        match: Match[str],
        ctx: LexerContext,
    ) -> Iterable[tuple[int, _TokenType, str]]:
        end = match.end()
        word = match.group(0)

        try:
            next_ch = ctx.text[end]
        except IndexError:
            next_ch = ""

        if next_ch in (".", "["):
            # This word is the start of a path (to a variable).
            yield (match.start(), Name.Variable, word)
            ctx.stack.append("path")
        elif self.re_param_delimiter.match(ctx.text, end):
            # Looks like a named parameter/argument
            yield (match.start(), Name.Attribute, word)
        elif word in self.liquid_reserved_words:
            yield (match.start(), Keyword.Constant, word)
        elif word in self.liquid_operator_words:
            yield (match.start(), Operator.Word, word)
        else:
            yield (match.start(), Name.Variable, word)

        ctx.pos = end

    tokens = {
        "root": [
            (r"[^{]+", Text),
            (
                r"(\{%-?)(\s*)(\#)",
                bygroups(Punctuation, Whitespace, Comment),
                "inline-comment",
            ),
            (
                r"(\{%-?)(\s*)(liquid)",
                bygroups(Punctuation, Whitespace, Name.Tag),
                "line-statements",
            ),
            (
                r"(\{%-?)(\s*)(comment)(\s*)(-?%})",
                bygroups(Punctuation, Whitespace, Name.Tag, Whitespace, Punctuation),
                "block-comment",
            ),
            (
                r"(\{%-?)(\s*)(raw)(\s*)(-?%})",
                bygroups(Punctuation, Whitespace, Name.Tag, Whitespace, Punctuation),
                "raw-tag",
            ),
            (
                r"(\{%-?)(\s*)(if|unless|else|elsif|case|when|endif|endunless|endcase)\b(\s*)",
                bygroups(Punctuation, Whitespace, Keyword.Reserved, Whitespace),
                "tag-expression",
            ),
            (
                r"(\{%-?)(\s*)([a-z][a-z_0-9]*)(\s*)",
                bygroups(Punctuation, Whitespace, Name.Tag, Whitespace),
                "tag-expression",
            ),
            (
                r"(\{\{-?)(\s*)",
                bygroups(Punctuation, Whitespace),
                "output-expression",
            ),
            (r"\{", Text),
        ],
        "inline-comment": [
            (r"[^\-%]+", Comment),
            (r"-?%}", Punctuation, "#pop"),
            (r"[\-%]", Comment),
        ],
        "block-comment": [
            (r"[^{]+", Comment),
            (r"{%-?\s*comment\s*-?%}", Comment, "#push"),
            (r"(\{%-?)(\s*)(endcomment)(\s*)(-?%\})", endcomment_callback),
            (r"\{", Comment),
        ],
        "raw-tag": [
            (r"[^{]+", Text),
            (
                r"(\{%-?)(\s*)(endraw)(\s*)(-?%\})",
                bygroups(Punctuation, Whitespace, Name.Tag, Whitespace, Punctuation),
                "#pop",
            ),
            (r"\{", Text),
        ],
        "tag-expression": [
            include("expression"),
            (r"-?%}", Punctuation, "#pop"),
        ],
        "output-expression": [
            include("expression"),
            (r"-?}}", Punctuation, "#pop"),
        ],
        "expression": [
            (r'"', String.Double, "double-string"),
            (r"'", String.Single, "single-string"),
            (r"\d+\.\d+", Number.Float),
            (r"\d+", Number.Integer),
            (
                r"(\|)(\s*)([\u0080-\uFFFFa-zA-Z_][\u0080-\uFFFFa-zA-Z0-9_-]*)",
                bygroups(Punctuation, Whitespace, Name.Function),
            ),
            (r"\[", Punctuation, "path"),
            (r"[\u0080-\uFFFFa-zA-Z_][\u0080-\uFFFFa-zA-Z0-9_-]*", word_callback),
            (r">=|<=|==|!=|<>|>|<|=", Operator),
            (r"[,:]|\.\.|\(|\)", Punctuation),
            (r"[ \t]+", Whitespace),
        ],
        "single-string": [
            (r"\\.", String.Escape),
            (r"'", String.Single, "#pop"),
            (r"[^\\']+", String.Single),
        ],
        "double-string": [
            (r"\\.", String.Escape),
            (r'"', String.Double, "#pop"),
            (r'[^\\"]+', String.Double),
        ],
        "path": [
            (r"\.", Punctuation),
            (r"\[", Punctuation, "#push"),
            (r"]", Punctuation, "#pop"),
            (r"[\u0080-\uFFFFa-zA-Z_][\u0080-\uFFFFa-zA-Z0-9_-]*", Name.Variable),
            (r"\d+", Number.Integer),
            (r'"', String.Double, "double-string"),
            (r"'", String.Single, "single-string"),
            default("#pop"),
        ],
        "line-statements": [
            (r"-?%}", Punctuation, "#pop"),
            (
                r"(\s*)(if|unless|else|elsif|case|when|endif|endunless|endcase)\b",
                bygroups(Whitespace, Keyword.Reserved),
                "line-expression",
            ),
            (
                r"(\s*)([a-z][a-z_0-9]+)",
                bygroups(Whitespace, Name.Tag),
                "line-expression",
            ),
            (r"[ \t]+", Whitespace),
        ],
        "line-expression": [
            (r"[ \t\r]*\n", Whitespace, "#pop"),
            include("expression"),
            (r"-?%}", Punctuation, ("#pop", "#pop")),
        ],
    }


class Liquid2Lexer(ExtendedLiquidLexer):
    """Lexer for Liquid templates including syntax introduced with Liquid2."""

    name = "liquid2"
    url = "https://github.com/jg-rp/python-liquid2"
    aliases = ["liquid2"]
    filenames = ["*.liquid"]
    # version_added = "2.0"

    # TODO


# TODO: DelegatingLexer
