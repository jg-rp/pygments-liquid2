from pygments.lexer import DelegatingLexer
from pygments.lexer import RegexLexer
from pygments.lexer import bygroups
from pygments.lexer import combined
from pygments.lexer import default
from pygments.lexer import include
from pygments.lexer import this
from pygments.lexer import using
from pygments.token import Comment
from pygments.token import Error
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


class Liquid2Lexer(RegexLexer):
    """Lexer for Liquid templates."""

    name = "liquid"
    url = "https://github.com/jg-rp/python-liquid2"
    aliases = ["liquid"]
    filenames = ["*.liquid"]
    version_added = "2.0"

    tokens = {
        "root": [
            (r"[^{]+", Text),
            # tags and block tags
            (r"(\{%)(\s*)", bygroups(Punctuation, Whitespace), "tag-or-block"),
            # output tags
            (
                r"(\{\{)(\s*)([^\s}]+)",
                bygroups(Punctuation, Whitespace, using(this, state="generic")),
                "output",
            ),
            (r"\{", Text),
        ],
        "tag-or-block": [
            # builtin logic blocks
            (r"(if|unless|elsif|case)(?=\s+)", Keyword.Reserved, "condition"),
            (
                r"(when)(\s+)",
                bygroups(Keyword.Reserved, Whitespace),
                combined("end-of-block", "whitespace", "generic"),
            ),
            (
                r"(else)(\s*)(%\})",
                bygroups(Keyword.Reserved, Whitespace, Punctuation),
                "#pop",
            ),
            # other builtin blocks
            (
                r"(capture)(\s+)([^\s%]+)(\s*)(%\})",
                bygroups(
                    Name.Tag,
                    Whitespace,
                    using(this, state="variable"),
                    Whitespace,
                    Punctuation,
                ),
                "#pop",
            ),
            (
                r"(comment)(\s*)(%\})",
                bygroups(Name.Tag, Whitespace, Punctuation),
                "comment",
            ),
            (r"(raw)(\s*)(%\})", bygroups(Name.Tag, Whitespace, Punctuation), "raw"),
            # end of block
            (
                r"(end(case|unless|if))(\s*)(%\})",
                bygroups(Keyword.Reserved, None, Whitespace, Punctuation),
                "#pop",
            ),
            (
                r"(end([^\s%]+))(\s*)(%\})",
                bygroups(Name.Tag, None, Whitespace, Punctuation),
                "#pop",
            ),
            # builtin tags (assign and include are handled together with usual tags)
            (
                r"(cycle)(\s+)(?:([^\s:]*)(:))?(\s*)",
                bygroups(
                    Name.Tag,
                    Whitespace,
                    using(this, state="generic"),
                    Punctuation,
                    Whitespace,
                ),
                "variable-tag-markup",
            ),
            # other tags or blocks
            (r"([^\s%]+)(\s*)", bygroups(Name.Tag, Whitespace), "tag-markup"),
        ],
        "output": [
            include("whitespace"),
            (r"\}\}", Punctuation, "#pop"),  # end of output
            (r"\|", Punctuation, "filters"),
        ],
        "filters": [
            include("whitespace"),
            (r"\}\}", Punctuation, ("#pop", "#pop")),  # end of filters and output
            (
                r"([^\s|:]+)(:?)(\s*)",
                bygroups(Name.Function, Punctuation, Whitespace),
                "filter-markup",
            ),
        ],
        "filter-markup": [
            (r"\|", Punctuation, "#pop"),
            include("end-of-tag"),
            include("default-param-markup"),
        ],
        "condition": [
            include("end-of-block"),
            include("whitespace"),
            (
                r"([^\s=!><]+)(\s*)([=!><]=?)(\s*)(\S+)(\s*)(%\})",
                bygroups(
                    using(this, state="generic"),
                    Whitespace,
                    Operator,
                    Whitespace,
                    using(this, state="generic"),
                    Whitespace,
                    Punctuation,
                ),
            ),
            (r"\b!", Operator),
            (r"\bnot\b", Operator.Word),
            (
                r'([\w.\'"]+)(\s+)(contains)(\s+)([\w.\'"]+)',
                bygroups(
                    using(this, state="generic"),
                    Whitespace,
                    Operator.Word,
                    Whitespace,
                    using(this, state="generic"),
                ),
            ),
            include("generic"),
            include("whitespace"),
        ],
        "generic-value": [include("generic"), include("end-at-whitespace")],
        "operator": [
            (
                r"(\s*)((=|!|>|<)=?)(\s*)",
                bygroups(Whitespace, Operator, None, Whitespace),
                "#pop",
            ),
            (
                r"(\s*)(\bcontains\b)(\s*)",
                bygroups(Whitespace, Operator.Word, Whitespace),
                "#pop",
            ),
        ],
        "end-of-tag": [(r"\}\}", Punctuation, "#pop")],
        "end-of-block": [(r"%\}", Punctuation, ("#pop", "#pop"))],
        "end-at-whitespace": [(r"\s+", Whitespace, "#pop")],
        # states for unknown markup
        "param-markup": [
            include("whitespace"),
            # params with colons or equals
            (r"([^\s=:]+)(\s*)(=|:)", bygroups(Name.Attribute, Whitespace, Operator)),
            # explicit variables
            (
                r"(\{\{)(\s*)([^\s}])(\s*)(\}\})",
                bygroups(
                    Punctuation,
                    Whitespace,
                    using(this, state="variable"),
                    Whitespace,
                    Punctuation,
                ),
            ),
            include("string"),
            include("number"),
            include("keyword"),
            (r",", Punctuation),
        ],
        "default-param-markup": [
            include("param-markup"),
            (r".", Text),  # fallback for switches / variables / un-quoted strings / ...
        ],
        "variable-param-markup": [
            include("param-markup"),
            include("variable"),
            (r".", Text),  # fallback
        ],
        "tag-markup": [
            (r"%\}", Punctuation, ("#pop", "#pop")),  # end of tag
            include("default-param-markup"),
        ],
        "variable-tag-markup": [
            (r"%\}", Punctuation, ("#pop", "#pop")),  # end of tag
            include("variable-param-markup"),
        ],
        # states for different values types
        "keyword": [(r"\b(false|true)\b", Keyword.Constant)],
        "variable": [
            (r"[a-zA-Z_]\w*", Name.Variable),
            (r"(?<=\w)\.(?=\w)", Punctuation),
        ],
        "string": [(r"'[^']*'", String.Single), (r'"[^"]*"', String.Double)],
        "number": [(r"\d+\.\d+", Number.Float), (r"\d+", Number.Integer)],
        "generic": [  # decides for variable, string, keyword or number
            include("keyword"),
            include("string"),
            include("number"),
            include("variable"),
        ],
        "whitespace": [(r"[ \t]+", Whitespace)],
        # states for builtin blocks
        "comment": [
            (
                r"(\{%)(\s*)(endcomment)(\s*)(%\})",
                bygroups(Punctuation, Whitespace, Name.Tag, Whitespace, Punctuation),
                ("#pop", "#pop"),
            ),
            (r".", Comment),
        ],
        "raw": [
            (r"[^{]+", Text),
            (
                r"(\{%)(\s*)(endraw)(\s*)(%\})",
                bygroups(Punctuation, Whitespace, Name.Tag, Whitespace, Punctuation),
                "#pop",
            ),
            (r"\{", Text),
        ],
    }
