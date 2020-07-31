import re

from tokex.utils import grammar
import _test_case

class TestGrammarConstruction(_test_case.TokexTestCase):

    def test_tokenize_grammar(self):
        grammar_string = r"""
            { 'a' 'b' 'c' }
            (? 'd' 'e' 'f' )
            (* 'g' 'h' 'i' )
            (+ 'g' 'h' 'i' )
            (?'d' 'e' 'f' )
            (*'g' 'h' 'i' )
            (+'g' 'h' 'i' )
            (*'g' 'h' 'i' ['a'])
            (+'g' 'h' 'i' [(b: 'b')])
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

        grammar_tokens = grammar._tokenize_grammar(grammar_string)

        self.assertEqual(grammar_tokens, [
            "{", "'a'", "'b'", "'c'", "}",
            "(?", "'d'", "'e'", "'f'", ")",
            "(*", "'g'", "'h'", "'i'", ")",
            "(+", "'g'", "'h'", "'i'", ")",
            "(?", "'d'", "'e'", "'f'", ")",
            "(*", "'g'", "'h'", "'i'", ")",
            "(+", "'g'", "'h'", "'i'", ")",
            "(*", "'g'", "'h'", "'i'", "[", "'a'", "]", ")",
            "(+", "'g'", "'h'", "'i'", "[", "(b:", "'b'", ")", "]", ")",
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

    def test_parse_token(self):
        test_grammar = grammar.construct_grammar(r"""
            "a" "a b" 'c' 'efg' `h` `i j k` ^l^ ^m n o^ $p$ $q r s$
            "a\"'`$^b" 'c\'"`$^d' `e\`'"^$f` ^g`'"\^$h^ $i`'"\$^j$
            _
            _str_
            _notstr_
            _!a`'"\_$^_
        """)

        self.assertIsInstance(test_grammar.tokens[0].regex, test_grammar.tokens[0].LiteralMatcher)
        self.assertFalse(test_grammar.tokens[0].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[0].regex.literal, 'a')

        self.assertIsInstance(test_grammar.tokens[1].regex, test_grammar.tokens[1].LiteralMatcher)
        self.assertFalse(test_grammar.tokens[1].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[1].regex.literal, 'a b')

        self.assertIsInstance(test_grammar.tokens[2].regex, test_grammar.tokens[2].LiteralMatcher)
        self.assertFalse(test_grammar.tokens[2].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[2].regex.literal, 'c')

        self.assertIsInstance(test_grammar.tokens[3].regex, test_grammar.tokens[3].LiteralMatcher)
        self.assertFalse(test_grammar.tokens[3].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[3].regex.literal, 'efg')

        self.assertIsInstance(test_grammar.tokens[4].regex, test_grammar.tokens[4].LiteralMatcher)
        self.assertTrue(test_grammar.tokens[4].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[4].regex.literal, 'h')

        self.assertIsInstance(test_grammar.tokens[5].regex, test_grammar.tokens[5].LiteralMatcher)
        self.assertTrue(test_grammar.tokens[5].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[5].regex.literal, 'i j k')

        self.assertIsInstance(test_grammar.tokens[6].regex, re._pattern_type)
        self.assertTrue(test_grammar.tokens[6].regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[6].regex.pattern, 'l')

        self.assertIsInstance(test_grammar.tokens[7].regex, re._pattern_type)
        self.assertTrue(test_grammar.tokens[7].regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[7].regex.pattern, 'm n o')

        self.assertIsInstance(test_grammar.tokens[8].regex, re._pattern_type)
        self.assertFalse(test_grammar.tokens[8].regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[8].regex.pattern, 'p')

        self.assertIsInstance(test_grammar.tokens[9].regex, re._pattern_type)
        self.assertFalse(test_grammar.tokens[9].regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[9].regex.pattern, 'q r s')

        self.assertIsInstance(test_grammar.tokens[10].regex, test_grammar.tokens[10].LiteralMatcher)
        self.assertFalse(test_grammar.tokens[10].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[10].regex.literal, 'a"\'`$^b')

        self.assertIsInstance(test_grammar.tokens[11].regex, test_grammar.tokens[11].LiteralMatcher)
        self.assertFalse(test_grammar.tokens[11].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[11].regex.literal, "c'\"`$^d")

        self.assertIsInstance(test_grammar.tokens[12].regex, test_grammar.tokens[12].LiteralMatcher)
        self.assertTrue(test_grammar.tokens[12].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[12].regex.literal, 'e`\'"^$f')

        self.assertIsInstance(test_grammar.tokens[13].regex, re._pattern_type)
        self.assertTrue(test_grammar.tokens[13].regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[13].regex.pattern, 'g`\'"^$h')

        self.assertIsInstance(test_grammar.tokens[14].regex, re._pattern_type)
        self.assertFalse(test_grammar.tokens[14].regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[14].regex.pattern, 'i`\'"$^j')

    def test_parse_comment(self):
        test_grammar = grammar.construct_grammar(r"""
            'a' 'b' 'c' # letters
            # some more letters
            'q' "r" `e`
        """)

        self.assertListEqual(
            [t.regex.literal for t in test_grammar.tokens],
            ['a', 'b', 'c', 'q', 'r', 'e']
        )

        test_grammar = grammar.construct_grammar("'c' # letters")

        self.assertListEqual(
            [t.regex.literal for t in test_grammar.tokens],
            ['c']
        )


    def test_parse_error(self):
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "a")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "()")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, ",")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "<>")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "[]")


    def test_parse_named_token(self):
        test_grammar = grammar.construct_grammar(r"""
            <abc: "123">
            <def : '456'>
            < ghi : `7<>8`>
            <
             jkl: _!><_>
            <mno: <pqr: '90'>>
        """)

        self.assertIsInstance(test_grammar.tokens[0], grammar.NamedToken)
        self.assertFalse(test_grammar.tokens[0].token.regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[0].token.regex.literal, '123')

        self.assertIsInstance(test_grammar.tokens[1], grammar.NamedToken)
        self.assertFalse(test_grammar.tokens[1].token.regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[1].token.regex.literal, '456')

        self.assertIsInstance(test_grammar.tokens[2], grammar.NamedToken)
        self.assertTrue(test_grammar.tokens[2].token.regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[2].token.regex.literal, '7<>8')

        self.assertIsInstance(test_grammar.tokens[3], grammar.NamedToken)
        self.assertTrue(test_grammar.tokens[3].token.regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[3].token.regex.pattern, '(?!><$).*$')

        self.assertIsInstance(test_grammar.tokens[4], grammar.NamedToken)
        self.assertIsInstance(test_grammar.tokens[4].token, grammar.NamedToken)
        self.assertFalse(test_grammar.tokens[4].token.token.regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[4].token.token.regex.literal, '90')

        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "<mno: 'a' 'b'>")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "<mno: 'a'")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "mno: 'a'>")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, '<"mno": "a">')
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "<'mno': 'a'>")


    def test_parse_named_grammar(self):
        test_grammar = grammar.construct_grammar(r"""
            (abc: "123")
            (def : '456')
            ( ghi : `7()8`)
            (
             jkl: _!)(_)
            (mno: (pqr: '90') )
            (stu: 'a' `b` "c")
        """)

        self.assertIsInstance(test_grammar.tokens[0], grammar.Grammar)
        self.assertFalse(test_grammar.tokens[0].tokens[0].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[0].tokens[0].regex.literal, '123')

        self.assertIsInstance(test_grammar.tokens[1], grammar.Grammar)
        self.assertFalse(test_grammar.tokens[1].tokens[0].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[1].tokens[0].regex.literal, '456')

        self.assertIsInstance(test_grammar.tokens[2], grammar.Grammar)
        self.assertTrue(test_grammar.tokens[2].tokens[0].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[2].tokens[0].regex.literal, '7()8')

        self.assertIsInstance(test_grammar.tokens[3], grammar.Grammar)
        self.assertTrue(test_grammar.tokens[3].tokens[0].regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[3].tokens[0].regex.pattern, '(?!)($).*$')

        self.assertIsInstance(test_grammar.tokens[4], grammar.Grammar)
        self.assertFalse(test_grammar.tokens[4].tokens[0].tokens[0].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[4].tokens[0].tokens[0].regex.literal, '90')

        self.assertIsInstance(test_grammar.tokens[5], grammar.Grammar)
        self.assertFalse(test_grammar.tokens[5].tokens[0].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[5].tokens[0].regex.literal, 'a')
        self.assertTrue(test_grammar.tokens[5].tokens[1].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[5].tokens[1].regex.literal, 'b')
        self.assertFalse(test_grammar.tokens[5].tokens[2].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[5].tokens[2].regex.literal, 'c')

        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "(mno: 'a'")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "mno: 'a')")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, '("mno": "a")')
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "('mno': 'a')")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "('mno': 'a' ['b'])")


    def test_parse_zero_or_one(self):
        test_grammar = grammar.construct_grammar(r"""
            (?
              (? 'a' "b" `c`)
              (?_ _str_ _notstr_ )
              (?_!\_notstr\__)
              (?_!\_str\__)
            )
        """)

        self.assertIsInstance(test_grammar.tokens[0], grammar.ZeroOrOne)
        self.assertIsInstance(test_grammar.tokens[0].tokens[0], grammar.ZeroOrOne)
        self.assertIsInstance(test_grammar.tokens[0].tokens[1], grammar.ZeroOrOne)
        self.assertIsInstance(test_grammar.tokens[0].tokens[2], grammar.ZeroOrOne)
        self.assertIsInstance(test_grammar.tokens[0].tokens[3], grammar.ZeroOrOne)

        self.assertIsInstance(test_grammar.tokens[0].tokens[0].tokens[0], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[0].tokens[1], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[0].tokens[2], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[0].tokens[0].regex.literal, 'a')
        self.assertFalse(test_grammar.tokens[0].tokens[0].tokens[0].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[0].tokens[0].tokens[1].regex.literal, 'b')
        self.assertFalse(test_grammar.tokens[0].tokens[0].tokens[1].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[0].tokens[0].tokens[2].regex.literal, 'c')
        self.assertTrue(test_grammar.tokens[0].tokens[0].tokens[2].regex.case_sensitive)

        self.assertIsInstance(test_grammar.tokens[0].tokens[1].tokens[0], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[1].tokens[1], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[1].tokens[2], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[1].tokens[0].regex.pattern, grammar.Token.all_token.pattern)
        self.assertFalse(test_grammar.tokens[0].tokens[1].tokens[0].regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[0].tokens[1].tokens[1].regex.pattern, grammar.Token.str_token.pattern)
        self.assertFalse(test_grammar.tokens[0].tokens[1].tokens[1].regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[0].tokens[1].tokens[2].regex.pattern, grammar.Token.not_str_token.pattern)
        self.assertFalse(test_grammar.tokens[0].tokens[1].tokens[2].regex.flags & re.I)

        self.assertIsInstance(test_grammar.tokens[0].tokens[2].tokens[0], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[2].tokens[0].regex.pattern, "(?!_notstr_$).*$")
        self.assertTrue(test_grammar.tokens[0].tokens[2].tokens[0].regex.flags & re.I)

        self.assertIsInstance(test_grammar.tokens[0].tokens[3].tokens[0], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[3].tokens[0].regex.pattern, "(?!_str_$).*$")
        self.assertTrue(test_grammar.tokens[0].tokens[3].tokens[0].regex.flags & re.I)

        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "(?")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, ")")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "(?))")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "(?{)}")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "( ? 'a' )")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "(? 'a' ['b'])")


    def test_parse_zero_or_more(self):
        test_grammar = grammar.construct_grammar(r"""
            (*
              (* 'a' "b" `c`)
              (*_ _str_ _notstr_ )
              (* [<c:'c'>] _!\_notstr\__)
              (*_!\_str\__ ['b'])
            )
        """)

        self.assertIsInstance(test_grammar.tokens[0], grammar.ZeroOrMore)
        self.assertIsInstance(test_grammar.tokens[0].tokens[0], grammar.ZeroOrMore)
        self.assertIsInstance(test_grammar.tokens[0].tokens[1], grammar.ZeroOrMore)
        self.assertIsInstance(test_grammar.tokens[0].tokens[2], grammar.ZeroOrMore)
        self.assertIsInstance(test_grammar.tokens[0].tokens[3], grammar.ZeroOrMore)

        self.assertIsInstance(test_grammar.tokens[0].tokens[0].tokens[0], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[0].tokens[1], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[0].tokens[2], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[0].tokens[0].regex.literal, 'a')
        self.assertFalse(test_grammar.tokens[0].tokens[0].tokens[0].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[0].tokens[0].tokens[1].regex.literal, 'b')
        self.assertFalse(test_grammar.tokens[0].tokens[0].tokens[1].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[0].tokens[0].tokens[2].regex.literal, 'c')
        self.assertTrue(test_grammar.tokens[0].tokens[0].tokens[2].regex.case_sensitive)

        self.assertIsInstance(test_grammar.tokens[0].tokens[1].tokens[0], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[1].tokens[1], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[1].tokens[2], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[1].tokens[0].regex.pattern, grammar.Token.all_token.pattern)
        self.assertFalse(test_grammar.tokens[0].tokens[1].tokens[0].regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[0].tokens[1].tokens[1].regex.pattern, grammar.Token.str_token.pattern)
        self.assertFalse(test_grammar.tokens[0].tokens[1].tokens[1].regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[0].tokens[1].tokens[2].regex.pattern, grammar.Token.not_str_token.pattern)
        self.assertFalse(test_grammar.tokens[0].tokens[1].tokens[2].regex.flags & re.I)

        self.assertIsInstance(test_grammar.tokens[0].tokens[2].tokens[0], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[2].tokens[0].regex.pattern, "(?!_notstr_$).*$")
        self.assertTrue(test_grammar.tokens[0].tokens[2].tokens[0].regex.flags & re.I)
        self.assertIsInstance(test_grammar.tokens[0].tokens[2].delimiter_grammar.tokens[0], grammar.NamedToken)
        self.assertEqual(test_grammar.tokens[0].tokens[2].delimiter_grammar.tokens[0].token.regex.literal, "c")
        self.assertEqual(test_grammar.tokens[0].tokens[2].delimiter_grammar.tokens[0].name, "c")
        self.assertEqual(test_grammar.tokens[0].tokens[2].delimiter_grammar.tokens[0].token.regex.literal, "c")

        self.assertIsInstance(test_grammar.tokens[0].tokens[3].tokens[0], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[3].tokens[0].regex.pattern, "(?!_str_$).*$")
        self.assertTrue(test_grammar.tokens[0].tokens[3].tokens[0].regex.flags & re.I)
        self.assertIsInstance(test_grammar.tokens[0].tokens[3].delimiter_grammar.tokens[0], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[3].delimiter_grammar.tokens[0].regex.literal, "b")

        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "(*")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, ")")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "(*))")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "(*(?})")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "( *")


    def test_parse_one_or_more(self):
        test_grammar = grammar.construct_grammar(r"""
            (+
              (+ 'a' "b" `c`)
              (+_ _str_ _notstr_ )
              (+ [<c:'c'>] _!\_notstr\__)
              (+_!\_str\__ ['b'])
            )
        """)

        self.assertIsInstance(test_grammar.tokens[0], grammar.OneOrMore)
        self.assertIsInstance(test_grammar.tokens[0].tokens[0], grammar.OneOrMore)
        self.assertIsInstance(test_grammar.tokens[0].tokens[1], grammar.OneOrMore)
        self.assertIsInstance(test_grammar.tokens[0].tokens[2], grammar.OneOrMore)
        self.assertIsInstance(test_grammar.tokens[0].tokens[3], grammar.OneOrMore)

        self.assertIsInstance(test_grammar.tokens[0].tokens[0].tokens[0], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[0].tokens[1], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[0].tokens[2], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[0].tokens[0].regex.literal, 'a')
        self.assertFalse(test_grammar.tokens[0].tokens[0].tokens[0].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[0].tokens[0].tokens[1].regex.literal, 'b')
        self.assertFalse(test_grammar.tokens[0].tokens[0].tokens[1].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[0].tokens[0].tokens[2].regex.literal, 'c')
        self.assertTrue(test_grammar.tokens[0].tokens[0].tokens[2].regex.case_sensitive)

        self.assertIsInstance(test_grammar.tokens[0].tokens[1].tokens[0], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[1].tokens[1], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[1].tokens[2], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[1].tokens[0].regex.pattern, grammar.Token.all_token.pattern)
        self.assertFalse(test_grammar.tokens[0].tokens[1].tokens[0].regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[0].tokens[1].tokens[1].regex.pattern, grammar.Token.str_token.pattern)
        self.assertFalse(test_grammar.tokens[0].tokens[1].tokens[1].regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[0].tokens[1].tokens[2].regex.pattern, grammar.Token.not_str_token.pattern)
        self.assertFalse(test_grammar.tokens[0].tokens[1].tokens[2].regex.flags & re.I)

        self.assertIsInstance(test_grammar.tokens[0].tokens[2].tokens[0], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[2].tokens[0].regex.pattern, "(?!_notstr_$).*$")
        self.assertTrue(test_grammar.tokens[0].tokens[2].tokens[0].regex.flags & re.I)
        self.assertIsInstance(test_grammar.tokens[0].tokens[2].delimiter_grammar.tokens[0], grammar.NamedToken)
        self.assertEqual(test_grammar.tokens[0].tokens[2].delimiter_grammar.tokens[0].token.regex.literal, "c")
        self.assertEqual(test_grammar.tokens[0].tokens[2].delimiter_grammar.tokens[0].name, "c")
        self.assertEqual(test_grammar.tokens[0].tokens[2].delimiter_grammar.tokens[0].token.regex.literal, "c")

        self.assertIsInstance(test_grammar.tokens[0].tokens[3].tokens[0], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[3].tokens[0].regex.pattern, "(?!_str_$).*$")
        self.assertTrue(test_grammar.tokens[0].tokens[3].tokens[0].regex.flags & re.I)
        self.assertIsInstance(test_grammar.tokens[0].tokens[3].delimiter_grammar.tokens[0], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[3].delimiter_grammar.tokens[0].regex.literal, "b")

        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "(+")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, ")")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "(+))")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "(+(?})")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "( +")


    def test_parse_one_of_set(self):
        test_grammar = grammar.construct_grammar(r"""
            {
              { 'a' "b" `c`}
              {_ _str_ _notstr_ }
              {_!\_notstr\__}
              {_!\_str\__}
            }
        """)

        self.assertIsInstance(test_grammar.tokens[0], grammar.OneOfSet)
        self.assertIsInstance(test_grammar.tokens[0].tokens[0], grammar.OneOfSet)
        self.assertIsInstance(test_grammar.tokens[0].tokens[1], grammar.OneOfSet)
        self.assertIsInstance(test_grammar.tokens[0].tokens[2], grammar.OneOfSet)
        self.assertIsInstance(test_grammar.tokens[0].tokens[3], grammar.OneOfSet)

        self.assertIsInstance(test_grammar.tokens[0].tokens[0].tokens[0], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[0].tokens[1], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[0].tokens[2], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[0].tokens[0].regex.literal, 'a')
        self.assertFalse(test_grammar.tokens[0].tokens[0].tokens[0].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[0].tokens[0].tokens[1].regex.literal, 'b')
        self.assertFalse(test_grammar.tokens[0].tokens[0].tokens[1].regex.case_sensitive)
        self.assertEqual(test_grammar.tokens[0].tokens[0].tokens[2].regex.literal, 'c')
        self.assertTrue(test_grammar.tokens[0].tokens[0].tokens[2].regex.case_sensitive)

        self.assertIsInstance(test_grammar.tokens[0].tokens[1].tokens[0], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[1].tokens[1], grammar.Token)
        self.assertIsInstance(test_grammar.tokens[0].tokens[1].tokens[2], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[1].tokens[0].regex.pattern, grammar.Token.all_token.pattern)
        self.assertFalse(test_grammar.tokens[0].tokens[1].tokens[0].regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[0].tokens[1].tokens[1].regex.pattern, grammar.Token.str_token.pattern)
        self.assertFalse(test_grammar.tokens[0].tokens[1].tokens[1].regex.flags & re.I)
        self.assertEqual(test_grammar.tokens[0].tokens[1].tokens[2].regex.pattern, grammar.Token.not_str_token.pattern)
        self.assertFalse(test_grammar.tokens[0].tokens[1].tokens[2].regex.flags & re.I)

        self.assertIsInstance(test_grammar.tokens[0].tokens[2].tokens[0], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[2].tokens[0].regex.pattern, "(?!_notstr_$).*$")
        self.assertTrue(test_grammar.tokens[0].tokens[2].tokens[0].regex.flags & re.I)

        self.assertIsInstance(test_grammar.tokens[0].tokens[3].tokens[0], grammar.Token)
        self.assertEqual(test_grammar.tokens[0].tokens[3].tokens[0].regex.pattern, "(?!_str_$).*$")
        self.assertTrue(test_grammar.tokens[0].tokens[3].tokens[0].regex.flags & re.I)

        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "{")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "}")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "{)}")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "{(?})")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "{'a' ['b']}")


    def test_parse_sub_grammar_definitions(self):
        test_grammar = grammar.construct_grammar(r"""
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

        self.assertListEqual([token.regex.literal for token in test_grammar.tokens], [
            'a', 'b', 'c', 'd', 'e', 'f', 'g',
            'h', 'i', 'j', 'k', 'l', 'm', 'n',
            'o', 'p', 'q', 'r',
        ])

        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "@gram A:'a'@@")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "@gram@A:'a'@@")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "@gramA: @gramB: @gramA@ @@ @@")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "@gramA: @gramA@ @@")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "@grammer@")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "@gramA: @gramB: 'b' @@ @@ @gramB@")
        self.assertRaises(grammar.GrammarParsingError, grammar.construct_grammar, "@gramA: @gramA: '' @@ @@ @gramA@")
