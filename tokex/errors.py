class TokexError(Exception):
    """ Base class for all tokex-specific errors """


class GrammarParsingError(TokexError):
    """ Base class for errors which occur while parsing an input tokex grammar """


class UnknownGrammarTokenError(GrammarParsingError):
    """ Error thrown when we are unable to tokenize a user-defined grammar. """

    def __init__(self, token):
        super(UnknownGrammarTokenError, self).__init__()

        self.token = token

    def __str__(self):
        return "Unknown grammar token: %s" % self.token


class InvalidGrammarTokenFlagsError(GrammarParsingError):
    """ Error thrown when a grammar token in a user-defined grammar has an invalid flag """

    def __init__(self, flags, element):
        super(InvalidGrammarTokenFlagsError, self).__init__()

        self.flags = flags
        self.element = element

    def __str__(self):
        add_s = ""
        if len(self.flags) > 1:
            add_s = "s"
        return "Invalid flag%s given to %r: %s.  Valid flags are: %s" % (
            add_s,
            self.element,
            "".join(self.flags),
            self.element.valid_flags
        )


class MismatchedBracketsError(GrammarParsingError):
    """
    Error thrown when opening/closing brackets for a given element are mismatched
    For example, opening for a Zero or more, and closing for a one of set
    """

    def __init__(self, bracket, current_scope=None):
        super(MismatchedBracketsError, self).__init__()

        self.bracket = bracket
        self.current_scope = current_scope

    def __str__(self):
        if self.current_scope:
            return "Mismatched bracket given: %s for scoped element: %r" % (self.bracket, self.current_scope)

        return "Mismatched bracket given: %s" % self.bracket


class SubGrammarError(GrammarParsingError):
    """ Raised when a user-defined grammar has invalid sub grammars within it """

    def __init__(self, msg):
        super(SubGrammarError, self).__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg
