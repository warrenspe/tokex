import textwrap

from . import utils



class TokexError(Exception):
    """ Base class for all tokex-specific errors """

    grammar_string = None
    match_span_start = None
    match_span_end = None
    grammar_stack = None
    sub_grammar_stack = None

    def grammar_string_error_context(self):
        """ Returns a string showing context around where an error occurred """

        if None in [self.grammar_string, self.match_span_start, self.match_span_end]:
            return ""

        # Create a grammar snippet showing the text around the error
        start_of_line = self.grammar_string.rfind("\n", 0, self.match_span_start) + 1 # Inclusive - first char of line
        if start_of_line == -1:
            start_of_line = 0
        end_of_line = self.grammar_string.find("\n", self.match_span_end) # Exclusive, line ends at this - 1
        if end_of_line == -1:
            end_of_line = len(self.grammar_string)

        # We will only show at most 50 characters before/after the match_span
        grammar_snippet_start = max(self.match_span_start - 50, start_of_line)
        grammar_snippet_end = min(self.match_span_end + 50, end_of_line)
        grammar_snippet = self.grammar_string[grammar_snippet_start: grammar_snippet_end]

        # Get the line number/column number of the line in question
        line_num = self.grammar_string.count("\n", 0, self.match_span_start) + 1
        col_num = self.match_span_start - grammar_snippet_start + 1

        # Create a string like "    ^^^" showing where in the line the error is
        justified_caret = "".join((
            " " * (col_num - 1),
            "^" * (self.match_span_end - self.match_span_start)
        ))

        return textwrap.dedent("""
            Line %s Column %s
            %s
            %s
        """).strip() % (
            line_num,
            col_num,
            grammar_snippet,
            justified_caret
        )

    def __str__(self):
        return repr(self)


###
# Tokenizing errors
###

class GrammarTokenizingError(TokexError):
    """ Base class for errors which occur while tokenizing an input tokex grammar """

    def __init__(self, err_msg, grammar_string, match_span):
        self.err_msg = err_msg
        self.grammar_string = grammar_string
        self.match_span_start, self.match_span_end = match_span

    def __repr__(self):
        return textwrap.dedent("""
            Error encountered while tokenizing tokex grammar:
            %s
            %s
        """).strip() % (
            self.err_msg,
            self.grammar_string_error_context()
        )


class UnknownGrammarTokenError(GrammarTokenizingError):
    """ Error thrown when we are unable to tokenize a user-defined grammar. """

    def __init__(self, token, *args):
        err_msg = "Encountered unknown grammar token: %s" % token
        super(UnknownGrammarTokenError, self).__init__(err_msg, *args)


###
# Grammar Parsing (Element Tree construction time) errors
###

class GrammarParsingError(TokexError):
    """ Base class for errors which occur while parsing an input tokex grammar """

    tree_type = "Element"

    def __init__(self, err_msg):
        self.err_msg = err_msg

    def __repr__(self):
        grammar_tree_at_error = self.get_tree()
        tree_at_error_string = "%s Tree at the time of error:" % self.tree_type if grammar_tree_at_error else ""

        return "\n".join(filter(None, [
            "Error encountered while constructing tokex element tree: %s" % self.err_msg,
            self.grammar_string_error_context(),
            tree_at_error_string,
            grammar_tree_at_error
        ]))

    def inject_stack(self, grammar_string, token_dict, grammar_stack, sub_grammar_stack):
        self.grammar_string = grammar_string
        self.match_span_start, self.match_span_end = token_dict["match"].span()
        self.grammar_stack = grammar_stack
        self.sub_grammar_stack = sub_grammar_stack

    def get_tree(self):
        return utils.format_element_tree(self.grammar_stack[0]) if self.grammar_stack else ""


class InvalidGrammarTokenFlagsError(GrammarParsingError):
    """ Error thrown when a grammar token in a user-defined grammar has an invalid flag """

    def __init__(self, invalid_flags, element):
        add_s = "s" if len(invalid_flags) > 1 else ""
        err_msg = "Invalid flag%s %s given to %r, valid flags are: %s" % (
            add_s,
            ", ".join(sorted(invalid_flags)),
            element,
            ", ".join(sorted(element.valid_flags)) if element.valid_flags else None
        )
        super(InvalidGrammarTokenFlagsError, self).__init__(err_msg)


class InvalidRegexError(GrammarParsingError):
    """ Error thrown when an invalid regular expression is given to a RegexString element """

    def __init__(self, regex):
        err_msg = "Invalid regular expression given: %s" % regex
        super(InvalidRegexError, self).__init__(err_msg)


class MutuallyExclusiveGrammarTokenFlagsError(GrammarParsingError):
    """ Error thrown when a grammar token in a user-defined grammar is given mutually exclusive flags """

    def __init__(self, element, invalid_flags):
        err_msg = "Mutually exclusive flags given to %r: %s" % (
            element,
            ", ".join(sorted(invalid_flags)),
        )
        super(MutuallyExclusiveGrammarTokenFlagsError, self).__init__(err_msg)


class InvalidDelimiterError(GrammarParsingError):
    """ Error thrown when a scoped grammar which cannot have a delimiter is given a delimiter """

    def __init__(self, element):
        err_msg = "Cannot add iterator delimiters to %r" % element
        super(InvalidDelimiterError, self).__init__(err_msg)


class DuplicateDelimiterError(GrammarParsingError):
    """ Error thrown when a scoped grammar is given more than one delimiter """

    def __init__(self, element):
        err_msg = "Multiple iterator delimiters defined for %r" % element
        super(DuplicateDelimiterError, self).__init__(err_msg)


class ExtraClosingBracketsError(GrammarParsingError):
    """ Error thrown when extra mismatched closing brackets are given that do not have associated opening brackets """

    def __init__(self, token):
        err_msg = "Extra closing brackets given; found an extra: %s" % token
        super(ExtraClosingBracketsError, self).__init__(err_msg)


class ExtraOpeningBracketsError(GrammarParsingError):
    """ Error thrown when extra mismatched opening brackets are given that do not have associated closing brackets """

    def __init__(self, element):
        err_msg = "Extra opening brackets given; %r was not closed" % element
        super(ExtraOpeningBracketsError, self).__init__(err_msg)
        self.match_span_start, self.match_span_end = element.token_dict["match"].span()

    def inject_stack(self, grammar_string, token_dict, grammar_stack, sub_grammar_stack):
        """ Override so that we use the token dict which opened the extra scope, rather than the last token dict of the grammar """

        self.grammar_string = grammar_string
        self.grammar_stack = grammar_stack
        self.sub_grammar_stack = self.sub_grammar_stack


class MismatchedBracketsError(GrammarParsingError):
    """ Error thrown when mismatching opening/closing brackets are given for a given element """

    def __init__(self, token, last_scope):
        err_msg = "Mismatched brackets given; got: %s, expecting closing brackets for: %s" % (
            token,
            last_scope
        )
        super(MismatchedBracketsError, self).__init__(err_msg)


class NamedElementContentsError(GrammarParsingError):
    """ Error thrown when invalid contents are given to a Named Element """


###
# Sub Grammar Errors
###

class SubGrammarError(GrammarParsingError):
    """ Base class for sub grammar related errors raised while processing a tokex grammar """

    tree_type = "Sub Grammar"

    def get_tree(self):
        return utils.format_subgrammar_tree(self.sub_grammar_stack[0]) if self.sub_grammar_stack else ""


class SubGrammarsDisabledError(SubGrammarError):
    """ Raised when a sub grammar is defined while allow_sub_grammar_definitions is False """

    def __init__(self, name):
        err_msg = "Cannot define sub grammar %s while allow_sub_grammar_definitions is False" % name
        super(SubGrammarsDisabledError, self).__init__(err_msg)


class SubGrammarScopeError(SubGrammarError):
    """ Raised when a sub grammar is defined outside of the global scope or another sub grammar element """

    def __init__(self, scope_element, name):
        err_msg = textwrap.dedent("""
            Error defining sub grammar %s. Sub Grammars can only be defined globally or within other sub grammars, not inside a: %s
        """).strip() % (name, scope_element)
        super(SubGrammarScopeError, self).__init__(err_msg)


class UndefinedSubGrammarError(SubGrammarError):
    """ Raised when an undefined sub grammar is used """

    def __init__(self, name):
        err_msg = "Sub grammar %s does not exist" % name
        super(UndefinedSubGrammarError, self).__init__(err_msg)
