import re

from .. import flags

from ._base_grammar_element import BaseGrammarElement

class BaseScopedElement(BaseGrammarElement):
    """ Base class for scoped elements, as several share a similar process flow """

    def _apply_sub_elements(self, string_tokens, idx):
        """
        Function which applies the sub elements of this element to the input tokens to see if they match

        Outputs: If our sub elements don't match the string tokens, False, None, None
                 Otherwise: A triple containing: {
                     match: A boolean depicting whether or not this construct matches the iterable at the current position.
                     new_idx: The index this construct ceased matching upon the iterable, if match is True. Else None
                     output: A list of all returned dictionaries from the sub elements
                 )
        """

        outputs = []

        for sub_element in sub_elements:
            match, idx, output = sub_element.apply(string_tokens, idx)

            if not match:
                return False, None, None

            if output is not None:
                outputs.append(output)

        return True, idx, outputs



class ZeroOrOne(BaseScopedElement):
    """ Element which can match a contained grammar zero or one times """

    def _apply(self, string_tokens, idx):
        # If the index we're considering is beyond the end of our tokens we have nothing to match on.  However, since
        # we can match zero times, return True.  This allows gramars with trailing ZeroOrOne rules to match strings
        # which don't use them.
        if idx >= len(string_tokens):
            return True, idx, None

        _, new_idx, output = super(ZeroOrOne, self).match(string_tokens, idx)

        return True, new_idx or idx, (None if output is None else output[self.name])
