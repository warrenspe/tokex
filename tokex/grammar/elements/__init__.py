from ._base_element import BaseElement, BaseScopedElement
from .singular import AnyString, Newline, StringLiteral, RegexString
from .scoped import Grammar, NamedElement, IteratorDelimiter, ZeroOrOne, ZeroOrMore, OneOrMore, OneOfSet
from .sub_grammar import SubGrammarDefinition, SubGrammarUsage


# Set which contains the first token of grammar elements which can have escapes within their contents
FIRST_CHAR_ESCAPES = {
    '~',
    '"',
    "'"
}

__all__ = [
    "BaseElement",
    "BaseScopedElement",
    "AnyString",
    "Newline",
    "StringLiteral",
    "RegexString",
    "Grammar",
    "NamedElement",
    "IteratorDelimiter",
    "ZeroOrOne",
    "ZeroOrMore",
    "OneOrMore",
    "SubGrammarDefinition",
    "SubGrammarUsage"
]
