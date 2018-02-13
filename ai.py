##############################################################################
# PyConnect4: ai.py
# DESCRIPTION: This file contains the implemmetation of the AI handler class.
# This class is responsible on generating the best move available based on
# the board evaluation score.
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

from copy import copy
from game import Game
from board import Board
from transposition_table import TranspositionTable


class AI:
    """
    Describes that class that provides AI to the Connect4 game.
    This class implementation is based on the negamax variant of the alpha
    beta pruning algorithm, combined with caching transposition table and
    our Board bitboard style container.
    For more information & references see the comments below.
    """

    #: Describes the default moves exploring order.
    MOVE_EXPLORING_ORDER = [3, 4, 2, 5, 1, 6, 0]

    #: Creaets a map between the given timeout and the search depth.
    TIMEOUT_DEPTH_MAP = {
        0.001: 1,
        0.010: 3,
        0.050: 4,
        0.1: 4,
        0.3: 5,
        0.5: 6,
        3: 7
    }

    #: Defines the default depth
    DEFAULT_DEPTH = 8

    #: Describe the exception message in case no move available.
    NO_AVAILABLE_MOVE_MESSAGE = "No possible AI moves"

    def __init__(self):
        """
        Initializes a new AI handler instance.
        """
        self.__tp_table = TranspositionTable()
        self.__move_selection_delegate = None
        self.__depth = AI.DEFAULT_DEPTH
        self.__best_move = None

    def reset(self):
        """
        Resets the AI data.
        """
        self.__tp_table.reset()
        self.__best_move = None
        self.__depth = AI.DEFAULT_DEPTH
        self.__move_selection_delegate = None

    def find_legal_move(self, g, func, timeout=None):
        """
        Looks for a legal move.
        :param g: The game instance.
        :param func: A callback fired when a move is selected. Note that
        this callback can be fired multiple times.
        :param timeout: A search timeout [optional].
        """
        board = g.get_board()

        # We can perform any move?
        valid_moves = board.get_valid_moves()
        if board.is_full() or valid_moves == 0:
            raise RuntimeError(AI.NO_AVAILABLE_MOVE_MESSAGE)

        # Init
        self.reset()
        self.__move_selection_delegate = func

        # Handle obvious moves manually
        if self.__handle_obvious_moves(g.get_board()):
            return

        # Did we got a timeout?
        if timeout is not None:
            for v in AI.TIMEOUT_DEPTH_MAP:
                if timeout <= v:
                    self.__depth = AI.TIMEOUT_DEPTH_MAP[v]
                    break

        # Perform an IDS
        self.__iterative_deepening_search(g.get_board())

        # If nothing chosen, just get SOMETHING
        if self.__best_move is None:
            non_losing_moves = board.get_valid_non_losing_moves()
            if non_losing_moves != 0:
                # Do something
                func(self.__get_column_from_bitmask(non_losing_moves))
            else:
                # We're gonna lose....
                func(self.__get_column_from_bitmask(valid_moves))

    # region Private API

    def __handle_obvious_moves(self, board):
        """
        Attempt to create some manual, quick response cases.
        :return: True if the move has been handled, false otherwise.
        """
        # We are going to win?
        winning_moves = board.get_winning_moves()
        if winning_moves != 0:
            self.__move_selection_delegate(self.__get_column_from_bitmask(
                winning_moves))
            return True

        # We have only one valid non-losing move to perform? It'll be
        # usuraly when we'll gonna lose if we won't respond accordingly.
        non_losing_moves = board.get_valid_non_losing_moves()
        if non_losing_moves == 0:
            # We don't have anything safe we can play so we just choose
            # whatever we can. We lost :'(.
            self.__move_selection_delegate(self.__get_column_from_bitmask(
                board.get_valid_moves()))
            return True

        # This is a self-defense move?
        if Board.popcount(non_losing_moves) == 1:
            self.__move_selection_delegate(self.__get_column_from_bitmask(
                non_losing_moves))
            return True

        return False

    def __get_column_from_bitmask(self, bitmask):
        """
        Get the given bitmask move column.
        :param bitmask: The move bitmask.
        :return: The integer column.
        """
        for i in range(Board.WIDTH):
            if bitmask & Board.create_column_bitmask(i) != 0:
                return i

    def __iterative_deepening_search(self, board):
        """
        Performs an Iterative Deepening Search (IDS).
        See: https://chessprogramming.wikispaces.com/Iterative+Deepening.
        """
        for depth in range(0, self.__depth):
            pv_table, score = self.__tp_table_based_search(
                board,
                Board.MIN_SCORE,
                Board.MAX_SCORE,
                depth + 1, ply=1)

            if len(pv_table) > 0:
                self.__best_move = pv_table[0]
                self.__move_selection_delegate(pv_table[0])

    def __tp_table_based_search(self, board, alpha, beta, depth, ply=1):
        """
        Perform a transposition table based graph search. This function
        invokes the actual search algorithm only in case it can't find the
        board evaluation value in the TP table. In case it does, it returns
        it. Note that if a search is really performed, the TP table is
        being updated automatically by this function.
        :param board: The board instance.
        :param alpha: The alpha/be
        ta cutoff algorithm alpha value.
        :param beta: The alpha/beta cutoff algorithm beta value
        :param depth: The searching depth.
        :param ply: The current play.
        :return: A tuple contains the Principal Variation table and the
        evaluation score.
        """
        # Gets the board hash
        key = board.get_hash()

        # Check if we got something in our transposition table
        has_hit, move_column, evaluation_score = self.__tp_table.thaw(
            key, alpha, beta, depth)

        if has_hit:
            if move_column is not None:
                return [move_column], evaluation_score
            return [], evaluation_score

        # Search the move using the PVS variation of the Alpha Beta algorithm.
        move_column, evaluation_score = self.__pvs_search(board, alpha,
                                                          beta, depth, ply)

        # Store the move in our transposition table.
        self.__tp_table.freeze(key, move_column, evaluation_score,
                               alpha, beta, depth)

        return move_column, evaluation_score

    def __pvs_search(self, board, alpha, beta, depth, ply):
        """
        Implements a PVS search to eevaluate the game board and look for
        the best board score in the Connect4 game. This algorithm is
        based on the negamax with alpha-beta puring algorithm.

        For the used searching algorithms, see:
        PV: https://chessprogramming.wikispaces.com/Principal+Variation+Search
        Negamax: https://chessprogramming.wikispaces.com/Negamax
        Alpha-Beta: https://chessprogramming.wikispaces.com/Alpha-Beta

        :param board: The current board state to evaluate and performs the
        moves on. Note that this method assumes that nobody already won and
        that the current player cannot win next move. Thus these conditions
        must be checked before invoking this method.
        :param alpha: The score window within which we are evaluating the
        position for the maximizer (alpha < beta).
        :param beta: The score window within which we are evaluating the
        position for the minimizer (alpha < beta).
        :param depth: The current search depth.
        :param ply: The current ply number.
        :return:
        """
        # We gonna have a draw?
        if board.get_performed_moves_count() >= \
                (Board.WIDTH * Board.HEIGHT - 2):
            return [], Board.DRAW_SCORE  # We're "meh" about it.

        # # Do we got any more moves to do?
        valid_moves = board.get_valid_non_losing_moves()
        if valid_moves == 0:
            # No more valid moves, so return the (relatively) worst scoring
            # value we can have
            return [], Board.MIN_SCORE / ply

        if depth <= 0:
            return [], board.evaluate(0)

        # Iterate on the moves and search for the best move to perform.
        best_pv_table = []
        best_score = alpha
        for i, move_column in enumerate(AI.MOVE_EXPLORING_ORDER):
            # Get the move
            move_mask = valid_moves & Board.create_column_bitmask(move_column)
            if move_mask == 0:
                continue

            # Gets a clone of this board
            new_board = copy(board)

            # Perform 'dat move!
            new_board.perform_move_with_mask(move_mask)

            # We're implementing the PVS algorithm and thus we need to
            # reduce the window based on our iteration, depth and a/b
            # values, so what should we do now?
            if depth == 1 or i == 0 or (beta - alpha) == 1:
                pv_table, score = self.__tp_table_based_search(
                    new_board, -beta, -best_score, depth - 1, ply + 1)

            else:
                # Since we're implementing the PVS alpha/beta variation,
                # we uses zero-window for all of our other searches.
                _, score = self.__tp_table_based_search(
                    new_board, -best_score - 1,
                    -best_score, depth - 1, depth + 1)
                score = -score
                if score > best_score:
                    pv_table, score = self.__tp_table_based_search(
                        new_board, -beta, -best_score, depth - 1, ply + 1)
                else:
                    continue

            # Check the result score
            score = -score
            if score > best_score:
                # Save this score
                best_score = score
                best_pv_table = [move_column] + pv_table
            elif not best_pv_table:
                # Make sure we got a table...
                best_pv_table = [move_column] + pv_table

            if best_score >= beta:
                # Perform a beta cutoff
                break

        return best_pv_table, best_score
