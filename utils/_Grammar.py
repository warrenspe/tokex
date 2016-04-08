"""
File containing a Grammar object and grammar parsing function which are used to parse user-defined grammars.
"""

# Standard imports
import re, collections

###
# Custom exceptions
###

class GrammarParsingError(Exception):
    """
    Error thrown when a user-defined grammar is malformed.
    """

###
# Utility functions
###

def _tokenizeGrammar(grammarString):
    """
    Function which accepts a grammar string and returns an iterable of tokens
    """

    grammarTokensPattern = "|".join((
        r"@[^@]*?:",       # Defined Sub Grammar open
        r"@@",             # Defined Sub Grammar close
        r"\{\{",           # One of Set open
        r"\}\}",           # One of Set close
        r"\(\(",           # Zero or More open
        r"\)\)",           # Zero or More close
        r"\[\[",           # Zero or One open
        r"\]\]",           # Zero or One close
        r"\(\w*?:",        # Named Grammar open
        r"\)",             # Named Grammar close
        r"<\w*?:",         # Named Token open
        r">",              # Named Token close
        r"_!.*?(?<!\\)_",  # Not Token Regex
        r"_notstr_",       # Not String Regex
        r"_str_",          # String Regex
        r"_",              # All Regex
        r"\^.*?(?<!\\)\^", # Regex
        r"\$.*?(?<!\\)\$", # Case Insensitive Regex
        r"'.*?(?<!\\)'",   # Literal Token
        r'".*?(?<!\\)"',   # Literal Token
        r"`.*?(?<!\\)`",   # Case Insensitive Literal Token
    ))


    nonGrammarTokenPattern = r"(?P<nontoken>\S+)"

    pattern = "|".join((grammarTokensPattern, nonGrammarTokenPattern))

    iterator = re.finditer(pattern, grammarString)

    tokens = []
    try:
        while True:
            match = iterator.next()
            if 'nontoken' in match.groupdict() and match.groupdict()['nontoken'] is not None:
                raise GrammarParsingError("Unknown token: %s" % match.groupdict()['nontoken'])
            tokens.append(match.group())

    except StopIteration:
        return tokens


def _processSubGrammarDefinitions(grammarTokens):
    """
    Function which expands subgrammar definitions into the grammar string.

    Inputs: grammarTokens - A list of tokens in the grammar

    Outputs: A list of tokens in the grammar, after having expanded user defined grammar tokens.
    """

    subGrammars = collections.defaultdict(list)
    subGrammarStack = []

    parsedGrammarTokens = []

    idx = 0

    # Parse out any defined sub grammars
    for token in grammarTokens:
        # Handle new defined sub grammar declarations
        if token[0] == '@' and token[-1] == ':':
            subGrammarName = token[1:-1]
            if subGrammarname in subGrammars:
                raise GrammarParsingError("Redeclaration of defined sub grammar: %s" % subGrammarName)

            subGrammarStack.append(subGrammarName)

        # Handle the closing of sub grammar declarations
        elif token == '@@':
            if not subGrammarStack:
                raise GrammarParsingError("Rogue @@; not currently defining a sub grammar.")

            subGrammarStack.pop()

        # Handle inserting a sub grammar
        elif token[0] == '@' and token[-1] == '@':
            subGrammarName = token[1:-1]

            if subGrammarName in subGrammarStack:
                raise GrammarParsingError("Cannot apply %s; %s is not yet fully defined." % (token, subGrammarName))

            # Handle applying a sub grammar to another sub grammar declaration
            if len(subGrammarStack):
                subGrammars[subGrammarStack[-1]].extend(subGrammars[subGrammarName])

            # Handle applying a sub grammar to the main grammar
            else:
                parsedGrammarTokens.extend(subGrammars[subGrammarName])

        # Handle adding tokens to a defined sub grammar
        elif len(subGrammarStack):
            subGrammars[subGrammarStack[-1]].append(token)

        # Handle adding tokens not defined in a sub grammar
        else:
            parsedGrammarTokens.append(token)

    if len(subGrammarStack):
        raise GrammarParsingError("Unclosed defined sub grammar: %s" % subGrammarStack[-1])

    return parsedGrammarTokens


def constructGrammar(grammarString, allowSubGrammarDefinitions=True):
    """
    Function which accepts a user-defined grammar string and returns an instance of Grammar representing it.

    Inputs: grammarString              - The user-defined grammar string representing the grammar we should construct.
            allowSubGrammarDefinitions - A boolean, indicating whether or not we should process user defined sub grammars.
    """

    stackOpenDict = {
        "{{": OneOfSet,
        "[[": ZeroOrOne,
        "((": ZeroOrMore,
    }

    stackNamingOpenDict = {
        "<": NamedToken,
        "(": Grammar,
    }

    stackCloseDict = {
        "}}": OneOfSet,
        "]]": ZeroOrOne,
        "))": ZeroOrMore,
        ">": NamedToken,
        ")": Grammar,
    }

    grammar = Grammar()
    grammarStack = [grammar]

    grammarTokens = _tokenizeGrammar(grammarString)

    if allowSubGrammarDefinitions:
        grammarTokens = _processSubGrammarDefinitions(grammarString)

    if not len(grammarTokens):
        raise GrammarParsingError

    for token in grammarTokens:
        if not len(grammarStack):
            raise GrammarParsingError("Too many closing brackets; grammar stack empty while still tokens remaining.")

        # Stack-modifying open tokens
        if token in stackOpenDict:
            obj = stackOpenDict[token]()
            grammarStack[-1].append(obj)
            grammarStack.append(obj)

        # Closing tokens
        elif token in stackCloseDict:
            if not isinstance(grammarStack[-1], stackCloseDict[token]):
                error = "Cannot Close %s, most recent grammar: %s, not %s" % (token, grammarStack[-1], stackCloseDict[token])
                raise GrammarParsingError(error)

            grammarStack.pop()

        # Named tokens & grammars
        elif token[0] in stackNamingOpenDict and token[-1] == ":":
            obj = stackNamingOpenDict[token[0]]()
            obj.name = token[1:-1]
            grammarStack[-1].append(obj)
            grammarStack.append(obj)

        # Singlular tokens
        elif token[0] in ("'", '"', '`', '^', '$', '_'):
            grammarStack[-1].append(Token(token))

        else:
            raise GrammarParsingError("Unknown token: %s" % repr(token))

    if len(grammarStack) != 1:
        raise GrammarParsingError("Too few closing brackets; grammar stack length: %s when all tokens processed." %
                                   len(grammarStack))

    return grammar

###
# User-defined grammar constructs
###

class _SParseGrammar(object):

    def match(self, stringTokens, idx):
        """
        Function which accepts an iterable of tokens and a current index and determines whether or not this construct
        matches the list at the current position. Should be overridden in subclasses.

        Inputs: stringTokens - An iterable of string tokens to determine if we match upon.
                idx          - The start index within the stringTokens to begin processing at.

        Outputs: A triple containing: {
            match: A boolean depicting whether or not this construct matches the iterable at the current position.
            newIdx: The index this construct ceased matching upon the iterable, if match is True. Else None
            output: If there are any named matches within this construct, a dictionary or list.  Else None
        )
        """

        raise NotImplementedError


class Grammar(_SParseGrammar):
    """
    Grammar class representing a user-defined grammar.  Can contain further instances of itself within its language.

    An instance of this class is expected as a parameter when initializing instances of utils.StringParse.StringParser.
    """

    name = None
    tokens = None

    def __init__(self):
        self.tokens = list()


    def append(self, item):
        self.tokens.append(item)


    def match(self, stringTokens, idx):
        returnDict = dict()
        for item in self.tokens:
            match, idx, output = item.match(stringTokens, idx)

            if not match:
                return False, None, None

            if isinstance(output, dict):
                returnDict.update(output)

        return True, idx, {self.name: returnDict}


class Token(_SParseGrammar):
    """
    Token class representing one of the various types of tokens that can be present in a user-defined grammar.
    """

    # Built-in regex's
    allToken = re.compile(r".+$")
    strToken = re.compile(r"([\"'])(\\\1|[^\1])*\1$")
    notStrToken = re.compile(r"[^\"']*$")

    regex = None

    class LiteralMatcher(object):
        literal = None
        caseSensitive = False

        def __init__(self, literal, caseSensitive=0):
            self.literal = literal
            if caseSensitive == re.I:
                self.caseSensitive = True


        def match(self, token):
            return self.literal == token if self.caseSensitive else self.literal.lower() == token.lower()


    def __init__(self, grammarToken):
        if grammarToken[0] != grammarToken[-1]:
            raise GrammarParsingError("Token must start and end with the same character.")


        if grammarToken[0] == "_":
            if grammarToken == "_":
                self.regex = Token.allToken
            elif grammarToken == "_str_":
                self.regex = Token.strToken
            elif grammarToken == "_notstr_":
                self.regex = Token.notStrToken
            elif grammarToken[1] == "!":
                self.regex = re.compile("(?!%s$).*$" % grammarToken[2:-1], re.I)
            else:
                raise GrammarParsingError("Unknown token: %s" % grammarToken)

        elif grammarToken[0] in ("'", '"', '`'):
            self.regex = Token.LiteralMatcher(grammarToken[1:-1], grammarToken[0] != '`')

        elif grammarToken[0] in ('^', '$'):
            flags = (re.I if grammarToken[0] == '$' else 0)
            self.regex = re.compile(grammarToken[1:-1], flags)

        else:
            raise GrammarParsingError("Unknown token type: %s." % grammarToken)



    def match(self, stringTokens, idx):
        # If the index we're considering is beyond the end of our tokens, we have nothing to match on. Return False.
        if idx >= len(stringTokens):
            return False, None, None

        match = self.regex.match(stringTokens[idx])

        if match:
            return True, idx + 1, None

        return False, None, None


class NamedToken(_SParseGrammar):
    name = None
    token = None

    def append(self, item):
        if self.token is not None:
            raise GrammarParsingError("Cannot append %s to NamedToken, already have token: %s" % (item, self.token))
        self.token = item


    def match(self, stringTokens, idx):
        match, newIdx, _ = self.token.match(stringTokens, idx)

        if match:
            return True, newIdx, {self.name: stringTokens[idx]}

        return False, None, None

class ZeroOrOne(Grammar):

    name = '__ZeroOrOneNameSpace'

    def match(self, stringTokens, idx):
        # If the index we're considering is beyond the end of our tokens we have nothing to match on.  However, since
        # we can match Zero times, return True.  This allows gramars with trailing ZeroOrOne rules to match strings
        # which don't use them.
        if idx >= len(stringTokens):
            return True, idx, None

        _, newIdx, output = super(ZeroOrOne, self).match(stringTokens, idx)
        return True, newIdx or idx, output[self.name]


class ZeroOrMore(Grammar):

    name = '__ZeroOrMoreNameSpace'

    def match(self, stringTokens, idx):
        outputs = []
        while idx < len(stringTokens):
            match, newIdx, output = super(ZeroOrMore, self).match(stringTokens, idx)

            if not match or idx == newIdx:
                break

            idx = newIdx
            outputs.append(output[self.name])

        returnOutputs = collections.defaultdict(list)
        for output in outputs:
            for key, val in output.items():
                returnOutputs[key].append(val)

        return True, idx, dict(returnOutputs) or None


class OneOfSet(_SParseGrammar):
    grammars = []

    def __init__(self):
        self.grammars = []


    def append(self, grammar):
        self.grammars.append(grammar)


    def match(self, stringTokens, idx):
        for grammar in self.grammars:
            match, newIdx, output = grammar.match(stringTokens, idx)
            if match:
                return True, newIdx, output
        return False, None, None
