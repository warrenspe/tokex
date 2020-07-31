import inspect
import logging
import sys

from . import grammar
from .. import tokenizers

class StringParser:
    grammar = None
    tokenizer = None

    def __init__(self, input_grammar, allow_sub_grammar_definitions, tokenizer):
        self.grammar = grammar.construct_grammar(input_grammar, allow_sub_grammar_definitions)

        if inspect.isclass(tokenizer) and issubclass(tokenizer, tokenizers.TokexTokenizer):
            self.tokenizer = tokenizer()
        elif isinstance(tokenizer, tokenizers.TokexTokenizer):
            self.tokenizer = tokenizer
        else:
            raise Exception("Given tokenizer is not an instance of subclass of tokenizers.TokexTokenizer")


    # User-Level functions
    def match(self, input_string, match_entirety=True):
        """
        Runs the loaded grammar against a string and returns the output if it matches the input string.

        Inputs: input_string   - The string to parse.
                match_entirety - A boolean, if True requires the entire string to be matched by the grammar.
                                if False, trailing tokens not matched by the grammar will not cause a match failure.

        Outputs: A dictionary representing the output of parsing if the string matches the grammar, else None.
        """

        tokens = self.tokenizer.tokenize(input_string)

        logging.debug("Input Tokens:\n%s" % tokens)

        match, endIdx, output = self.grammar.match(tokens, 0)

        if match and (not match_entirety or endIdx == len(tokens)):
            return output[None]



