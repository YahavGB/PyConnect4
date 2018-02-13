##############################################################################
# PyConnect4: ui.py
# DESCRIPTION: This file contains the implementation of the game GUI.
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


############################################################
# Imports
############################################################

import socket
import math
import os
import tkinter as t
from PIL import ImageTk, Image

from communicator import Connect4Communicator
from game import Game
from board import Board
from player import Player
from ai import AI


class Connect4GUI(t.Frame):
    """
    Designed to handle the GUI aspects (creating a window, buttons and
    pop-ups. Also initializes the communicator object.
    """

    ############################################################
    # Constants
    ############################################################

    #: Defines the game title.
    GAME_TITLE = "Four in a Row"

    #: Defines the game title bar text.
    GAME_TITLEBAR_FORMAT = "Four in a Row (%s player)"

    #: Defines the invalid play location message.
    INVALID_LOCATION_MESSAGE = "The selected location is invalid."

    #: Defines the current player name title.
    PLAYER_TITLE = "You"

    #: Defines the opponent player name title.
    OPPONENT_TITLE = "Opponent"

    #: Defines the message that will tell the player is playing now.
    NOW_PLAYING = "Now Playing"

    #: Defines the moves counter.
    MOVE_NUMBER_FORMAT = "Move #%d"

    #: Defines the Win message.
    CURRENT_PLAYER_WON_MESSAGE = "You've won! You Rocks!"

    #: Defines the Lose message.
    CURRENT_PLAYER_LOSE_MESSAGE = "Ugh, You lost..."

    #: Describe the server connecting message.
    SERVER_WAITING_MESSAGE = "Waiting for a client (Server IP: %s)..."

    #: Describe the client connecting message.
    CLIENT_WAITING_MESSAGE = "Connecting to the server..."

    #: Describe the opponent thinking message.
    OPPONENT_THINKING_MESSAGE = "Opponent is thinking, please wait..."

    #: Describe the AI thinking message.
    AI_THINKING_MESSAGE = "The Amazing AI is generating move..."

    #: Defines the game title Y padding.
    GAME_TITLE_PADDING_Y = 35

    #: Defines the screen width.
    SCREEN_WIDTH = 645

    #: Defines the screen height.
    SCREEN_HEIGHT = 485

    #: Defines the width for each board spot (a.k.a disc container).
    BOARD_LOCATION_SIZE_X = 50

    #: Defines the height for each board spot (a.k.a disc container).
    BOARD_LOCATION_SIZE_Y = 50

    #: Defines the board X padding.
    BOARD_PADDING_X = 20

    #: Defines the board Y padding.
    BOARD_PADDING_Y = 10

    #: Defines the status bar Y padding.
    STATUS_BAR_PADDING_Y = 20

    #: Defines the player panels Y padding.
    PLAYER_PANEL_PADDING_Y = 20

    #: Defines the Y padding between the player title and subtitle.
    PLAYER_PANEL_PADDING_TO_SUBTITLE_Y = 25

    #: Defines the Y padding between the player subtitle and image.
    PLAYER_PANEL_PADDING_TO_IMAGE_Y = 30

    #: Defines the images base path.
    IMAGES_BASE_PATH = 'images'

    #: Defines the game background image name.
    IMAGE_BACKGROUND = 'background.jpg'

    #: Defines the game board image name.
    IMAGE_BOARD_BACKGROUND = 'board_background.jpg'

    #: Defines the disc image path (should be formatted).
    IMAGE_DISC_FORMAT = 'disc_%s.jpg'

    #: Defines the column highlighter image path..
    IMAGE_COLUMN_HIGHLIGHTER = 'highlight_arrow.jpg'

    #: Defines the default text color.
    DEFAULT_COLOR = 'white'

    #: Defines the errors text color.
    ERROR_TEXT_COLOR = 'red'

    #: Defines the win message color.
    CURRENT_PLAYER_WON_COLOR = "green"

    #: Defines the lose message color.
    CURRENT_PLAYER_LOSE_COLOR = "red"

    #: Defines the status bar font.
    STATUS_BAR_FONT = "Helvetica 22 italic"

    #: Defines the game title font.
    TITLE_FONT = "Helvetica 32 bold"

    #: Defines the player title font.
    PLAYER_TITLE_FONT = "Helvetica 24"

    #: Defines the player sub-title font.
    PLAYER_SUBTITLE_FONT = "Helvetica 16"

    #: Defines the current turn font.
    CURRENT_TURN_FONT = "Helvetica 18 bold"

    #: Defines the moves counter font.
    MOVES_COUNTER_FONT = "Helvetica 18 italic"

    #: Defines the board marker fill.
    BOARD_MARKER_FILL = ''  # = transparent

    #: Defines the board marker weight.
    BOARD_MARKER_WEIGHT = 7

    #: Defines the timeout for a status bar timeout delegate invocation.
    STATUS_BAR_TIMEOUT_DURATION = 4000

    #: Define a time of AI move generation delay. This value must be used
    # to allow the rendering pipeline to work correctly.
    AI_RENDER_DELAY = 200

    #: The default AI move generation timeout, in seconds.
    AI_DEFAULT_TIMEOUT = 3

    #: Define the angle in which we're gonna move to create a circle
    # stride. Note that 2 pi radians = 60 degrees
    POLY_CIRCLE_STRIDE_ANGLE = math.pi * 2

    ############################################################
    # Ctor
    ############################################################

    def __init__(self, parent, game, player, port, ip=None):
        """
        Initializes the GUI and connects the communicator.
        :param parent: the tkinter root.
        :type parent: t.Window
        :param ip: the ip to connect to.
        :param port: the port to connect to.
        """
        t.Frame.__init__(self, parent)

        # Setup the iVars
        self.__parent = parent
        self.__game = game
        self.__ai_engine = AI()
        self.__current_player = player
        self.__board_pos_x = 0
        self.__board_pos_y = 0
        self.__current_turn_pos_y = 0
        self.__board_discs = {}
        self.__current_highlighted_row = None
        self.__highlighter_res_id = None
        self.__status_bar_res_id = None
        self.__status_bar_timeout_res_id = None
        self.__current_turn_left_res_id = None
        self.__current_turn_right_res_id = None
        self.__current_move_res_id = None
        self.__board_ui_disabled = True
        self.__is_current_turn = player.get_player_number() == Game.PLAYER_ONE
        self.__communicator = Connect4Communicator(self.__parent, port, ip)

        # Initialize the drawing canvas
        self.__canvas = t.Canvas(self.__parent,
                                 width=Connect4GUI.SCREEN_WIDTH,
                                 height=Connect4GUI.SCREEN_HEIGHT)
        self.__canvas.image_resources = {}  # Saves us from being GC'ed.

        # Setup the UI
        self.__canvas.pack(expand=t.YES, fill=t.BOTH, padx=0, pady=0)
        self.__init_ui()

        # Write the title bar text
        self.__parent.title(Connect4GUI.GAME_TITLEBAR_FORMAT %
                            self.__current_player.get_color())

        # Register UI events
        self.__parent.bind('<Button-1>', self.__handle_mouse_click)
        self.__parent.bind('<Motion>', self._handle_mouse_move)
        game.set_on_game_over_callback(self.__handle_game_end)

        # Start to work on the communication
        self.__setup_communication_channel()

    ############################################################
    # Private Methods
    ############################################################

    # region Public API

    def perform_player_move(self, column):
        """
        Perform a move by the currently playing player/
        :param column: The played column.
        :return: True if the move successfully made, false otherwise.
        """
        # Clear the status bar
        self.truncate_status_bar()

        # Firstly perform the move locally.
        if not self.perform_move(self.__current_player, column):
            return False

        # Now transfer it to the opponent client.
        self.__communicator.move_played(
            self.__current_player.get_player_number(), column)

        return True

    def perform_move(self, player, column):
        """
        Performs a single move for the given player.
        :param player: The playing player instance.
        :param column: The column to play in.
        :return: True if the move successfully made, false otherwise.
        """
        # Perform the move in the UI and the game
        if not self.__perform_move(column):
            return False

        # Mark that this is the {player}'s opponent turn
        self.__is_current_turn = not self.__is_current_turn
        self.__ui_set_current_turn(
            self.__game.get_opponent(player.get_player_number()))

        # Update the moves counter
        self.__ui_update_moves_counter()

        return True

    def add_disc(self, color, row, column):
        """
        Adds a disck to the board.
        :param color: The disc color.
        :param row: The row location.
        :param column: The column location.
        """
        # Get the disc image
        disc_img = self.__get_image(Connect4GUI.IMAGE_DISC_FORMAT % color)

        # Compute the right position
        pos_x = self.__board_pos_x + Connect4GUI.BOARD_PADDING_X + \
            Connect4GUI.BOARD_LOCATION_SIZE_X * column
        pos_y = self.__board_pos_y + Connect4GUI.BOARD_PADDING_Y + \
            Connect4GUI.BOARD_LOCATION_SIZE_Y * row

        # Draw the disc
        res_id = self.__canvas.create_image(pos_x, pos_y,
                                            image=disc_img, anchor=t.NW)
        self.__board_discs[(row, column)] = res_id

    def highlight_column(self, column):
        """
        Highlights the given column.
        :param column: The column number.
        """
        # Do we got a highlighted column?
        if self.__current_highlighted_row == column:
            return

        if self.__highlighter_res_id is not None:
            self.unhighlight_column()

        # Get the arrow picture
        arrow = self.__get_image(Connect4GUI.IMAGE_COLUMN_HIGHLIGHTER)

        # Calculate the positioning
        pos_x = self.__board_pos_x + Connect4GUI.BOARD_LOCATION_SIZE_X * \
            column + arrow.width() / 2
        pos_y = self.__board_pos_y - arrow.height()

        # Render
        self.__current_highlighted_row = column
        self.__highlighter_res_id = self.__canvas.create_image(pos_x, pos_y,
                                                               image=arrow,
                                                               anchor=t.NW)

    def unhighlight_column(self):
        """
        Un-highlight the currently highlighted column.
        """
        if self.__highlighter_res_id is not None:
            self.__canvas.delete(self.__highlighter_res_id)
            self.__highlighter_res_id = None
            self.__current_highlighted_row = None

    def set_status_bar_text(self, text, color, timeout_delegate=None):
        """
        Sets the status bar text.
        :param text: The text to put.
        :param color: The text color.
        :param timeout_delegate: A delegate to invoke after a given timeout.
        """
        # If we already got content on our status bar, remove it first.
        if self.__status_bar_res_id is not None:
            self.truncate_status_bar()

        # Compute the positioning
        pos_x = Connect4GUI.SCREEN_WIDTH / 2
        pos_y = self.__board_pos_y / 2 + Connect4GUI.STATUS_BAR_PADDING_Y

        # Render
        self.__status_bar_res_id = self.__canvas.create_text(
            pos_x, pos_y,
            fill=color, font=Connect4GUI.STATUS_BAR_FONT, text=text)

        # Should we invoke any timeout delegate?
        if timeout_delegate:
            # Avoid duplication
            if self.__status_bar_timeout_res_id is not None:
                self.after_cancel(self.__status_bar_timeout_res_id)
                self.__status_bar_timeout_res_id = None

            # Schedule
            self.__status_bar_timeout_res_id = self.after(
                Connect4GUI.STATUS_BAR_TIMEOUT_DURATION, timeout_delegate)

    def truncate_status_bar(self):
        """
        Truncate the status bar.
        """
        # Did we got a status bar resource?
        if self.__status_bar_res_id is not None:
            self.__canvas.delete(self.__status_bar_res_id)
            self.__status_bar_res_id = None

        # Clear the status bar timer
        if self.__status_bar_timeout_res_id is not None:
            self.after_cancel(self.__status_bar_timeout_res_id)
            self.__status_bar_timeout_res_id = None

    # endregion

    # region UI Events

    def __handle_game_end(self, game, winner):
        """
        Handle the game over event.
        :param game: The game instance.
        :param winner: The winner player number.
        """
        # Update the status bar
        this_player_won = winner == self.__current_player.get_player_number()
        if this_player_won:
            color = Connect4GUI.CURRENT_PLAYER_WON_COLOR
            self.set_status_bar_text(Connect4GUI.CURRENT_PLAYER_WON_MESSAGE,
                                     color)
        else:
            color = Connect4GUI.CURRENT_PLAYER_LOSE_COLOR
            self.set_status_bar_text(Connect4GUI.CURRENT_PLAYER_LOSE_MESSAGE,
                                     color)

        # Mark the winning discs positions
        initial_coord, end_coord = game.get_board().get_winning_coordinates()
        self.__ui_mark_board(initial_coord, end_coord, color)

        # Clearn the current turn indicator
        self.__ui_clean_current_turn()

        # Disable the board UI
        self.__board_ui_disabled = True

    def __handle_mouse_click(self, event):
        """
        Handle the mouse click event.
        :param event: The even information.
        """
        if self.__is_board_ui_disabled():
            return

        # Clear the cursor
        self.unhighlight_column()

        # Did we selected any column to play in?
        column = self.__get_mouse_board_column(event.x, event.y)

        if column is None:
            return

        if not self.perform_player_move(column):
            self.set_status_bar_text(Connect4GUI.INVALID_LOCATION_MESSAGE,
                                     Connect4GUI.ERROR_TEXT_COLOR,
                                     lambda: self.truncate_status_bar())

    def _handle_mouse_move(self, event):
        """
        Handle the mouse click event.
        :param event: The even information.
        """
        self.__handle_column_highlight(event)

    # endregion

    # region Communication

    def __setup_communication_channel(self):
        """
        Setups the game communication channel.
        """
        # Show the connection message
        if self.__current_player.get_player_number() == Game.PLAYER_ONE:
            # This is the server program according to the instructions
            self.set_status_bar_text(Connect4GUI.SERVER_WAITING_MESSAGE %
                                     self.__communicator.get_ip_address(),
                                     Connect4GUI.DEFAULT_COLOR)
        else:
            # This is the client program
            self.set_status_bar_text(Connect4GUI.CLIENT_WAITING_MESSAGE,
                                     Connect4GUI.DEFAULT_COLOR)

        # Register the UI events
        self.__communicator.set_on_connected(self.__on_connected)
        self.__communicator.set_on_player_selected(self.__on_player_selected)
        self.__communicator.set_on_move_performed(
            self.__handle_move_played)

        # Attempt to connect
        self.__communicator.connect()

    def __on_connected(self):
        """
        Handle the "on opponent connected" event.
        """
        # Notify the other player who are we
        self.__communicator.set_player_type(
            self.__current_player.get_player_number(),
            self.__current_player.get_player_type())

    def __handle_move_played(self, player, column):
        """
        Handle the "move played" event.
        :param player: The player who performed the move.
        :param column: The move column.
        """
        # We shouldn't handle our moves, only our opponent
        if self.__current_player.get_player_number() == player:
            return

        # Perform the move
        self.perform_move(self.__game.get_opponent(
            self.__current_player.get_player_number()), column)

        if self.__game.get_winner() is None:
            # Do we play as AI?
            if self.__current_player.get_player_type() == \
                    Player.PLAYER_TYPE_COMPUTER:
                self.after(Connect4GUI.AI_RENDER_DELAY, self.__handle_ai_move)

    def __on_player_selected(self, player_number, player_type):
        """
        Handle the "player selected" (a.k.a. "human"/"ai" chose) event.
        :param player_number: The player number.
        :param player_type: The player type.
        """
        # We got a message for our opponent?
        if self.__current_player.get_player_number() == player_number:
            return

        # Update the opponent player information
        self.__game.get_player(player_number).set_player_type(player_type)

        # Remove the waiting status bar title.
        self.truncate_status_bar()

        # Create the players panels
        self.__ui_create_player_panel(self.__game.get_player(Game.PLAYER_ONE))
        self.__ui_create_player_panel(self.__game.get_player(Game.PLAYER_TWO))

        # Enable the UI
        self.__board_ui_disabled = False

        # Starts the game
        self.__start_game()

    # endregion

    # region Private Helpers

    def __get_image(self, image_path):
        """
        Gets an image resource.
        :param image_path: The image path.
        :return: The loaded image resource, or the cached one if the image
        was already loaded.
        :type ImageTk.PhotoImage:
        """
        image_path = os.path.join(Connect4GUI.IMAGES_BASE_PATH, image_path)
        if image_path in self.__canvas.image_resources:
            return self.__canvas.image_resources[image_path]

        img = Image.open(image_path).convert('RGBA')
        image = ImageTk.PhotoImage(img)

        self.__canvas.image_resources[image_path] = image
        return image

    def __computes_polygon_oval_coords(self, x0, y0, x1, y1, stride=25,
                                       angle=0):
        """
        Compute the coordinates used to draw a polygon based oval with the
        given axis and rotation. We'll use this function to create rotatable
        oval.
        :param x0: The initial x coordinate.
        :param y0: The initial y coordinate.
        :param x1: The end x coordinate.
        :param y1: The end y coordinate.
        :param stride: The number of steps in the polygon division used to
        make it looks like a circle.
        :param angle: The rotation angle in degrees.
        :return: An array contains the coordinates for the polygon.
        """
        # Converts the angle into radians
        angle = math.radians(angle)

        # Gets the major axes
        major_x = (x1 - x0) / 2.0
        major_y = (y1 - y0) / 2.0

        # Computes the center location (ex6, lol)
        center_x = x0 + major_x
        center_y = y0 + major_y

        # Computes the oval polygon as a list of coordinates
        coordinates_list = []
        for i in range(stride):
            # Calculate the angle for this step
            theta = Connect4GUI.POLY_CIRCLE_STRIDE_ANGLE * (float(i) / stride)

            x1 = major_x * math.cos(theta)
            y1 = major_y * math.sin(theta)

            # Rotate the X and Y coordinates
            x = (x1 * math.cos(angle)) + (y1 * math.sin(angle))
            y = (y1 * math.cos(angle)) - (x1 * math.sin(angle))

            # Append them
            coordinates_list.append(round(x + center_x))
            coordinates_list.append(round(y + center_y))

        return coordinates_list

    def __in_board_column(self, column, x, y):
        """
        Determines if the given X and Y coordinates resist in the given X
        and Y coordinates.
        :param column: The column index.
        :param x: The X coordinate.
        :param y: The Y coordinate.
        :return: True if the coordinates are in the given column at the
        board, false otherwise.
        """
        # Compute the positions
        x0 = self.__board_pos_x + Connect4GUI.BOARD_PADDING_X + \
            (column * Connect4GUI.BOARD_LOCATION_SIZE_X)
        x1 = x0 + Connect4GUI.BOARD_LOCATION_SIZE_X

        y0 = self.__board_pos_y + Connect4GUI.BOARD_PADDING_Y
        y1 = y0 + (Board.HEIGHT * Connect4GUI.BOARD_LOCATION_SIZE_Y)

        # Do we have an intersection?
        if x0 <= x <= x1 and y0 <= y <= y1:
            return True

        return False

    def __is_board_ui_disabled(self):
        """
        Determine if the board UI is disabled or not.
        :return: True if the board UI is disabled, false otherwise.
        """
        return self.__board_ui_disabled or not self.__is_current_turn \
            or self.__current_player.get_player_type() == \
            Player.PLAYER_TYPE_COMPUTER

    def __get_mouse_board_column(self, x, y):
        """
        Gets the column in which the mouse sits in based on the given
        coordinates.
        :param x: The X coordinate.
        :param y: The Y coordinate.
        :return: The mouse board column or None if the mouse isn't on the
        board.
        """
        for c in range(Board.WIDTH):
            if self.__in_board_column(c, x, y):
                return c
        return None

    def __handle_column_highlight(self, event):
        """
        Handles the row highlight task.
        :param event: The mouse event container.
        """
        # Is the board disabled?
        if self.__is_board_ui_disabled():
            return

        # Do we need to highlight any row?
        highlighted_column = self.__get_mouse_board_column(event.x, event.y)
        if highlighted_column is None:
            return

        # Remove old highlights
        if self.__current_highlighted_row is not None:
            self.__current_highlighted_row = None
            self.unhighlight_column()

        # Highlight it
        self.highlight_column(highlighted_column)

    def __handle_ai_move(self):
        """
        Generates and plays a move by the AI.
        """

        def __do_handle_ai_move():
            """
            Do the actual AI move handling (after the GUI is updated).
            """
            # Init
            selected_move = None

            def move_selected(value):
                # Notify Python that this is an outer variable.
                # See: https://stackoverflow.com/a/12182176/1497516
                nonlocal selected_move

                # Save the last value.
                selected_move = value

            # Get the move
            self.__ai_engine.find_legal_move(self.__game, move_selected,
                                             Connect4GUI.AI_DEFAULT_TIMEOUT)

            # Play it
            self.perform_player_move(selected_move)

        # Set the AI thinking label for this player so she won't get bored
        self.set_status_bar_text(Connect4GUI.AI_THINKING_MESSAGE,
                                 Connect4GUI.DEFAULT_COLOR)

        # Do the actual AI handling
        self.after(Connect4GUI.AI_RENDER_DELAY, __do_handle_ai_move)

    def __start_game(self):
        """
        Starts the game.
        """
        # Mark the current player
        self.__ui_set_current_turn(self.__game.get_player(Game.PLAYER_ONE))

        # Set the move number
        self.__ui_update_moves_counter()

        # We're starting?
        if self.__is_current_turn:
            # Is this the AI who playing?
            if self.__current_player.get_player_type() == \
                    Player.PLAYER_TYPE_COMPUTER:
                self.after(Connect4GUI.AI_RENDER_DELAY, self.__handle_ai_move)

    def __perform_move(self, column):
        """
        Performs a single move.
        :param column: The column to play in.
        :return: True if the move have successfully done, false otherwise.
        """
        # Can we perform that move?
        if not self.__game.is_valid_move(column):
            return False

        # Get the disk row
        row = Board.HEIGHT - 1 - self.__game.get_board() \
            .count_column_items(column)
        player_color = self.__game.get_player(
            self.__game.get_current_player()).get_color()

        # Put the disc in our lovely gui
        self.add_disc(player_color, row, column)

        # Perform the move
        self.__game.make_move(column)

        # Re-render the current moves counter
        self.__ui_update_moves_counter()

        return True

    def __init_ui(self):
        """
        Initialize and render the game UI.
        """
        # Create the background
        self.__ui_create_background()

        # Create the background
        self.__ui_create_board()

        # Disable the option to resize the window
        self.__parent.resizable(False, False)

    def __ui_create_background(self):
        """
        Renders the game background (and the title... haha).
        """
        # Background Image
        bg_image = self.__get_image(Connect4GUI.IMAGE_BACKGROUND)
        self.__canvas.create_image(0, 0, image=bg_image, anchor=t.NW)

        # The game title
        self.__canvas.create_text(Connect4GUI.SCREEN_WIDTH / 2,
                                  Connect4GUI.GAME_TITLE_PADDING_Y,
                                  fill=Connect4GUI.DEFAULT_COLOR,
                                  font=Connect4GUI.TITLE_FONT,
                                  text=Connect4GUI.GAME_TITLE)

    def __ui_create_board(self):
        """
        Renders the board.
        """
        # Load the background
        board_bg = self.__get_image(Connect4GUI.IMAGE_BOARD_BACKGROUND)

        # Position in the center of the screen
        self.__board_pos_x = math.floor((Connect4GUI.SCREEN_WIDTH -
                                         board_bg.width()) / 2)
        self.__board_pos_y = math.floor((Connect4GUI.SCREEN_HEIGHT -
                                         board_bg.height()) / 1.4)
        self.__canvas.create_image(self.__board_pos_x, self.__board_pos_y,
                                   image=board_bg, anchor=t.NW)

    def __ui_create_player_panel(self, player):
        """
        Renders the player panel.
        :param player: The player instance we're rendering the panel for.
        :param is_left_panel: True if this is the left panel, false otherwise.
        """
        # Setup
        is_left_panel = self.__ui_get_left_player(player)

        pos_x = 0
        pos_y = self.__board_pos_y + Connect4GUI.PLAYER_PANEL_PADDING_Y

        # Resolve data based on the panel location
        if is_left_panel:
            pos_x = self.__board_pos_x / 2
        else:
            pos_x = self.__board_pos_x * 1.5 + self.__get_image(
                Connect4GUI.IMAGE_BOARD_BACKGROUND).width()

        # Render the player title
        if self.__current_player.get_player_number() == \
                player.get_player_number():
            player_title = Connect4GUI.PLAYER_TITLE
        else:
            player_title = Connect4GUI.OPPONENT_TITLE

        self.__canvas.create_text(pos_x, pos_y,
                                  # fill=player.get_color(),

                                  font=Connect4GUI.PLAYER_TITLE_FONT,
                                  text=player_title)

        # Create the subtitle
        pos_y += Connect4GUI.PLAYER_PANEL_PADDING_TO_SUBTITLE_Y
        self.__canvas.create_text(pos_x, pos_y,
                                  fill=player.get_color(),
                                  font=Connect4GUI.PLAYER_SUBTITLE_FONT,
                                  text=player.get_name())

        # Render the disc
        disc_img = self.__get_image(Connect4GUI.IMAGE_DISC_FORMAT %
                                    player.get_color())
        pos_y += Connect4GUI.PLAYER_PANEL_PADDING_TO_IMAGE_Y + \
            disc_img.height() / 2

        # Compute the right position
        self.__canvas.create_image(pos_x, pos_y, image=disc_img)

        # Save this position so we can use it later.
        self.__current_turn_pos_y = pos_y + disc_img.height()

    def __ui_get_left_player(self, player):
        """
        Determine if this is the left panel player.
        :param player: The player instance.
        :return: True if this is the left panel player, false otherwise.
        """
        if player.get_player_number() == Game.PLAYER_ONE:
            return True
        return False

    def __ui_set_current_turn(self, player):
        """
        Update the UI to show the current player.
        :param player: The player.
        """
        # Resolve the panel
        is_left_panel = self.__ui_get_left_player(player)

        if is_left_panel:
            # We already have that panel?
            if self.__current_turn_left_res_id is not None:
                return

            # Get the x position
            pos_x = self.__board_pos_x / 2

            # Remove the other canvas
            if self.__current_turn_right_res_id is not None:
                self.__canvas.delete(self.__current_turn_right_res_id)
                self.__current_turn_right_res_id = None
        else:
            # We already have that panel?
            if self.__current_turn_right_res_id is not None:
                return

            # Resolve the position
            pos_x = self.__board_pos_x * 1.5 + self.__get_image(
                Connect4GUI.IMAGE_BOARD_BACKGROUND).width()

            # Remove the other canvas
            if self.__current_turn_left_res_id is not None:
                self.__canvas.delete(self.__current_turn_left_res_id)
                self.__current_turn_left_res_id = None

        pos_y = self.__current_turn_pos_y
        res_id = self.__canvas.create_text(pos_x, pos_y,
                                           fill=Connect4GUI.DEFAULT_COLOR,
                                           font=Connect4GUI.CURRENT_TURN_FONT,
                                           text=Connect4GUI.NOW_PLAYING)

        if is_left_panel:
            self.__current_turn_left_res_id = res_id
        else:
            self.__current_turn_right_res_id = res_id

        # If this is the opponent player, notify the user via the status bar
        if self.__current_player != player:
            self.set_status_bar_text(Connect4GUI.OPPONENT_THINKING_MESSAGE,
                                     Connect4GUI.DEFAULT_COLOR)
        else:
            self.truncate_status_bar()

    def __ui_clean_current_turn(self):
        """
        Cleans the current turn indicator.
        """
        # Left panel
        if self.__current_turn_left_res_id is not None:
            self.__canvas.delete(self.__current_turn_left_res_id)
            self.__current_turn_left_res_id = None

        # Right panel
        if self.__current_turn_right_res_id is not None:
            self.__canvas.delete(self.__current_turn_right_res_id)
            self.__current_turn_left_res_id = None

    def __ui_update_moves_counter(self):
        """
        Sets the move number in the UI.
        :param number: The move number.
        """
        # Remove the old label
        if self.__current_move_res_id is not None:
            self.__canvas.delete(self.__current_move_res_id)
            self.__current_move_res_id = None

        # Compute the next move
        move_number = self.__game.get_moves_count() + 1

        # Compute the positions
        board_bg = self.__get_image(Connect4GUI.IMAGE_BOARD_BACKGROUND)
        pos_x = Connect4GUI.SCREEN_WIDTH / 2
        pos_y = self.__board_pos_y + board_bg.height() + 20

        self.__current_move_res_id = self.__canvas.create_text(
            pos_x, pos_y,
            fill=Connect4GUI.DEFAULT_COLOR,
            font=Connect4GUI.MOVES_COUNTER_FONT,
            text=(Connect4GUI.MOVE_NUMBER_FORMAT % move_number))

    def __ui_mark_board(self, initial_coord, end_coord, color):
        """
        Marks the given coordinates on the board.
        :param initial_coord: The initial coordinate.
        :param end_coord: The end coordinate.
        :param color: The color to use to mark the coordinates with.
        """
        # Calculate the marking oval coordinates based on the win sequence.
        angle = 0
        is_left_diagonal = False
        is_right_diagonal = False
        if initial_coord[1] == end_coord[1]:
            # Vertical win, so we'll mark one column on the x and the
            # difference between the columns in the y.
            diff_x = 1
            diff_y = (end_coord[0] - initial_coord[0]) + 1
        elif initial_coord[0] == end_coord[0]:
            # This is an horizontal win, so we'll mark one column on the y
            # and the difference between the columns in the x.
            diff_x = (end_coord[1] - initial_coord[1]) + 1
            diff_y = 1
        else:
            # This is a digaonal win. Now we need to determine where it
            # points to? It goes from top left to bottom right ("\") or from
            # bottom left to top right ("/").
            if initial_coord[1] < end_coord[1]:
                # This is a top left to bottom right diagonal.
                diff_x = (end_coord[1] - initial_coord[1]) + 1
                diff_y = 1
                angle = 45  # 45" clockwise
                is_left_diagonal = True
            else:
                # This is a top right to bottom left diagonal. Thus we need
                #  to firstly swap between the coordinates so we make sure
                # the min coordinate is less then the big one.
                tmp = initial_coord
                initial_coord = end_coord
                end_coord = tmp

                # And now we're save to calculate as we normally do
                diff_x = (end_coord[1] - initial_coord[1]) + 1
                diff_y = 1
                angle = -45  # 45" anti-clockwise
                is_right_diagonal = True

        # Computes the (x0, y0) and (x1, y1) coordinates
        x0 = self.__board_pos_x + Connect4GUI.BOARD_PADDING_X
        x0 += (initial_coord[1] * Connect4GUI.BOARD_LOCATION_SIZE_X)
        x1 = x0 + (diff_x * Connect4GUI.BOARD_LOCATION_SIZE_X)

        y0 = self.__board_pos_y + Connect4GUI.BOARD_PADDING_Y
        y0 += (initial_coord[0] * Connect4GUI.BOARD_LOCATION_SIZE_Y)
        y1 = y0 + (diff_y * Connect4GUI.BOARD_LOCATION_SIZE_Y)

        # If we had a diagonal, we need to to re-adjust the x and y
        # coordinates based on the the rotation changes. Thus, we need to
        # push the x and y coordinates accordingly to the X difference.
        if is_left_diagonal or is_right_diagonal:
            diagonal_diff = max(diff_x - 1, 1) / 2
            if is_left_diagonal:
                x0 -= Connect4GUI.BOARD_LOCATION_SIZE_X * diagonal_diff
                x1 += Connect4GUI.BOARD_LOCATION_SIZE_X * diagonal_diff
                y0 -= Connect4GUI.BOARD_LOCATION_SIZE_Y * diagonal_diff
                y1 -= Connect4GUI.BOARD_LOCATION_SIZE_Y * diagonal_diff
            else:
                x0 -= Connect4GUI.BOARD_LOCATION_SIZE_X * diagonal_diff
                x1 += Connect4GUI.BOARD_LOCATION_SIZE_X * diagonal_diff
                y0 += Connect4GUI.BOARD_LOCATION_SIZE_Y * diagonal_diff
                y1 += Connect4GUI.BOARD_LOCATION_SIZE_Y * diagonal_diff

        # Render
        self.__canvas.create_polygon(
            self.__computes_polygon_oval_coords(x0, y0, x1, y1, angle=angle),
            outline=color,
            width=Connect4GUI.BOARD_MARKER_WEIGHT,
            fill=Connect4GUI.BOARD_MARKER_FILL)

    # endregion
