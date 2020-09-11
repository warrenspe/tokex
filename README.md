# tokex
A Python 2/3 compatible string parsing library allowing for parsing of complex strings into dictionaries and lists of tokens.

## Why tokex?
Admittedly, with a complex enough regex, Python's built-in [re](https://docs.python.org/3.6/library/re.html) library will allow you to accomplish anything that you would be able to accomplish using tokex.  The main difference between the two is that re is focused on matching characters while tokex is focused on matching tokens.  Compared to re however, tokex allows for a more spaced out, readable definition of a grammar which can result in fewer bugs than if it were written as a re pattern, and allows for grouping and reuse of grammar tokens as named sub grammars in a way reminiscent of BNF, which can significantly cut down on the overall size of the grammar.  Finally, tokex allows for Python style comments to be inserted directly into the grammar.

## Usage
tokex exposes two API functions: compile and match.

tokex.**compile(**_input\_grammar,_ _allow\_sub\_grammar\_definitions=True_, _tokenizer=tokex.tokenizers.TokexTokenizer,_ _default\_flags=tokex.flags.DEFAULTS,_ _debug=True_**)**

> Compile a tokex grammar into a Tokex object, which can be used for matching using its **match()** method.  If you intend to call match several times using the same input grammar, using a precompiled Tokex object can be slightly more performant, as the tokex grammar won't have to be parsed each time
>
> If *allow\_sub\_grammar\_definitions* is set to True it will enable [Sub Grammars](#sub-grammars) within the given grammar. Note that tokex is susceptible to the [billion laughs](https://en.wikipedia.org/wiki/Billion_laughs) attack when compiling untrusted 3rd party grammars with this feature enabled.  If compilation of 3rd party grammars is ever required, sub grammar support should be turned off to mitigate this type of attack.
> 
> A custom tokenizer can be passed through the _tokenizer_ parameter. If given it should be set to an instance/subclass of tokex.tokenizers.TokexTokenizer.
> 
>  _default\_flags_ can be passed as a set of strings of flags to apply to valid elements by default. Default flags can be overridden by specifying an opposing flag on elements in the grammar.  See [Grammar Notes](#grammar-notes) for the set of flags which are applied by default.
> 
> If _debug_ is passed as True, it will enable the logging logger (named "tokex"), which will print out debugging information regarding the grammar as it processes an input string.

tokex.**match(**_input\_grammar,_ _input_string,_ _match_entirety=True,_ _allow\_sub\_grammar\_definitions=True,_ _tokenizer=tokex.tokenizers.TokexTokenizer,_ _default\_flags=tokex.flags.DEFAULTS,_ _debug=True_**)**

> Matches a given tokex grammar against an input string and returns either a dictionary of named matches if the grammar matches the input string or None if it doesn't.
> 
> If *match\_entirety* is True the grammar will only match the input string if the entire input string is consumed.  If it is False, trailing tokens at the end of the input string may be ignored if they do not match the grammar.
> 
> If *allow\_sub\_grammar\_definitions* is set to True it will enable [Sub Grammars](#sub-grammars) within the given grammar. Note that tokex is susceptible to the [billion laughs](https://en.wikipedia.org/wiki/Billion_laughs) attack when compiling untrusted 3rd party grammars with this feature enabled.  If compilation of 3rd party grammars is ever required, sub grammar support should be turned off to mitigate this type of attack.
> 
>  _default\_flags_ can be passed as a set of strings of flags to apply to valid elements by default. Default flags can be overridden by specifying an opposing flag on elements in the grammar.  See [Grammar Notes](#grammar-notes) for the set of flags which are applied by default
> 
> A custom tokenizer can be passed through the _tokenizer_ parameter. If given it should be set to an instance/subclass of tokex.tokenizers.TokexTokenizer.
> 
> If _debug_ is passed as True, it will enable the logging logger (named "tokex"), which will print out debugging information regarding the grammar as it processes an input string.

### Tokex Object
A Tokex object (constructed using tokex.compile) has the following methods on it:

Tokex.**match(**_input_string,_ _match_entirety=True_, _debug=False_**)**

> Tokex.match runs a precompiled grammar against an input string and returns either a dictionary of named matches if the grammar matches the input string or None if it doesn't.
> 
> If *match\_entirety* is True the grammar will only match the input string if the entire input string is consumed.  If it is False, trailing tokens at the end of the input string may be ignored if they do not match the grammar.
> 
> If _debug_ is passed as True, it will enable the logging logger (named "tokex"), which will print out debugging information regarding the grammar as it processes an input string.

## Usage Examples
The following examples will show parsing of tokens in simplified SQL queries

**Drop Query**
```
>>> import tokex
>>> drop_tokex = tokex.compile("""
    'DROP'
    <target: ~table|database~>
    ?(if_exists: 'IF' 'EXISTS')
    <name: .>
""")

>>> drop_tokex.match("DROP DATABASE test_database")
{'target': 'DATABASE', 'name': 'test_database'}

>>> drop_tokex.match("DROP TABLE IF EXISTS test_table")
{'target': 'TABLE', 'if_exists': None, 'name': 'test_table'}

>>> drop_tokex.match("DROP test_table") is None # Missing DATABASE or TABLE token
True
```

**Update Query**
```
>>> update_tokex = tokex.compile(r"""
    'UPDATE' <table_name: .> "SET"
    +(columns:
        <name: .> "=" <value: .> sep { ',' }
    )
    ?('WHERE' +(where_clauses: <token: !~(ORDER)|(LIMIT)~> ) )
    ?(order: 'ORDER' 'BY' <column: .> <direction: ~(ASC)|(DESC)~> )
    ?('LIMIT' <limit: ~\\d+~> )
""")

>>> update_tokex.match("UPDATE test SET a=1, b=2, c = 3 WHERE a > 0 AND b = 2 ORDER BY c DESC limit 1")
{
    'table_name': 'test',
    'columns': [
        {'name': 'a', 'value': '1'},
        {'name': 'b', 'value': '2'},
        {'name': 'c', 'value': '3'}
    ],
    'where_clauses': [
        {'token': 'a'}, {'token': '>'}, {'token': '0'},
        {'token': 'AND'},
        {'token': 'b'}, {'token': '='}, {'token': '2'}
    ],
    'order': {'column': 'c', 'direction': 'DESC'},
    'limit': '1'
}

>>> update_tokex.match("UPDATE test SET a=1 LIMIT 1")
{
    'table_name': 'test',
    'columns': [{'name': 'a', 'value': '1'}],
    'limit': '1'
}

>>> update_tokex.match("UPDATE test_table SET WHERE a > 1") is None # Missing a column to set
True
```

**Select Query**
```
>>> select_tokex = tokex.compile(r"""
    def join_condition {
        +(conditions:  <condition: !~(INNER)|(LEFT)|(WHERE)|(ORDER)|(LIMIT)~>)
    }
    def where_condition {
        +(conditions: <condition: !~(ORDER)|(LIMIT)~> )
    }

    'SELECT' ?(distinct: "DISTINCT")
        +(select_attributes: <name: !"from"> sep { ',' } )
    'FROM' <table: .>
    *(joins:
        {
            (inner: "INNER" "JOIN" <table: .> "ON" join_condition() )
            (left: "LEFT" "JOIN" <table: .> "ON" join_condition() )
        }
    )
    ?(where: "WHERE" where_condition() )
    ?(order: "ORDER" "BY" <order_by_column: .> <order_by_direction: ~(ASC)|(DESC)~> )
    ?("LIMIT" <limit: ~\\d+~> )
""")

>>> select_tokex.match("SELECT * FROM test limit 1")
{
    'select_attributes': [{'name': '*'}],
    'table': 'test',
    'limit': '1'
}

>>> select_tokex.match("""
    SELECT a, b, c
    FROM test_table
    INNER JOIN a ON a = t
    INNER JOIN b ON b = a
    LEFT JOIN c ON c = a
    WHERE a > 1 AND b < 2
    ORDER BY a DESC
    LIMIT 2
""")
{
    'select_attributes': [{'name': 'a'}, {'name': 'b'}, {'name': 'c'}],
    'table': 'test_table',
    'joins': [
        {
            'inner': {
                'table': 'a', 'conditions': [{'condition': 'a'}, {'condition': '='}, {'condition': 't'}]
            }
        },
        {
            'inner': {
                'table': 'b', 'conditions': [{'condition': 'b'}, {'condition': '='}, {'condition': 'a'}]
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
        'conditions': [
            {'condition': 'a'}, {'condition': '>'}, {'condition': '1'},
            {'condition': 'AND'},
            {'condition': 'b'}, {'condition': '<'}, {'condition': '2'}
        ]
    },
    'order': {
        'order_by_column': 'a', 'order_by_direction': 'DESC'
    },
    'limit': '2'
}

>>> select_tokex.match("SELECT FROM test") is None # Missing select columns
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
#### Grammar Notes
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
- Some flags are set by default; these can be overridden by passing a custom set of default flags to match/compile:
  - Case Insensitive (**i**)

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
>>> string_literal_tokex = tokex.compile("'abc' 'def' 'g'")
>>> string_literal_tokex.match("abc def g") # Matches
>>> string_literal_tokex.match("g def abc") is None # Does not match
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
>>> regular_expression_tokex = tokex.compile("~(yes)|(no)|(maybe)~")
>>> regular_expression_tokex.match("maybe") # Matches

>>> numeric_regular_expression_tokex = tokex.compile(r"~\\d+~")
>>> numeric_regular_expression_tokex.match("4570") # Matches
```

### Any String
Matches any non-whitespace input token.
Note: This element will not match a newline (if newlines have been [tokenized](#input-string-tokenization)).

#### Syntax
`.`

#### Valid Flags
- Quoted: **q**
  - `q.` - Matches any quoted (wrapped by either ' or ") non-whitespace input token
- Unquoted: **u**
  - `u.` - Matches any unquoted (not wrapped by either ' or ") non-whitespace input token

#### Examples
```
>>> any_string_tokex = tokex.compile(".")
>>> any_string_tokex.match("maybe") # Matches
>>> any_string_tokex.match("'ANYTHING'") # Matches
```

### Newline
Matches a newline in an input string .
Note that Newline elements will only match newlines in input strings if newlines are tokenized by setting `tokenize_newlines=True` on the tokenizer. See [Input String Tokenization](#input-string-tokenization)

#### Syntax
`$`

#### Examples
```
>>> newline_tokex = tokex.compile(". $ .", tokenizer=tokex.tokenizers.TokexTokenizer(tokenize_newlines=True))
>>> newline_tokex.match("something \n else ") # Matches
>>> newline_tokex.match("something else ") # Does not match
```

### Named Tokens
Matched tokens wrapped in a named token will have the matched token recorded in the nearest named section.
Note: Only singular elements (documented above, not below) can be wrapped inside a named token

#### Syntax
`<token-name: ...>`

#### Examples
```
>>> named_token_tokex = tokex.compile("<token: .>")
>>> named_token_tokex.match("some_token")
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
>>> named_grammar_tokex = tokex.compile("(test: 'a' <middle: .> 'c')")
>>> named_grammar_tokex.match("a b c") # Matches
{'test': {'middle': 'b'}}
>>> named_grammar_tokex.match("a b") # Does not match
```

### Zero Or One (optionally Named) Section
Acts the same way that a regular Named Section does, however will match an input string zero or one times.  In other words, the elements it contains are optional.
Note: A Zero Or One section can be given a name or not.  If it is, all the named tokens within it will be grouped up into a dictionary mapped to by the name you give the section.  If it isn't, all named matches will be populated in the nearest parent named grammar

#### Syntax
`?(name: ... )`
or
`?( ... )`


#### Examples
```
>>> zero_or_one_tokex = tokex.compile("'prefix' ?( <middle_element: !'suffix'>) 'suffix'")
>>> zero_or_one_tokex.match("prefix middle_token suffix") # Matches
{'middle_element': 'middle_token'}
>>> zero_or_one_tokex.match("prefix suffix") # Still matches

>>> zero_or_one_tokex = tokex.compile("'SELECT' ?(distinct: 'distinct')")
>>> zero_or_one_tokex.match("select distinct") # Matches
{'distinct': None}
>>> zero_or_one_tokex.match("select") # Matches
{}
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
>>> zero_or_one_grammar = tokex.compile("*(as: <a: 'a'>) *(bs: <b: 'b'>)")
>>> zero_or_one_grammar.match("a a b b b")
{'as': [{'a': 'a'}, {'a': 'a'}], 'bs': [{'b': 'b'}, {'b': 'b'}, {'b': 'b'}]}
>>> zero_or_one_grammar.match("b b")
{'bs': [{'b': 'b'}, {'b': 'b'}]}

>>> zero_or_one_grammar = tokex.compile("*(letters: <letter: .> sep { ',' })")
>>> zero_or_one_grammar.match("a, b, c")
{'letters': [{'letter': 'a'}, {'letter': 'b'}, {'letter': 'c'}]}
>>> zero_or_one_grammar.match("a, b c") # Does not match, as there's no , between b and c
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
>>> one_or_more_grammar = tokex.compile("+(as: <a: 'a'>) +(bs: <b: 'b'>)")
>>> one_or_more_grammar.match("a a b b b")
{'as': [{'a': 'a'}, {'a': 'a'}], 'bs': [{'b': 'b'}, {'b': 'b'}, {'b': 'b'}]}
>>> one_or_more_grammar.match("b b") # Does not match, as there are no a's

>>> one_or_more_grammar = tokex.compile("+(letters: <letter: .> sep { ',' })")
>>> one_or_more_grammar.match("a, b, c")
{'letters': [{'letter': 'a'}, {'letter': 'b'}, {'letter': 'c'}]}
>>> one_or_more_grammar.match("a, b c") # Does not match, as there's no , between b and c
```

### One of Set
Specifies that one grammar of the set of contained grammars should match the input string at the current position.
Will attempt to match each grammar in order until one matches.

#### Syntax
`{ ... }`

#### Examples
Match one grammar of a set, zero or many times:
```
>>> one_of_set_tokex = tokex.compile("""
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
>>> one_of_set_tokex.match("""
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

### Sub Grammars
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
