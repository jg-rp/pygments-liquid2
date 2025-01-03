"""A lexer for Liquid2.

There's also `ExtendedLiquidLexer`, which should be more "correct" than the
Liquid lexer bundled with Pygments.
"""

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
    - Tag and output expressions that span multiple lines.

    We've also removed the `not` operator as Shopify/Liquid does not have a logical
    `not` operator.
    """

    name = "liquid-ext"
    url = "https://www.rubydoc.info/github/Shopify/liquid"
    aliases = ["liquid-ext"]
    filenames = ["*.liquid"]
    version_added = "2.0"

    # The token type to use for markup delimiters (`{{`, `}}`, `{%` and `%}`).
    # Change this to Comment.Preproc for DelegatingLexer
    delimiter_token = Punctuation

    # The token type to use for control flow tag names.
    control_flow_token = Keyword.Reserved

    # The token type to use for all other tag names.
    # Change this to Keyword to match the Django lexer
    tag_name_token = Name.Tag

    # Non-markup token type. Change this to Other for DelegatingLexer.
    text_token = Text

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
                (Punctuation, Whitespace, self.tag_name_token, Whitespace, Punctuation),
            ):
                yield (index, token_type, group)
                index += len(group)

        ctx.stack.pop()
        ctx.pos = match.end()

    tokens = {
        "root": [
            (r"[^{]+", text_token),
            (
                r"(\{%-?)(\s*)(\#)",
                bygroups(delimiter_token, Whitespace, Comment),
                "inline-comment",
            ),
            (
                r"(\{%-?)(\s*)(liquid)",
                bygroups(delimiter_token, Whitespace, tag_name_token),
                "line-statements",
            ),
            (
                r"(\{%-?)(\s*)(comment)(\s*)(-?%})",
                bygroups(
                    delimiter_token,
                    Whitespace,
                    tag_name_token,
                    Whitespace,
                    delimiter_token,
                ),
                "block-comment",
            ),
            (
                r"(\{%-?)(\s*)(raw)(\s*)(-?%})",
                bygroups(
                    delimiter_token,
                    Whitespace,
                    tag_name_token,
                    Whitespace,
                    delimiter_token,
                ),
                "raw-tag",
            ),
            (
                r"(\{%-?)(\s*)(if|unless|else|elsif|case|when|endif|endunless|endcase|for|endfor)\b(\s*)",
                bygroups(delimiter_token, Whitespace, control_flow_token, Whitespace),
                "tag-expression",
            ),
            (
                r"(\{%-?)(\s*)([a-z][a-z_0-9]*)(\s*)",
                bygroups(delimiter_token, Whitespace, tag_name_token, Whitespace),
                "tag-expression",
            ),
            (
                r"(\{\{-?)(\s*)",
                bygroups(delimiter_token, Whitespace),
                "output-expression",
            ),
            (r"\{", text_token),
        ],
        "inline-comment": [
            (r"[^\-%]+", Comment),
            (r"-?%}", delimiter_token, "#pop"),
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
                bygroups(
                    delimiter_token,
                    Whitespace,
                    tag_name_token,
                    Whitespace,
                    delimiter_token,
                ),
                "#pop",
            ),
            (r"\{", Text),
        ],
        "tag-expression": [
            include("multiline-expression"),
            (r"-?%}", delimiter_token, "#pop"),
        ],
        "output-expression": [
            include("multiline-expression"),
            (r"-?}}", delimiter_token, "#pop"),
        ],
        "expression": [
            (r'"', String.Double, "double-string"),
            (r"'", String.Single, "single-string"),
            (r"\d+\.\d+", Number.Float),
            (r"\d+", Number.Integer),
            (
                r"(\|)(\s*)([\u0080-\uFFFFa-zA-Z_][\u0080-\uFFFFa-zA-Z0-9_-]*)",
                bygroups(Operator, Whitespace, Name.Function),
            ),
            (r"\[", Punctuation, "path"),
            (
                r"([\u0080-\uFFFFa-zA-Z_][\u0080-\uFFFFa-zA-Z0-9_-]*)([\[\.])",
                bygroups(Name.Variable, Punctuation),
                "path",
            ),
            (
                r"([\u0080-\uFFFFa-zA-Z_][\u0080-\uFFFFa-zA-Z0-9_-]*)(\s*)(?=[:=])",
                bygroups(Name.Attribute, Whitespace),
            ),
            (
                r"(true|false|nil|null|with|reversed|as)\b",
                Keyword.Constant,
            ),
            (
                r"(and|or|contains|in)\b",
                Operator.Word,
            ),
            (
                r"[\u0080-\uFFFFa-zA-Z_][\u0080-\uFFFFa-zA-Z0-9_-]*",
                Name.Variable,
            ),
            (r">=|<=|==|!=|<>|>|<|=", Operator),
            (r"[,:]|\.\.|\(|\)", Punctuation),
        ],
        "multiline-expression": [
            include("expression"),
            (r"[ \t\n\r]+", Whitespace),
        ],
        "inline-expression": [
            include("expression"),
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
            (r"-?%}", delimiter_token, "#pop"),
            (
                r"(\s*)(if|unless|else|elsif|case|when|endif|endunless|endcase|for|endfor)\b",
                bygroups(Whitespace, control_flow_token),
                "line-expression",
            ),
            (
                r"(\s*)([a-z][a-z_0-9]+)",
                bygroups(Whitespace, tag_name_token),
                "line-expression",
            ),
            (r"[ \t]+", Whitespace),
        ],
        "line-expression": [
            (r"[ \t\r]*\n", Whitespace, "#pop"),
            include("inline-expression"),
            (r"-?%}", delimiter_token, ("#pop", "#pop")),
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
# - with Comment.Preproc instead of Punctuation
