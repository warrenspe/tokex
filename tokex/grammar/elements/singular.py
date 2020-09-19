import re

from ... import errors
from .. import flags

from ._base_element import BaseElement

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

        is_quoted = to_match[0] in ('"', "'") and to_match[-1] == to_match[0]

        if self.has_flag(flags.QUOTED):
            if is_quoted:
                return to_match[1:-1]

            return None

        if self.has_flag(flags.UNQUOTED) and is_quoted:
            return None

        return to_match


class AnyString(BaseSingular):
    valid_flags = {
        flags.QUOTED,
        flags.UNQUOTED
    }

    def human_readable_name(self):
        return "Any String ."

    def _apply(self, string_tokens, idx):
        if self._apply_first(string_tokens, idx) is not None:
            return True, idx + 1, None

        return False, None, None


class Newline(BaseSingular):
    def human_readable_name(self):
        return "Newline $"

    def _apply(self, string_tokens, idx):
        to_match = self._apply_first(string_tokens, idx)

        if to_match == "\n":
            return True, idx + 1, None

        return False, None, None


class StringLiteral(BaseSingular):
    valid_flags = {
        flags.CASE_SENSITIVE,
        flags.CASE_INSENSITIVE,
        flags.QUOTED,
        flags.UNQUOTED,
        flags.NOT
    }

    def setup(self):
        if self.token_str:
            # Strip the ' / " away
            self.token_str = self.token_str[1:-1]

            if self.has_flag(flags.CASE_INSENSITIVE):
                self.token_str = self.token_str.lower()

    def human_readable_name(self):
        return "String Literal %s" % self.token_str

    def _apply(self, string_tokens, idx):
        to_match = self._apply_first(string_tokens, idx)

        if to_match is not None:
            matches = (to_match == self.token_str)
            if matches ^ self.has_flag(flags.NOT):
                return True, idx + 1, None

        return False, None, None

class RegexString(BaseSingular):
    valid_flags = {
        flags.CASE_SENSITIVE,
        flags.CASE_INSENSITIVE,
        flags.QUOTED,
        flags.UNQUOTED,
        flags.NOT
    }

    def setup(self):
        if self.token_str:
            # Strip the ~ away
            self.token_str = self.token_str[1:-1]

            if self.has_flag(flags.CASE_INSENSITIVE):
                self.token_str = self.token_str.lower()

            try:
                self.regex = re.compile(self.token_str)

            except re.error:
                raise errors.InvalidRegexError(self.token_str)

    def human_readable_name(self):
        return "Regular Expression %s" % self.token_str

    def _apply(self, string_tokens, idx):
        to_match = self._apply_first(string_tokens, idx)

        if to_match is not None:
            matches = bool(self.regex.match(to_match))

            if matches ^ self.has_flag(flags.NOT):
                return True, idx + 1, None

        return False, None, None
