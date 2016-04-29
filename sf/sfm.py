#!/usr/bin/env pypy
# -*- coding: utf-8 -*-

from __future__ import print_function
from multiprocessing import Process, Queue
import sys, re, random

import sflib

DEPTH = 4
WORKERS = 4
def work(in_q, out_q):
    while True:
        move, pos = in_q.get()
        out_q.put((move, sflib.search(pos, DEPTH)))

def init_board(board_file):
    output = (
        '         \n'
        '         \n'
    )
    with open(board_file) as f:
        for line in f:
            output += ' ' + line

    output += (
        '         \n'
        '          '
    )
    return output

opening_list = {}
def openings():
    global opening_list
    moves = []
    for move in ('e2e4', 'd2d4', 'b1c3', 'g1f3', 'c2c4'):
        moves.append((sflib.parse(move[:2]), sflib.parse(move[2:])))
    pos = sflib.Position(sflib.initial, 0, (True,True), (True,True), 0, 0)
    opening_list[pos] = moves

in_q = Queue()
out_q = Queue()

def next_move(pos):
    opening_moves = opening_list.get(pos)
    if opening_moves:
        return random.sample(opening_moves, 1)[0]

    valid_moves = pos.valid_moves()
    for move in valid_moves:
        next_pos = pos.move(move)
        in_q.put((move, next_pos))

    next_moves = []
    for i in range(len(valid_moves)):
        (move, (next_move, score, depth)) = out_q.get()
        if next_move:
            #print('w move:', sflib.format_move(move), ', b best move: ', sflib.format_move(next_move, True), ', score:', score, ', depth:', depth)
            next_moves.append((move, next_move, score, depth))

    best_move = min(next_moves, key=lambda m: m[2])
    if best_move[2] < 0 - sflib.MATE_VALUE:
        print('You will lose...')
        return min([m for m in next_moves if m[2] < 0-sflib.MATE_VALUE], key=lambda m: m[3])[0]

    candidate_moves = sorted([move for move in next_moves if abs(move[2] - best_move[2]) < 51], key=lambda m: m[2])
    for move in candidate_moves:
        print('move:', sflib.format_move(move[0]) + ', score:',  str(move[2]) + ', depth:', str(move[3]))
    return random.sample(candidate_moves, 1)[0][0]

def rotate_move(move):
    return (119-move[0], 119-move[1])

def accept_move(pos):
    move = None
    while move not in pos.valid_moves():
        match = re.match('([a-h][1-8])'*2, raw_input('Your move: '))
        if match:
            move = rotate_move((sflib.parse(match.group(1)), sflib.parse(match.group(2))))
        else:
            # Inform the user when invalid input (e.g. "help") is entered
            print("Please enter a move like g8f6")
    return move

def main():
    global DEPTH
    if len(sys.argv) > 1 and sys.argv[1] != '0':
            board = init_board(sys.argv[1])
    else:
        board = sflib.initial

    if len(sys.argv) > 2:
        DEPTH = int(sys.argv[2])

    worker_list = []
    for i in range(WORKERS):
        worker_list.append(Process(target=work, args=(in_q, out_q,)))
        worker_list[i].start()

    try:
        openings()
        pos = sflib.Position(board, 0, (True,True), (True,True), 0, 0)
        while True:
            sflib.print_pos(pos)
            machine_move = next_move(pos)
            print('My move:', sflib.format_move(machine_move))
            pos = pos.move(machine_move)

            sflib.print_pos(pos.rotate())
            player_move = accept_move(pos)
            pos=pos.move(player_move)


    except BaseException as e:
        print(e)
    finally:
        for i in range(WORKERS): worker_list[i].terminate()

    return

if __name__ == '__main__':
    main()
