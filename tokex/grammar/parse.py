"""
File containing utilities to parse a user-defined grammar string into a grammar tree
"""

import contextlib
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
        # ZeroOrOne Unnamed Grammar open
        r"\?\(",
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
    all_flags_re = re.compile("[%s]+" % "".join((getattr(flags, flag) for flag in flags.__all__)))
    escape_re = re.compile(r"\\(.)")

    for match in re.finditer(pattern, grammar_string, re.I):
        if match.groupdict().get('_nontoken_'):
            raise errors.UnknownGrammarTokenError(match.groupdict()['_nontoken_'], grammar_string, match.span())

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
                    raise errors.InvalidGrammarTokenFlagsError(invalid_flags, element, grammar_string, match.span())

        # Handle escapes in the token
        if matched_token[0] in elements.FIRST_CHAR_ESCAPES:
            matched_token = matched_token[0] + escape_re.sub(r"\1", matched_token[1:-1]) + matched_token[-1]

        matched_tokens.append({
            "match": match,
            "token": matched_token,
            "flags": token_flags
        })

    return matched_tokens


def construct_grammar(grammar_string, allow_sub_grammar_definitions=False, default_flags=flags.DEFAULTS):
    """
    Function which accepts a user-defined grammar string and returns an instance of Grammar representing it.

    Inputs: grammar_string - The user-defined grammar string representing the grammar we should construct.
            allow_sub_grammar_definitions - A boolean, indicating whether or not we should process sub grammars
                                            See the README for more information on what sub grammars are used for
                                            and the dangers of allowing them when parsing untrusted third-party grammars
            default_flags - Can be passed as a set of flags, which will set the defaults for all elements in the grammar

    Outputs: An instance of a Grammar class which can be used to parse input strings.
    """

    grammar_tokens = tokenize_grammar(grammar_string)

    # The grammar stack; opening tokens add a new item to the stack, closing tokens pop one off
    # Pre-populated with an outer-most grammar that will be returned from this function
    grammar_stack = [elements.Grammar(default_flags=default_flags)]

    # A stack of sub_grammars; used to handle nested sub_grammar definitions
    # We prepopulate it with an outer-most subgrammar to handle global sub-grammar definitions
    sub_grammar_stack = [elements.SubGrammarDefinition(default_flags=default_flags)]

    token_dict = None

    error_params = lambda: grammar_string, token_dict, grammar_stack
    sub_grammar_error_params = lambda: grammar_string, token_dict, sub_grammar_stack

    @contextlib.contextmanager
    def inject_parsing_context_into_errors():
        """ Injects information about the state of parsing into errors for better messages """

        try:
            yield

        except errors.TokexError as e:
            e.inject_stack(grammar_string, token_dict, grammar_stack, sub_grammar_stack)
            raise

    with inject_parsing_context_into_errors():
        for token_idx, token_dict in enumerate(grammar_tokens):
            token_match = token_dict["match"]
            token_flags = token_dict["flags"]
            token = token_dict["token"]

            # Openers
            if token == "{":
                element = elements.OneOfSet(token, token_flags, default_flags, token_dict)
                grammar_stack[-1].add_sub_element(element)
                grammar_stack.append(element)

            elif token[:2] == "*(":
                element = elements.ZeroOrMore(token, token_flags, default_flags, token_dict)
                grammar_stack[-1].add_sub_element(element)
                grammar_stack.append(element)

            elif token[:2] == "+(":
                element = elements.OneOrMore(token, token_flags, default_flags, token_dict)
                grammar_stack[-1].add_sub_element(element)
                grammar_stack.append(element)

            elif token[:2] == "?(":
                element = elements.ZeroOrOne(token, token_flags, default_flags, token_dict)
                grammar_stack[-1].add_sub_element(element)
                grammar_stack.append(element)

            elif token[0] == "(":
                element = elements.Grammar(token, token_flags, default_flags, token_dict)
                grammar_stack[-1].add_sub_element(element)
                grammar_stack.append(element)

            elif token[0] == "<":
                element = elements.NamedElement(token, token_flags, default_flags, token_dict)
                grammar_stack[-1].add_sub_element(element)
                grammar_stack.append(element)

            elif token[:3].lower() == "sep":
                element = elements.IteratorDelimiter(token, token_flags, default_flags, token_dict)
                if grammar_stack[-1].delimiter_grammar:
                    raise errors.DuplicateDelimiterError(grammar_stack[-1])

                if not getattr(grammar_stack[-1], "can_have_delimiter", False):
                    raise errors.InvalidDelimiterError(grammar_stack[-1])

                grammar_stack[-1].delimiter_grammar = element
                grammar_stack.append(element)

            # Closers
            elif token == "}":
                if isinstance(grammar_stack[-1],
                              (elements.SubGrammarDefinition, elements.IteratorDelimiter, elements.OneOfSet)):
                    if isinstance(grammar_stack[-1], elements.SubGrammarDefinition):
                        new_sub_grammar = sub_grammar_stack.pop()
                        sub_grammar_stack[-1].sub_grammars[new_sub_grammar.name] = new_sub_grammar

                    grammar_stack.pop()

                else:
                    raise errors.MismatchedBracketsError(token, grammar_stack[-1])

            elif token == ")":
                if isinstance(grammar_stack[-1],
                              (elements.ZeroOrMore, elements.ZeroOrOne, elements.OneOrMore, elements.Grammar)):
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
                grammar_stack[-1].add_sub_element(elements.StringLiteral(token, token_flags, default_flags, token_dict))

            elif token[0] == "~":
                grammar_stack[-1].add_sub_element(elements.RegexString(token, token_flags, default_flags, token_dict))

            elif token[0] in ("'", '"'):
                grammar_stack[-1].add_sub_element(elements.StringLiteral(token, token_flags, default_flags, token_dict))

            elif token == "$":
                grammar_stack[-1].add_sub_element(elements.Newline(token, token_flags, default_flags, token_dict))

            elif token == ".":
                grammar_stack[-1].add_sub_element(elements.AnyString(token, token_flags, default_flags, token_dict))

            # Sub Grammar open
            elif token[:3].lower() == "def":
                element = elements.SubGrammarDefinition(token, token_flags, default_flags, token_dict)

                if not allow_sub_grammar_definitions:
                    raise errors.SubGrammarsDisabledError(element.name)

                # Only allow definition of a new subgrammar within the global scope and other subgrammars
                for stack_element in grammar_stack[1:]:
                    if not isinstance(stack_element, elements.SubGrammarDefinition):
                        raise errors.SubGrammarScopeError(stack_element, element.name)

                element = elements.SubGrammarDefinition(token, token_flags, default_flags, token_dict)
                grammar_stack.append(element)
                sub_grammar_stack.append(element)

            # Sub Grammar Usage
            elif token[-1] == ")":
                # Find the referenced sub_grammar
                sub_grammar_name = elements.SubGrammarUsage(token, token_flags, default_flags, token_dict).name

                for parent_sub_grammar in reversed(sub_grammar_stack):
                    if sub_grammar_name in parent_sub_grammar.sub_grammars:
                        for sub_element in parent_sub_grammar.sub_grammars[sub_grammar_name].sub_elements:
                            grammar_stack[-1].add_sub_element(sub_element)

                        break

                else:
                    raise errors.UndefinedSubGrammarError(sub_grammar_name)

            else:
                raise errors.GrammarParsingError("Unknown token: %s" % repr(token))

            if not grammar_stack:
                raise errors.ExtraClosingBracketsError(token)

        if len(grammar_stack) > 1:
            raise errors.ExtraOpeningBracketsError(grammar_stack[-1].token_dict)

        return grammar_stack[0]
