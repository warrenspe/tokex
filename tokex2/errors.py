class TokexError:
    """ Base class for all tokex-specific errors """


class GrammarParsingError(TokexError):
    """ Base class for errors which occur while parsing an input tokex grammar """


class UnknownGrammarTokenError(GrammarParsingError):
    """ Error thrown when we are unable to tokenize a user-defined grammar. """

    def __init__(self, token):
        super().__init__()

        self.token = token

    def __str__(self):
        return "Unknown grammar token: %s" % self.token


class InvalidGrammarTokenFlagsError(GrammarParsingError):
    """ Error thrown when a grammar token in a user-defined grammar has an invalid flag """

    def __init__(self, flag, element):
        super().__init__()

        self.flag = flag
        self.element = element

    def __str__(self):
        return "Invalid flag given to token: %s.  Valid flags are: %s" % (self.flag, self.element.flags)


class MismatchedBracketsError(GrammarParsingError):
    """
    Error thrown when opening/closing brackets for a given element are mismatched
    For example, opening for a Zero or more, and closing for a one of set
    """

    def __init__(self, bracket):
        super().__init__()

        self.bracket = bracket

    def __str__(self):
        return "Mismatched bracket given: %s" % self.bracket


class SubGrammarError(GrammarParsingError):
    """ Raised when a user-defined grammar has invalid sub grammars within it """

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg
