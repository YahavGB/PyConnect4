##############################################################################
# PyConnect4: game.py
# DESCRIPTION: This file contains the implemmetation of the Game class.
# This class is responsible on handle a Four in a row game, a.k.a. handle
# the board changes, perform moves, determine the game winner etc.
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


from board import Board
from player import Player


class Game:
    """
    A class that represents the Connect 4 Game.
    """
    ############################################################
    # Constants
    ############################################################

    #: Describes a game state - currently playing.
    STATE_PLAYING = 1

    #: Describes a game state - the game is over.
    STATE_OVER = 2

    #: Describes the invalid move exception text.
    INVALID_MOVE_MESSAGE = "Illegal move."

    #: Describes the invalid player number exception text.
    INVALID_PLAYER_MESSAGE = "Invalid player number."

    #: Describe the 1'st player number.
    PLAYER_ONE = 0

    #: Describe the 2'nd player number.
    PLAYER_TWO = 1

    #: Describe the draw result.
    DRAW = 2

    #: Describe the 1'st player color.
    PLAYER_ONE_COLOR = "red"

    #: Describe the 2'nd player color.
    PLAYER_TWO_COLOR = "yellow"

    ############################################################
    # Ctor
    ############################################################

    def __init__(self):
        """
        Initialize a new Game instance.
        """
        # Initialize our iVars
        self.__state = Game.STATE_PLAYING
        self.__board = Board()
        self.__current_player = Game.PLAYER_ONE
        self.__game_winner = None
        self.__player_one = Player(Game.PLAYER_ONE, Game.PLAYER_ONE_COLOR)
        self.__player_two = Player(Game.PLAYER_TWO, Game.PLAYER_TWO_COLOR)
        self.__on_game_over = None

    ############################################################
    # Methods
    ############################################################

    # region Public API

    def get_board(self):
        """
        Gets the game board instance.
        :return: The board instance.
        """
        return self.__board

    def make_move(self, column):
        """
        Perform a move.
        :param column: The column in which to perform_move in.
        """
        # Can we perform this move?
        if not self.is_valid_move(column):
            raise RuntimeError(Game.INVALID_MOVE_MESSAGE)

        # Will this move cause us to win the game? note that we must check
        # it before performing the actual move since we decided to maintain
        # only the current player bitboard (in order to save resources).
        we_have_a_winner = self.__board.is_winning_move(column)

        # Perform the move
        self.__board.perform_move(column)

        # We got a winner?
        if we_have_a_winner:
            # Declare the winner.
            self.__handle_game_over(self.__current_player)
            return

        # Our board is full?
        if self.__board.is_full():
            # Than it's a draw.
            self.__handle_game_over(Game.DRAW)
            return

        # Toggle the current player
        self.__toggle_current_player()

    def get_winner(self):
        """
        Gets the winner of the game.
        :return: Game.PLAYER_ONE or Game.PLAYER_TWO if one of these players
        won, Game.DRAW if there's a draw or None if the game isn't settled
        yet.
        """
        return self.__game_winner

    def get_player_at(self, row, col):
        """
        Gets the player who have a disk in the given rol and col.
        The row and column variance starts at the top left at (0, 0) and
        continues to the bottom left.
            ----------------------------
            |(0, 0) (0, 1), ..., (0, n)|
            |(1, 0) (1, 1), ..., (1, n)|
            |  ... ... ... ... ... ... |
            |(n, 0) (n, 1), ..., (n, n)|
            ----------------------------
        :param row: The given row.
        :param col: The given col.
        :return: The player who has a disk in the given coordinate, as one
        of the Game.PLAYER_*** constants, or None if it's an empty spot.
        """
        # Rotate and reflect it on our bitboard locations
        if self.__board.has_player_bit_at(row, col):
            # We got a bit which owned by the current player, who is this?
            if self.__current_player == Game.PLAYER_ONE:
                return Game.PLAYER_ONE
            else:
                return Game.PLAYER_TWO
        elif self.__board.has_opponent_bit_at(row, col):
            # We got a bit which owned by the opponent player, who is this?
            if self.__current_player == Game.PLAYER_ONE:
                return Game.PLAYER_TWO
            else:
                return Game.PLAYER_ONE

        return None

    def get_current_player(self):
        """
        Gets the current player.
        :return: The current player number, as one of the Game.PLAYER_****
        constants.
        """
        return self.__current_player

    def get_player(self, player):
        """
        Gets the instnace of the given player by her player number.
        :param player: The integer that represents the player. One of the
        Game.PLAYER_**** constants.
        :return: The Player instance.
        """
        if player == Game.PLAYER_ONE:
            return self.__player_one
        elif player == Game.PLAYER_TWO:
            return self.__player_two

        raise ValueError(Game.INVALID_PLAYER_MESSAGE)

    def get_opponent(self, player):
        """
        Gets the given player opponent instance.
        :param player: The player number,
        :param player: The integer that represents the player. One of the
        Game.PLAYER_**** constants.
        :return: The Player instance.
        """
        if player == Game.PLAYER_ONE:
            return self.__player_two
        elif player == Game.PLAYER_TWO:
            return self.__player_one

        raise ValueError(Game.INVALID_PLAYER_MESSAGE)

    def is_valid_move(self, column):
        """
        Determines wehter or not a given move is valid.
        :param column: The column.
        :return: True if the move is valid, false otehrwise.
        """
        if self.__state == Game.STATE_OVER:
            return False

        return self.__board.can_perform_move(column)

    def get_state(self):
        """
        Gets the current game state.
        :return: The current game state - one of the Game.STATE_*** constants.
        """
        return self.__state

    def get_moves_count(self):
        """
        Gets the number of performed moves.
        :return: The number of performed moves.
        """
        return self.__board.get_performed_moves_count()

    def set_on_game_over_callback(self, callback):
        """
        Sets a callback that will be fired when the game is over.
        :param callback: A delegate to fire when the game end. The delegate
        signature is with the signature void(Game game, int winner).
        """
        self.__on_game_over = callback

    def get_board_representation(self):
        """
        Gets the board human representation (a.k.a. string representation).
        :return: A string that represents the current board.
        """
        if self.__current_player == Game.PLAYER_ONE:
            current_player = self.get_player(Game.PLAYER_ONE)
            opponent_player = self.get_player(Game.PLAYER_TWO)
        else:
            current_player = self.get_player(Game.PLAYER_TWO)
            opponent_player = self.get_player(Game.PLAYER_ONE)

        return self.__board.get_board_human_representation(
            current_player.get_color_char(),
            opponent_player.get_color_char())

    def __repr__(self):
        """
        Gets the string representation for this game.
        :return: A string that representing the game.
        """
        # General game description
        container = ['<Game %s (state=%s)>' % (id(self), self.__state)]
        if self.__state == Game.STATE_OVER:
            container.append('Game Over! Winner' + str(self.__game_winner))
        else:
            container.append('%s to perform_move now.' %
                             self.get_player(self.__current_player)
                             .get_color())

        # The players
        container.append(self.__player_one.__repr__())
        container.append(self.__player_two.__repr__())

        # The board
        container.append(self.get_board_representation())

        # Concat all
        return '\n'.join(container)

    @staticmethod
    def is_valid_player_number(value):
        """
        Determine if the given value is a valid player number.
        :param value: The player number value.
        :return: True if the given value is a valid player number,
        False otherwise.
        """
        return value == Game.PLAYER_ONE or value == Game.PLAYER_TWO

    # endregion

    # region Private Methods

    def __toggle_current_player(self):
        """
        Toggles the current player.
        """
        if self.__current_player == Game.PLAYER_ONE:
            self.__current_player = Game.PLAYER_TWO
        else:
            self.__current_player = Game.PLAYER_ONE

    def __handle_game_over(self, winner):
        """
        Handle the game over event.
        :param winner: The game winner.
        """
        # Mark our new state
        self.__state = Game.STATE_OVER

        # Set the winner
        self.__game_winner = winner

        # Fire the game over event delegate
        if self.__on_game_over is not None:
            self.__on_game_over(self, winner)

    # endregion
