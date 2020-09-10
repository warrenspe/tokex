from ._base_element import BaseElement, BaseScopedElement
from .singular import AnyString, Newline, StringLiteral, RegexString
from .scoped import Grammar, NamedElement, IteratorDelimiter, ZeroOrOne, ZeroOrMore, OneOrMore, OneOfSet
from .sub_grammar import SubGrammarDefinition, SubGrammarUsage


# Dictionary which maps the first character of a grammar token to a grammar element class for all elements which
# can accept flags
FIRST_CHAR_VALID_FLAGS = {
    ".": AnyString,
    "~": RegexString,
    "'": StringLiteral,
    '"': StringLiteral,
}

FIRST_CHAR_ESCAPES = {
    '~',
    '"',
    "'"
}

__all__ = [
    BaseElement,
    BaseScopedElement,
    AnyString,
    Newline,
    StringLiteral,
    RegexString,
    Grammar,
    NamedElement,
    IteratorDelimiter,
    ZeroOrOne,
    ZeroOrMore,
    OneOrMore,
    SubGrammarDefinition,
    SubGrammarUsage
]
