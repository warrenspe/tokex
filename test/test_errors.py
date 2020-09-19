import re
import textwrap

import _test_case

from tokex.grammar.parse import tokenize_grammar, construct_grammar
from tokex.grammar import elements
from tokex.grammar import flags
from tokex import errors
from tokex import functions

class TestErrors(_test_case.TokexTestCase):
    """ Class which tests the construction of a Tokex grammar from a grammar string """

    maxDiff = 1500

    gsec_line_col_re = re.compile("Line (\d+) Column (\d+)")
    gsec_caret_line_re = re.compile(r"^ *\^+$")

    def _parse_gsec(self, gsec):
        """ Parses a grammar-string-error-context string """

        lines = [line for line in gsec.split("\n") if line.strip()]

        line_col_re_match = self.gsec_line_col_re.search(lines[0])

        line = int(line_col_re_match.group(1))
        column = int(line_col_re_match.group(2))

        # Ensure the right amount of caret padding is present
        self.assertEqual(lines[2].count(" "), column - 1)
        num_carets = lines[2].count("^")

        return {
            "line": line,
            "column": column,
            "grammar_snippet": lines[1].lstrip(),
            "num_carets": num_carets
        }

    def _parse_grammar_parsing_error_string(self, grammar_parsing_error):
        gpe_str = str(grammar_parsing_error)
        lines = gpe_str.split("\n")
        intro_and_err_msg = lines[0]
        err_msg = intro_and_err_msg.split(": ", 1)[1]

        gsec_info = {}
        current_line = 1
        if self.gsec_line_col_re.search(gpe_str):
            for line_idx, line in enumerate(lines[1:], start=current_line):
                if self.gsec_caret_line_re.match(line):
                    break

            else:
                raise Exception("Caret line not found despite gsec apparently present")

            gsec_info = self._parse_gsec("\n".join(lines[1: line_idx + 1]))
            current_line = line_idx + 1

        tree_info = {}
        # If we have something else, it is the grammar tree
        if len(lines) > current_line:
            tree_info["grammar_tree"] = []
            tree_info["tree_type"] = lines[current_line].split(" ", 1)[0]
            for line in lines[current_line + 1: len(lines)]:
                tree_info["grammar_tree"].append([line.count("    "), line.lstrip()])

        return {
            "err_msg": err_msg,
            **gsec_info,
            **tree_info
        }

    def get_exception(self, grammar_string, exception_type, allow_sub_grammar_definitions=True):
        with self.assertRaises(exception_type) as cm:
            functions.compile(grammar_string, allow_sub_grammar_definitions=allow_sub_grammar_definitions)
        return cm.exception

    def test_tokex_error_grammar_string_error_context(self):
        # Test an error in the middle of a grammar
        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            $ error $
            "test" "test" "test"
        """)

        e = self.get_exception(grammar_string, errors.TokexError)
        self.assertEqual(
            self._parse_gsec(e.grammar_string_error_context()),
            {
                "line": 4,
                "column": 3,
                "grammar_snippet": "$ error $",
                "num_carets": 5
            }
        )

        # Test a grammar with an immediate error
        grammar_string = textwrap.dedent('''error $ "test" "test" "test" ''')
        e = self.get_exception(grammar_string, errors.TokexError)
        self.assertEqual(
            self._parse_gsec(e.grammar_string_error_context()),
            {
                "line": 1,
                "column": 1,
                "grammar_snippet": 'error $ "test" "test" "test" ',
                "num_carets": 5
            }
        )

        # Test a grammar with an error on a long line
        grammar_string = textwrap.dedent('''
            "1234567890 1234567890 1234567890 1234567890 1234567890 1234567890" error "1234567890 1234567890 1234567890 1234567890 1234567890 1234567890"
        ''')
        e = self.get_exception(grammar_string, errors.TokexError)
        self.assertEqual(
            self._parse_gsec(e.grammar_string_error_context()),
            {
                "line": 2,
                "column": 51,
                "grammar_snippet": '7890 1234567890 1234567890 1234567890 1234567890" error "1234567890 1234567890 1234567890 1234567890 1234',
                "num_carets": 5
            }
        )

    def test_grammar_tokenizing_error(self):
        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            $ error_thrown $
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.TokexError)
        self.assertIn("tokenizing", str(e))
        self.assertIn("error_thrown", str(e))

    def test_unknown_grammar_token_error(self):
        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            $ error_thrown $
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.UnknownGrammarTokenError)
        self.assertIn("Encountered unknown grammar token: error_thrown", str(e))
        self.assertEqual(
            self._parse_gsec(e.grammar_string_error_context()),
            {
                "line": 4,
                "column": 3,
                "grammar_snippet": '$ error_thrown $',
                "num_carets": 12
            }
        )

    def test_grammar_parsing_error(self):
        # Test an error with full tree/context
        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            $ i. $
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.GrammarParsingError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Invalid flag i given to <[Any String .]>, valid flags are: q, u",
            "line": 4,
            "column": 3,
            "grammar_snippet": '$ i. $',
            "tree_type": "Element",
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Newline $]>']
            ],
            "num_carets": 2
        })

        # Test an error with no grammar tree
        grammar_string = textwrap.dedent("""
            )
        """)
        e = self.get_exception(grammar_string, errors.GrammarParsingError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Extra closing brackets given; found an extra: )",
            "line": 2,
            "column": 1,
            "grammar_snippet": ")",
            "num_carets": 1
        })

        # Test an error with no error context
        e = errors.GrammarParsingError("Test error message")
        e.grammar_string = "'test' #"
        e.match_span_start = 7
        e.match_span_end = 8
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Test error message",
            "line": 1,
            "column": 8,
            "grammar_snippet": "'test' #",
            "num_carets": 1
        })

        # Test an error with no grammar tree nor error context
        e = errors.GrammarParsingError("Test error message")
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Test error message"
        })


    def test_invalid_grammar_token_flags_error(self):
        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            $ !. $
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.InvalidGrammarTokenFlagsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Invalid flag ! given to <[Any String .]>, valid flags are: q, u",
            "line": 4,
            "column": 3,
            "grammar_snippet": "$ !. $",
            "tree_type": "Element",
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Newline $]>']
            ],
            "num_carets": 2
        })

        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            $ !i. $
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.InvalidGrammarTokenFlagsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Invalid flags !, i given to <[Any String .]>, valid flags are: q, u",
            "line": 4,
            "column": 3,
            "grammar_snippet": "$ !i. $",
            "tree_type": "Element",
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Newline $]>']
            ],
            "num_carets": 3
        })

    def test_invalid_regex_error(self):
        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            $ ~[)~ $
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.InvalidRegexError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Invalid regular expression given: [)",
            "line": 4,
            "column": 3,
            "grammar_snippet": "$ ~[)~ $",
            "tree_type": "Element",
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Newline $]>']
            ],
            "num_carets": 4
        })


    def test_mutually_exclusive_grammar_tokens_flags_error(self):
        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            $ si. $
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.MutuallyExclusiveGrammarTokenFlagsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Mutually exclusive flags given to <[Any String .]>: i, s",
            "line": 4,
            "column": 3,
            "grammar_snippet": "$ si. $",
            "tree_type": "Element",
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Newline $]>']
            ],
            "num_carets": 3
        })

    def test_invalid_delimiter_error(self):
        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            <test: sep { . }>
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.InvalidDelimiterError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Cannot add iterator delimiters to <[Named Element <test: ...>]>",
            "line": 4,
            "column": 8,
            "grammar_snippet": "<test: sep { . }>",
            "tree_type": "Element",
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Named Element <test: ...>]>']
            ],
            "num_carets": 5
        })

        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            (test: sep { . })
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.InvalidDelimiterError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Cannot add iterator delimiters to <[Named Section (test: ...)]>",
            "line": 4,
            "column": 8,
            "grammar_snippet": "(test: sep { . })",
            "tree_type": "Element",
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Named Section (test: ...)]>']
            ],
            "num_carets": 5
        })


    def test_duplicate_delimiter_error(self):
        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            *(test: sep { . } sep { $ })
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.DuplicateDelimiterError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Multiple iterator delimiters defined for <[Zero or More *(test: ...)]>",
            "line": 4,
            "column": 19,
            "grammar_snippet": "*(test: sep { . } sep { $ })",
            "tree_type": "Element",
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Zero or More *(test: ...)]>'],
                [1, '<[Iterator Delimiter sep {...}]>'],
                [2, '<[Any String .]>']
            ],
            "num_carets": 5
        })

        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            *(test: sep { . } 'test' sep { $ })
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.DuplicateDelimiterError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Multiple iterator delimiters defined for <[Zero or More *(test: ...)]>",
            "line": 4,
            "column": 26,
            "grammar_snippet": "*(test: sep { . } 'test' sep { $ })",
            "tree_type": "Element",
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Zero or More *(test: ...)]>'],
                [1, '<[String Literal test]>'],
                [1, '<[Iterator Delimiter sep {...}]>'],
                [2, '<[Any String .]>']
            ],
            "num_carets": 5
        })

    def test_extra_closing_brackets_error(self):
        grammar_string = textwrap.dedent("""
            'test' )
        """)
        e = self.get_exception(grammar_string, errors.ExtraClosingBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Extra closing brackets given; found an extra: )",
            "line": 2,
            "column": 8,
            "grammar_snippet": "'test' )",
            "tree_type": "Element",
            "grammar_tree": [
                [0, '<[String Literal test]>']
            ],
            "num_carets": 1
        })

        grammar_string = textwrap.dedent(")")
        e = self.get_exception(grammar_string, errors.ExtraClosingBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Extra closing brackets given; found an extra: )",
            "line": 1,
            "column": 1,
            "grammar_snippet": ")",
            "num_carets": 1
        })

    def test_extra_opening_brackets_error(self):
        grammar_string = textwrap.dedent("{")
        e = self.get_exception(grammar_string, errors.ExtraOpeningBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Extra opening brackets given; <[One of Set {...}]> was not closed",
            "line": 1,
            "column": 1,
            "grammar_snippet": "{",
            "num_carets": 1,
            "grammar_tree": [
                [0, '<[One of Set {...}]>']
            ],
            "tree_type": "Element"
        })

        grammar_string = textwrap.dedent("*(a:")
        e = self.get_exception(grammar_string, errors.ExtraOpeningBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Extra opening brackets given; <[Zero or More *(a: ...)]> was not closed",
            "line": 1,
            "column": 1,
            "grammar_snippet": "*(a:",
            "num_carets": 4,
            "grammar_tree": [
                [0, '<[Zero or More *(a: ...)]>']
            ],
            "tree_type": "Element"
        })

        grammar_string = textwrap.dedent("(section:")
        e = self.get_exception(grammar_string, errors.ExtraOpeningBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Extra opening brackets given; <[Named Section (section: ...)]> was not closed",
            "line": 1,
            "column": 1,
            "grammar_snippet": "(section:",
            "num_carets": 9,
            "grammar_tree": [
                [0, '<[Named Section (section: ...)]>']
            ],
            "tree_type": "Element"
        })

        grammar_string = textwrap.dedent("+(abc: 'test' ) <test:")
        e = self.get_exception(grammar_string, errors.ExtraOpeningBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Extra opening brackets given; <[Named Element <test: ...>]> was not closed",
            "line": 1,
            "column": 17,
            "grammar_snippet": "+(abc: 'test' ) <test:",
            "num_carets": 6,
            "grammar_tree": [
                [0, '<[One or More +(abc: ...)]>'],
                [1, '<[String Literal test]>'],
                [0, '<[Named Element <test: ...>]>']
            ],
            "tree_type": "Element"
        })

        grammar_string = textwrap.dedent("'test' ?( 'test'")
        e = self.get_exception(grammar_string, errors.ExtraOpeningBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Extra opening brackets given; <[Zero or One ?(...)]> was not closed",
            "line": 1,
            "column": 8,
            "grammar_snippet": "'test' ?( 'test'",
            "num_carets": 2,
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[Zero or One ?(...)]>'],
                [1, '<[String Literal test]>'],
            ],
            "tree_type": "Element"
        })

        grammar_string = textwrap.dedent("'test' +(a:")
        e = self.get_exception(grammar_string, errors.ExtraOpeningBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Extra opening brackets given; <[One or More +(a: ...)]> was not closed",
                "line": 1,
                "column": 8,
                "grammar_snippet": "'test' +(a:",
                "num_carets": 4,
                "grammar_tree": [
                    [0, '<[String Literal test]>'],
                    [0, '<[One or More +(a: ...)]>'],
                ],
                "tree_type": "Element"
            })

    def test_mismatched_brackets_error(self):
        grammar_string = textwrap.dedent("'test' { . )")
        e = self.get_exception(grammar_string, errors.MismatchedBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Mismatched brackets given; got: ), expecting closing brackets for: <[One of Set {...}]>",
            "line": 1,
            "column": 12,
            "grammar_snippet": "'test' { . )",
            "num_carets": 1,
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[One of Set {...}]>'],
                [1, '<[Any String .]>']
            ],
            "tree_type": "Element"
        })

        grammar_string = textwrap.dedent("'test' { . >")
        e = self.get_exception(grammar_string, errors.MismatchedBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Mismatched brackets given; got: >, expecting closing brackets for: <[One of Set {...}]>",
            "line": 1,
            "column": 12,
            "grammar_snippet": "'test' { . >",
            "num_carets": 1,
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[One of Set {...}]>'],
                [1, '<[Any String .]>']
            ],
            "tree_type": "Element"
        })

        grammar_string = textwrap.dedent("'test' { . >")
        e = self.get_exception(grammar_string, errors.MismatchedBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Mismatched brackets given; got: >, expecting closing brackets for: <[One of Set {...}]>",
            "line": 1,
            "column": 12,
            "grammar_snippet": "'test' { . >",
            "num_carets": 1,
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[One of Set {...}]>'],
                [1, '<[Any String .]>']
            ],
            "tree_type": "Element"
        })

        grammar_string = textwrap.dedent("'test' { . > $")
        e = self.get_exception(grammar_string, errors.MismatchedBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Mismatched brackets given; got: >, expecting closing brackets for: <[One of Set {...}]>",
            "line": 1,
            "column": 12,
            "grammar_snippet": "'test' { . > $",
            "num_carets": 1,
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[One of Set {...}]>'],
                [1, '<[Any String .]>']
            ],
            "tree_type": "Element"
        })

        grammar_string = textwrap.dedent("'test' *(a: . > $")
        e = self.get_exception(grammar_string, errors.MismatchedBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Mismatched brackets given; got: >, expecting closing brackets for: <[Zero or More *(a: ...)]>",
            "line": 1,
            "column": 15,
            "grammar_snippet": "'test' *(a: . > $",
            "num_carets": 1,
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[Zero or More *(a: ...)]>'],
                [1, '<[Any String .]>']
            ],
            "tree_type": "Element"
        })

        grammar_string = textwrap.dedent("'test' +(a: . } $")
        e = self.get_exception(grammar_string, errors.MismatchedBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Mismatched brackets given; got: }, expecting closing brackets for: <[One or More +(a: ...)]>",
            "line": 1,
            "column": 15,
            "grammar_snippet": "'test' +(a: . } $",
            "num_carets": 1,
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[One or More +(a: ...)]>'],
                [1, '<[Any String .]>']
            ],
            "tree_type": "Element"
        })

        grammar_string = textwrap.dedent("'test' <a: . } $")
        e = self.get_exception(grammar_string, errors.MismatchedBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Mismatched brackets given; got: }, expecting closing brackets for: <[Named Element <a: ...>]>",
            "line": 1,
            "column": 14,
            "grammar_snippet": "'test' <a: . } $",
            "num_carets": 1,
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[Named Element <a: ...>]>'],
                [1, '<[Any String .]>']
            ],
            "tree_type": "Element"
        })

        grammar_string = textwrap.dedent("'test' <a: . ) $")
        e = self.get_exception(grammar_string, errors.MismatchedBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Mismatched brackets given; got: ), expecting closing brackets for: <[Named Element <a: ...>]>",
            "line": 1,
            "column": 14,
            "grammar_snippet": "'test' <a: . ) $",
            "num_carets": 1,
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[Named Element <a: ...>]>'],
                [1, '<[Any String .]>']
            ],
            "tree_type": "Element"
        })

        grammar_string = textwrap.dedent("*(a: 'test' sep { . ) $")
        e = self.get_exception(grammar_string, errors.MismatchedBracketsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Mismatched brackets given; got: ), expecting closing brackets for: <[Iterator Delimiter sep {...}]>",
            "line": 1,
            "column": 21,
            "grammar_snippet": "*(a: 'test' sep { . ) $",
            "num_carets": 1,
            "grammar_tree": [
                [0, '<[Zero or More *(a: ...)]>'],
                [1, '<[String Literal test]>'],
                [1, '<[Iterator Delimiter sep {...}]>'],
                [2, '<[Any String .]>']
            ],
            "tree_type": "Element"
        })

    def test_named_element_contents_error(self):
        # Test passing two contents
        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            $ <test: 'test' .> $
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.NamedElementContentsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "<[Named Element <test: ...>]> cannot contain more than one element, already contains: <[String Literal test]>",
            "line": 4,
            "column": 17,
            "grammar_snippet": "$ <test: 'test' .> $",
            "tree_type": "Element",
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Newline $]>'],
                [0, '<[Named Element <test: ...>]>'],
                [1, '<[String Literal test]>']
            ],
            "num_carets": 1
        })

        # Test passing non-singular elements
        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            $ <test: {'test' .}> $
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.NamedElementContentsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "<[Named Element <test: ...>]> can only contain singular elements, not <[One of Set {...}]>",
            "line": 4,
            "column": 10,
            "grammar_snippet": "$ <test: {'test' .}> $",
            "tree_type": "Element",
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Newline $]>'],
                [0, '<[Named Element <test: ...>]>']
            ],
            "num_carets": 1
        })

        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            $ <test: (a:'test' .)> $
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.NamedElementContentsError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "<[Named Element <test: ...>]> can only contain singular elements, not <[Named Section (a: ...)]>",
            "line": 4,
            "column": 10,
            "grammar_snippet": "$ <test: (a:'test' .)> $",
            "tree_type": "Element",
            "grammar_tree": [
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[String Literal test]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Any String .]>'],
                [0, '<[Newline $]>'],
                [0, '<[Named Element <test: ...>]>']
            ],
            "num_carets": 3
        })

    def test_sub_grammars_disabled_error(self):
        grammar_string = textwrap.dedent("""
            def test { . }
            'test' 'test' 'test'
            . . .
            $ <test: .> $
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.SubGrammarsDisabledError, False)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Cannot define sub grammar test while allow_sub_grammar_definitions is False",
            "line": 2,
            "column": 1,
            "grammar_snippet": "def test { . }",
            "num_carets": 10
        })

    def test_sub_grammar_scope_error(self):
        grammar_string = textwrap.dedent("""
            'test' 'test' 'test'
            . . .
            { def testg { . } }
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.SubGrammarScopeError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Error defining sub grammar testg. Sub Grammars can only be defined globally or within other sub grammars, not inside a: <[One of Set {...}]>",
            "line": 4,
            "column": 3,
            "grammar_snippet": "{ def testg { . } }",
            "num_carets": 11
        })

        grammar_string = textwrap.dedent("""
            def q {
                def q2{ $ }
                .
            }

            'test' 'test' 'test'
            . . .
            <test: def testg { . } >
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.SubGrammarScopeError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Error defining sub grammar testg. Sub Grammars can only be defined globally or within other sub grammars, not inside a: <[Named Element <test: ...>]>",
            "line": 9,
            "column": 8,
            "grammar_snippet": "<test: def testg { . } >",
            "num_carets": 11,
            "grammar_tree": [
                [0, '<[Sub Grammar def q { ... }]>'],
                [1, '<[Any String .]>'],
                [1, '<[Sub Grammar def q2 { ... }]>'],
                [2, '<[Newline $]>']
            ],
            "tree_type": "Sub"
        })

        grammar_string = textwrap.dedent("""
            def q { . }
            'test' 'test' 'test'
            . . .
            ?( { def testg { . } } )
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.SubGrammarScopeError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Error defining sub grammar testg. Sub Grammars can only be defined globally or within other sub grammars, not inside a: <[One of Set {...}]>",
            "line": 5,
            "column": 6,
            "grammar_snippet": "?( { def testg { . } } )",
            "num_carets": 11,
            "grammar_tree": [
                [0, '<[Sub Grammar def q { ... }]>'],
                [1, '<[Any String .]>']
            ],
            "tree_type": "Sub"
        })

    def test_undefined_sub_grammar_error(self):
        grammar_string = textwrap.dedent("""
            def q { . }
            'test' 'test' 'test'
            . . .
            r()
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.UndefinedSubGrammarError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Sub grammar r does not exist",
            "line": 5,
            "column": 1,
            "grammar_snippet": "r()",
            "num_carets": 3,
            "grammar_tree": [
                [0, '<[Sub Grammar def q { ... }]>'],
                [1, '<[Any String .]>']
            ],
            "tree_type": "Sub"
        })

        grammar_string = textwrap.dedent("""
            def q {
                q()
            }
            'test' 'test' 'test'
            . . .
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.UndefinedSubGrammarError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Sub grammar q does not exist",
            "line": 3,
            "column": 5,
            "grammar_snippet": "q()",
            "num_carets": 3
        })

        grammar_string = textwrap.dedent("""
            def q {
                def r2 { . }
            }
            r2()
            'test' 'test' 'test'
            . . .
            "test" "test" "test"
        """)
        e = self.get_exception(grammar_string, errors.UndefinedSubGrammarError)
        error_details = self._parse_grammar_parsing_error_string(e)
        self.assertDictEqual(error_details, {
            "err_msg": "Sub grammar r2 does not exist",
            "line": 5,
            "column": 1,
            "grammar_snippet": "r2()",
            "num_carets": 4,
            "grammar_tree": [
                [0, '<[Sub Grammar def q { ... }]>'],
                [1, '<[Sub Grammar def r2 { ... }]>'],
                [2, '<[Any String .]>']
            ],
            "tree_type": "Sub"
        })
