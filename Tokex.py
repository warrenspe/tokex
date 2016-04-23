"""
    File containing a string parsing class which can accept a grammar and input string to return a dictionary of
    parsed tokens from the string, depending on whether or not the grammar given matches the input string and which
    named tokens exist within the grammar.

    Copyright (C) 2016 Warren Spencer
    warrenspencer27@gmail.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Standard imports
import inspect, sys

# Project imports
import utils.Grammar
import tokenizers.Tokenizer

# GLOBALS
DEBUG = False # If True will print out debugging info to sys.stderr during a match

class _StringParser(object):
    grammar = None
    tokenizer = None

    def __init__(self, grammar, allowSubGrammarDefinitions, tokenizer):
        self.grammar = utils.Grammar.constructGrammar(grammar, allowSubGrammarDefinitions)

        if inspect.isclass(tokenizer) and issubclass(tokenizer, tokenizers.Tokenizer.TokexTokenizer):
            self.tokenizer = tokenizer()
        elif isinstance(tokenizer, tokenizers.Tokenizer.TokexTokenizer):
            self.tokenizer = tokenizer
        else:
            raise Exception("Given tokenizer is not an instance of subclass of tokenizers.Tokenizer.TokexTokenizer")


    # User-Level functions
    def match(self, inputString, matchEntirety=True):
        """
        Runs the loaded grammar against a string and returns the output if it matches the input string.

        Inputs: inputString   - The string to parse.
                matchEntirety - A boolean, if True requires the entire string to be matched by the grammar.
                                if False, trailing tokens not matched by the grammar will not cause a match failure.

        Outputs: A dictionary representing the output of parsing if the string matches the grammar, else None.
        """

        tokens = self.tokenizer.tokenize(inputString)

        if DEBUG:
            sys.stderr.write("\nInput Tokens:\n\n%s\n\n" % tokens)
            sys.stderr.flush()

        try:
            utils.Grammar.DEBUG = DEBUG
            match, endIdx, output = self.grammar.match(tokens, 0)


        finally:
            utils.Grammar.DEBUG = False

        if match and (not matchEntirety or endIdx == len(tokens)):
            return output[None]


def compile(grammar,
            allowSubGrammarDefinitions=True,
            tokenizer=tokenizers.Tokenizer.TokexTokenizer):
    """
    Constructs and returns an instance of _StringParser for repeated parsing of strings using the given grammar.

    Inputs: grammar   - The grammar to use to parse the input string.
            allowSubGrammarDefinitions - A Boolean, indicating whether or not sub grammar declarations,
                                         (@name: grammar @@), should be processed.  If grammarString has
                                         come from an untrusted source this should be set to False, to
                                         mitigate the potential for a `Billion Laughs` attack.
            tokenizer - Optional: An instance or class of tokenizers.Tokenizer.TokexTokenizer or a subclass of it,
                            used to tokenize the input string for parsing. Defaults to the base class TokexTokenizer.

    Outputs: An instance of _StringParser whose `match` function can be used to repeatedly parse input strings.
    """

    return _StringParser(grammar, allowSubGrammarDefinitions, tokenizer)


def match(grammar,
          inputString,
          matchEntirety=True,
          allowSubGrammarDefinitions=True,
          tokenizer=tokenizers.Tokenizer.TokexTokenizer):
    """
    Convenience function for performing matches using a grammar against a string.

    Inputs: grammar       - The grammar to use to parse the input string.
            inputString   - The string to be parsed.
            matchEntirety - A boolean, if True requires the entire string to be matched by the grammar.
                                       if False, trailing tokens not matched by the grammar will not
                                                 cause a match failure.
            allowSubGrammarDefinitions - A Boolean, indicating whether or not sub grammar declarations,
                                         (@name: grammar @@), should be processed.  If grammarString has
                                         come from an untrusted source this should be set to False, to
                                         mitigate the potential for a `Billion Laughs` attack.
            tokenizer     - Optional: An instance or class of tokenizers.Tokenizer.TokexTokenizer or a subclass of it,
                            used to tokenize the input string for parsing. Defaults to the base class TokexTokenizer.

    Outputs: The result of matching the inputString, if it matches, else None.
    """

    return _StringParser(
        grammar,
        allowSubGrammarDefinitions,
        tokenizer
    ).match(inputString, matchEntirety=matchEntirety)
