import logging

class BaseElement:
    """ Base class which all defined grammar element subclass from """

    human_readable_name = None

    # Regular expression string which matches valid token names (ex: named sub grammars, named tokens, etc)
    valid_token_name_re = "[a-zA-Z0-9_-]+"

    def __init__(self, token_str, flags):
        self.token_str = token_str
        self._flags = flags

        self.setup()

    def __repr__(self):
        return "<%s>" % self.human_readable_name

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

        if idx < len(string_tokens):
            logging.debug("Matched: %s\n" % match)

        return match, idx, output

    def has_flag(self, flag): # TODO default flags
        """
        Returns a boolean indicating whether or not this grammar element was initialized with the given flag
        or, if not, if the flag was set as a default
        """

        return flag in self._flags


class BaseScopedElement(BaseElement):
    """ Base class for grammar elements which can have sub elements within them """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
