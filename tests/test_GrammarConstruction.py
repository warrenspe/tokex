# Standard imports
import re

# Project imports
import utils._Grammar as Grammar
import tests

class TestGrammarConstruction(tests.TokexTestCase):

    def testTokenizeGrammar(self):
        grammarString = r"""
            {{ 'a' 'b' 'c' }}
            [[ 'd' 'e' 'f' ]]
            (( 'g' 'h' 'i' ))
            ( abc: 'abc' '123')
            (
             def: 'def' '456' )
            (ghi: 'ghi' '789')
            < abc: '123'>
            <
             def: '456' >
            <ghi: '789'>
            @ abc: '123'@@
            @
             def: '456' @@
            @ghi: '789'@@
            _!abc_
            _! abc _
            _!abc \_ def_
            _notstr_
            _str_
            _
            ^someRegex^
            ^ someRegex^
            ^someRegex ^
            ^ someRegex ^
            $AnotherRegex$
            $AnotherRegex $
            $ AnotherRegex$
            $ AnotherRegex $
            "string"
            " string "
            "str ing"
            "str'ing"
            "str\"ing"
            ""
            'string'
            ' string '
            'str ing'
            'str"ing'
            'str\'ing'
            ''
            `string`
            ` string `
            `str ing`
            `str'ing`
            `str"ing`
            `str\`ing`
            ``
        """

        grammarTokens = Grammar._tokenizeGrammar(grammarString)

        self.assertEqual(grammarTokens, [
            "{{", "'a'", "'b'", "'c'", "}}",
            "[[", "'d'", "'e'", "'f'", "]]",
            "((", "'g'", "'h'", "'i'", "))",
            "( abc:", "'abc'", "'123'", ")",
            "(\n             def:", "'def'", "'456'", ")",
            "(ghi:", "'ghi'", "'789'", ")",
            "< abc:", "'123'", ">",
            "<\n             def:", "'456'", ">",
            "<ghi:", "'789'", ">",
            "@ abc:", "'123'", "@@",
            "@\n             def:", "'456'", "@@",
            "@ghi:", "'789'", "@@",
            "_!abc_", "_! abc _", "_!abc _ def_",
            "_notstr_", "_str_", "_",
            "^someRegex^", "^ someRegex^", "^someRegex ^", "^ someRegex ^",
            "$AnotherRegex$", "$AnotherRegex $", "$ AnotherRegex$", "$ AnotherRegex $",
            '"string"', '" string "', '"str ing"', '"str\'ing"', '"str"ing"', '""',
            "'string'", "' string '", "'str ing'", "'str\"ing'", "'str'ing'", "''",
            "`string`", "` string `", "`str ing`", "`str'ing`", '`str"ing`', "`str`ing`", "``",
        ])

    def testParseToken(self):
        grammar = Grammar.constructGrammar(r"""
            "a" "a b" 'c' 'efg' `h` `i j k` ^l^ ^m n o^ $p$ $q r s$
            "a\"'`$^b" 'c\'"`$^d' `e\`'"^$f` ^g`'"\^$h^ $i`'"\$^j$
            _
            _str_
            _notstr_
            _!a`'"\_$^_
        """)

        self.assertIsInstance(grammar.tokens[0].regex, grammar.tokens[0].LiteralMatcher)
        self.assertFalse(grammar.tokens[0].regex.caseSensitive)
        self.assertEqual(grammar.tokens[0].regex.literal, 'a')

        self.assertIsInstance(grammar.tokens[1].regex, grammar.tokens[1].LiteralMatcher)
        self.assertFalse(grammar.tokens[1].regex.caseSensitive)
        self.assertEqual(grammar.tokens[1].regex.literal, 'a b')

        self.assertIsInstance(grammar.tokens[2].regex, grammar.tokens[2].LiteralMatcher)
        self.assertFalse(grammar.tokens[2].regex.caseSensitive)
        self.assertEqual(grammar.tokens[2].regex.literal, 'c')

        self.assertIsInstance(grammar.tokens[3].regex, grammar.tokens[3].LiteralMatcher)
        self.assertFalse(grammar.tokens[3].regex.caseSensitive)
        self.assertEqual(grammar.tokens[3].regex.literal, 'efg')

        self.assertIsInstance(grammar.tokens[4].regex, grammar.tokens[4].LiteralMatcher)
        self.assertTrue(grammar.tokens[4].regex.caseSensitive)
        self.assertEqual(grammar.tokens[4].regex.literal, 'h')

        self.assertIsInstance(grammar.tokens[5].regex, grammar.tokens[5].LiteralMatcher)
        self.assertTrue(grammar.tokens[5].regex.caseSensitive)
        self.assertEqual(grammar.tokens[5].regex.literal, 'i j k')

        self.assertIsInstance(grammar.tokens[6].regex, re._pattern_type)
        self.assertFalse(grammar.tokens[6].regex.flags & re.I)
        self.assertEqual(grammar.tokens[6].regex.pattern, 'l')

        self.assertIsInstance(grammar.tokens[7].regex, re._pattern_type)
        self.assertFalse(grammar.tokens[7].regex.flags & re.I)
        self.assertEqual(grammar.tokens[7].regex.pattern, 'm n o')

        self.assertIsInstance(grammar.tokens[8].regex, re._pattern_type)
        self.assertTrue(grammar.tokens[8].regex.flags & re.I)
        self.assertEqual(grammar.tokens[8].regex.pattern, 'p')

        self.assertIsInstance(grammar.tokens[9].regex, re._pattern_type)
        self.assertTrue(grammar.tokens[9].regex.flags & re.I)
        self.assertEqual(grammar.tokens[9].regex.pattern, 'q r s')

        self.assertIsInstance(grammar.tokens[10].regex, grammar.tokens[10].LiteralMatcher)
        self.assertFalse(grammar.tokens[10].regex.caseSensitive)
        self.assertEqual(grammar.tokens[10].regex.literal, 'a"\'`$^b')

        self.assertIsInstance(grammar.tokens[11].regex, grammar.tokens[11].LiteralMatcher)
        self.assertFalse(grammar.tokens[11].regex.caseSensitive)
        self.assertEqual(grammar.tokens[11].regex.literal, "c'\"`$^d")

        self.assertIsInstance(grammar.tokens[12].regex, grammar.tokens[12].LiteralMatcher)
        self.assertTrue(grammar.tokens[12].regex.caseSensitive)
        self.assertEqual(grammar.tokens[12].regex.literal, 'e`\'"^$f')

        self.assertIsInstance(grammar.tokens[13].regex, re._pattern_type)
        self.assertFalse(grammar.tokens[13].regex.flags & re.I)
        self.assertEqual(grammar.tokens[13].regex.pattern, 'g`\'"^$h')

        self.assertIsInstance(grammar.tokens[14].regex, re._pattern_type)
        self.assertTrue(grammar.tokens[14].regex.flags & re.I)
        self.assertEqual(grammar.tokens[14].regex.pattern, 'i`\'"$^j')

    def testParseComment(self):
        grammar = Grammar.constructGrammar(r"""
            'a' 'b' 'c' # letters
            # some more letters
            'q' "r" `e`
        """)

        self.assertListEqual(
            [t.regex.literal for t in grammar.tokens],
            ['a', 'b', 'c', 'q', 'r', 'e']
        )


    def testParseError(self):
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "a")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "()")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, ",")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "<>")


    def testParseNamedToken(self):
        grammar = Grammar.constructGrammar(r"""
            <abc: "123">
            <def : '456'>
            < ghi : `7<>8`>
            <
             jkl: _!><_>
            <mno: <pqr: '90'>>
        """)

        self.assertIsInstance(grammar.tokens[0], Grammar.NamedToken)
        self.assertFalse(grammar.tokens[0].token.regex.caseSensitive)
        self.assertEqual(grammar.tokens[0].token.regex.literal, '123')

        self.assertIsInstance(grammar.tokens[1], Grammar.NamedToken)
        self.assertFalse(grammar.tokens[1].token.regex.caseSensitive)
        self.assertEqual(grammar.tokens[1].token.regex.literal, '456')

        self.assertIsInstance(grammar.tokens[2], Grammar.NamedToken)
        self.assertTrue(grammar.tokens[2].token.regex.caseSensitive)
        self.assertEqual(grammar.tokens[2].token.regex.literal, '7<>8')

        self.assertIsInstance(grammar.tokens[3], Grammar.NamedToken)
        self.assertTrue(grammar.tokens[3].token.regex.flags)
        self.assertEqual(grammar.tokens[3].token.regex.pattern, '(?!><$).*$')

        self.assertIsInstance(grammar.tokens[4], Grammar.NamedToken)
        self.assertIsInstance(grammar.tokens[4].token, Grammar.NamedToken)
        self.assertFalse(grammar.tokens[4].token.token.regex.caseSensitive)
        self.assertEqual(grammar.tokens[4].token.token.regex.literal, '90')

        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "<mno: 'a' 'b'>")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "<mno: 'a'")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "mno: 'a'>")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, '<"mno": "a">')
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "<'mno': 'a'>")


    def testParseNamedGrammar(self):
        grammar = Grammar.constructGrammar(r"""
            (abc: "123")
            (def : '456')
            ( ghi : `7()8`)
            (
             jkl: _!)(_)
            (mno: (pqr: '90') )
            (stu: 'a' `b` "c")
        """)

        self.assertIsInstance(grammar.tokens[0], Grammar.Grammar)
        self.assertFalse(grammar.tokens[0].tokens[0].regex.caseSensitive)
        self.assertEqual(grammar.tokens[0].tokens[0].regex.literal, '123')

        self.assertIsInstance(grammar.tokens[1], Grammar.Grammar)
        self.assertFalse(grammar.tokens[1].tokens[0].regex.caseSensitive)
        self.assertEqual(grammar.tokens[1].tokens[0].regex.literal, '456')

        self.assertIsInstance(grammar.tokens[2], Grammar.Grammar)
        self.assertTrue(grammar.tokens[2].tokens[0].regex.caseSensitive)
        self.assertEqual(grammar.tokens[2].tokens[0].regex.literal, '7()8')

        self.assertIsInstance(grammar.tokens[3], Grammar.Grammar)
        self.assertTrue(grammar.tokens[3].tokens[0].regex.flags)
        self.assertEqual(grammar.tokens[3].tokens[0].regex.pattern, '(?!)($).*$')

        self.assertIsInstance(grammar.tokens[4], Grammar.Grammar)
        self.assertFalse(grammar.tokens[4].tokens[0].tokens[0].regex.caseSensitive)
        self.assertEqual(grammar.tokens[4].tokens[0].tokens[0].regex.literal, '90')

        self.assertIsInstance(grammar.tokens[5], Grammar.Grammar)
        self.assertFalse(grammar.tokens[5].tokens[0].regex.caseSensitive)
        self.assertEqual(grammar.tokens[5].tokens[0].regex.literal, 'a')
        self.assertTrue(grammar.tokens[5].tokens[1].regex.caseSensitive)
        self.assertEqual(grammar.tokens[5].tokens[1].regex.literal, 'b')
        self.assertFalse(grammar.tokens[5].tokens[2].regex.caseSensitive)
        self.assertEqual(grammar.tokens[5].tokens[2].regex.literal, 'c')

        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "(mno: 'a'")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "mno: 'a')")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, '("mno": "a")')
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "('mno': 'a')")


    def testParseZeroOrOne(self):
        grammar = Grammar.constructGrammar(r"""
            [[
              [[ 'a' "b" `c`]]
              [[_ _str_ _notstr_ ]]
              [[_!\_notstr\__]]
              [[_!\_str\__]]
            ]]
        """)

        self.assertIsInstance(grammar.tokens[0], Grammar.ZeroOrOne)
        self.assertIsInstance(grammar.tokens[0].tokens[0], Grammar.ZeroOrOne)
        self.assertIsInstance(grammar.tokens[0].tokens[1], Grammar.ZeroOrOne)
        self.assertIsInstance(grammar.tokens[0].tokens[2], Grammar.ZeroOrOne)
        self.assertIsInstance(grammar.tokens[0].tokens[3], Grammar.ZeroOrOne)

        self.assertIsInstance(grammar.tokens[0].tokens[0].tokens[0], Grammar.Token)
        self.assertIsInstance(grammar.tokens[0].tokens[0].tokens[1], Grammar.Token)
        self.assertIsInstance(grammar.tokens[0].tokens[0].tokens[2], Grammar.Token)
        self.assertEqual(grammar.tokens[0].tokens[0].tokens[0].regex.literal, 'a')
        self.assertFalse(grammar.tokens[0].tokens[0].tokens[0].regex.caseSensitive)
        self.assertEqual(grammar.tokens[0].tokens[0].tokens[1].regex.literal, 'b')
        self.assertFalse(grammar.tokens[0].tokens[0].tokens[1].regex.caseSensitive)
        self.assertEqual(grammar.tokens[0].tokens[0].tokens[2].regex.literal, 'c')
        self.assertTrue(grammar.tokens[0].tokens[0].tokens[2].regex.caseSensitive)

        self.assertIsInstance(grammar.tokens[0].tokens[1].tokens[0], Grammar.Token)
        self.assertIsInstance(grammar.tokens[0].tokens[1].tokens[1], Grammar.Token)
        self.assertIsInstance(grammar.tokens[0].tokens[1].tokens[2], Grammar.Token)
        self.assertEqual(grammar.tokens[0].tokens[1].tokens[0].regex.pattern, Grammar.Token.allToken.pattern)
        self.assertFalse(grammar.tokens[0].tokens[1].tokens[0].regex.flags)
        self.assertEqual(grammar.tokens[0].tokens[1].tokens[1].regex.pattern, Grammar.Token.strToken.pattern)
        self.assertFalse(grammar.tokens[0].tokens[1].tokens[1].regex.flags)
        self.assertEqual(grammar.tokens[0].tokens[1].tokens[2].regex.pattern, Grammar.Token.notStrToken.pattern)
        self.assertFalse(grammar.tokens[0].tokens[1].tokens[2].regex.flags)

        self.assertIsInstance(grammar.tokens[0].tokens[2].tokens[0], Grammar.Token)
        self.assertEqual(grammar.tokens[0].tokens[2].tokens[0].regex.pattern, "(?!_notstr_$).*$")
        self.assertTrue(grammar.tokens[0].tokens[2].tokens[0].regex.flags)

        self.assertIsInstance(grammar.tokens[0].tokens[3].tokens[0], Grammar.Token)
        self.assertEqual(grammar.tokens[0].tokens[3].tokens[0].regex.pattern, "(?!_str_$).*$")
        self.assertTrue(grammar.tokens[0].tokens[3].tokens[0].regex.flags)

        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "[[")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "]]")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "[[))]]")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "[[((]]))")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "[ [")


    def testParseZeroOrMore(self):
        grammar = Grammar.constructGrammar(r"""
            ((
              (( 'a' "b" `c`))
              ((_ _str_ _notstr_ ))
              ((_!\_notstr\__))
              ((_!\_str\__))
            ))
        """)

        self.assertIsInstance(grammar.tokens[0], Grammar.ZeroOrMore)
        self.assertIsInstance(grammar.tokens[0].tokens[0], Grammar.ZeroOrMore)
        self.assertIsInstance(grammar.tokens[0].tokens[1], Grammar.ZeroOrMore)
        self.assertIsInstance(grammar.tokens[0].tokens[2], Grammar.ZeroOrMore)
        self.assertIsInstance(grammar.tokens[0].tokens[3], Grammar.ZeroOrMore)

        self.assertIsInstance(grammar.tokens[0].tokens[0].tokens[0], Grammar.Token)
        self.assertIsInstance(grammar.tokens[0].tokens[0].tokens[1], Grammar.Token)
        self.assertIsInstance(grammar.tokens[0].tokens[0].tokens[2], Grammar.Token)
        self.assertEqual(grammar.tokens[0].tokens[0].tokens[0].regex.literal, 'a')
        self.assertFalse(grammar.tokens[0].tokens[0].tokens[0].regex.caseSensitive)
        self.assertEqual(grammar.tokens[0].tokens[0].tokens[1].regex.literal, 'b')
        self.assertFalse(grammar.tokens[0].tokens[0].tokens[1].regex.caseSensitive)
        self.assertEqual(grammar.tokens[0].tokens[0].tokens[2].regex.literal, 'c')
        self.assertTrue(grammar.tokens[0].tokens[0].tokens[2].regex.caseSensitive)

        self.assertIsInstance(grammar.tokens[0].tokens[1].tokens[0], Grammar.Token)
        self.assertIsInstance(grammar.tokens[0].tokens[1].tokens[1], Grammar.Token)
        self.assertIsInstance(grammar.tokens[0].tokens[1].tokens[2], Grammar.Token)
        self.assertEqual(grammar.tokens[0].tokens[1].tokens[0].regex.pattern, Grammar.Token.allToken.pattern)
        self.assertFalse(grammar.tokens[0].tokens[1].tokens[0].regex.flags)
        self.assertEqual(grammar.tokens[0].tokens[1].tokens[1].regex.pattern, Grammar.Token.strToken.pattern)
        self.assertFalse(grammar.tokens[0].tokens[1].tokens[1].regex.flags)
        self.assertEqual(grammar.tokens[0].tokens[1].tokens[2].regex.pattern, Grammar.Token.notStrToken.pattern)
        self.assertFalse(grammar.tokens[0].tokens[1].tokens[2].regex.flags)

        self.assertIsInstance(grammar.tokens[0].tokens[2].tokens[0], Grammar.Token)
        self.assertEqual(grammar.tokens[0].tokens[2].tokens[0].regex.pattern, "(?!_notstr_$).*$")
        self.assertTrue(grammar.tokens[0].tokens[2].tokens[0].regex.flags)

        self.assertIsInstance(grammar.tokens[0].tokens[3].tokens[0], Grammar.Token)
        self.assertEqual(grammar.tokens[0].tokens[3].tokens[0].regex.pattern, "(?!_str_$).*$")
        self.assertTrue(grammar.tokens[0].tokens[3].tokens[0].regex.flags)

        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "((")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "))")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "((]]))")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "(([[))]]")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "( (")


    def testParseOneOfSet(self):
        grammar = Grammar.constructGrammar(r"""
            {{
              {{ 'a' "b" `c`}}
              {{_ _str_ _notstr_ }}
              {{_!\_notstr\__}}
              {{_!\_str\__}}
            }}
        """)

        self.assertIsInstance(grammar.tokens[0], Grammar.OneOfSet)
        self.assertIsInstance(grammar.tokens[0].tokens[0], Grammar.OneOfSet)
        self.assertIsInstance(grammar.tokens[0].tokens[1], Grammar.OneOfSet)
        self.assertIsInstance(grammar.tokens[0].tokens[2], Grammar.OneOfSet)
        self.assertIsInstance(grammar.tokens[0].tokens[3], Grammar.OneOfSet)

        self.assertIsInstance(grammar.tokens[0].tokens[0].tokens[0], Grammar.Token)
        self.assertIsInstance(grammar.tokens[0].tokens[0].tokens[1], Grammar.Token)
        self.assertIsInstance(grammar.tokens[0].tokens[0].tokens[2], Grammar.Token)
        self.assertEqual(grammar.tokens[0].tokens[0].tokens[0].regex.literal, 'a')
        self.assertFalse(grammar.tokens[0].tokens[0].tokens[0].regex.caseSensitive)
        self.assertEqual(grammar.tokens[0].tokens[0].tokens[1].regex.literal, 'b')
        self.assertFalse(grammar.tokens[0].tokens[0].tokens[1].regex.caseSensitive)
        self.assertEqual(grammar.tokens[0].tokens[0].tokens[2].regex.literal, 'c')
        self.assertTrue(grammar.tokens[0].tokens[0].tokens[2].regex.caseSensitive)

        self.assertIsInstance(grammar.tokens[0].tokens[1].tokens[0], Grammar.Token)
        self.assertIsInstance(grammar.tokens[0].tokens[1].tokens[1], Grammar.Token)
        self.assertIsInstance(grammar.tokens[0].tokens[1].tokens[2], Grammar.Token)
        self.assertEqual(grammar.tokens[0].tokens[1].tokens[0].regex.pattern, Grammar.Token.allToken.pattern)
        self.assertFalse(grammar.tokens[0].tokens[1].tokens[0].regex.flags)
        self.assertEqual(grammar.tokens[0].tokens[1].tokens[1].regex.pattern, Grammar.Token.strToken.pattern)
        self.assertFalse(grammar.tokens[0].tokens[1].tokens[1].regex.flags)
        self.assertEqual(grammar.tokens[0].tokens[1].tokens[2].regex.pattern, Grammar.Token.notStrToken.pattern)
        self.assertFalse(grammar.tokens[0].tokens[1].tokens[2].regex.flags)

        self.assertIsInstance(grammar.tokens[0].tokens[2].tokens[0], Grammar.Token)
        self.assertEqual(grammar.tokens[0].tokens[2].tokens[0].regex.pattern, "(?!_notstr_$).*$")
        self.assertTrue(grammar.tokens[0].tokens[2].tokens[0].regex.flags)

        self.assertIsInstance(grammar.tokens[0].tokens[3].tokens[0], Grammar.Token)
        self.assertEqual(grammar.tokens[0].tokens[3].tokens[0].regex.pattern, "(?!_str_$).*$")
        self.assertTrue(grammar.tokens[0].tokens[3].tokens[0].regex.flags)

        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "{{")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "}}")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "{{]]}}")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "{{[[}}]]")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "{ {")


    def testParseSubGrammarDefinitions(self):
        grammar = Grammar.constructGrammar(r"""
            @gramA: 'a'@@
            @ gramB: 'b'@@
            @gramC : 'c'@@
            @ gramD : 'd'@@
            @gramE: 'e' @@
            @gramF: 'f'
            @@
            @
            gramG
            : 'g'
            @@
            @gramH: @gramI: 'i' @@ 'h' @gramI@ @@
            @gramJ:'j'@gramK: 'k' @@@gramK@@@

            @gramL: 'l'
                @gramM: 'm' @@
                @gramN: @gramM@ `n` @@
                @gramN@
            @@

            @gramO:
                @gramO2: 'o' @@
                @gramP:
                    @gramP2: 'p' @@
                    @gramQ:
                        @gramR: 'r' @@
                        @gramO2@
                        @gramP2@
                        'q'
                        @gramR@
                    @@
                    @gramQ@
                @@
                @gramP@
            @@

            @-: @@

            @gramA@
            @
             gramB
            @
            @ gramC @
            @gramD @
            @ gramE@
            @gramF@
            @gramG@
            @gramH@
            @gramJ@
            @gramL@
            @gramO@
            @-@
        """)

        self.assertListEqual([token.regex.literal for token in grammar.tokens], [
            'a', 'b', 'c', 'd', 'e', 'f', 'g',
            'h', 'i', 'j', 'k', 'l', 'm', 'n',
            'o', 'p', 'q', 'r',
        ])

        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "@gram A:'a'@@")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "@gram@A:'a'@@")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "@gramA: @gramB: @gramA@ @@ @@")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "@gramA: @gramA@ @@")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "@grammer@")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "@gramA: @gramB: 'b' @@ @@ @gramB@")
        self.assertRaises(Grammar.GrammarParsingError, Grammar.constructGrammar, "@gramA: @gramA: '' @@ @@ @gramA@")
