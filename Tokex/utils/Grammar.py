import collections
import functools
import logging
import re
import sys

###
# Custom exceptions
###

class GrammarParsingError(Exception):
    """
    Error thrown when a user-defined grammar is malformed.
    """

class GrammarTokenizingError(GrammarParsingError):
    """
    Error thrown when we are unable to tokenize a user-defined grammar.
    """

    def __init__(self, token):
        super(GrammarParsingError, self).__init__(self)

        self.token = token

    def __str__(self):
        return "Unknown token when parsing Grammar: %s" % self.token


###
# Utility functions
###

def _tokenize_grammar(grammar_string):
    """
    Function which accepts a grammar string and returns an iterable of tokens
    """

    grammar_tokens_pattern = "|".join((
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


    comment_token_pattern =  r"(?P<comment>#[^\n]*(\n|$))"
    non_grammar_token_pattern = r"(?P<nontoken>\S+)"

    pattern = "|".join((grammar_tokens_pattern, comment_token_pattern, non_grammar_token_pattern))

    iterator = re.finditer(pattern, grammar_string)

    tokens = []
    try:
        while True:
            match = next(iterator)
            if 'nontoken' in match.groupdict() and match.groupdict()['nontoken'] is not None:
                raise GrammarTokenizingError(match.groupdict()['nontoken'])

            elif 'comment' in match.groupdict() and match.groupdict()['comment'] is not None:
                continue

            to_append = match.group()

            # Check for escapes in tokens, remove the escaping \ if present
            if to_append[0] in ('"', "'", '`', '^', '$', '_'):
                to_append = to_append.replace("\\%s" % to_append[0], to_append[0])

            tokens.append(to_append)

    except StopIteration:
        return tokens


def _process_sub_grammar_definitions(grammar_tokens):
    """
    Function which expands subgrammar definitions into the grammar string.

    Inputs: grammar_tokens - A list of tokens in the grammar

    Outputs: A list of tokens in the grammar, after having expanded user defined grammar tokens.
    """

    # List of tokens after expanding defined sub grammars
    parsed_grammar_tokens = []

    # Dictionary mapping sub grammar names to tokens they contain
    # Note: None is being used here to refer to the global namespace, ie the main list of tokens.
    #       so we map it here to parsed_grammar_tokens
    sub_grammars = collections.defaultdict(list, {None: parsed_grammar_tokens})

    # Dictionary for determining the scope of a sub grammar declaration.
    # Maps the name of a sub grammar to a list of sub grammar names within its scope.
    sub_grammar_name_spaces = collections.defaultdict(list)

    # Stack of sub grammar names to record the current grammar being constructed.
    sub_grammar_stack = [None] # Use None to record the topmost, global namespace

    for token in grammar_tokens:
        # Handle new defined sub grammar declarations
        if token[0] == '@' and token[-1] == ':':
            sub_grammar_name = token[1:-1].strip()
            if sub_grammar_name in sub_grammars or sub_grammar_name in sub_grammar_stack:
                raise GrammarParsingError("Redeclaration of defined sub grammar: %s" % sub_grammar_name)

            sub_grammar_stack.append(sub_grammar_name)

        # Handle the closing of sub grammar declarations
        elif token == '@@':
            if sub_grammar_stack[-1] is None:
                raise GrammarParsingError("Unexpected @@; not currently defining a sub grammar.")

            closed_grammar = sub_grammar_stack.pop()

            # Remove any sub grammars defined within the recently closed grammar's scope
            if closed_grammar in sub_grammar_name_spaces:
                for sub_grammar_name in sub_grammar_name_spaces.pop(closed_grammar):
                    sub_grammars.pop(sub_grammar_name)

            # Add the newly closed sub grammar to its parents namespace
            sub_grammar_name_spaces[sub_grammar_stack[-1]].append(closed_grammar)

            # Edge case; empty sub grammar has been saved, add a key to our defaultdict so it can be later used
            if closed_grammar not in sub_grammars:
                sub_grammars[closed_grammar] # sub_grammars is a defaultdict so accessing the key adds it

        # Handle inserting a sub grammar
        elif token[0] == '@' and token[-1] == '@':
            sub_grammar_name = token[1:-1].strip()

            if sub_grammar_name not in sub_grammars:
                # Give a slightly more descriptive error message if we've seen a declaration for this sub grammar before
                if sub_grammar_name in sub_grammar_stack:
                    raise GrammarParsingError("Cannot apply %s; %s is not yet fully defined." % (token, sub_grammar_name))

                raise GrammarParsingError("Unknown sub grammar: %s" % sub_grammar_name)

            # Apply the sub grammar to the most recent sub grammar (or topmost grammar)
            sub_grammars[sub_grammar_stack[-1]].extend(sub_grammars[sub_grammar_name])

        # Handle adding tokens to a defined sub grammar (or topmost grammar)
        else:
            sub_grammars[sub_grammar_stack[-1]].append(token)

    if sub_grammar_stack[-1] is not None:
        raise GrammarParsingError("Unclosed defined sub grammar: %s" % sub_grammar_stack[-1])

    return parsed_grammar_tokens


def construct_grammar(grammar_string, allow_sub_grammar_definitions=True):
    """
    Function which accepts a user-defined grammar string and returns an instance of Grammar representing it.

    Inputs: grammar_string                - The user-defined grammar string representing the grammar we should construct.
            allow_sub_grammar_definitions - A boolean, indicating whether or not we should process user defined sub grammars.
    """

    stack_open_dict = {
        "{": OneOfSet,
        "(?": ZeroOrOne,
        "(*": ZeroOrMore,
        "(+": OneOrMore,
    }

    stack_naming_open_dict = {
        "<": NamedToken,
        "(": Grammar,
    }

    stack_close_dict = {
        "}": OneOfSet,
        ")": (ZeroOrOne, ZeroOrMore, OneOrMore, Grammar),
        ">": NamedToken,
        "]": MoreDelimiter,
    }

    grammar = Grammar()
    grammar_stack = [grammar]

    grammar_tokens = _tokenize_grammar(grammar_string)

    if allow_sub_grammar_definitions:
        grammar_tokens = _process_sub_grammar_definitions(grammar_tokens)

    for token in grammar_tokens:
        if not len(grammar_stack):
            raise GrammarParsingError("Too many closing brackets; grammar stack empty while still tokens remaining.")

        # Stack-modifying open tokens
        if token in stack_open_dict:
            obj = stack_open_dict[token]()
            grammar_stack[-1].append(obj)
            grammar_stack.append(obj)

        # Closing tokens
        elif token in stack_close_dict:
            if not isinstance(grammar_stack[-1], stack_close_dict[token]):
                error = "Cannot Close %s, most recent: %s, not %s" % (token, grammar_stack[-1], stack_close_dict[token])
                raise GrammarParsingError(error)

            grammar_stack.pop()

        # Named tokens & grammars
        elif token[0] in stack_naming_open_dict and token[-1] == ":":
            obj = stack_naming_open_dict[token[0]]()
            obj.name = token[1:-1].strip()
            grammar_stack[-1].append(obj)
            grammar_stack.append(obj)

        # Singlular tokens
        elif token[0] in ("'", '"', '`', '^', '$', '_'):
            grammar_stack[-1].append(Token(token))

        # Iterator delimiters
        elif token == "[":
            # Ensure that the token preceeding us is a OneOrMore or a ZeroOrMore
            if not isinstance(grammar_stack[-1], (ZeroOrMore, OneOrMore)):
                error = "Iteration delimiter must be applied to a (* ) or (+ ) block, not %s" % grammar_stack[-1]
                raise GrammarParsingError(error)

            obj = MoreDelimiter()
            grammar_stack[-1].delimiter_grammar = obj
            grammar_stack.append(obj)

        else:
            raise GrammarParsingError("Unknown token: %s" % repr(token))

    if len(grammar_stack) != 1:
        raise GrammarParsingError("Too few closing brackets; grammar stack length: %s when all tokens processed." %
                                   len(grammar_stack))

    return grammar

###
# User-defined grammar constructs
###

class _TokexGrammar(object):

    def __init__(self, *args, **kwargs):
        self.match = self._match_wrapper(self.match)


    def _match_wrapper(self, match_function):
        """
        Function wrapper which takes a match function and wraps it in another function to perform additional
        functionality when matching.
        """

        @functools.wraps(match_function)
        def match_wrapper(string_tokens, idx):
            if logging.getLogger().isEnabledFor(logging.DEBUG) and idx < len(string_tokens):
                logging.debug("Current Token: %s\n\nMATCHING: %s\n" % (self, string_tokens[idx]))

            match, idx, output = match_function(string_tokens, idx)

            if logging.getLogger().isEnabledFor(logging.DEBUG) and idx < len(string_tokens):
                logging.debug("Matched: %s\n" % match)

            return match, idx, output

        return match_wrapper


    def match(self, string_tokens, idx):
        """
        Function which accepts an iterable of tokens and a current index and determines whether or not this construct
        matches the list at the current position. Should be overridden in subclasses.

        Inputs: string_tokens - An iterable of string tokens to determine if we match upon.
                idx          - The start index within the string_tokens to begin processing at.

        Outputs: A triple containing: {
            match: A boolean depicting whether or not this construct matches the iterable at the current position.
            new_idx: The index this construct ceased matching upon the iterable, if match is True. Else None
            output: If there are any named matches within this construct, a dictionary or list.  Else None
        )
        """

        raise NotImplementedError


class Grammar(_TokexGrammar):
    """
    Grammar class representing a user-defined grammar.  Can contain further instances of itself within its language.

    An instance of this class is expected as a parameter when initializing instances of utils.string_parser.StringParser.
    """

    name = None
    tokens = None

    def __init__(self):
        _TokexGrammar.__init__(self)
        self.tokens = list()


    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, [repr(t) for t in self.tokens])


    def append(self, item):
        self.tokens.append(item)


    def match(self, string_tokens, idx):
        return_dict = dict()
        for item in self.tokens:
            match, idx, output = item.match(string_tokens, idx)

            if not match:
                return False, None, None

            if isinstance(output, dict):
                return_dict.update(output)

        return True, idx, {self.name: return_dict}


class Token(_TokexGrammar):
    """
    Token class representing one of the various types of tokens that can be present in a user-defined grammar.
    """

    # Built-in regex's
    all_token = re.compile(r".+$")
    str_token = re.compile(r"([\"'])(\\\1|[^\1])*\1$")
    not_str_token = re.compile(r"[^\"']*$")

    regex = None

    class LiteralMatcher(object):
        literal = None
        case_sensitive = False

        def __init__(self, literal, case_sensitive=0):
            self.literal = literal
            self.case_sensitive = case_sensitive


        def match(self, token):
            return self.literal == token if self.case_sensitive else self.literal.lower() == token.lower()


    def __init__(self, grammar_token):
        _TokexGrammar.__init__(self)

        if grammar_token[0] != grammar_token[-1]:
            raise GrammarParsingError("Token must start and end with the same character: %s" % grammar_token)


        if grammar_token[0] == "_":
            if grammar_token == "_":
                self.regex = Token.all_token
            elif grammar_token == "_str_":
                self.regex = Token.str_token
            elif grammar_token == "_notstr_":
                self.regex = Token.not_str_token
            elif grammar_token[1] == "!":
                self.regex = re.compile("(?!%s$).*$" % grammar_token[2:-1], re.I)
            else:
                raise GrammarParsingError("Unknown token: %s" % grammar_token)

        elif grammar_token[0] in ("'", '"', '`'):
            self.regex = Token.LiteralMatcher(grammar_token[1:-1], grammar_token[0] == '`')

        elif grammar_token[0] in ('^', '$'):
            flags = (re.I if grammar_token[0] == '^' else 0)
            self.regex = re.compile(grammar_token[1:-1], flags)

        else:
            raise GrammarParsingError("Unknown token type: %s." % grammar_token)


    def __repr__(self):
        return self.regex.literal if isinstance(self.regex, Token.LiteralMatcher) else self.regex.pattern


    def match(self, string_tokens, idx):
        # If the index we're considering is beyond the end of our tokens, we have nothing to match on. Return False.
        if idx >= len(string_tokens):
            return False, None, None

        match = self.regex.match(string_tokens[idx])

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


    def match(self, string_tokens, idx):
        match, new_idx, _ = self.token.match(string_tokens, idx)

        if match:
            return True, new_idx, {self.name: string_tokens[idx]}

        return False, None, None

class ZeroOrOne(Grammar):

    name = '__ZeroOrOneNameSpace'

    def match(self, string_tokens, idx):
        # If the index we're considering is beyond the end of our tokens we have nothing to match on.  However, since
        # we can match Zero times, return True.  This allows gramars with trailing ZeroOrOne rules to match strings
        # which don't use them.
        if idx >= len(string_tokens):
            return True, idx, None

        _, new_idx, output = super(ZeroOrOne, self).match(string_tokens, idx)

        return True, new_idx or idx, (None if output is None else output[self.name])


class MoreDelimiter(Grammar):
    """
    Class which can be applied to a (* ) or (+ ) block to define a grammar which must be present between matches.
    """

    name = '__MoreDelimiterNameSpace'


class ZeroOrMore(Grammar):

    name = '__ZeroOrMoreNameSpace'
    delimiter_grammar = None
    match_count = 0 # Convenience attribute for implementing OneOrMore; reset on each call to match

    def _update_output_lists(self, dict_to_update_with, default_dict_to_update):
        for key in dict_to_update_with:
            default_dict_to_update[key].append(dict_to_update_with[key])


    def match(self, string_tokens, idx):
        self.match_count = 0
        outputs = collections.defaultdict(list)
        current_idx = idx

        while idx < len(string_tokens):
            current_idx = idx
            delimiter_output = None

            # If we're not processing the first match, check that any delimiter grammar we may have matches before
            # the next occurance of our grammar
            if self.match_count > 0 and self.delimiter_grammar is not None:
                match, idx, delimiter_output = self.delimiter_grammar.match(string_tokens, idx)

                if not match:
                    break

            match, idx, output = Grammar.match(self, string_tokens, idx)

            if not match or idx == current_idx:
                break

            current_idx = idx
            self.match_count += 1

            if output:
                self._update_output_lists(output[self.name], outputs)

            if delimiter_output:
                self._update_output_lists(delimiter_output[self.delimiter_grammar.name], outputs)

        return True, current_idx, dict(outputs) or None


class OneOrMore(ZeroOrMore):

    name = '__OneOrMoreNameSpace'

    def match(self, string_tokens, idx):
        _, new_idx, output = ZeroOrMore.match(self, string_tokens, idx)

        return self.match_count > 0, new_idx, output


class OneOfSet(Grammar):

    def match(self, string_tokens, idx):
        for grammar in self.tokens:
            match, new_idx, output = grammar.match(string_tokens, idx)
            if match:
                return True, new_idx, output
        return False, None, None
