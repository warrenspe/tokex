import re

from ._base_grammar_element import BaseGrammarElement

class SubGrammarDefinition(BaseScopedGrammarElement):
    """ Element for sub grammar scopes. """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.name = self.token_str[2:-1]

    @classmethod
    def _grammar_tokens(cls):
        return [
            cls.create_grammar_token(
                r"\{<%s>" % cls.valid_token_name_re,
                opens=True
            ),
            cls.create_grammar_token(
                r"\}"
                closes=True
            )
        ]


class SubGrammarUsage(BaseGrammarElement):
    """ Element for sub grammar replacements. """

    def __init__(self, *args, **kwargs):
        super()__init__(*args, **kwargs)

        self.name = self.str_token[1:-1]

    @classmethod
    def _grammar_tokens(cls):
        return [
            cls.create_grammar_token(r"\{%s\}" % cls.valid_token_name_re)
        ]
