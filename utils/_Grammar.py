"""
    File containing a Grammar object and grammar parsing function which are used to parse user-defined grammars.
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
        r"@\s*[\w-]+?\s*:",  # Defined Sub Grammar open
        r"@\s*[\w-]*?\s*@",  # Defined Sub Grammar close & Usage
        r"\{",               # One of Set open
        r"\}",               # One of Set close
        r"\[",               # Iterator Delimiter Open
        r"\]",               # Iterator Delimiter Close
        r"\(\*" ,            # Zero or More open
        r"\(\?",             # Zero or One open
        r"\(\+",             # One or More open
        r"\(\s*[\w-]+?\s*:", # Named Grammar open
        r"\)",               # Flow & Named Grammar close
        r"<\s*[\w-]+?\s*:",  # Named Token open
        r">",                # Named Token close
        r"_!.*?(?<!\\)_",    # Not Token Regex
        r"_notstr_",         # Not String Regex
        r"_str_",            # String Regex
        r"_",                # All Regex
        r"\^.*?(?<!\\)\^",   # Regex
        r"\$.*?(?<!\\)\$",   # Case Insensitive Regex
        r"'.*?(?<!\\)'",     # Literal Token
        r'".*?(?<!\\)"',     # Literal Token
        r"`.*?(?<!\\)`",     # Case Insensitive Literal Token
    ))


    commentTokenPattern =  r"(?P<comment>#[^\n]*(\n|$))"
    nonGrammarTokenPattern = r"(?P<nontoken>\S+)"

    pattern = "|".join((grammarTokensPattern, commentTokenPattern, nonGrammarTokenPattern))

    iterator = re.finditer(pattern, grammarString)

    tokens = []
    try:
        while True:
            match = next(iterator)
            if 'nontoken' in match.groupdict() and match.groupdict()['nontoken'] is not None:
                raise GrammarParsingError("Unknown token: %s" % match.groupdict()['nontoken'])

            elif 'comment' in match.groupdict() and match.groupdict()['comment'] is not None:
                continue

            toAppend = match.group()

            # Check for escapes in tokens, remove the escaping \ if present
            if toAppend[0] in ('"', "'", '`', '^', '$', '_'):
                toAppend = toAppend.replace("\\%s" % toAppend[0], toAppend[0])

            tokens.append(toAppend)

    except StopIteration:
        return tokens


def _processSubGrammarDefinitions(grammarTokens):
    """
    Function which expands subgrammar definitions into the grammar string.

    Inputs: grammarTokens - A list of tokens in the grammar

    Outputs: A list of tokens in the grammar, after having expanded user defined grammar tokens.
    """

    # List of tokens after expanding defined sub grammars
    parsedGrammarTokens = []

    # Dictionary mapping sub grammar names to tokens they contain
    # Note: None is being used here to refer to the global namespace, ie the main list of tokens.
    #       so we map it here to parsedGrammarTokens
    subGrammars = collections.defaultdict(list, {None: parsedGrammarTokens})

    # Dictionary for determining the scope of a sub grammar declaration.
    # Maps the name of a sub grammar to a list of sub grammar names within its scope.
    subGrammarNameSpaces = collections.defaultdict(list)

    # Stack of sub grammar names to record the current grammar being constructed.
    subGrammarStack = [None] # Use None to record the topmost, global namespace

    for token in grammarTokens:
        # Handle new defined sub grammar declarations
        if token[0] == '@' and token[-1] == ':':
            subGrammarName = token[1:-1].strip()
            if subGrammarName in subGrammars or subGrammarName in subGrammarStack:
                raise GrammarParsingError("Redeclaration of defined sub grammar: %s" % subGrammarName)

            subGrammarStack.append(subGrammarName)

        # Handle the closing of sub grammar declarations
        elif token == '@@':
            if subGrammarStack[-1] is None:
                raise GrammarParsingError("Unexpected @@; not currently defining a sub grammar.")

            closedGrammar = subGrammarStack.pop()

            # Remove any sub grammars defined within the recently closed grammar's scope
            if closedGrammar in subGrammarNameSpaces:
                for subGrammarName in subGrammarNameSpaces.pop(closedGrammar):
                    subGrammars.pop(subGrammarName)

            # Add the newly closed sub grammar to its parents namespace
            subGrammarNameSpaces[subGrammarStack[-1]].append(closedGrammar)

            # Edge case; empty sub grammar has been saved, add a key to our defaultdict so it can be later used
            if closedGrammar not in subGrammars:
                subGrammars[closedGrammar] # subGrammars is a defaultdict so accessing the key adds it

        # Handle inserting a sub grammar
        elif token[0] == '@' and token[-1] == '@':
            subGrammarName = token[1:-1].strip()

            if subGrammarName not in subGrammars:
                # Give a slightly more descriptive error message if we've seen a declaration for this sub grammar before
                if subGrammarName in subGrammarStack:
                    raise GrammarParsingError("Cannot apply %s; %s is not yet fully defined." % (token, subGrammarName))

                raise GrammarParsingError("Unknown sub grammar: %s" % subGrammarName)

            # Apply the sub grammar to the most recent sub grammar (or topmost grammar)
            subGrammars[subGrammarStack[-1]].extend(subGrammars[subGrammarName])

        # Handle adding tokens to a defined sub grammar (or topmost grammar)
        else:
            subGrammars[subGrammarStack[-1]].append(token)

    if subGrammarStack[-1] is not None:
        raise GrammarParsingError("Unclosed defined sub grammar: %s" % subGrammarStack[-1])

    return parsedGrammarTokens


def constructGrammar(grammarString, allowSubGrammarDefinitions=True):
    """
    Function which accepts a user-defined grammar string and returns an instance of Grammar representing it.

    Inputs: grammarString              - The user-defined grammar string representing the grammar we should construct.
            allowSubGrammarDefinitions - A boolean, indicating whether or not we should process user defined sub grammars.
    """

    stackOpenDict = {
        "{": OneOfSet,
        "(?": ZeroOrOne,
        "(*": ZeroOrMore,
        "(+": OneOrMore,
    }

    stackNamingOpenDict = {
        "<": NamedToken,
        "(": Grammar,
    }

    stackCloseDict = {
        "}": OneOfSet,
        ")": (ZeroOrOne, ZeroOrMore, OneOrMore, Grammar),
        ">": NamedToken,
        "]": MoreDelimiter,
    }

    grammar = Grammar()
    grammarStack = [grammar]

    grammarTokens = _tokenizeGrammar(grammarString)

    if allowSubGrammarDefinitions:
        grammarTokens = _processSubGrammarDefinitions(grammarTokens)

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
                error = "Cannot Close %s, most recent: %s, not %s" % (token, grammarStack[-1], stackCloseDict[token])
                raise GrammarParsingError(error)

            grammarStack.pop()

        # Named tokens & grammars
        elif token[0] in stackNamingOpenDict and token[-1] == ":":
            obj = stackNamingOpenDict[token[0]]()
            obj.name = token[1:-1].strip()
            grammarStack[-1].append(obj)
            grammarStack.append(obj)

        # Singlular tokens
        elif token[0] in ("'", '"', '`', '^', '$', '_'):
            grammarStack[-1].append(Token(token))

        # Iterator delimiters
        elif token == "[":
            # Ensure that the token preceeding us is a OneOrMore or a ZeroOrMore
            if not isinstance(grammarStack[-1], (ZeroOrMore, OneOrMore)):
                error = "Iteration delimiter must be applied to a (* ) or (+ ) block, not %s" % grammarStack[-1]
                raise GrammarParsingError(error)

            obj = MoreDelimiter()
            grammarStack[-1].delimiterGrammar = obj
            grammarStack.append(obj)

        else:
            raise GrammarParsingError("Unknown token: %s" % repr(token))

    if len(grammarStack) != 1:
        raise GrammarParsingError("Too few closing brackets; grammar stack length: %s when all tokens processed." %
                                   len(grammarStack))

    return grammar

###
# User-defined grammar constructs
###

class _TokexGrammar(object):

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


class Grammar(_TokexGrammar):
    """
    Grammar class representing a user-defined grammar.  Can contain further instances of itself within its language.

    An instance of this class is expected as a parameter when initializing instances of utils.StringParse.StringParser.
    """

    name = None
    tokens = None

    def __init__(self):
        self.tokens = list()


    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, [repr(t) for t in self.tokens])


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


class Token(_TokexGrammar):
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
            self.caseSensitive = caseSensitive


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
            self.regex = Token.LiteralMatcher(grammarToken[1:-1], grammarToken[0] == '`')

        elif grammarToken[0] in ('^', '$'):
            flags = (re.I if grammarToken[0] == '$' else 0)
            self.regex = re.compile(grammarToken[1:-1], flags)

        else:
            raise GrammarParsingError("Unknown token type: %s." % grammarToken)


    def __repr__(self):
        return self.regex.literal if isinstance(self.regex, Token.LiteralMatcher) else self.regex.pattern


    def match(self, stringTokens, idx):
        # If the index we're considering is beyond the end of our tokens, we have nothing to match on. Return False.
        if idx >= len(stringTokens):
            return False, None, None

        match = self.regex.match(stringTokens[idx])

        if match:
            return True, idx + 1, None

        return False, None, None


class NamedToken(_TokexGrammar):
    name = None
    token = None

    def __repr__(self):
        return "<NamedToken: %s>" % repr(self.token)

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

        return True, newIdx or idx, (None if output is None else output[self.name])


class MoreDelimiter(Grammar):
    """
    Class which can be applied to a (* ) or (+ ) block to define a grammar which must be present between matches.
    """

    name = '__MoreDelimiterNameSpace'


class ZeroOrMore(Grammar):

    name = '__ZeroOrMoreNameSpace'
    delimiterGrammar = None
    matchCount = 0 # Convenience attribute for implementing OneOrMore; reset on each call to match

    def _updateOutputLists(self, dictToUpdateWith, defaultDictToUpdate):
        for key in dictToUpdateWith:
            defaultDictToUpdate[key].append(dictToUpdateWith[key])


    def match(self, stringTokens, idx):
        self.matchCount = 0
        outputs = collections.defaultdict(list)
        while idx < len(stringTokens):
            match, newIdx, output = Grammar.match(self, stringTokens, idx)

            if not match or idx == newIdx:
                break

            idx = newIdx
            self.matchCount += 1
            if output:
                self._updateOutputLists(output[self.name], outputs)

            if self.delimiterGrammar is not None and idx < len(stringTokens):
                match, newIdx, output = self.delimiterGrammar.match(stringTokens, idx)
                if not match or idx == newIdx:
                    break

                idx = newIdx
                if output:
                    self._updateOutputLists(output[self.delimiterGrammar.name], outputs)

        return True, idx, dict(outputs) or None


class OneOrMore(ZeroOrMore):

    name = '__OneOrMoreNameSpace'

    def match(self, stringTokens, idx):
        _, newIdx, output = ZeroOrMore.match(self, stringTokens, idx)

        return self.matchCount > 0, newIdx, output


class OneOfSet(Grammar):

    def match(self, stringTokens, idx):
        for grammar in self.tokens:
            match, newIdx, output = grammar.match(stringTokens, idx)
            if match:
                return True, newIdx, output
        return False, None, None
