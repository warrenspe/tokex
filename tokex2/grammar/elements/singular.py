import re

from .. import flags

from ._base_grammar_element import BaseGrammarElement

class BaseSingularElement(BaseGrammarElement):
    """ Base class for singular elements, as most share a similar process flow """

    def _apply_first(self, string_tokens, idx):
        """
        Function which performs initial checking of the string/tokens idx

        Outputs: If successful, a string containing the token to match.
                 If unsuccessful, None
        """

        # If the index we're considering is beyond the end of our tokens, we have nothing to match on. Return False.
        if idx >= len(string_tokens):
            return None

        to_match = string_tokens[idx]

        if self.has_flag(flags.CASE_INSENSITIVE):
            to_match = to_match.lower()

        if self.has_flag(flags.QUOTED):
            if to_match[0] not in ('"', "'") or to_match[-1] not in ('"', "'"):
                return None

            to_match = to_match[1:-1]

        elif self.has_flag(flags.UNQUOTED):
            if to_match[0] in ('"', "'") or to_match[-1] in ('"', "'"):
                return None

        return to_match


class AnythingElement(BaseSingularElement):
    @classmethod
    def _grammar_tokens(cls):
        return [
            cls.create_grammar_token(
                r"\.",
                flags=[
                    flags.QUOTED,
                    flags.UNQUOTED
                ]
            )
        ]

    def _apply(self, string_tokens, idx):
        if self._apply_first(string_tokens, idx):
            return True, idx + 1, None

        return False, None, None


class NewlineElement(BaseSingularElement):
    @classmethod
    def _grammar_tokens(cls):
        return [
            cls.create_grammar_token(r"\$"),
            flags=[
                flags.NOT
            ]
        ]

    def _apply(self, string_tokens, idx):
        to_match = self._apply_first(string_tokens, idx)

        if to_match == "\n":
            return True, idx + 1, None

        return False, None, None



class LiteralStringElement(BaseSingularElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.has_flag(flags.CASE_INSENSITIVE):
            self.token_str = self.token_str.lower()

    @classmethod
    def _grammar_tokens(cls):
        return [
            cls.create_grammar_token(
                r"'.*?(?<!\\)'",
                flags=[
                    flags.QUOTED,
                    flags.UNQUOTED,
                    flags.CASE_INSENSITIVE,
                    flags.CASE_SENSITIVE,
                    flags.NOT
                ]
            ),
            cls.create_grammar_token(
                r'".*?(?<!\\)"',
                flags=[
                    flags.QUOTED,
                    flags.UNQUOTED,
                    flags.CASE_INSENSITIVE,
                    flags.CASE_SENSITIVE,
                    flags.NOT
                ]
            )
        ]

    def _apply(self, string_tokens, idx):
        to_match = self._apply_first(string_tokens, idx)

        if to_match is not None:
            matches = token_to_match == self.token_str
            if matches ^ self.has_flag(flags.NOT):
                return True, idx + 1, None

        return False, None, None

class RegexStringElement(BaseSingularElement):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.regex = re.compile(
            self.token_str,
            flags=re.I if self.has_flag(flags.CASE_INSENSITIVE) else 0
        )

    @classmethod
    def _grammar_tokens(cls):
        return [
            cls.create_grammar_token(
                r"~.*?(?<!\\)~",
                flags=[
                    flags.QUOTED,
                    flags.UNQUOTED,
                    flags.CASE_INSENSITIVE,
                    flags.CASE_SENSITIVE,
                    flags.NOT
                ]
            )
        ]

    def _apply(self, string_tokens, idx):
        to_match = self._apply_first(string_tokens, idx)

        if to_match is not None:
            matches = self.regex.match(to_match):

            if matches ^ self.has_flag(flags.NOT):
                return True, idx + 1, None

        return False, None, None
