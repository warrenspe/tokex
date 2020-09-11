import inspect
import logging

from .grammar import flags, parse
from . import tokenizers
from .logger import LOGGER, TemporaryLogLevel

class Tokex(object):
    _grammar = None
    _tokenizer = None

    def __init__(self, input_grammar, allow_sub_grammar_definitions, tokenizer, default_flags=flags.DEFAULTS):
        self._grammar = parse.construct_grammar(input_grammar, allow_sub_grammar_definitions, default_flags)

        if inspect.isclass(tokenizer) and issubclass(tokenizer, tokenizers.TokexTokenizer):
            self._tokenizer = tokenizer()

        elif isinstance(tokenizer, tokenizers.TokexTokenizer):
            self._tokenizer = tokenizer

        else:
            raise Exception("Given tokenizer is not an instance of subclass of tokenizers.TokexTokenizer")


    # User-Level functions
    def match(self, input_string, match_entirety=True, debug=False):
        """
        Runs the loaded grammar against a string and returns the output if it matches the input string.

        Inputs: input_string   - The string to parse.
                match_entirety - A boolean, if True requires the entire string to be matched by the grammar.
                                if False, trailing tokens not matched by the grammar will not cause a match failure.
                debug          - A boolean, if True will set the debugging level to DEBUG for the duration of the match

        Outputs: A dictionary representing the output of parsing if the string matches the grammar, else None.
        """

        with TemporaryLogLevel(logging.DEBUG if debug else LOGGER.getEffectiveLevel()):
            tokens = self._tokenizer.tokenize(input_string)

            LOGGER.debug("Input Tokens:\n%s", tokens)

            match, end_idx, output = self._grammar.apply(tokens, 0)

            if match and (not match_entirety or end_idx == len(tokens)):
                return output[None] or {}

            return None
