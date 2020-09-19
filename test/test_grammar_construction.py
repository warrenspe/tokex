import re

from tokex.grammar.parse import tokenize_grammar, construct_grammar
from tokex.grammar import elements
from tokex.grammar import flags
from tokex import errors
import _test_case

class TestGrammarConstruction(_test_case.TokexTestCase):
    """ Class which tests the construction of a Tokex grammar from a grammar string """

    def test_tokenize_grammar(self):
        grammar_string = r"""
            { 'a' 'b' 'c' }
            ?(a: 'd' 'e' 'f' )
            *(b
: 'g' 'h' 'i' )
            +(1 : 'g' 'h' 'i' )
            ?(ab_12:'d' 'e' 'f' )
            ?('d' 'e' 'f' )
            *(a:'g' 'h' 'i' )
            +(a: 'g' 'h' 'i' )
            *(a:'g' 'h' 'i' sep {'a'})
            +(a: 'g' 'h' 'i' sep{ (b: 'b') })
            ( abc: 'abc' '123')
            (
             def: 'def' '456' )
            (ghi: 'ghi' '789')
            < abc: '123'>
            <
             def: '456' >
            <ghi: '789'>
            def abc { '123'}
            def
                def{
             '456' }
            def    ghi
                { '789'
                }

            $

            ~someRegex~
            ~ someRegex~
            ~someRegex ~
            ~ someRegex ~
        """

        grammar_tokens = [t["token"] for t in tokenize_grammar(grammar_string)]

        self.assertEqual(grammar_tokens, [
            "{", "'a'", "'b'", "'c'", "}",
            "?(a:", "'d'", "'e'", "'f'", ")",
            "*(b\n:", "'g'", "'h'", "'i'", ")",
            "+(1 :", "'g'", "'h'", "'i'", ")",
            "?(ab_12:", "'d'", "'e'", "'f'", ")",
            "?(", "'d'", "'e'", "'f'", ")",
            "*(a:", "'g'", "'h'", "'i'", ")",
            "+(a:", "'g'", "'h'", "'i'", ")",
            "*(a:", "'g'", "'h'", "'i'", "sep {", "'a'", "}", ")",
            "+(a:", "'g'", "'h'", "'i'", "sep{", "(b:", "'b'", ")", "}", ")",
            "( abc:", "'abc'", "'123'", ")",
            "(\n             def:", "'def'", "'456'", ")",
            "(ghi:", "'ghi'", "'789'", ")",
            "< abc:", "'123'", ">",
            "<\n             def:", "'456'", ">",
            "<ghi:", "'789'", ">",
            "def abc {", "'123'", "}",
            "def\n                def{", "'456'", "}",
            "def    ghi\n                {", "'789'", "}",
            "$",
            "~someRegex~", "~ someRegex~", "~someRegex ~", "~ someRegex ~",
        ])

        flags_grammar_string = r"""
            !'abc'
            !" abc"
            !"abc \" def"
            u.
            q.
            .
            s~AnotherRegex~
            s~AnotherRegex ~
            s~ AnotherRegex~
            s~ AnotherRegex ~
            "string"
            " string "
            "str ing"
            "str'ing"
            "str\"ing"
            "str\"ing\\"
            ""
            'string'
            ' string '
            'str ing'
            'str"ing'
            'str\'ing'
            ''
            s"string"
            s" string "
            s"str ing"
            s"str'ing"
            s"str\"ing"
            s"str\`ing"
            s""
            i"string"
            i" string "
            i"str ing"
            i"str'ing"
            i"str\"ing"
            i"str\`ing"
            i""
        """

        grammar_tokens = ["%s|%s" % ("".join(sorted(t["flags"] or [])), t["token"]) for t in tokenize_grammar(flags_grammar_string)]

        self.assertEqual(grammar_tokens, [
            "!|'abc'", '!|" abc"', '!|"abc \\" def"',
            "u|.", "q|.", "|.",
            "s|~AnotherRegex~", "s|~AnotherRegex ~", "s|~ AnotherRegex~", "s|~ AnotherRegex ~",
            '|"string"', '|" string "', '|"str ing"', '|"str\'ing"', '|"str\\"ing"', '|"str\\"ing\\\\"', '|""',
            "|'string'", "|' string '", "|'str ing'", "|'str\"ing'", "|'str\\'ing'", "|''",
            "s|\"string\"", "s|\" string \"", "s|\"str ing\"", "s|\"str'ing\"", 's|\"str\\"ing\"', "s|\"str\\`ing\"", "s|\"\"",
            "i|\"string\"", "i|\" string \"", "i|\"str ing\"", "i|\"str'ing\"", 'i|\"str\\"ing\"', "i|\"str\\`ing\"", "i|\"\"",
        ])

    def test_parse_token(self):
        test_grammar = construct_grammar(r"""
            "a" "a b" 'c' 'efg' s'h' s"i j k" ~l~ ~m n o~ s~p~ s~q r s~
            "a\"'`$~b\\" 'c\'"`$^d\\\\' u~g`'"\~$h~ q~i`'"\~\\^j\\\\~
            .
            q.
            u.
            !"a`'\"$^"
            $
        """)

        self.assertIsInstance(test_grammar.sub_elements[0], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[0].token_str, 'a')
        self.assertIsNone(test_grammar.sub_elements[0]._grammar_flags)

        self.assertIsInstance(test_grammar.sub_elements[1], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[1].token_str, 'a b')
        self.assertIsNone(test_grammar.sub_elements[1]._grammar_flags)

        self.assertIsInstance(test_grammar.sub_elements[2], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[2].token_str, 'c')
        self.assertIsNone(test_grammar.sub_elements[2]._grammar_flags)

        self.assertIsInstance(test_grammar.sub_elements[3], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[3].token_str, 'efg')
        self.assertIsNone(test_grammar.sub_elements[3]._grammar_flags)

        self.assertIsInstance(test_grammar.sub_elements[4], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[4].token_str, 'h')
        self.assertEqual(test_grammar.sub_elements[4]._grammar_flags, {flags.CASE_SENSITIVE})

        self.assertIsInstance(test_grammar.sub_elements[5], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[5].token_str, 'i j k')
        self.assertEqual(test_grammar.sub_elements[5]._grammar_flags, {flags.CASE_SENSITIVE})

        self.assertIsInstance(test_grammar.sub_elements[6], elements.RegexString)
        self.assertEqual(test_grammar.sub_elements[6].token_str, 'l')
        self.assertIsNone(test_grammar.sub_elements[6]._grammar_flags)

        self.assertIsInstance(test_grammar.sub_elements[7], elements.RegexString)
        self.assertEqual(test_grammar.sub_elements[7].token_str, 'm n o')
        self.assertIsNone(test_grammar.sub_elements[7]._grammar_flags)

        self.assertIsInstance(test_grammar.sub_elements[8], elements.RegexString)
        self.assertEqual(test_grammar.sub_elements[8].token_str, 'p')
        self.assertEqual(test_grammar.sub_elements[8]._grammar_flags, {flags.CASE_SENSITIVE})

        self.assertIsInstance(test_grammar.sub_elements[9], elements.RegexString)
        self.assertEqual(test_grammar.sub_elements[9].token_str, 'q r s')
        self.assertEqual(test_grammar.sub_elements[9]._grammar_flags, {flags.CASE_SENSITIVE})

        self.assertIsInstance(test_grammar.sub_elements[10], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[10].token_str, 'a"\'`$~b\\')
        self.assertIsNone(test_grammar.sub_elements[10]._grammar_flags)

        self.assertIsInstance(test_grammar.sub_elements[11], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[11].token_str, 'c\'"`$^d\\\\')
        self.assertIsNone(test_grammar.sub_elements[11]._grammar_flags)

        self.assertIsInstance(test_grammar.sub_elements[12], elements.RegexString)
        self.assertEqual(test_grammar.sub_elements[12].token_str, 'g`\'"~$h')
        self.assertEqual(test_grammar.sub_elements[12]._grammar_flags, {flags.UNQUOTED})

        self.assertIsInstance(test_grammar.sub_elements[13], elements.RegexString)
        self.assertEqual(test_grammar.sub_elements[13].token_str, 'i`\'"~\\^j\\\\')
        self.assertEqual(test_grammar.sub_elements[13]._grammar_flags, {flags.QUOTED})

        self.assertIsInstance(test_grammar.sub_elements[14], elements.AnyString)
        self.assertIsNone(test_grammar.sub_elements[14]._grammar_flags)

        self.assertIsInstance(test_grammar.sub_elements[15], elements.AnyString)
        self.assertEqual(test_grammar.sub_elements[15]._grammar_flags, {flags.QUOTED})

        self.assertIsInstance(test_grammar.sub_elements[16], elements.AnyString)
        self.assertEqual(test_grammar.sub_elements[16]._grammar_flags, {flags.UNQUOTED})

        self.assertIsInstance(test_grammar.sub_elements[17], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[17].token_str, 'a`\'"$^')
        self.assertEqual(test_grammar.sub_elements[17]._grammar_flags, {flags.NOT})

        self.assertIsInstance(test_grammar.sub_elements[18], elements.Newline)
        self.assertIsNone(test_grammar.sub_elements[18]._grammar_flags)

    def test_parse_comment(self):
        test_grammar = construct_grammar(r"""
            s'a' i'b' 'c' # letters
            # some more letters
            q'q' u"r" !'e'
        """)

        self.assertListEqual(
            [t.token_str for t in test_grammar.sub_elements],
            ['a', 'b', 'c', 'q', 'r', 'e']
        )

        test_grammar = construct_grammar("'c' # letters")

        self.assertListEqual(
            [t.token_str for t in test_grammar.sub_elements],
            ['c']
        )

    def test_parse_error(self):
        self.assertRaises(errors.TokexError, construct_grammar, "a")
        self.assertRaises(errors.TokexError, construct_grammar, "()")
        self.assertRaises(errors.TokexError, construct_grammar, ",")
        self.assertRaises(errors.TokexError, construct_grammar, "<>")
        self.assertRaises(errors.TokexError, construct_grammar, "[]")
        self.assertRaises(errors.TokexError, construct_grammar, "(asdf asdf : 'a')")
        self.assertRaises(errors.TokexError, construct_grammar, "'a\"")
        self.assertRaises(errors.TokexError, construct_grammar, r"'a\'")

    def test_parse_named_element(self):
        test_grammar = construct_grammar(r"""
            <abc: "123">
            <def : !'456'>
            < ghi : s~7<>8~>
            <
             jkl: q.>
            <mno: $>
        """)

        self.assertIsInstance(test_grammar.sub_elements[0], elements.NamedElement)
        self.assertEqual(test_grammar.sub_elements[0].name, 'abc')
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[0], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[0].sub_elements[0].token_str, "123")
        self.assertIsNone(test_grammar.sub_elements[0].sub_elements[0]._grammar_flags)

        self.assertIsInstance(test_grammar.sub_elements[1], elements.NamedElement)
        self.assertEqual(test_grammar.sub_elements[1].name, 'def')
        self.assertIsInstance(test_grammar.sub_elements[1].sub_elements[0], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[1].sub_elements[0].token_str, "456")
        self.assertEqual(test_grammar.sub_elements[1].sub_elements[0]._grammar_flags, {flags.NOT})

        self.assertIsInstance(test_grammar.sub_elements[2], elements.NamedElement)
        self.assertEqual(test_grammar.sub_elements[2].name, 'ghi')
        self.assertIsInstance(test_grammar.sub_elements[2].sub_elements[0], elements.RegexString)
        self.assertEqual(test_grammar.sub_elements[2].sub_elements[0].token_str, "7<>8")
        self.assertEqual(test_grammar.sub_elements[2].sub_elements[0]._grammar_flags, {flags.CASE_SENSITIVE})

        self.assertIsInstance(test_grammar.sub_elements[3], elements.NamedElement)
        self.assertEqual(test_grammar.sub_elements[3].name, 'jkl')
        self.assertIsInstance(test_grammar.sub_elements[3].sub_elements[0], elements.AnyString)
        self.assertEqual(test_grammar.sub_elements[3].sub_elements[0]._grammar_flags, {flags.QUOTED})

        self.assertIsInstance(test_grammar.sub_elements[4], elements.NamedElement)
        self.assertEqual(test_grammar.sub_elements[4].name, 'mno')
        self.assertIsInstance(test_grammar.sub_elements[4].sub_elements[0], elements.Newline)
        self.assertIsNone(test_grammar.sub_elements[4].sub_elements[0]._grammar_flags)

        self.assertRaises(errors.TokexError, construct_grammar, "<mno: 'a' 'b'>")
        self.assertRaises(errors.TokexError, construct_grammar, "<mno: {'a' 'b'}>")
        self.assertRaises(errors.TokexError, construct_grammar, "<mno: 'a'")
        self.assertRaises(errors.TokexError, construct_grammar, "mno: 'a'>")
        self.assertRaises(errors.TokexError, construct_grammar, '<"mno": "a">')
        self.assertRaises(errors.TokexError, construct_grammar, "<'mno': 'a'>")
        self.assertRaises(errors.TokexError, construct_grammar, "<a: <b: 'a'>>")


    def test_parse_grammar(self):
        test_grammar = construct_grammar(r"""
            (abc: "123")
            (def :q'456')
            ( ghi : s'7()8')
            (
             jkl: !~()~)
            (mno: (pqr: .) )
            (stu: i'a' $ q"c")
        """)

        self.assertIsInstance(test_grammar.sub_elements[0], elements.Grammar)
        self.assertEqual(test_grammar.sub_elements[0].name, 'abc')
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[0], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[0].sub_elements[0].token_str, '123')
        self.assertIsNone(test_grammar.sub_elements[0].sub_elements[0]._grammar_flags)

        self.assertIsInstance(test_grammar.sub_elements[1], elements.Grammar)
        self.assertEqual(test_grammar.sub_elements[1].name, 'def')
        self.assertIsInstance(test_grammar.sub_elements[1].sub_elements[0], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[1].sub_elements[0].token_str, '456')
        self.assertEqual(test_grammar.sub_elements[1].sub_elements[0]._grammar_flags, {flags.QUOTED})

        self.assertIsInstance(test_grammar.sub_elements[2], elements.Grammar)
        self.assertEqual(test_grammar.sub_elements[2].name, 'ghi')
        self.assertIsInstance(test_grammar.sub_elements[2].sub_elements[0], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[2].sub_elements[0].token_str, '7()8')
        self.assertEqual(test_grammar.sub_elements[2].sub_elements[0]._grammar_flags, {flags.CASE_SENSITIVE})

        self.assertIsInstance(test_grammar.sub_elements[3], elements.Grammar)
        self.assertEqual(test_grammar.sub_elements[3].name, 'jkl')
        self.assertIsInstance(test_grammar.sub_elements[3].sub_elements[0], elements.RegexString)
        self.assertEqual(test_grammar.sub_elements[3].sub_elements[0].token_str, '()')
        self.assertEqual(test_grammar.sub_elements[3].sub_elements[0]._grammar_flags, {flags.NOT})

        self.assertIsInstance(test_grammar.sub_elements[4], elements.Grammar)
        self.assertEqual(test_grammar.sub_elements[4].name, 'mno')
        self.assertIsInstance(test_grammar.sub_elements[4].sub_elements[0], elements.Grammar)
        self.assertEqual(test_grammar.sub_elements[4].sub_elements[0].name, 'pqr')
        self.assertIsInstance(test_grammar.sub_elements[4].sub_elements[0].sub_elements[0], elements.AnyString)
        self.assertIsNone(test_grammar.sub_elements[4].sub_elements[0].sub_elements[0]._grammar_flags)

        self.assertIsInstance(test_grammar.sub_elements[5], elements.Grammar)
        self.assertEqual(test_grammar.sub_elements[5].name, 'stu')
        self.assertIsInstance(test_grammar.sub_elements[5].sub_elements[0], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[5].sub_elements[0].token_str, 'a')
        self.assertEqual(test_grammar.sub_elements[5].sub_elements[0]._grammar_flags, {flags.CASE_INSENSITIVE})
        self.assertIsInstance(test_grammar.sub_elements[5].sub_elements[1], elements.Newline)
        self.assertIsNone(test_grammar.sub_elements[5].sub_elements[1]._grammar_flags)
        self.assertIsInstance(test_grammar.sub_elements[5].sub_elements[2], elements.StringLiteral)
        self.assertEqual(test_grammar.sub_elements[5].sub_elements[2].token_str, 'c')
        self.assertEqual(test_grammar.sub_elements[5].sub_elements[2]._grammar_flags, {flags.QUOTED})

        self.assertRaises(errors.TokexError, construct_grammar, "(mno: 'a'")
        self.assertRaises(errors.TokexError, construct_grammar, "(m no: 'a')")
        self.assertRaises(errors.TokexError, construct_grammar, "mno: 'a')")
        self.assertRaises(errors.TokexError, construct_grammar, '("mno": "a")')
        self.assertRaises(errors.TokexError, construct_grammar, "('mno': 'a')")
        self.assertRaises(errors.TokexError, construct_grammar, "('mno': 'a' ['b'])")


    def test_parse_zero_or_one(self):
        test_grammar = construct_grammar(r"""
            ?(a:
              ?(b_: 'a' !"b" q'c')
              ?(-c:. q. u. )
              ?(  de:{$ .} )
              ?(.)
              ?()
            )
        """)

        self.assertIsInstance(test_grammar.sub_elements[0], elements.ZeroOrOne)
        self.assertEqual(test_grammar.sub_elements[0].name, 'a')
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[0], elements.ZeroOrOne)
        self.assertEqual(test_grammar.sub_elements[0].sub_elements[0].name, 'b_')
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[1], elements.ZeroOrOne)
        self.assertEqual(test_grammar.sub_elements[0].sub_elements[1].name, '-c')
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[2], elements.ZeroOrOne)
        self.assertEqual(test_grammar.sub_elements[0].sub_elements[2].name, 'de')
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[3], elements.ZeroOrOne)
        self.assertIsNone(test_grammar.sub_elements[0].sub_elements[3].name)
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[4], elements.ZeroOrOne)
        self.assertIsNone(test_grammar.sub_elements[0].sub_elements[4].name)

        se = test_grammar.sub_elements[0].sub_elements

        self.assertIsInstance(se[0].sub_elements[0], elements.StringLiteral)
        self.assertEqual(se[0].sub_elements[0].token_str, 'a')
        self.assertIsNone(se[0].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[0].sub_elements[1], elements.StringLiteral)
        self.assertEqual(se[0].sub_elements[1].token_str, 'b')
        self.assertEqual(se[0].sub_elements[1]._grammar_flags, {flags.NOT})

        self.assertIsInstance(se[0].sub_elements[2], elements.StringLiteral)
        self.assertEqual(se[0].sub_elements[2].token_str, 'c')
        self.assertEqual(se[0].sub_elements[2]._grammar_flags, {flags.QUOTED})


        self.assertIsInstance(se[1].sub_elements[0], elements.AnyString)
        self.assertIsNone(se[1].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[1].sub_elements[1], elements.AnyString)
        self.assertEqual(se[1].sub_elements[1]._grammar_flags, {flags.QUOTED})

        self.assertIsInstance(se[1].sub_elements[2], elements.AnyString)
        self.assertEqual(se[1].sub_elements[2]._grammar_flags, {flags.UNQUOTED})


        self.assertIsInstance(se[2].sub_elements[0], elements.OneOfSet)
        self.assertIsNone(se[2].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[2].sub_elements[0].sub_elements[0], elements.Newline)
        self.assertIsNone(se[2].sub_elements[0].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[2].sub_elements[0].sub_elements[1], elements.AnyString)
        self.assertIsNone(se[2].sub_elements[0].sub_elements[1]._grammar_flags)

        self.assertIsInstance(se[3].sub_elements[0], elements.AnyString)
        self.assertIsNone(se[3].sub_elements[0]._grammar_flags)

        self.assertEqual(len(se[4].sub_elements), 0)

        self.assertRaises(errors.TokexError, construct_grammar, "?(a:")
        self.assertRaises(errors.TokexError, construct_grammar, ")")
        self.assertRaises(errors.TokexError, construct_grammar, "?(a:))")
        self.assertRaises(errors.TokexError, construct_grammar, "?(a:{)}")
        self.assertRaises(errors.TokexError, construct_grammar, "? (a: 'a' )")
        self.assertRaises(errors.TokexError, construct_grammar, "?(a: 'a' sep { 'b'})")


    def test_parse_zero_or_more(self):
        test_grammar = construct_grammar(r"""
            *(a:
              *(b_: 'a' !"b" q'c')
              *(-c:. q. u. )
              *(  de:{$ .} sep { !~a~})
            )
        """)

        self.assertIsInstance(test_grammar.sub_elements[0], elements.ZeroOrMore)
        self.assertEqual(test_grammar.sub_elements[0].name, 'a')
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[0], elements.ZeroOrMore)
        self.assertEqual(test_grammar.sub_elements[0].sub_elements[0].name, 'b_')
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[1], elements.ZeroOrMore)
        self.assertEqual(test_grammar.sub_elements[0].sub_elements[1].name, '-c')
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[2], elements.ZeroOrMore)
        self.assertEqual(test_grammar.sub_elements[0].sub_elements[2].name, 'de')

        se = test_grammar.sub_elements[0].sub_elements

        self.assertIsInstance(se[0].sub_elements[0], elements.StringLiteral)
        self.assertEqual(se[0].sub_elements[0].token_str, 'a')
        self.assertIsNone(se[0].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[0].sub_elements[1], elements.StringLiteral)
        self.assertEqual(se[0].sub_elements[1].token_str, 'b')
        self.assertEqual(se[0].sub_elements[1]._grammar_flags, {flags.NOT})

        self.assertIsInstance(se[0].sub_elements[2], elements.StringLiteral)
        self.assertEqual(se[0].sub_elements[2].token_str, 'c')
        self.assertEqual(se[0].sub_elements[2]._grammar_flags, {flags.QUOTED})


        self.assertIsInstance(se[1].sub_elements[0], elements.AnyString)
        self.assertIsNone(se[1].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[1].sub_elements[1], elements.AnyString)
        self.assertEqual(se[1].sub_elements[1]._grammar_flags, {flags.QUOTED})

        self.assertIsInstance(se[1].sub_elements[2], elements.AnyString)
        self.assertEqual(se[1].sub_elements[2]._grammar_flags, {flags.UNQUOTED})


        self.assertIsInstance(se[2].sub_elements[0], elements.OneOfSet)
        self.assertIsNone(se[2].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[2].sub_elements[0].sub_elements[0], elements.Newline)
        self.assertIsNone(se[2].sub_elements[0].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[2].sub_elements[0].sub_elements[1], elements.AnyString)
        self.assertIsNone(se[2].sub_elements[0].sub_elements[1]._grammar_flags)

        self.assertIsNotNone(se[2].delimiter_grammar)
        self.assertIsInstance(se[2].delimiter_grammar.sub_elements[0], elements.RegexString)
        self.assertEqual(se[2].delimiter_grammar.sub_elements[0].token_str, 'a')
        self.assertEqual(se[2].delimiter_grammar.sub_elements[0]._grammar_flags, {flags.NOT})

        self.assertRaises(errors.TokexError, construct_grammar, "*(a:")
        self.assertRaises(errors.TokexError, construct_grammar, ")")
        self.assertRaises(errors.TokexError, construct_grammar, "*(a:))")
        self.assertRaises(errors.TokexError, construct_grammar, "*(a:{)}")
        self.assertRaises(errors.TokexError, construct_grammar, "* (a: 'a' )")
        self.assertRaises(errors.TokexError, construct_grammar, "*(a: 'a' sep)")
        self.assertRaises(errors.TokexError, construct_grammar, "*(a: 'a' sep {)")


    def test_parse_one_or_more(self):
        test_grammar = construct_grammar(r"""
            +(a:
              +(b_: 'a' !"b" q'c')
              +(-c:. q. u. )
              +(  de:{$ .} sep { !~a~})
            )
        """)

        self.assertIsInstance(test_grammar.sub_elements[0], elements.OneOrMore)
        self.assertEqual(test_grammar.sub_elements[0].name, 'a')
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[0], elements.OneOrMore)
        self.assertEqual(test_grammar.sub_elements[0].sub_elements[0].name, 'b_')
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[1], elements.OneOrMore)
        self.assertEqual(test_grammar.sub_elements[0].sub_elements[1].name, '-c')
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[2], elements.OneOrMore)
        self.assertEqual(test_grammar.sub_elements[0].sub_elements[2].name, 'de')

        se = test_grammar.sub_elements[0].sub_elements

        self.assertIsInstance(se[0].sub_elements[0], elements.StringLiteral)
        self.assertEqual(se[0].sub_elements[0].token_str, 'a')
        self.assertIsNone(se[0].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[0].sub_elements[1], elements.StringLiteral)
        self.assertEqual(se[0].sub_elements[1].token_str, 'b')
        self.assertEqual(se[0].sub_elements[1]._grammar_flags, {flags.NOT})

        self.assertIsInstance(se[0].sub_elements[2], elements.StringLiteral)
        self.assertEqual(se[0].sub_elements[2].token_str, 'c')
        self.assertEqual(se[0].sub_elements[2]._grammar_flags, {flags.QUOTED})


        self.assertIsInstance(se[1].sub_elements[0], elements.AnyString)
        self.assertIsNone(se[1].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[1].sub_elements[1], elements.AnyString)
        self.assertEqual(se[1].sub_elements[1]._grammar_flags, {flags.QUOTED})

        self.assertIsInstance(se[1].sub_elements[2], elements.AnyString)
        self.assertEqual(se[1].sub_elements[2]._grammar_flags, {flags.UNQUOTED})


        self.assertIsInstance(se[2].sub_elements[0], elements.OneOfSet)
        self.assertIsNone(se[2].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[2].sub_elements[0].sub_elements[0], elements.Newline)
        self.assertIsNone(se[2].sub_elements[0].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[2].sub_elements[0].sub_elements[1], elements.AnyString)
        self.assertIsNone(se[2].sub_elements[0].sub_elements[1]._grammar_flags)

        self.assertIsNotNone(se[2].delimiter_grammar)
        self.assertIsInstance(se[2].delimiter_grammar.sub_elements[0], elements.RegexString)
        self.assertEqual(se[2].delimiter_grammar.sub_elements[0].token_str, 'a')
        self.assertEqual(se[2].delimiter_grammar.sub_elements[0]._grammar_flags, {flags.NOT})

        self.assertRaises(errors.TokexError, construct_grammar, "+(a:")
        self.assertRaises(errors.TokexError, construct_grammar, ")")
        self.assertRaises(errors.TokexError, construct_grammar, "+(a:))")
        self.assertRaises(errors.TokexError, construct_grammar, "+(a:{)}")
        self.assertRaises(errors.TokexError, construct_grammar, "+ (a: 'a' )")
        self.assertRaises(errors.TokexError, construct_grammar, "+(a: 'a' sep)")
        self.assertRaises(errors.TokexError, construct_grammar, "+(a: 'a' sep {)")


    def test_parse_one_of_set(self):
        test_grammar = construct_grammar(r"""
            {
              { 'a' !"b" q'c'}
              {. q. u. }
              {  {$ .} }
            }
        """)

        self.assertIsInstance(test_grammar.sub_elements[0], elements.OneOfSet)
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[0], elements.OneOfSet)
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[1], elements.OneOfSet)
        self.assertIsInstance(test_grammar.sub_elements[0].sub_elements[2], elements.OneOfSet)

        se = test_grammar.sub_elements[0].sub_elements

        self.assertIsInstance(se[0].sub_elements[0], elements.StringLiteral)
        self.assertEqual(se[0].sub_elements[0].token_str, 'a')
        self.assertIsNone(se[0].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[0].sub_elements[1], elements.StringLiteral)
        self.assertEqual(se[0].sub_elements[1].token_str, 'b')
        self.assertEqual(se[0].sub_elements[1]._grammar_flags, {flags.NOT})

        self.assertIsInstance(se[0].sub_elements[2], elements.StringLiteral)
        self.assertEqual(se[0].sub_elements[2].token_str, 'c')
        self.assertEqual(se[0].sub_elements[2]._grammar_flags, {flags.QUOTED})


        self.assertIsInstance(se[1].sub_elements[0], elements.AnyString)
        self.assertIsNone(se[1].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[1].sub_elements[1], elements.AnyString)
        self.assertEqual(se[1].sub_elements[1]._grammar_flags, {flags.QUOTED})

        self.assertIsInstance(se[1].sub_elements[2], elements.AnyString)
        self.assertEqual(se[1].sub_elements[2]._grammar_flags, {flags.UNQUOTED})


        self.assertIsInstance(se[2].sub_elements[0], elements.OneOfSet)
        self.assertIsNone(se[2].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[2].sub_elements[0].sub_elements[0], elements.Newline)
        self.assertIsNone(se[2].sub_elements[0].sub_elements[0]._grammar_flags)

        self.assertIsInstance(se[2].sub_elements[0].sub_elements[1], elements.AnyString)
        self.assertIsNone(se[2].sub_elements[0].sub_elements[1]._grammar_flags)

        self.assertRaises(errors.TokexError, construct_grammar, "{a:.}")
        self.assertRaises(errors.TokexError, construct_grammar, "{a:")
        self.assertRaises(errors.TokexError, construct_grammar, "}")
        self.assertRaises(errors.TokexError, construct_grammar, "{)}")
        self.assertRaises(errors.TokexError, construct_grammar, "{'a' sep { 'b'}}")


    def test_parse_sub_grammar_definitions(self):
        test_grammar = construct_grammar(r"""
            def gramA { 'a' }
            def   gramB{'b'}
            def gramC { 'c'
            }
            def gramD
                {
                'd'}
            def gramE
                {'e'}
            def gramF{ 'f'    'f2'         }
            def
            gramG
            { 'g'
            }
            def gramH{ def gramI{ 'i' } 'h' gramI() }
            def gramJ {'j' def gramK{ 'k' }gramK()}

            def gramL{ 'l'
                def gramM{ 'm' }
                def gramN{ gramM() !'n' }
                gramN()
            }

            def gramO{
                def gramO2{ 'o' }
                def gramP{
                    def gramP2{ 'p' }
                    def gramQ{
                        def gramR{ 'r' }
                        gramO2()
                        gramP2()
                        'q'
                        gramR()
                    }
                    gramQ()
                }
                gramP()
            }

            def _{ }

            gramA()
             gramB
             ()
            gramC ()
            gramD        ()
            gramE()
            gramF()
            gramG()
            gramH()
            gramJ()
            gramL()
            gramO()
            _()
        """, allow_sub_grammar_definitions=True)

        self.assertListEqual([token.token_str for token in test_grammar.sub_elements], [
            'a', 'b', 'c', 'd', 'e', 'f', 'f2', 'g',
            'h', 'i', 'j', 'k', 'l', 'm', 'n',
            'o', 'p', 'q', 'r',
        ])

        self.assertRaises(errors.TokexError, construct_grammar, "def gramA{'a'}", allow_sub_grammar_definitions=False)
        self.assertRaises(errors.TokexError, construct_grammar, "def gram A{'a'}", allow_sub_grammar_definitions=True)
        self.assertRaises(errors.TokexError, construct_grammar, "def gram{A{'a'}", allow_sub_grammar_definitions=True)
        self.assertRaises(errors.TokexError, construct_grammar, "defgramA{'a'}", allow_sub_grammar_definitions=True)
        self.assertRaises(errors.TokexError, construct_grammar, "def gramA{ def gramB{ def gramC{ . } } } gramC()", allow_sub_grammar_definitions=True)
        self.assertRaises(errors.TokexError, construct_grammar, "def grammer", allow_sub_grammar_definitions=True)
        self.assertRaises(errors.TokexError, construct_grammar, "def gramA{ def gramB { 'b' } } gramB()", allow_sub_grammar_definitions=True)
        self.assertRaises(errors.TokexError, construct_grammar, "def gramA{ def gramB{ '' } } gramC()", allow_sub_grammar_definitions=True)
