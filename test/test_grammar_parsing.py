import tokex
import _test_case

class TestGrammarParsing(_test_case.TokexTestCase):

    def test_parse_tokens(self):
        grammar = """
            'a' "b" s'c'
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
            . q. u.!'a_c'
        """
        regex_grammar = tokex.compile(grammar)

        self.assertIsNotNone(regex_grammar.match('anything "string" notstring nota_c'))
        self.assertIsNotNone(regex_grammar.match("anything 'string' notstring nota_c"))
        self.assertTrue(regex_grammar._grammar.apply(["anything", "'string'", "notstring", "nota\\_c"], 0)[0])

        self.assertIsNone(regex_grammar.match('anything "string" notstring a_c'))
        self.assertIsNone(regex_grammar.match('anything "string" "notstring" nota_c'))
        self.assertIsNone(regex_grammar.match('anything "string" \'notstring\' nota_c'))
        self.assertIsNone(regex_grammar.match('anything string notstring nota_c'))

        self.assertIsNone(tokex.match("s~caseSensitive~", "casesensitive"))
        self.assertIsNone(tokex.match("s~caseSensitive~", "CASESENSITIVE"))
        self.assertIsNotNone(tokex.match("i~caseSensitive~", "caseSensitive"))
        self.assertIsNotNone(tokex.match("i~caseSensitive~", "casesensitive"))
        self.assertIsNotNone(tokex.match("i~caseSensitive~", "CASESENSITIVE"))

        # Test newlines
        grammar = "'test' $ 'test'"
        newline_grammar = tokex.compile(grammar, tokenizer=tokex.tokenizers.TokexTokenizer(tokenize_newlines=True))
        self.assertIsNotNone(newline_grammar.match("test \n test"))
        self.assertIsNone(newline_grammar.match("test \\n test"))


    def test_parse_named_token(self):
        grammar = """
            <a1: 'a'>
            <a2: .>
            <a3: '>'>
            <a4: '<'>
            <a5: i'>'>
            <q:>
            <q2: >
            <a6: !'>'>
            <a7: 'q'>
            <a7: 'b'>
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
            (c: 'c' 'c' 'c')
        """

        named_grammar_grammar = tokex.compile(grammar)

        self.assertDictEqual(named_grammar_grammar.match('a b c f c c c'), {
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
            },
            'c': None
        })

        self.assertIsNone(named_grammar_grammar.match('a b c'))
        self.assertIsNone(named_grammar_grammar.match('a b f'))
        self.assertIsNone(named_grammar_grammar.match('f'))
        self.assertIsNone(named_grammar_grammar.match('a c f'))
        self.assertIsNone(named_grammar_grammar.match('a a b c f'))
        self.assertIsNone(named_grammar_grammar.match(''))

    def test_parse_zero_or_one(self):
        grammar = """
            ?(a: 'a')
            ?(b:
                <bi: 'b'>
            )
            ?(c:
                (ci: <cii: 'c'>)
            )
            ?(d:
                ?(di:
                    ?(dii:
                        ?(diii:
                            <dv: 'd'>
                        )
                    )
                )
            )
            ?(e:
                ?(ei:
                    ?(eii:
                        ?(eiii:
                            (ev:<evi: 'e'>)
                        )
                    )
                )
            )
            ?(
                ?(
                    <outer: 'q'>
                )
                ?()
            )
        """

        zero_or_one_grammar = tokex.compile(grammar)

        self.assertDictEqual(zero_or_one_grammar.match('a b c d e q'), {
            'a': None,
            'b': {'bi': 'b'},
            'c': {'ci': {'cii': 'c'}},
            'd': {'di': {'dii': {'diii': {'dv': 'd'}}}},
            'e': {'ei': {'eii': {'eiii': {'ev': {'evi': 'e'}}}}},
            'outer': 'q'
        })

        self.assertDictEqual(zero_or_one_grammar.match('b c d e'), {
            'b': {'bi': 'b'},
            'c': {'ci': {'cii': 'c'}},
            'd': {'di': {'dii': {'diii': {'dv': 'd'}}}},
            'e': {'ei': {'eii': {'eiii': {'ev': {'evi': 'e'}}}}},
        })

        self.assertDictEqual(zero_or_one_grammar.match('c d e'), {
            'c': {'ci': {'cii': 'c'}},
            'd': {'di': {'dii': {'diii': {'dv': 'd'}}}},
            'e': {'ei': {'eii': {'eiii': {'ev': {'evi': 'e'}}}}},
        })

        self.assertDictEqual(zero_or_one_grammar.match('a b e'), {
            'a': None,
            'b': {'bi': 'b'},
            'e': {'ei': {'eii': {'eiii': {'ev': {'evi': 'e'}}}}},
        })

        self.assertDictEqual(zero_or_one_grammar.match('d e'), {
            'd': {'di': {'dii': {'diii': {'dv': 'd'}}}},
            'e': {'ei': {'eii': {'eiii': {'ev': {'evi': 'e'}}}}},
        })

        self.assertDictEqual(zero_or_one_grammar.match('e'), {
            'e': {'ei': {'eii': {'eiii': {'ev': {'evi': 'e'}}}}},
        })

        self.assertDictEqual(zero_or_one_grammar.match('q'), {
            'outer': 'q'
        })

        self.assertDictEqual(zero_or_one_grammar.match(''), {})

        self.assertIsNone(zero_or_one_grammar.match('f'))
        self.assertIsNone(zero_or_one_grammar.match('a b c d e f'))
        self.assertIsNone(zero_or_one_grammar.match('a b c g e f'))


    def test_parse_zero_or_more(self):
        grammar = """
            *(a:
                'a'
            )
            *(b:
                <bi: 'b'>
            )
            *(c:
                (c1:
                   <c2: 'c2'>
                   <c3: 'c3'>
                )
            )
            *(d:
                *(di:
                    *(dii:
                        *(diii:
                            <d: 'd'>
                        )
                    )
                )
            )
            *(e:
                *(ei:
                    *(eii:
                        *(eiii:
                            (e:<e: 'e'>)
                        )
                    )
                )
            )
        """

        zero_or_more_grammar = tokex.compile(grammar)

        self.assertDictEqual(zero_or_more_grammar.match('a b c2 c3 d e'), {
            'a': [None],
            'b': [{'bi': 'b'}],
            'c': [{'c1': {'c2': 'c2', 'c3': 'c3'}}],
            'd': [{'di': [{'dii': [{'diii': [{'d': 'd'}]}]}]}],
            'e': [{'ei': [{'eii': [{'eiii': [{'e': {'e': 'e'}}]}]}]}],
        })

        self.assertDictEqual(zero_or_more_grammar.match('a b d e'), {
            'a': [None],
            'b': [{'bi': 'b'}],
            'd': [{'di': [{'dii': [{'diii': [{'d': 'd'}]}]}]}],
            'e': [{'ei': [{'eii': [{'eiii': [{'e': {'e': 'e'}}]}]}]}],
        })

        self.assertDictEqual(zero_or_more_grammar.match('b c2 c3 d e'), {
            'b': [{'bi': 'b'}],
            'c': [{'c1': {'c2': 'c2', 'c3': 'c3'}}],
            'd': [{'di': [{'dii': [{'diii': [{'d': 'd'}]}]}]}],
            'e': [{'ei': [{'eii': [{'eiii': [{'e': {'e': 'e'}}]}]}]}],
        })

        self.assertDictEqual(zero_or_more_grammar.match('c2 c3 d e'), {
            'c': [{'c1': {'c2': 'c2', 'c3': 'c3'}}],
            'd': [{'di': [{'dii': [{'diii': [{'d': 'd'}]}]}]}],
            'e': [{'ei': [{'eii': [{'eiii': [{'e': {'e': 'e'}}]}]}]}],
        })

        self.assertDictEqual(zero_or_more_grammar.match('a b e'), {
            'a': [None],
            'b': [{'bi': 'b'}],
            'e': [{'ei': [{'eii': [{'eiii': [{'e': {'e': 'e'}}]}]}]}],
        })

        self.assertDictEqual(zero_or_more_grammar.match('d e'), {
            'd': [{'di': [{'dii': [{'diii': [{'d': 'd'}]}]}]}],
            'e': [{'ei': [{'eii': [{'eiii': [{'e': {'e': 'e'}}]}]}]}],
        })

        self.assertDictEqual(zero_or_more_grammar.match('e'), {
            'e': [{'ei': [{'eii': [{'eiii': [{'e': {'e': 'e'}}]}]}]}],
        })

        self.assertDictEqual(zero_or_more_grammar.match('a a a a a a a a a a b b b d d e e'), {
            'a': [None] * 10,
            'b': [{'bi': 'b'}, {'bi': 'b'}, {'bi': 'b'}],
            'd': [{'di': [{'dii': [{'diii': [{'d': 'd'}, {'d': 'd'}]}]}]}],
            'e': [{'ei': [{'eii': [{'eiii': [{'e': {'e': 'e'}}, {'e': {'e': 'e'}}]}]}]}],
        })

        self.assertDictEqual(zero_or_more_grammar.match('a a a a a a a a a a e e e e e e e'), {
            'a': [None] * 10,
            'e': [{'ei': [{'eii': [{'eiii': [{'e': {'e': 'e'}}, {'e': {'e': 'e'}}, {'e': {'e': 'e'}}, {'e': {'e': 'e'}},
                  {'e': {'e': 'e'}}, {'e': {'e': 'e'}}, {'e': {'e': 'e'}}]}]}]}],
        })

        self.assertDictEqual(zero_or_more_grammar.match('c2 c3 c2 c3 c2 c3'), {
            'c': [{'c1': {'c2': 'c2', 'c3': 'c3'}}, {'c1': {'c2': 'c2', 'c3': 'c3'}}, {'c1': {'c2': 'c2', 'c3': 'c3'}}],
        })

        self.assertDictEqual(zero_or_more_grammar.match(''), {})

        self.assertIsNone(zero_or_more_grammar.match('f'))
        self.assertIsNone(zero_or_more_grammar.match('a b c d e f'))
        self.assertIsNone(zero_or_more_grammar.match('a b c g e f'))


        grammar = """
            *(_:
                <a:'a'> sep{<b:'b'>}
            )
        """

        zero_or_more_grammar = tokex.compile(grammar)

        self.assertDictEqual(zero_or_more_grammar.match('a'), {'_': [{'a': 'a'}]})
        self.assertIsNone(zero_or_more_grammar.match('a b'))
        self.assertDictEqual(zero_or_more_grammar.match('a b a'), {'_': [{'a': 'a', 'b': 'b'}, {'a': 'a'}]})
        self.assertIsNone(zero_or_more_grammar.match('a b a b'))
        self.assertIsNone(zero_or_more_grammar.match('b'))
        self.assertIsNone(zero_or_more_grammar.match('a a'))


    def test_parse_one_or_more(self):
        grammar = """
            +(a:
                'a'
            )
            +(b:
                <bi: 'b'>
            )
            +(c:
                (c1:
                   <c2: 'c2'>
                   <c3: 'c3'>
                )
            )
            +(d:
                +(di:
                    +(dii:
                        +(diii:
                            <d: 'd'>
                        )
                    )
                )
            )
            +(e:
                +(ei:
                    +(eii:
                        +(eiii:
                            (e:<e: 'e'>)
                        )
                    )
                )
            )
        """

        one_or_more_grammar = tokex.compile(grammar)

        self.assertDictEqual(one_or_more_grammar.match('a b c2 c3 d e'), {
            'a': [None],
            'b': [{'bi': 'b'}],
            'c': [{'c1': {'c2': 'c2', 'c3': 'c3'}}],
            'd': [{'di': [{'dii': [{'diii': [{'d': 'd'}]}]}]}],
            'e': [{'ei': [{'eii': [{'eiii': [{'e': {'e': 'e'}}]}]}]}],
        })


        grammar = "+(_: <a:'a'> sep { <b:'b'> })"

        one_or_more_grammar = tokex.compile(grammar)

        self.assertDictEqual(one_or_more_grammar.match('a'), {'_': [{'a': 'a'}]})
        self.assertIsNone(one_or_more_grammar.match('a b'))
        self.assertDictEqual(one_or_more_grammar.match('a b a'), {'_': [{'a': 'a', 'b': 'b'}, {'a': 'a'}]})

        self.assertIsNone(one_or_more_grammar.match(''))
        self.assertIsNone(one_or_more_grammar.match('f'))
        self.assertIsNone(one_or_more_grammar.match('b'))
        self.assertIsNone(one_or_more_grammar.match('a a'))
        self.assertIsNone(one_or_more_grammar.match('a b'))
        self.assertIsNone(one_or_more_grammar.match('a b a b'))
        self.assertIsNone(one_or_more_grammar.match('b'))
        self.assertIsNone(one_or_more_grammar.match('a a'))


        grammar = """
            +(_:
                <a:'a'> sep {<b:'b'> }
            )
        """

        one_or_more_grammar = tokex.compile(grammar)

        self.assertDictEqual(one_or_more_grammar.match('a'), {'_': [{'a': 'a'}]})
        self.assertIsNone(one_or_more_grammar.match('a b'))
        self.assertDictEqual(one_or_more_grammar.match('a b a'), {'_': [{'a': 'a', 'b': 'b'}, {'a': 'a'}]})
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
            *(_:
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
            '_': [
                {'a': 'a'}, {'a': 'a'}, {'a': 'a'}, {'a': 'a'},
                {'c': 'c'}, {'c': 'c'}, {'c': 'c'},
                None, None, None, None, None, None, None, None, None, None, None,
                {'b': {'b1': 'b1', 'b2': 'b2'}},
                {'a': 'a'}, {'a': 'a'}, {'a': 'a'},
                {'b': {'b1': 'b1', 'b2': 'b2'}}
            ]
        })

        self.assertDictEqual(one_of_set_grammar.match(''), {})
        self.assertDictEqual(one_of_set_grammar.match('e'), {'_': [None]})
