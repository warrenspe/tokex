"""
    File containing an implementation of an SQL input string tokenizer.

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

# Project imports
import Tokenizer

class SQLTokenizer(Tokenizer.TokexTokenizer):
    """
    Tokenizer used to tokenize SQL queries.
    """

    tokenizerRegexes = [
        '"[^"]*"',
        "'[^']*'",
        '\w+',
        '!=',
        '<=',
        '>=',
        '==',
        '\S'
    ]
