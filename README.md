# PyConnect4
A full human V. computer implementation of the Connect4 game using Python.

# General Game Highlights
This implementation contains the following features:
* Human V. Human, Human V. Computer and Computer V. Computer modes.
* Cross platform graphical UI based on tkinter and PIL.
* Network based games using sockets.
* AI implementation for the computer player.

# AI highlights
The following algorithms has been used for the AI:
* The game board was implemented using bitboard for faster computation.
* The AI is based on the Alpha-Beta variation of the negamax algorithm to perform efficient graph search with beta cutoffs.
* The AI uses a PVS search to retrieve the selected PV.
* The AI uses IDS to perform better depth searching.
* To make sure we won't evaluate repeating board states, I've implemented a Transposition Table.
* This implementation supports timeout factors.

# How to start a new game
This game has two modes - a server mode and client mode. To start a game, a server must be created first and then a client shall connect to it.
The following command should be executed to start a new game:

    python3 connect4 <human/ai> <port> <ip-addr>

Where the arguments is as follows:
1. `<human/ai>`: An indicator if the current game instance is managed by a human or by the built-in AI engine. If you'll select an AI the graphical interface will be disabled and the computer will select a moves instead of you.
2. `<port>`: The port in which the game will be run at. If you host the game (a.k.a. the server instance), you should select a random **open** port. If you're the client who wish to connect to a given server, you should specify the server port.
3. `<ip-addr>`: The IP address if the server to connect to. **Note that if you're the server, you shouldn't specify this argument.** In fact, based on this argument the application decide whether or not you're the server or client.

Alternatively, a `local_execution.sh` script has been supplied to fastly invoke a game between two playes on the same computer:

    $ local_execution.sh <human/ai-player1> <human/ai-player2> <ip-addr>

The supplied arguments for this script is as follows:
1. `<human/ai-player1>`: One of the values "human" or "ai", which used to determine if the first player plays as a human or as a computer.
2. `<human/ai-player2>`: One of the values "human" or "ai", which used to determine if the second player plays as a human or as a computer.
3. `<ip-addr>`: The local computer IP address.

# License
This code is been released under the GPL V3 license. Please refer to the LICENSE file for more information.