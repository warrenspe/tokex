import re

class TokexTokenizer(object):
    """
    Base class for Tokex tokenizers.  Uses re.findall & a collection of regular expressions to break up an
    input string into a sequence of tokens.

    Can be extended by subclassing this class & implementing a `tokenize` function or creating a custom
    list of tokenizer_regexes/tweaking tokenize_newlines

    Use of this function without subclassing will tokenize an input string by breaking up all occurrances of quotes
    into their own separate token; all sequences of alphanumeric tokens into their own separate token, and all
    concurrent non-alphanumeric space characters into their own token.
    """

    tokenizer_regexes = (
        r'"[^"]*"',
        r"'[^']*'",
        r"\b\w+\b",
        r"[^a-zA-Z0-9_ \t\n\r\f\v]+"
    )

    def __init__(self, tokenizer_regexes=None, tokenize_newlines=False, ignore_empty_lines=False):
        """
        Inputs: tokenizer_regexes  - Can be passed to provide a custom list of tokenizer regexes to parse
                                     an input string with.
                tokenize_newlines  - A boolean indicating whether newlines should be treated as tokens
                ignore_empty_lines - A boolean indicating whether we should skip over empty lines or not.
                                     Only has an effect if tokenize_newlines is passed and True
        """

        self.tokenize_newlines = tokenize_newlines
        self.ignore_empty_lines = ignore_empty_lines

        if tokenizer_regexes:
            self.tokenizer_regexes = tokenizer_regexes

        if self.tokenize_newlines:
            self.tokenizer_regexes = list(self.tokenizer_regexes) + [r"\n"]

    def tokenize(self, input_string):
        """
        Function which is called by tokex to break an input string into tokens, processed by tokex.

        Inputs: input_string - A string, to break into tokens.

        Outputs: A list of tokens from input_string.
        """

        tokens = re.findall(
            "(%s)" % "|".join(self.tokenizer_regexes),
            input_string,
            flags=re.MULTILINE
        )

        if self.tokenize_newlines and self.ignore_empty_lines:
            for idx in reversed(range(len(tokens))):
                if tokens[idx] == "\n" and ((idx > 0 and tokens[idx - 1] == "\n") or idx == 0):
                    tokens.pop(idx)

        return tokens


class NumericTokenizer(TokexTokenizer):
    """
    Tokenizers which keeps numeric values together as a single token
    """

    tokenizer_regexes = (
        r'"[^"]*"',
        r"'[^']*'",
        r"\S+",
    )
