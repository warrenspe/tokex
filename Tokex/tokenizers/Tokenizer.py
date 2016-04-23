"""
    File containing the base class for a Tokex input string tokenizer.

    Copyright (C) 2016 Warren Spencer
    warrenspencer27@gmail.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Standard imports
import re

class TokexTokenizer(object):
    """
    Base class for Tokex Tokenizers.  Uses re.findall & a collection of regular expressions to break up an
    input string into a sequence of tokens.

    Can be extended by subclassing this class & implementing a `tokenize` function, or by creating a custom
    list of tokenizerRegexes.

    Use of this function without subclassing will tokenize an input string by breaking up all occurrances of quotes
    into their own separate token; all sequences of ascii tokens into their own separate token, and all
    remaining non-white space characters into their own token.  Note that this will cause things like "!=" to be
    broken into two separate tokens.
    """

    tokenizerRegexes = [
        '"[^"]*"',
        "'[^']*'",
        '\w+',
        '\S'
    ]


    def tokenize(self, inputString):
        """
        Function which is called by Tokex to break an input string into tokens, processed by Tokex.

        Inputs: inputString - A string, to break into tokens.

        Outputs: A list of tokens from inputString.
        """

        return re.findall("(%s)" % "|".join(self.tokenizerRegexes), inputString)
