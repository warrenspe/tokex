import itertools

from ._base_grammar_element import BaseGrammarElement
from .singular import AnythingElement, NewlineElement, LiteralStringElement, RegexStringElement
from .sub_grammar import SubGrammarDefinition, SubGrammarUsage



all_elements = [
    AnythingElement,
    NewlineElement,
    LiteralStringElement,
    RegexStringElement,

    SubGrammarDefinition,
    SubGrammarUsage
]
element_tokens = list(itertools.chain([
    element._grammar_tokens() for element in all_elements
]))
