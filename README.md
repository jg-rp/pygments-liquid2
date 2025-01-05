<h1 align="center">Pygments Liquid2</h1>

<p align="center">
Some Liquid lexers for Pygments.
</p>

<p align="center">
  <a href="https://github.com/jg-rp/pygments-liquid2/blob/main/LICENSE.txt">
    <img src="https://img.shields.io/pypi/l/pygments-liquid2?style=flat-square" alt="License">
  </a>
  <a href="https://github.com/jg-rp/pygments-liquid2/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/jg-rp/pygments-liquid2/tests.yaml?branch=main&label=tests&style=flat-square" alt="Tests">
  </a>
  <a href="https://pypi.org/project/pygments-liquid2">
    <img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dm/pygments-liquid2?style=flat-square">
  </a>
  <br>
  <a href="https://pypi.org/project/pygments-liquid2">
    <img src="https://img.shields.io/pypi/v/pygments-liquid2.svg?style=flat-square" alt="PyPi - Version">
  </a>
  <a href="https://pypi.org/project/pygments-liquid2">
    <img src="https://img.shields.io/pypi/pyversions/pygments-liquid2.svg?style=flat-square" alt="Python versions">
  </a>
</p>

---

## Table of Contents

- [Installation](#installation)
- [Available lexers](#liquid-lexers)
- [Lexer priority](#lexer-priority)
- [License](#license)

## Installation

```console
pip install pygments-liquid2
```

This package uses the [Pygments plugin entry point](https://pygments.org/docs/plugins/), so, if its installed in your Python environment, additional Liquid lexers will be available automatically. Confirm this by listing lexers with one of the following methods.

### Listing lexers on the command line:

```console
pygmentize -L lexers | grep -i liquid
```

```
* html+liquid, htmlliquid:
    HTML+Liquid (filenames *.html.liquid, *.htm.liquid, *.xhtml.liquid)
* html+liquid2, html+liquid, htmlliquid:
    HTML+Liquid2 (filenames *.html.liquid, *.htm.liquid, *.xhtml.liquid)
* liquid2, liquid:
    liquid2 (filenames *.liquid)
* liquid:
    liquid (filenames *.liquid)
* liquid:
    liquid-std (filenames *.liquid)
```

### Listing lexers with Python

```python
from pygments.lexers import get_all_lexers

all_lexers = get_all_lexers(plugins=True)
liquid_lexers = sorted(lexer for lexer in all_lexers if "liquid" in lexer[0].lower())

for name, aliases, _filenames, _mimetypes in liquid_lexers:
    print(f"{name}: {aliases}")
```

## Available lexers

After installation, these Liquid lexers should be available.

### `liquid`

The Liquid lexer built in to Pygments.

This lexer is importable from Python using `from pygments.lexers import LiquidLexer`.

### `liquid-std`

An alternative Liquid lexer for [Shopify/Liquid](https://github.com/Shopify/liquid) syntax. This lexer makes the following changes over the built-in Liquid lexer.

- Add support for nested block comments (those with balanced `comment`/`endcomment` tags).
- Add support for whitespace control, like `{{- some.thing -}}`.
- Add support for inline comment tags, like `{% # some comment %}`.
- Add support for `{% liquid %}` tags.
- Add support for bracketed variable and index, like `foo[bar]["with a space"][1]`.
- Allow tag and output expressions to span multiple lines.
- Remove the logical `not` keyword.

This lexer is importable from Python using `from pygments_liquid2 import StandardLiquidLexer`.

### `html+liquid`

A [`DelegatingLexer`](https://pygments.org/docs/lexerdevelopment/#delegating-lexer) for highlighting HTML with standard Liquid markup.

This lexer is importable from Python using `from pygments_liquid2 import HtmlLiquidLexer`.

### `liquid2`

A Liquid lexer with the following extended syntax over `liquid-std` described above.

- Add support for new style comments, like `{# some comment #}`.
- Add support for template strings, like `{{ "Hello, ${you | upcase}" }}`.
- Add some extra keywords.
- Add support for scientific notation for floats and integers.
- Add more whitespace control characters, like `{{+ some.thing ~}}`.

This lexer is importable from Python using `from pygments_liquid2 import Liquid2Lexer`.

### `html+liquid2`

A [`DelegatingLexer`](https://pygments.org/docs/lexerdevelopment/#delegating-lexer) for highlighting HTML with Liquid2 markup.

This lexer is importable from Python using `from pygments_liquid2 import HtmlLiquid2Lexer`.

## Lexer priority

`liquid2` and `html+liquid2` are given a higher priority than the Liquid lexer built-in to Pygments and `liquid-std`. So, when using Pygments functions like `get_lexer_for_filename()` and `guess_lexer()`, you should expect to get a Liquid2 lexer over a standard Liquid lexer.

## License

`pygments-liquid2` is distributed under the terms of the [BSD-2-Clause](https://github.com/jg-rp/pygments-liquid2/blob/main/LICENSE.txt) license.

We've used bits and pieces from lexers built-in to Pygments, so we included their [BSD-2-Clause license](https://github.com/jg-rp/pygments-liquid2/blob/main/LICENSE_Pygments.txt) too.
