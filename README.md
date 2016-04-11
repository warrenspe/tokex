# SParse
A Python structured string parsing library allowing for parsing of complex strings into dictionaries and lists of tokens.

## Why SParse?
Admittedly, with a complex enough regex, Python's built-in [re](https://docs.python.org/3.6/library/re.html) library will allow you to accomplish anything that you could accomplish using SParse.  However, SParse allows for a more spaced out, readable definition of a grammar than re, which typically leads to fewer bugs.  As well, SParse allows for grouping of related tokens in named sub grammars, which can significantly cut down on the overall size of the grammar, and for sub grammars to be defined and re-used in a way reminiscent of BNF.

## Defining a Grammar.
Below is a BNF representation of an SParse compatible grammar.
```
grammar ::= <statement> | <statement> <grammar>
statement ::= <token> | <name-quantifier> | <flow-quantifier> | <sub-grammar-declaration> | <sub-grammar-usage>

name-quantifier ::= <named-token> | <named-grammar>
named-token ::= "<" <name> ": " <token> ">"
named-grammar ::= "(" <name> ": " <grammar> ")"

flow-quantifier ::= <zero-or-one> | <zero-or-more> | <one-of-set>
zero-or-one ::= "[[" <grammar> "]]"
zero-or-more ::= "((" <grammar> "))"
one-of-set ::= "{{" <grammar> "}}"

sub-grammar-declaration ::= "@" <name> ": " <grammar> "@@"
sub-grammar-usage ::= "@" <name> "@"

token ::= <literal> | <literal-case-sensitive> | <regex> | <all> | <str> | <not-str> | <not-regex>
name ::= <number> | <uppercase letter> | <lowercase letter> | "_" | "-"

literal ::= '"' <anything> '"' | "'" <anything> "'"
literal-case-sensitive ::= '`' <anything> '`'
regex ::= "^" <anything> "^" | "$" <anything> "$"
all ::= "_"
str ::= "_str_"
not-str ::= "_notstr_"
not-regex ::= "_!" <anything> "_"
```

## SParse Grammar Tokens
Below is a description of each type of token that can be used to construct an SParse grammar.
#### General Notes
- For `@name: ... @@`, `(name: ... )`, and `<name: ... >` declarations, the name can consist of any characters from: a-z, A-Z, 0-9, \_ and -.
- To escape ', ", \`, ^, $, \_ within `'...'`, `"..."`, ``...``, `^...^`, `$...$`, `_!..._`
          respectively, use a `\`. Example: `_!one\_up_`

### Grammar Declarations

### Tokens

#### Literal Token
Matches an input token.

##### Syntax
`'Literal Token'`  
`"Literal Token"`  
``Literal Token`` (case sensitive)  

### Regular Expressions
Matches a token if the `re` regular expression it contains matches it.

#### Syntax
    `^Regular Expr^`  
    `$Regular Expr$` (case sensitive)  

##### Convenience Regular Expressions
`_` Matches any token (Short for `^.+^`)  
`_str_` Matches any string token, ie; it begins and ends with a " or '  
`_notstr_` Matches any token, except string tokens (begins or ends with " or ')  
`_!..._` Matches any token EXCEPT the one it contains.  Example: `_!from_` (case insensitive)

### Naming
Token wrappers which cause matches within them to be included in the output from the match.

#### Named Tokens
Named Match. Usage: `<attribute-name: token-to-match>`.
Matched tokens wrapped in a named token will have the matched token recorded in the nearest grammar.

##### Syntax
`<name: token>` Examples: `<colName: _>` `<innerJoin: "inner">`

#### Named Grammar
After parsing, each named grammar will equate to a dictionary, with all named
matches made within it being recorded as key: value pairs.
For a named grammar to match a string, each and every token within it must be able to match the input string.  If any single
token within the grammar cannot match a token, the grammar does not match the input string.
##### Syntax
`(name: ...)` Example: `(test: 'a' <middle: _> 'c')`
                      Matches: `"a b c"`
                      Does not match: `"a b"`

### Flow

#### Zero Or One
Specifies zero or one matches of the grammar it wraps.

##### Syntax
`[[ ... ]]`

#### Zero Or More
Specifies zero or more matches of the grammar it wraps.
Named grammars & named tokens wrapped by Zero Or More brackets will be returned as a dictionary, mapping name: [matches].
Named token matches outside of a named grammar will be grouped into a list of matches, while matches inside a named
grammar will be grouped into a list of dictionaries of matches.

##### Syntax
`(( ... ))` Example: `[[<a: 'a'> (b: <c: 'c'> <d: 'd'>)]]` parsing: `'a c d a c d'`
=>
```
{
    'a': ['a', 'a'],
    'b': [{'c': 'c', 'd': 'd'}, {'c': 'c', 'd': 'd'}]
}
```

#### One of Set
Specifies that one grammar of the set of grammars it contains should match the input string at the current position.
Will attempt to match each grammar it contains with the string until one matches in its entirety.

##### Syntax
`{{ ... }}`


#### Sub Grammar
Defines a sub grammar which can be later referenced by using: `@name@`.  

##### Syntax
`@name: grammar @@`  

##### Notes:
- Defined sub grammars can be nested arbitrarily, but only exist within the scope of the
  namespace of the sub grammar they were defined in.  Sub grammars defined outside of any
  other sub grammars are considered global. Example:
```
@grammarA: 
    @grammarB: 'Grammar B Only exists inside grammarA' @@  
    @grammarB@ '<- This works'  
@@  
@grammarB@ "<- This raises an exception; as it is undefined outside of grammarA's scope."
```  
- Defined sub grammars will be expanded when the grammar is compiled.  This, combined with
  the ability to arbitrarily recurse defined sub grammars means that grammar compilation is
  susceptible to the [Billion Laughs](https://en.wikipedia.org/wiki/Billion_laughs) attack.
  Because of this, you should either not compile untrusted 3rd party grammars, or you should
  disable sub grammar definitions when compiling 3rd party grammars (see documentation below).
- Defined sub grammars can occur anywhere within your grammar, however the act of defining a
  sub grammar does not make any modifications to your grammar until it is used.  For example:  
  `'a' @b: 'b' @@ 'c'` does not match `'a b c'`, but does match `'a c'`  
  `'a' @b: 'b' @@ @b@ 'c'` matches `'a b c'`
- Defined sub grammars cannot be applied until their declaration is finished.  For example,
  while the following is valid:  
  `@a: 'a' @b: 'b' @@ @b@ @@ @a@` (Matches "a b")  
  the following raises an exception.  
  `@a: 'a' @b: @a@ @@ @@` (@a@ cannot appear until the sub grammar 'a' is completed)

# Examples
