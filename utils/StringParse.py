"""
File containing a string parsing class which upon being fed a utils.GrammarParse.Grammar object, 
"""

class StringParser(object):

    grammar = None

    def __init__(self, grammar):
        self.grammar = grammar


    # User-Level functions
    def tokenizeString(self, inputString):
        """
        Tokenizes a string, splitting on whitespace.  Takes quotes and apostrophes into account when splitting tokens.
        Example: "abc def 'g h i' jkl" -> ['abc', 'def', "'g h i'", 'jkl']

        Inputs: inputString - The string to tokenize.

        Outputs: An iterable of tokens.
        """

        pass # TODO


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
