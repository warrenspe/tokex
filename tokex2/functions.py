import inspect
import sys

from .utils import string_parser
from .tokenizers import tokenizer


def compile(input_grammar,
            allow_sub_grammar_definitions=True,
            tokenizer=tokenizer.TokexTokenizer):
    """
    Constructs and returns an instance of _StringParser for repeated parsing of strings using the given grammar.

    Inputs: input_grammar   - The grammar to use to parse the input string.
            allow_sub_grammar_definitions - A Boolean, indicating whether or not sub grammar declarations,
                                            (@name: grammar @@), should be processed.  If grammarString has
                                            come from an untrusted source this should be set to False, to
                                            mitigate the potential for a `Billion Laughs` attack.
            tokenizer - Optional: An instance or class of tokenizers.Tokenizer.TokexTokenizer or a subclass of it,
                            used to tokenize the input string for parsing. Defaults to the base class TokexTokenizer.

    Outputs: An instance of _StringParser whose `match` function can be used to repeatedly parse input strings.
    """

    return string_parser.StringParser(input_grammar, allow_sub_grammar_definitions, tokenizer)


def match(input_grammar,
          input_string,
          match_entirety=True,
          allow_sub_grammar_definitions=True,
          tokenizer=tokenizer.TokexTokenizer):
    """
    Convenience function for performing matches using a grammar against a string.

    Inputs: input_grammar        - The grammar to use to parse the input string.
            input_string   - The string to be parsed.
            match_entirety - A boolean, if True requires the entire string to be matched by the grammar.
                                       if False, trailing tokens not matched by the grammar will not
                                                 cause a match failure.
            allow_sub_grammar_definitions - A Boolean, indicating whether or not sub grammar declarations,
                                         (@name: grammar @@), should be processed.  If grammarString has
                                         come from an untrusted source this should be set to False, to
                                         mitigate the potential for a `Billion Laughs` attack.
            tokenizer      - Optional: An instance or class of tokenizers.Tokenizer.TokexTokenizer or a subclass of it,
                            used to tokenize the input string for parsing. Defaults to the base class TokexTokenizer.

    Outputs: The result of matching the input_string, if it matches, else None.
    """

    return string_parser.StringParser(
        input_grammar,
        allow_sub_grammar_definitions,
        tokenizer
    ).match(input_string, match_entirety=match_entirety)
