# tokex
A Python 2/3 compatible string parsing library allowing for parsing of complex strings into dictionaries and lists of tokens.

## Why tokex?
Admittedly, with a complex enough regex, Python's built-in [re](https://docs.python.org/3.6/library/re.html) library will allow you to accomplish anything that you would be able to accomplish using tokex.  The main difference between the two is that re is focused on matching characters while tokex is focused on matching tokens.  Compared to re however, tokex allows for a more spaced out, readable definition of a grammar which can result in fewer bugs than if it were written as a re pattern, and allows for grouping and reuse of grammar tokens as named sub grammars in a way reminiscent of BNF, which can significantly cut down on the overall size of the grammar.  Finally, tokex allows for Python style comments to be inserted directly into the grammar.

## Usage
tokex exposes two API functions: compile and match.

**tokex.compile** accepts a grammar and returns an object with a match function, which accepts two parameters: inputString and matchEntirety (see tokex.match).  tokex.compile is useful in much the same way as re.compile, for compiling a grammar that will be used to match strings multiple times.  tokex.compile accepts three parameters:
- grammar: (String) The grammar to compile.  This is similar in concept to the pattern parameter passed to re.compile.
- allowSubGrammarDefinitions: (Boolean) Default True.  Toggles support for named sub grammars (See below).  tokex is susceptible to the [billion laughs](https://en.wikipedia.org/wiki/Billion_laughs) attack when compiling untrusted 3rd party grammars.  If this is ever required, sub grammar support should be turned off to mitigate this type of attack.
- tokenizer: (tokexTokenizer subclass or instance) Optional: Either a class or an instance, descending from tokenizers.Tokenizer.tokexTokenizer which will be used to tokenize input strings to the parser.  Uses tokenizers.Tokenizer.tokexTokenizer by default if none passed.

**tokex.match** compiles a grammar and runs it against an input string and returns either None or a dictionary of named matches found within the input string, depending on whether or not the grammar matches the input string.  tokex.match accepts five parameters:
- grammar: (String) See tokex.compile.
- inputString: (String) to match the grammar against.
- matchEntirety: (Boolean) Default True.  If True, requires that the entire input string be matched by the grammar.  If set to False, allows for tokens to be remaining at the end of the input string, as long as the grammar matches from the beginning.
- allowSubGrammarDefinitions: (Boolean) See tokex.compile.
- tokenizer: (tokexTokenizer subclass or instance) Optional: See tokex.compile.

## Usage Examples
The following examples will show parsing of tokens in simplified SQL queries

**Drop Query**
```
>>> import tokex
>>> dropTokex = tokex.compile("""
    'DROP'
    <target: ~table|database~>
    ?(ifExists: 'IF' 'EXISTS')
    <name: .>
""")

>>> dropTokex.match("DROP DATABASE testDatabase")
{'target': 'DATABASE', 'name': 'testDatabase'}

>>> dropTokex.match("DROP TABLE IF EXISTS testTable")
{'target': 'TABLE', 'ifExists': None, 'name': 'testTable'}

>>> dropTokex.match("DROP testTable") is None # Missing DATABASE or TABLE token
True
```

**Update Query**
```
>>> updateTokex = tokex.compile(r"""
    'UPDATE' <tableName: .> "SET"
    +(columns:
        <name: .> "=" <value: .> sep { ',' }
    )
    ?(where: 'WHERE' +(clauses: <clause: !~(ORDER)|(LIMIT)~> ) )
    ?(order: 'ORDER' 'BY' <column: .> <direction: ~(ASC)|(DESC)~> )
    ?(limit: 'LIMIT' <value: ~\\d+~> )
""")

>>> updateTokex.match("UPDATE test SET a=1, b=2, c = 3 WHERE a > 0 AND b = 2 ORDER BY c DESC limit 1")
{
    'tableName': 'test',
    'columns': [
        {'name': 'a', 'value': '1'},
        {'name': 'b', 'value': '2'},
        {'name': 'c', 'value': '3'}
    ],
    'where': {
        'clauses': [
            {'clause': 'a'},
            {'clause': '>'},
            {'clause': '0'},
            {'clause': 'AND'},
            {'clause': 'b'},
            {'clause': '='},
            {'clause': '2'}
        ]
    },
    'order': {'column': 'c', 'direction': 'DESC'},
    'limit': {'value': '1'}
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
>>> selectTokex = tokex.compile(r"""
    def joinCondition {
        +(conditions:  <condition: !~(INNER)|(LEFT)|(WHERE)|(ORDER)|(LIMIT)~>)
    }
    def whereCondition {
        +(conditions: <condition: !~(ORDER)|(LIMIT)~> )
    }

    'SELECT' ?(distinct: "DISTINCT")
        +(selectAttributes: <name: !~from~> sep { ',' } )
    'FROM' <table: .>
    *(joins:
        {
            (inner: "INNER" "JOIN" <table: .> "ON" joinCondition() )
            (left: "LEFT" "JOIN" <table: .> "ON" joinCondition() )
        }
    )
    ?(where: "WHERE" whereCondition() )
    ?(order: "ORDER" "BY" <orderByColumn: .> <orderByDirection: ~(ASC)|(DESC)~> )
    ?(limit: "LIMIT" <limit: ~\\d+~> )
""")

>>> selectTokex.match("SELECT * FROM test limit 1")
{
    'table': 'test',
    'selectAttributes': [{'name': '*'}],
    'limit': {'limit': '1'}
}

>>> selectTokex.match("""
    SELECT a, b, c
    FROM testTable
    INNER JOIN a ON a = t
    INNER JOIN b ON b = a
    LEFT JOIN c ON c = a
    WHERE a > 1 AND b < 2
    ORDER BY a DESC
    LIMIT 2
""")
{
    'selectAttributes': [
        {'name': 'a'},
        {'name': 'b'},
        {'name': 'c'}
    ],
    'table': 'testTable',
    'joins': [
        {
            'inner': {
                'table': 'a',
                'conditions': [{'condition': 'a'}, {'condition': '='}, {'condition': 't'}]
            }
        },
        {
            'inner': {
                'table': 'b',
                'conditions': [{'condition': 'b'}, {'condition': '='}, {'condition': 'a'}]
            }
        },
        {
            'left': {
                'table': 'c',
                'conditions': [{'condition': 'c'}, {'condition': '='}, {'condition': 'a'}]
            }
        }
    ],
    'where': {
        'condition': [
            {'condition': 'a'}, {'condition': '>'}, {'condition': '1'},
            {'condition': 'AND'},
            {'condition': 'b'}, {'condition': '<'}, {'condition': '2'}
        ]
    },
    'order': {'orderByColumn': 'a', 'orderByDirection': 'DESC'},
    'limit': {'limit': '2'}
}

>>> selectTokex.match("SELECT FROM test") is None # Missing select columns
True
```

## Input String Tokenization
- By default, input strings will be tokenized using the default tokenizer, which tokenizes tokens using the following order of precedence:

  All occurrances of `"[^"]*"` or `'[^']*'` are broken up into their own tokens
  All alphanumeric strings are broken into their own token (strings of consecutive a-z, A-Z, 0-9, \_)
  All other non-white space characters are broken up into their own 1-character tokens.

  You can also specify that newlines should be tokenized by instantiating a new instance of `tokenizers.tokenizer.TokexTokenizer`, passing `tokenize_newlines=True`.
  If you do this, you can also pass `ignore_empty_lines=True` to only tokenize which will prevent the trailing newline on empty lines from being tokenized.

  The tokenizing behavior can be further modified by creating a new subclass of `tokenizers.tokenizer.TokexTokenizer`.
  For minor customizations to the base tokenization you can override the base classes `tokenizer_regexes` attribute.  This attribute is set to a list of regular expression strings (strings that could be passed to re.compile) of tokens to match.  Strings at the start of the list take precedence over strings at the end (ie, they will be tried on each position of the input string in order).
  For full control over tokenization, you can override the base classes `tokenize` method.  It should accept a string to tokenize and return a list of parsed tokens.


## Defining A Grammar
Below is a description of each type of grammar element that can be used to construct a tokex grammar.
#### Notes
- Certain elements can take names, for example
  - Sub Grammars: `def grammar_name { ... }`
  - Named Sections: `(section_name: ... )`
  These names can consist of any characters from the following sets: a-z, A-Z, 0-9, \_, and -
- Use \ to escape characters within certain elements.  For example:
  - "a string with an \" embedded quote"
  - ~a regular expression with an \~ embedded tilde~
  Note that this also means that you have to escape slashes within regular expressions.  Two slashes in a grammar = 1 slash in the regular expression.  So a total of 4 are needed to match a slash character using the regular expression
  - ~a regular expression with an \\\\ embedded slash~
- Comments can be included in grammars in a similar fashion to python by using #.  They can appear anywhere in a line and all characters afterwards are considered a part of the comment

### String Literal
Matches an input token exactly.

#### Syntax
`"String Literal"`
or
`'String Literal'`

#### Valid Flags
- Case Sensitive: **s**
  - `s"Case Sensitive String"` - Case of input token must also match case of grammar element to match
- Case Insensitive: **i**
  - `i"Case Insensitive String"` - Case of input token does not need to match case of grammar element to match
- Quoted: **q**
  - `q"Quoted String"` - Input token must be additionally be wrapped by either ' or " to match the grammar element.
- Unquoted: **u**
  - `u"Unquoted String"` - If the input token is wrapped by ' or " it will not match the grammar element.
- Not: **!**
  - `!"Not String"` - The input token matches the grammar element if it does not match the given string.
  - Note: **!** is applied after any other given flags, for example `!q"asdf"` matches any string which is not "asdf" or 'asdf'

#### Examples
```
>>> stringLiteralTokex = tokex.compile("'abc' 'def' 'g'")
>>> stringLiteralTokex.match("abc def g") # Matches
>>> stringLiteralTokex.match("g def abc") is None # Does not match
```

### Regular Expressions
Matches if the `re` regular expression it contains matches the input token.

#### Syntax
`~Regular Expression~`

#### Valid Flags
- Case Sensitive: **s**
  - `s~Case Sensitive Regular Expression~` - Case of input token must also match case of grammar element expression to match
- Case Insensitive: **i**
  - `i~Case Insensitive Regular Expression~` - Case of input token does not need to match case of grammar element expression to match
- Quoted: **q**
  - `q~Quoted Regular Expression~` - Input token must be additionally be wrapped by either ' or " to match the grammar element expression.
- Unquoted: **u**
  - `u~Unquoted Regular Expression~` - If the input token is wrapped by ' or " it will not match the grammar element expression.
- Not: **!**
  - `!~Not Regular Expression~` - The input token matches the grammar element if it does not match the grammar element expression.
  - Note: **!** is applied after any other given flags, for example `!q"asdf"` matches any string which is not "asdf" or 'asdf'


#### Examples
```
>>> regularExpressionTokex = tokex.compile("~(yes)|(no)|(maybe)~")
>>> regularExpressionTokex.match("maybe") # Matches

>>> numericRegularExpressionTokex = tokex.compile(r"~\\d+~")
>>> numericRegularExpressionTokex.match("4570") # Matches
```

### Any String
Matches any non-whitespace input token.
Note: This element will not match a newline (if newlines have been [tokenized](#Input String Tokenization)).

#### Syntax
`.`

#### Valid Flags
- Quoted: **q**
  - `q.` - Matches any quoted (wrapped by either ' or ") non-whitespace input token
- Unquoted: **u**
  - `u.` - Matches any unquoted (not wrapped by either ' or ") non-whitespace input token

#### Examples
```
>>> anyStringTokex = tokex.compile(".")
>>> anyStringTokex.match("maybe") # Matches
>>> anyStringTokex.match("'ANYTHING'") # Matches
```

### Newline
Matches a newline in an input string .
Note that Newline elements will only match newlines in input strings if newlines are tokenized by setting `tokenize_newlines=True` on the tokenizer. See [Input String Tokenization](#Input String Tokenization)

#### Syntax
`$`

#### Examples
```
>>> newlineTokex = tokex.compile(". $ .", tokenizer=tokex.tokenizers.TokexTokenizer(tokenize_newlines=True))
>>> newlineTokex.match("something \n else ") # Matches
>>> newlineTokex.match("something else ") # Does not match
```

### Named Tokens
Matched tokens wrapped in a named token will have the matched token recorded in the nearest named section.
Note: Only singular elements (documented above, not below) can be wrapped inside a named token

#### Syntax
`<token-name: ...>`

#### Examples
```
>>> namedTokenTokex = tokex.compile("<token: .>")
>>> namedTokenTokex.match("some_token")
{'token': 'some_token'}
```

### Named Section
A named section does not actually match any tokens in an input string, instead it acts as a container for the elements within it and has the following two effects:
1. The elements within it will only match an input grammar if they *all* match.  If the contained elements do not all match, then none of them will match.
2. The output from any matching named tokens within a named section will be be grouped together into a single dictionary

#### Syntax
`(name: ...)`

#### Examples
```
>>> namedGrammarTokex = tokex.compile("(test: 'a' <middle: .> 'c')")
>>> namedGrammarTokex.match("a b c") # Matches
{'test': {'middle': 'b'}}
>>> namedGrammarTokex.match("a b") # Does not match
```

### Zero Or One Named Section
Acts the same way that a regular Named Section does, however will match an input string zero or one times.  In other words, the elements it contains are optional.

#### Syntax
`?(name: ... )`

#### Examples
```
>>> zeroOrOneTokex = tokex.compile("'prefix' ?(middle: <middle_element: !'suffix'>) 'suffix'")
>>> zeroOrOneTokex.match("prefix middle_token suffix") # Matches
{'middle': {'middle_element': 'middle_token'}}
>>> zeroOrOneTokex.match("prefix suffix") # Still matches
```

### Zero Or More Named Section
Acts the same way that a regular Named Section does, however will match an input string zero or more times.  In other words, the elements it contains are optional, or can be present one or more times.

Notes:
 - Each time a zero or more named section matches it will create a new dictionary "context" which all named sections will populate.  On the next iteration, it creates a fresh dictionary for the named sections to populate.
 - A zero or more named section can have an optional iteration delimiter section specified on it, using the following syntax: `sep { ... }`.  The effect of doing this is that subsequent matches (after the first match) will only match if the grammar elements defined within the `sep { ... }` are present.  If any named tokens appear within the iteration delimiter section they will populate the previous iterations dictionary.

#### Syntax
`*(name: ... )`
`*(name: ... sep { ... } )` (the grammar within the `sep { ... }` must occur between each match of the section)

#### Examples
```
>>> zeroOrMoreGrammar = tokex.compile("*(as: <a: 'a'>) *(bs: <b: 'b'>)")
>>> zeroOrMoreGrammar.match("a a b b b")
{'as': [{'a': 'a'}, {'a': 'a'}], 'bs': [{'b': 'b'}, {'b': 'b'}, {'b': 'b'}]}
>>> zeroOrMoreGrammar.match("b b")
{'bs': [{'b': 'b'}, {'b': 'b'}]}

>>> zeroOrMoreGrammar = tokex.compile("*(letters: <letter: .> sep { ',' })")
>>> zeroOrMoreGrammar.match("a, b, c")
{'letters': [{'letter': 'a'}, {'letter': 'b'}, {'letter': 'c'}]}
>>> zeroOrMoreGrammar.match("a, b c") # Does not match, as there's no , between b and c
```

### One Or More
Acts the same way that a regular Named Section does, however will match an input string one or more times.  In other words, the elements it contains are required, and can be present one or more times.

Notes:
 - Each time a one or more named section matches it will create a new dictionary "context" which all named sections will populate.  On the next iteration, it creates a fresh dictionary for the named sections to populate.
 - A one or more named section can have an optional iteration delimiter section specified on it, using the following syntax: `sep { ... }`.  The effect of doing this is that subsequent matches (after the first match) will only match if the grammar elements defined within the `sep { ... }` are present.  If any named tokens appear within the iteration delimiter section they will populate the previous iterations dictionary.

#### Syntax
`+(name: ... )`
`+(name: ... sep { ... } )` (the grammar within the `sep { ... }` must occur between each match of the section)

#### Examples
```
>>> oneOrMoreGrammar = tokex.compile("+(as: <a: 'a'>) +(bs: <b: 'b'>)")
>>> oneOrMoreGrammar.match("a a b b b")
{'as': [{'a': 'a'}, {'a': 'a'}], 'bs': [{'b': 'b'}, {'b': 'b'}, {'b': 'b'}]}
>>> oneOrMoreGrammar.match("b b") # Does not match, as there are no a's

>>> oneOrMoreGrammar = tokex.compile("+(letters: <letter: .> sep { ',' })")
>>> oneOrMoreGrammar.match("a, b, c")
{'letters': [{'letter': 'a'}, {'letter': 'b'}, {'letter': 'c'}]}
>>> oneOrMoreGrammar.match("a, b c") # Does not match, as there's no , between b and c
```

### One of Set
Specifies that one grammar of the set of contained grammars should match the input string at the current position.
Will attempt to match each grammar in order until one matches.

#### Syntax
`{ ... }`

#### Examples
Match one grammar of a set, zero or many times:
```
>>> oneOfASetTokex = tokex.compile("""
    'ALTER' 'TABLE' <table_name: .>
    *(conditions:
        {
            (add_column: 'add' 'column' <name: .> <type: .>)
            (remove_column: 'remove' 'column' <name: .>)
            (modify_column: 'modify' 'column' <name: .> <new_name: .> <new_type: .>)
            (add_index: 'add' 'index' <column: .>)
            (remove_index: 'remove' 'index' <column: .>)
        } sep { ',' }
    )
""")
>>> oneOfASetTokex.match("""
    ALTER TABLE test
    ADD COLUMN a int,
    REMOVE COLUMN a_old,
    REMOVE INDEX a_old
""")
{
    'table_name': 'test',
    'conditions': [
        {'add_column': {'name': 'a', 'type': 'int'}},
        {'remove_column': {'name': 'a_old'}},
        {'remove_index': {'column': 'a_old'}}
    ]
}

```

### Sub Grammar
Defines a named sub grammar which can be later referenced by using: `sub_grammar_name()`.

#### Syntax
`def name { ... }`

#### Notes:
- Defined sub grammars can be nested arbitrarily, but only exist within the scope of the
  namespace of the sub grammar they were defined in.  Sub grammars defined outside of any
  other sub grammars are considered global. Example:
```
def grammarA {
    def grammarB { 'Grammar B Only exists inside grammarA' }
    grammarB() '<- This works'
}
grammarB() "<- This raises an exception; as it is undefined outside of grammarA's scope."
```
- Defined sub grammars will be expanded when the grammar is compiled.  This, combined with
  the ability to arbitrarily recurse defined sub grammars means that grammar compilation is
  susceptible to the [Billion Laughs](https://en.wikipedia.org/wiki/Billion_laughs) attack.
  Because of this, you should either not compile untrusted 3rd party grammars, or you should
  disable sub grammar definitions when compiling 3rd party grammars (see documentation below).
- Defined sub grammars can occur anywhere within your grammar, however the act of defining a
  sub grammar does not make any modifications to your grammar until it is used.  For example:
  `'a' def b { 'b' } 'c'` does not match `'a b c'`, but does match `'a c'`
  `'a' def b { 'b' } b() 'c'` matches `'a b c'`
- Defined sub grammars cannot be applied until their declaration is finished.  For example,
  while the following is valid:
```
def a {
    'a'
    def b { 'b' }
    b()
}
a()
```
(Matches "a b")
The following raises an exception.
```
def a {
    'a'
    def b { a() }
}
```
(`a()` cannot appear until the sub grammar 'a' is completed)

## Notes
- To debug why a grammar matches/doesn't match a particular input string, set python's logging level to DEBUG before calling match on the input string.  Detailed debugging information will be written to STDERR.
