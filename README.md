# NOTE - THIS LIBRARY IS STILL IN DEVELOPMENT & NOT READY FOR USE

# SParse
A Python structured string parsing library allowing for parsing of complex strings into dictionaries and lists of tokens.

## Why SParse?
Admittedly, with a complex enough regex, Python's built-in `re` library will allow you to accomplish anything that you could accomplish using SParse.  However, SParse allows for a more readable definition of a grammar than re, which typically amounts to fewer bugs.  As well, SParse allows for grouping of related tokens in named subgrammars, and for subgrammars to be defined and re-used in a way reminiscent of BNF.

# Defining a Grammar.
Below is a BNF Grammar of an SParse compatible grammar, describing strings which it can parse.

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


#### Below is a detailed description of each type of token that can be used to create a SParse grammar:

    ###
    # Grammar Declarations
    ###

    @name: grammar @@ - Defines a sub grammar which can be later referenced in another grammar by using: @name@.
                        Notes:
                            * Defined sub grammars can be nested arbitrarily. Example:
                              `@grammarA: 'a' 'b' 'c' @@`
                              `@grammarB: 'd' @grammarA@ 'e' @grammarA@ @@`
                            * Defined sub grammars will be expanded when the grammar is compiled.  This, combined with
                              the ability to arbitrarily recurse defined sub grammars means that grammar compilation is
                              susceptible to the [Billion Laughs](https://en.wikipedia.org/wiki/Billion_laughs) attack.
                              Because of this, you should either not compile untrusted 3rd party grammars, or you should
                              disable sub grammar definition when compiling 3rd party grammars (see documentation below)
                            * @ is NOT a valid character in the name of a defined sub grammar. Example: @name@grammar:
                            * Defined sub grammars can occur anywhere within your grammar, however the act of defining a
                              sub grammar does not make any modifications to your grammar until it is used.  For example:
                              `'a' @sub: 'b' @@ 'c'` does not match 'a b c', but does match 'a c'
                              `'a' @sub: 'b' @@ @sub@ 'c'` matches 'a b c'
                            * Defined sub grammars cannot be applied until their declaration is finished.  For example,
                              while the following is valid:
                              `@a: 'a1' @b: 'b' @@ @b@ 'a2' @@` (Matches "a1 b a2")
                              the following is invalid:
                              `@a: 'a1' @b: @a@ @@ 'a2' @@` (@a@ cannot appear until the sub grammar 'a' is completed)


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

# Examples
