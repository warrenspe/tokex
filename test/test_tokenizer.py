import re

from tokex import tokenizers
import _test_case

class TestTokenizer(_test_case.TokexTestCase):

    input_string = r"""
        separate words which should be tokenized _separate_ly_
        (words) [to] {be} <tokenized> #separately# $from$ ;their; |surrounding| !characters!

        == <= >= != ... !=...<=
    """

    def test_tokenizer(self):
        tokenizer = tokenizers.TokexTokenizer()

        self.assertEqual(tokenizer.tokenize(self.input_string), [
            "separate", "words", "which", "should", "be", "tokenized", "_separate_ly_",
            "(", "words", ")", "[", "to", "]", "{", "be", "}", "<", "tokenized", ">", "#", "separately", "#",
            "$", "from", "$", ";", "their", ";", "|", "surrounding", "|", "!", "characters", "!",
            "==", "<=", ">=", "!=", "...", "!=...<="

        ])

    def test_tokenize_newlines(self):
        tokenizer = tokenizers.TokexTokenizer(tokenize_newlines=True)

        self.assertEqual(tokenizer.tokenize(self.input_string), [
            "\n", "separate", "words", "which", "should", "be", "tokenized", "_separate_ly_", "\n",
            "(", "words", ")", "[", "to", "]", "{", "be", "}", "<", "tokenized", ">", "#", "separately", "#",
            "$", "from", "$", ";", "their", ";", "|", "surrounding", "|", "!", "characters", "!", "\n", "\n",
            "==", "<=", ">=", "!=", "...", "!=...<=", "\n"
        ])

        tokenizer = tokenizers.TokexTokenizer(tokenize_newlines=True, ignore_empty_lines=True)

        self.assertEqual(tokenizer.tokenize(self.input_string), [
            "separate", "words", "which", "should", "be", "tokenized", "_separate_ly_", "\n",
            "(", "words", ")", "[", "to", "]", "{", "be", "}", "<", "tokenized", ">", "#", "separately", "#",
            "$", "from", "$", ";", "their", ";", "|", "surrounding", "|", "!", "characters", "!", "\n",
            "==", "<=", ">=", "!=", "...", "!=...<=", "\n"
        ])


class TestNumericTokenizer(_test_case.TokexTestCase):

    input_string = r"""
        separate words which should be tokenized _separate_ly_

        $1230.1230 123. 12430$ 123,123 1234 123.123

        == <= >= != ... !=...<=
    """

    def test_numeric_tokenizer(self):
        tokenizer = tokenizers.NumericTokenizer()

        self.assertEqual(tokenizer.tokenize(self.input_string), [
            "separate", "words", "which", "should", "be", "tokenized", "_separate_ly_",

            "$1230.1230", "123.", "12430$", "123,123", "1234", "123.123",

            "==", "<=", ">=", "!=", "...", "!=...<="
        ])
