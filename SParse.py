"""
File containing a string parsing class which upon being fed a utils.GrammarParse.Grammar object, 
"""

# Standard imports
import re

# Project imports
import _Grammar

class _StringParser(object):

    grammar = None
    stringTokenizer = re.compile("""("[^"]*"|'[^']*'|\S+)""")

    def __init__(self, grammar, allowSubGrammarDefinitions):
        self.grammar = _Grammar.constructGrammar(grammar, allowSubGrammarDefinitions)


    # User-Level functions
    def tokenizeString(self, inputString):
        """
        Tokenizes a string, splitting on whitespace.  Takes quotes and apostrophes into account when splitting tokens.
        Example: "abc def 'g h i' jkl" -> ['abc', 'def', "'g h i'", 'jkl']

        Inputs: inputString - The string to tokenize.

        Outputs: An iterable of tokens.
        """

        return self.stringTokenizer.findall(inputString)


    def match(self, inputString, matchEntirety=True):
        """
        Runs the loaded grammar against a string and returns the output if it matches the input string.

        Inputs: inputString   - The string to parse.
                matchEntirety - A boolean, if True requires the entire string to be matched by the grammar.
                                if False, trailing tokens not matched by the grammar will not cause a match failure.

        Outputs: A dictionary representing the output of parsing if the string matches the grammar, else None.
        """

        tokens = self.tokenizeString(inputString)

        match, endIdx, output = grammar.match(tokens)

        if match and (not matchEntirety or endIndex == len(tokens)):
            return output


def compile(grammar, allowSubGrammarDefinitions=True):
    """
    Constructs and returns an instance of _StringParser for repeated parsing of strings using the given grammar.
    """

    return _StringParser(grammar)


def match(self, grammarString, inputString, matchEntirety=True, allowSubGrammarDefinitions=True):
    """
    Convenience function for performing matches using a grammar against a string.

    Inputs: grammar                    - The grammar to use to parse the input string.
            inputString                - The string to be parsed.
            matchEntirety              - A boolean, if True requires the entire string to be matched by the grammar.
                                         if False, trailing tokens not matched by the grammar will not cause a match failure.
            allowSubGrammarDefinitions - A Boolean, indicating whether or not sub grammar declarations, (@name: grammar @@),
                                         should be processed.  If grammarString has come from an untrusted source this should
                                         be set to False, to mitigate the potential for a `Billion Laughs` attack.

    Outputs: The result of matching the inputString, if it matches, else None.
    """

    return _StringParser(grammar).match(inputString, matchEntirety=matchEntirety)
