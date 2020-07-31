from . import tokenizer

class SQLTokenizer(tokenizer.TokexTokenizer):
    """
    Tokenizer used to tokenize SQL queries.
    """

    tokenizer_regexes = [
        '"[^"]*"',
        "'[^']*'",
        '\w+',
        '!=',
        '<=',
        '>=',
        '==',
        '\S'
    ]
