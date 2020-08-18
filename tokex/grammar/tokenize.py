import re

from .. import errors
from . import elements


def tokenize_grammar(grammar_string):
    """
    Function which accepts a grammar string and returns an iterable of tokens
    """

    #pattern = "|".join((
    ###    r"@\s*[\w-]+?\s*:",  # Defined Sub Grammar open
    ###    r"@\s*[\w-]*?\s*@",  # Defined Sub Grammar close & Usage
    #    r"\{",               # One of Set open
    #    r"\}",               # One of Set close
    #    r"\[",               # Iterator Delimiter Open
    #    r"\]",               # Iterator Delimiter Close
    #    r"\(\*" ,            # Zero or More open
    #    r"\(\?",             # Zero or One open
    #    r"\(\+",             # One or More open
    #    r"\(\s*[\w-]+?\s*:", # Named Grammar open
    #    r"\)",               # Flow & Named Grammar close
    #    r"<\s*[\w-]+?\s*:",  # Named Token open
    #    r">",                # Named Token close
    ###    r"_!.*?(?<!\\)_",    # Not Token Regex
    ###    r"_notstr_",         # Not String Regex
    ###    r"_str_",            # String Regex
    ###    r"_",                # All Regex
    ###    r"\^.*?(?<!\\)\^",   # Regex
    ###    r"\$.*?(?<!\\)\$",   # Case Insensitive Regex
    ###    r"'.*?(?<!\\)'",     # Literal Token
    ###    r'".*?(?<!\\)"',     # Literal Token
    ###    r"`.*?(?<!\\)`",     # Case Insensitive Literal Token
    ###    r"\\n",               # Newline Token

    #))


    token_patterns = []
    for idx, element_token in enumerate(elements.element_tokens):
        flags = ""
        if element_token.flags:
            flags = "(?P<_%sf>[%s]+)?" % (idx, "".join(token.flags))
        token_patterns.append(r"(?:%s(?P<_%s>%s)" % (flags, idx, token.re_string))

    pattern = "|".join(token_patterns)

    # Special non-token-class tokens to match
    ] + [
        r"(?P<_comment_>#[^\n]*(\n|$))", # Comments
        r"(?P<_nontoken_>\S+)" # Final fallback - nontoken
    ])

    matched_tokens = []
    for match in re.finditer(pattern, grammar_string):
        if '_nontoken_' in match.groupdict():
            raise errors.UnknownGrammarTokenError(match.groupdict().get('_nontoken_'))

        elif '_comment_' in match.groupdict():
            continue

        # Get the token class which matched the grammar token
        matchdict = match.groupdict()
        matched_token = match.groupdict[match.lastgroup]
        matched_flags = matchdict.get(match.lastgroup + 'f')
        element_token = elements.element_tokens[int(match.lastgroup.strip("_"))]

        if matched_flags:
            matched_flags = list(matched_flags)
            for flag in matched_flags:
                if flag not in element_token.flags:
                    raise InvalidGrammarTokenFlagsError(flag, element_token["cls"])

        # Handle escapes in the token
        if element_token.escapes:
            for escape in element_token.escapes:
            matched_token = matched_token.replace(r"\%s" % escape, escape)

        matched_tokens.append({
            "token_str": matched_token,
            "flags": matched_flags,
            "element_token": element_token
        })

    return matched_tokens
