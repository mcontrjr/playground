"""Pure CSV parsers for each supported bank export format.

No module in this package may import SQLAlchemy or otherwise touch the
database — parsers are pure functions of (text, filename) -> ParseResult.
"""
