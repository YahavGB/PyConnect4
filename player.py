##############################################################################
# PyConnect4: player.py
# DESCRIPTION: This file contains the implementation of the game player class.
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


class Player:
    """
    Describes a player in the game.
    """

    ############################################################
    # Constants
    ############################################################

    #: Describes the human player name.
    PLAYER_NAME_HUMAN = "Human"

    #: Describes the computer (AI) player name.
    PLAYER_NAME_COMPUTER = "Computer"

    #: Describe a human player type.
    PLAYER_TYPE_HUMAN = 1

    #: Describes a computer (AI) player type.
    PLAYER_TYPE_COMPUTER = 2

    #: Describes the invalid player number exception message.
    INVALID_PLAYER_TYPE_MESSAGE = "The given player type is invalid."

    ############################################################
    # Ctor
    ############################################################

    def __init__(self, player_number, color):
        """
        Initializes a new player.
        :param player_number: The player number.
        :param color: The player color.
        """
        self.__number = player_number
        self.__color = color
        self.__player_type = Player.PLAYER_TYPE_HUMAN

    ############################################################
    # Public API
    ############################################################

    def __eq__(self, other):
        """
        Compare two player instances.
        :param other: The other player instance.
        :return: True if this is the same player, false otherwise.
        """
        return self.__number == other.get_player_number()

    def get_player_number(self):
        """
        Gets the player number, this value meets one of the Game.PLAYER_****
        constants.
        :return: The player number.
        """
        return self.__number

    def get_player_type(self):
        """
        Gets the player type.
        :return: One of the Player.PLAYER_TYPE_**** constants.
        """
        return self.__player_type

    def set_player_type(self, value):
        """
        Sets the player type.
        :param value: The player type, one of the Player.PLAYER_TYPE_****
        constants.
        """
        if not Player.is_valid_type(value):
            raise ValueError(Player.INVALID_PLAYER_TYPE_MESSAGE)
        self.__player_type = value

    def get_color(self):
        """
        Gets a string that represents this player color.
        :return: The string that represents the player color.
        """
        return self.__color

    def get_color_char(self):
        """
        Gets a char that represents this player color.
        :return: A char that represents the player color.
        """
        return self.__color[0].upper()

    def get_name(self):
        """
        Gets the player name.
        :return: A string containing the player name.
        """
        if self.__player_type == Player.PLAYER_TYPE_COMPUTER:
            return Player.PLAYER_NAME_COMPUTER
        return Player.PLAYER_NAME_HUMAN

    def __repr__(self):
        return "<Player %s (color=%s, name=%s)>" % \
            (id(self), self.__color, self.get_name())

    @staticmethod
    def is_valid_type(value):
        """
        Determine if the given value is a valid player type.
        :param value: The player type.
        :return: True if this is a valid type, false otherwise.
        """
        return value != Player.PLAYER_TYPE_HUMAN \
            or value != Player.PLAYER_TYPE_COMPUTER
