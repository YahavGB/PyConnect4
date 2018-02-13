##############################################################################
# PyConnect4: transposition_table.py
# DESCRIPTION: This file contains the implementation of the game
# transposition table. A transposition table is a cache storage for each
# evaluated move and it allows to quickly retrieve board state evaluation
# score for way faster performance.
#
# Copyright (C) 2018 Yahav G. Bar
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

from collections import OrderedDict, namedtuple

#: Declares a transposition table entry. We could've use a standard class
# but it'd be just a waste of resources. A proper C#/Java style
# implementation would be to declare it as a struct.
TPEntry = namedtuple('Entry', ['move', 'depth', 'score', 'type'])


class TranspositionTable:
    """
    Defines a Transposition Table in our Connect4 Game.
    A Transposition Table is a simple hash map dictionary. That table will
    serve us asa cache of a given board position to its equivalent
    evaluation score and thus will reduce re-scoring the board over and over.
    Note that if there're collisions we keep the last entry and override the
    previous one.

    For Transposition Table information, see:
    https://chessprogramming.wikispaces.com/Transposition+Table
    http://en.wikipedia.org/wiki/Transposition_table
    """

    ############################################################
    # Constants
    ############################################################

    #: Define the TP table max size
    MAX_SIZE = 50000

    #: Define a transposition table "value in the bounds" range cache type.
    TYPE_EXACT = object()

    #: Define a transposition table "value in upper bounds" range cache type.
    TYPE_UPPER_BOUND = object()

    #: Define a transposition table "value in lower bounds" range cache type.
    TYPE_LOWER_BOUND = object()

    ############################################################
    # Ctor
    ############################################################

    def __init__(self):
        """
        Initialize a new transposition table.
        """
        self.__tp_table = OrderedDict()
        self.__size = TranspositionTable.MAX_SIZE
        self.reset()

    ############################################################
    # Methods Implementation
    ############################################################

    def reset(self):
        """
        Reset the transposition table.
        :return:
        """
        self.__tp_table = {}

    def freeze(self, board_hash, pv_table, score, alpha, beta, depth):
        """
        Freeze (store) the given data in the transposition table.
        :param board_hash: The board hash.
        :param pv_table: The sequence PV table.
        :param score: The board evaluation score.
        :param alpha: The alpha value.
        :param beta: The beta value.
        :param depth: The move depth.
        """
        # Get the actual move
        if pv_table is not None and len(pv_table) > 0:
            move = pv_table[0]
        else:
            move = None

        # What is our cache type?
        if depth == 0 or depth == -1 or alpha < score < beta:
            # We found an exact storage value
            cache_type = TranspositionTable.TYPE_EXACT
        elif score >= beta:
            # This value is the lower bound of the alpha/beta cutoff
            cache_type = TranspositionTable.TYPE_LOWER_BOUND
            score = beta
        elif score <= alpha:
            # This value is the upper bound of the alpha/beta cutoff
            cache_type = TranspositionTable.TYPE_UPPER_BOUND
            score = alpha
        else:
            # Invalid storage value
            raise ValueError

        # Create a new transposition table entry
        entry = TPEntry(move, depth, int(score), cache_type)
        self.__tp_table.pop(board_hash, None)
        self.__tp_table[board_hash] = entry

        # Did we exceed our max size?
        if len(self.__tp_table) > self.__size:
            # Remove the first None (null) entry
            self.__tp_table.popitem(last=False)

    def thaw(self, board_hash, alpha, beta, depth):
        """
        Thaw (retrieve) the score of the given board (represented with its
        board hash) for the given alpha, beta and depth vales.
        :param board_hash: The board hash.
        :param alpha: The alpha value.
        :param beta: The beta value.
        :param depth: The move depth.
        :return: A tuple with three entries:
            A) A boolean value that determines if we found the value in the
               transposition or not (has hit).
            B) The move column that caused this board hash, by its
               mask representation, or none if this hash does not exists in
               the transposition table.
            C) The move evaluation score, or None if the hash doesn't
               exists in the transposition table or doesn't produce a valid
               hit for the given alpha, beta and depth values.
        """
        # Attempt to find the value in our transposition table
        if board_hash not in self.__tp_table:
            return False, None, None

        entry = self.__tp_table[board_hash]

        # Check if we got a transposition table hit (a.k.a. a matching
        # value for this hash value, and find out what the value it
        # co-responds to).
        has_hit = False
        if entry.depth == -1:
            has_hit = True
        elif entry.depth >= depth:
            if entry.type is TranspositionTable.TYPE_EXACT:
                has_hit = True
            elif entry.type is TranspositionTable.TYPE_LOWER_BOUND and \
                    entry.score >= beta:
                has_hit = True
            elif entry.type is TranspositionTable.TYPE_UPPER_BOUND and \
                    entry.score <= alpha:
                has_hit = True

        # Have we hit the transposition table entry?
        if not has_hit:
            return False, entry.move, None

        # Return the stored value in the transposition table
        return True, entry.move, entry.score
