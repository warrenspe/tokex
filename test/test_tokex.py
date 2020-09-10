import _test_case
import tokex
from tokex.utils.string_parser import StringParser

class TestTokex(_test_case.TokexTestCase):

    def test_tokex_match(self):
        self.assertIsNotNone(tokex.match('"a" "b" "c"', 'a b c'))
        self.assertIsNone(tokex.match('"a" "b" "c"', 'a b c d'))
        self.assertIsNotNone(tokex.match('"a" "b" "c"', 'a b c d', match_entirety=False))
        self.assertIsNone(tokex.match('"a" "b" "c"', 'a', match_entirety=False))

        parser2 = tokex.compile("'a' @b: 'b' @@ @b@")

        self.assertIsNotNone(tokex.match("'a' @b: 'b' @@ @b@", 'a b'))
        self.assertIsNone(tokex.match("'a' @b: 'b' @@ @b@", 'a b c'))
        self.assertIsNotNone(tokex.match("'a' @b: 'b' @@ @b@", 'a b c', match_entirety=False))
        self.assertIsNone(tokex.match("'a' @b: 'b' @@ @b@", 'a', match_entirety=False))


    def test_tokex_compile(self):
        parser = tokex.compile('"a" "b" "c"')

        self.assertIsInstance(parser, StringParser)

        self.assertIsNotNone(parser.match('a b c'))
        self.assertIsNone(parser.match('a b c d'))
        self.assertIsNotNone(parser.match('a b c d', match_entirety=False))
        self.assertIsNone(parser.match('a', match_entirety=False))

        parser2 = tokex.compile("'a' @b: 'b' @@ @b@")

        self.assertIsInstance(parser2, StringParser)
        self.assertIsNotNone(parser2.match('a b'))
        self.assertIsNone(parser2.match('a b c'))
        self.assertIsNotNone(parser2.match('a b c', match_entirety=False))
        self.assertIsNone(parser2.match('a', match_entirety=False))
