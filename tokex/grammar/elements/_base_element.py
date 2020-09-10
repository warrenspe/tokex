import logging
import re

from .. import flags

class BaseElement(object):
    """ Base class which all defined grammar element subclass from """

    # A set of flags which are valid to be set for this element
    valid_flags = None

    def __init__(self, token_str="", _flags=None, default_flags=flags.DEFAULTS):
        self.token_str = token_str
        # Records what flags were defined on the grammar
        self._grammar_flags = _flags
        # Records what flags will be used with the element; combines grammar flags with default flags
        self._flags = set(_flags) if _flags else None

        default_flags = default_flags or flags.DEFAULTS

        # Check that 2+ mutually exclusive flags weren't given
        if self._flags:
            for m_ex_set in flags.__MUTUALLY_EXCLUSIVE__:
                if len(m_ex_set.difference(self._flags)) < len(m_ex_set) - 1:
                    raise Exception("Mutually exclusive flags given: %s" % ", ".join(m_ex_set))

        # Set default flags
        if self.valid_flags and default_flags:
            for flag in default_flags:
                # Check if the default flag appears in any mutually exclusive set
                for m_ex_set in flags.__MUTUALLY_EXCLUSIVE__:
                    if flag in m_ex_set:
                        # If it does, check if we were given any of the other alternatives.  If not, apply the default
                        if len(m_ex_set.difference(self._flags or [])) == len(m_ex_set):
                            self._flags = self._flags or set()
                            self._flags.add(flag)

                        break

                # If we're in the else, the flag wasn't in any mutually exclusive set.  Apply it
                else:
                    self._flags = self._flags or set()
                    self._flags.add(flag)

        self.setup()

    def __repr__(self):
        return "<[%s]>" % self.human_readable_name()

    def human_readable_name(self):
        """ Returns a string which can be displayed to users, showing what sort of element they're looking at """

        return "Tokex Element"

    def _apply(self, string_tokens, idx):
        """
        Function which accepts an iterable of tokens and a current index and determines whether or not this token
        matches the list at the current position. Should be overridden in subclasses.

        Inputs: string_tokens - An iterable of string tokens to determine if we match upon.
                idx          - The start index within the string_tokens to begin processing at.

        Outputs: A triple containing: {
            match: A boolean depicting whether or not this construct matches the iterable at the current position.
            new_idx: The index this construct ceased matching upon the iterable, if match is True. Else None
            output: If there are any named matches within this construct, a dictionary or list.  Else None
        )
        """

        raise NotImplementedError

    def setup(self):
        pass

    def apply(self, string_tokens, idx):
        """
        Used to apply this token to an iterable of tokens at a specified position.  Uses self._apply to do the work
        of matching the inputs.

        Inputs: string_tokens - An iterable of string tokens to determine if we match upon.
                idx           - The start index within the string_tokens to begin processing at.

        Outputs: A triple containing: {
            match: A boolean depicting whether or not this construct matches the iterable at the current position.
            new_idx: The index this construct ceased matching upon the iterable, if match is True. Else None
            output: If there are any named matches within this construct, a dictionary or list.  Else None
        )
        """

        if idx < len(string_tokens):
            logging.debug("Current Token: %s\n\nMATCHING: %s\n" % (self, string_tokens[idx]))

        match, idx, output = self._apply(string_tokens, idx)

        if idx is not None and idx < len(string_tokens):
            logging.debug("Matched: %s\n" % match)

        return match, idx, output

    def has_flag(self, flag):
        """
        Returns a boolean indicating whether or not this grammar element was initialized with the given flag
        or, if not, if the flag was set as a default
        """

        return flag in (self._flags or '')


class BaseScopedElement(BaseElement):
    """ Base class for grammar elements which can have sub elements within them """

    name = None

    # Regular expression string which matches valid token names (ex: named sub grammars, named tokens, etc)
    name_re_str = "[a-zA-Z0-9_-]+"
    name_re = re.compile(name_re_str)

    def __init__(self, *args, **kwargs):
        super(BaseScopedElement, self).__init__(*args, **kwargs)

        # List of sub elements that this grammar element contains
        self.sub_elements = []

    def add_sub_element(self, sub_element):
        """
        Adds a sub element to this grammar element.  This is used in places such as zero or more for example,
        where the zero or more element will contain one or more sub elements

        Inputs: sub_element - The element to add as a sub element of this element.
                              Should be a subclass of BaseGrammar
        """

        self.sub_elements.append(sub_element)
