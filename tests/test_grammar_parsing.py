import tokex
import _test_case

class TestGrammarParsing(_test_case.TokexTestCase):

    def test_parse_tokens(self):
        grammar = """
            'a' "b" `c`
        """
        token_grammar = tokex.compile(grammar)

        self.assertIsNotNone(token_grammar.match('a b c'))
        self.assertIsNotNone(token_grammar.match('a b c '))
        self.assertIsNotNone(token_grammar.match(' a b c'))
        self.assertIsNotNone(token_grammar.match(' a  b  c '))

        self.assertIsNone(token_grammar.match("a b c d"))
        self.assertIsNone(token_grammar.match("c b c"))
        self.assertIsNone(token_grammar.match("a a c"))
        self.assertIsNone(token_grammar.match("a b b"))
        self.assertIsNone(token_grammar.match("a b C"))
        self.assertIsNone(token_grammar.match("a b"))
        self.assertIsNone(token_grammar.match("a"))
        self.assertIsNone(token_grammar.match(""))

        grammar = """
            _ _str_ _notstr_ _!a\_c_
        """
        regex_grammar = tokex.compile(grammar)

        self.assertIsNotNone(regex_grammar.match('anything "string" notstring nota_c'))
        self.assertIsNotNone(regex_grammar.match("anything 'string' notstring nota_c"))
        self.assertTrue(regex_grammar.grammar.match(["anything", "'string'", "notstring", "nota\\_c"], 0)[0])

        self.assertIsNone(regex_grammar.match('anything "string" notstring a_c'))
        self.assertIsNone(regex_grammar.match('anything "string" "notstring" nota_c'))
        self.assertIsNone(regex_grammar.match('anything "string" \'notstring\' nota_c'))
        self.assertIsNone(regex_grammar.match('anything string notstring nota_c'))

        self.assertIsNone(tokex.match("$caseSensitive$", "casesensitive"))
        self.assertIsNone(tokex.match("$caseSensitive$", "CASESENSITIVE"))
        self.assertIsNotNone(tokex.match("$caseSensitive$", "caseSensitive"))
        self.assertIsNotNone(tokex.match("^caseSensitive^", "casesensitive"))
        self.assertIsNotNone(tokex.match("^caseSensitive^", "CASESENSITIVE"))



    def test_parse_named_token(self):
        grammar = """
            <a1: 'a'>
            <a2: _>
            <a3: '>'>
            <a4: '<'>
            <a5: `>`>
            <a6: _!>_>
            <a7: 'q'>
            <a7: <b: 'b'>>
        """

        named_token_grammar = tokex.compile(grammar)

        self.assertDictEqual(named_token_grammar.match('a b > < > < q b'), {
            'a1': 'a',
            'a2': 'b',
            'a3': '>',
            'a4': '<',
            'a5': '>',
            'a6': '<',
            'a7': 'b'
        })

        self.assertIsNone(named_token_grammar.match(''))
        self.assertIsNone(named_token_grammar.match(' b > < > < q b'))
        self.assertIsNone(named_token_grammar.match('a b > < > < q'))
        self.assertIsNone(named_token_grammar.match('a b > < > > q b'))
        self.assertIsNone(named_token_grammar.match('b b > < > < q b'))

    def test_parse_named_grammar(self):
        grammar = """
            ( a:
                <a1: 'a'>
                <a2: 'b'>
                (a3: <a4: 'c'>)
            )
            (
             b:
                (c: (d: (e: <f: 'f'>) ) )
            )
        """

        named_grammar_grammar = tokex.compile(grammar)

        a = named_grammar_grammar.match('a b c f')
        b = {
            'a': {
                'a1': 'a',
                'a2': 'b',
                'a3': {'a': 'c'}
            },
            'b': {
                'c': {
                    'd': {
                        'e': {
                            'f': 'f'
                        }
                    }
                }
            }
        }

        self.assertDictEqual(named_grammar_grammar.match('a b c f'), {
            'a': {
                'a1': 'a',
                'a2': 'b',
                'a3': {'a4': 'c'}
            },
            'b': {
                'c': {
                    'd': {
                        'e': {
                            'f': 'f'
                        }
                    }
                }
            }
        })

        self.assertIsNone(named_grammar_grammar.match('a b c'))
        self.assertIsNone(named_grammar_grammar.match('a b f'))
        self.assertIsNone(named_grammar_grammar.match('f'))
        self.assertIsNone(named_grammar_grammar.match('a c f'))
        self.assertIsNone(named_grammar_grammar.match('a a b c f'))
        self.assertIsNone(named_grammar_grammar.match(''))

    def test_parse_zero_or_one(self):
        grammar = """
            (?'a')
            (?
                <b: 'b'>
            )
            (?
                (c: <c: 'c'>)
            )
            (?
                (?
                    (?
                        (?
                            <d: 'd'>
                        )
                    )
                )
            )
            (?
                (?
                    (?
                        (?
                            (e:<e: 'e'>)
                        )
                    )
                )
            )
        """

        zero_or_one_grammar = tokex.compile(grammar)

        self.assertDictEqual(zero_or_one_grammar.match('a b c d e'), {
            'b': 'b',
            'c': {'c': 'c'},
            'd': 'd',
            'e': {'e': 'e'}
        })

        self.assertDictEqual(zero_or_one_grammar.match('b c d e'), {
            'b': 'b',
            'c': {'c': 'c'},
            'd': 'd',
            'e': {'e': 'e'}
        })

        self.assertDictEqual(zero_or_one_grammar.match('c d e'), {
            'c': {'c': 'c'},
            'd': 'd',
            'e': {'e': 'e'}
        })

        self.assertDictEqual(zero_or_one_grammar.match('a b e'), {
            'b': 'b',
            'e': {'e': 'e'}
        })

        self.assertDictEqual(zero_or_one_grammar.match('d e'), {
            'd': 'd',
            'e': {'e': 'e'}
        })

        self.assertDictEqual(zero_or_one_grammar.match('e'), {
            'e': {'e': 'e'}
        })

        self.assertDictEqual(zero_or_one_grammar.match(''), {})

        self.assertIsNone(zero_or_one_grammar.match('f'))
        self.assertIsNone(zero_or_one_grammar.match('a b c d e f'))
        self.assertIsNone(zero_or_one_grammar.match('a b c g e f'))


    def test_parse_zero_or_more(self):
        grammar = """
            (*
                'a'
            )
            (*
                <b: 'b'>
            )
            (*
                (c:
                   <c2: 'c2'>
                   <c3: 'c3'>
                )
            )
            (*
                (*
                    (*
                        (*
                            <d: 'd'>
                        )
                    )
                )
            )
            (*
                (*
                    (*
                        (*
                            (e:<e: 'e'>)
                        )
                    )
                )
            )
        """

        zero_or_more_grammar = tokex.compile(grammar)

        self.assertDictEqual(zero_or_more_grammar.match('a b c2 c3 d e'), {
            'b': ['b'],
            'c': [{'c2': 'c2', 'c3': 'c3'}],
            'd': [[[['d']]]],
            'e': [[[[{'e': 'e'}]]]]
        })

        self.assertDictEqual(zero_or_more_grammar.match('a b d e'), {
            'b': ['b'],
            'd': [[[['d']]]],
            'e': [[[[{'e': 'e'}]]]]
        })

        self.assertDictEqual(zero_or_more_grammar.match('b c2 c3 d e'), {
            'b': ['b'],
            'c': [{'c2': 'c2', 'c3': 'c3'}],
            'd': [[[['d']]]],
            'e': [[[[{'e': 'e'}]]]]
        })

        self.assertDictEqual(zero_or_more_grammar.match('c2 c3 d e'), {
            'c': [{'c2': 'c2', 'c3': 'c3'}],
            'd': [[[['d']]]],
            'e': [[[[{'e': 'e'}]]]]
        })

        self.assertDictEqual(zero_or_more_grammar.match('a b e'), {
            'b': ['b'],
            'e': [[[[{'e': 'e'}]]]]
        })

        self.assertDictEqual(zero_or_more_grammar.match('d e'), {
            'd': [[[['d']]]],
            'e': [[[[{'e': 'e'}]]]]
        })

        self.assertDictEqual(zero_or_more_grammar.match('e'), {
            'e': [[[[{'e': 'e'}]]]]
        })

        self.assertDictEqual(zero_or_more_grammar.match('a a a a a a a a a a b b b d d e e'), {
            'b': ['b', 'b', 'b'],
            'd': [[[['d', 'd']]]],
            'e': [[[[{'e': 'e'}, {'e': 'e'}]]]]
        })

        self.assertDictEqual(zero_or_more_grammar.match('a a a a a a a a a a e e e e e e e e'), {
            'e': [[[[{'e': 'e'}, {'e': 'e'}, {'e': 'e'}, {'e': 'e'}, {'e': 'e'}, {'e': 'e'}, {'e': 'e'}, {'e': 'e'}]]]]
        })

        self.assertDictEqual(zero_or_more_grammar.match('c2 c3 c2 c3 c2 c3'), {
            'c': [{'c2': 'c2', 'c3': 'c3'}, {'c2': 'c2', 'c3': 'c3'}, {'c2': 'c2', 'c3': 'c3'}],
        })

        self.assertDictEqual(zero_or_more_grammar.match(''), {})

        self.assertIsNone(zero_or_more_grammar.match('f'))
        self.assertIsNone(zero_or_more_grammar.match('a b c d e f'))
        self.assertIsNone(zero_or_more_grammar.match('a b c g e f'))


        grammar = """
            (*
                <a:'a'> [<b:'b'>]
            )
        """

        zero_or_more_grammar = tokex.compile(grammar)

        self.assertDictEqual(zero_or_more_grammar.match('a'), {'a': ['a']})
        self.assertIsNone(zero_or_more_grammar.match('a b'))
        self.assertDictEqual(zero_or_more_grammar.match('a b a'), {'a': ['a', 'a'], 'b': ['b']})
        self.assertIsNone(zero_or_more_grammar.match('a b a b'))
        self.assertIsNone(zero_or_more_grammar.match('b'))
        self.assertIsNone(zero_or_more_grammar.match('a a'))


    def test_parse_one_or_more(self):
        grammar = """
            (+
                'a'
            )
            (+
                <b: 'b'>
            )
            (+
                (c:
                   <c2: 'c2'>
                   <c3: 'c3'>
                )
            )
            (+
                (+
                    (+
                        (+
                            <d: 'd'>
                        )
                    )
                )
            )
            (+
                (+
                    (+
                        (+
                            (e:<e: 'e'>)
                        )
                    )
                )
            )
        """

        one_or_more_grammar = tokex.compile(grammar)

        self.assertDictEqual(one_or_more_grammar.match('a b c2 c3 d e'), {
            'b': ['b'],
            'c': [{'c2': 'c2', 'c3': 'c3'}],
            'd': [[[['d']]]],
            'e': [[[[{'e': 'e'}]]]]
        })


        grammar = "(+ <a:'a'> [<b:'b'>])"

        one_or_more_grammar = tokex.compile(grammar)

        self.assertDictEqual(one_or_more_grammar.match('a'), {'a': ['a']})
        self.assertIsNone(one_or_more_grammar.match('a b'))
        self.assertDictEqual(one_or_more_grammar.match('a b a'), {'a': ['a', 'a'], 'b': ['b']})

        self.assertIsNone(one_or_more_grammar.match(''), {})
        self.assertIsNone(one_or_more_grammar.match('f'))
        self.assertIsNone(one_or_more_grammar.match('b'))
        self.assertIsNone(one_or_more_grammar.match('a a'))
        self.assertIsNone(one_or_more_grammar.match('a b'))
        self.assertIsNone(one_or_more_grammar.match('a b a b'))
        self.assertIsNone(one_or_more_grammar.match('b'))
        self.assertIsNone(one_or_more_grammar.match('a a'))


        grammar = """
            (+
                <a:'a'> [<b:'b'>]
            )
        """

        one_or_more_grammar = tokex.compile(grammar)

        self.assertDictEqual(one_or_more_grammar.match('a'), {'a': ['a']})
        self.assertIsNone(one_or_more_grammar.match('a b'))
        self.assertDictEqual(one_or_more_grammar.match('a b a'), {'a': ['a', 'a'], 'b': ['b']})
        self.assertIsNone(one_or_more_grammar.match('a b a b'))

        self.assertIsNone(one_or_more_grammar.match('a a'))
        self.assertIsNone(one_or_more_grammar.match('b'))


    def test_parse_one_of_set(self):
        grammar = """
            {
                <a:'a'>
                (b: <b1:'b1'> 'b2')
                {
                    <c:'c'>
                    'd'
                    'e'
                }
            }
        """

        one_of_set_grammar = tokex.compile(grammar)

        self.assertDictEqual(one_of_set_grammar.match('a'), {'a': 'a'})
        self.assertDictEqual(one_of_set_grammar.match('b1 b2'), {'b': {'b1': 'b1'}})
        self.assertDictEqual(one_of_set_grammar.match('c'), {'c': 'c'})
        self.assertDictEqual(one_of_set_grammar.match('d'), {})
        self.assertDictEqual(one_of_set_grammar.match('e'), {})

        self.assertIsNone(one_of_set_grammar.match(''))
        self.assertIsNone(one_of_set_grammar.match('b3'))
        self.assertIsNone(one_of_set_grammar.match('b1'))
        self.assertIsNone(one_of_set_grammar.match('b2'))

        grammar = """
            (*
                {
                    <a:'a'>
                    (b: <b1:'b1'> <b2:'b2'>)
                    {
                        <c:'c'>
                        'd'
                        'e'
                    }
                }
            )
        """

        one_of_set_grammar = tokex.compile(grammar)

        self.assertDictEqual(one_of_set_grammar.match('a a a a c c c d d d d d e e e e e e b1 b2 a a a b1 b2'), {
            'a': ['a', 'a', 'a', 'a', 'a', 'a', 'a'],
            'b': [{'b1': 'b1', 'b2': 'b2'}, {'b1': 'b1', 'b2': 'b2'}],
            'c': ['c', 'c', 'c']
        })

        self.assertDictEqual(one_of_set_grammar.match(''), {})
        self.assertDictEqual(one_of_set_grammar.match('e'), {})
