##############################################################################
# PyConnect4: communicator.py
# DESCRIPTION: This file is responsible on the communication in the game.
# This file contains two classes - Communicator, which is a standard class
# (provided by the school, modified by us a bit), and a Connect4Communicator
# class, which inherits the base communicator class and responsible on the
# communication in the game. This class implements the game protocol and
# provides fast methods to determine the game changes.
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



import socket
import csv
from csv import StringIO
from board import Board
from game import Game
from player import Player


class Communicator:
    """
    Implements a non-blocking socket interface, where a message can be sent
    (immediately, after an initial connection has been created) and a message
    can be anticipated (after an initial connection has been created) and
    acted upon. The initial connection needs to be explicitly created by
    invoking connect(), which attempts establishment in a non blocking way.
    """

    WAIT_PERIOD = 100  # The wait period between two read attempts.
    BUFFER_SIZE = 1024  # The socket read / write buffer size (in bytes).
    CONNECT_TIMEOUT = 0.01  # The (client) connection timeout, set as a very

    # low value to create a connection "chance" (will
    # not happen if simply set to non blocking), but
    # without interfering the mainloop flow.

    def __init__(self, root, port, ip=None):
        """
        Constructor.
        :param root: the tkinter root (used for accessing the main loop).
        :param ip: the ip to connect to (client) or listen on (server).
        :param port: the port to connect to (client or listen on (server).
        :param server: true if the communicator is started in server mode,
                       otherwise false.
        """

        # Make sure we're not instantiating this class directly, this is a
        # workaround to achieve an abstract class decl.
        if type(self) == Communicator:
            raise TypeError()

        self.__root = root
        self.__port = port
        self.__ip = ip
        self.__socket = None
        self.__bound_func = None
        self.__server_socket = None
        # This means this communicator is a server communicator and is
        # responsible for trying and listening for an incoming connection.
        if self.__ip is None:
            self.__ip = socket.gethostbyname(socket.gethostname())
            self.__server_socket = socket.socket()
            self.__server_socket.bind((self.__ip, self.__port))
            self.__server_socket.listen(1)
            self.__server_socket.setblocking(0)  # non blocking.

    def connect(self):
        """
        Has to be invoked before any message sending and receiving can be
        accomplished. Uses the tkinter main loop to constantly listen on a
        given port for an incoming connection (server) or attempt and connect
        to a remote host via an IP and a port number.
        :return: None.
        """
        if self.__socket:
            return
        try:
            # This is the server communicator, try and accept connections.
            if self.__server_socket is not None:
                self.__socket, _ = self.__server_socket.accept()
                self.__socket.setblocking(0)
                self.__server_socket.close()
            # This is the client communicator, try and connect (quickly).
            else:
                self.__socket = socket.socket()
                self.__socket.settimeout(self.CONNECT_TIMEOUT)
                self.__socket.connect((self.__ip, self.__port))
                self.__socket.setblocking(0)
            self.__get_message()
        except socket.error:
            # Always close the socket if created, then make it none (this
            # way it is evident that a connection was not yet established).
            if self.__socket:
                self.__socket.close()
                self.__socket = None
            # Try again in a given interval.
            self.__root.after(self.WAIT_PERIOD, self.connect)

    def get_ip_address(self):
        return self.__ip

    def bind_action_to_message(self, func):
        """
        Binds a specific function to the event of receiving a message.
        :param func: the function.
        :return: None.
        """
        self.__bound_func = func

    def send_message(self, message):
        """
        Sends a message via the socket (if a connection is established).
        If the socket is not yet connected, does nothing (no retry).
        :param message: the message to be sent.
        :return: None.
        """
        if not self.is_connected():
            self.__root.after(self.WAIT_PERIOD, lambda: self.
                              send_message(message))
            return
        self.__socket.send(str(message).encode())

    def is_connected(self):
        """
        Returns true once a connection has been established.
        :return: true if a connection is established, else false.
        """
        return self.__socket is not None

    def _get_root(self):
        """
        Gets the tkinter root object (call marked as protected).
        :return: The tkinter root.
        """
        return self.__root

    def __get_message(self):
        """
        Upon regular intervals, try and receive a message from the connection
        socket (if established). If the message is empty, it means the remote
        host was abruptly closed, so do nothing. Otherwise invoke a given 2nd
        order function on the received message. If no message was made
        available, the method re-tries after a fixed interval.
        :return: None.
        """
        if self.is_connected():
            try:
                message = self.__socket.recv(
                    Communicator.BUFFER_SIZE).decode()
                # Don't register again - the remote host is closed. Close app.
                if len(message) == 0:
                    self.__root.destroy()
                    return
                if self.__bound_func is not None:
                    self.__bound_func(message)
            except socket.error:
                pass
        self.__root.after(self.WAIT_PERIOD, self.__get_message)


class Connect4Communicator(Communicator):
    """
    Implements a Connect4 specific communicator class. This class defines
    the game communication protocol and provide fixed set of methods that
    allows to communicate between two Connect4 programs.
    """

    ############################################################
    # Constants
    ############################################################

    #: Define a message type - player type selected.
    MESSAGE_TYPE_PLAYER_SELECTED = 1

    #: Define a message type - perform a move.
    MESSAGE_TYPE_MOVE = 2

    #: Describes the error message raised when calling bind_action_to_message.
    BIND_DISABLED_MESSAGE = "You can't set a bindable callback directly " \
                            "with Connect4Communicator. Use one of the " \
                            "events provided with this class instead."

    #: Describes the error message raised when sending invalid message type.
    INVALID_MESSAGE_TYPE = "Invalid message type given."

    #: Describes the error message raised when providing invalid message args.
    INVALID_MESSAGE_ARGS = "The given arguments are invalid for this message."

    #: Describes the length of a message.
    MESSAGE_FORMAT_LEN = 2

    #: Describes the location of the message type.
    MESSAGE_FORMAT_TYPE_LOC = 0

    #: Describes the location of the message args.
    MESSAGE_FORMAT_ARGS_LOC = 1

    #: Describe the args count for a move message.
    PLY_SEL_MESSAGE_ARGS_COUNT = 2

    #: Describe the player number in the player type message.
    PLY_SEL_MESSAGE_PLAYER_LOC = 0

    #: Describe the player type (ai/human) in the player type message.
    PLY_SEL_TYPE_LOC = 1

    #: Describe the args count for a move message.
    MOVE_MESSAGE_ARGS_COUNT = 2

    #: Describe the player number in the move message.
    MOVE_MESSAGE_PLAYER_LOC = 0

    #: Describe the column location in the move message.
    MOVE_MESSAGE_COLUMN_LOC = 1

    def __init__(self, root, port, ip=None):
        """
        Initializes a new communicator object .
        :param root: the tkinter root (used for accessing the main loop).
        :param ip: the ip to connect to (client) or listen on (server).
        :param port: the port to connect to (client or listen on (server).
        :param server: true if the communicator is started in server mode,
                       otherwise false.
        """
        # Super
        Communicator.__init__(self, root, port, ip)

        # iVars decls
        self.__on_connected = None
        self.__on_player_selected = None
        self.__on_move_performed = None

        # Declare the messages validator assembler callbacks
        self.__assemble_validators = {
            Connect4Communicator.MESSAGE_TYPE_PLAYER_SELECTED:
                self.__do_assemble_player_sel_args,
            Connect4Communicator.MESSAGE_TYPE_MOVE:
                self.__do_assemble_move_args
        }

        # Declare the message handlers callbacks.
        self.__disassemble_handlers = {
            Connect4Communicator.MESSAGE_TYPE_PLAYER_SELECTED:
                self.__handle_disassembled_player_sel,
            Connect4Communicator.MESSAGE_TYPE_MOVE:
                self.__handle_disassembled_move
        }

        # Register ourselves to receive incoming messages
        # (note the usage of the direct call to the super, since our method
        #  is disabled)
        Communicator.bind_action_to_message(
            self, self.__handle_incoming_message)

    def set_on_connected(self, delegate):
        """
        Sets the delegate that will be fired when a communication has been
        established.
        :param delegate: The delegate. Signature: void(void).
        """
        self.__on_connected = delegate

    def get_on_connected(self):
        """
        Gets the delegate that will be fired when a communication has been
        established.
        :return: The delegate (void(void)) 2nd order function.
        """
        return self.__on_connected

    def set_on_player_selected(self, delegate):
        """
        Sets the delegate that will be fired when a player type has been
        selected.
        :param delegate: The delegate. Signature: void(player_number, type).
        """
        self.__on_player_selected = delegate

    def get_on_player_selected(self):
        """
        Gets the delegate that will be fired when a player type has been
        selected.
        :return: The delegate 2nd order (void(int, int)) function.
        """
        return self.__on_player_selected

    def set_on_move_performed(self, delegate):
        """
        Sets the delegate that will be fired when a move has been
        performed.
        :param delegate: The delegate. Signature: void(player, column).
        """
        self.__on_move_performed = delegate

    def get_on_move_performed(self):
        """
        Gets the delegate that will be fired when a move has been
        performed.
        :return: The delegate 2nd order (void(int, int)) function.
        """
        return self.__on_move_performed

    def set_player_type(self, player, type):
        """
        Sends the other message our player type.
        :param player: The current program player number.
        :param type: The player type (human/ai).
        """
        buff = self.__assemble_message(
            Connect4Communicator.MESSAGE_TYPE_PLAYER_SELECTED,
            player, type)

        self.send_message(buff)

    def move_played(self, player, column):
        """
        Inform the other player that a move has been played.
        :param player: The player number.
        :param column: The move column as integer.
        """
        buff = self.__assemble_message(Connect4Communicator.MESSAGE_TYPE_MOVE,
                                       player, column)
        self.send_message(buff)

    # region Overwritten methods

    def connect(self):
        """
        Has to be invoked before any message sending and receiving can be
        accomplished. Uses the tkinter main loop to constantly listen on a
        given port for an incoming connection (server) or attempt and connect
        to a remote host via an IP and a port number.
        :return: None.
        """
        # Super
        Communicator.connect(self)

        # We've successfully connected?
        if self.is_connected() and self.__on_connected is not None:
            # Invoke our event on the mainloop.
            self._get_root().after(0, self.__on_connected)

    def bind_action_to_message(self, func):
        """
        Binds a specific function to the event of receiving a message.
        :param func: the function.
        :return: None.
        """
        raise RuntimeError(Connect4Communicator.BIND_DISABLED_MESSAGE)

    # endregion

    # region Private API

    def __handle_incoming_message(self, message):
        """
        Handles an incoming message.
        :param message: The message.
        """
        message_type, message_args = self.__disassemble_message(message)

        # Handle the message
        self.__disassemble_handlers[message_type](*message_args)

    def __assemble_message(self, message_type, *args):
        """
        Assemble the given message
        :param type: The message type, one of the
        Connect4Communicator.MESSAGE_TYPE_**** constants.
        :param args: A set of message arguments.
        :return: The assembled message content
        """
        # Is this a valid message?
        if message_type not in self.__assemble_validators:
            raise ValueError(Connect4Communicator.INVALID_MESSAGE_TYPE)

        # Attempt to invoke the validator and check that message.
        if not self.__assemble_validators[message_type](*args):
            raise ValueError(Connect4Communicator.INVALID_MESSAGE_ARGS)

        # Attain the message content
        message_content = [[message_type], list(args)]

        # Format it
        buff = StringIO()
        writer = csv.writer(buff, quoting=csv.QUOTE_NONNUMERIC)
        for line in message_content:
            writer.writerow(line)

        return buff.getvalue()

    def __disassemble_message(self, message):
        """
        Disassemble a message into a message type and extra args.
        :param message: The message string.
        :return: A tuple contains the message type and the message args,
        or None if the de-assemble process failed.
        """
        # This is an empty message?
        if message == "":
            return None, None

        # Attempt to read the CSV data
        lines = message.splitlines()
        if len(lines) < Connect4Communicator.MESSAGE_FORMAT_LEN:
            return None, None
        if len(lines) > Connect4Communicator.MESSAGE_FORMAT_LEN:
            # In case the message lines is bigger than we allow, concat it.
            lines = lines[0:Connect4Communicator.MESSAGE_FORMAT_LEN]

        # Get the message contents
        message_type_str = lines[Connect4Communicator.MESSAGE_FORMAT_TYPE_LOC]
        message_args_str = lines[Connect4Communicator.MESSAGE_FORMAT_ARGS_LOC]

        # This is a valid message?
        message_type = 0
        try:
            message_type = int(message_type_str)
            if message_type not in self.__disassemble_handlers:
                return None, None
        except ValueError:
            # This isn't an int, so that's bad
            return None, None

        # Attempt to read the message args as a csv line
        # See: https://stackoverflow.com/a/3305973/1497516
        message_args = list(csv.reader(message_args_str.splitlines()))

        return message_type, message_args

    def __do_assemble_move_args(self, *args):
        """
        Validate a move message.
        :param args: The message args.
        :return: True if this is a valid message, false otherwise.
        """
        # Did we got enough args?
        if len(args) != Connect4Communicator.MOVE_MESSAGE_ARGS_COUNT:
            return False

        # Make sure we got valid integer values
        player_str = str(args[Connect4Communicator.MOVE_MESSAGE_PLAYER_LOC])
        column_str = str(args[Connect4Communicator.MOVE_MESSAGE_COLUMN_LOC])
        try:
            # Player
            player = int(player_str)
            if not Game.is_valid_player_number(player):
                return False

            # Column
            column = int(column_str)
            if not Board.is_valid_column_index(column):
                return False
        except ValueError:
            return False

        # It's good (the protocol can't know about invalid moves).
        return True

    def __handle_disassembled_move(self, args):
        """
        Handle a disassembled move.
        :param args: The move args.
        :return: True if this is a valid move, which was handled, or false
        otherwise.
        """
        # Did we got enough args?
        if len(args) != Connect4Communicator.MOVE_MESSAGE_ARGS_COUNT:
            return False

        # Attempt to get the player and column integers
        player_str = str(args[Connect4Communicator.MOVE_MESSAGE_PLAYER_LOC])
        column_str = str(args[Connect4Communicator.MOVE_MESSAGE_COLUMN_LOC])
        try:
            # Check the player
            player = int(player_str)
            if not Game.is_valid_player_number(player):
                return False

            # Check the column
            column = int(column_str)
            if Board.is_valid_column_index(column):
                # Notify the user about performed move
                if self.__on_move_performed is not None:
                    self.__on_move_performed(player, column)
            else:
                return False

            return True
        except ValueError:
            return False

    def __do_assemble_player_sel_args(self, *args):
        """
        Validate a player selected message.
        :param args: The message args.
        :return: True if this is a valid message, false otherwise.
        """
        # Did we got enough args?
        if len(args) != Connect4Communicator.PLY_SEL_MESSAGE_ARGS_COUNT:
            return False

        # Make sure we got valid integer values
        num_str = str(args[Connect4Communicator.PLY_SEL_MESSAGE_PLAYER_LOC])
        type_str = str(args[Connect4Communicator.PLY_SEL_TYPE_LOC])
        try:
            # Player number
            player_number = int(num_str)
            if not Game.is_valid_player_number(player_number):
                return False

            # Player type
            player_type = int(type_str)
            if not Player.is_valid_type(player_type):
                return False
        except ValueError:
            return False

        # It's good (the protocol can't know about invalid moves).
        return True

    def __handle_disassembled_player_sel(self, args):
        """
        Handle a disassembled player selected message.
        :param args: The move args.
        :return: True if this is a message, false otherwise.
        """
        # Did we got enough args?
        if len(args) != Connect4Communicator.MOVE_MESSAGE_ARGS_COUNT:
            return False

        # Attempt to get the player and column integers
        num_str = str(args[Connect4Communicator.PLY_SEL_MESSAGE_PLAYER_LOC])
        type_str = str(args[Connect4Communicator.PLY_SEL_TYPE_LOC])
        try:
            # Check the player
            player_number = int(num_str)
            if not Game.is_valid_player_number(player_number):
                return False

            # Check the column
            player_type = int(type_str)
            if Player.is_valid_type(player_type):
                # Notify the user about performed move
                if self.__on_player_selected is not None:
                    self.__on_player_selected(player_number, player_type)
            else:
                return False

            return True
        except ValueError:
            return False

    # endregion
