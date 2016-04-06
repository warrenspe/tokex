# SParse
Python structured string parsing library.

# Defining a Grammar.
Below is a BNF Grammar of an SParse compatible grammar, describing strings which can be parsed by SParse.

grammar ::= <statement> | <statement> <grammar>
statement ::= <token> | <name-quantifier> | <flow-quantifier>

name-quantifier ::= <named-token> | <named-grammar>
named-token ::= "<" <name> ": " <token> ">"
named-grammar ::= "(" <name> ": " <grammar> ")"

flow-quantifier ::= <zero-or-one> | <zero-or-more> | <one-of-set>
zero-or-one ::= "[[" <grammar> "]]"
zero-or-more ::= "((" <grammar> "))"
one-of-set ::= "{{" <grammar> "}}"

token ::= <literal> | <literal-case-insensitive> | <regex> | <all> | <str> | <not-str> | <not-token>


# Below is a detailed description of each type of token that can be used to create a SParse grammar:

    ###
    # Tokens
    ###

    'Literal Token' - Must match an input token.
    "Literal Token" - Must match an input token.
    `Literal Token` - Must match an input token (case sensitive).

    ^Regular Expr^  - Matches a token if its python regular expression matches it.
    $Regular Expr$  - Matches a token if its python regular expression matches it (case insensitive).

    # Convenience Regular Expressions (case insensitive)

    _               - Matches any token (Short for $.+$)

    _str_           - Matches any token, as long as it is a literal string (begins and ends with " or ')

    _notstr_        - Matches any token, except literal strings (begins or ends with " or ')

    _!..._          - Matches any token EXCEPT the one passed.  Example: _!from_


    NOTE: to escape ', ", `, ^, $, _ within '...', "...", `...`, ^...^, $...^, _!..._
          respectively, use a \ - Example: _!one\_up_


    ###
    # Naming
    ###

    <name: token>   - Named Match. Usage: <attribute-name: token-to-match>.
                      Tokens matched using a named match will have the matched token recorded in the nearest grammar.
                      See named grammars below.  Examples: <colName: _> <innerJoin: "inner">

    (name: ...)     - Named Grammar. After parsing, each named grammar will equate to a dictionary, with all named
                      matches made within it being recorded as key: value pairs, name: matched-token.
                      To match a string, it must be able to successfully match all of the tokens it contains. If it
                      cannot match a token, no match is made. Example: (test: 'a' 'b' 'c')
                      Matches: "a b c"
                      Does not match: "a b"

    ###
    # Flow
    ###

    [[...]]         - Specifies zero or one matches of the grammar it wraps.

    ((...))         - Specifies zero or more matches of the grammar it wraps.  Named grammars & named tokens wrapped by
                      Zero Or More brakets will returned as a list of dictionaries.  Named token matches outside of a
                      named grammar will be grouped into a list, while matches inside a named grammar will be grouped
                      into a dictionary.
                      Example: [[<a: 'a'> (b: <c: 'c'> <d: 'd'>)]]  <- 'a c d a c d'
                      => {
                             'a': ['a', 'a'],
                             'b': [{'c': 'c', 'd': 'd'}, {'c': 'c', 'd': 'd'}]
                         }

    {{...}}         - Specifies one grammar of the set.  Will attempt to match each grammar it contains with the string
                      until one matches in its entirety.
