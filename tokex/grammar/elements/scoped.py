from ... import errors

from ._base_grammar_element import BaseScopedElement
from .singular import BaseSingular

class Grammar(BaseScopedElement):
    """ Optionally named element which contains other grammar elements. """

    human_readable_name = 'Named Section (name: ...)'
    name = None
    delimiter_grammar = None

    def setup(self):
        self.name = self.token_str[self.token_str.index("("):] or None

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

        outputs = {}

        for sub_element in self.sub_elements:
            match, idx, output = sub_element.apply(string_tokens, idx)

            if not match:
                return False, None, None

            if output is not None:
                outputs.update(output)

        return True, idx, outputs or None

    def _apply(self, string_tokens, idx):
        match, new_idx, output = self._apply_sub_elements(string_tokens, idx)

        if match:
            return True, new_idx, {self.name: output}

        return False, None, None


class NamedElementToken(Grammar):
    human_readable_name = 'Any String [ . ]'

    def add_sub_element(self, sub_element):
        """
        Adds a sub element to this NamedElementToken.  This is used in places such as zero or more for example,
        where the zero or more element will contain one or more sub elements

        Inputs: sub_element - The element to add as a sub element of this element.
                              Should be a subclass of BaseGrammar
        """

        if len(self.sub_elements):
            raise errors.GrammarParsingError("%r cannot contain more than one element, already contains: %r" % (self, self.sub_elements[0]))

        if not isinstance(sub_element, BaseSingular):
            raise errors.GrammarParsingError("%r can only contain singular elements, not %r" % (self, sub_element))

        self.sub_elements.append(sub_element)

    def _apply(self, string_tokens, idx):
        match, new_idx, _ = self.sub_elements.apply(string_tokens, idx)

        if match:
            return True, new_idx, {self.name: string_tokens[idx]}

        return False, None, None


class ZeroOrOne(Grammar):
    """ Element which can match a contained grammar zero or one times """

    def _apply(self, string_tokens, idx):
        # If the index we're considering is beyond the end of our tokens we have nothing to match on.  However, since
        # we can match zero times, return True.  This allows gramars with trailing ZeroOrOne rules to match strings
        # which don't use them.
        if idx >= len(string_tokens):
            return True, idx, None

        match, new_idx, output = self._apply_sub_elements(string_tokens, idx)

        if match:
            return True, new_idx, ({self.name: output} if output else None)

        return True, idx, None


class ZeroOrMore(Grammar):
    """ Element which can match a contained grammar zero or more times """

    minimum_matches = 0

    def _apply(self, string_tokens, idx):
        # If the index we're considering is beyond the end of our tokens we have nothing to match on.  However, since
        # we can match zero times, return True.  This allows gramars with trailing ZeroOrMore rules to match strings
        # which don't use them.
        if idx >= len(string_tokens):
            return True, idx, None

        match_count = 0
        current_idx = idx
        outputs = []
        while current_idx < len(string_tokens):
            match, new_idx, output = self._apply_sub_elements(string_tokens, idx)

            # If we're not processing the first match, check that any delimiter grammar we may have matches before
            # the next occurance of our grammar
            delimiter_output = None
            if match_count > 0 and self.delimiter_grammar is not None:
                match, idx, delimiter_output = self.delimiter_grammar.apply(string_tokens, idx)

                if not match:
                    break

            match, idx, output = Grammar.apply(self, string_tokens, idx)

            if not match or idx == current_idx:
                break

            self.match_count += 1
            if delimiter_output:
                outputs[-1] = {**outputs[-1], **delimiter_output}
            outputs.append(output)
            current_idx = idx

        if match_count > self.minimum_matches:
            return True, current_idx, ({self.name: outputs} if outputs else None)

        return False, None, None


class OneOrMore(ZeroOrMore):
    """ Element which can match a contained grammar one or more times """

    minimum_matches = 1


class OneOfSet(Grammar):
    """ Element which can match any one of its contained grammars """

    def _apply(self, string_tokens, idx):
        for element in self.sub_elements:
            match, new_idx, output = element.match(string_tokens, idx)
            if match:
                return True, new_idx, output

        return False, None, None
