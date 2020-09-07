import re

from .. import flags

from ._base_grammar_element import BaseElement

class BaseSingular(BaseElement):
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
            if to_match[0] not in ('"', "'") or to_match[-1] != to_match[0]:
                return None

            to_match = to_match[1:-1]

        elif self.has_flag(flags.NOT) and self.has_flag(flags.QUOTED):
            if to_match[0] in ('"', "'") and to_match[-1] == to_match[0]:
                return None

        return to_match


class AnyString(BaseSingular):
    human_readable_name = 'Any String [ . ]'
    valid_flags = {
        flags.QUOTED,
        flags.NOT
    }

    def _apply(self, string_tokens, idx):
        if self._apply_first(string_tokens, idx):
            return True, idx + 1, None

        return False, None, None


class Newline(BaseSingular):
    human_readable_name = 'Newline [ $ ]'

    def _apply(self, string_tokens, idx):
        to_match = self._apply_first(string_tokens, idx)

        if to_match == "\\n":
            return True, idx + 1, None

        return False, None, None


class StringLiteral(BaseSingular):
    human_readable_name = 'String Literal [ "..." ]'
    valid_flags = {
        flags.CASE_SENSITIVE,
        flags.CASE_INSENSITIVE,
        flags.QUOTED,
        flags.NOT
    }

    def setup(self):
        if self.has_flag(flags.CASE_INSENSITIVE):
            self.token_str = self.token_str.lower()

    def _apply(self, string_tokens, idx):
        to_match = self._apply_first(string_tokens, idx)

        if to_match is not None:
            matches = (to_match == self.token_str)
            if matches ^ self.has_flag(flags.NOT):
                return True, idx + 1, None

        return False, None, None

class RegexString(BaseSingular):
    human_readable_name = 'Regular Expression [ ~...~ ]'
    valid_flags = {
        flags.CASE_SENSITIVE,
        flags.QUOTED,
        flags.NOT
    }

    def setup(self):
        self.regex = re.compile(
            self.token_str,
            flags=re.I if self.has_flag(flags.CASE_INSENSITIVE) else 0
        )

    def _apply(self, string_tokens, idx):
        to_match = self._apply_first(string_tokens, idx)

        if to_match is not None:
            matches = self.regex.match(to_match)

            if matches ^ self.has_flag(flags.NOT):
                return True, idx + 1, None

        return False, None, None
