
class BaseGrammarElement:
    """ Base class which all defined grammar element subclass from """

    # Regular expression string which matches valid token names (ex: named sub grammars, named tokens, etc)
    valid_token_name_re = "[a-zA-Z0-9_-]+"

    ###
    # These class functions must be defined on derived subclasses
    ###

    def __init__(self, token_str, flags):
        self.token_str = token_str
        self._flags = flags

    @classmethod
    def _grammar_tokens(cls):
        """
        Function which should return a list of dictionaries created via the create_grammar_token class function.
        Each token in the list will be used to match tokens in user-defined grammars and map them to this class.
        """

        raise NotImplementedError

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

    ###
    # API class functions
    ###

    def __repr__(self):
        return "<%s>" % (self.__class__.__name__)

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

    def has_flag(self, flag):
        """ Returns a boolean indicating whether or not this grammar element was initialized with the given flag """

        return flag in self._flags

    @classmethod
    def create_grammar_token(cls, re_string, flags=None, escapes=None):
        """
        Creates a new grammar element token dictionary.
        These are used to control how an input grammar is parsed into element classes.

        Inputs: re_string - A string which will be converted into a regular expression which will match definitions
                            for this element in a user defined grammar
                flags     - If this token can accept leading flags, they should be given in a list of string
                escapes   - A list of strings of characters which can be escaped within the token
        """

        return {
            "cls": cls,
            "re_string": re_string,
            "escapes": escapes,
            "flags": flags
        }


class BaseScopedGrammarElement(BaseGrammarElement):
    """ Base class for grammar elements which can have sub elements within them """


    ###
    # These class functions can be defined on derived subclasses
    ###

    def _verify_sub_elements(self):
        """
        Called during grammar construction.  Should look at the list of sub_elements and perform any validation necessary.

        Outputs: None
        """

        return None

    def _add_sub_element(self, sub_element):
        """
        Adds a sub element to this grammar element.  This is used in places such as zero or more for example,
        where the zero or more element will contain one or more sub elements

        Inputs: sub_element - The element to add as a sub element of this element.
                              Should be a subclass of BaseGrammarElement
        """

        self.sub_elements.append(sub_element)

        self.verify_sub_elements()

    ###
    # API class functions
    ###

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # List of sub elements that this grammar element contains
        self.sub_elements = []

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, [repr(t) for t in self.sub_elements])

    def add_sub_element(self, sub_element):
        """
        Adds a sub element to this grammar element.  This is used in places such as zero or more for example,
        where the zero or more element will contain one or more sub elements

        Inputs: sub_element - The element to add as a sub element of this element.
                              Should be a subclass of BaseGrammarElement
        """

        self.sub_elements.append(sub_element)

        self._verify_sub_elements()

    @classmethod
    def create_grammar_token(cls, *args, opens=False, closes=False, **kwargs):
        """
        Creates a new grammar element token dictionary.
        These are used to control how an input grammar is parsed into element classes.

        Inputs: *args/**kwargs - See BaseGrammarElement.create_grammar_token for a description of the other parameters
                                 which can be passed
        Inputs: opens     - A boolean indicating whether this class should be added to the parsing stack when seen.
                            If True a new context is created for this type of element when this token is seen
                closes    - A boolean indicating whether seeing this token should pop the nearest instance of this
                            element from the parsing stack
        """

        return {
            super().create_grammar_token(*args, **kwargs),
            "opens": opens,
            "closes": closes
        }
