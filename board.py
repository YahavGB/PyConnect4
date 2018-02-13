##############################################################################
# PyConnect4: board.py
# DESCRIPTION: This file contains the implemetation of the Board class.
# This class is responsible to handle on the entire board pieces, win/lose
# check, evaluation etc.
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


class Board:
    """
    Describes the Connect4 Board.
    For WAY (!) better performance, we decided to represent the game board
    with the bitboard algorithm. A bitboard is a 64bits integer (uint64_t)
    that used as a binary number in which each "1"/"on" flag means there's
    a disc on and each "0"/"off" means there's no disc on.

    Since there's no differentiation between players in a bitboard,
    we're representing our game board as the following:
    A) A bitboard "bitboard_mask" with "on" flag on [any] used point.
    B) a bitboard "current_position" with "on" on any [current player] discs.

    Using that technique we can know the entire board state. To thaw the
    opponent discs, all one need to do is to xor the general board mask
    from the current player mask (a.k.a. bitboard_mask ^ current_positions)

    The encoding positioning of the bits in the bitboard mask is as the
    following:
     .  .  .  .  .  .  .
     5 12 19 26 33 40 47
     4 11 18 25 32 39 46
     3 10 17 24 31 38 45
     2  9 16 23 30 37 44
     1  8 15 22 29 36 43
     0  7 14 21 28 35 42

     Thus, for example, a "4434" game is been represented as:
    bitboard: 0b1110000001000000000000000000000):
      0 1 2 3 4 5 6
    5 . . . . . . .
    4 . . . . . . .
    3 . . . . . . .
    2 . . . . X . .
    1 . . . . X . .
    0 . . . X X . .

    Note that since we're using a 6x7 board, we have to use an extra,
    empty, bits row, a.k.a., the bits 6, 13, 20, 27, 34, 41 and 48 are
    unused. Thus, to perform bits calculation we always need to use the
    absolute value of the differentiation between the rows and columns to
    thaw the right value (a.k.a. board_height - abs(rows - columns)).

    To read more about bitboards, see:
    http://chessprogramming.wikispaces.com/Bitboards
    https://eprints.qut.edu.au/85005/1/
    __staffhome.qut.edu.au_staffgroupm%24_meaton_Desktop_bits-7.pdf
    """
    ############################################################
    # Constants
    ############################################################

    #: The board default rows length.
    WIDTH = 7

    #: The board default rows length.
    HEIGHT = 6

    #: Describes the size diff between the board rows and columns (col - row).
    SIZE_DIFF = 1

    #: The minimum number of discs in row that causes a win.
    WIN_ROW_LENGTH = 4

    #: Defines the maximum score a board can have.
    # MAX_SCORE = 1000
    MAX_SCORE = (WIDTH * HEIGHT + 1) / 2 - 3

    #: Defines the minimum score a board can have.
    # MIN_SCORE = -1 * MAX_SCORE
    MIN_SCORE = -(WIDTH * HEIGHT) / 2 + 3

    #: Defines the draw score.
    DRAW_SCORE = 0

    #: Define the minimum index for a diagonal row (in rectangle perspective).
    MIN_DIAGONAL_ROW = 3

    #: Define a win sequence type - vertical.
    WIN_SEQUENCE_VERTICAL = 0

    #: Define a win sequence type - horizontal.
    WIN_SEQUENCE_HORIZONTAL = 1

    #: Define a win sequence type - left diagonal.
    WIN_SEQUENCE_L_DIAGONAL = 2

    #: Define a win sequence type - right diagonal.
    WIN_SEQUENCE_R_DIAGONAL = 3

    ############################################################
    # Static Variables
    ############################################################

    #: Define the mask that describes a full row at HEIGHT (the last row).
    __bottom_row_mask = 0

    #: Define the mask that describes a full board.
    __board_full_mask = 0

    #: Defines an array that contains bitmasks that describe the winning
    # ways. Note that each bitmask contains the entire row/column/diagonal
    # and thus one would need to use popcount(...) to make sure we really won.
    __winning_sequences = []

    #: Define the evaluation scoring histogram.
    __weights_histogram = [0, 0, 1, 4, 0]

    ############################################################
    # Ctor
    ############################################################

    def __init__(self):
        """
        Initializes a new board.
        """
        # Setup iVars
        self.__bitboard = 0
        self.__current_position_mask = 0
        self.__performed_moves = 0
        self.__player_sign = 1

        # Initialize our static variables
        Board.initialize()

    ############################################################
    # Methods
    ############################################################

    # region Public API

    def get_bitboard(self):
        """
        Gets the integer mask that represents this bitboard.
        :return: Integer (uint64_t tbh) that represents this bitboard.
        """
        return self.__bitboard

    def get_player_board(self):
        """
        Gets the integer mask that represents the current player board mask.
        :return: Integer (uint64_t) that represents this current player.
        """
        return self.__current_position_mask

    def get_opponent_board(self):
        """
        Gets the integer mask that represents the opponent board mask.
        :return: Integer (uint64_t) that represents this current player.
        """
        return self.__current_position_mask ^ self.__bitboard

    def has_player_bit_at(self, row, column):
        """
        Determine if the current player has a bit in the given row and
        column. The row and column variance starts at the top left at (0,
        0) and continues to the bottom left.
            ----------------------------
            |(0, 0) (0, 1), ..., (0, n)|
            |(1, 0) (1, 1), ..., (1, n)|
            |  ... ... ... ... ... ... |
            |(n, 0) (n, 1), ..., (n, n)|
            ----------------------------
        :param row: The row location.
        :param column: The column location
        :return: True if there's a bit in the given (row, column),
        false otherwise.
        """
        # Rotate and reflect it on our bitboard locations
        r = Board.HEIGHT - Board.SIZE_DIFF - row
        c = column * Board.WIDTH

        # Check
        return (self.__current_position_mask & (1 << (r + c))) != 0

    def has_opponent_bit_at(self, row, column):
        """
        Determine if the current opponent has a bit in the given row and
        column. The row and column variance starts at the top left at (0,
        0) and continues to the bottom left.
            ----------------------------
            |(0, 0) (0, 1), ..., (0, n)|
            |(1, 0) (1, 1), ..., (1, n)|
            |  ... ... ... ... ... ... |
            |(n, 0) (n, 1), ..., (n, n)|
            ----------------------------
        :param row: The row location.
        :param column: The column location
        :return: True if there's a bit in the given (row, column),
        false otherwise.
        """
        # Rotate and reflect it on our bitboard locations
        r = Board.HEIGHT - Board.SIZE_DIFF - row
        c = column * Board.WIDTH

        # Check
        return (self.get_opponent_board() & (1 << (r + c))) != 0

    def perform_move(self, column):
        """
        Place a disc at the given column.
        :param column: The column to place the disk at.
        :return: True if the move has been successfully made, false otherwise.
        """
        move_mask = (self.__bitboard + Board.create_bottom_bitmask(column)) &\
            Board.create_column_bitmask(column)

        # Perform the move by its mask
        self.perform_move_with_mask(move_mask)

    def perform_move_with_mask(self, move_mask):
        """
        Performs a given move that is been represented using the given bit
        mask.
        :param move_mask: An integer that represents the move mask.
        """
        # Switch the current player (Player 1 -> Player 2 and vise versa)
        self.__current_position_mask ^= self.__bitboard

        # Perform the move!
        self.__bitboard |= move_mask

        # Increment the moves counter
        self.__performed_moves += 1

        self.__player_sign *= -1

    def is_winning_move(self, column):
        """
        Determine whether playing the given column will cause the current
        player to win the game.
        :param column: The column to perform_move in.
        :return: True if this move will cause the player to win,
        false otherwise.
        """
        return (self.get_valid_moves() &
                Board.create_column_bitmask(column) &
                self.__get_player_winning_mask()) != 0

    def get_winning_moves(self):
        """
        Gets a mask that contains all the moves the player can perform in
        order to win the game.
        :return: The moves mask.
        """
        return (self.get_valid_moves() &
                self.__get_player_winning_mask())

    def get_valid_moves(self):
        """
        Gets a bitboard mask that represents the locations of the valid moves.
        :return: A integer mask representing the valid positions.
        """
        return (self.__bitboard + Board.__bottom_row_mask) & \
            Board.__board_full_mask

    def get_valid_non_losing_moves(self):
        """
        Get a bitboard mask that represents the moves the current perform_move
        may perform_move in, excluding the moves that will cause her to lose.
        :return: A bitboard bit mask.
        """
        # Get the entire valid moves
        valid_moves = self.get_valid_moves()

        # Gets a bitboard which contains the locations in which the current
        # player opponent will win if she plays in them.
        opponent_win_bitmask = self.__get_opponent_winning_mask()

        # Compute the location of moves we must perform to defend ourselfs
        self_defense_moves = valid_moves & opponent_win_bitmask

        # Do we need to defend ourselfs from a next win?
        if self_defense_moves != 0:
            # If we're here that means that if we won't perform_move at the
            # specified location, we'll lose at the next turn! OMG! Thats bad!
            #
            # How much locations is it? We hope so much it's not more than
            # one, so we can REALLY defend ourselves!
            if (self_defense_moves & (self_defense_moves - 1)) != 0:
                # Ugh, nope, the opponent has more than one move she can
                # perform to win, so we don't have anything to do about it...
                return 0

            # We have one location in which we must perform_move in order to
            # defend ourselves from a 100% lose in the next turn, so any other
            # move isn't really relevant. We'll just choose that move.
            valid_moves = self_defense_moves

        # Return the possible moves excluded moves which will help the
        # opponent to actually win in the next turn (for instance, she has
        # 3 vertical discs in diagonal position and we help her to reach
        # the 4'th location).
        return valid_moves & ~(opponent_win_bitmask >> 1)

    def can_perform_move(self, column):
        """
        Determines whether or not the given move is valid.
        :param column: The column.
        :return: True if the move is valid, false otherwise.
        """
        # We're out of bounds?
        if not Board.is_valid_column_index(column):
            return False

        # Chheck if this spot is taken or not.
        return (self.__bitboard & Board.create_top_bitmask(column)) == 0

    def is_full(self):
        """
        Determine whether or not the board is full.
        :return: True if the board is full, false otherwise.
        """
        return self.__bitboard == Board.__board_full_mask

    def count_column_items(self, column):
        """
        Count the number of marked pieces in the given column.
        :param column: The column to count.
        :return: The number of pieces put on that column.
        """
        return Board.popcount(
            Board.create_column_bitmask(column) & self.__bitboard)

    def get_performed_moves_count(self):
        """
        Gets the number of performed moves.
        :return: The number of performed moves.
        """
        return self.__performed_moves

    def get_hash(self):
        """
        Creates a hash representation for the current board state.
        :return: The hash representation.
        """
        return self.__bitboard + self.__current_position_mask

    def get_winning_coordinates(self):
        """
        Gets the initial and end coordinates that caused the player to win.
        Note that this method call be called only after there's a win and
        thus will look at the opponent mask and not the current player one.
        In addition, note that this method does use loops to find the
        coordinates, since we can't determine it using standard bitwise
        operations. Thus, it'll better to not invoke it for determine if
        there's a winner and instead use the other methods which depend on
        bitwise operations and thus are much faster.

        :return: A tuple that contains two points, represented as a (row,
        column) tuple, which represents the winning point initial and end
        locations, or None if the player hasn't win yet.
        Example: ((2, 4), (5, 4)) (a.k.a, a vertical win in the 4'th column).
        """
        # Look for vertical win
        result = self.__vertical_win_lookup()
        if result is not None:
            return result

        # Look for horizontal win
        result = self.__horizontal_win_lookup()
        if result is not None:
            return result

        # Look for diagonal win
        return self.__diagonal_win_lookup()

    def get_board_human_representation(self, current_player, opponent_player):
        """
        Gets a string that represents the current board state.
        :param current_player: A character that identify the current player.
        :param opponent_player: A character that identify the opponent player.
        :return: A string that represents the board visually.
        """
        board_descriptor = []
        board_rows = []

        for r in range(Board.HEIGHT):
            buff = []
            for c in range(Board.WIDTH):
                if self.has_player_bit_at(r, c):
                    buff.append('[%s]' % current_player)
                elif self.has_opponent_bit_at(r, c):
                    buff.append('[%s]' % opponent_player)
                else:
                    buff.append('[ ]')
            board_descriptor.append(buff)

        # Create the board legend
        for i, line in enumerate(board_descriptor):
            board_rows.append('%d %s' % (i, ' '.join(line)))

        board_rows = [' '.join([' ' + str(x) + ' ' for x in range(
            Board.WIDTH)])] + board_rows

        return '  ' + '\n'.join(board_rows)

    def __copy__(self):
        """
        Shallow copy the given board.
        :return: The new, cloned, board instance.
        """
        copy = Board()

        copy.__bitboard = self.__bitboard
        copy.__current_position_mask = self.__current_position_mask
        copy.__performed_moves = self.__performed_moves
        copy.__player_sign = self.__player_sign

        return copy

    def evaluate(self, move_mask):
        """
        Perform an heuristic evaluation of the current board.
        :param move_mask: Additional move to apply on the evaluation.
        :return: The evaluation score.
        """
        # Do we got a draw?
        if self.__bitboard == Board.__board_full_mask:
            return Board.DRAW_SCORE

        player_bitboard = self.__current_position_mask | move_mask
        opponent_bitboard = self.get_opponent_board()

        # Iterate over the available winning patterns and check if we match
        # one of them. Because we will count the bit the number of bits set
        # on each pattern, the more patterns we'll match - the best.
        player_histogram = [0, 0, 0, 0, 0]
        opponent_histogram = [0, 0, 0, 0, 0]
        for pattern in Board.__winning_sequences:
            # Get the applicable sequence masks
            player_mask = pattern & player_bitboard
            opponent_mask = pattern & opponent_bitboard

            # Can SOMEONE do somethin' here?
            if player_mask == 0 and opponent_mask == 0:
                continue

            # Count the bits (a.k.a. discs) in each mask
            player_bits = Board.popcount(player_mask)
            opponent_bits = Board.popcount(opponent_mask)

            # A killer move?!
            if player_bits == Board.WIN_ROW_LENGTH:
                return Board.MAX_SCORE * self.__player_sign
            elif opponent_bits == Board.WIN_ROW_LENGTH:
                return Board.MIN_SCORE * self.__player_sign

            # Count in the histogram
            if opponent_bits == 0:
                player_histogram[player_bits] += 1
            elif player_bits == 0:
                opponent_histogram[opponent_bits] += 1

        # Move on each histogram bucket and calculate
        player_score = 0
        opponent_score = 0
        for i in range(len(self.__weights_histogram)):
            player_score += player_histogram[i] * \
                self.__weights_histogram[i]
            opponent_score += opponent_histogram[i] * \
                self.__weights_histogram[i]

        return self.__player_sign * (player_score - opponent_score)

    def __repr__(self):
        """
        Gets a string representation of this board state.
        :return: A string that represents this board state.
        """
        sb = "<Board %s>" % id(self)

        sb += "Bitboard (%s):\n%s\n" % (
            bin(self.__bitboard), Board.bitboard_to_string(self.__bitboard))
        sb += "Player Board (%s):\n%s\n" % (
            bin(self.__current_position_mask),
            Board.bitboard_to_string(self.__current_position_mask))
        sb += "Opponent Board (%s):\n%s\n" % (
            bin(self.get_opponent_board()),
            Board.bitboard_to_string(self.get_opponent_board()))
        return sb

    # endregion

    # region Static API

    @staticmethod
    def initialize():
        """
        Initialize the class static variables.
        """
        # Have we initialized already? (I'd use a flag here, but it's a waste)
        if Board.__board_full_mask != 0:
            return

        # Creates a bitmask of the most bottom row
        Board.__bottom_row_mask = Board.create_bottom_row_bitmask(
            Board.HEIGHT, Board.WIDTH)

        # Create a bitmask containing the whole the board
        Board.__board_full_mask = Board.__bottom_row_mask * \
            ((1 << Board.HEIGHT) - Board.SIZE_DIFF)

        # Create a sequence (list) of bitmasks each one describes a win
        # combination. This sequence will contain both horizontal, vertical
        #  and diagonal win possibilities. E.g., a sequence might be a
        # bitmask that contains (0,0), (0,1), (0,2) and (0,3) bits turned on.
        Board.__winning_sequences = []

        # Columns
        Board.__winning_sequences += Board.__create_winning_column_sequences()

        # Row
        Board.__winning_sequences += Board.__create_winning_row_sequences()

        # Diagonals
        Board.__winning_sequences += \
            Board.__create_winning_diagonal_sequences()

    @staticmethod
    def is_valid_column_index(index):
        """
        Verify if the given index is a valid column index.
        :param index: The column index.
        :return: True if the given value is a valid column, false otherwise.
        """
        return 0 <= index < Board.WIDTH

    @staticmethod
    def bitboard_to_string(b):
        """
        Converts the given bitboard into a string to view it nicely.

        Example: 0b100000010000011000011100001110000000
          0 1 2 3 4 5 6
        5 . . . . . . .
        4 . . . . . . .
        3 . . . . . . .
        2 . X X . . . .
        1 . X X X . . .
        0 . X X X X X .
        :param b: The bitboard.
        :param rows: The number of rows.
        :param columns: The number of columns.
        :return: The representation string.
        """
        # Setup
        size = max(Board.WIDTH, Board.HEIGHT)
        sequences = []
        container = []

        # Read the bitboard and build a corresponding array that represents it
        for c in range(size - Board.SIZE_DIFF - 1, -1, -1):
            sequence = []
            for r in range(size):
                position = r * size + c
                if (b & (1 << position)) != 0:
                    sequence.append('X')
                else:
                    sequence.append('.')
            sequences.append(sequence)

        # Add a lovely legend!
        container.append((' ' * 2) + ' '.join([str(x) for x in range(size)]))
        for i, sequence in enumerate(sequences):
            container.append(
                ' '.join([str(size - i - Board.SIZE_DIFF - 1)] + sequence))

        return '\n'.join(container)

    @staticmethod
    def popcount(mask):
        """
        Get the total number of bits set on the given bits mask.
        This implementation is based on the problem known as the "Hamming
        weight" and the selected implementation is the best for cases where
        most bits are 0, which most likely relevant to our case.
        See:
        https://en.wikipedia.org/wiki/Hamming_weight#Efficient_implementation
        https://stackoverflow.com/a/109025

        :param mask: The bitmask to count.
        :return: Integer representing the total bit number.
        """
        # Setup
        counter = 0

        # Back iterate and count each "on" bit
        while mask != 0:
            counter += 1
            mask &= mask - 1

        return counter

    @staticmethod
    def create_top_bitmask(column):
        """
        Creates a bitmask containing a single 1 bit that is corresponding to
        the top cell of a given column.
        :param column: The column to highlight.
        :return: The bit mask.
        """
        return 1 << ((Board.HEIGHT - Board.SIZE_DIFF) +
                     column * (Board.HEIGHT + Board.SIZE_DIFF))

    @staticmethod
    def create_bottom_bitmask(column):
        """
        Creates a bitmask containing a single 1 bit that is corresponding to
        the bottom cell of a given column.
        :param column: The column to highlight.
        :return: The bit mask.
        """
        return 1 << column * (Board.HEIGHT + Board.SIZE_DIFF)

    @staticmethod
    def create_bottom_row_bitmask(rows, columns):
        """
        Recursively create a mask with on flag on each bit at the bottom row.
        :param rows: The number of rows.
        :param columns: The number of columns.
        :return: The bitmask.
        """
        if columns == 0:
            return 0

        return Board.create_bottom_row_bitmask(rows, columns - 1) \
            | 1 << (columns - Board.SIZE_DIFF) * (rows + Board.SIZE_DIFF)

    @staticmethod
    def create_row_bitmask(row, columns):
        """
        Recursively create a mask with on flag on each bit at the given row.
        :param row: The row.
        :param columns: The remaining columns.
        :return: The bitmask.
        """
        if columns == 0:
            return 0

        return Board.create_row_bitmask(row, columns - 1) \
            | (2 ** row) << (columns - Board.SIZE_DIFF) * \
                            (Board.HEIGHT + Board.SIZE_DIFF)

    # endregion

    # region Private API

    @staticmethod
    def __create_winning_column_sequences():
        """
        Create the column combinations that will lead the user to win the
        game.
        :return: A list of winning sequences.
        """
        sequences = []
        for c in range(Board.WIDTH):
            base_mask = Board.create_column_bitmask(c)
            for i in range(0, Board.HEIGHT - Board.WIN_ROW_LENGTH + 1):
                m = base_mask & (base_mask >> i) & \
                    (base_mask << Board.HEIGHT - Board.WIN_ROW_LENGTH - i)
                sequences.append(m)
        return sequences

    @staticmethod
    def __create_winning_row_sequences():
        """
        Create the row combinations that will lead the user to win the
        game.
        :return: A list of winning sequences.
        """
        sequences = []
        computed_height = Board.HEIGHT + Board.SIZE_DIFF
        for r in range(Board.HEIGHT):
            base_mask = Board.create_row_bitmask(r, Board.WIDTH)
            for i in range(0, Board.WIDTH - Board.WIN_ROW_LENGTH + 1):
                m = base_mask & (base_mask >> computed_height * i) & \
                    (base_mask << computed_height * (
                        Board.WIDTH - Board.WIN_ROW_LENGTH - i))
                sequences.append(m)
        return sequences

    @staticmethod
    def __create_winning_diagonal_sequences():
        """
        Create the diagonal combinations that will lead the user to win the
        game.
        :return: A list of winning sequences.
        """
        # Init
        left_top_diagonals = []
        left_bottom_diagonals = []
        right_top_diagonals = []
        right_bottom_diagonals = []

        # Iterate on each row that can produce us a valid "full" diagonal.
        # That means, for row (0,0) to (5,5) the full diagonal will contain
        # the points (0, 0), (1, 1), (2, 2), (3, 3), (4, 4) and (5, 5).
        for row in range(Board.MIN_DIAGONAL_ROW, Board.HEIGHT):
            # Calculate the diagonal base positions
            left_top = Board.create_bottom_bitmask(Board.HEIGHT - row)
            left_bottom = Board.create_top_bitmask(row)
            right_top = Board.create_bottom_bitmask(row)
            right_bottom = Board.create_top_bitmask(Board.HEIGHT - row)

            # Iterate on the board width and fetch the top-right (width+1)
            # or bottom-left (width-1) point.
            for column in range(Board.WIDTH):
                left_top |= left_top << (Board.WIDTH + 1)
                left_bottom |= left_bottom >> (Board.WIDTH + 1)
                right_top |= right_top >> (Board.WIDTH - 1)
                right_bottom |= right_bottom << (Board.WIDTH - 1)

            # right_top = right_top << 7
            # Save the diagonal with their corresponding initial row
            left_top_diagonals.append((row, left_top))
            left_bottom_diagonals.append((row, left_bottom))
            right_top_diagonals.append((row, right_top))
            right_bottom_diagonals.append((row, right_bottom))

        # Now we shall start and gather each diagonal combination, we'll do
        # it by taking each "full" diagonal and shift it by the times of
        # the row it was belong to (-1 cause we already saw the first point).
        diagonals = []

        # Resolve the top left diagonals (moving by width+1)
        diagonals += Board.__resolve_base_diagonals(
            left_top_diagonals,
            mask_fn=lambda m, i, l:
            (m << (Board.WIDTH + 1) *
             (l - i)) & m >> ((Board.WIDTH + 1) *
                              (Board.WIN_ROW_LENGTH - l)) +
                             (i * (Board.WIDTH + 1)))

        # Resolve the bottom left diagonals (moving by width+1)
        diagonals += Board.__resolve_base_diagonals(
            left_bottom_diagonals,
            mask_fn=lambda m, i, l:
            (m >> (Board.WIDTH + 1) * i) &
            (m << (Board.WIDTH + 1) * (l - i)))

        # Resolve the bottom left diagonals (moving by width-1)
        diagonals += Board.__resolve_base_diagonals(
            right_top_diagonals,
            mask_fn=lambda m, i, l:
            (m >> (Board.WIDTH - 1) * i) &
            (m << (Board.WIDTH - 1) * (l - i)))

        # Resolve the bottom right diagonals
        diagonals += Board.__resolve_base_diagonals(
            right_bottom_diagonals,
            mask_fn=lambda m, i, l:
            (m << ((Board.WIDTH - 1) * i)) &
            (m >> (Board.HEIGHT * (Board.WIN_ROW_LENGTH - l + (l - i)))))

        return diagonals

    @staticmethod
    def create_column_bitmask(column):
        """
        Creates a bitmask containing 1 on all the cells of a given column.
        :param column: The column to create the mask for.
        :return: The bitmask.
        """
        return ((1 << Board.HEIGHT) - Board.SIZE_DIFF) << \
            column * (Board.HEIGHT + Board.SIZE_DIFF)

    def __get_player_winning_mask(self):
        """
        Gets a bitboard mask that contains the locations in which the
        current player will win if she plays in.
        :return: A bitboard mask.
        """
        return self.__compute_winning_mask(self.__current_position_mask,
                                           self.__bitboard)

    def __get_opponent_winning_mask(self):
        """
        Gets a bitboard mask that contains the locations in which the
        current player opponent will win if she plays in.
        :return: A bitboard mask.
        """
        # Compute the opponent bitboard
        opponent_bitboard = self.__current_position_mask ^ self.__bitboard

        # Compute the winning positions
        return self.__compute_winning_mask(opponent_bitboard,
                                           self.__bitboard)

    def __compute_winning_mask(self, player_mask, bitboard):
        """
        Computes a mask that contains the current player winning positions.
        :param player_mask: The current player mask.
        :param bitboard: The bitboard mask.
        :return: A mask that contains a bitboard that represents all of
        \the winning positions.
        """

        # Setup
        computed_height = Board.HEIGHT + Board.SIZE_DIFF

        # Check if we can win by performing a vertical move. This case is
        # true simply when we have bits aligned one after another,
        # so we can just shift them to check for matching.
        mask = (player_mask << 1) & (player_mask << 2) & (player_mask << 3)

        # Check if we can win by performing a vertical win. To do that we
        # need to align the bits by the board rows count and check for the
        # existence of 3 bits that aligned correctly one after another.
        # Unlike vertical win, which can be performed by one move, we got
        # two possibilities here - move to the right or move to the left. We
        # need to check them both.

        # Left horizontal movement win
        h_mask = (player_mask >> computed_height) \
            & (player_mask >> 2 * computed_height)
        mask |= h_mask & (player_mask >> 3 * computed_height)
        mask |= h_mask & (player_mask << computed_height)

        # Right horizontal movement win
        h_mask = (player_mask << computed_height) \
            & (player_mask << 2 * computed_height)
        mask |= h_mask & (player_mask << 3 * computed_height)
        mask |= h_mask & (player_mask >> computed_height)

        # Finally, we need to check for diagonals. To do so we need both to
        # shift the bits in the corresponding direction and move them in
        # accordance to the board rows count.

        # Left to right diagonal
        d_mask = (player_mask << Board.HEIGHT) & \
                 (player_mask << 2 * Board.HEIGHT)
        mask |= d_mask & (player_mask << 3 * Board.HEIGHT)
        mask |= d_mask & (player_mask >> Board.HEIGHT)

        d_mask = (player_mask >> Board.HEIGHT) & \
                 (player_mask >> 2 * Board.HEIGHT)
        mask |= d_mask & (player_mask << Board.HEIGHT)
        mask |= d_mask & (player_mask >> 3 * Board.HEIGHT)

        # Right to left diagonal
        d_mask = (player_mask << (Board.HEIGHT + 2)) & \
                 (player_mask << 2 * (Board.HEIGHT + 2))
        mask |= d_mask & (player_mask << 3 * (Board.HEIGHT + 2))
        mask |= d_mask & (player_mask >> (Board.HEIGHT + 2))
        d_mask = (player_mask >> (Board.HEIGHT + 2)) & \
                 (player_mask >> 2 * (Board.HEIGHT + 2))
        mask |= d_mask & (player_mask << (Board.HEIGHT + 2))
        mask |= d_mask & (player_mask >> 3 * (Board.HEIGHT + 2))

        # Mask out the rest of the bitboard
        return mask & (Board.__board_full_mask ^ bitboard)

    def __vertical_win_lookup(self):
        """
        Performs a lookup for a vertical win.
        :return: The initial and end coordinates of the winning discs,
        or None if no such win achieved.
        """
        # Initialize our variables
        # Note that we use a counter and initial position techinique since
        # we can't assume we will thaw exactly Board.WIN_ROW_LENGTH win
        # value. In other words, assuming WIN_ROW_LENGTH = 4, we might thaw
        # a win by having a 4 row, but might actually create a row with > 4
        #  as well. In that cause it'll be more logical to mark the entire
        # discs and not only the 4 out of N.
        initial_position = None
        counter = 0
        for c in range(Board.WIDTH):
            for r in range(Board.HEIGHT):
                # Do we have a disc here?
                if self.has_opponent_bit_at(r, c):
                    # Count that spot
                    counter += 1

                    # Mark the initial position if we need to
                    if initial_position is None:
                        initial_position = (r, c)
                else:
                    # Have we satisfy our need?
                    if counter >= Board.WIN_ROW_LENGTH:
                        break

                    # Reset
                    counter = 0
                    initial_position = None

        # Do we have a winner?
        if counter >= Board.WIN_ROW_LENGTH:
            # Yup, we got a win! Remember to do counter - 1 since we
            # already counted the first location.
            return initial_position, \
                   (initial_position[0] + counter - 1,
                    initial_position[1])

        # No win found
        return None

    def __horizontal_win_lookup(self):
        """
        Performs a lookup for a horizontal win.
        :return: The initial and end coordinates of the winning discs,
        or None if no such win achieved.
        """
        # Initialize our variables
        initial_position = None
        counter = 0

        # Iterate and search
        for r in range(Board.HEIGHT):
            for c in range(Board.WIDTH):
                # Do we have a disc here?
                if self.has_opponent_bit_at(r, c):
                    # Count that spot
                    counter += 1

                    # Mark the initial position if we need to
                    if initial_position is None:
                        initial_position = (r, c)
                else:
                    # Have we satisfy our need?
                    if counter >= Board.WIN_ROW_LENGTH:
                        break

                    # Reset
                    counter = 0
                    initial_position = None

        # Do we have a winner?
        if counter >= Board.WIN_ROW_LENGTH:
            # Yup, we got a win! Remember to do counter - 1 since we
            # already counted the first location.
            return initial_position, \
                   (initial_position[0],
                    initial_position[1] + counter - 1)

        # No win found
        return None

    def __diagonal_win_lookup(self):
        """
        Performs a lookup for a diagonal win.
        :return: The initial and end coordinates of the winning discs,
        or None if no such win achieved.
        """
        diagonals = []
        num = Board.HEIGHT + Board.WIDTH - 1

        # Collect the diagonals
        for i in range(num):
            # Check our directions
            start_row = min(i, Board.HEIGHT - 1)
            start_col = i - start_row
            length = min(start_row, Board.WIDTH - 1 - start_col) + 1

            # Do we even need that row? It has a win potential?
            if length < Board.WIN_ROW_LENGTH:
                continue

            left_diagonal = []
            right_diagonal = []
            for j in range(length):
                # Collect the top left to bottom right diagonals
                left_diagonal.append((start_row - j, start_col + j))

                # Collect the top right to bottom left diagonals
                right_diagonal.append((start_row - j,
                                       Board.WIDTH - 1 - (start_col + j)))

            diagonals.append(left_diagonal)
            diagonals.append(right_diagonal)

        # Check each diagonal
        for diagonal in diagonals:
            counter = 0
            initial_index = None

            # Count how much points we got in this diagonal
            for i, point in enumerate(diagonal):
                # We have a disc on that diagonal part?
                if self.has_opponent_bit_at(point[0], point[1]):
                    # Mark it
                    if initial_index is None:
                        initial_index = i
                    counter += 1
                else:
                    # Did we got enough discs?
                    if counter >= Board.WIN_ROW_LENGTH:
                        break

                    # Reset
                    counter = 0
                    initial_index = None

            # Did we got a row?
            if counter >= Board.WIN_ROW_LENGTH:
                return diagonal[initial_index], diagonal[initial_index +
                                                         counter - 1]

        return None

    # endregion

    @staticmethod
    def __resolve_base_diagonals(base_diagonals, mask_fn):
        """
        Apply a custom mask callback and generate a sequence of diagonals
        based on the given base diagonals.
        :param base_diagonals: The base diagonal.
        :param mask_fn: The mask creation callback.
        :return: A list of resolved diagonals.
        """
        diagonals = []
        for diagonal in base_diagonals:
            base_mask = diagonal[1]

            if diagonal[0] < Board.WIN_ROW_LENGTH:
                # This is an exact 4 lines diagonal, so just take it.
                diagonals.append(diagonal[1])
                continue

            # Calculate the diagonal length
            length = diagonal[0] - (Board.WIN_ROW_LENGTH - 1)
            for i in range(length + 1):
                # Create a mask
                mask = mask_fn(diagonal[1], i, length)
                diagonals.append(base_mask & mask)

        return diagonals
