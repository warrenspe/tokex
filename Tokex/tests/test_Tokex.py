# Project imports
import tests
import Tokex

class TestTokex(tests.TokexTestCase):

    def testTokexMatch(self):
        self.assertIsNotNone(Tokex.match('"a" "b" "c"', 'a b c'))
        self.assertIsNone(Tokex.match('"a" "b" "c"', 'a b c d'))
        self.assertIsNotNone(Tokex.match('"a" "b" "c"', 'a b c d', matchEntirety=False))
        self.assertIsNone(Tokex.match('"a" "b" "c"', 'a', matchEntirety=False))

        parser2 = Tokex.compile("'a' @b: 'b' @@ @b@")

        self.assertIsNotNone(Tokex.match("'a' @b: 'b' @@ @b@", 'a b'))
        self.assertIsNone(Tokex.match("'a' @b: 'b' @@ @b@", 'a b c'))
        self.assertIsNotNone(Tokex.match("'a' @b: 'b' @@ @b@", 'a b c', matchEntirety=False))
        self.assertIsNone(Tokex.match("'a' @b: 'b' @@ @b@", 'a', matchEntirety=False))


    def testTokexCompile(self):
        parser = Tokex.compile('"a" "b" "c"')

        self.assertIsInstance(parser, Tokex._StringParser)

        self.assertIsNotNone(parser.match('a b c'))
        self.assertIsNone(parser.match('a b c d'))
        self.assertIsNotNone(parser.match('a b c d', matchEntirety=False))
        self.assertIsNone(parser.match('a', matchEntirety=False))

        parser2 = Tokex.compile("'a' @b: 'b' @@ @b@")

        self.assertIsInstance(parser2, Tokex._StringParser)
        self.assertIsNotNone(parser2.match('a b'))
        self.assertIsNone(parser2.match('a b c'))
        self.assertIsNotNone(parser2.match('a b c', matchEntirety=False))
        self.assertIsNone(parser2.match('a', matchEntirety=False))
