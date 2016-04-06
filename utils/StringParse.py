"""
File containing a string parsing class which upon being fed a utils.GrammarParse.Grammar object, 
"""

class StringParser(object):

    grammar = None

    def __init__(self, grammar):
        self.grammar = grammar


    def match(self, inputString):
        return grammar.match(inputString)
