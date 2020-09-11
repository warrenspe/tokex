from .grammar import flags
from .tokex_class import Tokex
from .tokenizers import tokenizer


def compile(input_grammar,
            allow_sub_grammar_definitions=True,
            tokenizer=tokenizer.TokexTokenizer,
            default_flags=flags.DEFAULTS):
    """
    Constructs and returns an instance of _StringParser for repeated parsing of strings using the given grammar.

    Inputs: input_grammar - The grammar to use to parse the input string.
            allow_sub_grammar_definitions - A Boolean, indicating whether or not sub grammar declarations,
                                            (@name: grammar @@), should be processed.  If grammarString has
                                            come from an untrusted source this should be set to False, to
                                            mitigate the potential for a `Billion Laughs` attack.
            tokenizer - Optional: An instance or class of tokenizers.Tokenizer.TokexTokenizer or a subclass of it,
                        used to tokenize the input string for parsing. Defaults to the base class TokexTokenizer.
            default_flags - A set of flags which will apply to all elements by default.
                            Default flags can be overridden by specifying an opposing flag on elements in the grammar.


    Outputs: An instance of _StringParser whose `match` function can be used to repeatedly parse input strings.
    """

    return Tokex(input_grammar, allow_sub_grammar_definitions, tokenizer, default_flags=default_flags)


def match(input_grammar,
          input_string,
          match_entirety=True,
          allow_sub_grammar_definitions=True,
          tokenizer=tokenizer.TokexTokenizer,
          default_flags=flags.DEFAULTS,
          debug=False):
    """
    Convenience function for performing matches using a grammar against a string.

    Inputs: input_grammar  - The grammar to use to parse the input string.
            input_string   - The string to be parsed.
            match_entirety - A boolean, if True requires the entire string to be matched by the grammar.
                             if False, trailing tokens not matched by the grammar will not cause a match failure.
            allow_sub_grammar_definitions - A Boolean, indicating whether or not sub grammar declarations,
                                         (@name: grammar @@), should be processed.  If grammarString has
                                         come from an untrusted source this should be set to False, to
                                         mitigate the potential for a `Billion Laughs` attack.
            tokenizer      - Optional: An instance or class of tokenizers.Tokenizer.TokexTokenizer or a subclass of it,
                             used to tokenize the input string for parsing. Defaults to the base class TokexTokenizer.
            default_flags - A set of flags which will apply to all elements by default.
                            Default flags can be overridden by specifying an opposing flag on elements in the grammar.
            debug          - A boolean, if True will set the debugging level to DEBUG for the duration of the match

    Outputs: The result of matching the input_string, if it matches, else None.
    """

    return Tokex(
        input_grammar,
        allow_sub_grammar_definitions,
        tokenizer,
        default_flags=default_flags,
    ).match(input_string, match_entirety=match_entirety, debug=debug)
