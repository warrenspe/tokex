from ._base_grammar_element import BaseScopedElement

class SubGrammarDefinition(BaseScopedElement):
    """ Element for sub grammar scopes. Only used during grammar creation, these never actually makes it into a Grammar object """

    def setup(self):
        self.name = self.token_str[2:-1]
        self.sub_grammars = {}


class SubGrammarUsage(BaseScopedElement):
    """ Element for sub grammar replacements. Only used during grammar creation, these never actually makes it into a Grammar object """

    def setup(self):
        self.name = self.str_token[1:-1]
