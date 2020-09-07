from ._base_element import BaseElement
from .singular import AnyString, Newline, LiteralString, RegexString
from .scoped import Grammar, NamedElementToken, ZeroOrOne, ZeroOrMore, OneOrMore
from .sub_grammar import SubGrammarDefinition, SubGrammarUsage


# Dictionary which maps the first character of a grammar token to a grammar element class for all elements which
# can accept flags
FIRST_CHAR_VALID_FLAGS = {
    ".": AnyString,
    "~": RegexString,
    "'": LiteralString,
    '"': LiteralString,
}

__all__ = [
    BaseElement,
    AnyString,
    Newline,
    LiteralString,
    RegexString,
    Grammar,
    NamedElementToken,
    ZeroOrOne,
    ZeroOrMore,
    OneOrMore,
    SubGrammarDefinition,
    SubGrammarUsage
]
