"""
File containing utilities to parse a user-defined grammar string into a grammar tree
"""

import re

from .. import errors
from . import elements
from . import flags

def tokenize_grammar(grammar_string):
    """ Function which accepts a grammar string and returns an iterable of tokens """

    # Function to create regex's for given flags
    flags_re_string = lambda f: "[%s]*" % "".join(f)

    name_re_str = elements.BaseScopedElement.name_re_str

    pattern = "|".join((
        # Defined Sub Grammar open
        r"def\s+%s\s*\{" % name_re_str,
        # Defined Sub Grammar usage
        r"%s\s*\(\s*\)" % name_re_str,
        # Iterator Delimiter Open
        r"sep\s*\{",
        # ZeroOrMore, OneOrMore, ZeroOrOne, and Named Grammar open
        r"[*+?]?\(\s*%s\s*:" % name_re_str,
        # Named Token open
        r"<\s*%s?\s*:" % name_re_str,
        # One of Set open
        r"\{",
        # All Regex
        r"%s\." % flags_re_string(elements.AnyString.valid_flags),
        # Regex
        r"%s~(?:[^\\~]*(?:\\.)*)*~" % flags_re_string(elements.RegexString.valid_flags),
        # Literal String
        #r"%s'.*?(?<!\\)'" % flags_re_string(elements.StringLiteral.valid_flags),
        r"%s'(?:[^\\']*(?:\\.)*)*'" % flags_re_string(elements.StringLiteral.valid_flags),
        # Literal String
        #r'%s".*?(?<!\\)"' % flags_re_string(elements.StringLiteral.valid_flags),
        r'%s"(?:[^\\"]*(?:\\.)*)*"' % flags_re_string(elements.StringLiteral.valid_flags),
        # Newline Token
        r"\$",

        # Closers
        # Named Token close
        r">",
        # Flow & Named Grammar close
        r"\)",
        # Sub Grammar, Iterator Delimiter, & One of Set close
        r"\}",

        # Special non-token-class tokens to match
        # Comments
        r"(?P<_comment_>#[^\n]*(\n|$))",
        # Final fallback - nontoken
        r"(?P<_nontoken_>\S+)"
    ))

    matched_tokens = []
    all_flags_re = re.compile("[%s]+" % "".join(flags.__all__))
    escape_re = re.compile(r"\\(.)")

    for match in re.finditer(pattern, grammar_string, re.I):
        if match.groupdict().get('_nontoken_'):
            raise errors.UnknownGrammarTokenError(match.groupdict().get('_nontoken_'))

        elif match.groupdict().get('_comment_'):
            continue

        matched_token = match.group()

        # Check for flags on the token
        token_flags = None
        if matched_token[:3].lower() not in ("def", "sep") and matched_token[:-2] != "()":
            token_flags = all_flags_re.match(matched_token)
            if token_flags:
                token_flags = set(token_flags.group())
                matched_token = matched_token[len(token_flags):]

                # Ensure the flags set on the element are valid
                element = elements.FIRST_CHAR_VALID_FLAGS[matched_token[0]]
                invalid_flags = token_flags.difference(element.valid_flags)
                if invalid_flags:
                    raise errors.InvalidGrammarTokenFlagsError(invalid_flags, element)

        # Handle escapes in the token
        if matched_token[0] in elements.FIRST_CHAR_ESCAPES:
            matched_token = matched_token[0] + escape_re.sub(r"\1", matched_token[1:-1]) + matched_token[-1]

        matched_tokens.append({
            "token": matched_token,
            "flags": token_flags
        })

    return matched_tokens


def construct_grammar(grammar_string, allow_sub_grammar_definitions=False, default_flags=flags.DEFAULTS):
    """
    Function which accepts a user-defined grammar string and returns an instance of Grammar representing it.

    Inputs: grammar_string                - The user-defined grammar string representing the grammar we should construct.
            allow_sub_grammar_definitions - A boolean, indicating whether or not we should process sub grammars
                                            See the README for more information on what sub grammars are used for
                                            and the dangers of allowing them when parsing untrusted third-party grammars.
            default_flags                 - Can be passed as a set of flags, which will set the defaults for all elements in the grammar

    Outputs: An instance of a Grammar class which can be used to parse input strings.
    """

    grammar_tokens = tokenize_grammar(grammar_string)

    # The grammar stack; opening tokens add a new item to the stack, closing tokens pop one off
    # Pre-populated with an outer-most grammar that will be returned from this function
    grammar_stack = [elements.Grammar(default_flags=default_flags)]

    # A stack of sub_grammars; used to handle nested sub_grammar definitions
    # We prepopulate it with an outer-most subgrammar to handle global sub-grammar definitions
    sub_grammar_stack = [elements.SubGrammarDefinition(default_flags=default_flags)]

    for token_idx, token_dict in enumerate(grammar_tokens):
        if not len(grammar_stack):
            raise errors.MismatchedBracketsError(grammar_tokens[token_idx - 1])

        flags = token_dict["flags"]
        token = token_dict["token"]

        # Openers
        if token == "{":
            element = elements.OneOfSet(token, flags, default_flags)
            grammar_stack[-1].add_sub_element(element)
            grammar_stack.append(element)

        elif token[:2] == "*(":
            element = elements.ZeroOrMore(token, flags, default_flags)
            grammar_stack[-1].add_sub_element(element)
            grammar_stack.append(element)

        elif token[:2] == "+(":
            element = elements.OneOrMore(token, flags, default_flags)
            grammar_stack[-1].add_sub_element(element)
            grammar_stack.append(element)

        elif token[:2] == "?(":
            element = elements.ZeroOrOne(token, flags, default_flags)
            grammar_stack[-1].add_sub_element(element)
            grammar_stack.append(element)

        elif token[0] == "(":
            element = elements.Grammar(token, flags, default_flags)
            grammar_stack[-1].add_sub_element(element)
            grammar_stack.append(element)

        elif token[0] == "<":
            element = elements.NamedElement(token, flags, default_flags)
            grammar_stack[-1].add_sub_element(element)
            grammar_stack.append(element)

        elif token[:3].lower() == "sep":
            element = elements.IteratorDelimiter(token, flags, default_flags)
            if grammar_stack[-1].delimiter_grammar:
                raise errors.GrammarParsingError("Multiple %r defined for %r" % (element, grammar_stack[-1]))

            if not getattr(grammar_stack[-1], "can_have_delimiter", False):
                raise errors.GrammarParsingError("Cannot add iterator delimiter to %r" % grammar_stack[-1])

            grammar_stack[-1].delimiter_grammar = element
            grammar_stack.append(element)

        # Closers
        elif token == "}":
            if isinstance(grammar_stack[-1], (elements.SubGrammarDefinition, elements.IteratorDelimiter, elements.OneOfSet)):
                if isinstance(grammar_stack[-1], elements.SubGrammarDefinition):
                    new_sub_grammar = sub_grammar_stack.pop()
                    sub_grammar_stack[-1].sub_grammars[new_sub_grammar.name] = new_sub_grammar

                grammar_stack.pop()

            else:
                raise errors.MismatchedBracketsError(token, grammar_stack[-1])

        elif token == ")":
            if isinstance(grammar_stack[-1], (elements.ZeroOrMore, elements.ZeroOrOne, elements.OneOrMore, elements.Grammar)):
                grammar_stack.pop()

            else:
                raise errors.MismatchedBracketsError(token, grammar_stack[-1])

        elif token == ">":
            if isinstance(grammar_stack[-1], (elements.NamedElement)):
                grammar_stack.pop()

            else:
                raise errors.MismatchedBracketsError(token, grammar_stack[-1])

        # Singular tokens
        elif token[0] in ("'", '"'):
            grammar_stack[-1].add_sub_element(elements.StringLiteral(token, flags, default_flags))

        elif token[0] == "~":
            grammar_stack[-1].add_sub_element(elements.RegexString(token, flags, default_flags))

        elif token[0] in ("'", '"'):
            grammar_stack[-1].add_sub_element(elements.StringLiteral(token, flags, default_flags))

        elif token == "$":
            grammar_stack[-1].add_sub_element(elements.Newline(token, flags, default_flags))

        elif token == ".":
            grammar_stack[-1].add_sub_element(elements.AnyString(token, flags, default_flags))

        # Sub Grammar open
        elif token[:3].lower() == "def":
            if not allow_sub_grammar_definitions:
                raise errors.SubGrammarError("Cannot define a Sub-grammar when allow_sub_grammar_definitions is False")

            # Only allow definition of a new subgrammar within the global scope and other subgrammars
            for element in grammar_stack[1:]:
                if not isinstance(element, elements.SubGrammarDefinition):
                    raise errors.SubGrammarError("Sub grammars cannot be defined within a %r element" % element)

            element = elements.SubGrammarDefinition(token, flags, default_flags)
            grammar_stack.append(element)
            sub_grammar_stack.append(element)

        # Sub Grammar Usage
        elif token[-1] == ")":
            # Find the referenced sub_grammar
            sub_grammar_name = elements.SubGrammarUsage(token, flags, default_flags).name

            for parent_sub_grammar in reversed(sub_grammar_stack):
                if sub_grammar_name in parent_sub_grammar.sub_grammars:
                    for sub_element in parent_sub_grammar.sub_grammars[sub_grammar_name].sub_elements:
                        grammar_stack[-1].add_sub_element(sub_element)

                    break

            else:
                raise errors.SubGrammarError("Cannot find named sub grammar: %s" % sub_grammar_name)


        else:
            raise errors.GrammarParsingError("Unknown token: %s" % repr(token))

        if len(grammar_stack) == 0:
            raise errors.MismatchedBracketsError(token)

    if len(grammar_stack) > 1:
        raise errors.MismatchedBracketsError(grammar_stack[-1].token_str)

    return grammar_stack[0]


###
# Utility functions
###

#def _process_sub_grammar_definitions(grammar_tokens):
#    """
#    Function which expands subgrammar definitions into the grammar string.
#
#    Inputs: grammar_tokens - A list of tokens in the grammar
#
#    Outputs: A list of tokens in the grammar, after having expanded user defined grammar tokens.
#    """
#
#    # List of tokens after expanding defined sub grammars
#    parsed_grammar_tokens = []
#
#    # Dictionary mapping sub grammar names to tokens they contain
#    # Note: None is being used here to refer to the global namespace, ie the main list of tokens.
#    #       so we map it here to parsed_grammar_tokens
#    sub_grammars = collections.defaultdict(list, {None: parsed_grammar_tokens})
#
#    # Dictionary for determining the scope of a sub grammar declaration.
#    # Maps the name of a sub grammar to a list of sub grammar names within its scope.
#    sub_grammar_name_spaces = collections.defaultdict(list)
#
#    # Stack of sub grammar names to record the current grammar being constructed.
#    sub_grammar_stack = [None] # Use None to record the topmost, global namespace
#
#    for token in grammar_tokens:
#        # Handle new defined sub grammar declarations
#        if token[0] == '@' and token[-1] == ':':
#            sub_grammar_name = token[1:-1].strip()
#            if sub_grammar_name in sub_grammars or sub_grammar_name in sub_grammar_stack:
#                raise GrammarParsingError("Redeclaration of defined sub grammar: %s" % sub_grammar_name)
#
#            sub_grammar_stack.append(sub_grammar_name)
#
#        # Handle the closing of sub grammar declarations
#        elif token == '@@':
#            if sub_grammar_stack[-1] is None:
#                raise GrammarParsingError("Unexpected @@; not currently defining a sub grammar.")
#
#            closed_grammar = sub_grammar_stack.pop()
#
#            # Remove any sub grammars defined within the recently closed grammar's scope
#            if closed_grammar in sub_grammar_name_spaces:
#                for sub_grammar_name in sub_grammar_name_spaces.pop(closed_grammar):
#                    sub_grammars.pop(sub_grammar_name)
#
#            # Add the newly closed sub grammar to its parents namespace
#            sub_grammar_name_spaces[sub_grammar_stack[-1]].append(closed_grammar)
#
#            # Edge case; empty sub grammar has been saved, add a key to our defaultdict so it can be later used
#            if closed_grammar not in sub_grammars:
#                sub_grammars[closed_grammar] # sub_grammars is a defaultdict so accessing the key adds it
#
#        # Handle inserting a sub grammar
#        elif token[0] == '@' and token[-1] == '@':
#            sub_grammar_name = token[1:-1].strip()
#
#            if sub_grammar_name not in sub_grammars:
#                # Give a slightly more descriptive error message if we've seen a declaration for this sub grammar before
#                if sub_grammar_name in sub_grammar_stack:
#                    raise GrammarParsingError("Cannot apply %s; %s is not yet fully defined." % (token, sub_grammar_name))
#
#                raise GrammarParsingError("Unknown sub grammar: %s" % sub_grammar_name)
#
#            # Apply the sub grammar to the most recent sub grammar (or topmost grammar)
#            sub_grammars[sub_grammar_stack[-1]].extend(sub_grammars[sub_grammar_name])
#
#        # Handle adding tokens to a defined sub grammar (or topmost grammar)
#        else:
#            sub_grammars[sub_grammar_stack[-1]].append(token)
#
#    if sub_grammar_stack[-1] is not None:
#        raise GrammarParsingError("Unclosed defined sub grammar: %s" % sub_grammar_stack[-1])
#
#    return parsed_grammar_tokens
#
#
#def construct_grammar(grammar_string, allow_sub_grammar_definitions=True):
#    """
#    Function which accepts a user-defined grammar string and returns an instance of Grammar representing it.
#
#    Inputs: grammar_string                - The user-defined grammar string representing the grammar we should construct.
#            allow_sub_grammar_definitions - A boolean, indicating whether or not we should process user defined sub grammars.
#    """
#
#    stack_open_dict = {
#        "{": OneOfSet,
#        "(?": ZeroOrOne,
#        "(*": ZeroOrMore,
#        "(+": OneOrMore,
#    }
#
#    stack_naming_open_dict = {
#        "<": NamedToken,
#        "(": Grammar,
#    }
#
#    stack_close_dict = {
#        "}": OneOfSet,
#        ")": (ZeroOrOne, ZeroOrMore, OneOrMore, Grammar),
#        ">": NamedToken,
#        "]": MoreDelimiter,
#    }
#
#    grammar = Grammar()
#    grammar_stack = [grammar]
#
#    grammar_tokens = _tokenize_grammar(grammar_string)
#
#    if allow_sub_grammar_definitions:
#        grammar_tokens = _process_sub_grammar_definitions(grammar_tokens)
#
#    for token in grammar_tokens:
#        if not len(grammar_stack):
#            raise GrammarParsingError("Too many closing brackets; grammar stack empty while still tokens remaining.")
#
#        # Stack-modifying open tokens
#        if token in stack_open_dict:
#            obj = stack_open_dict[token]()
#            grammar_stack[-1].append(obj)
#            grammar_stack.append(obj)
#
#        # Closing tokens
#        elif token in stack_close_dict:
#            if not isinstance(grammar_stack[-1], stack_close_dict[token]):
#                error = "Cannot Close %s, most recent: %s, not %s" % (token, grammar_stack[-1], stack_close_dict[token])
#                raise GrammarParsingError(error)
#
#            grammar_stack.pop()
#
#        # Named tokens & grammars
#        elif token[0] in stack_naming_open_dict and token[-1] == ":":
#            obj = stack_naming_open_dict[token[0]]()
#            obj.name = token[1:-1].strip()
#            grammar_stack[-1].append(obj)
#            grammar_stack.append(obj)
#
#        # Singlular tokens
#        elif token[0] in ("'", '"', '`', '^', '$', '_') or token in (r'\n',):
#            grammar_stack[-1].append(Token(token))
#
#        # Iterator delimiters
#        elif token == "[":
#            # Ensure that the token preceeding us is a OneOrMore or a ZeroOrMore
#            if not isinstance(grammar_stack[-1], (ZeroOrMore, OneOrMore)):
#                error = "Iteration delimiter must be applied to a (* ) or (+ ) block, not %s" % grammar_stack[-1]
#                raise GrammarParsingError(error)
#
#            obj = MoreDelimiter()
#            grammar_stack[-1].delimiter_grammar = obj
#            grammar_stack.append(obj)
#
#        else:
#            raise GrammarParsingError("Unknown token: %s" % repr(token))
#
#    if len(grammar_stack) != 1:
#        raise GrammarParsingError("Too few closing brackets; grammar stack length: %s when all tokens processed." %
#                                   len(grammar_stack))
#
#    return grammar

###
# User-defined grammar constructs
###

#class _TokexGrammar:
#
#    def __init__(self, *args, **kwargs):
#        self.match = self._match_wrapper(self.match)
#
#
#    def _match_wrapper(self, match_function):
#        """
#        Function wrapper which takes a match function and wraps it in another function to perform additional
#        functionality when matching.
#        """
#
#        @functools.wraps(match_function)
#        def match_wrapper(string_tokens, idx):
#            if logging.getLogger().isEnabledFor(logging.DEBUG) and idx < len(string_tokens):
#                logging.debug("Current Token: %s\n\nMATCHING: %s\n" % (self, string_tokens[idx]))
#
#            match, idx, output = match_function(string_tokens, idx)
#
#            if logging.getLogger().isEnabledFor(logging.DEBUG) and idx < len(string_tokens):
#                logging.debug("Matched: %s\n" % match)
#
#            return match, idx, output
#
#        return match_wrapper
#
#
#    def match(self, string_tokens, idx):
#        """
#        Function which accepts an iterable of tokens and a current index and determines whether or not this construct
#        matches the list at the current position. Should be overridden in subclasses.
#
#        Inputs: string_tokens - An iterable of string tokens to determine if we match upon.
#                idx          - The start index within the string_tokens to begin processing at.
#
#        Outputs: A triple containing: {
#            match: A boolean depicting whether or not this construct matches the iterable at the current position.
#            new_idx: The index this construct ceased matching upon the iterable, if match is True. Else None
#            output: If there are any named matches within this construct, a dictionary or list.  Else None
#        )
#        """
#
#        raise NotImplementedError
#
#
#class Grammar(_TokexGrammar):
#    """
#    Grammar class representing a user-defined grammar.  Can contain further instances of itself within its language.
#
#    An instance of this class is expected as a parameter when initializing instances of utils.string_parser.StringParser.
#    """
#
#    name = None
#    tokens = None
#
#    def __init__(self):
#        _TokexGrammar.__init__(self)
#        self.tokens = list()
#
#
#    def __repr__(self):
#        return "<%s: %s>" % (self.__class__.__name__, [repr(t) for t in self.tokens])
#
#
#    def append(self, item):
#        self.tokens.append(item)
#
#
#    def match(self, string_tokens, idx):
#        return_dict = dict()
#        for item in self.tokens:
#            match, idx, output = item.match(string_tokens, idx)
#
#            if not match:
#                return False, None, None
#
#            if isinstance(output, dict):
#                return_dict.update(output)
#
#        return True, idx, {self.name: return_dict}
#
#
#class Token(_TokexGrammar):
#    """
#    Token class representing one of the various types of tokens that can be present in a user-defined grammar.
#    """
#
#    # Built-in regex's
#    all_token = re.compile(r".+$")
#    str_token = re.compile(r"([\"'])(\\\1|[^\1])*\1$")
#    not_str_token = re.compile(r"[^\"']*$")
#    newline_token = re.compile(r"\n")
#
#    regex = None
#
#    class LiteralMatcher:
#        literal = None
#        case_sensitive = False
#
#        def __init__(self, literal, case_sensitive=0):
#            self.literal = literal
#            self.case_sensitive = case_sensitive
#
#
#        def match(self, token):
#            return self.literal == token if self.case_sensitive else self.literal.lower() == token.lower()
#
#
#    def __init__(self, grammar_token):
#        _TokexGrammar.__init__(self)
#
#        if grammar_token[0] != grammar_token[-1]:
#            raise GrammarParsingError("Token must start and end with the same character: %s" % grammar_token)
#
#
#        if grammar_token[0] == "_":
#            if grammar_token == "_":
#                self.regex = Token.all_token
#            elif grammar_token == r"\n":
#                self.regex = Token.newline_token
#            elif grammar_token == "_str_":
#                self.regex = Token.str_token
#            elif grammar_token == "_notstr_":
#                self.regex = Token.not_str_token
#            elif grammar_token[1] == "!":
#                self.regex = re.compile("(?!%s$).*$" % grammar_token[2:-1], re.I)
#            else:
#                raise GrammarParsingError("Unknown token: %s" % grammar_token)
#
#        elif grammar_token[0] in ("'", '"', '`'):
#            self.regex = Token.LiteralMatcher(grammar_token[1:-1], grammar_token[0] == '`')
#
#        elif grammar_token[0] in ('^', '$'):
#            flags = (re.I if grammar_token[0] == '^' else 0)
#            self.regex = re.compile(grammar_token[1:-1], flags)
#
#        else:
#            raise GrammarParsingError("Unknown token type: %s." % grammar_token)
#
#
#    def __repr__(self):
#        return self.regex.literal if isinstance(self.regex, Token.LiteralMatcher) else self.regex.pattern
#
#
#    def match(self, string_tokens, idx):
#        # If the index we're considering is beyond the end of our tokens, we have nothing to match on. Return False.
#        if idx >= len(string_tokens):
#            return False, None, None
#
#        match = self.regex.match(string_tokens[idx])
#
#        if match:
#            return True, idx + 1, None
#
#        return False, None, None
#
#
#class NamedToken(_TokexGrammar):
#    name = None
#    token = None
#
#    def __repr__(self):
#        return "<NamedToken: %s>" % repr(self.token)
#
#    def append(self, item):
#        if self.token is not None:
#            raise GrammarParsingError("Cannot append %s to NamedToken, already have token: %s" % (item, self.token))
#        self.token = item
#
#
#    def match(self, string_tokens, idx):
#        match, new_idx, _ = self.token.match(string_tokens, idx)
#
#        if match:
#            return True, new_idx, {self.name: string_tokens[idx]}
#
#        return False, None, None
#
#class ZeroOrOne(Grammar):
#
#    name = '__ZeroOrOneNameSpace'
#
#    def match(self, string_tokens, idx):
#        # If the index we're considering is beyond the end of our tokens we have nothing to match on.  However, since
#        # we can match Zero times, return True.  This allows gramars with trailing ZeroOrOne rules to match strings
#        # which don't use them.
#        if idx >= len(string_tokens):
#            return True, idx, None
#
#        _, new_idx, output = super(ZeroOrOne, self).match(string_tokens, idx)
#
#        return True, new_idx or idx, (None if output is None else output[self.name])
#
#
#class MoreDelimiter(Grammar):
#    """
#    Class which can be applied to a (* ) or (+ ) block to define a grammar which must be present between matches.
#    """
#
#    name = '__MoreDelimiterNameSpace'
#
#
#class ZeroOrMore(Grammar):
#
#    name = '__ZeroOrMoreNameSpace'
#    delimiter_grammar = None
#    match_count = 0 # Convenience attribute for implementing OneOrMore; reset on each call to match
#
#    def _update_output_lists(self, dict_to_update_with, default_dict_to_update):
#        for key in dict_to_update_with:
#            default_dict_to_update[key].append(dict_to_update_with[key])
#
#
#    def match(self, string_tokens, idx):
#        self.match_count = 0
#        outputs = collections.defaultdict(list)
#        urrent_idx = idx
#
#        while idx < len(string_tokens):
#            current_idx = idx
#            delimiter_output = None
#
#            # If we're not processing the first match, check that any delimiter grammar we may have matches before
#            # the next occurance of our grammar
#            if self.match_count > 0 and self.delimiter_grammar is not None:
#                match, idx, delimiter_output = self.delimiter_grammar.match(string_tokens, idx)
#
#                if not match:
#                    break
#
#            match, idx, output = Grammar.match(self, string_tokens, idx)
#
#            if not match or idx == current_idx:
#                break
#
#            current_idx = idx
#            self.match_count += 1
#
#            if output:
#                self._update_output_lists(output[self.name], outputs)
#
#            if delimiter_output:
#                self._update_output_lists(delimiter_output[self.delimiter_grammar.name], outputs)
#
#        return True, current_idx, dict(outputs) or None
#
#
#class OneOrMore(ZeroOrMore):
#
#    name = '__OneOrMoreNameSpace'
#
#    def match(self, string_tokens, idx):
#        _, new_idx, output = ZeroOrMore.match(self, string_tokens, idx)
#
#        return self.match_count > 0, new_idx, output
#
#
#class OneOfSet(Grammar):
#
#    def match(self, string_tokens, idx):
#        for grammar in self.tokens:
#            match, new_idx, output = grammar.match(string_tokens, idx)
#            if match:
#                return True, new_idx, output
#        return False, None, None
