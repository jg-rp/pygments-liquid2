"""Lexers for Liquid2 and Liquid2 with HTML.

There's also `StandardLiquidLexer`, which should be more "correct" than the
Liquid lexer bundled with Pygments.
"""

from __future__ import annotations

import re
from typing import Any
from typing import Iterable
from typing import Iterator
from typing import Match

from pygments.lexer import DelegatingLexer
from pygments.lexer import ExtendedRegexLexer
from pygments.lexer import LexerContext
from pygments.lexer import bygroups
from pygments.lexer import default
from pygments.lexer import include
from pygments.lexers.html import HtmlLexer
from pygments.token import Comment
from pygments.token import Keyword
from pygments.token import Name
from pygments.token import Number
from pygments.token import Operator
from pygments.token import Other
from pygments.token import Punctuation
from pygments.token import String
from pygments.token import Text
from pygments.token import Token
from pygments.token import Whitespace
from pygments.token import _TokenType
from pygments.util import html_doctype_matches


class StandardLiquidLexer(ExtendedRegexLexer):
    """Lexer for Liquid templates.

    This lexer handles some things that the Pygments bundled Liquid lexer does not:

    - Nested block comments (those with balanced `comment`/`endcomment` tags).
    - Whitespace control.
    - Inline comment tags (`{% # some comment %}`).
    - `{% liquid %}` tags.
    - Bracketed variable and index syntax (`foo[bar]["with a space"][1]`).
    - Tag and output expressions that span multiple lines.

    We've also removed the `not` operator as Shopify/Liquid does not have a logical
    `not` operator.
    """

    name = "liquid-std"
    url = "https://www.rubydoc.info/github/Shopify/liquid"
    aliases = ["liquid"]
    filenames = ["*.liquid"]

    # If this is installed, it should take priority over the Pygments Liquid lexer.
    priority = 0.5

    # The token type to use for markup delimiters (`{{`, `}}`, `{%` and `%}`).
    # Change this to Comment.Preproc for DelegatingLexer
    delimiter_token_type = Punctuation

    # The token type to use for control flow tag names.
    control_flow_token_type = Keyword.Reserved

    # The token type to use for all other tag names.
    # Change this to Keyword to match the Django lexer
    tag_name_token_type = Name.Tag

    # Non-markup token type. Change this to Other for DelegatingLexer.
    text_token_type = Text

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
                (
                    Punctuation,
                    Whitespace,
                    Token.Liquid.Tag.Name,
                    Whitespace,
                    Punctuation,
                ),
            ):
                yield (index, token_type, group)
                index += len(group)

        ctx.stack.pop()
        ctx.pos = match.end()

    tokens = {
        "root": [
            (r"[^{]+", Token.Liquid.Text),
            (
                r"(\{%-?)(\s*)(\#)",
                bygroups(Token.Liquid.Delimiter, Whitespace, Comment),
                "inline-comment",
            ),
            (
                r"(\{%-?)(\s*)(liquid)",
                bygroups(Token.Liquid.Delimiter, Whitespace, Token.Liquid.Tag.Name),
                "line-statements",
            ),
            (
                r"(\{%-?)(\s*)(comment)(\s*)(-?%})",
                bygroups(
                    Token.Liquid.Delimiter,
                    Whitespace,
                    Token.Liquid.Tag.Name,
                    Whitespace,
                    Token.Liquid.Delimiter,
                ),
                "block-comment",
            ),
            (
                r"(\{%-?)(\s*)(raw)(\s*)(-?%})",
                bygroups(
                    Token.Liquid.Delimiter,
                    Whitespace,
                    Token.Liquid.Tag.Name,
                    Whitespace,
                    Token.Liquid.Delimiter,
                ),
                "raw-tag",
            ),
            (
                r"(\{%-?)(\s*)(if|unless|else|elsif|case|when|endif|endunless|endcase|for|endfor)\b(\s*)",
                bygroups(
                    Token.Liquid.Delimiter,
                    Whitespace,
                    Token.Liquid.ControlFlow,
                    Whitespace,
                ),
                "tag-expression",
            ),
            (
                r"(\{%-?)(\s*)([a-z][a-z_0-9]*)(\s*)",
                bygroups(
                    Token.Liquid.Delimiter,
                    Whitespace,
                    Token.Liquid.Tag.Name,
                    Whitespace,
                ),
                "tag-expression",
            ),
            (
                r"(\{\{-?)(\s*)",
                bygroups(Token.Liquid.Delimiter, Whitespace),
                "output-expression",
            ),
            (r"\{", Token.Liquid.Text),
        ],
        "inline-comment": [
            (r"[^\-%]+", Comment),
            (r"-?%}", Token.Liquid.Delimiter, "#pop"),
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
                    Token.Liquid.Delimiter,
                    Whitespace,
                    Token.Liquid.Tag.Name,
                    Whitespace,
                    Token.Liquid.Delimiter,
                ),
                "#pop",
            ),
            (r"\{", Text),
        ],
        "tag-expression": [
            include("multiline-expression"),
            (r"-?%}", Token.Liquid.Delimiter, "#pop"),
        ],
        "output-expression": [
            include("multiline-expression"),
            (r"-?}}", Token.Liquid.Delimiter, "#pop"),
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
                r"(true|false|nil|null|with|reversed|as|for)\b",
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
            (r"-?%}", Token.Liquid.Delimiter, "#pop"),
            (
                r"(\s*)(if|unless|else|elsif|case|when|endif|endunless|endcase|for|endfor)\b",
                bygroups(Whitespace, Token.Liquid.ControlFlow),
                "line-expression",
            ),
            (
                r"(\s*)([a-z][a-z_0-9]+)",
                bygroups(Whitespace, Token.Liquid.Tag.Name),
                "line-expression",
            ),
            (r"[ \t]+", Whitespace),
        ],
        "line-expression": [
            (r"[ \t\r]*\n", Whitespace, "#pop"),
            include("inline-expression"),
            (r"-?%}", Token.Liquid.Delimiter, ("#pop", "#pop")),
        ],
    }

    def get_tokens_unprocessed(  # type: ignore[override]  # noqa: D102
        self,
        text: str | None = None,
        context: LexerContext | None = None,
    ) -> Iterator[tuple[int, _TokenType, str]]:
        """Replace Token.Liquid.* with token types set as class attributes."""
        for index, token, value in super().get_tokens_unprocessed(text, context):
            if token is Token.Liquid.Text:
                yield index, self.text_token_type, value
            elif token is Token.Liquid.Delimiter:
                yield index, self.delimiter_token_type, value
            elif token is Token.Liquid.Tag.Name:
                yield index, self.tag_name_token_type, value
            elif token is Token.Liquid.ControlFlow:
                yield index, self.control_flow_token_type, value
            else:
                yield index, token, value

    @staticmethod
    def analyse_text(text: str) -> float:  # noqa: D102
        rv = 0.0
        if re.search(r"\{%-?\s*(liquid|include|render)", text) is not None:
            rv += 0.5
        if re.search(r"\{%-?\s*if\s*.*?%\}", text) is not None:
            rv += 0.1
        if re.search(r"\{\{.*?\}\}", text) is not None:
            rv += 0.1
        return rv


class _DelegatedLiquidLexer(StandardLiquidLexer):
    """A `StandardLiquidLexer` configured for use in a `DelegatingLexer`."""

    delimiter_token_type = Comment.Preproc
    control_flow_token_type = Keyword
    tag_name_token_type = Keyword
    text_token_type = Other


class HtmlLiquidLexer(DelegatingLexer):
    """Liquid with HTML lexer.

    Nested Javascript and CSS is highlighted too.
    """

    name = "HTML+Liquid"
    aliases = ["html+liquid", "htmlliquid"]
    filenames = [
        "*.html.liquid",
        "*.htm.liquid",
        "*.xhtml.liquid",
    ]
    version_added = ""
    alias_filenames = ["*.html", "*.htm", "*.xhtml"]
    url = "https://www.rubydoc.info/github/Shopify/liquid"

    def __init__(self, **options: Any):
        super().__init__(HtmlLexer, _DelegatedLiquidLexer, **options)

    @staticmethod
    def analyse_text(text: str) -> float:  # noqa: D102
        rv = _DelegatedLiquidLexer.analyse_text(text) - 0.01
        if html_doctype_matches(text):
            rv += 0.5
        return rv


# NOTE: I've resorted to copying and modifying StandardLiquidLexer.tokens here. Things
# like additional whitespace control characters are pervasive, making inheritance worse
# than code duplication in this case, I think.


class Liquid2Lexer(ExtendedRegexLexer):
    """Lexer for Liquid templates including syntax introduced with Liquid2."""

    name = "liquid2"
    url = "https://github.com/jg-rp/python-liquid2"
    aliases = ["liquid2", "liquid"]
    filenames = ["*.liquid"]

    # If this is installed, it should take priority over the standard Liquid lexer.
    priority = 0.6

    # The token type to use for markup delimiters (`{{`, `}}`, `{%` and `%}`).
    # Change this to Comment.Preproc for DelegatingLexer
    delimiter_token_type = Punctuation

    # The token type to use for control flow tag names.
    control_flow_token_type = Keyword.Reserved

    # The token type to use for all other tag names.
    # Change this to Keyword to match the Django lexer
    tag_name_token_type = Name.Tag

    # Non-markup token type. Change this to Other for DelegatingLexer.
    text_token_type = Text

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
                (
                    Punctuation,
                    Whitespace,
                    Token.Liquid.Tag.Name,
                    Whitespace,
                    Punctuation,
                ),
            ):
                yield (index, token_type, group)
                index += len(group)

        ctx.stack.pop()
        ctx.pos = match.end()

    # TODO: `{# .. #}` comments
    # TODO: `"hello ${you}!"` template strings
    # TODO: scientific notation

    tokens = {
        "root": [
            (r"[^{]+", Token.Liquid.Text),
            (
                r"(\{%[\-\~\+]?)(\s*)(\#)",
                bygroups(Token.Liquid.Delimiter, Whitespace, Comment),
                "inline-comment",
            ),
            (
                r"(\{[\-\~\+]?)(\s*)(liquid)",
                bygroups(Token.Liquid.Delimiter, Whitespace, Token.Liquid.Tag.Name),
                "line-statements",
            ),
            (
                r"(\{%[\-\~\+]?)(\s*)(comment)(\s*)([\-\~\+]?%})",
                bygroups(
                    Token.Liquid.Delimiter,
                    Whitespace,
                    Token.Liquid.Tag.Name,
                    Whitespace,
                    Token.Liquid.Delimiter,
                ),
                "block-comment",
            ),
            (
                r"(\{%[\-\~\+]?)(\s*)(raw)(\s*)([\-\~\+]?%})",
                bygroups(
                    Token.Liquid.Delimiter,
                    Whitespace,
                    Token.Liquid.Tag.Name,
                    Whitespace,
                    Token.Liquid.Delimiter,
                ),
                "raw-tag",
            ),
            (
                r"(\{%[\-\~\+]?)(\s*)(if|unless|else|elsif|case|when|endif|endunless|endcase|for|endfor)\b(\s*)",
                bygroups(
                    Token.Liquid.Delimiter,
                    Whitespace,
                    Token.Liquid.ControlFlow,
                    Whitespace,
                ),
                "tag-expression",
            ),
            (
                r"(\{%[\-\~\+]?)(\s*)([a-z][a-z_0-9]*)(\s*)",
                bygroups(
                    Token.Liquid.Delimiter,
                    Whitespace,
                    Token.Liquid.Tag.Name,
                    Whitespace,
                ),
                "tag-expression",
            ),
            (
                r"(\{\{[\-\~\+]?)(\s*)",
                bygroups(Token.Liquid.Delimiter, Whitespace),
                "output-expression",
            ),
            (r"\{", Token.Liquid.Text),
        ],
        "inline-comment": [
            (r"[^\-%]+", Comment),
            (r"[\-\~\+]?%}", Token.Liquid.Delimiter, "#pop"),
            (r"[\-%]", Comment),
        ],
        "block-comment": [
            (r"[^{]+", Comment),
            (r"{%[\-\~\+]?\s*comment\s*[\-\~\+]?%}", Comment, "#push"),
            (
                r"(\{%[\-\~\+]?)(\s*)(endcomment)(\s*)([\-\~\+]?%\})",
                endcomment_callback,
            ),
            (r"\{", Comment),
        ],
        "raw-tag": [
            (r"[^{]+", Text),
            (
                r"(\{%[\-\~\+]?)(\s*)(endraw)(\s*)([\-\~\+]?%\})",
                bygroups(
                    Token.Liquid.Delimiter,
                    Whitespace,
                    Token.Liquid.Tag.Name,
                    Whitespace,
                    Token.Liquid.Delimiter,
                ),
                "#pop",
            ),
            (r"\{", Text),
        ],
        "tag-expression": [
            include("multiline-expression"),
            (r"[\-\~\+]?%}", Token.Liquid.Delimiter, "#pop"),
        ],
        "output-expression": [
            include("multiline-expression"),
            (r"[\-\~\+]?}}", Token.Liquid.Delimiter, "#pop"),
        ],
        "expression": [
            (r'"', String.Double, "double-string"),
            (r"'", String.Single, "single-string"),
            (r"\d+\.\d+", Number.Float),
            (r"\d+", Number.Integer),
            (
                r"(\|\|?)(\s*)([\u0080-\uFFFFa-zA-Z_][\u0080-\uFFFFa-zA-Z0-9_-]*)",
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
                r"(true|false|nil|null|with|reversed|as|if|else|not|for)\b",
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
            (r"[\-\~\+]?%}", Token.Liquid.Delimiter, "#pop"),
            (
                r"(\s*)(if|unless|else|elsif|case|when|endif|endunless|endcase|for|endfor)\b",
                bygroups(Whitespace, Token.Liquid.ControlFlow),
                "line-expression",
            ),
            (
                r"(\s*)([a-z][a-z_0-9]+)",
                bygroups(Whitespace, Token.Liquid.Tag.Name),
                "line-expression",
            ),
            (r"[ \t]+", Whitespace),
        ],
        "line-expression": [
            (r"[ \t\r]*\n", Whitespace, "#pop"),
            include("inline-expression"),
            (r"[\-\~\+]?%}", Token.Liquid.Delimiter, ("#pop", "#pop")),
        ],
    }


class _DelegatedLiquid2Lexer(Liquid2Lexer):
    """A `Liquid2Lexer` configured for use in a `DelegatingLexer`."""

    delimiter_token_type = Comment.Preproc
    control_flow_token_type = Keyword
    tag_name_token_type = Keyword
    text_token_type = Other


class HtmlLiquid2Lexer(DelegatingLexer):
    """Liquid2 with HTML lexer.

    Nested Javascript and CSS is highlighted too.
    """

    name = "HTML+Liquid"
    aliases = ["html+liquid", "htmlliquid"]
    filenames = [
        "*.html.liquid",
        "*.htm.liquid",
        "*.xhtml.liquid",
    ]
    version_added = ""
    alias_filenames = ["*.html", "*.htm", "*.xhtml"]
    url = "https://github.com/jg-rp/python-liquid2"

    # If this is installed, it should take priority over the standard Liquid lexer.
    priority = 0.6

    def __init__(self, **options: Any):
        super().__init__(HtmlLexer, _DelegatedLiquid2Lexer, **options)

    @staticmethod
    def analyse_text(text: str) -> float:  # noqa: D102
        rv = _DelegatedLiquid2Lexer.analyse_text(text) - 0.01
        if html_doctype_matches(text):
            rv += 0.5
        return rv
