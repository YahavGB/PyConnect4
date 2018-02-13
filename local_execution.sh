#!/bin/bash
PORT=$(($RANDOM + ($RANDOM % 2) * 32768))

echo "Starting on port $PORT"
python3 ./connect4.py $1 $PORT &
python3 ./connect4.py $2 $PORT $3
