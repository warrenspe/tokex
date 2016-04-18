# Project imports
import Tokex
import tests

class TestGrammarParsing(tests.TokexTestCase):

    def testParseTokens(self):
        grammar = """
            'a' "b" `c`
        """
        tokenGrammar = Tokex.compile(grammar)

        self.assertIsNotNone(tokenGrammar.match('a b c'))
        self.assertIsNotNone(tokenGrammar.match('a b c '))
        self.assertIsNotNone(tokenGrammar.match(' a b c'))
        self.assertIsNotNone(tokenGrammar.match(' a  b  c '))

        self.assertIsNone(tokenGrammar.match("a b c d"))
        self.assertIsNone(tokenGrammar.match("c b c"))
        self.assertIsNone(tokenGrammar.match("a a c"))
        self.assertIsNone(tokenGrammar.match("a b b"))
        self.assertIsNone(tokenGrammar.match("a b C"))
        self.assertIsNone(tokenGrammar.match("a b"))
        self.assertIsNone(tokenGrammar.match("a"))
        self.assertIsNone(tokenGrammar.match(""))

        grammar = """
            _ _str_ _notstr_ _!a\_c_
        """
        regexGrammar = Tokex.compile(grammar)

        self.assertIsNotNone(regexGrammar.match('anything "string" notstring nota_c'))
        self.assertIsNotNone(regexGrammar.match("anything 'string' notstring nota_c"))
        self.assertTrue(regexGrammar.grammar.match(["anything", "'string'", "notstring", "nota\\_c"], 0)[0])

        self.assertIsNone(regexGrammar.match('anything "string" notstring a_c'))
        self.assertIsNone(regexGrammar.match('anything "string" "notstring" nota_c'))
        self.assertIsNone(regexGrammar.match('anything "string" \'notstring\' nota_c'))
        self.assertIsNone(regexGrammar.match('anything string notstring nota_c'))


    def testParseNamedToken(self):
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

        namedTokenGrammar = Tokex.compile(grammar)

        self.assertDictEqual(namedTokenGrammar.match('a b > < > < q b'), {
            'a1': 'a',
            'a2': 'b',
            'a3': '>',
            'a4': '<',
            'a5': '>',
            'a6': '<',
            'a7': 'b'
        })

        self.assertIsNone(namedTokenGrammar.match(''))
        self.assertIsNone(namedTokenGrammar.match(' b > < > < q b'))
        self.assertIsNone(namedTokenGrammar.match('a b > < > < q'))
        self.assertIsNone(namedTokenGrammar.match('a b > < > > q b'))
        self.assertIsNone(namedTokenGrammar.match('b b > < > < q b'))

    def testParseNamedGrammar(self):
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

        namedGrammarGrammar = Tokex.compile(grammar)

        a = namedGrammarGrammar.match('a b c f')
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

        self.assertDictEqual(namedGrammarGrammar.match('a b c f'), {
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

        self.assertIsNone(namedGrammarGrammar.match('a b c'))
        self.assertIsNone(namedGrammarGrammar.match('a b f'))
        self.assertIsNone(namedGrammarGrammar.match('f'))
        self.assertIsNone(namedGrammarGrammar.match('a c f'))
        self.assertIsNone(namedGrammarGrammar.match('a a b c f'))
        self.assertIsNone(namedGrammarGrammar.match(''))

    def testParseZeroOrOne(self):
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

        zeroOrOneGrammar = Tokex.compile(grammar)

        self.assertDictEqual(zeroOrOneGrammar.match('a b c d e'), {
            'b': 'b',
            'c': {'c': 'c'},
            'd': 'd',
            'e': {'e': 'e'}
        })

        self.assertDictEqual(zeroOrOneGrammar.match('b c d e'), {
            'b': 'b',
            'c': {'c': 'c'},
            'd': 'd',
            'e': {'e': 'e'}
        })

        self.assertDictEqual(zeroOrOneGrammar.match('c d e'), {
            'c': {'c': 'c'},
            'd': 'd',
            'e': {'e': 'e'}
        })

        self.assertDictEqual(zeroOrOneGrammar.match('a b e'), {
            'b': 'b',
            'e': {'e': 'e'}
        })

        self.assertDictEqual(zeroOrOneGrammar.match('d e'), {
            'd': 'd',
            'e': {'e': 'e'}
        })

        self.assertDictEqual(zeroOrOneGrammar.match('e'), {
            'e': {'e': 'e'}
        })

        self.assertDictEqual(zeroOrOneGrammar.match(''), {})

        self.assertIsNone(zeroOrOneGrammar.match('f'))
        self.assertIsNone(zeroOrOneGrammar.match('a b c d e f'))
        self.assertIsNone(zeroOrOneGrammar.match('a b c g e f'))


    def testParseZeroOrMore(self):
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

        zeroOrMoreGrammar = Tokex.compile(grammar)

        self.assertDictEqual(zeroOrMoreGrammar.match('a b c2 c3 d e'), {
            'b': ['b'],
            'c': [{'c2': 'c2', 'c3': 'c3'}],
            'd': [[[['d']]]],
            'e': [[[[{'e': 'e'}]]]]
        })

        self.assertDictEqual(zeroOrMoreGrammar.match('a b d e'), {
            'b': ['b'],
            'd': [[[['d']]]],
            'e': [[[[{'e': 'e'}]]]]
        })

        self.assertDictEqual(zeroOrMoreGrammar.match('b c2 c3 d e'), {
            'b': ['b'],
            'c': [{'c2': 'c2', 'c3': 'c3'}],
            'd': [[[['d']]]],
            'e': [[[[{'e': 'e'}]]]]
        })

        self.assertDictEqual(zeroOrMoreGrammar.match('c2 c3 d e'), {
            'c': [{'c2': 'c2', 'c3': 'c3'}],
            'd': [[[['d']]]],
            'e': [[[[{'e': 'e'}]]]]
        })

        self.assertDictEqual(zeroOrMoreGrammar.match('a b e'), {
            'b': ['b'],
            'e': [[[[{'e': 'e'}]]]]
        })

        self.assertDictEqual(zeroOrMoreGrammar.match('d e'), {
            'd': [[[['d']]]],
            'e': [[[[{'e': 'e'}]]]]
        })

        self.assertDictEqual(zeroOrMoreGrammar.match('e'), {
            'e': [[[[{'e': 'e'}]]]]
        })

        self.assertDictEqual(zeroOrMoreGrammar.match('a a a a a a a a a a b b b d d e e'), {
            'b': ['b', 'b', 'b'],
            'd': [[[['d', 'd']]]],
            'e': [[[[{'e': 'e'}, {'e': 'e'}]]]]
        })

        self.assertDictEqual(zeroOrMoreGrammar.match('a a a a a a a a a a e e e e e e e e'), {
            'e': [[[[{'e': 'e'}, {'e': 'e'}, {'e': 'e'}, {'e': 'e'}, {'e': 'e'}, {'e': 'e'}, {'e': 'e'}, {'e': 'e'}]]]]
        })

        self.assertDictEqual(zeroOrMoreGrammar.match('c2 c3 c2 c3 c2 c3'), {
            'c': [{'c2': 'c2', 'c3': 'c3'}, {'c2': 'c2', 'c3': 'c3'}, {'c2': 'c2', 'c3': 'c3'}],
        })

        self.assertDictEqual(zeroOrMoreGrammar.match(''), {})

        self.assertIsNone(zeroOrMoreGrammar.match('f'))
        self.assertIsNone(zeroOrMoreGrammar.match('a b c d e f'))
        self.assertIsNone(zeroOrMoreGrammar.match('a b c g e f'))


        grammar = """
            (*
                <a:'a'> [<b:'b'>]
            )
        """

        zeroOrMoreGrammar = Tokex.compile(grammar)

        self.assertDictEqual(zeroOrMoreGrammar.match('a'), {'a': ['a']})
        self.assertIsNone(zeroOrMoreGrammar.match('a b'))
        self.assertDictEqual(zeroOrMoreGrammar.match('a b a'), {'a': ['a', 'a'], 'b': ['b']})
        self.assertIsNone(zeroOrMoreGrammar.match('a b a b'))
        self.assertIsNone(zeroOrMoreGrammar.match('b'))
        self.assertIsNone(zeroOrMoreGrammar.match('a a'))


    def testParseOneOrMore(self):
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

        oneOrMoreGrammar = Tokex.compile(grammar)

        self.assertDictEqual(oneOrMoreGrammar.match('a b c2 c3 d e'), {
            'b': ['b'],
            'c': [{'c2': 'c2', 'c3': 'c3'}],
            'd': [[[['d']]]],
            'e': [[[[{'e': 'e'}]]]]
        })


        grammar = "(+ <a:'a'> [<b:'b'>])"

        oneOrMoreGrammar = Tokex.compile(grammar)

        self.assertDictEqual(oneOrMoreGrammar.match('a'), {'a': ['a']})
        self.assertIsNone(oneOrMoreGrammar.match('a b'))
        self.assertDictEqual(oneOrMoreGrammar.match('a b a'), {'a': ['a', 'a'], 'b': ['b']})

        self.assertIsNone(oneOrMoreGrammar.match(''), {})
        self.assertIsNone(oneOrMoreGrammar.match('f'))
        self.assertIsNone(oneOrMoreGrammar.match('b'))
        self.assertIsNone(oneOrMoreGrammar.match('a a'))
        self.assertIsNone(oneOrMoreGrammar.match('a b'))
        self.assertIsNone(oneOrMoreGrammar.match('a b a b'))
        self.assertIsNone(oneOrMoreGrammar.match('b'))
        self.assertIsNone(oneOrMoreGrammar.match('a a'))


        grammar = """
            (+
                <a:'a'> [<b:'b'>]
            )
        """

        oneOrMoreGrammar = Tokex.compile(grammar)

        self.assertDictEqual(oneOrMoreGrammar.match('a'), {'a': ['a']})
        self.assertIsNone(oneOrMoreGrammar.match('a b'))
        self.assertDictEqual(oneOrMoreGrammar.match('a b a'), {'a': ['a', 'a'], 'b': ['b']})
        self.assertIsNone(oneOrMoreGrammar.match('a b a b'))

        self.assertIsNone(oneOrMoreGrammar.match('a a'))
        self.assertIsNone(oneOrMoreGrammar.match('b'))


    def testParseOneOfSet(self):
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

        oneOfSetGrammar = Tokex.compile(grammar)

        self.assertDictEqual(oneOfSetGrammar.match('a'), {'a': 'a'})
        self.assertDictEqual(oneOfSetGrammar.match('b1 b2'), {'b': {'b1': 'b1'}})
        self.assertDictEqual(oneOfSetGrammar.match('c'), {'c': 'c'})
        self.assertDictEqual(oneOfSetGrammar.match('d'), {})
        self.assertDictEqual(oneOfSetGrammar.match('e'), {})

        self.assertIsNone(oneOfSetGrammar.match(''))
        self.assertIsNone(oneOfSetGrammar.match('b3'))
        self.assertIsNone(oneOfSetGrammar.match('b1'))
        self.assertIsNone(oneOfSetGrammar.match('b2'))

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

        oneOfSetGrammar = Tokex.compile(grammar)

        self.assertDictEqual(oneOfSetGrammar.match('a a a a c c c d d d d d e e e e e e b1 b2 a a a b1 b2'), {
            'a': ['a', 'a', 'a', 'a', 'a', 'a', 'a'],
            'b': [{'b1': 'b1', 'b2': 'b2'}, {'b1': 'b1', 'b2': 'b2'}],
            'c': ['c', 'c', 'c']
        })

        self.assertDictEqual(oneOfSetGrammar.match(''), {})
        self.assertDictEqual(oneOfSetGrammar.match('e'), {})
