# Tokex
A Python 2/3 compatible string parsing library allowing for parsing of complex strings into dictionaries and lists of tokens.

[Why Tokex?](https://github.com/warrenspe/Tokex/blob/master/README.md#why-tokex)  
[Usage](https://github.com/warrenspe/Tokex/blob/master/README.md#usage)  
[Usage Examples](https://github.com/warrenspe/Tokex/blob/master/README.md#usage-examples)  
[Input String Tokenization](https://github.com/warrenspe/Tokex/blob/master/README.md#input-string-tokenization)  
[Defining A Grammar (BNF)](https://github.com/warrenspe/Tokex/blob/master/README.md#defining-a-grammar-bnf)  
[Defining A Grammar](https://github.com/warrenspe/Tokex/blob/master/README.md#defining-a-grammar)  
&nbsp;&nbsp;&nbsp;[General Notes](https://github.com/warrenspe/Tokex/blob/master/README.md#general-notes)  
&nbsp;&nbsp;&nbsp;[Tokens](https://github.com/warrenspe/Tokex/blob/master/README.md#tokens)  
&nbsp;&nbsp;&nbsp;[Regular Expressions](https://github.com/warrenspe/Tokex/blob/master/README.md#regular-expressions)  
&nbsp;&nbsp;&nbsp;[Naming](https://github.com/warrenspe/Tokex/blob/master/README.md#naming)  
&nbsp;&nbsp;&nbsp;[Flow](https://github.com/warrenspe/Tokex/blob/master/README.md#flow)  
&nbsp;&nbsp;&nbsp;[Sub Grammar](https://github.com/warrenspe/Tokex/blob/master/README.md#sub-grammar)  
[Notes](https://github.com/warrenspe/Tokex/blob/master/README.md#notes-1)  

## Why Tokex?
Admittedly, with a complex enough regex, Python's built-in [re](https://docs.python.org/3.6/library/re.html) library will allow you to accomplish anything that you would be able to accomplish using Tokex.  The main difference between the two is that re is focused on matching characters while Tokex is focused on matching tokens.  Compared to re however, Tokex allows for a more spaced out, readable definition of a grammar which can result in fewer bugs than if it were written as a re pattern, and allows for grouping and reuse of grammar tokens as named sub grammars in a way reminiscent of BNF, which can significantly cut down on the overall size of the grammar.  Finally, Tokex allows for Python style comments to be inserted directly into the grammar.

## Usage
Tokex attempts to emulates re in its usage by offering two functions, compile and match.

**Tokex.compile** accepts a grammar and returns an object with a match function, which accepts two parameters: inputString and matchEntirety (see Tokex.match).  Tokex.compile is useful in much the same way as re.compile, for compiling a grammar that will be used to match strings multiple times.  Tokex.compile accepts three parameters:
- grammar: (String) The grammar to compile.  This is similar in concept to the pattern parameter passed to re.compile.
- allowSubGrammarDefinitions: (Boolean) Default True.  Toggles support for named sub grammars (See below).  Tokex is susceptible to the [billion laughs](https://en.wikipedia.org/wiki/Billion_laughs) attack when compiling untrusted 3rd party grammars.  If this is ever required, sub grammar support should be turned off to mitigate this type of attack.
- tokenizer: (TokexTokenizer subclass or instance) Optional: Either a class or an instance, descending from tokenizers.Tokenizer.TokexTokenizer which will be used to tokenize input strings to the parser.  Uses tokenizers.Tokenizer.TokexTokenizer by default if none passed.

**Tokex.match** compiles a grammar and runs it against an input string and returns either None or a dictionary of named matches found within the input string, depending on whether or not the grammar matches the input string.  Tokex.match accepts five parameters:
- grammar: (String) See Tokex.compile.
- inputString: (String) to match the grammar against.
- matchEntirety: (Boolean) Default True.  If True, requires that the entire input string be matched by the grammar.  If set to False, allows for tokens to be remaining at the end of the input string, as long as the grammar matches from the beginning.
- allowSubGrammarDefinitions: (Boolean) See Tokex.compile.
- tokenizer: (TokexTokenizer subclass or instance) Optional: See Tokex.compile.

## Usage Examples
The following examples will show parsing of tokens in simplified SQL queries

**Drop Query**
```
>>> import Tokex
>>> dropTokex = Tokex.compile("""
    'DROP'
    <target: ^table|database^>
    (? <ifExists: 'IF'> 'EXISTS' )
    <name: _>""")

>>> dropTokex.match("DROP DATABASE testDatabase")
{'target': 'DATABASE', 'name': 'testDatabase'}

>>> dropTokex.match("DROP TABLE IF EXISTS testTable")
{'target': 'TABLE', 'ifExists': 'IF', 'name': 'testTable'}

>>> dropTokex.match("DROP testTable") is None # Missing DATABASE or TABLE token
True
```

**Update Query**
```
>>> updateTokex = Tokex.compile("""
    'UPDATE' <tableName: _> "SET"
    (+
        (columnSets: <columnToSet: _> "=" <value: _>) [',']
    )
    (? 'WHERE' (+ <whereClause: _!ORDER|LIMIT_> ) )
    (? 'ORDER' 'BY' <orderByColumn: _> <orderByDirection: ^ASC|DESC^> )
    (? 'LIMIT' <limit: ^\d+^> )""")

>>> updateTokex.match("UPDATE test SET a=1, b=2, c = 3 WHERE a > 0 AND b = 2 ORDER BY c DESC limit 1")
{
    'tableName': 'test',
    'columnSets': [{'columnToSet': 'a', 'value': '1'},
                   {'columnToSet': 'b', 'value': '2'},
                   {'columnToSet': 'c', 'value': '3'}],
    'whereClause': ['a', '>', '0', 'AND', 'b', '=', '2'],
    'orderByColumn': 'c',
    'orderByDirection': 'DESC',
    'limit': '1'
}

>>> updateTokex.match("UPDATE test SET a=1 LIMIT 1")
{
    'tableName': 'test',
    'columnSets': [{'columnToSet': 'a', 'value': '1'}],
    'limit': '1'
}

>>> updateTokex.match("UPDATE testTable SET WHERE a > 1") is None # Missing a column to set
True
```

**Select Query**
```
>>> selectTokex = Tokex.compile("""
    @joinCondition:
        (+ <condition: _!INNER|LEFT|WHERE|ORDER|LIMIT_> )
    @@
    @whereCondition:
        (+ <whereCondition: _!ORDER|LIMIT_> )
    @@

    'SELECT' (? <distinct: "DISTINCT"> )
        (+ <selectAttributes: _!from_> [','] )
    'FROM' <fromTable: _>
    (*
        {
            (innerJoins: "INNER" "JOIN" <tableName: _> "ON" @joinCondition@ )
            (leftJoins: "LEFT" "JOIN" <tableName: _> "ON" @joinCondition@ )
        }
    )
    (? "WHERE" @whereCondition@ )
    (? "ORDER" "BY" <orderByColumn: _> <orderByDirection: ^ASC|DESC^> )
    (? "LIMIT" <limit: ^\d+^> )""")

>>> selectTokex.match("SELECT * FROM test limit 1")
{'fromTable': 'test', 'selectAttributes': ['*'], 'limit': '1'}

>>> selectTokex.match("""
    SELECT a, b, c
    FROM testTable
    INNER JOIN a ON a = t
    INNER JOIN b ON b = a
    LEFT JOIN c ON c = a
    WHERE a > 1 AND b < 2
    ORDER BY a DESC
    LIMIT 2""")
{
    'selectAttributes': ['a', 'b', 'c'],
    'fromTable': 'testTable',
    'innerJoins': [{'condition': ['a', '=', 't'], 'tableName': 'a'},
                   {'condition': ['b', '=', 'a'], 'tableName': 'b'}],
    'leftJoins': [{'condition': ['c', '=', 'a'], 'tableName': 'c'}],
    'whereCondition': ['a', '>', '1', 'AND', 'b', '<', '2'],
    'orderByColumn': 'a',
    'orderByDirection': 'DESC',
    'limit': '2'
}

>>> selectTokex.match("SELECT FROM test") is None # Missing select columns
True
```

## Input String Tokenization
- By default, input strings will be tokenized using the default tokenizer, which tokenizes tokens using the following order of precedence:

  All occurrances of `"[^"]*"` or `'[^']*'` are broken up into their own tokens  
  All alphanumeric strings are broken into their own token (strings of consecutive a-z, A-Z, 0-9, _)  
  All other non-white space characters are broken up into their own 1-character tokens.  

  The tokenizing behavior can be modified by creating a new subclass of `tokenizers.Tokenizer.TokexTokenizer`, or by using one of the pre-built tokenizers in `/tokenizers/`.  There are only two requirements for implementing your own tokenizing class:  

1. It must be a subclass of `tokenizers.Tokenizer.TokexTokenizer`
2. It must define a `tokenize` method, accepting just the string to tokenize and returning a list of parsed tokens.

Alternatively, the base class can be extended simply by creating a subclass and overriding a class list named `tokenizerRegexes`.  This list should contain regular expressions to match tokens, in order of precedence (ie a regular expression in index 0 has precedence over one in index 1).  This eliminates the need to define a `tokenize` method.

## Defining a Grammar (BNF)
Below is a BNF representation of a Tokex compatible grammar.
```
grammar ::= <statement> | <statement> <grammar>
statement ::= <token> | <name-quantifier> | <flow-quantifier> | <sub-grammar-declaration> | <sub-grammar-usage> | <comment>

name-quantifier ::= <named-token> | <named-grammar>
named-token ::= "<" <name> ": " <token> ">"
named-grammar ::= "(" <name> ": " <grammar> ")"

flow-quantifier ::= <zero-or-one> | <zero-or-more> | <one-or-more> | <one-of-set>
zero-or-one ::= "(?" <grammar> | <delimiter-grammar> ")"
zero-or-more ::= "(*" <grammar> | <delimiter-grammar> ")"
one-or-more ::= "(+" <grammar> ")"
one-of-set ::= "{" <grammar> "}"

delimiter-grammar ::= "" | "[" <grammar> "]"

comment ::= "#" <anything> "\n" | "#" <anything> EOF

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

## Defining A Grammar
Below is a description of each type of token that can be used to construct a Tokex grammar.
#### General Notes
- For `@name: ... @@`, `(name: ... )`, and `<name: ... >` declarations, the name can consist of any characters from: a-z, A-Z, 0-9, \_ and -.
- To escape ', ", \`, ^, $, \_ within `'...'`, `"..."`, `` `...` ``, `^...^`, `$...$`, `_!..._`
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
```
>>> namedGrammarTokex = Tokex.compile("(test: 'a' <middle: _> 'c')")
>>> namedGrammarTokex.match("a b c")
{'test': {'middle': 'b'}}
>>> namedGrammarTokex.match("a b") is None
True
```

### Flow

#### Zero Or One
Specifies zero or one matches of the grammar it wraps.

##### Syntax
`(? ... )`

##### Examples
`'DROP' 'TABLE' (? <ifExists: 'IF'> 'EXISTS' ) <tableName: _notstr_>`

#### Zero Or More
Specifies zero or more matches of the grammar it wraps.
Named grammars & named tokens wrapped by zero or more brackets will be returned as a dictionary, mapping names to a list of matches.
Named token matches outside of a named grammar will be grouped into a list of matches, while matches inside a named
grammar will be grouped into a list of dictionaries of matches.

##### Syntax
`(* ... )`  
`(* ... [ ... ] )` (the grammar within the `[]` brackets must occur between each match of the grammar within the `(* )`  

##### Examples
```
>>> Tokex.match("""
    'INSERT' 'INTO' <tableName: _notstr_> 'VALUES'
    (*
        (values:
            '(' (* <val:_> [','] ) ')'
        ) [',']
    )
    """, "INSERT INTO test VALUES (1, 2, 3), (4, 5, 6)")

{
    'tableName': 'test',
    'values': [
        {'val': ['1', '2', '3']},
        {'val': ['4', '5', '6']}
    ]
}
```

#### One Or More
Specifies one or more matches of the grammar it wraps. Essentially the same as a zero or more block in every other aspect.

##### Syntax
`(+ ... )`  
`(+ ... [ ... ] )` (the grammar within the `[]` brackets must occur between each match of the grammar within the `(* )`  

##### Examples
```
>>> createTokex = Tokex.compile("""
    'CREATE'
    {
        (database: 'DATABASE' <name: _>)
        (table:
            'TABLE' <name: _> "("
            (+
                (columnDefs: <columnName: _!index_> <columnType: _> ) [',']
            )
            (*
                ',' 'INDEX' <indexedColumnNames: _>
            )
            ")"
        )
    }
    """)

>>> createTokex.match("CREATE database test")
{'database': {'name': 'test'}}

>>> createTokex.match("""
        CREATE TABLE testTable (
            colA int,
            colB char,
            index colA
        )
    """)

{'table': {
    'name': 'testTable'
    'columnDefs': [
        {'columnName': 'colA', 'columnType': 'int'},
        {'columnName': 'colB', 'columnType': 'char'}
    ],
    'indexedColumnNames': ['colA'],
}}

```

#### One of Set
Specifies that one grammar of the set of grammars it contains should match the input string at the current position.
Will attempt to match each grammar it contains with the string until one matches in its entirety.

##### Syntax
`{ ... }`

##### Examples
Match one grammar of a set, zero or many times:
```
>>> alterTokex = Tokex.compile("""
    'ALTER' 'TABLE' <tableName: _>
    (*
        {
            (addColumn: 'add' 'column' <name: _> <type: _>)
            (removeColumn: 'remove' 'column' <name: _>)
            (modifyColumn: 'modify' 'column' <name: _> <newName: _> <newType: _>)
            (addIndex: 'add' 'index' <column: _>)
            (removeIndex: 'remove' 'index' <column: _>)
        } [',']
    )""")
>>> alterTokex.match("""
    ALTER TABLE test
    ADD COLUMN a int,
    REMOVE COLUMN a_old,
    REMOVE INDEX a_old
    """)
{'addColumn': [{'name': 'a', 'type': 'int'}],
 'removeColumn': [{'name': 'a_old'}],
 'removeIndex': [{'column': 'a_old'}],
 'tableName': 'test'}

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

## Notes
- To debug why a grammar matches/doesn't match a particular input string, set `Tokex.DEBUG = True` before calling match on the input string.  Detailed debugging information will be written to STDERR.
