from ._base_element import BaseScopedElement

class SubGrammarDefinition(BaseScopedElement):
    """ Element for sub grammar scopes. Only used during grammar creation, these never actually makes it into a Grammar object """

    def human_readable_name(self):
        return "Sub Grammar def %s { ... }" % self.name

    def setup(self):
        self.sub_grammars = {}

        if self.token_str:
            # Find the name of the sub grammar; stripping off the def prefix
            self.name = self.name_re.search(self.token_str[3:]).group()


class SubGrammarUsage(BaseScopedElement):
    """ Element for sub grammar replacements. Only used during grammar creation, these never actually makes it into a Grammar object """

    def human_readable_name(self):
        return "Sub Grammar Usage %s()" % self.name

    def setup(self):
        self.sub_grammars = {}

        if self.token_str:
            self.name = self.name_re.search(self.token_str).group()
