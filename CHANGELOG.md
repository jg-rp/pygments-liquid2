# Pygments Liquid2 Change Log

## Version 0.2.0

(Just for `Liquid2Lexer`, `StandardLiquidLexer` is unchanged.)

- Add special case for lambda expressions, like `{% assign foo = bar | map: item => item.a[0] %}`
- Use `Name.Other` instead of `Name.Variable`.

## Version 0.1.1

- Fix comments in `{% liquid %}` tags.

## Version 0.1.0

Initial release.
