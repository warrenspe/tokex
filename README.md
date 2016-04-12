# Tokex
A Python structured string parsing library allowing for parsing of complex strings into dictionaries and lists of tokens.

## Why Tokex?
Admittedly, with a complex enough regex, Python's built-in [re](https://docs.python.org/3.6/library/re.html) library will allow you to accomplish anything that you would be able to accomplish using Tokex.  The main difference between Tokex and re is that re is focused on matching characters, while Tokex is focused on matching tokens.  Compared to re however, Tokex allows for a more spaced out, readable definition of a grammar than re which can result in fewer bugs, and allows for grouping and reuse of grammar tokens in named sub grammars in a way reminiscent of BNF, which can significantly cut down on the overall size of the grammar.

## Usage
Tokex attempts to emulates re in its usage.  Tokex offers two functions, compile and match.

**Tokex.compile** accepts a grammar and returns an object with a match function following the same spec as Tokex.match.  Tokex.compile is useful in much the same way as re.compile, for compiling a grammar that will be used to match strings multiple times.  Tokex.compile accepts two parameters:
- grammar: (String) The grammar to compile.  This is very similar in concept to the pattern parameter passed to re.compile.
- allowSubGrammarDefinitions: (Boolean) Default True.  Toggles support for named sub grammars (See below).  Tokex is susceptible to the [billion laughs](https://en.wikipedia.org/wiki/Billion_laughs) attack when compiling untrusted 3rd party grammars.  If this is ever done, sub grammar support should be turned off to mitigate this type of attack.

**Tokex.match** compiles a grammar and runs it against an input string and returns either None or a dictionary of named matches found within the input string, depending on whether or not the grammar matches the input string.  Tokex.match accepts 4 parameters:
- grammar: (String) See Tokex.compile
- inputString: (String) to match the grammar against.
- matchEntirety: (Boolean) Default True.  If True, requires that the entire input string be matched by the grammar.  If set to False, allows for tokens to be remaining at the end of the input string, as long as the grammar matches from the beginning.
- allowSubGrammarDefinitions: (Boolean) See Tokex.compile

## Usage Examples
The following examples will show parsing of tokens in simplified SQL queries

```

```

## Notes
By default, input strings will be tokenized based on the following rules, in the following order of precedence:

All occurrances of "[^"]*" or '[^']*' are broken up into their own tokens
All alphanumeric strings are broken into their own token (strings of consecutive a-z, A-Z, 0-9, _)
All other non-white space characters are broken up into their own 1-character tokens.

The tokenizing behavior can be modified by updating the attribute `tokenizerRegexes` of a compiled grammar.  This attribute refers to a list of strings that are joined using "|" and passed to the `re.findall` function to tokenize the query.  As an example:  
- Allow '#' characters to be joined in tokens with other alphanumeric characters to, say, create tokens like: "Phone#" (instead of "Phone", "#")
  - `parser.tokenizerRegexes[2] = "[\w#]+`

This 'feature' will be getting reworked in a future version.

## Defining a Grammar.
Below is a BNF representation of a Tokex compatible grammar.
```
grammar ::= <statement> | <statement> <grammar>
statement ::= <token> | <name-quantifier> | <flow-quantifier> | <sub-grammar-declaration> | <sub-grammar-usage> | <comment>

name-quantifier ::= <named-token> | <named-grammar>
named-token ::= "<" <name> ": " <token> ">"
named-grammar ::= "(" <name> ": " <grammar> ")"

flow-quantifier ::= <zero-or-one> | <zero-or-more> | <one-of-set>
zero-or-one ::= "[[" <grammar> "]]"
zero-or-more ::= "((" <grammar> "))"
one-of-set ::= "{{" <grammar> "}}"

comment ::= "#" <anything> "\n" | "#" <anything> "EOF"

sub-grammar-declaration ::= "@" <name> ": " <grammar> "@@"
sub-grammar-usage ::= "@" <name> "@"

token ::= <literal> | <literal-case-sensitive> | <regex> | <all> | <str> | <not-str> | <not-token>
name ::= <number> | <uppercase letter> | <lowercase letter> | "_" | "-"

literal ::= '"' <anything> '"' | "'" <anything> "'"
literal-case-sensitive ::= '`' <anything> '`'
regex ::= "^" <anything> "^" | "$" <anything> "$"
all ::= "_"
str ::= "_str_"
not-str ::= "_notstr_"
not-token ::= "_!" <anything> "_"
```

## Tokex Grammar Tokens
Below is a description of each type of token that can be used to construct an Tokex grammar.
#### General Notes
- For `@name: ... @@`, `(name: ... )`, and `<name: ... >` declarations, the name can consist of any characters from: a-z, A-Z, 0-9, \_ and -.
- To escape ', ", \`, ^, $, \_ within `'...'`, `"..."`, ``...``, `^...^`, `$...$`, `_!..._`
          respectively, use a `\`. Example: `_!one\_up_`
- Comments can be included in grammars in a similar fashion to python by using hashtags.

### Tokens
Matches an input token exactly.

##### Syntax
`'Literal Token'`  
`"Literal Token"`  
`` `Literal Token` `` (case sensitive)  

##### Examples
`'insert' 'into '`
`"butterscotch" "pudding"`
`` `CAPITAL` ``

### Regular Expressions
Matches a token if the `re` regular expression it contains matches it.

##### Syntax
`^Regular Expr^`  
`$Regular Expr$` (case sensitive)  

##### Examples
`^(yes|no|maybe)^`
`$(FROM|From|from)$`

##### Convenience Regular Expressions
`_` Matches any token (Short for `^.+^`)  
`_str_` Matches any string token; ie one that begins and ends with a " or '  
`_notstr_` Matches any token, except string tokens (begins and ends with " or ')  
`_!..._` Matches any token except the one it contains.  Example: `_!from_` (case insensitive)

### Naming
Token wrappers which cause matches within them to be included in the output from the match.

#### Named Tokens
Matched tokens wrapped in a named token will have the matched token recorded in the nearest grammar.

##### Syntax
`<match-name: token-to-match>`

##### Examples
Examples: `<colName: _>` `<innerJoin: "inner">`

#### Named Grammar
After parsing, each named grammar will equate to a dictionary, with all named
matches made within it being recorded as key: value pairs.
For a named grammar to match a string, each and every token within it must be able to match the input string.  If any single
token within the grammar cannot match a token, the grammar will not match the input string.

##### Syntax
`(name: ...)`

##### Examples
`(test: 'a' <middle: _> 'c')`  
Matches: `"a b c"`  
Does not match: `"a b"`  
Returns: `{'test': {'middle': 'b'}}`  

### Flow

#### Zero Or One
Specifies zero or one matches of the grammar it wraps.

##### Syntax
`[[ ... ]]`

##### Examples
`'DROP' 'TABLE' [[<ifExists: 'IF'> 'EXISTS']] <tableName: _notstr_>`

#### Zero Or More
Specifies zero or more matches of the grammar it wraps.
Named grammars & named tokens wrapped by Zero Or More brackets will be returned as a dictionary, mapping name to a list of matches.
Named token matches outside of a named grammar will be grouped into a list of matches, while matches inside a named
grammar will be grouped into a list of dictionaries of matches.

##### Syntax
`(( ... ))`

##### Examples
```
'INSERT' 'INTO' <tableName: _notstr_> 'VALUES'
((
  (value:
    '(' (( _ )) ') ','
  )
))
```

`(( <tok: 'a'> (gram: <b: 'b'> <c: 'c'>) ))` parsing: `'a b c a b c'`  
=>
```
{
    'tok': ['a', 'a'],
    'gram': [{'b': 'b', 'c': 'c'}, {'b': 'b', 'c': 'c'}]
}
```

#### One of Set
Specifies that one grammar of the set of grammars it contains should match the input string at the current position.
Will attempt to match each grammar it contains with the string until one matches in its entirety.

##### Syntax
`{{ ... }}`

##### Examples
Match one grammar of a set, zero or many times:
```
'ALTER' 'TABLE' <tableName: _notstr_>
((
  {{
    (addColumn: 'add' 'column' <name: _> <type: _>)
    (removeColumn: 'remove' 'column' <name: _>)
    (modifyColumn: 'modify' 'column' <name: _> <newName: _> <newType: _>)
    (addIndex: 'add' 'index' <column: _>)
    (removeIndex: 'remove' 'index' <column: _>)
  }}
))
```

### Sub Grammar
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
```
@a:
    'a'
    @b: 'b' @@
    @b@
@@
@a@
```
(Matches "a b")  
The following raises an exception.
```
@a:
    'a'
    @b: @a@ @@
@@
```
(`@a@` cannot appear until the sub grammar 'a' is completed)
