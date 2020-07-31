import re

class TokexTokenizer(object):
    """
    Base class for Tokex Tokenizers.  Uses re.findall & a collection of regular expressions to break up an
    input string into a sequence of tokens.

    Can be extended by subclassing this class & implementing a `tokenize` function, or by creating a custom
    list of tokenizerRegexes.

    Use of this function without subclassing will tokenize an input string by breaking up all occurrances of quotes
    into their own separate token; all sequences of ascii tokens into their own separate token, and all
    remaining non-white space characters into their own token.  Note that this will cause things like "!=" to be
    broken into two separate tokens.
    """

    tokenizer_regexes = [
        '"[^"]*"',
        "'[^']*'",
        '\w+',
        '\S'
    ]


    def tokenize(self, input_string):
        """
        Function which is called by tokex to break an input string into tokens, processed by tokex.

        Inputs: input_string - A string, to break into tokens.

        Outputs: A list of tokens from input_string.
        """

        return re.findall("(%s)" % "|".join(self.tokenizer_regexes), input_string)
