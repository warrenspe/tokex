from ... import errors

from ._base_element import BaseScopedElement
from .singular import BaseSingular


class Grammar(BaseScopedElement):
    """ Named element which contains other grammar elements. """

    can_have_delimiter = False
    delimiter_grammar = None

    def setup(self):
        if self.token_str:
            self.name = self.name_re.search(self.token_str)
            if self.name:
                self.name = self.name.group()

    def human_readable_name(self):
        return "Named Section (%s: ...)" % self.name

    def _apply_sub_elements(self, string_tokens, idx):
        """
        Function which applies the sub elements of this element to the input tokens to see if they match

        Outputs: If our sub elements don't match the string tokens, False, None, None
                 Otherwise: A triple containing: {
                     match: A boolean depicting whether or not this construct matches the
                            iterable at the current position.
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


class NamedElement(Grammar):
    """ Named element which contains another singular element """

    def add_sub_element(self, sub_element):
        """
        Adds a sub element to this NamedElement.  This is used in places such as zero or more for example,
        where the zero or more element will contain one or more sub elements

        Inputs: sub_element - The element to add as a sub element of this element.
                              Should be a subclass of BaseGrammar
        """

        if self.sub_elements:
            raise errors.GrammarParsingError("%r cannot contain more than one element, already contains: %r" %
                                             (self, self.sub_elements[0]))

        if not isinstance(sub_element, BaseSingular):
            raise errors.GrammarParsingError("%r can only contain singular elements, not %r" % (self, sub_element))

        self.sub_elements.append(sub_element)

    def human_readable_name(self):
        return "Named Element <%s: ...>" % self.name

    def _apply(self, string_tokens, idx):
        if not self.sub_elements:
            return True, idx, None

        match, new_idx, _ = self.sub_elements[0].apply(string_tokens, idx)

        if match:
            return True, new_idx, {self.name: string_tokens[idx]}

        return False, None, None


class IteratorDelimiter(Grammar):
    """
    Element which can appear inside of another scoped container and causes the parent container to only
    match more than once if the delimiter matches between iterations
    """

    def setup(self):
        pass

    def human_readable_name(self):
        return "Iterator delimiter sep { ... }"

    def _apply(self, string_tokens, idx):
        match, idx, output = super(IteratorDelimiter, self)._apply(string_tokens, idx)

        if match and output is not None:
            output = output[None]

        return match, idx, output


class ZeroOrOne(Grammar):
    """ Element which can match a contained grammar zero or one times """

    def human_readable_name(self):
        return "Zero or One ?(%s: ...)" % self.name

    def _apply(self, string_tokens, idx):
        # If the index we're considering is beyond the end of our tokens we have nothing to match on.  However, since
        # we can match zero times, return True.  This allows gramars with trailing ZeroOrOne rules to match strings
        # which don't use them.
        if idx >= len(string_tokens):
            return True, idx, None

        match, new_idx, output = self._apply_sub_elements(string_tokens, idx)

        if match:
            if self.name:
                return True, new_idx, ({self.name: output} if new_idx > idx else None)
            return True, new_idx, output

        return True, idx, None


class ZeroOrMore(Grammar):
    """ Element which can match a contained grammar zero or more times """

    can_have_delimiter = True

    def human_readable_name(self):
        return "Zero or More *(%s: ...)" % self.name

    def _repeatedly_match(self, string_tokens, idx):
        match_count = 0
        current_idx = idx
        outputs = []
        while current_idx < len(string_tokens):
            new_idx = current_idx

            # If we're not processing the first match, check that any delimiter grammar we may have matches before
            # the next occurance of our grammar
            if match_count > 0 and self.delimiter_grammar is not None:
                match, new_idx, delimiter_output = self.delimiter_grammar.apply(string_tokens, new_idx)

                if not match:
                    break

                if delimiter_output:
                    outputs[-1].update(delimiter_output)

            # Try to match our sub elements
            match, new_idx, output = self._apply_sub_elements(string_tokens, new_idx)

            # If we don't match, or we do but we don't consume any tokens (ie we're stuck) exit the loop
            if not match or new_idx == current_idx:
                break

            match_count += 1
            outputs.append(output or None)
            current_idx = new_idx

        return match_count, current_idx, outputs

    def _apply(self, string_tokens, idx):
        # If the index we're considering is beyond the end of our tokens we have nothing to match on.  However, since
        # we can match zero times, return True.  This allows gramars with trailing ZeroOrMore rules to match strings
        # which don't use them.
        if idx >= len(string_tokens):
            return True, idx, None

        _, new_idx, outputs = self._repeatedly_match(string_tokens, idx)

        return True, new_idx, ({self.name: outputs} if new_idx > idx else None)


class OneOrMore(ZeroOrMore):
    """ Element which can match a contained grammar one or more times """

    can_have_delimiter = True

    def human_readable_name(self):
        return "One or More +(%s: ...)" % self.name

    def _apply(self, string_tokens, idx):
        match_count, idx, outputs = self._repeatedly_match(string_tokens, idx)

        if match_count > 0:
            return True, idx, {self.name: outputs}

        return False, None, None


class OneOfSet(Grammar):
    """ Element which can match any one of its contained grammars """

    def human_readable_name(self):
        return "One of Set {...}"

    def _apply(self, string_tokens, idx):
        for element in self.sub_elements:
            match, new_idx, output = element.apply(string_tokens, idx)
            if match:
                return True, new_idx, output

        return False, None, None
