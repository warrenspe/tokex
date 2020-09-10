import re

from tokex.tokenizers import TokexTokenizer
import _test_case

class TestTokenizer(_test_case.TokexTestCase):

    input_string = r"""
        separate words which should be tokenized _separate_ly_
        (words) [to] {be} <tokenized> #separately# $from$ ;their; |surrounding| !characters!

        == <= >= != ... !=...<=
    """

    def test_tokenizer(self):
        tokenizer = TokexTokenizer()

        self.assertEqual(tokenizer.tokenize(self.input_string), [
            "separate", "words", "which", "should", "be", "tokenized", "_separate_ly_",
            "(", "words", ")", "[", "to", "]", "{", "be", "}", "<", "tokenized", ">", "#", "separately", "#",
            "$", "from", "$", ";", "their", ";", "|", "surrounding", "|", "!", "characters", "!",
            "==", "<=", ">=", "!=", "...", "!=...<="

        ])

    def test_tokenize_newlines(self):
        tokenizer = TokexTokenizer(tokenize_newlines=True)

        self.assertEqual(tokenizer.tokenize(self.input_string), [
            "\n", "separate", "words", "which", "should", "be", "tokenized", "_separate_ly_", "\n",
            "(", "words", ")", "[", "to", "]", "{", "be", "}", "<", "tokenized", ">", "#", "separately", "#",
            "$", "from", "$", ";", "their", ";", "|", "surrounding", "|", "!", "characters", "!", "\n", "\n",
            "==", "<=", ">=", "!=", "...", "!=...<=", "\n"
        ])

        tokenizer = TokexTokenizer(tokenize_newlines=True, ignore_empty_lines=True)

        self.assertEqual(tokenizer.tokenize(self.input_string), [
            "separate", "words", "which", "should", "be", "tokenized", "_separate_ly_", "\n",
            "(", "words", ")", "[", "to", "]", "{", "be", "}", "<", "tokenized", ">", "#", "separately", "#",
            "$", "from", "$", ";", "their", ";", "|", "surrounding", "|", "!", "characters", "!", "\n",
            "==", "<=", ">=", "!=", "...", "!=...<=", "\n"
        ])
