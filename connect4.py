##############################################################################
# PyConnect4: connect4.py
# DESCRIPTION: This file contains the four in a row entry point. This file
# resolves the command line arguments and presents the game GUI.
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


import sys
from ui import Connect4GUI
import tkinter as t
from player import Player
from game import Game

############################################################
# Constants
############################################################

#: Defines the "is human" argument location.
CLI_ARG_IS_HUMAN_LOC = 0

#: Defines the connect port argument location.
CLI_ARG_PORT_LOC = 1

#: Defines the connect ip address argument location.
CLI_ARG_IP_ADDR_LOC = 2

#: Defines the number of required arguments to successfully execute the
# program.
CLI_REQUIRED_ARGS_COUNT = 2

#: Defines the number of optional argument number.
CLI_OPTIONAL_ARGS_COUNT = 1

#: Defines the invalid arguments message.
CLI_INVALID_ARGS_MESSAGE = "Illegal program arguments."

#: Defines the minimum port number.
MIN_PORT_NUMBER = 0

#: Defines the maximum port number.
MAX_PORT_NUMBER = 65535

#: Defines that the player is a human.
CLI_HUMAN_ARG_VALUE = 'human'

#: Defines that the player is an AI.
CLI_AI_ARG_VALUE = 'ai'

############################################################
# Helper Functions
############################################################


def resolve_args():
    """
    Resolve the received program parameters.
    :return: A tuple contains the resolved program args or None if the
    given arguments are invalid.
    """
    # Setup
    args = sys.argv[1:]
    args_len = len(args)

    # Did we got enough arguments?
    if args_len < CLI_REQUIRED_ARGS_COUNT:
        return None, None, None

    # Resolve the player type
    is_ai = False
    if args[CLI_ARG_IS_HUMAN_LOC] == CLI_AI_ARG_VALUE:
        is_ai = True
    elif args[CLI_ARG_IS_HUMAN_LOC] != CLI_HUMAN_ARG_VALUE:
        return None, None, None

    # Check the port
    port_number = None
    try:
        port_number = int(args[CLI_ARG_PORT_LOC])
    except ValueError:
        return None, None, None

    if port_number < MIN_PORT_NUMBER or port_number > MAX_PORT_NUMBER:
        return None, None, None

    # Finalize
    ip_addr = None
    if args_len == CLI_REQUIRED_ARGS_COUNT + CLI_OPTIONAL_ARGS_COUNT:
        # We got an ip
        ip_addr = args[CLI_ARG_IP_ADDR_LOC]

    # We didn't got an IP
    return is_ai, port_number, ip_addr


def get_player_number(ip_address):
    """
    Gets the player number based on her IP address.
    :param ip_address: The IP address.
    :return: The player number.
    """

    if ip_address is None:
        return Game.PLAYER_ONE
    return Game.PLAYER_TWO

############################################################
# The program main entry point
############################################################


if __name__ == "__main__":
    # four_in_a_row.py is_human port <ip>
    is_ai, port_number, ip_address = resolve_args()
    if is_ai is None:
        print(CLI_INVALID_ARGS_MESSAGE)
        sys.exit()

    # Setup the game object
    game = Game()
    current_player = game.get_player(get_player_number(ip_address))

    if is_ai:
        current_player.set_player_type(Player.PLAYER_TYPE_COMPUTER)
    else:
        current_player.set_player_type(Player.PLAYER_TYPE_HUMAN)

    # Executes the UI
    root = t.Tk()
    Connect4GUI(root, game, current_player, port_number, ip_address)

    root.mainloop()
